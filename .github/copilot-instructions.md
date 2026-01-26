## Purpose
Give a brief, actionable orientation for editing the small data-cleaning project in this repo.

## Big picture
- Source data: `data/opafy24nid.dat` appears to be the raw data file. Two analysis-language scripts live alongside it: `data/opafy24nid.sas` (SAS) and `data/opafy24nid.sps` (SPSS). Treat these as canonical source/ingestion artifacts.
- Cleaning/transform code: `py/clean_data.py` is the Python entry point for cleaning. It currently imports `pandas` but contains no implementation yet — new work should happen here.
- Outputs: `json/` is present but empty; likely intended to hold processed JSON outputs or downstream artifacts.

When modifying the code, assume the pipeline is: raw data in `data/` -> transform in `py/clean_data.py` -> write to `json/` (or other downstream formats).

## Key files and their roles (explicit)
- `data/opafy24nid.dat` — raw dataset (fixed-width or delimited binary/text). Inspect `opafy24nid.sas` / `opafy24nid.sps` to learn the intended column layout and parsing logic.
- `data/opafy24nid.sas` — SAS script describing variable names/types/positions. Use it as the authoritative schema when implementing reading/parsing in Python.
- `py/clean_data.py` — Python cleaning module (imports pandas). Keep new code modular (pure functions) so it can be unit tested later.

## Developer workflows (concrete commands)
- Run the Python cleaner locally (simple run while developing):

  powershell> python .\py\clean_data.py

- Inspect raw schema: open `data/opafy24nid.sas` (or `.sps`) to find column widths/names before writing parsing code.

## Project-specific conventions and patterns
- Single-responsibility layout: raw data in `data/`, scripts in `py/`, outputs in `json/`. Maintain this separation.
- Prefer `pandas` for table transformations (the repo already imports it). Use explicit dtype and parse logic derived from the SAS/SPSS scripts.
- Avoid editing the `.sas` or `.sps` files unless the change is intended to update the canonical ingestion logic — reference them, copy parsing rules into Python.

## Integration points and external tooling
- This repo relies on (or expects) SAS/SPSS-formatted metadata in the `data/` folder. If you need to re-create `opafy24nid.dat`, use the SAS or SPSS scripts with the appropriate tools (not included here).

## How to make small, safe edits (examples)
- When adding parsing code, include a short inline example in `py/clean_data.py` using `pandas.read_fwf` or `pandas.read_csv` with explicit columns derived from `opafy24nid.sas`.
- Keep side effects (file writes) behind a `if __name__ == "__main__":` block so functions remain testable.

## What the agent should *not* assume
- There are no tests, no CI, and no build files present — do not assume test runners are set up.
- Do not assume the exact column widths or separators for `opafy24nid.dat` without consulting `opafy24nid.sas` or `opafy24nid.sps`.

## When to ask the user
- If you need to change the canonical ingestion logic (the `.sas`/`.sps` behavior) — ask which source to follow.
- If a proposed change writes new permanent outputs to `json/` or modifies raw data, ask for confirmation and a short migration note.

---
If anything here is missing or unclear, tell me which area you want expanded (parsing examples, test scaffolding, or a suggested `requirements.txt`).
