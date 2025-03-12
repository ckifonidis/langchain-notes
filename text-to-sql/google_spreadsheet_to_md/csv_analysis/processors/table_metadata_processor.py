"""
Module for processing table metadata from tables_description files.
"""

from typing import Dict, Any, Optional
import pandas as pd
from langchain.chat_models.base import BaseChatModel
from langchain.schema import HumanMessage, SystemMessage

class TableMetadataProcessor:
    """Process and analyze table metadata from tables_description files."""
    
    def __init__(self, chat_model: BaseChatModel):
        """
        Initialize processor with LLM model.
        
        Args:
            chat_model: LangChain chat model for analysis
        """
        self.chat_model = chat_model

    def analyze_tables_description(self, df: pd.DataFrame) -> str:
        """
        Process tables_description data and generate structured analysis.
        
        Args:
            df: DataFrame containing tables description data
            
        Returns:
            String containing structured description of table metadata
        """
        # Convert DataFrame to string representation
        csv_content = df.to_string()
        
        # Create prompt for LLM
        prompt = f"""You are a database documentation expert. Analyze this tables_description data and provide a structured overview of the metadata for each table.

CSV Content:
{csv_content}

For each table in the data, describe:
1. The table's name and primary purpose
2. Technical details like type, partitioning, refresh frequency
3. Data sensitivity and PII fields if any
4. Production details and dependencies
5. Any other relevant metadata

Important guidelines:
1. Group information by table name
2. Include both Greek and English text where present
3. Use clear section headers
4. Present information in a structured, easy-to-read format
5. Focus on completeness and clarity rather than specific formatting

Present the analysis in a way that will be useful as context when generating table documentation later.
"""
        
        # Get response from LLM
        messages = [
            SystemMessage(content="You are a database documentation expert. Provide a clear, structured analysis of the tables metadata."),
            HumanMessage(content=prompt)
        ]
        
        response = self.chat_model.invoke(messages)
        return response.content.strip()

    def enrich_database_documentation(self,
                                  database_info: Dict[str, Any],
                                  metadata_text: Optional[str] = None) -> str:
        """
        Generate enriched markdown documentation for the database.
        
        Args:
            database_info: Dictionary containing database tables information
            metadata_text: Optional metadata analysis from tables_description
            
        Returns:
            Markdown string containing enriched documentation
        """
        # Convert table info to string representation
        table_content = pd.DataFrame(database_info).to_string()
        
        # Create prompt for LLM
        prompt = f"""You are a technical documentation expert. Generate comprehensive markdown documentation for this database:

INPUT INFORMATION:
----------------
TABLES INFORMATION:
{table_content}

TABLES METADATA CONTEXT:
{metadata_text if metadata_text else "No additional metadata available"}

TASK:
-----
Generate clear and comprehensive markdown documentation that includes:

1. A high-level database overview:
   - Purpose and scope of the database
   - Technical architecture and design principles
   - Common patterns and conventions

2. Detailed tables documentation:
   - Group tables by functional area/domain
   - For each table:
     * Purpose and role in the system
     * Technical details (type, partitioning, refresh frequency)
     * Data sensitivity and PII fields
     * Production flow and dependencies
     * Integration points and dependencies

3. Additional Information:
   - Data governance and security considerations
   - Common access patterns
   - Performance considerations
   - Dependencies between tables

DOCUMENTATION GUIDELINES:
----------------------
1. Use clear, technical language suitable for database documentation
2. Include both Greek and English text where present
3. Maintain consistent formatting and structure
4. Highlight important relationships between tables
5. Include any relevant constraints or business rules

FORMAT:
-------
# Database Overview

[Comprehensive database description]

## Architecture and Design

[Technical architecture details]

## Tables

### [Functional Area 1]

#### Table: [Table Name]
[Table description and details]

Technical Details:
- Type: [table type]
- Partitioning: [partition details]
- Refresh: [frequency]
- Source: [data source]
- Ingestion: [process]

[Additional sections for each functional area]

## Security and Governance

[Security considerations and governance details]

## Dependencies and Relationships

[Key table relationships and dependencies]

Provide only the markdown content, no additional explanations."""
        
        # Get response from LLM
        messages = [
            SystemMessage(content="You are a database documentation expert specializing in technical documentation."),
            HumanMessage(content=prompt)
        ]
        
        response = self.chat_model.invoke(messages)
        return response.content.strip()

    def enrich_table_documentation(self,
                                 table_name: str,
                                 column_info: Dict[str, Any],
                                 metadata_text: Optional[str] = None) -> str:
        """
        Generate enriched markdown documentation for a table.
        
        Args:
            table_name: Name of the table
            column_info: Dictionary containing column information
            metadata_text: Optional metadata analysis from tables_description
            
        Returns:
            Markdown string containing enriched documentation
        """
        # Convert column info to string representation
        column_content = pd.DataFrame(column_info).to_string()
        
        # Create prompt for LLM
        prompt = f"""You are a technical documentation expert. Generate comprehensive markdown documentation for this table:

SPREADSHEET INFORMATION:
----------------------
TABLE NAME: {table_name}

DATABASE NAME EXTRACTION:
----------------------
Extract the database name from the spreadsheet title using these rules in order:
1. If title matches pattern "BIG DATA <name> catalog":
   - Use <name> as the database name
2. If title contains both "BIG DATA" and "catalog":
   - Extract text between these markers as database name
3. If neither pattern matches:
   - Remove common words like "data", "catalog", "big"
   - Use the most specific remaining noun
4. Convert final name to lowercase

Example patterns:
- "BIG DATA bank catalog" -> database: "bank"
- "BIG DATA hr system catalog" -> database: "hr"
- "customer data catalog" -> database: "customer"

INPUT INFORMATION:
----------------
COLUMN INFORMATION:
{column_content}

TABLES METADATA CONTEXT:
{metadata_text if metadata_text else "No additional metadata available"}

TASK:
-----
Generate clear and comprehensive markdown documentation that includes:

1. Database name as the main heading (level 1) using the extraction rules above

2. High-level table information (from metadata context):
   - Purpose and role in the system
   - Technical details (type, partitioning, refresh frequency)
   - Data sensitivity and PII fields
   - Production details and dependencies
   - Other relevant metadata

3. A table summarizing all columns with these aspects:
   - Column Name: The name of the column as used in the database
   - Column Type: The data type of the column
   - Column Description: A clear description of what the column represents
   - Column Notes: A natural language paragraph containing:
     * Valid values and constraints
     * Business rules and conditions
     * Dependencies and relationships with other columns
     * System context (stdata/idata/odata) and special handling
     * Any additional relevant information in flowing text
     * Written for vector database analysis and semantic search

Example Column Note:
"This field accepts branch codes like 602 (MyBank) and 603 (Alternative Networks). Used in stdata context and affects terminal ID validation. When branch is 603, terminal IDs have specific meanings: 60301 for ΣΕΠΠΠ, 60302 for OTE. Required for all transactions with validation rules varying by channel. Part of core branch identification system with direct impact on transaction processing and routing."

DOCUMENTATION GUIDELINES:
----------------------
1. Understand both column information and metadata context
2. Include both Greek and English text where present
3. Use proper markdown syntax and clear section headers
4. For each column:
   - Identify its proper name and type
   - Extract or infer a meaningful description
   - Create comprehensive notes using available context
5. Use clear, technical language suitable for database documentation
6. Include any relevant enumerated values or constraints

FORMAT:
-------
# Database Name

## Table: {table_name}

### Overview
[Comprehensive description incorporating metadata context]

### Technical Details
[Available technical metadata, properly organized]

### Columns
| Column Name | Type | Description | Notes |
|-------------|------|-------------|-------|
[Detailed column information with enriched descriptions]

Provide only the markdown content, no additional explanations."""
        
        # Get response from LLM
        messages = [
            SystemMessage(content="You are a database documentation expert specializing in technical documentation."),
            HumanMessage(content=prompt)
        ]
        
        response = self.chat_model.invoke(messages)
        return response.content.strip()