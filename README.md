# US Sentencing Commission Data Analysis

A Python project for analyzing US Sentencing Commission (USSC) data, focusing on firearm offenses under 18 U.S.C. § 922(g)(1) and a subset of cross-reference "crimes against the person" guideline applications.

## Overview

This project processes and analyzes USSC public release data from fiscal years 2002-2024. It specifically focuses on cases involving 18 U.S.C. § 922(g)(1) (felon in possession of a firearm) that are not accompanied by certain other statutes, and examines how these cases are sentenced under cross-reference guidelines, particularly the 2A guidelines. 

## Notes from the Authors

The United States Sentencing Commission publishes datafiles related to federal sentencing practices for each fiscal year dating back to 2002[^1] for "researchers insterested in studying sentencing practices through quantitative methods". The effort is noble, if poorly executed. Outside of 2024, when a CSV file is made available, data is only accessible to those with licenses for IBM's SPSS statistical or Viya's SAS software packages--limiting the ability of non-institutional researchers to readily access the Commission's sentencing data. And though the CSV file is a nice gesture (given that many comma separated values (CSV) files can be opened in commonly used spreadsheet programs like Microsoft Excel) this file is too large to be viewed by such a program. 

For large datasets such as the annual "Individual Datafiles", the Commission ought to explore ways to make its data more readily accessible to researchers by re-examining its data structure and taxonomy. There are numerous examples in the USSC's datafiles of ghost data, where nearly all rows have thousands of empty columns to satisfy the needs of one or two marginal cases. The earliest examples are the `SMIN` columns, which list the statutory minimum sentence for each crime of conviction. Most individuals have entries in the `SMIN1` column, and a decreasing number of individuals have entries in `SMIN2` and so on, but there are 266 `SMIN` columns! Ditto for `SMAX`. And these are not isolated instances. The datafile is lousy with empty, superfluous columns--which go a long way to making the Commission's files unreadable to anyone without a data science background.

Researchers and the commission alike would benefit from a reexamination of the structure and taxonomy of USSC datafiles, in particular the choice of a relational database when a document database (essentially a list of JSON dictionaries) would reduce filesize, improve legibility, and increase transparency. JSON's ability to handle lists of varying sizes is it's greatest strength relative to traditional relational databases, and would allow the commssion the flexibility to make individual entries as large or long as they needed to be while most entries remain fairly compact. The file size savings would be remarkable. The clear tradeoff when abandoning relational databases is the loss of the spreadsheet format and all of the analytical advantages such a format provides through the power of spreadsheet programs like Microsoft Excel. But the Commission's datafiles are too large for Excel to read, and until 2024, you needed a statistical software license to produce CSV files for analysis anyway. 

For clarity, the current Individual Datafiles exceed the maximum number of column entries for Microsoft Excel, ending at column XFD--that's 16,384 columns for every individual entry. Most entries use less than 1% of these columns. Further, many of these columns represent Base Offense Level Variables, Specific Offense Characteristic Variables, and Adjustment Variables that are used in the guideline calculations to determine the sentencing range. There are 40 categories Base Offense Level Variables, 25 categories of Specific Offense Characteristic Variables, and over 175 categories of Adjustment Variables--each of these categories can have hundreds of variable entries. That's potentially tens of thousands of datapoints to assess in order to check the operations of the sentencing guidelines. 

This variable bloat and dataset opacity make oversight nearly impossible. As we discovered during this analysis, the lack of multiple views into the data make it difficult to determine whether our analysis passes muster--comparing the subset of data we chose with the original dataset is prohibitively time-consuming. The work for this project is publicly available here for transparency and replicability, but not the original datafiles, only the CSV files outputted from SPSS. We wanted to include such files where applicable, but the file sizes require the use of Git Large File Storage and so I am merely including the JSON and CSV files created by the `clean.py` function. For original files, please feel free to contact me or generate your own CSV files from the publicly available data on the USSC's webpage. 

Some other general data consistency issues:
1. for some reason the column names in vintages 2004-2006 are lowercase, while all other years are uppercase. Fix for uniformity.
2. all data vintages are successfully parsed with UTF-8 encoding outside of 2023, which requires ISO-8859-1 encoding. Fix for uniformity.



## Project Structure

