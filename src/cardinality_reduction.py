from value_mappings.area_affected_mappings import area_affected_unified_mapping
from config import substitute_lists


import re
import pandas as pd

from value_mappings.event_type_categories import EVENT_TYPE_CATEGORIES

def add_qualifier_to_county_names(series):
    """
    Replace substrings of the form '<region1> and <region2> county'
    with '<region1> county:<region2> county' in a pandas Series.
    Handles general 'X and Y county' or 'X county and Y county'.

    Examples:
      "henepin and ramsey county" -> "henepin county:ramsey county"
      "san diego and orange county" -> "san diego county:orange county"
      "king county and pierce county" -> "king county:pierce county"
    """
    def _replace(text):
        if not isinstance(text, str):
            return text

        # Handles types like "A and B county"
        # e.g. "henepin and ramsey county" -> "henepin county:ramsey county"
        pat1 = re.compile(r'^\s*(.+?)\s+and\s+(.+?)\s+county\s*$', re.IGNORECASE)
        m1 = pat1.match(text)
        if m1:
            part1 = m1.group(1).strip()
            part2 = m1.group(2).strip()
            return f"{part1} county:{part2} county"

        # Handles types like "A county and B county"
        # e.g. "king county and pierce county" -> "king county:pierce county"
        pat2 = re.compile(r'^\s*(.+? county)\s+and\s+(.+? county)\s*$', re.IGNORECASE)
        m2 = pat2.match(text)
        if m2:
            return f"{m2.group(1).strip()}:{m2.group(2).strip()}"
        
        # Handles types like "A county and B" (just in case)
        pat3 = re.compile(r'^\s*(.+? county)\s+and\s+(.+?)\s*$', re.IGNORECASE)
        m3 = pat3.match(text)
        if m3:
            return f"{m3.group(1).strip()}:{m3.group(2).strip()}"

        return text

    return series.apply(_replace)

def remove_special_symbols_and_numbers(series):
    """
    Removes all special symbols and numbers except ':' from strings in a pandas Series.
    Leaves only alphabetic characters, whitespace, and colons.
    Args:
        series (pd.Series): Series of strings.
    Returns:
        pd.Series: Series with special symbols and numbers removed (except ':').
    """
    def _clean(text):
        if not isinstance(text, str):
            return text
        # Remove all non-letter, non-whitespace, and non-colon characters
        return re.sub(r'[^a-zA-Z\s:]', '', text)
    return series.apply(_clean)


def standardize_area_affected(series):
    """
    Standardizes the values in a pandas Series using the area_affected_mappings.
    Any value found in the mapping is replaced with the unified name.
    Args:
        series (pd.Series): Series of values to standardize.
    Returns:
        pd.Series: Standardized series.
    """
    # Build reverse lookup: source_value -> unified_name
    reverse_mapping = dict()
    for unified, sources in area_affected_unified_mapping.items():
        for src in sources:
            reverse_mapping[src.lower()] = unified

    def _standardize(val):
        if not isinstance(val, str):
            return val
        lval = val.lower()
        return reverse_mapping.get(lval, val)

    return series.apply(_standardize)

def add_event_category_column(df):
    """
    Adds an 'event_category' column to the DataFrame, mapping from the 'event_type' column
    using data/value_mappings/event_type_categories.py.

    Args:
        df (pd.DataFrame): The DataFrame containing an 'event_type' column.

    Returns:
        pd.DataFrame: DataFrame with new 'event_category' column.
    """
    def _map_category(event_type):
        for category, events in EVENT_TYPE_CATEGORIES.items():
            if any([event in event_type for event in events]):
                return category
        return "unknown"
    # Apply category mapping to create the new column
    df['event_category'] = df['event_type'].apply(_map_category)

  