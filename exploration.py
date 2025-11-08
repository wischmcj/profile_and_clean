import os
import pandas as pd
from pandas.api.types import is_datetime64_any_dtype as is_datetime, is_numeric_dtype as is_numeric


from config import *
# col_name_correction, defaults, to_snake_case



def column_freq_across_files(column_lists):
    """
    Count occurrences of each column within sublists of column_lists
    This presents data to the use for use in creating column_name_correction configurations
    """
    good_col_lists = [x for x in column_lists if all([not 'Unknown' in colname for colname in x])]
    distinct_column_lists = set.intersection(*good_col_lists)
    print(distinct_column_lists)

    all_columns = set()
    for col_set in good_col_lists:
        all_columns.update(col_set)

    print(column_lists)
    # Get columns occurng in every sublist of column_lists
    good_col_lists = [x for x in column_lists if all([not 'Unknown' in colname for colname in x])]
    distinct_column_lists = set.intersection(*good_col_lists)
    print(f"Columns occurring in every sublist of column_lists: {distinct_column_lists}")

    column_counts = {col: sum(1 for col_set in good_col_lists if col in col_set) for col in all_columns}
    print("\nColumn occurrence counts:")
    num_files = len(column_lists)
    for col, count in sorted(column_counts.items(), key=lambda x: -x[1]):
        print(f"{col}: {count}/{num_files}")

def search_for_bad_values(df):
    """
    Searches for bad values in a dataframe, returning:
    - low_cardinality: a dictionary of low cardinality values
    """
    low_cardinality = {}
    for col in df.columns:
       # we report on values that occur half as often as they would if randomly distributed
       unique_vals = df[col].unique()
       expected_freq_percentile = (1/len(unique_vals))/2
       print(f"Expected frequency percentile for {col} is {expected_freq_percentile}")
       if expected_freq_percentile>1 or expected_freq_percentile<0.01:
           breakpoint()
           print(f"Expected frequency percentile for {col} is {expected_freq_percentile}")
           expected_freq_percentile = .1
       low_cardinality = identify_low_cardianlity_values(df[col], 
                                                       input_files=df['year'],
                                                       min_percentile=expected_freq_percentile)
       print(f" - Low cardinality values for {col}:")
       print(f'{low_cardinality}')
       breakpoint()

def characterize_nulls(series):
    null_count = series.isnull().sum()
    total_rows = len(series)
    null_percentage = (null_count / total_rows) * 100 if total_rows > 0 else 0
    null_info = {
        'null_count': null_count,
        'null_percentage': null_percentage,
        'has_nulls': null_count > 0
    }
    return null_info

def identify_low_cardianlity_values(series, input_files, min_percentile=0.25, max_percentile=0.9):
    """
    Identify unique values in the input series that occur infrequently.
    Returns a list of values and their counts that are considered 'low cardinality'.
    You may customize the threshold with `min_count` or `max_percentage`.
    """
    value_counts = series.value_counts(dropna=False)
    # Set thresholds based on percentiles of value_counts
    if len(value_counts) > 0:
        min_count = int(value_counts.quantile(min_percentile))
        max_count = int(value_counts.quantile(max_percentile))
        print(f"Min count: {min_count}, Max count: {max_count}")

    total = len(series)
    low_cardinality = []
    for val, count in value_counts.items():
        percentage = (count / total) * 100 if total > 0 else 0
        if not (count <= max_count and count >= min_count):
            low_cardinality.append({'value': val, 'count': count, 'percentage': percentage})
    for entry in low_cardinality:
        # For each low cardinality value, get the associated input_files
        indices = series[series == entry['value']].index
        entry['input_files'] = input_files.loc[indices].unique().tolist()
    return low_cardinality


def profile_columns(df, include_unique_vals=False):
    """
    Profiles columns of a dataframe, returning:
    - column_data_types: a dictionary of column data types
    - target_data_type: a dictionary of target data types
    - column_null_info: a dictionary of column null information
    """
    inferred_data_types = df.infer_objects()
    
    profiles = {}
    for col in df.columns:
        profile_info = {
            'column_data_types': {},
            'target_data_type': {},
            'column_null_info': {},
        } 
        # Track current column dfdata type
        profile_info['column_data_types'] = str(df[col].dtype)
        profile_info['column_null_info'] = characterize_nulls(df[col])
        profile_info['target_data_type'] = inferred_data_types[col].dtype

        print(f"Column '{col}':")
        print(f" - Data Type: {profile_info['column_data_types']}")
        print(f" - Data Type: {profile_info['target_data_type']}")
        print(f" - Nulls: {profile_info['column_null_info']['null_count']}/{len(df)} ({profile_info['column_null_info']['null_percentage']:.2f}%)")
        
        if include_unique_vals:
            profile_info['unique_vals'] = df[col].unique()
            print(f" - Unique count: {len(profile_info['unique_vals'])}")
            if len(profile_info['unique_vals']) < 20:
                print(f" - Values: {profile_info['unique_vals']}")
            else:
                print(f" - Sample values: {profile_info['unique_vals'][:20]}")

        profiles[col] = profile_info
    return profiles

