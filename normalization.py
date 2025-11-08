import os
import re
import pandas as pd
from pandas.api.types import is_datetime64_any_dtype as is_datetime, is_numeric_dtype as is_numeric

from ftfy import fix_text

from config import *
# col_name_correction, defaults, to_snake_case


def to_snake_case(column_name):
    return column_name.lower().replace('  ', '').replace(' ', '_')

def correct_column_names_by_config(df):
    """Correct column names replacing 
        each of the indicated wrong column 
        names with the correct column name"""
    summary_dict = {'renamed': [], 'not_found': [], 'unexpected': []}
    for correct_col_name,  wrong_col_names in col_name_correction.items():
        # correct incorrect file names
        renamed = []
        for wrong_col_name in wrong_col_names:
            if wrong_col_name in df.columns:
                df.rename(columns={wrong_col_name: correct_col_name}, inplace=True)
                renamed.append(wrong_col_name)
        if len(renamed) > 0:
            summary_dict['renamed'].append(renamed)
            print(f"Renamed columns: {renamed} in {df['year'].iloc[0]}")
        # check if expected column is present
        if correct_col_name not in df.columns:
            summary_dict['not_found'].append(correct_col_name)
            print(f"Column {correct_col_name} not found in {df['year'].iloc[0]}")
    for col in df.columns:
        if col not in col_name_correction.keys():
            summary_dict['unexpected'].append(col)
            print(f"Column {col} not found in col_name_correction")
    return df, summary_dict

    

def correct_common_string_issues(series):
    """
    Correct common string issues in a series
    """
    # Remove leading and trailing whitespace
    new_series = series.str.strip()
    # elimiate duplicate spaces
    new_series =new_series.str.split().str.join(" ")
    # new_series = new_series.apply(fix_text)
    return new_series

    # INSERT_YOUR_CODE
def standardize_delimited_field(series, field_name):
    """
    Standardize the delimiters in a string Series according to delimiter_correction config.
    - series: pd.Series to process
    - field_name: the name of the field/column (str)
    Returns a new pd.Series with standardized delimiters.
    """
    if field_name not in delimiter_correction:
        # No correction mapping for this field, return as is
        return series

    correct_delim, wrong_delims = delimiter_correction[field_name]
    # Remove duplicates and make sure the correct delimiter is not in the 'wrong' list
    wrong_delims_to_replace = [d for d in set(wrong_delims) if d != correct_delim and d != ""]

    # Replace each incorrect delimiter with the correct one
    new_series = series.copy().astype(str)
    for delim in wrong_delims_to_replace:
        new_series = new_series.str.replace(delim, correct_delim)

    # Remove consecutive delimiters (e.g. ';;' or ',,')
    repeated = r'({0})+'.format(re.escape(correct_delim))
    new_series = new_series.str.replace(repeated, correct_delim, regex=True)
    
    # remove spaces between list items and delimiters
    def split_and_join(in_str):
        split_list = in_str.split(correct_delim)
        stripped_list = [item.strip() for item in split_list if item.strip() != ""]
        return correct_delim.join(stripped_list)

    new_series = new_series.apply(split_and_join)

    return new_series

    # INSERT_YOUR_CODE
def remove_bracketed_references(series):
    """
    Remove substrings in the form [13], [1], [abc], etc. from each string in the Series.
    Uses regex to match square-bracket-surrounded text/numbers.
    """
    import re
    return series.astype(str).str.replace(r'\[\s*[\dA-Za-z]+\s*\]', '', regex=True)

def remove_quotes(series):
    """
    Remove quotes from the start and end of each string in the Series.
    """
    return series.astype(str).str.replace(r'^"|"$', '', regex=True)

def replace_values_str(series):
    """
    Replace values in the Series that are in the replace_list.
    """

    for value, replacement in replace_list.items():
        series.loc[series==value] = replacement
    return series

def replace_values(series):
    """
    Replace values in the Series that are in the replace_list.
    """
    for value, replacement in replace_list.items():
        to_replace_idx = series.isin([value])
        new_series = series.copy()
        new_series[to_replace_idx] = replacement
    return new_series


    # INSERT_YOUR_CODE
def standardize_datetime_series(series):
    """
    Standardizes values in a Series to 'YYYY-MM-DD HH:MM:SS' format.
    Also handles values like 'MonthName' or 'MonthName, Year' by converting to a datetime.
    Invalid dates are coerced to NaT.

    Args:
        series (pd.Series): Series containing date or datetime strings.

    Returns:
        pd.Series: Standardized datetime strings or NaT
    """
    import pandas as pd
    import re

    def parse_date(val):
        # Fast-path: try normal datetime parse first (handles yyyy-mm-dd... or mm/dd/yyyy etc)
        try:
            dt = pd.to_datetime(val, errors='coerce')
            if pd.notna(dt):
                return dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            pass

        if isinstance(val, str):
            # Handle cases like 'March', 'March, 2022', 'Mar', 'january', etc.
            trimmed = val.strip()
            if not trimmed or trimmed.lower() == "nan":
                return pd.NaT

            # Try to match month name with optional year
            month_pattern = r'^(?P<month>[A-Za-z]+),?\s*(?P<year>\d{4})?$'
            match = re.match(month_pattern, trimmed, re.IGNORECASE)
            if match:
                month_name = match.group('month').capitalize()
                year = match.group('year') or "1900"  # fallback year (arbitrary)
                try:
                    dt = pd.to_datetime(f"{month_name} 1, {year}", errors='coerce')
                    if pd.notna(dt):
                        return dt.strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    return pd.NaT

        return pd.NaT

    return series.apply(parse_date)


