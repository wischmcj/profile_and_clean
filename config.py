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
    'alert_criteria': ('\n', ['\n', ';', ',']),
    'demand_loss_(mw)': ('', ['', ';', ',']),
    'number_of_customers_affected': ('', ['', ';', ',']),
}

nullify_list = {
    '1/0/1900',
    'Unknown',
    'Ongoing'
}

# Valid Values\
cleaned_columns = ['event_month', 'date_event_began', 'time_event_began', 'restoration_date', 'restoration_time', 
                    'area_affected', 'nerc_region', 'alert_criteria', 'event_type', 
                    'demand_loss_(mw)', 'number_of_customers_affected', 'year']

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
    Handles various data quality issues including:
    - "Unknown" values in restoration times/dates
    - Incomplete area affected entries
    - Numeric fields stored as strings
    - Missing Alert Criteria in older files
    """
    
    # Event timing - core required fields
    event_month = dy.String(
        nullable=False, 
        min_length=1,
        max_length=20
    )
    date_event_began = dy.String(
        nullable=False,
        min_length=8  # MM/DD/YYYY minimum
    )
    time_event_began = dy.String(
        nullable=False,
        min_length=8  # HH:MM:SS minimum
    )
    
    # Restoration timing - can have "Unknown" values
    restoration_date = dy.String(
        nullable=False,
        min_length=1
    )
    restoration_time = dy.String(
        nullable=False,
        min_length=1
    )
    
    # Location and affected infrastructure
    area_affected = dy.String(
        nullable=False,
        min_length=1  # Can be incomplete but shouldn't be empty
    )
    nerc_region = dy.String(
        nullable=False,
        min_length=2,
        max_length=4
    )
    
    # Event classification - nullable because not all files have it
    alert_criteria = dy.String(
        nullable=True,
        min_length=1
    )
    event_type = dy.String(
        nullable=False,
        min_length=1,
        max_length=100
    )
    
    # Impact metrics - stored as strings but should be numeric
    demand_loss_mw = dy.String(
        nullable=False,
        min_length=1
    )
    number_of_customers_affected = dy.String(
        nullable=False,
        min_length=1
    )
    
    # Year of event
    year = dy.Int32(
        nullable=False
    )
    
    # Validation rules for data quality
    
    @dy.rule()
    def valid_month_name(cls) -> pl.Expr:
        """Event month should be a valid month name"""
        valid_months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        return pl.col("event_month").is_in(valid_months)
    
    @dy.rule()
    def valid_nerc_region(cls) -> pl.Expr:
        """NERC region should be one of the known regions"""
        return pl.col("nerc_region").is_in(NERC_REGIONS)
    
    @dy.rule()
    def restoration_date_valid_or_unknown(cls) -> pl.Expr:
        """Restoration date should be either a valid date pattern or 'Unknown'"""
        # Allow "Unknown" or strings matching date patterns
        return (
            (pl.col("restoration_date").str.contains(r"^\d{1,2}/\d{1,2}/\d{4}$")) |
            (pl.col("restoration_date") == "Unknown")
        )
    
    @dy.rule()
    def restoration_time_valid_or_unknown(cls) -> pl.Expr:
        """Restoration time should be either a valid time pattern or 'Unknown'"""
        # Allow "Unknown" or strings matching time patterns (HH:MM:SS)
        return (
            (pl.col("restoration_time").str.contains(r"^\d{1,2}:\d{2}:\d{2}$")) |
            (pl.col("restoration_time") == "Unknown")
        )
    
    @dy.rule()
    def demand_loss_is_numeric(cls) -> pl.Expr:
        """Demand loss should be a valid number (even if stored as string)"""
        # Should be parseable as a number or be "0"
        return (
            pl.col("demand_loss_mw").str.to_integer().is_not_null() |
            (pl.col("demand_loss_mw") == "0")
        )
    
    @dy.rule()
    def customers_affected_is_numeric(cls) -> pl.Expr:
        """Number of customers affected should be a valid number"""
        # Should be parseable as a number or be "0"
        return (
            pl.col("number_of_customers_affected").str.to_integer().is_not_null() |
            (pl.col("number_of_customers_affected") == "0")
        )
    
    @dy.rule()
    def year_in_reasonable_range(cls) -> pl.Expr:
        """Year should be between 2002 and current time"""
        return (pl.col("year") >= 2002) & (pl.col("year") <= 2030)