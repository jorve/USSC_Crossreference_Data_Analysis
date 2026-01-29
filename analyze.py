import csv
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from py import dict_legend as dl

# Configuration constants
LOWER_BOUND = 2002
UPPER_BOUND = 2024
DESIRED_STATUTE_PREFIX = "18922G"
# this list was developed by hand, examining the dataset for instances of statutes that are not relevant to the analysis, such as those that are not 18§922(g)(1) or those that are accompanied by 18§924(c) or 18§924(e).
UNDESIRED_STATUTE_PREFIXES = [
    "18924C", "18924E", "21", "181203", "181366", "18111", "182113A", "18751",
    "26", "8", "181951", "18371", "181512", "18876", "182113O", "182119",
    "182312", "181341", "181203", "181962", "181959", "181201", "18113",
    "181513", "18844", "18875", "18248", "181958", "181591", "181952",
    "181521", "181071", "1822", "18117", "1833"
]

# Cross-reference charge codes
CROSS_REF_CHARGES = ["2A1.1", "2A1.2", "2A1.3", "2A1.4", "2A1.5", "2A2.1", "2A2.2", "2A2.3"]

# Threshold for TOTPRISN
TOTPRISN_THRESHOLD = 120


def build_district_template() -> Dict[str, int]:
    """
    Build a zeroed district->count mapping.
    Precomputed once and copied per-year for efficiency.
    """
    template: Dict[str, int] = {}
    for code in range(97):
        district_name = dl.district_dict(str(code))
        if district_name != "Unknown":
            template[district_name] = 0
    return template


DISTRICT_TEMPLATE = build_district_template()

# this function is used to check if a list of strings has any items that start with any of the given prefixes. We are using it to filter out statutes that are not relevant to the analysis.
def has_prefix(items: List[str], prefixes: List[str]) -> bool:
    """
    Check if any item in the items list starts with any of the given prefixes.
    
    Args:
        items: List of strings to check
        prefixes: List of prefix strings to search for
        
    Returns:
        True if any item starts with any prefix, False otherwise
    """
    if not items or not prefixes:
        return False
    return any(item.startswith(prefix) for item in items for prefix in prefixes)


def initialize_year_data() -> Dict[str, Any]:
    """
    Initialize the data structure for a single year.
    
    Returns:
        Dictionary with initialized counters and structures
    """
    # Initialize district counts dictionary (copy precomputed template)
    district_counts = DISTRICT_TEMPLATE.copy()
    
    return {
        "STAT_18922G": 0,
        # Counts for all qualifying 18922G cases by district (regardless guideline)
        "18922G_District_Counts": district_counts.copy(),
        "GDSTATHI_2K2.1": {
            "Total": 0,
            "TOTPRISN_Sum": 0.0,
            "TOTPRISN_Count": 0,
            "Demographics": {
                "RACE": {},
                "HISPANIC": {},
                "DISTRICT": {},
                "EDUC": {},
                "CITIZEN": {}
            },
            # Track counts and sentencing averages by district for 2K2.1 without 2A
            "District_Counts": district_counts.copy(),
            "District_TOTPRISN": {}
        },
        "Total_Records": 0,
        "GDLINEHI_2A": {
            "Over_120_TOTPRISN_Count": 0,
            "Total": 0,
            "TOTPRISN_Sum": 0.0,
            "TOTPRISN_Count": 0,
            "Cross-Reference Charge": {charge: 0 for charge in CROSS_REF_CHARGES},
            "Demographics": {
                "RACE": {},
                "HISPANIC": {},
                "DISTRICT": {},
                "EDUC": {},
                "CITIZEN": {}
            },
            "District_TOTPRISN": {}  # per-district sum/count for 2A cross-reference cases
        },
        # District_Counts: counts for all filtered 18922G cases by district
        "District_Counts": district_counts.copy(),
        # All_District_Counts: explicit alias for clarity if needed elsewhere
        "All_District_Counts": district_counts.copy()
    }


def is_valid_totprisn(value: Optional[str]) -> bool:
    """
    Check if a TOTPRISN value is valid and non-empty.
    
    Args:
        value: TOTPRISN value to check
        
    Returns:
        True if value is valid, False otherwise
    """
    return value is not None and value != "" and value != " "