def convert_to_target_types(df):
    """
    Identify rows with values incompatible with their target data types,
    separate them into a new dataframe, and convert valid rows to proper types.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with columns matching cleaned_columns and potentially mixed types
    
    Returns:
    --------
    valid_df : pd.DataFrame
        DataFrame with only compatible rows, converted to proper types
    incompatible_rows_df : pd.DataFrame
        DataFrame containing rows with type incompatibilities
    conversion_report : dict
        Report of conversions performed and rows moved
    """
    import numpy as np
    
    incompatible_row_indices = set()
    conversion_report = {
        'total_rows': len(df),
        'incompatible_rows': 0,
        'column_issues': {}
    }
    
    # Check each column for type compatibility
    for col in cleaned_columns:
        if col not in df.columns:
            print(f"Warning: Column {col} not found in DataFrame")
            continue
            
        target_type = cleaned_column_types[col]
        series = df[col]
        column_issues = []
        
        try:
            if target_type == "integer":
                # Check which rows cannot be converted to integer
                for idx, val in series.items():
                    if pd.isna(val):
                        continue
                    try:
                        int(val)
                    except (ValueError, TypeError):
                        incompatible_row_indices.add(idx)
                        column_issues.append({
                            'row_index': idx,
                            'value': val,
                            'issue': 'Cannot convert to integer'
                        })
            
            elif target_type == "datetime":
                # Check which rows cannot be converted to datetime
                for idx, val in series.items():
                    if pd.isna(val):
                        continue
                    try:
                        pd.to_datetime(val)
                    except (ValueError, TypeError):
                        incompatible_row_indices.add(idx)
                        column_issues.append({
                            'row_index': idx,
                            'value': val,
                            'issue': 'Cannot convert to datetime'
                        })
            
            elif target_type == "time":
                # Check which rows cannot be converted to time
                for idx, val in series.items():
                    if pd.isna(val):
                        continue
                    try:
                        # Accept both time objects and valid time strings
                        if not isinstance(val, pd.Timestamp) and hasattr(val, 'hour'):
                            # Already a time object
                            continue
                        pd.to_datetime(val, format='%H:%M:%S')
                    except (ValueError, TypeError):
                        incompatible_row_indices.add(idx)
                        column_issues.append({
                            'row_index': idx,
                            'value': val,
                            'issue': 'Cannot convert to time'
                        })
            
            elif target_type == "string":
                # Strings are generally flexible, but check for unexpected types
                for idx, val in series.items():
                    if pd.isna(val):
                        continue
                    # Most values can be converted to string, so this is usually permissive
                    pass
        
        except Exception as e:
            print(f"Error checking type compatibility for column {col}: {str(e)}")
        
        if column_issues:
            conversion_report['column_issues'][col] = column_issues
    
    # Separate compatible and incompatible rows
    valid_indices = [i for i in df.index if i not in incompatible_row_indices]
    valid_df = df.loc[valid_indices].copy()
    incompatible_rows_df = df.loc[list(incompatible_row_indices)].copy()
    
    conversion_report['incompatible_rows'] = len(incompatible_rows_df)
    conversion_report['valid_rows'] = len(valid_df)
    
    print(f"\nType Conversion Report:")
    print(f"  Total rows: {conversion_report['total_rows']}")
    print(f"  Valid rows: {conversion_report['valid_rows']}")
    print(f"  Incompatible rows: {conversion_report['incompatible_rows']}")
    
    if conversion_report['column_issues']:
        print(f"\nColumns with issues:")
        for col, issues in conversion_report['column_issues'].items():
            print(f"  {col}: {len(issues)} rows with issues")
    
    # Convert valid rows to target types
    print(f"\nConverting valid rows to target types...")
    for col in cleaned_columns:
        if col not in valid_df.columns:
            continue
            
        target_type = cleaned_column_types[col]
        
        try:
            if target_type == "integer":
                valid_df[col] = pd.to_numeric(valid_df[col], errors='coerce').astype('Int64')
                print(f"  Converted {col} to Int64")
            
            elif target_type == "datetime":
                valid_df[col] = pd.to_datetime(valid_df[col], errors='coerce')
                print(f"  Converted {col} to datetime64")
            
            elif target_type == "time":
                # Convert to datetime first, then extract time component
                valid_df[col] = pd.to_datetime(valid_df[col], format='%H:%M:%S', errors='coerce').dt.time
                print(f"  Converted {col} to time")
            
            elif target_type == "string":
                valid_df[col] = valid_df[col].astype('string')
                print(f"  Converted {col} to string")
        
        except Exception as e:
            print(f"  Warning: Could not convert {col} to {target_type}: {str(e)}")
    
    return valid_df, incompatible_rows_df, conversion_report