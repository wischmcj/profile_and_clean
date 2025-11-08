import os
import pandas as pd

from exploration import DOWNLOADS_DIR, profile_columns, column_freq_across_files, search_for_bad_values
from normalization import correct_column_names_by_config, to_snake_case

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


if __name__ == "__main__":
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

    df = combined_df
    # Identify null values and column data types
    #   will enable use of analytics functions 
    profile_info = profile_columns(df)
    print('Profile info:')
    # print({k: {k2: v2 for k2, v2 in v.items() if k2 != 'unique_vals'} for k, v in profile_info.items() })
    print(profile_info)
    breakpoint()


        
        
    # Profiles columns, getting counts of distinct values
    #  will help identify typos, null values, etc.
    print("\nDistinct values in each column:")
    unique_vals = {col: combined_df[col].unique() for col in combined_df.columns}
    print(unique_vals)

    breakpoint()

