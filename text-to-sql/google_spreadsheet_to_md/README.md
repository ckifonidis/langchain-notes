# Google Sheets to CSV Converter

A Python utility that downloads data from Google Sheets, analyzes it, and converts it to CSV files.

## Features

- Authenticates with Google Sheets API using OAuth2
- Downloads all sheets from a specified Google Spreadsheet
- Analyzes sheet data for column types and patterns
- Converts each sheet to a CSV file
- Handles varying column counts and sheet structures
- Provides detailed logging of the conversion process
- Generates analysis reports for each sheet

## Prerequisites

- Python 3.9 or higher
- Poetry for dependency management
- Google Cloud Project with Sheets API enabled
- Google OAuth2 credentials

## Setup

1. Install dependencies:
```bash
poetry install
```

2. Set up Google Cloud credentials:
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project or select an existing one
   - Enable the Google Sheets API
   - Create OAuth2 credentials:
     * Go to "APIs & Services" > "Credentials"
     * Click "Create Credentials" > "OAuth client ID"
     * Choose "Desktop application" type
     * Download the credentials and save as `credentials.json` in the project directory

3. Create a `.env` file in the project directory:
```env
SPREADSHEET_ID=your_spreadsheet_id_here
CREDENTIALS_PATH=credentials.json  # Optional, defaults to credentials.json
OUTPUT_DIR=output  # Optional, defaults to output
ANALYSIS_DIR=analysis  # Optional, defaults to analysis

# CSV Export Options (Optional)
CSV_ENCODING=utf-8
CSV_DATE_FORMAT=%Y-%m-%d
CSV_FLOAT_FORMAT=%.2f
CSV_NA_REP=
```

The Spreadsheet ID can be found in your Google Sheets URL:
`https://docs.google.com/spreadsheets/d/[SPREADSHEET_ID]/edit`

## Usage

### Process Google Sheets

Run the main script to process Google Sheets data:

```bash
poetry run python main.py
```

The first time you run the script:
1. It will prompt for Google OAuth2 authentication
2. A browser window will open (or a URL will be provided)
3. Login with your Google account and grant access
4. The authentication token will be saved for future use

The script will:
- Download all sheets from the specified spreadsheet
- Analyze the data in each sheet
- Convert sheets to CSV files in the `output` directory
- Save analysis reports in the `analysis` directory
- Provide detailed logging of the process

## Output

The script generates two types of output:

1. CSV files in the `output` directory:
   - One file per sheet from the Google Spreadsheet
   - Maintains original sheet names
   - Preserves data formatting

2. Analysis files in the `analysis` directory:
   - JSON files containing analysis of each sheet
   - Includes column types, unique values, null counts
   - Provides sample values for each column

## Project Structure

```
.
├── main.py                  # Main entry point
├── sheets/                  # Core package
│   ├── __init__.py         # Package exports
│   ├── config.py           # Configuration management
│   ├── google_client.py    # Google Sheets API client
│   ├── data_processor.py   # Data processing and analysis
│   ├── file_manager.py     # File operations
│   └── sheet_processor.py  # Main processor class
├── credentials.json        # Google OAuth credentials (not in git)
├── .env                   # Environment variables (not in git)
├── token.pickle          # Saved authentication token (not in git)
├── output/              # Generated CSV files (not in git)
└── analysis/           # Analysis reports (not in git)
```

## Error Handling

The script includes comprehensive error handling for:
- Authentication issues
- Network connectivity problems
- Invalid spreadsheet IDs
- Permission issues
- Malformed data
- Data processing errors

If you encounter authentication errors, try removing the `token.pickle` file and running the script again to re-authenticate.

## Analysis Reports

Each sheet generates an analysis report containing:
- Row and column counts
- Column information:
  * Inferred data type
  * Number of unique values
  * Number of null values
  * Sample values
- Sheet-specific metadata

These reports can be used to:
- Understand data structure
- Identify patterns
- Detect data quality issues
- Plan data transformations