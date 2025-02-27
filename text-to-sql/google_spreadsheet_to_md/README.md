# Google Sheets to CSV Converter

A Python utility that downloads data from Google Sheets and converts it to CSV files.

## Features

- Authenticates with Google Sheets API using OAuth2
- Downloads all sheets from a specified Google Spreadsheet
- Converts each sheet to a CSV file
- Handles varying column counts and sheet structures
- Provides detailed logging of the conversion process

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
```
The Spreadsheet ID can be found in your Google Sheets URL:
`https://docs.google.com/spreadsheets/d/[SPREADSHEET_ID]/edit`

## Usage

### 1. Download Sheets to CSV

Run the main script to download Google Sheets data:

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
- Convert them to CSV files in the `output` directory
- Provide detailed logging of the process

### 2. Convert CSV to Markdown

After downloading the sheets to CSV, you can convert them to markdown format:

```bash
poetry run python csv_to_markdown.py
```

This script will:
- Read all CSV files from the `output` directory
- Convert each table to markdown format
- Save the markdown files in a `markdown` directory
- Each file will include a table header and formatted content

## Output

All CSV files are saved in the `output` directory. Each sheet from the Google Spreadsheet is converted to a separate CSV file, maintaining the original sheet name.

## Notes

- The script automatically handles sheets with varying column counts
- Empty sheets are skipped
- Column headers are preserved
- Special characters in sheet names are maintained in the output files

## File Structure

```
.
├── main.py              # Main script
├── csv_to_markdown.py   # CSV to Markdown converter
├── credentials.json     # Google OAuth credentials (not in git)
├── .env                # Environment variables (not in git)
├── token.pickle        # Saved authentication token (not in git)
├── output/            # Generated CSV files (not in git)
├── markdown/          # Generated Markdown files (not in git)
└── .gitignore         # Git ignore rules
```

## Error Handling

The script includes comprehensive error handling for:
- Authentication issues
- Network connectivity problems
- Invalid spreadsheet IDs
- Permission issues
- Malformed data

If you encounter authentication errors, try removing the `token.pickle` file and running the script again to re-authenticate.