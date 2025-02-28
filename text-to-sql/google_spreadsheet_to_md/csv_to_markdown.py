import os
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def csv_to_markdown_table(df: pd.DataFrame) -> str:
    """
    Convert a DataFrame to a markdown table string.
    
    Args:
        df (pd.DataFrame): The DataFrame to convert
        
    Returns:
        str: Markdown table representation
    """
    # Convert DataFrame to markdown table
    headers = '| ' + ' | '.join(str(col) for col in df.columns) + ' |'
    separator = '| ' + ' | '.join(['---'] * len(df.columns)) + ' |'
    
    # Convert each row to markdown format, handling missing values
    rows = []
    for _, row in df.iterrows():
        # Replace NaN with empty string and ensure all values are strings
        values = [str(val) if pd.notna(val) else '' for val in row]
        # Escape pipe characters in values
        values = [val.replace('|', '\\|') for val in values]
        rows.append('| ' + ' | '.join(values) + ' |')
    
    # Combine all parts
    return '\n'.join([headers, separator] + rows)

def process_csv_files(input_dir: str = 'output', output_dir: str = 'markdown'):
    """
    Process all CSV files in the input directory and convert them to markdown tables.
    
    Args:
        input_dir (str): Directory containing CSV files
        output_dir (str): Directory to save markdown files
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Process each CSV file
    for filename in os.listdir(input_dir):
        if filename.endswith('.csv'):
            input_path = os.path.join(input_dir, filename)
            output_filename = os.path.splitext(filename)[0] + '.md'
            output_path = os.path.join(output_dir, output_filename)
            
            try:
                logger.info(f"Processing {filename}...")
                
                # Read CSV file
                df = pd.read_csv(input_path)
                
                # Convert to markdown table
                markdown_content = f"# {os.path.splitext(filename)[0]}\n\n"
                markdown_content += csv_to_markdown_table(df)
                
                # Save to markdown file
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                
                logger.info(f"Created {output_filename}")
                
            except Exception as e:
                logger.error(f"Error processing {filename}: {str(e)}")
                continue

def main():
    """Main function to convert CSV files to markdown tables."""
    try:
        logger.info("Starting CSV to Markdown conversion...")
        process_csv_files()
        logger.info("Process completed successfully!")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()