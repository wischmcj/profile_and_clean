# Mapping of area_affected values to unified names
# Structure: unified_name -> [source_values]
# All source values are from distinct_values_area_affected.json
# Multi-area unified names use ':' as separator (e.g., 'Northern California:Central California')

area_affected_unified_mapping = {
    # ========== typos and misspellings ==========
    "connecticut": [
        "connecicut",  # typo: missing 'ut'
    ],
    
    "hennepin county": [
        "henepin and ramsey county",  # typo: "henepin" should be "hennepin"; also separates ramsey
    ],
    
    "queen anne": [
        "queen anneand#39",  # html entity error
    ],
    
    # ========== city prefixes (city of x -> x) ==========
    "highland": [
        "city of highland",
    ],
    
    "san diego": [
        "city of san diego",
    ],
    
    # ========== company/utility names ==========
    "pacific gas and electric": [
        "pacific gas and electric",
        "pacific gas and electric co",
    ],
    
    "consumers energy": [
        "consumers energy co",
    ],
    
    "first energy solutions": [
        "first energy solutions corp.",
    ],
    
    "otter tail power": [
        "otter tail power co",
    ],
    
    # ========== state/regional variations ==========
    "washington": [
        "washington state",
    ],
    
    # ========== city variations (with state added) ==========
    "sacramento": [
        "sacramento california",
    ],
    
    "tacoma": [
        "tacoma washington",
    ],
    
    "daytona beach": [
        "daytona beach florida",
    ],
    
    "medford": [
        "medford oregon",
    ],
    
    "idaho falls": [
        "idaho falls area idaho",
    ],
    
    # ========== county with state suffix ==========
    "salt lake county": [
        "salt lake county utah",
    ],
    
    "sweetwater county": [
        "sweetwater county wyoming",
    ],
    
    "prince george's county": [
        "prince george's county maryland",
    ],
    
    "new castle county": [
        "new castle delaware",
    ],
    
    "niagara county": [
        "niagara county new york",
    ],
    
    "hillsborough county": [
        "hillsborough county florida",
    ],
    
    # ========== multi-area groups (separated by colon) ==========
    "thurston county:kitsap county": [
        "thurston county and kitsap county",
    ],
    
    "san diego county:orange county": [
        "san diego and orange county",
    ],
    
    "los angeles county:orange county": [
        "los angeles and orange county",
    ],
    
    # ========== multi-area regions (separated by colon) ==========
    "greater portland:salem": [
        "greater portland and salem",
    ],
    
    "northern california:cecountyntral california": [
        "northern california",
        "central california",
    ],
    
    # ========== international regions ==========
    "british columbia:alberta": [
        "british columbia and alberta",
    ],
    
    # ========== multi-area regional combinations ==========
    "boston:southeast massachusetts": [
        "boston area and southeast massachusetts",
    ],
    
    # ========== capitalization and format fixes ==========
    "lower peninsula of michigan": [
        "entire lower peninsula michigan",
    ],
    
    "entire comed territory illinois": [
        "entire comed territory illinois",  # capitalization
    ],
    
    "north of roosevelt lake arizona": [
        "north of roosevelt lake arizona",  # capitalization
    ],
    
    # ========== state abbreviations ==========
    "pennsylvania": [
        "pa",
    ],
}

# ========== data quality issues ==========
# the following entries from distinct_values_area_affected.json appear to be data errors:
# 
# incomplete/fragment entries:
#   - "city of" (no location specified)
#   - "city and county of" (incomplete)
#   - "consolidated municipality of" (no city name)
#   - "inc." (fragment of company name)
#
# orphaned/truncated values:
#   - "and harris county" (orphaned ampersand)
#   - "s county" (truncated - likely "harris county")
#   - "and sedgwick county" (missing first county)
#   - "and skagit" (missing context)
#
# recommendation: flag and investigate these 8 values before applying the mapping.
