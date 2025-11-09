from collections import defaultdict
import os
import pandas as pd

import json
from exploration import profile_columns, column_freq_across_files, profile_delimited_columns, search_for_bad_values
from normalization import convert_to_target_types, correct_column_names_by_config, correct_common_string_issues, extract_distinct_delimited_values_and_cooccurrence, remove_bracketed_references, remove_quotes, replace_values, replace_values_str, standardize_datetime_series, standardize_delimited_field, substitute_values_str, to_snake_case
from config import cleaned_columns, cleaned_column_types

from cardinality_reduction import standardize_area_affected, add_qualifier_to_county_names, remove_special_symbols_and_numbers

DOWNLOADS_DIR = "./data/chosen"

#### HELPERS #####

def print_series_differences(series1, series2, save_to_file=False, write_dir = 'orig_to_clean_values'):
    """
    Print the differences between two pandas Series.
    Shows:
      - Values only in series1
      - Values only in series2
      - Values present in both
    """
    set1 = set(series1.dropna().unique())
    set2 = set(series2.dropna().unique())

    only_in_1 = set1 - set2
    only_in_2 = set2 - set1
    in_both = set1 & set2

    print("Values only in series 1:")
    print(sorted(list(only_in_1)))
    print("\nValues only in series 2:")
    print(sorted(list(only_in_2)))

    if save_to_file:
        with open(f'data/{write_dir}/{series1.name}.csv', 'w') as f:
            idxs = series1.index[series1.str.lower() != series2.str.lower()]
            if len(idxs)==0:
                print(f'Warning: No differences found in {series1.name}')
                return
            df = pd.DataFrame({'original': series1[idxs], 'corrected': series2[idxs]})
            df.to_csv(f, index=False)

#### MAIN FUNCTIONS ####

def read_find_headers_and_fix_cols(downloads_dir):
    """
    Read all .xls files into pandas DataFrames,
    In addition to reading the files, alsp:
    - corrects for variances in the number of rows above the table in each file 
    - adds year column to allow for identifying changes to standard file format over time 
    """
    # List all .xls files in the downloads directory
    xls_files = [os.path.join(downloads_dir, f) for f in os.listdir(downloads_dir) if f.lower().endswith('.xls')]

    df_list = []
    column_lists= []
    for file in xls_files:
        check_next_row = True
        # here we try a few values for skip rows in order to get the right header row
        skip_row_num = 0
        while check_next_row:
            df = pd.read_excel(file, header=0, skiprows=skip_row_num)
            columns =df.columns.tolist()
            # Warn if some columns do not have a header row
            no_header_cols =[colname for colname in columns if 'Unknown' in colname or 'Unnamed' in colname]
            if  skip_row_num <=4 and len(no_header_cols):
                skip_row_num +=1
            else:
                check_next_row = False
        if skip_row_num > 4:
            print(f"Could not find header row in {file}. File not read.")
            continue

        # Add year to allow for identifying changes to standard file format over time 
        year = int(file.split('/')[-1].split('_')[0])
        df['year'] = year
        column_lists.append(set(columns))
        df_list.append(df)
    return df_list, column_lists


def read_and_prep_column_meta():
    """
        Read in each file
        profile the columns
        update the column names to match
        combine the dataframes into a single dataframe
        return the combined dataframe and the column summaries

    Returns:
        combined_df: A pandas DataFrame containing the combined data from all files.
        column_summaries: A dictionary containing the summaries of the columns for each year.
    """
    # Profile columns accross file, create column mapping config 
    df_list, column_lists = read_find_headers_and_fix_cols(DOWNLOADS_DIR)
    column_freq_across_files(column_lists) 

    # correct column names and values
    # Run iteratively as column configs are built
    column_summaries = {}
    for df in df_list:
        df, column_summary = correct_column_names_by_config(df)
        column_summaries[df['year'].iloc[0]] = column_summary
        print(column_summary)

        
    # Combine the corrected dataframes into as single dataframe
    combined_df = pd.concat(df_list, ignore_index=True)
    print(f"\nCombined DataFrame shape: {combined_df.shape}")
    snake_case_columns = {col: to_snake_case(col) for col in combined_df.columns}
    # Removes all columns not specified in correct_column_names_by_config
    # combined_df = combined_df.keep_only_columns(col_name_correction.keys())
    combined_df.rename(columns=snake_case_columns, inplace=True)
    return combined_df, column_summaries

def apply_normalization_configs(df):
    for col in cleaned_columns:
        dtype = cleaned_column_types[col]
        series = df[col]

        if dtype == "datetime":
            series = standardize_datetime_series(series)


        series = series.astype(str)
        og_series = series.copy()
        series =series.str.lower()

        print(f"Correcting common string issues for {col}")
        new_series = correct_common_string_issues(series)
        # print_series_differences(series, new_series)
        series = new_series    

        print(f"Standardizing delimited field for {col}")
        new_series = standardize_delimited_field(series, col)
        # print_series_differences(series, new_series)
        series = new_series

        print(f"Removing bracketed references for {col}")
        new_series = remove_bracketed_references(series)
        # print_series_differences(series, new_series)
        series = new_series

        print(f"Removing quotes for {col}")
        new_series = remove_quotes(series)
        # print_series_differences(series, new_series)
        series = new_series
        
        print(f"Replacing values for {col}")
        new_series = replace_values_str(series)
        # print_series_differences(series, new_series)
        series = new_series

        print(f"Replacing values for {col}")
        new_series = replace_values(series)
        # print_series_differences(series, new_series)
        series = new_series

        print(f"Substituting values for {col}")
        new_series = substitute_values_str(series)
        # print_series_differences(series, new_series)
        series = new_series

        if series.name == 'nerc_region':
            series  = series.str.replace('re', 'texas re')
        
        # Save a mapping for all values in the series
        print_series_differences(og_series, new_series, save_to_file=True)
        df[col] = new_series

    return df

