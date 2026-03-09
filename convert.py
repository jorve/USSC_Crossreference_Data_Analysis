"""
convert.py

Converts raw USSC annual sentencing CSV files (opafy{YY}nid.csv) into
structured JSON dictionaries that preserve every field from the source data.

Variable series (fields that are numbered repetitions of the same variable,
e.g. GDSTAT1, GDSTAT2, …, GDSTATX) are collapsed into compact Python lists,
with blank/empty entries omitted so that each list contains only populated
values.  Every other field is kept as a scalar string, keyed by its
uppercased field name.

Series collapsed into lists
───────────────────────────
  GDSTAT_LIST   — statutory guideline per computation       (all years)
  GDREF_LIST    — 1st reference guideline per computation   (all years)
  GDCROS_LIST   — 2nd cross-reference guideline             (FY2004+)
  GDUNDR_LIST   — 3rd cross-reference guideline             (FY2012+)
  GDLINE_LIST   — sentencing (final) guideline per comp.    (FY2012+, public)
  NWSTAT_LIST   — deduplicated unique statutes              (all years)
  STA_LIST      — raw per-count statutes, STA{1,2,3}_N      (FY1999–FY2021)
  TTSC_LIST     — raw per-count statutes, TTSC{1,2,3}_N     (FY2022+)
  DRUGTYP_LIST  — drug type per drug count                  (all years)
  CHEMTYP_LIST  — chemical type per chemical count          (all years)
  REASON_LIST   — departure/variance reason codes           (all years)
  REAS_LIST     — alternate departure reason series         (all years)

"HI" scalar variables (GDLINEHI, GDSTATHI, GDREFHI, GDCROSHI, GDUNDRHI, …)
are NOT collapsed — they are preserved as individual scalar fields because
they are the primary computation variables used in analysis.

Output
──────
  data/{year}/full_data_{year}.json   — compact JSON array, one object per case

Usage
─────
  python convert.py              # process all years in [LOWER_BOUND, UPPER_BOUND]
  python convert.py 2018         # process a single year
  python convert.py 2015 2020    # process an inclusive range of years
"""

import csv
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

LOWER_BOUND = 2002
UPPER_BOUND = 2024

# ---------------------------------------------------------------------------
# Series detection
# ---------------------------------------------------------------------------
# Each entry maps an output list key to the field-name prefix for that series.
# The regex that is compiled for each prefix matches:
#   ^{PREFIX}{one-or-more-digits}$   (case-insensitive)
#
# This naturally excludes the "HI" scalar siblings — e.g. GDLINEHI does not
# end with digits, so it will never match the GDLINE series pattern.
#
# REASON is listed before REAS so that REASON1 is classified as REASON_LIST
# and not accidentally captured by a looser REAS check.  In practice the
# numeric-suffix-only regex makes order irrelevant (REASON1 won't match
# r"^REAS\d+$"), but the ordering makes intent explicit.
_SIMPLE_SERIES: List[Tuple[str, str]] = [
    ("GDSTAT_LIST",  "GDSTAT"),
    ("GDREF_LIST",   "GDREF"),
    ("GDCROS_LIST",  "GDCROS"),
    ("GDUNDR_LIST",  "GDUNDR"),
    ("GDLINE_LIST",  "GDLINE"),
    ("NWSTAT_LIST",  "NWSTAT"),
    ("DRUGTYP_LIST", "DRUGTYP"),
    ("CHEMTYP_LIST", "CHEMTYP"),
    ("REASON_LIST",  "REASON"),
    ("REAS_LIST",    "REAS"),
]

_COMPILED_SERIES: List[Tuple[str, "re.Pattern[str]"]] = [
    (key, re.compile(r"^" + re.escape(pfx) + r"\d+$", re.IGNORECASE))
    for key, pfx in _SIMPLE_SERIES
]

# Per-count statute fields have a different naming convention:
#   STA{1,2,3}_{count_number}   e.g. STA1_1, STA2_4, STA3_12  (FY1999–FY2021)
#   TTSC{1,2,3}_{count_number}  e.g. TTSC1_1                   (FY2022+)
_STA_RE  = re.compile(r"^STA[123]_\d+$",  re.IGNORECASE)
_TTSC_RE = re.compile(r"^TTSC[123]_\d+$", re.IGNORECASE)

ALL_LIST_KEYS: Tuple[str, ...] = tuple(
    [key for key, _ in _SIMPLE_SERIES] + ["STA_LIST", "TTSC_LIST"]
)


def _classify_field(upper_name: str) -> Optional[str]:
    """
    Return the output list key if this field belongs to a collapsible series,
    or None if it should be kept as a scalar.
    """
    for list_key, pattern in _COMPILED_SERIES:
        if pattern.match(upper_name):
            return list_key
    if _STA_RE.match(upper_name):
        return "STA_LIST"
    if _TTSC_RE.match(upper_name):
        return "TTSC_LIST"
    return None


def build_field_map(fieldnames: List[str]) -> Dict[str, Optional[str]]:
    """
    Pre-compute {UPPERCASE_FIELD_NAME → list_key_or_None} for every CSV
    header.  Called once per file so classification regexes run only once
    per field rather than once per field per row.
    """
    return {name.upper(): _classify_field(name.upper()) for name in fieldnames}


