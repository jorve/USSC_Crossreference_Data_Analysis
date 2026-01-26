import csv
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
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
    # Initialize district counts dictionary
    district_counts = {}
    for code in range(97):
        district_name = dl.district_dict(str(code))
        if district_name != "Unknown":
            district_counts[district_name] = 0
    
    return {
        "STAT_18922G": 0,
        "GDSTATHI_2K2.1": {
            "Total": 0,
            "Demographics": {
                "RACE": {},
                "HISPANIC": {},
                "DISTRICT": {},
                "EDUC": {},
                "CITIZEN": {}
            }
        },
        "Total_Records": 0,
        "GDLINEHI_2A": {
            "Over_120_TOTPRISN_Count": 0,
            "Total": 0,
            "Cross-Reference Charge": {charge: 0 for charge in CROSS_REF_CHARGES},
            "Demographics": {
                "RACE": {},
                "HISPANIC": {},
                "DISTRICT": {},
                "EDUC": {},
                "CITIZEN": {}
            }
        },
        "District_Counts": district_counts
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
    
    nwstat_list = record.get("NWSTAT_LIST", [])
    
    # Check if record matches desired statute criteria
    has_desired_statute = any(item.startswith(DESIRED_STATUTE_PREFIX) for item in nwstat_list)
    has_undesired_statute = has_prefix(nwstat_list, UNDESIRED_STATUTE_PREFIXES)
    
    if not (has_desired_statute and not has_undesired_statute):
        return
    
    year_data["STAT_18922G"] += 1
    gdstathi = record.get("GDSTATHI", "")
    gdlinehi = record.get("GDLINEHI", "")
    
    # Process GDSTATHI_2K2.1 records
    if gdstathi == "2K2.1":
        year_data["GDSTATHI_2K2.1"]["Total"] += 1
        
        # Process records with 2K2.1 statutory guideline but not 2A cross reference guideline
        if not gdlinehi.startswith("2A"):
            totprisn = parse_totprisn(record.get("TOTPRISN"))
            if totprisn is not None:
                # Store for average calculation (would need to track this separately)
                pass
            
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
            
            # Update district count
            dist_desc = record.get("DISTRICT_DESC")
            if dist_desc is not None and dist_desc in year_data["District_Counts"]:
                year_data["District_Counts"][dist_desc] += 1
        
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


def calculate_averages(year_data: Dict[str, Any], 
                       gdstathi_totprisn: List[float],
                       gdlinehi_totprisn: List[float]) -> None:
    """
    Calculate and store average TOTPRISN values.
    
    Args:
        year_data: Year data dictionary to update
        gdstathi_totprisn: List of TOTPRISN values for GDSTATHI_Ex_2A
        gdlinehi_totprisn: List of TOTPRISN values for GDLINEHI_2A
    """
    if gdstathi_totprisn:
        year_data["GDSTATHI_Ex_2A_TOTPRISN_Avg"] = round(
            sum(gdstathi_totprisn) / len(gdstathi_totprisn), 2
        )
    else:
        year_data["GDSTATHI_Ex_2A_TOTPRISN_Avg"] = 0
    
    if gdlinehi_totprisn:
        year_data["GDLINEHI_2A_TOTPRISN_Avg"] = round(
            sum(gdlinehi_totprisn) / len(gdlinehi_totprisn), 2
        )
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
    
    gdstathi_totprisn = []
    gdlinehi_totprisn = []
    
    with open(json_path, "r", encoding="utf-8") as json_file:
        all_data = json.load(json_file)
        
        for record in all_data:
            process_record(record, year_data, year, over120_records)
            
            # Track TOTPRISN values for averages (simplified - would need proper tracking)
            nwstat_list = record.get("NWSTAT_LIST", [])
            if (any(item.startswith(DESIRED_STATUTE_PREFIX) for item in nwstat_list) and
                not has_prefix(nwstat_list, UNDESIRED_STATUTE_PREFIXES)):
                
                gdstathi = record.get("GDSTATHI", "")
                gdlinehi = record.get("GDLINEHI", "")
                
                if gdstathi == "2K2.1" and not gdlinehi.startswith("2A"):
                    totprisn = parse_totprisn(record.get("TOTPRISN"))
                    if totprisn is not None:
                        gdstathi_totprisn.append(totprisn)
                
                if (gdlinehi.startswith("2A") and 
                    gdstathi == "2K2.1" and 
                    record.get("ACCAP") == "0"):
                    totprisn = parse_totprisn(record.get("TOTPRISN"))
                    if totprisn is not None:
                        gdlinehi_totprisn.append(totprisn)
    
    calculate_averages(year_data, gdstathi_totprisn, gdlinehi_totprisn)
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


def export_district_counts(tabbed_data: Dict[str, Any], output_path: str) -> None:
    """
    Export district counts by year to CSV.
    
    Args:
        tabbed_data: Dictionary containing all year data
        output_path: Path to output CSV file
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Get all unique districts across all years
    all_districts = set()
    for year_data in tabbed_data.values():
        district_counts = year_data.get("District_Counts", {})
        all_districts.update(district_counts.keys())
    
    # Filter out None values and sort
    sorted_districts = sorted([d for d in all_districts if d is not None])
    sorted_years = sorted(tabbed_data.keys(), key=int)
    
    fieldnames = ["District"] + sorted_years
    
    with open(output_path, 'w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        
        for district in sorted_districts:
            row = {"District": district}
            for year in sorted_years:
                district_counts = tabbed_data[year].get("District_Counts", {})
                row[year] = district_counts.get(district, 0)
            writer.writerow(row)


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
    export_yearly_summary(tabbed_data, "./data/csv/yearly_summary.csv")
    export_district_counts(tabbed_data, "./data/csv/district_counts.csv")
    export_race_data(tabbed_data, "./data/csv/race_demographics.csv")
    export_hispanic_data(tabbed_data, "./data/csv/hispanic_demographics.csv")
    export_education_data(tabbed_data, "./data/csv/education_demographics.csv")
    export_citizen_data(tabbed_data, "./data/csv/citizen_demographics.csv")
    export_over120_records(over120_records, "./data/csv/over120.csv")
    print(f"Found {len(over120_records)} records with TOTPRISN > {TOTPRISN_THRESHOLD}")
    print("All CSV files created successfully.")


if __name__ == "__main__":
    main()
