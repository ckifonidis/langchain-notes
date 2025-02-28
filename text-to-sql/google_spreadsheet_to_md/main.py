#!/usr/bin/env python3
"""
Main script that coordinates the spreadsheet downloading and CSV analysis processes.
Takes a spreadsheet ID as input and organizes output files in a spreadsheet-specific directory.
"""

import os
import argparse
import logging
from typing import Dict, Any
from sheets import SheetProcessor
from sheets.config import Config
from csv_table_analyzer import TableDescriptionAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_output_directory(spreadsheet_id: str) -> str:
    """
    Create and return the path to the spreadsheet-specific output directory.
    
    Args:
        spreadsheet_id: The ID of the Google Spreadsheet
        
    Returns:
        str: Path to the spreadsheet-specific output directory
    """
    output_dir = os.path.join('output', spreadsheet_id)
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def download_spreadsheet(spreadsheet_id: str, output_dir: str) -> Dict[str, Any]:
    """
    Download and process the Google Spreadsheet.
    
    Args:
        spreadsheet_id: The ID of the Google Spreadsheet
        output_dir: Directory where CSV files will be saved
        
    Returns:
        Dict[str, Any]: Analysis results from the sheet processor
    """
    # Create config with custom output directory
    config = Config()
    config.update(
        spreadsheet_id=spreadsheet_id,
        output_dir=output_dir
    )
    
    # Initialize and run sheet processor
    processor = SheetProcessor(config)
    logger.info("Processing Google Sheets data...")
    analyses = processor.process_spreadsheet()
    
    # Display summary
    logger.info("\nSpreadsheet Processing Summary:")
    for sheet_name, analysis in analyses.items():
        logger.info(f"\nSheet: {sheet_name}")
        logger.info(f"Rows: {analysis['row_count']}")
        logger.info(f"Columns: {analysis['column_count']}")
        logger.info("Column Types:")
        for col, details in analysis['columns'].items():
            logger.info(f"  - {col}: {details['type']}")
    
    return analyses

def analyze_csv_files(output_dir: str) -> None:
    """
    Analyze CSV files in the output directory.
    
    Args:
        output_dir: Directory containing CSV files to analyze
    """
    # Initialize and run CSV analyzer
    analyzer = TableDescriptionAnalyzer(output_dir=output_dir)
    analyzer.process_all_files()

def main():
    """Main function to orchestrate the downloading and analysis processes."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Download and analyze Google Spreadsheet data.')
    parser.add_argument('spreadsheet_id', help='The ID of the Google Spreadsheet to process')
    parser.add_argument('--no-llm', action='store_true', help='Disable LLM-based analysis')
    
    args = parser.parse_args()
    
    try:
        # Set up output directory for this spreadsheet
        output_dir = setup_output_directory(args.spreadsheet_id)
        logger.info(f"Output directory: {output_dir}")
        
        # Step 1: Download and process spreadsheet
        logger.info("\nStep 1: Downloading spreadsheet...")
        analyses = download_spreadsheet(args.spreadsheet_id, output_dir)
        
        # Step 2: Analyze generated CSV files
        logger.info("\nStep 2: Analyzing CSV files...")
        analyze_csv_files(output_dir)
        
        logger.info("\nProcessing completed successfully!")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()