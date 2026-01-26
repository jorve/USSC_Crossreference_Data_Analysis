import sys
import os
import csv
import json
from pathlib import Path
from typing import Dict, Optional, List
from py import dict_legend as dl

# identifying the key variables in the larger dataset that we want to use, listed in DEFENDANT_KEYS
# Variable descriptions available at https://www.ussc.gov/sites/default/files/pdf/research-and-publications/datafiles/USSC_Public_Release_Codebook_FY99_FY24.pdf
DEFENDANT_KEYS = [
    "USSCIDN", "POOFFICE", "ZONE",  "AGE", "ACCAP", "DISTRICT", "CITIZEN",
    "GDLINEHI", "GDREFHI", "GDSTATHI", "HISPORIG", "MONRACE", "MONSEX", "NEWEDUC",
    "NOUSTAT", "RANGEPT", "SENTTOT", "TOTPRISN"
]

# Constants for list prefixes
LIST_PREFIXES = ["GDREF", "GDLINE", "GDSTAT", "NWSTAT"]

# Setting the range of years for which we want to process/clean data
lower_bound = 2002
upper_bound = 2024

# Map each key to its corresponding function in the dl package (moved outside loop for performance)
KEY_TO_FUNCTION = {
    "CITIZEN": dl.citizen_dict,
    "DISTRICT": dl.district_dict,
    "MONRACE": dl.monrace_dict,
    "MONSEX": dl.monsex_dict,
    "NEWEDUC": dl.neweduc_dict,
    "HISPORIG": dl.hisporig_dict,
    "RANGEPT": dl.rangept_dict
}


def get_case_insensitive_value(row: Dict[str, str], key: str) -> Optional[str]:
    """
    Get a value from a dictionary using case-insensitive key lookup.
    
    This function is necessary because the column names in vintages 2004-2006 are lowercase,
    while all other years are uppercase.
    
    Args:
        row: Dictionary to search in
        key: Key to look for (case-insensitive)
        
    Returns:
        Value if found, None otherwise
    """
    # Try exact match first
    if key in row:
        return row[key]
    # Try uppercase
    if key.upper() in row:
        return row[key.upper()]
    # Try lowercase
    if key.lower() in row:
        return row[key.lower()]
    return None


def is_empty_value(value: Optional[str]) -> bool:
    """
    Check if a value is considered empty.
    
    Args:
        value: Value to check
        
    Returns:
        True if value is empty, False otherwise
    """
    return value is None or value == "" or value == " "


def write_json_file(data: List[Dict], file_path: str) -> None:
    """
    Write data to a JSON file, creating parent directories if needed.
    
    Args:
        data: List of dictionaries to write
        file_path: Path to the output JSON file
    """
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)


def write_csv_file(data: List[Dict], file_path: str) -> None:
    """
    Write data to a CSV file, creating parent directories if needed.
    
    Args:
        data: List of dictionaries to write
        file_path: Path to the output CSV file
    """
    if not data:
        raise ValueError("Cannot write CSV file: data is empty")
    
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    headers = list(data[0].keys())
    
    with open(file_path, mode="w", newline='', encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)


def load_csv_to_json(csv_path: str, json_path: str, csv_output: str) -> None:
    """
    Load raw CSV data, clean it, and output both JSON and simplified CSV files.
    
    Args:
        csv_path: Path to the input CSV file
        json_path: Path to the output JSON file
        csv_output: Path to the output CSV file
    """
    csv.field_size_limit(sys.maxsize)
    sentencing_json = []

    # Need to specify encoding as ISO-8859-1 to handle special characters in the data,
    # as the 2023 dataset will throw an error with UTF-8 encoding specified
    with open(csv_path, mode="r", encoding="ISO-8859-1") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            # Use case-insensitive lookup for DEFENDANT_KEYS
            normalized = {k.upper(): get_case_insensitive_value(row, k) for k in DEFENDANT_KEYS}
            normalized.update({
                "GDREF_LIST": [],
                "GDLINE_LIST": [],
                "GDSTAT_LIST": [],
                "NWSTAT_LIST": []
            })
            
            # This is where we take advantage of the JSON document's structure, adding any data
            # from columns that are populated, and ignoring all empty columns. The result is
            # a dictionary for each entry that is only as large as it needs to be.
            for fieldName in csv_reader.fieldnames:
                field_value = get_case_insensitive_value(row, fieldName)
                field_name_upper = fieldName.upper()
                
                if (not field_name_upper.endswith("HI") and 
                    not is_empty_value(field_value)):
                    for key in LIST_PREFIXES:
                        if field_name_upper.startswith(key):
                            normalized[key + "_LIST"].append(field_value)
                            break  # Avoid checking other prefixes once matched
            
            # Convert numeric codes into their corresponding descriptions as per the codebook
            for key, dict_function in KEY_TO_FUNCTION.items():
                normalized[key + "_DESC"] = dict_function(normalized[key])
                normalized.pop(key, None)
            
            sentencing_json.append(normalized)
    
    # Write output files
    write_json_file(sentencing_json, json_path)
    write_csv_file(sentencing_json, csv_output)


def build_file_paths(year: int) -> tuple[str, str, str]:
    """
    Build file paths for a given year.
    
    Args:
        year: Year as integer
        
    Returns:
        Tuple of (csv_input_path, json_output_path, csv_output_path)
    """
    year_str = str(year)
    year_suffix = year_str[-2:]
    base_path = Path("./data") / year_str
    
    csv_input = base_path / f"opafy{year_suffix}nid.csv"
    json_output = base_path / f"clean_data_{year_str}.json"
    csv_output = base_path / f"clean_data_{year_str}.csv"
    
    return str(csv_input), str(json_output), str(csv_output)


def main() -> None:
    """Main function to process data for all years."""
    for year in range(lower_bound, upper_bound + 1):
        try:
            csv_path, json_path, csv_output = build_file_paths(year)
            print(f"Processing year {year}...")
            load_csv_to_json(csv_path, json_path, csv_output)
            print(f"Completed year {year}")
        except FileNotFoundError as e:
            print(f"File not found for year {year}: {e}")
            print(f"  Expected CSV file: {csv_path}")
        except Exception as e:
            print(f"An error occurred processing year {year}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
