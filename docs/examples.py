

def changes_in_file_standard(column_summaries): 
    print([k for k,x in column_summaries.items() if 'Alert Criteria' in x['not_found']])
    # ['./chosen/2014_Annual_Summary.xls', './chosen/2013_Annual_Summary.xls']
    print([k for k,x in column_summaries.items() if 'Alert Criteria' not in x['not_found']])
    # ['./chosen/2022_Annual_Summary.xls', './chosen/2023_Annual_Summary.xls', 
    # './chosen/2015_Annual_Summary.xls', './chosen/2017_Annual_Summary.xls', 
    # './chosen/2021_Annual_Summary.xls', './chosen/2018_Annual_Summary.xls', 
    # './chosen/2016_Annual_Summary.xls', './chosen/2020_Annual_Summary.xls', 
    # './chosen/2019_Annual_Summary.xls']


def summarize_column_dist(column_summaries):
    has_missing_columns =  [k for k,x in column_summaries.items() if x['not_found']!=[]]
    print(f'Files with missing columns {has_missing_columns}')
    has_unexpected_columns =  [k for k,x in column_summaries.items() if x['unexpected']!=[]]
    print(f'Files with unexpected columns {has_unexpected_columns}')
    has_renamed_columns =  [k for k,x in column_summaries.items() if x['renamed']!=[]]
    print(f'Files with renamed columns {has_renamed_columns}')
    return has_missing_columns, has_unexpected_columns, has_renamed_columns