```
Sentencing/
├── clean.py                                        # Data cleaning script
├── analyze.py                                      # Data analysis script
├── py/
│   ├── dict_legend.py                              # Dictionary functions for code-to-description conversion
├── data/
│   ├── {year}/                                     # Year-specific data directories (2002-2024)
│   │   ├── opafy{YY}nid.csv                        # Raw USSC data files
│   │   ├── clean_data_{year}.json                  # Cleaned JSON output
│   │   └── clean_data_{year}.csv                   # Cleaned CSV output
│   └── csv/
│       ├── yearly_summary.csv                      # Summary statistics by year
│       ├── gdlinehi2a_district_counts.csv          # District counts for 2A cross-reference cases (GDSTATHI=2K2.1, GDLINEHI 2A, ACCAP=0)
│       ├── all_cases_district_counts.csv           # All processed cases by district and year
│       ├── 18922g_qualifying_district_counts.csv   # Qualifying 18922G cases by district and year
│       ├── gdstathi_2k21_no2a_district_counts.csv  # 2K2.1 without 2A cross-reference counts by district and year
│       ├── gdstathi_district_averages.csv          # Average TOTPRISN by district/year for 2K2.1 without 2A
│       ├── gdlinehi2a_district_averages.csv        # Average TOTPRISN by district/year for 2A cross-reference cases
│       ├── over120.csv                             # Records with TOTPRISN > 120 months
│       ├── ny_south_summary.csv                    # New York South district summary (2002-2021 and 2022-2024 buckets)
│       ├── race_demographics.csv                   # Race demographic breakdowns by year and guideline type
│       ├── hispanic_demographics.csv               # Hispanic origin demographic breakdowns by year and guideline type
│       ├── education_demographics.csv              # Education level demographic breakdowns by year and guideline type
│       └── citizen_demographics.csv                # Citizenship status demographic breakdowns by year and guideline type
└── README.md                                       # This file
```

## Features

### Data Cleaning (`clean.py`)
- Processes raw USSC CSV files with case-insensitive column name handling (handles lowercase columns in 2004-2006)
- Extracts key variables and converts numeric codes to human-readable descriptions
- Creates structured JSON and CSV outputs for analysis
- Handles encoding issues (ISO-8859-1 for input, UTF-8 for output)

### Data Analysis (`analyze.py`)
- Filters cases by statute criteria (18§922(g)(1) without certain accompanying statutes)
- Tracks sentencing patterns under guideline 2K2.1
- Analyzes cross-reference guideline applications (2A guidelines)
- Calculates average total prison time (TOTPRISN) for different case categories
- Tracks district-level distributions
- Generates summary statistics and reports

## Requirements

- Python 3.7+
- Standard library modules:
  - `csv`
  - `json`
  - `sys`
  - `os`
  - `pathlib` (for improved versions)

## Installation

1. Clone or download this repository
2. Ensure Python 3.7+ is installed
3. No external dependencies required (uses only Python standard library)

## Usage

### Step 1: Clean Raw Data

First, clean the raw USSC data files. Some work may be needed here to get the  Place raw CSV files in the appropriate year directories:
- Format: `data/{year}/opafy{YY}nid.csv` (e.g., `data/2024/opafy24nid.csv`)
This format matches the format chosen by the USSC. 

Run the cleaning script:

```bash
python clean.py
```

**Note:** Each year's data takes between 3-7 minutes to process. Processing all years (2002-2024) will take approximately 1-2 hours.

The script will:
- Read raw CSV files
- Extract and normalize key variables
- Convert numeric codes to descriptions
- Output cleaned JSON and CSV files for each year

### Step 2: Analyze Data

After cleaning the data, run the analysis script:

```bash
python analyze.py
```

The analysis script will:
- Process cleaned data for all years
- Calculate statistics and averages
- Generate summary CSV files in `data/csv/`

## Output Files

### `data/csv/yearly_summary.csv`
Summary statistics for each year including:
- Total records
- Count of 18§922(g)(1) cases
- Counts by guideline (2K2.1, 2A guidelines)
- Average total prison time
- Cross-reference charge distributions
- Counts of cases with TOTPRISN > 120 months

### District count and average CSVs

All district CSVs use rows = districts (from the district template) and columns = years (2002–2024). Counts or averages are in the cells.

| File | Contents |
|------|----------|
| `gdlinehi2a_district_counts.csv` | Counts by district and year for GDLINEHI 2A cross-reference cases (GDSTATHI = "2K2.1", GDLINEHI starts with "2A", ACCAP = "0"). |
| `all_cases_district_counts.csv` | Counts of all processed cases by district and year (no statute or guideline filter). |
| `18922g_qualifying_district_counts.csv` | Counts of qualifying 18922G cases by district and year (after 18922G/undesired-statute filter; any guideline). |
| `gdstathi_2k21_no2a_district_counts.csv` | Counts by district and year for cases with GDSTATHI = "2K2.1" and GDLINEHI not starting with "2A". |
| `gdstathi_district_averages.csv` | Average TOTPRISN by district and year for GDSTATHI = "2K2.1" without 2A cross-reference. |
| `gdlinehi2a_district_averages.csv` | Average TOTPRISN by district and year for GDLINEHI 2A cross-reference cases (GDSTATHI = "2K2.1", ACCAP = "0"). |

