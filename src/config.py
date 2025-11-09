import pandas as pd
import dataframely as dy
import polars as pl

##### STANDARDIZATION CONFIGS ####

# These value are used to map differently named, but 
# #  sementically equivalent columns to common column names
# Format:
# 'column_name': [
#     'alternative_column_name',
#     'alternative_column_name', ...
# ]
col_name_correction = {
    # These have alternative names in our sample
    'Event Type': [],
    'Demand Loss (MW)': [],
    # 'Restoration': [],
    'Alert Criteria':[],

    'Restoration Time': [
        'Time of Restoration',
    ],
    'Restoration Date': [
        'Date of Restoration',
    ],

    'Area Affected': [
        'Area', ],
    'NERC Region': [
        ' NERC Region'],
    'Number of Customers Affected': [
        'Number of Customers Affected 1[1]', 
        'Number of Customers Affected 1'],
    'Event Month': [ 
        'Month'],
    'Time Event Began': [ 
        'Time'],
    'Date Event Began': [ 
        'Date'],

    # Custom Fields 
    'year':[],
}

# These values are used to standardise the delimiters in a string
# Format:
# 'column_name': (correct delimiter, [incorrect delimiters])
delimiter_correction = {
    'area_affected': (':',[';', ',']),
    'nerc_region': (',', [',', ';', '/', ' ']),
    'event_type': ('-', ['/', ';', ',']),

}

# These values wholy replace the current value where appropriate
# format:
# 'column_name': {
#     'value_to_replace': 'value_to_replace_with',
#     'value_to_replace': 'value_to_replace_with', 
replace_list = {
    '1/0/1900': pd.NaT,
    'unknown': pd.NaT,
    'ongoing': pd.NaT,
    "'0'": 0,
    'nan': pd.NaT,
}

# These values are used to repalce values within a string with a more standard value
# format:
# 'column_name': {
#     'value_to_replace_with': [
#         'value_to_replace',
#         'value_to_replace', ...
substitute_lists = {
    'affected_areas': {
        '':[
            'city of',
            'city and county of',
            'consolidated municipality of',
            'corp.',
            'co.',
            'inc.',
            'state of',
            'state',
            'system-wide',
            'systemwide',
            'system wide',
            'entire',
            '.'
        ],
        # ' ':[
        #     ' area',
        # ],
        ':': [
            ' and',
            '&',
        ],
        'south east': [
            'south east',
            'southeast',
            'south eastern',
            'south-eastern',
        ],
        'north east': [
            'north east',
            'northeast',
            'north eastern',
            'north-eastern',
        ],
        'north west': [
            'north west',
            'northwest',
            'north western',
            'north-western',
        ],
        'south west': [
            'south west',
            'southwest',
            'south western',
            'south-western',
        ],
        'county': [
            'counties',
        ],
    },
    'event_type': {
        'natural disaster': [
            'natural disaster',
            'natural disaster (weather)',
            'natural disaster (weather related)',
            'natural disaster (weather-related)',
            'natural disaster (weather-related)',
            'natural disaster or weather',
            'natural disaster or weather related',
            'natural disaster or weather-related',
            'natural disaster or weather-related',
        ],
        'emergency': [
            'emergencies',
        ],
        'failure': [
            'Fault'
        ],
        '':[
            'of',
            '100',
            '+',
            'MW',
        ]
    },
    'nerc_region': {
        'npcc': [
            'mpcc'
        ],
        'mro': [
            'mro',
        ],
        'rf': [ 
            'rfc',
        ],
        'serc': [
            "serc",
        ],
        'wecc': [
            "wecc"
        ],
        're':[
            'tre',
            'texas re',
        ]
    },
}



##### END STATE VALUE LISTS ####

# Valid Values
cleaned_columns = ['event_month', 'date_event_began', 'time_event_began', 'restoration_date', 'restoration_time', 
                    'area_affected', 'nerc_region', 'alert_criteria', 'event_type', 
                    'demand_loss_(mw)', 'number_of_customers_affected', 'year']
# INSERT_YOUR_CODE
# List of datatypes for cleaned_columns, in order
cleaned_column_types = {
        "event_month": "string",
        "date_event_began": "datetime",
        "time_event_began": "timestamp",
        "restoration_date": "datetime",
        "restoration_time": "timestamp",
        "area_affected": "string",
        "nerc_region": "string",
        "alert_criteria": "string",  # nullable
        "event_type": "string",
        "demand_loss_(mw)": "integer",
        "number_of_customers_affected": "integer",
        "year": "integer"
    }


months_of_year = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december"
]

# Valid NERC regions
NERC_REGIONS = ["wecc", "serc", "npcc", "tre", "mro", "rfc", "spp"]

# Event types that appear in the data
VALID_EVENT_TYPES = [
    "system operations", "vandalism", "suspicious activity", "severe weather",
    "transmission interruption", "unplanned evacuation", "physical threat",
    "physical attack", "electrical system separation", "complete loss of monitoring"
]

# INSERT_YOUR_CODE
# List of all 50 U.S. states
US_STATES_TERRITORIES = [
    "alaska", "american samoa", "arizona", "arkansas", "california",
    "colorado", "connecticut", "delaware", "district of columbia", "florida",
    "georgia", "guam", "hawaii", "idaho", "illinois", "indiana", "iowa",
    "kansas", "kentucky", "louisiana", "maine", "marshall islands", "maryland",
    "massachusetts", "michigan", "minnesota", "mississippi", "missouri",
    "montana", "nebraska", "nevada", "new hampshire", "new jersey",
    "new mexico", "new york", "north carolina", "north dakota", "ohio",
    "oklahoma", "oregon", "palau", "pennsylvania", "puerto rico", "rhode island",
    "south carolina", "south dakota", "tennessee", "texas", "utah", "vermont",
    "virginia", "washington", "west virginia", "wisconsin", "wyoming"
]


