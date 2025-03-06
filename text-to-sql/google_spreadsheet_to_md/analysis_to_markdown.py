import os
import json
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def is_table_description(text_analysis: str) -> bool:
    """Check if the analysis is for a table description.

    Args:
        text_analysis: The text analysis content

    Returns:
        bool: True if this is a table description
    """
    return ("Type determined by LLM: TABLE_DESCRIPTION" in text_analysis) and \
           ("File Type: Tables Description" in text_analysis)

def create_llm_prompt(json_analysis: Dict[str, Any], text_analysis: str) -> str:
    """Create a prompt for the LLM to generate markdown documentation.

    Args:
        json_analysis: The JSON analysis data
        text_analysis: The text analysis content

    Returns:
        String containing the prompt for the LLM
    """
    # Extract table name from JSON
    table_name = json_analysis.get('sheet_name', '')

    return f"""You are a technical documentation expert. Generate a markdown (.md) documentation for a database table analyzing both the structured (JSON) and textual analysis provided.

INPUT INFORMATION:
----------------
JSON Analysis:
{json.dumps(json_analysis, indent=2)}

Text Analysis:
{text_analysis}

TASK:
-----
Generate a clear and comprehensive markdown documentation that includes:

1. Database name as the main heading (level 1)
2. Table name "{table_name}" as a subheading (level 2)
3. A table summarizing all columns with these aspects:
   - Column Name: The name of the column as used in the database
   - Column Type: The data type of the column
   - Column Description: A clear description of what the column represents

DOCUMENTATION GUIDELINES:
----------------------
1. Understand the column information from both the JSON and text analysis
2. For each column:
   - Identify its proper name from the available fields
   - Determine its actual data type
   - Extract or infer a meaningful description from the available information
3. If a column's description is not explicitly provided, infer it from:
   - The column name itself
   - Any patterns in the data
   - Related information in the analysis
4. Use clear, technical language suitable for database documentation
5. Include any relevant enumerated values or constraints if present

FORMAT REQUIREMENTS:
-----------------
- Use proper markdown syntax
- Structure the column table with aligned columns
- Escape any pipe characters (|) in content
- Return only the markdown content with no additional text or explanations

Generate the markdown documentation now:"""

def get_llm_agent():
    """Initialize and return an LLM agent.
    
    Returns:
        The initialized LLM agent (trying Deepseek first, falling back to Claude)
    """
    from model_selector import ModelType, use_model

    try:
        # Try Deepseek first
        return use_model(
            model_type=ModelType.DEEPSEEK,
            model_name="deepseek-chat",
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

def get_llm_response(prompt: str) -> str:
    """Get markdown content from LLM.
    
    Args:
        prompt: The prompt to send to LLM
        
    Returns:
        String containing the generated markdown content
    """
    try:
        # Initialize LLM agent
        llm_agent = get_llm_agent()
        
        # Create message for the LLM
        messages = [
            {
                "role": "system",
                "content": """You are a technical documentation expert specializing in database documentation. Your task is to:
                1. Analyze both structured (JSON) and unstructured (text) information about database tables
                2. Understand the actual meaning and purpose of each column by examining all available information
                3. Generate clear, accurate technical documentation that helps users understand the table structure
                4. Use your expertise to infer meaningful descriptions when they're not explicitly provided
                5. Recognize patterns in column names and data types to provide better documentation"""
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        # Get response from LLM
        response = llm_agent.invoke(messages)

        # Extract the markdown content from response
        return response.content

    except Exception as e:
        logger.error(f"Error getting LLM response: {str(e)}")
        raise

def process_analysis_files(json_path: str, text_path: str, output_dir: str) -> None:
    """Process analysis files and generate markdown using LLM.

    Args:
        json_path: Path to JSON analysis file
        text_path: Path to text analysis file
        output_dir: Directory to save markdown files
    """
    try:
        # Read text analysis first to check file type
        with open(text_path, 'r', encoding='utf-8') as f:
            text_analysis = f.read()

        # Skip if not a table description
        if not is_table_description(text_analysis):
            logger.info(f"Skipping {os.path.basename(json_path)} - Not a table description file")
            return

        # Read JSON analysis
        with open(json_path, 'r', encoding='utf-8') as f:
            json_analysis = json.load(f)

        # Create prompt for LLM
        prompt = create_llm_prompt(json_analysis, text_analysis)

        # Get markdown from LLM
        markdown_content = get_llm_response(prompt)

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Save markdown file
        table_name = os.path.basename(json_path).replace('_analysis.json', '')
        output_file = os.path.join(output_dir, f'{table_name}.md')

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        logger.info(f"Generated markdown documentation for {table_name}")

    except Exception as e:
        logger.error(f"Error processing analysis files: {str(e)}")
        #raise

# No standalone execution - this module is used by main.py