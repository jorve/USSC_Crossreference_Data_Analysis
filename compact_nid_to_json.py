"""
Convert a USSC *nid.csv data file into a memory-efficient JSON list of dictionaries.

Every CSV header appears as a key in each output object: scalar columns use the
value or null when empty. List groups: (1) any column whose name contains "_" is
grouped by the part before the first "_" (e.g. STA3_ABC, STA3_1 -> key "STA3", list
of non-null values in header order); (2) columns that are base+digits only (e.g.
SMIN1, SMIN2) are grouped by base, ordered by digit. List keys always present
(empty list when all null).

Usage:
  python compact_nid_to_json.py --year 2024
  python compact_nid_to_json.py --input ./data/2024/opafy24nid.csv
  python compact_nid_to_json.py --input ./data/2024/opafy24nid.csv --output ./data/2024/compact_2024.json
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Try UTF-8 first; 2023 and some vintages need ISO-8859-1
DEFAULT_ENCODING = "utf-8"
FALLBACK_ENCODING = "iso-8859-1"

# Pattern: base name (letters/underscore) + one or more digits at end (no underscore before digits)
NUMBERED_COLUMN_PATTERN = re.compile(r"^([A-Za-z_]+)(\d+)$")


def normalize_empty(value: Optional[str]) -> Optional[str]:
    """Return None if value is empty or whitespace, else strip and return."""
    if value is None:
        return None
    s = value.strip()
    return s if s else None


def get_value(row: Dict[str, str], col: str) -> Optional[str]:
    """Case-insensitive lookup (2004-2006 use lowercase column names)."""
    if col in row:
        return row[col]
    if col.upper() in row:
        return row[col.upper()]
    if col.lower() in row:
        return row[col.lower()]
    return None


def classify_columns(fieldnames: List[str]) -> Tuple[Dict[str, List[Tuple[int, str]]], List[str]]:
    """
    Split column names into:
      - list_groups: group_name -> [(order_key, original_name), ...] sorted by order_key.
        Any column whose name contains "_" is grouped by the part before the first "_"
        (e.g. STA3_ABC, STA3_1 -> group "STA3"; letters or digits after _ go into the list).
        Columns that match base+digits with no underscore (e.g. SMIN1, SMIN2) are grouped by base.
      - scalar_columns: columns with no "_" and no trailing digits pattern.
    """
    list_groups: Dict[str, List[Tuple[int, str]]] = {}
    scalar: List[str] = []

    for i, name in enumerate(fieldnames):
        name_stripped = name.strip()
        # Any column containing "_" -> group by part before first "_" (order by header position)
        if "_" in name_stripped:
            prefix = name_stripped.split("_", 1)[0]
            list_groups.setdefault(prefix, []).append((i, name))
            continue
        # Else: base + digits only (e.g. SMIN1, SMAX2) -> group by base, order by digit
        match = NUMBERED_COLUMN_PATTERN.match(name_stripped)
        if match:
            base, num_str = match.group(1), match.group(2)
            list_groups.setdefault(base, []).append((int(num_str), name))
            continue
        scalar.append(name)

    for key in list_groups:
        list_groups[key].sort(key=lambda x: x[0])

    return list_groups, scalar


def build_row(
    row: Dict[str, str],
    list_groups: Dict[str, List[Tuple[int, str]]],
    scalar_columns: List[str],
) -> Dict[str, Any]:
    """
    Build one compact dict for the row.
    - List groups (numbered, prefix, prefix+suffix) become a single key with a list of non-null values in order.
    - Every scalar CSV header is present; value is the string or null if empty.
    """
    out: Dict[str, Any] = {}

    for group_name, order_and_names in list_groups.items():
        values = []
        for _order, col in order_and_names:
            v = get_value(row, col)
            v = normalize_empty(v)
            if v is not None:
                values.append(v)
        out[group_name] = values

    for col in scalar_columns:
        v = get_value(row, col)
        v = normalize_empty(v)
        out[col] = v  # None serializes as null in JSON

    return out


def detect_encoding(path: Path) -> str:
    """Try UTF-8; if BOM or common chars fail, return fallback."""
    try:
        with open(path, "r", encoding=DEFAULT_ENCODING) as f:
            f.read(1024 * 1024)
        return DEFAULT_ENCODING
    except UnicodeDecodeError:
        return FALLBACK_ENCODING


def stream_csv_to_json(
    csv_path: Path,
    json_path: Path,
    *,
    encoding: Optional[str] = None,
) -> int:
    """
    Read CSV row by row and write a JSON array of compact dicts.
    Every CSV header has a key in each output dict (null when empty, except numbered groups are lists).
    Returns the number of records written.
    """
    if encoding is None:
        encoding = detect_encoding(csv_path)

    csv.field_size_limit(sys.maxsize)
    count = 0

    with open(csv_path, "r", encoding=encoding, newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        if not fieldnames:
            raise ValueError(f"No header row in {csv_path}")

        list_groups, scalar_columns = classify_columns(fieldnames)

        json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as out:
            out.write("[\n")
            first = True
            for row in reader:
                obj = build_row(row, list_groups, scalar_columns)
                if not first:
                    out.write(",\n")
                out.write(json.dumps(obj, ensure_ascii=False))
                first = False
                count += 1
                if count % 50_000 == 0:
                    print(f"  ... {count} records", flush=True)
            out.write("\n]\n")

    return count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert USSC *nid.csv to memory-efficient JSON (list of dicts, numbered columns as lists)."
    )
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--year", type=int, help="Year (e.g. 2024); input=data/{year}/opafy{YY}nid.csv")
    g.add_argument("--input", type=Path, help="Path to *nid.csv file")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output JSON path (default: same dir as input, compact_data_{year}.json or compact_output.json)",
    )
    parser.add_argument(
        "--encoding",
        choices=[DEFAULT_ENCODING, FALLBACK_ENCODING],
        default=None,
        help="Force encoding (default: auto-detect)",
    )
    args = parser.parse_args()

    if args.year is not None:
        y = args.year
        yy = str(y)[-2:]
        csv_path = Path(f"./data/{y}/opafy{yy}nid.csv")
        out_path = args.output or Path(f"./data/{y}/compact_data_{y}.json")
    else:
        csv_path = args.input
        out_path = args.output or csv_path.parent / "compact_output.json"

    if not csv_path.is_file():
        print(f"Error: input file not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Input:  {csv_path}")
    print(f"Output: {out_path}")
    print("Classifying columns and streaming...")
    n = stream_csv_to_json(csv_path, out_path, encoding=args.encoding)
    print(f"Done. Wrote {n} records to {out_path}")


if __name__ == "__main__":
    main()