# ---------------------------------------------------------------------------
# Row processing
# ---------------------------------------------------------------------------

def _is_empty(value: Optional[str]) -> bool:
    """True for values that should not be included in a list."""
    return value is None or value == "" or value == " "


def process_row(
    row: Dict[str, str],
    fieldnames: List[str],
    field_map: Dict[str, Optional[str]],
) -> Dict[str, Any]:
    """
    Convert one CSV row (from csv.DictReader) into a JSON-serialisable dict.

    - Fields belonging to a variable series are accumulated into their list;
      blank/empty values are skipped so every list element is meaningful.
    - All other fields become scalar string entries keyed by UPPERCASE name.
    - List keys that end up empty (series not present in this year's file)
      are omitted entirely to keep records compact.
    """
    lists: Dict[str, List[str]] = {k: [] for k in ALL_LIST_KEYS}
    record: Dict[str, Any] = {}

    for raw_name in fieldnames:
        upper_name = raw_name.upper()
        # DictReader keys match the original CSV header case; use raw_name
        # for the lookup so years with lowercase headers (FY2004-2006) work.
        value: Optional[str] = row.get(raw_name)
        list_key = field_map[upper_name]

        if list_key is not None:
            if not _is_empty(value):
                lists[list_key].append(value)  # type: ignore[arg-type]
        else:
            if not _is_empty(value):
                record[upper_name] = value

    # Attach non-empty lists only
    for key, values in lists.items():
        if values:
            record[key] = values

    return record


# ---------------------------------------------------------------------------
# Per-year conversion
# ---------------------------------------------------------------------------

def _build_paths(year: int) -> Tuple[Path, Path]:
    year_str = str(year)
    suffix   = year_str[-2:]          # e.g. "18" for 2018
    base     = Path("data") / year_str
    csv_in   = base / f"opafy{suffix}nid.csv"
    json_out = base / f"full_data_{year_str}.json"
    return csv_in, json_out


def _progress_bar(pct: float, width: int = 28) -> str:
    """Return an ASCII progress bar string for the given fraction (0.0–1.0)."""
    filled = int(width * pct)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {pct * 100:5.1f}%"


def _count_rows(path: Path) -> int:
    """Fast row count via binary newline scan (subtracts 1 for the header)."""
    with path.open("rb") as f:
        return sum(1 for _ in f) - 1


def convert_year(year: int) -> None:
    """Read the raw CSV for one fiscal year and write full_data_{year}.json."""
    csv_path, out_path = _build_paths(year)

    if not csv_path.exists():
        print(f"  [{year}] not found: {csv_path} — skipping")
        return

    file_size = csv_path.stat().st_size
    print(f"  [{year}] counting rows in {csv_path.name}  ({file_size / 1_048_576:.0f} MB)…", flush=True)
    total_rows = _count_rows(csv_path)
    print(f"  [{year}] {total_rows:,} rows — converting…", flush=True)

    # Use ISO-8859-1 for all years: it is a superset of ASCII and avoids the
    # UnicodeDecodeError that UTF-8 throws on the FY2023 file.
    csv.field_size_limit(sys.maxsize)
    records: List[Dict[str, Any]] = []

    with csv_path.open(encoding="ISO-8859-1", newline="") as fh:
        reader = csv.DictReader(fh)
        fieldnames: List[str] = reader.fieldnames or []
        if not fieldnames:
            print(f"  [{year}] CSV has no headers — skipping")
            return
        field_map = build_field_map(fieldnames)

        for i, row in enumerate(reader):
            records.append(process_row(row, fieldnames, field_map))
            # Redraw progress bar every 2,000 rows
            if i % 2_000 == 0:
                pct = i / total_rows if total_rows > 0 else 0
                print(
                    f"\r  [{year}] {_progress_bar(pct)}  {i:,} / {total_rows:,}",
                    end="",
                    flush=True,
                )

    # Overwrite the progress line with the final summary
    n = len(records)
    print(f"\r  [{year}] {_progress_bar(1.0)}  {n:,} records → {out_path.name}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        # Compact JSON (no indentation) — these files contain every column
        # from the raw CSV and can be large; whitespace would multiply size.
        json.dump(records, fh, ensure_ascii=False, separators=(",", ":"))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _parse_args(argv: List[str]) -> Tuple[int, int]:
    """
    Parse optional CLI year arguments.
      (no args)      → LOWER_BOUND .. UPPER_BOUND
      one arg        → single year
      two args       → inclusive range
    """
    if len(argv) == 1:
        return LOWER_BOUND, UPPER_BOUND
    if len(argv) == 2:
        y = int(argv[1])
        return y, y
    if len(argv) == 3:
        return int(argv[1]), int(argv[2])
    print(f"Usage: python {argv[0]} [start_year [end_year]]")
    sys.exit(1)


def main() -> None:
    lo, hi = _parse_args(sys.argv)
    print(f"Converting FY{lo}–FY{hi}…")
    for year in range(lo, hi + 1):
        try:
            convert_year(year)
        except Exception as exc:
            import traceback
            print(f"  [{year}] ERROR: {exc}")
            traceback.print_exc()
    print("Done.")


if __name__ == "__main__":
    main()
