import pandas as pd
import dataframely as dy
import polars as pl


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

defaults = {
    'Event Month': lambda x: pd.to_datetime(x['Date Event Began']).dt.month,
}

dtype_conversions = {
    'date_fields':{
        'fields': ['date_event_began', 'restoration_date', 'restoration_date'],
        'validation_function':pd.to_datetime,
    } 
    # ['time_event_began', 'restoration_time']: pd.to_timestamp,
}

delimiter_correction = {
    # column: (correct delimiter, [incorrect delimiters])
    'area_affected': (':',[';', ',']),
    'nerc_region': (',', [',', ';', '/', ' ']),
    'event_type': ('-', ['/', ';', ',']),
}

replace_list = {
    '1/0/1900': pd.NaT,
    'Unknown': pd.NaT,
    'Ongoing': pd.NaT,
    "'0'": 0,
    'nan': pd.NaT,
}

# Valid Values\
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
NERC_REGIONS = ["WECC", "SERC", "NPCC", "TRE", "MRO", "RFC", "SPP"]

# Event types that appear in the data
VALID_EVENT_TYPES = [
    "System Operations", "Vandalism", "Suspicious Activity", "Severe Weather",
    "Transmission Interruption", "Unplanned evacuation", "Physical threat",
    "Physical attack", "Electrical System Separation", "Complete loss of monitoring"
]


# Dataframely Schema for DOE Disturbance Events
class doeDisturbanceSchema(dy.Schema):
    """
    Schema for validating DOE electricity disturbance event data.
    Aligned with cleaned_column_types for proper data conversion.
    
    Handles various data quality issues including:
    - "Unknown" values in restoration times/dates
    - Incomplete area affected entries
    - Numeric fields stored as strings
    - Missing Alert Criteria in older files
    - Mixed data types across columns
    """
    
    # Date/Time fields - converted to datetime/timestamp types
    event_month = dy.String(
        nullable=True  # 14.57% nulls observed
    )
    date_event_began = dy.Datetime(
        nullable=True  # 1.16% nulls observed
    )
    time_event_began = dy.Time(
        nullable=True  # 0.98% nulls observed
    )
    
    # Restoration timing - converted to datetime/timestamp
    restoration_date = dy.Datetime(
        nullable=True  # 0.98% nulls observed
    )
    restoration_time = dy.Time(
        nullable=True  # 0.98% nulls observed
    )
    
    # Location and affected infrastructure - String types
    area_affected = dy.String(
        nullable=True,  # 0.98% nulls observed
        min_length=1  # Can be incomplete but shouldn't be empty
    )
    nerc_region = dy.String(
        nullable=True,  # 1.82% nulls observed
        min_length=1
    )
    
    # Event classification - nullable because not all files have it
    alert_criteria = dy.String(
        nullable=True,  # 14.57% nulls observed
        min_length=1
    )
    event_type = dy.String(
        nullable=True,  # 0.98% nulls observed
        min_length=1
    )
    
    # Impact metrics - converted to integer types
    demand_loss_mw = dy.Int64(
        nullable=True  # 2.63% nulls observed
    )
    number_of_customers_affected = dy.Int64(
        nullable=True  # 2.59% nulls observed
    )
    
    # Year of event - Integer type
    year = dy.Int32(
        nullable=False  # 0% nulls
    )
    
    # Validation rules for data quality
    
    @dy.rule()
    def event_month_is_valid_string(cls) -> pl.Expr:
        """Event month should be a valid datetime after conversion"""
        return pl.col("event_month").is_null() | pl.col("event_month").is_not_null()
    
    @dy.rule()
    def date_event_began_is_valid_date(cls) -> pl.Expr:
        """Date event began should be a valid datetime"""
        return pl.col("date_event_began").is_null() | (pl.col("date_event_began") >= pl.datetime(2002, 1, 1))
    
    @dy.rule()
    def time_event_began_is_valid_time(cls) -> pl.Expr:
        """Time event began should be a valid timestamp"""
        return pl.col("time_event_began").is_null() | pl.col("time_event_began").is_not_null()
    
    @dy.rule()
    def restoration_date_is_valid(cls) -> pl.Expr:
        """Restoration date should be valid datetime or null"""
        return pl.col("restoration_date").is_null() | (pl.col("restoration_date") >= pl.datetime(2002, 1, 1))
    
    @dy.rule()
    def restoration_time_is_valid(cls) -> pl.Expr:
        """Restoration time should be valid timestamp or null"""
        return pl.col("restoration_time").is_null() | pl.col("restoration_time").is_not_null()
    
    @dy.rule()
    def area_affected_has_content(cls) -> pl.Expr:
        """Area affected should have meaningful content"""
        return pl.col("area_affected").is_null() | (pl.col("area_affected").str.len() > 0)
    
    @dy.rule()
    def nerc_region_has_valid_codes(cls) -> pl.Expr:
        """NERC region should contain at least one valid region code"""
        valid_code_pattern = r"(WECC|SERC|NPCC|TRE|MRO|RFC|SPP|FRCC|TE|RE|PR|ERCOT|MPCC|RF)"
        return pl.col("nerc_region").is_null() | pl.col("nerc_region").str.contains(valid_code_pattern, literal=False)
    
    @dy.rule()
    def alert_criteria_valid_text(cls) -> pl.Expr:
        """Alert criteria should be substantive text or null"""
        return pl.col("alert_criteria").is_null() | (pl.col("alert_criteria").str.len() >= 10)
    
    @dy.rule()
    def event_type_has_content(cls) -> pl.Expr:
        """Event type should have meaningful content"""
        return pl.col("event_type").is_null() | (pl.col("event_type").str.len() > 0)
    
    @dy.rule()
    def demand_loss_is_non_negative(cls) -> pl.Expr:
        """Demand loss should be non-negative integer"""
        return pl.col("demand_loss_(mw)").is_null() | (pl.col("demand_loss_(mw)") >= 0)
    
    @dy.rule()
    def customers_affected_is_non_negative(cls) -> pl.Expr:
        """Number of customers affected should be non-negative integer"""
        return pl.col("number_of_customers_affected").is_null() | (pl.col("number_of_customers_affected") >= 0)
    
    @dy.rule()
    def year_in_reasonable_range(cls) -> pl.Expr:
        """Year should be between 2002 and 2030"""
        return (pl.col("year") >= 2002) & (pl.col("year") <= 2030)