# the above and below functions are used to parse the TOTPRISN value to a float, because the USSC stores almost everything as strings. 
def parse_totprisn(value: Optional[str]) -> Optional[float]:
    """
    Parse TOTPRISN value to float.
    
    Args:
        value: TOTPRISN value to parse
        
    Returns:
        Parsed float value or None if invalid
    """
    if not is_valid_totprisn(value):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def increment_demographic(data: Dict[str, Any], category: str, key: str) -> None:
    """
    Increment a demographic counter.
    
    Args:
        data: Dictionary containing demographics
        category: Category name (e.g., "RACE", "HISPANIC")
        key: Key to increment
    """
    if key not in data[category]:
        data[category][key] = 1
    else:
        data[category][key] += 1


def process_record(record: Dict[str, Any], year_data: Dict[str, Any], year: int,
                   over120_records: Optional[List[Dict[str, Any]]] = None) -> None:
    """
    Process a single record and update year data.
    
    Args:
        record: Record dictionary to process
        year_data: Year data dictionary to update
        year: Year as integer
        over120_records: Optional list to collect records with TOTPRISN > 120
    """
    record["YEAR"] = year
    year_data["Total_Records"] += 1

    # Track all cases by district (before any statute filtering)
    dist_desc = record.get("DISTRICT_DESC")
    if dist_desc is not None and dist_desc in year_data["All_District_Counts"]:
        year_data["All_District_Counts"][dist_desc] += 1
    
    nwstat_list = record.get("NWSTAT_LIST", [])
    
    # Check if record matches desired statute criteria
    has_desired_statute = any(item.startswith(DESIRED_STATUTE_PREFIX) for item in nwstat_list)
    has_undesired_statute = has_prefix(nwstat_list, UNDESIRED_STATUTE_PREFIXES)
    
    if not (has_desired_statute and not has_undesired_statute):
        return
    
    year_data["STAT_18922G"] += 1
    
    # Track qualifying 18922G cases by district (regardless guideline)
    if dist_desc is not None and dist_desc in year_data["18922G_District_Counts"]:
        year_data["18922G_District_Counts"][dist_desc] += 1

    gdstathi = record.get("GDSTATHI", "")
    gdlinehi = record.get("GDLINEHI", "")
    
    # Process GDSTATHI_2K2.1 records
    if gdstathi == "2K2.1":
        year_data["GDSTATHI_2K2.1"]["Total"] += 1
        
        # Process records with 2K2.1 statutory guideline but not 2A cross reference guideline
        if not gdlinehi.startswith("2A"):
            totprisn = parse_totprisn(record.get("TOTPRISN"))
            # Track demographics for GDSTATHI_2K2.1
            demographics = year_data["GDSTATHI_2K2.1"]["Demographics"]
            race_desc = record.get("MONRACE_DESC")
            if race_desc is not None:
                increment_demographic(demographics, "RACE", race_desc)
            
            hispanic_desc = record.get("HISPORIG_DESC")
            if hispanic_desc is not None:
                increment_demographic(demographics, "HISPANIC", hispanic_desc)
            
            educ_desc = record.get("NEWEDUC_DESC")
            if educ_desc is not None:
                increment_demographic(demographics, "EDUC", educ_desc)
            
            citizen_desc = record.get("CITIZEN_DESC")
            if citizen_desc is not None:
                increment_demographic(demographics, "CITIZEN", citizen_desc)
            
            # Track district counts and TOTPRISN aggregates for GDSTATHI_2K2.1 (without 2A cross-reference)
            if dist_desc is not None and dist_desc in year_data["GDSTATHI_2K2.1"]["District_Counts"]:
                year_data["GDSTATHI_2K2.1"]["District_Counts"][dist_desc] += 1
                if totprisn is not None:
                    # Track for overall averages (GDSTATHI without 2A)
                    year_data["GDSTATHI_2K2.1"]["TOTPRISN_Sum"] += totprisn
                    year_data["GDSTATHI_2K2.1"]["TOTPRISN_Count"] += 1

                    district_totprisn = year_data["GDSTATHI_2K2.1"]["District_TOTPRISN"]
                    if dist_desc not in district_totprisn:
                        district_totprisn[dist_desc] = {"sum": 0.0, "count": 0}
                    district_totprisn[dist_desc]["sum"] += totprisn
                    district_totprisn[dist_desc]["count"] += 1
    
    # Process GDLINEHI_2A records
    if (gdlinehi.startswith("2A") and 
        gdstathi == "2K2.1" and 
        record.get("ACCAP") == "0"):
        
        year_data["GDLINEHI_2A"]["Total"] += 1
        
        # Update cross-reference charge count
        if gdlinehi in year_data["GDLINEHI_2A"]["Cross-Reference Charge"]:
            year_data["GDLINEHI_2A"]["Cross-Reference Charge"][gdlinehi] += 1
        
        # Process TOTPRISN
        totprisn = parse_totprisn(record.get("TOTPRISN"))
        if totprisn is not None:
            if totprisn > TOTPRISN_THRESHOLD:
                year_data["GDLINEHI_2A"]["Over_120_TOTPRISN_Count"] += 1
                # Collect records with TOTPRISN > 120
                if over120_records is not None:
                    # Create a copy of the record to avoid modifying the original
                    record_copy = record.copy()
                    over120_records.append(record_copy)
            
            # Store for average calculation (would need to track this separately)
            
            # Update district count and per-district TOTPRISN aggregates
            dist_desc = record.get("DISTRICT_DESC")
            if dist_desc is not None and dist_desc in year_data["District_Counts"]:
                year_data["District_Counts"][dist_desc] += 1
                # Track for overall averages (GDLINEHI 2A)
                year_data["GDLINEHI_2A"]["TOTPRISN_Sum"] += totprisn
                year_data["GDLINEHI_2A"]["TOTPRISN_Count"] += 1
                district_totprisn = year_data["GDLINEHI_2A"]["District_TOTPRISN"]
                if dist_desc not in district_totprisn:
                    district_totprisn[dist_desc] = {"sum": 0.0, "count": 0}
                district_totprisn[dist_desc]["sum"] += totprisn
                district_totprisn[dist_desc]["count"] += 1
        
        # Track demographics for GDLINEHI_2A
        demographics = year_data["GDLINEHI_2A"]["Demographics"]
        race_desc = record.get("MONRACE_DESC")
        if race_desc is not None:
            increment_demographic(demographics, "RACE", race_desc)
        
        hispanic_desc = record.get("HISPORIG_DESC")
        if hispanic_desc is not None:
            increment_demographic(demographics, "HISPANIC", hispanic_desc)
        
        educ_desc = record.get("NEWEDUC_DESC")
        if educ_desc is not None:
            increment_demographic(demographics, "EDUC", educ_desc)
        
        citizen_desc = record.get("CITIZEN_DESC")
        if citizen_desc is not None:
            increment_demographic(demographics, "CITIZEN", citizen_desc)


