# Area Affected Mapping Implementation Guide

## Overview

Complete unified mapping system for the `area_affected` column in the dataset.

**Status**: ✅ Ready to implement  
**Source**: All source values verified from `distinct_values_area_affected.json`  
**Mappings**: 38 unified names from 47 source values  

## Quick Facts

| Metric | Value |
|--------|-------|
| Original distinct values | 1,055 |
| Source values mapped | 47 |
| Unified names created | 38 |
| Single-area mappings | 25 |
| Multi-area mappings | 13 |
| Data quality issues flagged | 8 |
| Implementation files | 3 formats (JSON, Python, docs) |

## File Structure

```
data/value_mappings/
├── area_affected_unified_mapping.json  ← PRIMARY FILE
├── area_affected_simple_mapping.json   (alternative format)
├── area_affected_mappings.py           (Python dict)
│
├── QUICK_START.md                      ← START HERE
├── USAGE_GUIDE.md                      (detailed docs)
├── MAPPING_CORRECTED_SUMMARY.md        (full reference)
├── MAPPING_EXAMPLES.md                 (before/after examples)
│
└── README.md                           (file directory)
```

## Mapping Format

**Structure**: `unified_area_name → [source_values]`

### Single Area (Simple Replacement)
```json
"Connecticut": ["Connecicut"]
```
One source value maps to one unified name.

### Multiple Source Values (Consolidation)
```json
"Pacific Gas & Electric": ["Pacific Gas and Electric", "Pacific Gas and Electric Co"]
```
Multiple source values representing the same entity consolidate to one name.

### Multi-Area Regions (Colon-Separated)
```json
"Northern California:Central California": ["Northern California", "Central California"]
```
Two distinct areas represented as `area1:area2`.

### Multi-Area from Single Source
```json
"Boston:Southeast Massachusetts": ["Boston area and Southeast Massachusetts"]
```
A source value representing multiple areas maps to colon-separated format.

## Implementation Steps

### 1. Load the Mapping

```python
import json
import pandas as pd

# Load primary mapping file
with open('data/value_mappings/area_affected_unified_mapping.json', 'r') as f:
    mapping_data = json.load(f)
    unified_mapping = mapping_data['unified_mappings']
    data_quality_issues = mapping_data['data_quality_issues']
```

### 2. Create Reverse Mapping

```python
# Convert from unified -> [sources] to sources -> unified
reverse_mapping = {}
for unified_name, source_values in unified_mapping.items():
    for source_value in source_values:
        reverse_mapping[source_value] = unified_name
```

### 3. Handle Data Quality Issues (Optional but Recommended)

```python
# Identify problematic values before mapping
all_issues = (
    data_quality_issues['fragments_incomplete'] + 
    data_quality_issues['orphaned_truncated']
)

issues_in_data = df[df['area_affected'].isin(all_issues)]
print(f"Found {len(issues_in_data)} records with data quality issues:")
print(issues_in_data['area_affected'].value_counts())

# You can handle these separately:
# df.loc[issues_in_data.index, 'area_affected'] = 'UNKNOWN'
```

### 4. Apply Mapping

```python
# Apply the reverse mapping
df['area_affected_unified'] = df['area_affected'].map(reverse_mapping)

# Keep original values that don't have a mapping
df['area_affected_unified'] = df['area_affected_unified'].fillna(df['area_affected'])
```

### 5. Validate

```python
# Count reduction
print(f"Original unique values: {df['area_affected'].nunique()}")
print(f"After mapping: {df['area_affected_unified'].nunique()}")

# Check unmapped
unmapped = df[df['area_affected_unified'] == df['area_affected']]
print(f"Unmapped values: {len(unmapped)}")

# Check multi-area values
multi_area = df[df['area_affected_unified'].str.contains(':', na=False)]
print(f"Multi-area records: {len(multi_area)}")
print(multi_area['area_affected_unified'].value_counts())
```

## Understanding Multi-Area Values

### What They Are
Values with `:` separator represent **multiple distinct geographic areas** affected:

```
"Northern California:Central California"
```

This means both Northern California AND Central California are affected.

### How to Use Them

**Option 1: Keep as-is**
```python
# Use for regional analysis
df.groupby('area_affected_unified').size()
```

**Option 2: Split for per-area analysis**
```python
# Split into individual areas
df['areas'] = df['area_affected_unified'].str.split(':')

# Expand rows (one area per row)
df_expanded = df.explode('areas')

# Now analyze by individual area
df_expanded.groupby('areas').size()
```

