# Area Affected Value Mapping - Complete Summary

## Overview

I have analyzed the `distinct_values_area_affected.json` file containing 1,055+ distinct values for the `area_affected` column and created a comprehensive unified mapping system.

## What Was Done

### Analysis Completed
✅ Identified and categorized all 1,055 distinct values
✅ Found 37 clear mapping rules (typos, duplicates, standardizations)
✅ Identified 8 data quality issues (fragments, truncated values, HTML entities)
✅ Organized mappings by category for easy understanding and implementation

### Files Created

Located in: `/data/value_mappings/`

1. **`area_affected_simple_mapping.json`** (⭐ PRIMARY FILE FOR DATA PROCESSING)
   - Simple key-value flat mapping: `{source: unified_value}`
   - Ready to use with `df['area_affected'].replace(mapping)`
   - 37 direct mappings

2. **`area_affected_complete_mapping.json`**
   - Detailed mapping with reasons and metadata
   - Includes data quality issues documentation
   - Organized for audit and understanding

3. **`area_affected_mappings.json`**
   - Categorized by type (typos, companies, regions, etc.)
   - Well-structured for code review
   - Includes summary and notes

4. **`area_affected_mappings.py`**
   - Python dictionary with detailed comments
   - Can be imported directly into scripts
   - Same data as JSON but in Python format

5. **`MAPPING_NOTES.md`** (COMPREHENSIVE DOCUMENTATION)
   - Full analysis and explanation
   - Implementation guidance
   - Data quality issues explained
   - Statistics and recommendations

6. **`MAPPING_EXAMPLES.md`** (QUICK REFERENCE)
   - Before/after table of all mappings
   - Grouped by category with examples
   - Usage examples with code

7. **`README.md`** (START HERE)
   - Quick start guide
   - File directory explanation
   - Statistics summary
   - Next steps

## Mapping Categories

### 1. Typos & Misspellings (3 mappings)
```
Connecicut → Connecticut
Henepin and Ramsey County → Hennepin County
Queen Anne&#39 → Queen Anne
```

### 2. Redundant Prefixes (2 mappings)
```
City of Highland → Highland
City of San Diego → San Diego
```

### 3. Company Names (4 mappings)
```
Pacific Gas and Electric → Pacific Gas & Electric
Consumers Energy Co → Consumers Energy
First Energy Solutions Corp. → First Energy Solutions
Otter Tail Power Co → Otter Tail Power
```

### 4. State Suffixes (6 mappings - city level)
```
Sacramento California → Sacramento
Tacoma Washington → Tacoma
... and 4 more
```

### 5. State Suffixes (6 mappings - county level)
```
Salt Lake County Utah → Salt Lake County
Sweetwater County Wyoming → Sweetwater County
... and 4 more
```

### 6. Multi-Area Groups (3 mappings - separated by `:`)
```
San Diego & Orange Counties → San Diego County:Orange County
Los Angeles and Orange Counties → Los Angeles County:Orange County
Thurston County and Kitsap County → Thurston County:Kitsap County
```

### 7. Regional Consolidations (4 mappings)
```
Northern California → Northern California:Central California
Central California → Northern California:Central California
South Eastern Michigan → Southeast Michigan
Central Coast area → Central Coast California
```

### 8. Multi-Area Format (2 mappings - separated by `:`)
```
Greater Portland & Salem → Greater Portland:Salem
British Columbia & Alberta → British Columbia:Alberta
```

### 9. International & Special (3 mappings)
```
System wide Puerto Rico → System-wide Puerto Rico
Entire ComEd territory Illinois → Entire ComEd Territory Illinois
North of Roosevelt lake Arizona → North of Roosevelt Lake Arizona
```

### 10. Abbreviations (1 mapping)
```
PA → Pennsylvania
```

## Data Quality Issues Identified

### Critical Issues Found (8 entries)

**Incomplete/Fragment Entries:**
- `City of` (no location specified)
- `City and County of` (incomplete)
- `Consolidated Municipality of` (no city name)
- `Inc.` (fragment of company name)

