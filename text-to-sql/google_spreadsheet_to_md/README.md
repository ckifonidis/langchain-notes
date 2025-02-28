# Google Spreadsheet to Markdown Converter

This tool downloads Google Spreadsheet data and analyzes its structure, particularly focusing on table descriptions.

## Setup

1. Install dependencies:
```bash
poetry install
```

2. Create a `.env` file with your credentials:
```env
SPREADSHEET_ID=your_default_spreadsheet_id
OPENAI_API_KEY=your_openai_key  # If using OpenAI models
ANTHROPIC_API_KEY=your_anthropic_key  # If using Anthropic models
DEEPSEEK_API_KEY=your_deepseek_key  # If using Deepseek models
```

3. Place your Google Sheets credentials in `credentials.json`

## Usage

The main script takes a spreadsheet ID as input and organizes all output files in a spreadsheet-specific directory:

```bash
# Basic usage
poetry run python main.py your_spreadsheet_id

# Disable LLM analysis
poetry run python main.py your_spreadsheet_id --no-llm

# Use specific model
poetry run python main.py your_spreadsheet_id --model-type openai --model-name gpt-4

# Adjust model temperature
poetry run python main.py your_spreadsheet_id --temperature 0.7
```

### Output Structure

All files are organized under `output/{spreadsheet_id}/`:
- CSV files from the spreadsheet
- Analysis files with `_analysis.txt` suffix
- Any additional generated documentation

### Options

- `spreadsheet_id`: (Required) The ID of the Google Spreadsheet to process
- `--no-llm`: Disable LLM-based analysis
- `--model-type`: Type of model to use (openai, anthropic, or deepseek)
- `--model-name`: Specific model name (default: deepseek-coder)
- `--temperature`: Model temperature (0-1, default: 0)