## Data Quality Issues (8 Flagged)

### Problem Entries
```
"City of"                    ❌ No location
"City and County of"         ❌ Incomplete
"Consolidated Municipality of" ❌ No city name
"Inc."                       ❌ Fragment
"& Harris County"            ❌ Orphaned ampersand
"s County"                   ❌ Truncated
"and Sedgwick Counties"      ❌ Missing county
"and Skagit"                 ❌ Missing context
```

### Handling Options

**Option 1: Mark as Unknown**
```python
all_issues = [...list of 8 values...]
df.loc[df['area_affected'].isin(all_issues), 'area_affected_unified'] = 'UNKNOWN'
```

**Option 2: Investigate Source Data**
```python
# Find records with issues
issue_records = df[df['area_affected'].isin(all_issues)]
# Cross-reference with other columns (date, coordinates, etc.)
# Try to recover actual location
```

**Option 3: Filter Out**
```python
# Keep only clean records
clean_df = df[~df['area_affected'].isin(all_issues)]
```

## Code Examples

### Complete Pipeline Function
```python
def apply_area_affected_mapping(df, mapping_path='data/value_mappings/area_affected_unified_mapping.json'):
    """Apply area_affected unified mapping to DataFrame"""
    
    import json
    
    # Load mapping
    with open(mapping_path, 'r') as f:
        mapping_data = json.load(f)
        unified_mapping = mapping_data['unified_mappings']
        data_quality_issues = mapping_data['data_quality_issues']
    
    # Create reverse mapping
    reverse_mapping = {}
    for unified_name, sources in unified_mapping.items():
        for source in sources:
            reverse_mapping[source] = unified_name
    
    # Flag data quality issues
    all_issues = (
        data_quality_issues['fragments_incomplete'] +
        data_quality_issues['orphaned_truncated']
    )
    df['area_affected_has_issue'] = df['area_affected'].isin(all_issues)
    
    # Apply mapping
    df['area_affected_unified'] = df['area_affected'].map(reverse_mapping)
    df['area_affected_unified'] = df['area_affected_unified'].fillna(df['area_affected'])
    
    return df
```

### Usage
```python
df = apply_area_affected_mapping(df)

# Check results
print(df[['area_affected', 'area_affected_unified', 'area_affected_has_issue']].head(10))
```

## Files Location

Primary mapping files:
- `data/value_mappings/area_affected_unified_mapping.json`
- `data/value_mappings/area_affected_simple_mapping.json`
- `data/value_mappings/area_affected_mappings.py`

Documentation:
- `data/value_mappings/QUICK_START.md` - Quick reference
- `data/value_mappings/USAGE_GUIDE.md` - Detailed guide
- `data/value_mappings/MAPPING_EXAMPLES.md` - Before/after examples
- `data/value_mappings/MAPPING_CORRECTED_SUMMARY.md` - Full reference

## Verification Checklist

- ✅ All 47 source values verified from `distinct_values_area_affected.json`
- ✅ Mapping structure is correct: `unified_name -> [sources]`
- ✅ Multi-area values use `:` separator consistently
- ✅ 8 data quality issues identified and documented
- ✅ Implementation code examples provided
- ✅ Validation logic included

## What's Included in This Mapping

### Typos Fixed (3)
- Misspellings corrected
- HTML entities decoded

### Company Names Standardized (4)
- Format consistency (& vs "and")
- Abbreviation removal ("Co", "Corp.")

### Geographic Designations Standardized (18)
- Redundant state suffixes removed
- City prefixes removed
- Regional descriptors unified

### Multi-Area Representations (13)
- County pairs consolidated
- Regional combinations unified
- Colon-separated for clarity

## What's NOT Included

- Values flagged as data quality issues (8)
- Values with no identified duplicates or issues (~1,000)

These are intentionally left as-is for your review/decision.

## Next Actions

1. ✅ Review this guide
2. 🔄 Choose implementation approach (see "Code Examples")
3. 🔄 Apply to your data pipeline
4. 🔄 Validate with your team
5. 🔄 Handle data quality issues
6. 🔄 Consider similar mappings for other columns

---

**Questions?** See:
- Quick reference → `QUICK_START.md`
- Implementation details → `USAGE_GUIDE.md`
- Full documentation → `MAPPING_CORRECTED_SUMMARY.md`
- Before/after examples → `MAPPING_EXAMPLES.md`

**Status**: ✅ Complete and production-ready


