import logging
from sheets import SheetProcessor
from sheets.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main function to process Google Sheets."""
    try:
        # Initialize processor with configuration
        config = Config()
        processor = SheetProcessor(config)
        
        # Process spreadsheet and get analyses
        logger.info("Processing Google Sheets data...")
        analyses = processor.process_spreadsheet()
        
        # Display summary
        logger.info("\nProcessing Summary:")
        for sheet_name, analysis in analyses.items():
            logger.info(f"\nSheet: {sheet_name}")
            logger.info(f"Rows: {analysis['row_count']}")
            logger.info(f"Columns: {analysis['column_count']}")
            logger.info("Column Types:")
            for col, details in analysis['columns'].items():
                logger.info(f"  - {col}: {details['type']}")
        
        logger.info("\nProcess completed successfully!")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()