def calculate_averages(year_data: Dict[str, Any]) -> None:
    """
    Calculate and store average TOTPRISN values.
    
    Args:
        year_data: Year data dictionary to update
    """
    gdstathi_sum = year_data.get("GDSTATHI_2K2.1", {}).get("TOTPRISN_Sum", 0.0)
    gdstathi_count = year_data.get("GDSTATHI_2K2.1", {}).get("TOTPRISN_Count", 0)
    if gdstathi_count:
        year_data["GDSTATHI_Ex_2A_TOTPRISN_Avg"] = round(gdstathi_sum / gdstathi_count, 2)
    else:
        year_data["GDSTATHI_Ex_2A_TOTPRISN_Avg"] = 0

    gdlinehi_sum = year_data.get("GDLINEHI_2A", {}).get("TOTPRISN_Sum", 0.0)
    gdlinehi_count = year_data.get("GDLINEHI_2A", {}).get("TOTPRISN_Count", 0)
    if gdlinehi_count:
        year_data["GDLINEHI_2A_TOTPRISN_Avg"] = round(gdlinehi_sum / gdlinehi_count, 2)
    else:
        year_data["GDLINEHI_2A_TOTPRISN_Avg"] = 0


def calculate_percentage(year_data: Dict[str, Any]) -> None:
    """
    Calculate percentage of STAT_18922G records.
    
    Args:
        year_data: Year data dictionary to update
    """
    if year_data["Total_Records"] > 0:
        percentage = round(
            year_data["STAT_18922G"] / year_data["Total_Records"], 4
        ) * 100
        year_data["18922g1_%_of_total"] = f"{percentage}%"
    else:
        year_data["18922g1_%_of_total"] = "0%"


