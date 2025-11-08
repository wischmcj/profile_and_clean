import os
import re
import pandas as pd
from pandas.api.types import is_datetime64_any_dtype as is_datetime, is_numeric_dtype as is_numeric

from ftfy import fix_text

from config import *
# col_name_correction, defaults, to_snake_case


def to_snake_case(column_name):
    return column_name.lower().replace('  ', '').replace(' ', '_')

def coerce_and_track(df, column_name, func = pd.to_datetime):
    initial_nulls = df[column_name].isna()
    proposed_values = func(df[column_name], errors='coerce')
    new_nulls = df[column_name].isna()
    coerced_idxs = new_nulls not in initial_nulls
    coerced_values = df[column_name].loc[coerced_idxs]
    print(f"Number of values coerced for {column_name}: {len(coerced_values)}")
    print(f"Coerced values: {coerced_values}")
    if len(coerced_values)<len(df)/10:
        df[column_name] = proposed_values
    return df, coerced_values, coerced_idxs


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

def correct_column_values(df):
    for column_name, default_func in defaults.items():
        if column_name not in df.columns:
            try:
                df[column_name] = default_func(df)
            except Exception as e:
                breakpoint()
                print(f"Error applying default function to {column_name} in {df['year'].iloc[0]}")
    return df

def correct_common_string_issues(series):
    """
    Correct common string issues in a series
    """
    # Remove leading and trailing whitespace
    new_series = series.str.strip()
    # elimiate duplicate spaces
    new_series =new_series.str.split().apply(lambda x: " ".join(x))
    new_series = new_series.apply(fix_text)
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
    # new_series = correct_common_string_issues(new_series)

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