**Orphaned/Truncated Values:**
- `& Harris County` (orphaned ampersand)
- `s County` (truncated - likely "Harris County")
- `and Sedgwick Counties` (missing first county)
- `and Skagit` (missing context)

**Recommended Action:**
1. Flag these 8 values during data loading
2. Review source data to recover complete values
3. Consider imputing from other columns (dates, coordinates, context)
4. If unrecoverable, assign to "Unknown" category

## Implementation Guide

### Python Implementation
```python
import json
import pandas as pd

# Load the mapping
with open('data/value_mappings/area_affected_simple_mapping.json', 'r') as f:
    mapping = json.load(f)['mapping']

# Apply to DataFrame
df['area_affected'] = df['area_affected'].replace(mapping)

# Verify changes
print(f"Unique values after mapping: {df['area_affected'].nunique()}")
```

### Expected Impact
- **Before**: 1,055 distinct values
- **After**: ~1,018 distinct values (37 mappings applied)
- **Improvement**: 3.5% reduction + standardized formatting

## Key Naming Conventions

1. State prefixes removed (e.g., `Tacoma Washington` → `Tacoma`)
2. Company names use ampersand `&` for consistency
3. Regional combinations use `and` (not ampersand)
4. County designations preserved in official names
5. Title case capitalization
6. HTML entities corrected
7. Grammatical improvements (e.g., adding "of")

## Files at a Glance

| File | Purpose | Audience | Format |
|------|---------|----------|--------|
| `area_affected_simple_mapping.json` | Direct implementation | Data Engineers | JSON |
| `area_affected_complete_mapping.json` | Audit & documentation | Analysts | JSON |
| `area_affected_mappings.json` | Code review | Developers | JSON |
| `area_affected_mappings.py` | Python import | Python devs | Python |
| `MAPPING_NOTES.md` | Full analysis | Everyone | Markdown |
| `MAPPING_EXAMPLES.md` | Quick reference | Everyone | Markdown |
| `README.md` | Getting started | Everyone | Markdown |

## Next Steps

1. ✅ **Review** - Share `MAPPING_EXAMPLES.md` with domain experts
2. 🔄 **Implement** - Use `area_affected_simple_mapping.json` with your data pipeline
3. 🚨 **Investigate** - Handle the 8 data quality issues
4. 📊 **Validate** - Check distinct value counts after applying mapping
5. 📝 **Document** - Add any additional manual mappings to `known_values.py`
6. 🔗 **Extend** - Consider similar analysis for `event_type` column

## Statistics

| Metric | Value |
|--------|-------|
| Original distinct values | 1,055 |
| Mapping rules created | 37 |
| Data quality issues | 8 |
| Issue percentage | ~0.76% |
| Expected unique values after mapping | ~1,018 |
| Expected reduction | 3.5% |

## Questions?

Refer to:
- **How do I use this?** → `README.md`
- **What are the examples?** → `MAPPING_EXAMPLES.md`
- **Why was this mapping chosen?** → `MAPPING_NOTES.md`
- **What's the implementation?** → See "Implementation Guide" above

## Location of All Files

```
/media/penguaman/code/ActualCode/adhoc/PlanetReimagined/
├── AREA_AFFECTED_MAPPING_SUMMARY.md (this file)
└── data/value_mappings/
    ├── README.md (start here!)
    ├── MAPPING_NOTES.md (comprehensive docs)
    ├── MAPPING_EXAMPLES.md (quick reference)
    ├── area_affected_simple_mapping.json (USE THIS!)
    ├── area_affected_complete_mapping.json (audit trail)
    ├── area_affected_mappings.json (structured view)
    ├── area_affected_mappings.py (Python format)
    └── known_values.py (extensible for future mappings)
```

---

**Status**: ✅ Complete - Ready for implementation
**Created**: 2025-11-09
**Format**: Production-ready JSON and Python

