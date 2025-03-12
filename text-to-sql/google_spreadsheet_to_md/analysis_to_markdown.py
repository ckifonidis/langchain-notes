import os
import json
import logging
from typing import Dict, Any, Optional
from model_selector import ModelType, use_model
from csv_analysis.processors.table_metadata_processor import TableMetadataProcessor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_file_type(text_analysis: str) -> str:
    """Check if the analysis is for a table or database description.

    Args:
        text_analysis: The text analysis content

    Returns:
        str: "TABLE_DESCRIPTION", "DATABASE_DESCRIPTION", or None if neither
    """
    if "**Type: TABLE_DESCRIPTION**" in text_analysis:
        return "TABLE_DESCRIPTION"
    elif "**Type: DATABASE_DESCRIPTION**" in text_analysis:
        return "DATABASE_DESCRIPTION"
    return None

def get_table_metadata(output_dir: str) -> Optional[str]:
    """
    Load the tables metadata analysis if available.
    
    Args:
        output_dir: Directory containing the tables_metadata_analysis.txt file
        
    Returns:
        String containing the metadata analysis or None if not available
    """
    metadata_path = os.path.join(output_dir, "tables_metadata_analysis.txt")
    if not os.path.exists(metadata_path):
        return None
        
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.warning(f"Failed to load table metadata: {str(e)}")
    return None

def get_llm_agent():
    """Initialize and return an LLM agent.
    
    Returns:
        The initialized LLM agent (trying Deepseek first, falling back to Claude)
    """
    try:
        # Try Deepseek first
        return use_model(
            model_type=ModelType.OPENAI,
            model_name="gpt-4o-mini-2024-07-18",
            temperature=0.0
        )
    except Exception as e:
        logger.warning(f"Failed to initialize Deepseek: {str(e)}")
        logger.info("Falling back to Claude-3...")
        
        # Fallback to Claude-3
        return use_model(
            model_type=ModelType.ANTHROPIC,
            temperature=0.0
        )

def process_analysis_files(json_path: str, text_path: str, output_dir: str) -> None:
    """Process analysis files and generate markdown using LLM.

    Args:
        json_path: Path to JSON analysis file
        text_path: Path to text analysis file
        output_dir: Directory to save markdown files
    """
    try:
        # Get name from filename
        name = os.path.basename(json_path).replace('_analysis.json', '')
        
        # Special handling for tables description
        if name == "tables description":
            metadata_path = os.path.join(output_dir, "tables_metadata_analysis.txt")
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    logger.info(f"Using existing metadata analysis for {name}")
                    markdown_content = f.read()
                    
                # Write the content and return early
                output_file = os.path.join(output_dir, f'{name}.md')
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                logger.info(f"Generated markdown documentation for {name}")
                return
            else:
                logger.error(f"Missing metadata analysis file: {metadata_path}")
                return
                
        # For all other files, proceed with normal processing
        try:
            with open(text_path, 'r', encoding='utf-8') as f:
                text_analysis = f.read()
        except IOError:
            logger.error(f"Missing text analysis file: {text_path}")
            return

        # Get the file type
        file_type = get_file_type(text_analysis)
        if not file_type:
            logger.info(f"Skipping {os.path.basename(json_path)} - Not a documentation file")
            return

        # Read JSON analysis
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                json_content = f.read()
        except IOError as ioe:
            logger.error(f"Error reading file {json_path}: {str(ioe)}")
            raise

        try:
            json_analysis = json.loads(json_content)
        except json.JSONDecodeError as je:
            logger.error(f"JSON decode error in {json_path}:")
            logger.error(f"Error at line {je.lineno}, col {je.colno}: {je.msg}")
            logger.error(f"Near text: {json_content[max(0, je.pos-50):je.pos+50]}")
            raise
            
        # Get table/database name from the filename
        name = os.path.basename(json_path).replace('_analysis.json', '')

        # Get the tables metadata analysis
        tables_metadata = get_table_metadata(output_dir)
        
        # Initialize LLM agent
        llm_agent = get_llm_agent()
        
        # Create metadata processor
        metadata_processor = TableMetadataProcessor(llm_agent)
        
        # Generate markdown based on file type
        if file_type == "TABLE_DESCRIPTION":
            markdown_content = metadata_processor.enrich_table_documentation(
                table_name=name,
                column_info=json_analysis,
                metadata_text=tables_metadata
            )
        else:  # DATABASE_DESCRIPTION
            markdown_content = metadata_processor.enrich_database_documentation(
                database_info=json_analysis,
                metadata_text=tables_metadata
            )

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Save markdown file
        output_file = os.path.join(output_dir, f'{name}.md')

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        logger.info(f"Generated markdown documentation for {name}")

    except Exception as e:
        logger.error(f"Error processing analysis files for {os.path.basename(json_path)}: {str(e)}")
        #raise

# No standalone execution - this module is used by main.py