def assume_values_where_possible(df):
    """
    Assume values where possible based on the data in the dataframe.
    """
    null_event_month = df['event_month'].isna() & df['date_event_began'].notna()
    print(f"Number of rows with null event month and not null date event began: {null_event_month.sum()}")
    df[null_event_month]['event_month'] = pd.to_datetime(df['date_event_began'][null_event_month]).dt.month_name()

    return df

def coerce_types_and_report(df):
    # INSERT_YOUR_CODE
    """
    Generates a report on the conversion process of dataframe columns to their target data types.

    This function attempts to coerce the datetypes of our columns to their target types,
    separates our rows with values incompatible with their target types, and 
    saves these rows for inspection. It then compiles and prints a report summarizing the conversions performed.
    """
    pre_conversion_profile_info = profile_columns(df, include_unique_vals=False)

    # Convert to target data types and separate incompatible rows
    print("\n" + "="*80)
    print("="*80)
    valid_df, incompatible_rows_df, conversion_report = convert_to_target_types(df)
    
    # Save incompatible rows for inspection
    if len(incompatible_rows_df) > 0:
        print(f"\n{len(incompatible_rows_df)} rows with type incompatibilities will be separated.")
        incompatible_rows_df.to_csv('data/incompatible_rows.csv', index=False)
        print("Incompatible rows saved to 'incompatible_rows.csv'")

    post_conversion_profile_info = profile_columns(valid_df, include_unique_vals=False)


    join_profile_info = {}
    for col in pre_conversion_profile_info.keys():
        col_info = defaultdict(dict)
        for k in pre_conversion_profile_info[col].keys():
            col_info[k]['initial'] = pre_conversion_profile_info[col]
            col_info[k]['final'] = post_conversion_profile_info[col]
        join_profile_info[col] = col_info

    print('Join profile info:')
    print(join_profile_info)

    return df, join_profile_info, conversion_report

def standardize_areas(df):
    """
    Standardize the areas in the dataframe.
    """
    new_series = df['area_affected'].copy()
    new_series = remove_special_symbols_and_numbers(new_series)
    new_series = standardize_area_affected(new_series)
    print_series_differences(df['area_affected'], new_series, save_to_file=True, write_dir = 'area_affected_standardization')
    df['area_affected'] = new_series
    return df

# INSERT_YOUR_CODE
def extract_states_from_affected_areas(df):
    """
    Creates a column 'affected_states' containing a list of state names 
    found in the 'area_affected' column using US_STATES_TERRITORIES from config.py.
    
    Args:
        df (pd.DataFrame): The dataframe with an 'area_affected' column.

    Returns:
        pd.DataFrame: DataFrame with new 'affected_states' column.
    """
    from config import US_STATES_TERRITORIES

    # Normalize state names for robust matching (removes case and periods)
    state_set = set(s.lower().replace('.', '') for s in US_STATES_TERRITORIES)

    def find_states(text):
        if not isinstance(text, str):
            return []
        tokens = [token.strip().replace('.', '') for token in text.replace(';', ':').split(':')]
        # We match on the whole token, as area lists like "Texas: Harris County; Maine"
        matches = []
        for token in tokens:
            # Only take "bare" state matches, e.g. "Texas", not "Harris County"
            normalized = token.lower()
            if normalized in state_set:
                matches.append(token.strip())
        return matches

    df['affected_states'] = df['area_affected'].apply(find_states)
    return df


def main():
    df, column_summaries= read_and_prep_column_meta()

    # Identify null values and column data types
    #   will enable use of analytics functions 
    profile_info = profile_columns(df)
    # print('Profile info:')
    # print(profile_info)
    
    df = apply_normalization_configs(df)
    df = assume_values_where_possible(df)
    df, join_profile_info, conversion_report = coerce_types_and_report(df)

    # tying up odds and ends    
    df['nerc_region'] = df['nerc_region'].str.split(',')
    df = df.rename(columns={'nerc_region': 'nerc_region_list'})

    # add states_effected column
    df = extract_states_from_affected_areas(df)
    df = standardize_areas(df)
    breakpoint()

    df.to_csv('data/cleaned_data.csv', index=False)
    return df

if __name__ == "__main__":
    df = main()
    breakpoint()
    df = profile_delimited_columns(df)

    # df = pd.read_csv('data/cleaned_data.csv')

    breakpoint()
    # Get rows where event_category contains 'weather' (case insensitive)
    weather_event_rows = df[df['event_category'].str.contains("Arkansas:Louisiana", case=False, na=False)]
    print(weather_event_rows)
    breakpoint()
    test = df[df['area_affected'].str.contains("Arkansas:Louisiana", case=False, na=False)]

    # import polars as pl
    # polar_df = pl.from_pandas(valid_df)

    # result = doeDisturbanceSchema.validate(polar_df)
    # print(result)



        
        
    # Profiles columns, getting counts of distinct values
    #  will help identify typos, null values, etc.
    print("\nDistinct values in each column of valid_df:")
    unique_vals = {col: valid_df[col].unique() for col in valid_df.columns}
    print(unique_vals)

    breakpoint()