def process_year_data(json_path: str, year: int, tabbed_data: Dict[str, Any],
                      over120_records: Optional[List[Dict[str, Any]]] = None) -> None:
    """
    Process data for a single year.
    
    Args:
        json_path: Path to the JSON data file
        year: Year as integer
        tabbed_data: Dictionary to store all year data
        over120_records: Optional list to collect records with TOTPRISN > 120
    """
    year_str = str(year)
    tabbed_data[year_str] = initialize_year_data()
    year_data = tabbed_data[year_str]
    
    with open(json_path, "r", encoding="utf-8") as json_file:
        all_data = json.load(json_file)
        
        for record in all_data:
            process_record(record, year_data, year, over120_records)

    calculate_averages(year_data)
    calculate_percentage(year_data)


def export_yearly_summary(tabbed_data: Dict[str, Any], output_path: str) -> None:
    """
    Export yearly summary data to CSV.
    
    Args:
        tabbed_data: Dictionary containing all year data
        output_path: Path to output CSV file
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        "Year",
        "Total_Records",
        "STAT_18922G",
        "GDSTATHI_2K2.1_Total",
        "GDLINEHI_2A_Total",
        "GDSTATHI_Ex_2A_TOTPRISN_Avg",
        "GDLINEHI_2A_TOTPRISN_Avg",
        "Over_120_TOTPRISN_Count",
    ] + CROSS_REF_CHARGES
    
    with open(output_path, 'w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        
        for year in sorted(tabbed_data.keys(), key=int):
            year_data = tabbed_data[year]
            cross_ref = year_data.get("GDLINEHI_2A", {}).get("Cross-Reference Charge", {})
            
            row = {
                "Year": year,
                "Total_Records": year_data.get("Total_Records", 0),
                "STAT_18922G": year_data.get("STAT_18922G", 0),
                "GDSTATHI_2K2.1_Total": year_data.get("GDSTATHI_2K2.1", {}).get("Total", 0),
                "GDLINEHI_2A_Total": year_data.get("GDLINEHI_2A", {}).get("Total", 0),
                "GDSTATHI_Ex_2A_TOTPRISN_Avg": year_data.get("GDSTATHI_Ex_2A_TOTPRISN_Avg", 0),
                "GDLINEHI_2A_TOTPRISN_Avg": year_data.get("GDLINEHI_2A_TOTPRISN_Avg", 0),
                "Over_120_TOTPRISN_Count": year_data.get("GDLINEHI_2A", {}).get("Over_120_TOTPRISN_Count", 0),
            }
            
            # Add cross-reference charge counts
            for charge in CROSS_REF_CHARGES:
                row[charge] = cross_ref.get(charge, 0)
            
            writer.writerow(row)


def _export_district_year_counts(
    tabbed_data: Dict[str, Any],
    output_path: str,
    counts_getter: Callable[[Dict[str, Any]], Dict[str, int]],
    *,
    district_field: str = "District",
    include_all_districts: bool = True,
) -> None:
    """
    Generic helper to export a district-by-year count matrix to CSV.

    Output format:
    - Rows: districts (sorted)
    - Columns: District, then each year (sorted)

    Args:
        tabbed_data: Dictionary containing all year data
        output_path: Path to output CSV file
        counts_getter: Callable(year_data) -> dict[district, count]
        district_field: Name of the district column (default: "District")
        include_all_districts: If True, include every district in DISTRICT_TEMPLATE
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    if include_all_districts:
        sorted_districts = sorted(DISTRICT_TEMPLATE.keys())
    else:
        all_districts = set()
        for year_data in tabbed_data.values():
            district_counts = counts_getter(year_data) or {}
            all_districts.update(district_counts.keys())
        sorted_districts = sorted([d for d in all_districts if d is not None])
    sorted_years = sorted(tabbed_data.keys(), key=int)
    counts_by_year = {y: counts_getter(tabbed_data[y]) or {} for y in sorted_years}
    fieldnames = [district_field] + sorted_years

    with open(output_path, "w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for district in sorted_districts:
            row = {district_field: district}
            for year in sorted_years:
                row[year] = counts_by_year[year].get(district, 0)
            writer.writerow(row)


def export_gdlinehi2a_district_counts(tabbed_data: Dict[str, Any], output_path: str) -> None:
    """
    Export district counts by year for GDLINEHI 2A cross-reference cases.
    This exports counts for cases where GDLINEHI starts with "2A", GDSTATHI = "2K2.1", and ACCAP = "0".
    
    Args:
        tabbed_data: Dictionary containing all year data
        output_path: Path to output CSV file
    """
    _export_district_year_counts(
        tabbed_data,
        output_path,
        lambda yd: yd.get("District_Counts", {}),
    )


def export_all_cases_district_counts(tabbed_data: Dict[str, Any], output_path: str) -> None:
    """
    Export counts of all processed cases by district and year.
    This uses the All_District_Counts structure populated in process_record,
    which is incremented for every record before any statute filtering.
    Includes all cases regardless of statute or guideline.
    """
    _export_district_year_counts(
        tabbed_data,
        output_path,
        lambda yd: yd.get("All_District_Counts", {}),
    )


def export_18922g_qualifying_district_counts(tabbed_data: Dict[str, Any], output_path: str) -> None:
    """
    Export counts of qualifying 18922G cases by district and year.
    This uses the 18922G_District_Counts structure populated in process_record
    after the 18922G/undesired-statute filter passes.
    Includes all qualifying 18922G cases regardless of guideline.
    """
    _export_district_year_counts(
        tabbed_data,
        output_path,
        lambda yd: yd.get("18922G_District_Counts", {}),
    )


def _export_district_year_averages(
    tabbed_data: Dict[str, Any],
    output_path: str,
    totals_getter: Callable[[Dict[str, Any]], Dict[str, Dict[str, Any]]],
) -> None:
    """
    Generic helper to export a district-by-year average TOTPRISN matrix to CSV.
    totals_getter(year_data) must return dict[district, {"sum": float, "count": int}].
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    sorted_districts = sorted(DISTRICT_TEMPLATE.keys())
    sorted_years = sorted(tabbed_data.keys(), key=int)
    totals_by_year = {y: totals_getter(tabbed_data[y]) or {} for y in sorted_years}
    fieldnames = ["District"] + sorted_years
    with open(output_path, "w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for district in sorted_districts:
            row: Dict[str, Any] = {"District": district}
            for year in sorted_years:
                dt = totals_by_year[year].get(district)
                row[year] = round(dt["sum"] / dt["count"], 2) if dt and dt.get("count", 0) > 0 else 0
            writer.writerow(row)


def export_gdstathi_district_averages(tabbed_data: Dict[str, Any], output_path: str) -> None:
    """
    Export average TOTPRISN by district and year for GDSTATHI = "2K2.1"
    cases that do NOT have GDLINEHI starting with "2A".
    """
    _export_district_year_averages(
        tabbed_data,
        output_path,
        lambda yd: yd.get("GDSTATHI_2K2.1", {}).get("District_TOTPRISN", {}),
    )


def export_gdlinehi2a_district_averages(tabbed_data: Dict[str, Any], output_path: str) -> None:
    """
    Export average TOTPRISN by district and year for GDLINEHI 2A cross-reference cases
    where GDSTATHI = "2K2.1" and ACCAP = "0".
    """
    _export_district_year_averages(
        tabbed_data,
        output_path,
        lambda yd: yd.get("GDLINEHI_2A", {}).get("District_TOTPRISN", {}),
    )


def export_gdstathi_2k21_no2a_district_counts(tabbed_data: Dict[str, Any], output_path: str) -> None:
    """
    Export GDSTATHI_2K2.1 district counts by year to CSV.
    This exports counts for cases with GDSTATHI = "2K2.1" that don't have GDLINEHI starting with "2A".
    
    Args:
        tabbed_data: Dictionary containing all year data
        output_path: Path to output CSV file
    """
    _export_district_year_counts(
        tabbed_data,
        output_path,
        lambda yd: yd.get("GDSTATHI_2K2.1", {}).get("District_Counts", {}),
    )


def export_demographic_data(tabbed_data: Dict[str, Any], 
                             category: str, 
                             output_path: str) -> None:
    """
    Export demographic data by year to CSV with separate columns for each guideline type.
    
    Args:
        tabbed_data: Dictionary containing all year data
        category: Demographic category name (e.g., "RACE", "HISPANIC", "EDUC", "CITIZEN")
        output_path: Path to output CSV file
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Get all unique values for this demographic category across all years and both guideline types
    all_values = set()
    for year_data in tabbed_data.values():
        # Get from GDSTATHI_2K2.1
        gdstathi_demo = year_data.get("GDSTATHI_2K2.1", {}).get("Demographics", {}).get(category, {})
        all_values.update(gdstathi_demo.keys())
        
        # Get from GDLINEHI_2A
        gdlinehi_demo = year_data.get("GDLINEHI_2A", {}).get("Demographics", {}).get(category, {})
        all_values.update(gdlinehi_demo.keys())
    
    # Filter out None values and sort
    sorted_values = sorted([v for v in all_values if v is not None])
    sorted_years = sorted(tabbed_data.keys(), key=int)
    
    # Create fieldnames: Category name, then for each year: {year}_GDSTATHI_2K2.1 and {year}_GDLINEHI_2A
    fieldnames = [category]
    for year in sorted_years:
        fieldnames.append(f"{year}_GDSTATHI_2K2.1")
        fieldnames.append(f"{year}_GDLINEHI_2A")
    
    with open(output_path, 'w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        
        for value in sorted_values:
            row = {category: value}
            for year in sorted_years:
                # Get counts from GDSTATHI_2K2.1
                gdstathi_demo = tabbed_data[year].get("GDSTATHI_2K2.1", {}).get("Demographics", {}).get(category, {})
                row[f"{year}_GDSTATHI_2K2.1"] = gdstathi_demo.get(value, 0)
                
                # Get counts from GDLINEHI_2A
                gdlinehi_demo = tabbed_data[year].get("GDLINEHI_2A", {}).get("Demographics", {}).get(category, {})
                row[f"{year}_GDLINEHI_2A"] = gdlinehi_demo.get(value, 0)
            
            writer.writerow(row)


def export_race_data(tabbed_data: Dict[str, Any], output_path: str) -> None:
    """
    Export race demographic data by year to CSV.
    
    Args:
        tabbed_data: Dictionary containing all year data
        output_path: Path to output CSV file
    """
    export_demographic_data(tabbed_data, "RACE", output_path)


def export_hispanic_data(tabbed_data: Dict[str, Any], output_path: str) -> None:
    """
    Export Hispanic origin demographic data by year to CSV.
    
    Args:
        tabbed_data: Dictionary containing all year data
        output_path: Path to output CSV file
    """
    export_demographic_data(tabbed_data, "HISPANIC", output_path)


def export_education_data(tabbed_data: Dict[str, Any], output_path: str) -> None:
    """
    Export education demographic data by year to CSV.
    
    Args:
        tabbed_data: Dictionary containing all year data
        output_path: Path to output CSV file
    """
    export_demographic_data(tabbed_data, "EDUC", output_path)


def export_citizen_data(tabbed_data: Dict[str, Any], output_path: str) -> None:
    """
    Export citizenship demographic data by year to CSV.
    
    Args:
        tabbed_data: Dictionary containing all year data
        output_path: Path to output CSV file
    """
    export_demographic_data(tabbed_data, "CITIZEN", output_path)


def export_over120_records(over120_records: List[Dict[str, Any]], output_path: str) -> None:
    """
    Export records with TOTPRISN > 120 to CSV.
    
    Args:
        over120_records: List of records with TOTPRISN > 120
        output_path: Path to output CSV file
    """
    if not over120_records:
        print(f"No records with TOTPRISN > {TOTPRISN_THRESHOLD} found.")
        return
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Get all unique keys from all records to create fieldnames
    all_keys = set()
    for record in over120_records:
        all_keys.update(record.keys())
    
    fieldnames = sorted(all_keys)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(over120_records)


def build_json_path(year: int) -> str:
    """
    Build path to JSON data file for a given year.
    
    Args:
        year: Year as integer
        
    Returns:
        Path to JSON file
    """
    return f"./data/{year}/clean_data_{year}.json"


def export_ny_south_summary(output_path: str) -> None:
    """
    Export summary statistics for New York South district in two time buckets:
    - 2002-2021
    - 2022-2024
    
    For each bucket, calculates:
    - Total records
    - Total 18922g cases
    - Cases with GDSTATHI="2K2.1" and GDLINEHI doesn't start with "2A": count and avg TOTPRISN
    - Cases with GDSTATHI="2K2.1" and GDLINEHI starts with "2A" and ACCAP != "1": count and avg TOTPRISN
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    TARGET_DISTRICT = "New York South"
    BUCKET1_START = 2002
    BUCKET1_END = 2021
    BUCKET2_START = 2022
    BUCKET2_END = 2024
    
    def _init_bucket(label: str) -> Dict[str, Any]:
        return {
            "Time_Period": label,
            "Total_Records": 0,
            "Total_18922G": 0,
            "GDSTATHI_2K2.1_No2A_Count": 0,
            "GDSTATHI_2K2.1_No2A_Avg_TOTPRISN": 0.0,
            "GDSTATHI_2K2.1_No2A_TOTPRISN_Sum": 0.0,
            "GDSTATHI_2K2.1_No2A_TOTPRISN_Count": 0,
            "GDLINEHI_2A_ACCAP_Not1_Count": 0,
            "GDLINEHI_2A_ACCAP_Not1_Avg_TOTPRISN": 0.0,
            "GDLINEHI_2A_ACCAP_Not1_TOTPRISN_Sum": 0.0,
            "GDLINEHI_2A_ACCAP_Not1_TOTPRISN_Count": 0,
        }

    bucket1 = _init_bucket("2002-2021")
    bucket2 = _init_bucket("2022-2024")
    
    # Process all years
    for year in range(LOWER_BOUND, UPPER_BOUND + 1):
        json_path = build_json_path(year)
        try:
            with open(json_path, "r", encoding="utf-8") as json_file:
                all_data = json.load(json_file)
                
                # Determine which bucket this year belongs to
                if BUCKET1_START <= year <= BUCKET1_END:
                    bucket = bucket1
                elif BUCKET2_START <= year <= BUCKET2_END:
                    bucket = bucket2
                else:
                    continue
                
                for record in all_data:
                    dist_desc = record.get("DISTRICT_DESC")
                    if dist_desc != TARGET_DISTRICT:
                        continue
                    
                    bucket["Total_Records"] += 1
                    
                    # Check if record matches desired statute criteria
                    nwstat_list = record.get("NWSTAT_LIST", [])
                    has_desired_statute = any(item.startswith(DESIRED_STATUTE_PREFIX) for item in nwstat_list)
                    has_undesired_statute = has_prefix(nwstat_list, UNDESIRED_STATUTE_PREFIXES)
                    
                    if not (has_desired_statute and not has_undesired_statute):
                        continue
                    
                    bucket["Total_18922G"] += 1
                    
                    gdstathi = record.get("GDSTATHI", "")
                    gdlinehi = record.get("GDLINEHI", "")
                    accap = record.get("ACCAP", "")
                    totprisn = parse_totprisn(record.get("TOTPRISN"))
                    
                    # Cases with GDSTATHI="2K2.1" and GDLINEHI doesn't start with "2A"
                    if gdstathi == "2K2.1" and not gdlinehi.startswith("2A"):
                        bucket["GDSTATHI_2K2.1_No2A_Count"] += 1
                        if totprisn is not None:
                            bucket["GDSTATHI_2K2.1_No2A_TOTPRISN_Sum"] += totprisn
                            bucket["GDSTATHI_2K2.1_No2A_TOTPRISN_Count"] += 1
                    
                    # Cases with GDSTATHI="2K2.1" and GDLINEHI starts with "2A" and ACCAP != "1"
                    if (gdstathi == "2K2.1" and 
                        gdlinehi.startswith("2A") and 
                        accap != "1"):
                        bucket["GDLINEHI_2A_ACCAP_Not1_Count"] += 1
                        if totprisn is not None:
                            bucket["GDLINEHI_2A_ACCAP_Not1_TOTPRISN_Sum"] += totprisn
                            bucket["GDLINEHI_2A_ACCAP_Not1_TOTPRISN_Count"] += 1
                            
        except FileNotFoundError:
            print(f"File not found for year {year}: {json_path}")
        except Exception as e:
            print(f"Error processing year {year} for NY South summary: {e}")
    
    def _finalize_bucket(bucket: Dict[str, Any]) -> None:
        if bucket["GDSTATHI_2K2.1_No2A_TOTPRISN_Count"] > 0:
            bucket["GDSTATHI_2K2.1_No2A_Avg_TOTPRISN"] = round(
                bucket["GDSTATHI_2K2.1_No2A_TOTPRISN_Sum"] / bucket["GDSTATHI_2K2.1_No2A_TOTPRISN_Count"],
                2,
            )
        if bucket["GDLINEHI_2A_ACCAP_Not1_TOTPRISN_Count"] > 0:
            bucket["GDLINEHI_2A_ACCAP_Not1_Avg_TOTPRISN"] = round(
                bucket["GDLINEHI_2A_ACCAP_Not1_TOTPRISN_Sum"] / bucket["GDLINEHI_2A_ACCAP_Not1_TOTPRISN_Count"],
                2,
            )

    _finalize_bucket(bucket1)
    _finalize_bucket(bucket2)

    NY_SOUTH_CSV_FIELDS = [
        "Time_Period", "Total_Records", "Total_18922G",
        "GDSTATHI_2K2.1_No2A_Count", "GDSTATHI_2K2.1_No2A_Avg_TOTPRISN",
        "GDLINEHI_2A_ACCAP_Not1_Count", "GDLINEHI_2A_ACCAP_Not1_Avg_TOTPRISN",
    ]
    rows = [{k: b[k] for k in NY_SOUTH_CSV_FIELDS} for b in (bucket1, bucket2)]
    with open(output_path, "w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=NY_SOUTH_CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    """Main function to process all years and export results."""
    tabbed_data = {}
    over120_records = []  # Collect all records with TOTPRISN > 120
    
    # Process each year
    for year in range(LOWER_BOUND, UPPER_BOUND + 1):
        try:
            json_path = build_json_path(year)
            print(f"Processing year {year}...")
            process_year_data(json_path, year, tabbed_data, over120_records)
            print(f"Completed year {year}")
        except FileNotFoundError:
            print(f"File not found for year {year}: {json_path}")
        except Exception as e:
            print(f"Error processing year {year}: {e}")
            import traceback
            traceback.print_exc()
    
    # Export results
    print("Exporting results...")
    csv_dir = "./data/csv"
    exports = [
        (export_yearly_summary, (tabbed_data, f"{csv_dir}/yearly_summary.csv")),
        (export_gdlinehi2a_district_counts, (tabbed_data, f"{csv_dir}/gdlinehi2a_district_counts.csv")),
        (export_all_cases_district_counts, (tabbed_data, f"{csv_dir}/all_cases_district_counts.csv")),
        (export_18922g_qualifying_district_counts, (tabbed_data, f"{csv_dir}/18922g_qualifying_district_counts.csv")),
        (export_gdstathi_2k21_no2a_district_counts, (tabbed_data, f"{csv_dir}/gdstathi_2k21_no2a_district_counts.csv")),
        (export_gdstathi_district_averages, (tabbed_data, f"{csv_dir}/gdstathi_district_averages.csv")),
        (export_gdlinehi2a_district_averages, (tabbed_data, f"{csv_dir}/gdlinehi2a_district_averages.csv")),
    ]
    for fn, args in exports:
        fn(*args)
    for category, name in [("RACE", "race"), ("HISPANIC", "hispanic"), ("EDUC", "education"), ("CITIZEN", "citizen")]:
        export_demographic_data(tabbed_data, category, f"{csv_dir}/{name}_demographics.csv")
    export_over120_records(over120_records, f"{csv_dir}/over120.csv")
    export_ny_south_summary(f"{csv_dir}/ny_south_summary.csv")
    print(f"Found {len(over120_records)} records with TOTPRISN > {TOTPRISN_THRESHOLD}")
    print("All CSV files created successfully.")


if __name__ == "__main__":
    main()