### `data/csv/over120.csv`
Individual records where total prison time (TOTPRISN) exceeds 120 months for cases meeting the GDLINEHI_2A criteria (2A guideline, 2K2.1 statutory guideline, and ACCAP = 0).

### `data/csv/ny_south_summary.csv`
Summary for the **New York South** district only, in two time buckets:
- **2002–2021**
- **2022–2024**

For each bucket: total records, total 18922G cases, count and average TOTPRISN for GDSTATHI = "2K2.1" without 2A, and count and average TOTPRISN for GDLINEHI 2A with ACCAP ≠ "1".

### Demographic Data Files

The following CSV files contain demographic breakdowns by year with separate columns for each guideline type:

#### `data/csv/race_demographics.csv`
Race demographic data showing counts by race category for each year, with separate columns for:
- `{year}_GDSTATHI_2K2.1`: Counts for cases with 2K2.1 guideline but not 2A cross-reference
- `{year}_GDLINEHI_2A`: Counts for cases with 2A cross-reference guideline

#### `data/csv/hispanic_demographics.csv`
Hispanic origin demographic data showing counts by Hispanic origin category for each year, with separate columns for each guideline type.

#### `data/csv/education_demographics.csv`
Education level demographic data showing counts by education category for each year, with separate columns for each guideline type.

#### `data/csv/citizen_demographics.csv`
Citizenship status demographic data showing counts by citizenship category for each year, with separate columns for each guideline type.

Each demographic file has:
- First column: The demographic category (e.g., "White/Caucasian", "Hispanic", "HS Diploma/GED", etc.)
- Subsequent columns: `{year}_GDSTATHI_2K2.1` and `{year}_GDLINEHI_2A` for each year in the analysis

## Data Sources

- **USSC Public Release Data**: Available from the [US Sentencing Commission](https://www.ussc.gov/research/datafiles/commission-datafiles)
- **Codebook**: Variable descriptions available at [USSC Codebook FY99-FY24](https://www.ussc.gov/sites/default/files/pdf/research-and-publications/datafiles/USSC_Public_Release_Codebook_FY99_FY24.pdf)

## Key Variables

The analysis focuses on these key variables:
- `NWSTAT_LIST`: List of statutes charged
- `GDSTATHI`: Statutory guideline (e.g., "2K2.1")
- `GDLINEHI`: Cross-reference guideline (e.g., "2A1.1", "2A2.1")
- `TOTPRISN`: Total prison time in months
- `DISTRICT_DESC`: Federal judicial district
- `ACCAP`: Acceptance of responsibility adjustment

## Filtering Criteria

The analysis filters for cases that:
- Include 18 U.S.C. § 922(g)(1) (`18922G` prefix in `NWSTAT_LIST`)
- Do NOT include certain other statutes (e.g., 18§924(c), 18§924(e), drug crimes, etc.)

See `UNDESIRED_STATUTE_PREFIXES` in the code for the complete list of excluded statute prefixes.

## Configuration

Key configuration variables (in `analyze.py`):

```python
LOWER_BOUND = 2002      # Starting year
UPPER_BOUND = 2024      # Ending year
TOTPRISN_THRESHOLD = 120  # Threshold for "over 120" analysis
```

## Notes

- **Column Name Variations**: Years 2004-2006 use lowercase column names, while other years use uppercase. The code handles this automatically.
- **Encoding**: Raw data files use ISO-8859-1 encoding to handle special characters. Output files use UTF-8.
- **Performance**: Processing is single-threaded. Each year takes 3-7 minutes depending on data size.
- **Memory**: Large JSON files (some years have 2+ million records) require sufficient RAM.

## Troubleshooting

### File Not Found Errors
- Ensure raw CSV files are in the correct directory structure: `data/{year}/opafy{YY}nid.csv`
- Check that year directories exist

### Encoding Errors
- Ensure input files use ISO-8859-1 encoding
- Some special characters may require manual handling

### Memory Issues
- Process years individually by adjusting `LOWER_BOUND` and `UPPER_BOUND`
- Consider processing in smaller batches

## License

MIT License

Copyright (c) 2026 Jeff Jorve

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Contributing

When contributing, please:
- Follow the existing code style
- Add docstrings to new functions
- Test with a small subset of data first
- Update this README if adding new features

## Contact

For questions or issues, please refer to the project repository or contact the maintainer.

[^1]: https://www.ussc.gov/research/datafiles/commission-datafiles# 