from collections import defaultdict
import os
import pandas as pd

from exploration import profile_columns, column_freq_across_files, search_for_bad_values
from normalization import convert_to_target_types, correct_column_names_by_config, correct_common_string_issues, remove_bracketed_references, remove_quotes, replace_values, replace_values_str, standardize_datetime_series, standardize_delimited_field, to_snake_case
from config import doeDisturbanceSchema, replace_list, cleaned_columns, dtype_conversions, delimiter_correction, cleaned_column_types

DOWNLOADS_DIR = "./data/chosen"
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

# INSERT_YOUR_CODE
def print_series_differences(series1, series2):
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

def apply_normalization_configs(df):
    for col in cleaned_columns:
        dtype = cleaned_column_types[col]
        series = df[col]

        if dtype == "datetime":
            series = standardize_datetime_series(series)

        # if dtype == "string" or dtype == "integer":
        # if dtype == "integer":
        series = series.astype(str)

        print(f"Correcting common string issues for {col}")
        new_series = correct_common_string_issues(series)
        print_series_differences(series, new_series)
        series = new_series    

        print(f"Standardizing delimited field for {col}")
        new_series = standardize_delimited_field(series, col)
        print_series_differences(series, new_series)
        series = new_series

        print(f"Removing bracketed references for {col}")
        new_series = remove_bracketed_references(series)
        print_series_differences(series, new_series)
        series = new_series

        print(f"Removing quotes for {col}")
        new_series = remove_quotes(series)
        print_series_differences(series, new_series)
        series = new_series
        
        print(f"Replacing values for {col}")
        new_series = replace_values_str(series)
        print_series_differences(series, new_series)
        new_series = replace_values(series)
        
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

def get_conversion_report(df):
    pre_conversion_profile_info = profile_columns(df, include_unique_vals=False)

    # Convert to target data types and separate incompatible rows
    print("\n" + "="*80)
    print("CONVERTING COLUMNS TO TARGET DATA TYPES")
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

def main():
    df, column_summaries= read_and_prep_column_meta()

    # Identify null values and column data types
    #   will enable use of analytics functions 
    profile_info = profile_columns(df)
    # print('Profile info:')
    # print(profile_info)
    
    df = apply_normalization_configs(df)
    df = assume_values_where_possible(df)
    df, join_profile_info, conversion_report = get_conversion_report(df)
    df.to_csv('data/cleaned_data.csv', index=False)
    breakpoint()

if __name__ == "__main__":
    # main()
    df = pd.read_csv('data/cleaned_data.csv')
    print(df.head())


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

