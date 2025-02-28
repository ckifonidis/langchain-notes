#!/usr/bin/env python3
"""
Script to process CSV files from the output directory, identify Tables Description files,
and output analysis results to text files with _analysis.txt suffix.

Functional requirements:
1. Read one CSV at a time from the output directory.
2. Decide what the CSV describes. There are the following cases:
   - Database description
   - Tables Description
   - Sample data
   - Other
   If the CSV is different from Tables Description, proceed to the next one.
3. The results of the processing should be outputted in the same output directory with the _analysis.txt suffix.

Note: In tables descriptions, each CSV row represents a table column and each CSV column
represents some kind of information on the table column. The information that it represents
is usually the CSV column header.
"""

import os
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
import time
import json
from dotenv import load_dotenv
from langchain.schema import HumanMessage, SystemMessage
from model_selector import ModelType, OpenAIModels, DeepseekModels, use_model

# Load environment variables from .env file
load_dotenv()

class TableDescriptionAnalyzer:
    """
    Class to analyze CSV files and identify Tables Description files.
    """
    
    def __init__(self,
                 output_dir: str = "output",
                 use_llm: bool = True,
                 model_type: ModelType = ModelType.DEEPSEEK,
                 model_name: Optional[str] = DeepseekModels.CODER,
                 temperature: float = 0):
        """
        Initialize the analyzer with the output directory path and model settings.
        
        Args:
            output_dir: Path to the directory containing CSV files and where analysis files will be saved
            use_llm: Whether to use LLM-based analysis to help determine CSV type
            model_type: Type of model to use (OPENAI, ANTHROPIC, etc.)
            model_name: Specific model name to use (defaults to each provider's default model)
            temperature: Model temperature setting (0 for most deterministic output)
        """
        self.output_dir = output_dir
        self.use_llm = use_llm
        self.model_type = model_type
        self.model_name = model_name
        self.temperature = temperature
    
    def get_csv_files(self) -> List[str]:
        """
        Get a list of all CSV files in the output directory.
        
        Returns:
            List of CSV filenames
        """
        return [f for f in os.listdir(self.output_dir) if f.endswith('.csv')]
    
    def analyze_csv(self, csv_filename: str) -> Dict[str, Any]:
        """
        Analyze a CSV file to determine its type.
        
        Args:
            csv_filename: Name of the CSV file to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            # Read the CSV file
            csv_path = os.path.join(self.output_dir, csv_filename)
            df = pd.read_csv(csv_path)
            
            # Analyze the structure of the CSV file
            analysis_result = self._analyze_structure(df)
            
            # Determine likely type based on rule-based analysis
            likely_type = self._determine_likely_type(analysis_result)
            
            # Use LLM for additional analysis if enabled
            llm_analysis = {}
            if self.use_llm:
                try:
                    llm_analysis = self._analyze_with_llm(df, csv_filename)
                    print(f"LLM analysis completed for {csv_filename}")
                except Exception as e:
                    print(f"Error in LLM analysis for {csv_filename}: {str(e)}")
                    llm_analysis = {"error": str(e)}
            
            return {
                "filename": csv_filename,
                "analysis": analysis_result,
                "likely_type": likely_type,
                "llm_analysis": llm_analysis
            }
        except Exception as e:
            print(f"Error analyzing {csv_filename}: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_with_llm(self, df: pd.DataFrame, csv_filename: str) -> Dict[str, Any]:
        """
        Use an LLM to analyze the CSV file and determine its type.
        
        Args:
            df: DataFrame containing the CSV data
            csv_filename: Name of the CSV file
            
        Returns:
            Dictionary containing LLM analysis results
        """
        # First run rule-based analysis
        analysis_result = self._analyze_structure(df)
        table_score = analysis_result.get("table_description_score", 0)
        db_score = analysis_result.get("database_description_score", 0)
        sample_score = analysis_result.get("sample_data_score", 0)
        
        # Get analysis reasons
        table_reasons = analysis_result.get("table_description_reasons", [])
        db_reasons = analysis_result.get("database_description_reasons", [])
        sample_reasons = analysis_result.get("sample_data_reasons", [])
        
        # Prepare a sample of the CSV data for the LLM
        sample_rows = min(10, len(df))
        sample_df = df.head(sample_rows)
        
        # Convert sample to string representation
        sample_str = sample_df.to_string()
        
        # Format the analysis scores and reasons
        analysis_summary = f"""
        Programmatic Analysis Results:
        1. Table Description Score: {table_score}
           Reasons:
           {chr(10).join(f'   - {reason}' for reason in table_reasons)}
        
        2. Database Description Score: {db_score}
           Reasons:
           {chr(10).join(f'   - {reason}' for reason in db_reasons)}
        
        3. Sample Data Score: {sample_score}
           Reasons:
           {chr(10).join(f'   - {reason}' for reason in sample_reasons)}
        """
        
        # Format column names analysis
        column_name_analysis = self._analyze_column_names(df.columns)
        
        # Additional metadata about the file
        file_metadata = f"""
        File Statistics:
        - Total number of rows: {len(df)}
        - Total number of columns: {len(df.columns)}
        - Number of unique values in first column: {df[df.columns[0]].nunique() if len(df.columns) > 0 else 0}

        Column Headers Analysis:
        - Headers: {', '.join(df.columns)}
        - Header Types:
          {chr(10).join(f"  - {col}: {col_type}" for col, col_type in column_name_analysis.items())}
        """
        
        # Count metadata and data columns
        column_types = self._analyze_column_names(df.columns)
        metadata_count = sum(1 for t in column_types.values() if t.startswith('Metadata'))
        data_count = sum(1 for t in column_types.values() if t.startswith('Data'))
        
        # Prepare the prompt for the LLM
        prompt = f"""
        Analyze the following CSV file and determine what it describes. The CSV file is named '{csv_filename}'.
        
        CSV Sample (first {sample_rows} rows):
        {sample_str}

        {file_metadata}

        Here is the programmatic analysis of the file structure:
        {analysis_summary}
        
        Column Header Analysis:
        - Total rows in CSV: {len(df)}
        - Total columns: {len(df.columns)}
        - Metadata-related columns: {metadata_count}
        - Data-related columns: {data_count}
        - Unknown purpose columns: {len(df.columns) - metadata_count - data_count}
        
        Important indicators:
        1. High proportion of metadata columns ({metadata_count}/{len(df.columns)}) suggests this might be a description/documentation file
        2. High proportion of data columns ({data_count}/{len(df.columns)}) suggests this might be actual data records
        3. Total number of rows ({len(df)}) - fewer rows often indicate metadata/description files, more rows suggest actual data records
        
        Key characteristics to consider:
        1. Table Description files:
           - Each ROW describes a COLUMN in a database table
           - Usually have relatively few rows (one per table column)
           - Column headers are mostly metadata-related ('column_name', 'type', 'description', etc.)
           - Content is metadata about table structure
           - Example headers: 'column', 'field', 'type', 'description', 'constraints', etc.
        
        2. Database Description files:
           - Each ROW describes a TABLE in a database
           - Column headers describe table-level properties
           - Usually have metadata-related headers but focused on tables rather than columns
           - Example headers: 'table_name', 'schema', 'partition', 'source', 'production_flow', etc.
        
        3. Sample/Reference Data files:
           - Each ROW is an actual data record
           - Often have many rows of similar data
           - Column headers represent business attributes
           - Content is actual business data, not metadata
           - Example headers: 'id', 'name', 'date', 'amount', 'status', etc.
        
        Given the file's characteristics, especially its column headers, determine if this CSV is one of:
        1. TABLE_DESCRIPTION: Column headers focus on column-level properties
        2. DATABASE_DESCRIPTION: Column headers focus on table-level properties
        3. SAMPLE_DATA: Column headers represent business data attributes
        4. OTHER: None of the above patterns match
        
        Explain your reasoning thoroughly, addressing:
        1. The significance of the column headers and their types
        2. The file's structure and content patterns
        3. Agreement or disagreement with the programmatic analysis
        4. Whether the rows represent metadata (about columns/tables) or actual data records
        
        Then conclude with a final determination of the CSV type.
        """
        
        # Create chat model using instance configuration
        chat_model = use_model(
            model_type=self.model_type,
            model_name=self.model_name,
            temperature=self.temperature
        )
        
        # Format messages for langchain
        messages = [
            SystemMessage(content="You are an expert data analyst specializing in database structures."),
            HumanMessage(content=prompt)
        ]
        
        # Get response from the model
        response = chat_model.invoke(messages)
        
        # Extract the LLM's response
        llm_response = response.content.strip()
        
        # Determine the type based on the LLM's response
        llm_type = "UNKNOWN"
        if "TABLE_DESCRIPTION" in llm_response.upper():
            llm_type = "TABLE_DESCRIPTION"
        elif "DATABASE_DESCRIPTION" in llm_response.upper():
            llm_type = "DATABASE_DESCRIPTION"
        elif "SAMPLE_DATA" in llm_response.upper():
            llm_type = "SAMPLE_DATA"
        elif "OTHER" in llm_response.upper():
            llm_type = "OTHER"
        
        return {
            "response": llm_response,
            "type": llm_type
        }
    
    def _analyze_column_names(self, columns: List[str]) -> Dict[str, str]:
        """
        Analyze column names to determine their likely types and purposes.
        
        Args:
            columns: List of column names
            
        Returns:
            Dictionary mapping column names to their likely types
        """
        # Common indicators for different types of columns
        metadata_indicators = {
            'description': 'Metadata - Description field',
            'type': 'Metadata - Data type field',
            'column': 'Metadata - Column name field',
            'key': 'Metadata - Key/constraint field',
            'constraint': 'Metadata - Key/constraint field',
            'comment': 'Metadata - Description field',
            'table': 'Metadata - Table information field',
            'database': 'Metadata - Database information field',
            'schema': 'Metadata - Schema information field',
            'field': 'Metadata - Column name field',
            'attribute': 'Metadata - Column name field',
            'datatype': 'Metadata - Data type field',
            'nullable': 'Metadata - Constraint field',
            'primary': 'Metadata - Key field',
            'foreign': 'Metadata - Key field',
            'index': 'Metadata - Index field',
            'partition': 'Metadata - Table property field',
            'source': 'Metadata - Source information field',
            'production': 'Metadata - Environment field',
            'flow': 'Metadata - Process field',
            'pending': 'Metadata - Status field'
        }
        
        # Common indicators for data/content columns
        data_indicators = {
            'id': 'Data - Identifier field',
            'date': 'Data - Temporal field',
            'time': 'Data - Temporal field',
            'name': 'Data - Label field',
            'code': 'Data - Code field',
            'value': 'Data - Value field',
            'amount': 'Data - Numeric field',
            'status': 'Data - Status field',
            'count': 'Data - Numeric field',
            'total': 'Data - Numeric field',
            'price': 'Data - Numeric field',
            'cost': 'Data - Numeric field'
        }
        
        result = {}
        
        for col in columns:
            col_lower = col.lower()
            
            # First check for metadata indicators
            metadata_match = False
            for indicator, type_desc in metadata_indicators.items():
                if indicator in col_lower:
                    result[col] = type_desc
                    metadata_match = True
                    break
            
            # If not metadata, check for data indicators
            if not metadata_match:
                data_match = False
                for indicator, type_desc in data_indicators.items():
                    if indicator in col_lower:
                        result[col] = type_desc
                        data_match = True
                        break
                
                # If neither metadata nor data, mark as unknown
                if not data_match:
                    result[col] = 'Unknown purpose'
        
        return result

    def _analyze_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze the structure of a CSV file to determine if it's a database description,
        table description, or sample data.
        
        Args:
            df: DataFrame containing the CSV data
            
        Returns:
            Dictionary containing analysis results
        """
        # Check for table description patterns
        table_description_indicators, table_description_reasons = self._check_table_description(df)
        
        # Check for database description patterns
        database_description_indicators, database_description_reasons = self._check_database_description(df)
        
        # Check for sample data patterns
        sample_data_indicators, sample_data_reasons = self._check_sample_data(df)
        
        return {
            "row_count": len(df),
            "column_count": len(df.columns),
            "column_names": df.columns.tolist(),
            "table_description_score": sum(table_description_indicators),
            "table_description_reasons": table_description_reasons,
            "database_description_score": sum(database_description_indicators),
            "database_description_reasons": database_description_reasons,
            "sample_data_score": sum(sample_data_indicators),
            "sample_data_reasons": sample_data_reasons
        }
    
    def _check_table_description(self, df: pd.DataFrame) -> Tuple[List[int], List[str]]:
        """
        Check if the CSV looks like a table description/schema.
        
        Args:
            df: DataFrame containing the CSV data
            
        Returns:
            Tuple containing a list of scores and a list of reasons
        """
        scores = []
        reasons = []
        
        column_names = df.columns.tolist()
        
        # Check for column name column
        col_name_indicators = ['column', 'column_name', 'columnname', 'field', 'attribute', 'name']
        has_col_name = any(col.lower() in col_name_indicators or
                          any(ind in col.lower() for ind in col_name_indicators)
                          for col in column_names)
        scores.append(3 if has_col_name else 0)
        if has_col_name:
            reasons.append("Contains column that appears to list column names")
        
        # Check for data type column
        type_indicators = ['type', 'data_type', 'datatype', 'data type']
        has_type_col = any(col.lower() in type_indicators or
                          any(ind in col.lower() for ind in type_indicators)
                          for col in column_names)
        scores.append(3 if has_type_col else 0)
        if has_type_col:
            reasons.append("Contains column for data types")
        
        # Check for description column
        desc_indicators = ['description', 'desc', 'comment', 'notes', 'details']
        has_desc_col = any(col.lower() in desc_indicators or
                          any(ind in col.lower() for ind in desc_indicators)
                          for col in column_names)
        scores.append(2 if has_desc_col else 0)
        if has_desc_col:
            reasons.append("Contains column for field descriptions")
        
        # Check for key/constraint indicators
        key_indicators = ['key', 'primary', 'foreign', 'constraint', 'index', 'unique']
        has_key_col = any(col.lower() in key_indicators or
                         any(ind in col.lower() for ind in key_indicators)
                         for col in column_names)
        scores.append(2 if has_key_col else 0)
        if has_key_col:
            reasons.append("Contains column referencing keys or constraints")
        
        # Check if type column contains SQL data types
        if has_type_col:
            type_col = next((col for col in column_names
                           if col.lower() in type_indicators or
                           any(ind in col.lower() for ind in type_indicators)), None)
            if type_col:
                sql_types = ['int', 'varchar', 'char', 'text', 'date', 'datetime', 'timestamp',
                            'decimal', 'numeric', 'float', 'boolean', 'bool', 'string']
                type_values = df[type_col].astype(str).str.lower()
                has_sql_types = any(type_values.str.contains(t).any() for t in sql_types)
                scores.append(2 if has_sql_types else 0)
                if has_sql_types:
                    reasons.append("Type column contains SQL data type values")
        
        # Check if rows look like column definitions
        # In a table description, we expect each row to represent a column
        if has_col_name:
            col_name_col = next((col for col in column_names
                               if col.lower() in col_name_indicators or
                               any(ind in col.lower() for ind in col_name_indicators)), None)
            if col_name_col:
                # Check if values in this column look like valid column names
                column_names_values = df[col_name_col].astype(str).str.strip()
                valid_column_names = column_names_values.str.match(r'^[a-zA-Z][a-zA-Z0-9_]*$').mean() > 0.5
                scores.append(3 if valid_column_names else 0)
                if valid_column_names:
                    reasons.append("Rows contain values that look like valid column names")
        
        return scores, reasons
    
    def _check_database_description(self, df: pd.DataFrame) -> Tuple[List[int], List[str]]:
        """
        Check if the CSV looks like a database description.
        
        Args:
            df: DataFrame containing the CSV data
            
        Returns:
            Tuple containing a list of scores and a list of reasons
        """
        scores = []
        reasons = []
        
        column_names = df.columns.tolist()
        
        # Check for table name column
        table_name_indicators = ['table', 'table_name', 'tablename', 'name', 'entity']
        has_table_name_col = any(col.lower() in table_name_indicators or
                                any(ind in col.lower() for ind in table_name_indicators)
                                for col in column_names)
        scores.append(3 if has_table_name_col else 0)
        if has_table_name_col:
            reasons.append("Contains column that appears to list table names")
        
        # Check for description column
        desc_indicators = ['description', 'desc', 'comment', 'notes', 'details']
        has_desc_col = any(col.lower() in desc_indicators or
                          any(ind in col.lower() for ind in desc_indicators)
                          for col in column_names)
        scores.append(2 if has_desc_col else 0)
        if has_desc_col:
            reasons.append("Contains column for table descriptions")
        
        # Check for schema/database column
        schema_indicators = ['schema', 'database', 'db', 'catalog']
        has_schema_col = any(col.lower() in schema_indicators or
                            any(ind in col.lower() for ind in schema_indicators)
                            for col in column_names)
        scores.append(1 if has_schema_col else 0)
        if has_schema_col:
            reasons.append("Contains column referencing schema or database")
        
        # Check if rows look like table names (short, often snake_case or PascalCase)
        if has_table_name_col:
            table_name_col = next((col for col in column_names
                                 if col.lower() in table_name_indicators or
                                 any(ind in col.lower() for ind in table_name_indicators)), None)
            if table_name_col:
                table_names = df[table_name_col].astype(str).str.strip()
                valid_table_names = table_names.str.match(r'^[a-zA-Z][a-zA-Z0-9_]*$').mean() > 0.7
                scores.append(2 if valid_table_names else 0)
                if valid_table_names:
                    reasons.append("Rows contain values that look like valid table names")
        
        return scores, reasons
    
    def _check_sample_data(self, df: pd.DataFrame) -> Tuple[List[int], List[str]]:
        """
        Check if the CSV looks like sample data.
        
        Args:
            df: DataFrame containing the CSV data
            
        Returns:
            Tuple containing a list of scores and a list of reasons
        """
        scores = []
        reasons = []
        
        column_names = df.columns.tolist()
        
        # Check for high row count relative to column count
        row_to_col_ratio = len(df) / len(column_names) if len(column_names) > 0 else 0
        high_row_ratio = row_to_col_ratio > 5  # More than 5 rows per column suggests sample data
        scores.append(2 if high_row_ratio else 0)
        if high_row_ratio:
            reasons.append(f"High row-to-column ratio ({row_to_col_ratio:.1f}), suggesting sample data")
        
        # Check for absence of metadata columns
        metadata_indicators = ['column', 'type', 'description', 'key', 'constraint', 'table']
        has_metadata_cols = any(any(ind in col.lower() for ind in metadata_indicators)
                               for col in column_names)
        scores.append(2 if not has_metadata_cols else 0)
        if not has_metadata_cols:
            reasons.append("Column names don't appear to be metadata-related")
        
        # Check for numeric columns with varied values (suggesting actual data)
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            varied_values = any(df[col].nunique() > 5 for col in numeric_cols)
            scores.append(2 if varied_values else 0)
            if varied_values:
                reasons.append("Contains numeric columns with varied values")
        
        # Check for date columns with varied values
        date_indicators = ['date', 'time', 'day', 'month', 'year']
        potential_date_cols = [col for col in column_names
                              if any(ind in col.lower() for ind in date_indicators)]
        if potential_date_cols:
            varied_dates = any(df[col].nunique() > 3 for col in potential_date_cols
                              if col in df.columns)
            scores.append(1 if varied_dates else 0)
            if varied_dates:
                reasons.append("Contains date-like columns with varied values")
        
        return scores, reasons
    
    def _determine_likely_type(self, analysis: Dict[str, Any]) -> str:
        """
        Determine the most likely type based on analysis scores.
        
        Args:
            analysis: Dictionary containing analysis results
            
        Returns:
            String indicating the likely type
        """
        table_score = analysis.get("table_description_score", 0)
        db_score = analysis.get("database_description_score", 0)
        sample_score = analysis.get("sample_data_score", 0)
        
        if table_score > db_score and table_score > sample_score:
            return "TABLE_DESCRIPTION"
        elif db_score > table_score and db_score > sample_score:
            return "DATABASE_DESCRIPTION"
        elif sample_score > db_score and sample_score > table_score:
            return "SAMPLE_DATA"
        else:
            # If scores are tied or all low, make a best guess
            if max(db_score, table_score, sample_score) < 3:
                return "UNKNOWN"
            elif db_score == table_score and db_score > sample_score:
                return "DATABASE_OR_TABLE_DESCRIPTION"
            elif db_score == sample_score and db_score > table_score:
                return "DATABASE_DESCRIPTION_OR_SAMPLE_DATA"
            elif table_score == sample_score and table_score > db_score:
                return "TABLE_DESCRIPTION_OR_SAMPLE_DATA"
            else:
                return "UNKNOWN"
    
    def get_file_type(self, analysis_result: Dict[str, Any]) -> str:
        """
        Determine the type of CSV file based on LLM analysis results.
        Falls back to rule-based scoring only if LLM is uncertain.
        
        Args:
            analysis_result: Dictionary containing analysis results
            
        Returns:
            String indicating the file type: 'TABLE_DESCRIPTION', 'DATABASE_DESCRIPTION', 'SAMPLE_DATA', or 'OTHER'
        """
        if "error" in analysis_result:
            return "OTHER"
        
        # Get LLM analysis and rule-based analysis
        llm_analysis = analysis_result.get("llm_analysis", {})
        rule_based_type = analysis_result.get("likely_type", "")
        analysis = analysis_result.get("analysis", {})
        table_score = analysis.get("table_description_score", 0)
        db_score = analysis.get("database_description_score", 0)
        
        # If LLM analysis is available, prioritize its decision
        if llm_analysis and "type" in llm_analysis:
            llm_type = llm_analysis.get("type", "")
            
            # If LLM confidently identifies the type
            if llm_type in ["TABLE_DESCRIPTION", "DATABASE_DESCRIPTION", "SAMPLE_DATA", "OTHER"]:
                print(f"LLM identified as {llm_type}")
                return llm_type
            
            # If LLM type is UNKNOWN or not clearly identified, it's uncertain
            print(f"LLM analysis uncertain, falling back to rule-based scoring")
        else:
            print(f"No LLM analysis available, using rule-based scoring")
        
        # Fall back to rule-based analysis only if LLM is uncertain or not available
        if "TABLE_DESCRIPTION" in rule_based_type:
            return "TABLE_DESCRIPTION"
        elif "DATABASE_DESCRIPTION" in rule_based_type:
            return "DATABASE_DESCRIPTION"
            
        # Check scores
        if table_score >= 5:  # If score is high enough, consider it a table description
            return "TABLE_DESCRIPTION"
        elif db_score >= 5:  # If score is high enough, consider it a database description
            return "DATABASE_DESCRIPTION"
            
        return "OTHER"
    
    def extract_table_info(self, df: pd.DataFrame) -> Tuple[Optional[str], List[Dict[str, Any]]]:
        """
        Extract table information from a Tables Description DataFrame.
        
        Args:
            df: DataFrame containing table description data
            
        Returns:
            Tuple containing table name (if found) and list of column information dictionaries
        """
        # Try to determine the table name from the filename or content
        table_name = None
        
        # Extract column information
        columns_info = []
        
        # Find the column name column
        column_name_indicators = ['column', 'name', 'field', 'attribute']
        column_name_col = next(
            (col for col in df.columns if any(ind in col.lower() for ind in column_name_indicators)),
            None
        )
        
        if column_name_col:
            # For each row (which represents a column in the described table)
            for _, row in df.iterrows():
                column_info = {}
                
                # Extract column name
                column_info['name'] = row[column_name_col]
                
                # Extract other information about the column
                for col in df.columns:
                    if col != column_name_col and pd.notna(row[col]):
                        # Use the column header as the key and the cell value as the value
                        column_info[col] = row[col]
                
                columns_info.append(column_info)
        
        return table_name, columns_info
    
    def process_table_columns_description(self, csv_filename: str, analysis_result: Dict[str, Any]) -> Optional[str]:
        """
        Process a table columns description CSV file (where each row describes a column) and generate analysis text.
        
        Args:
            csv_filename: Name of the CSV file to process
            analysis_result: Dictionary containing analysis results
            
        Returns:
            Analysis text or None if processing failed
        """
        try:
            # Read the CSV file
            csv_path = os.path.join(self.output_dir, csv_filename)
            df = pd.read_csv(csv_path)
            
            # Extract table information
            table_name, columns_info = self.extract_table_info(df)
            
            # Generate analysis text
            analysis_text = f"Analysis of {csv_filename}\n"
            analysis_text += "=" * (len(analysis_text) - 1) + "\n\n"
            
            # Basic file information
            analysis_text += f"File Type: Tables Description\n"
            if table_name:
                analysis_text += f"Table Name: {table_name}\n"
            analysis_text += f"Number of Columns in CSV: {len(df.columns)}\n"
            analysis_text += f"Number of Rows in CSV: {len(df)}\n\n"
            
            # Explanation of table description structure
            analysis_text += "Structure Explanation:\n"
            analysis_text += "-" * 20 + "\n"
            analysis_text += "This is a Tables Description file where:\n"
            analysis_text += "- Each ROW represents a COLUMN in the described database table\n"
            analysis_text += "- Each COLUMN in this CSV represents information about the database table columns\n"
            analysis_text += "- The CSV column headers indicate what information is provided about each database column\n\n"
            
            # CSV Column Headers (which represent information types about table columns)
            analysis_text += "CSV Column Headers (Information Types):\n"
            analysis_text += "-" * 20 + "\n"
            for col in df.columns:
                analysis_text += f"- {col}\n"
            analysis_text += "\n"
            
            # Described Table Structure
            analysis_text += "Described Table Structure:\n"
            analysis_text += "-" * 20 + "\n"
            analysis_text += f"Number of Columns in Described Table: {len(columns_info)}\n\n"
            
            # Column information
            analysis_text += "Column Information:\n"
            analysis_text += "-" * 20 + "\n"
            
            for i, col_info in enumerate(columns_info):
                if 'name' in col_info:
                    analysis_text += f"Column {i+1}: {col_info['name']}\n"
                    
                    # Add other information about the column
                    for key, value in col_info.items():
                        if key != 'name':
                            analysis_text += f"  {key}: {value}\n"
                    
                    analysis_text += "\n"
            
            # Analysis details
            analysis_text += "Analysis Details:\n"
            analysis_text += "-" * 20 + "\n"
            
            # Add analysis reasons
            analysis = analysis_result.get("analysis", {})
            
            if "table_description_reasons" in analysis:
                analysis_text += "Table Description Indicators:\n"
                for reason in analysis["table_description_reasons"]:
                    analysis_text += f"  - {reason}\n"
                analysis_text += "\n"
            
            # Add LLM analysis if available
            llm_analysis = analysis_result.get("llm_analysis", {})
            if llm_analysis and "response" in llm_analysis:
                analysis_text += "LLM Analysis:\n"
                analysis_text += "-" * 20 + "\n"
                analysis_text += f"Type determined by LLM: {llm_analysis.get('type', 'UNKNOWN')}\n\n"
                analysis_text += "LLM Reasoning:\n"
                analysis_text += f"{llm_analysis['response']}\n\n"
            
            return analysis_text
            
        except Exception as e:
            print(f"Error processing {csv_filename}: {str(e)}")
            return None
    
    def save_analysis(self, csv_filename: str, analysis_text: str) -> None:
        """
        Save analysis text to a file with _analysis.txt suffix.
        
        Args:
            csv_filename: Name of the CSV file
            analysis_text: Analysis text to save
        """
        # Generate output filename
        output_filename = csv_filename.replace(".csv", "_analysis.txt")
        output_path = os.path.join(self.output_dir, output_filename)
        
        # Save analysis text to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(analysis_text)
            
        print(f"Analysis saved to {output_path}")
    
    def process_database_description(self, csv_filename: str, analysis_result: Dict[str, Any]) -> Optional[str]:
        """
        Process a database description CSV file (where each row describes a table) and generate analysis text.
        
        Args:
            csv_filename: Name of the CSV file to process
            analysis_result: Dictionary containing analysis results
            
        Returns:
            Analysis text or None if processing failed
        """
        try:
            # Read the CSV file
            csv_path = os.path.join(self.output_dir, csv_filename)
            df = pd.read_csv(csv_path)
            
            # Generate analysis text
            analysis_text = f"Analysis of {csv_filename}\n"
            analysis_text += "=" * (len(analysis_text) - 1) + "\n\n"
            
            # Basic file information
            analysis_text += f"File Type: Database Description\n"
            analysis_text += f"Number of Columns in CSV: {len(df.columns)}\n"
            analysis_text += f"Number of Rows in CSV: {len(df)}\n\n"
            
            # Explanation of database description structure
            analysis_text += "Structure Explanation:\n"
            analysis_text += "-" * 20 + "\n"
            analysis_text += "This is a Database Description file where:\n"
            analysis_text += "- Each ROW describes a TABLE in the database\n"
            analysis_text += "- Each COLUMN describes table-level properties\n"
            analysis_text += "- The CSV column headers indicate what information is provided about each table\n\n"
            
            # CSV Column Headers
            analysis_text += "CSV Column Headers (Information Types):\n"
            analysis_text += "-" * 20 + "\n"
            for col in df.columns:
                analysis_text += f"- {col}\n"
            analysis_text += "\n"
            
            # Tables Information
            analysis_text += "Tables Information:\n"
            analysis_text += "-" * 20 + "\n"
            
            # Find table name column (using the Big_Data_Table column or similar)
            table_name_indicators = ['table', 'table_name', 'tablename', 'big_data_table']
            table_name_col = next(
                (col for col in df.columns if any(ind in col.lower() for ind in table_name_indicators)),
                df.columns[0]  # Fallback to first column if no obvious table name column
            )
            
            # Process each table
            for i, row in df.iterrows():
                table_name = row[table_name_col]
                analysis_text += f"Table {i+1}: {table_name}\n"
                
                # Add other information about the table
                for col in df.columns:
                    if col != table_name_col and pd.notna(row[col]):
                        analysis_text += f"  {col}: {row[col]}\n"
                
                analysis_text += "\n"
            
            # Analysis details
            analysis_text += "Analysis Details:\n"
            analysis_text += "-" * 20 + "\n"
            
            # Add analysis reasons
            analysis = analysis_result.get("analysis", {})
            
            if "database_description_reasons" in analysis:
                analysis_text += "Database Description Indicators:\n"
                for reason in analysis["database_description_reasons"]:
                    analysis_text += f"  - {reason}\n"
                analysis_text += "\n"
            
            # Add LLM analysis if available
            llm_analysis = analysis_result.get("llm_analysis", {})
            if llm_analysis and "response" in llm_analysis:
                analysis_text += "LLM Analysis:\n"
                analysis_text += "-" * 20 + "\n"
                analysis_text += f"Type determined by LLM: {llm_analysis.get('type', 'UNKNOWN')}\n\n"
                analysis_text += "LLM Reasoning:\n"
                analysis_text += f"{llm_analysis['response']}\n\n"
            
            return analysis_text
            
        except Exception as e:
            print(f"Error processing {csv_filename}: {str(e)}")
            return None

    def process_all_files(self) -> None:
        """
        Process all CSV files in the output directory.
        """
        csv_files = self.get_csv_files()
        
        if not csv_files:
            print("No CSV files found in the output directory.")
            return
            
        print(f"Found {len(csv_files)} CSV files in the output directory.")
        
        tables_description_count = 0
        database_description_count = 0
        processed_count = 0
        skipped_count = 0
        error_count = 0
        
        start_time = time.time()
        
        for i, csv_file in enumerate(csv_files):
            print(f"\nProcessing {i+1}/{len(csv_files)}: {csv_file}...")
            
            try:
                # Analyze the CSV file
                analysis_result = self.analyze_csv(csv_file)
                file_type = self.get_file_type(analysis_result)
                
                analysis_text = None
                
                # Process based on file type
                if file_type == "TABLE_DESCRIPTION":
                    print(f"{csv_file} is a Table Columns Description. Processing...")
                    tables_description_count += 1
                    analysis_text = self.process_table_columns_description(csv_file, analysis_result)
                    
                elif file_type == "DATABASE_DESCRIPTION":
                    print(f"{csv_file} is a Database Description. Processing...")
                    database_description_count += 1
                    analysis_text = self.process_database_description(csv_file, analysis_result)
                    
                if analysis_text:
                    # Save the analysis
                    self.save_analysis(csv_file, analysis_text)
                    processed_count += 1
                else:
                    print(f"Failed to process {csv_file}.")
                    error_count += 1
                    
                if file_type in ["SAMPLE_DATA", "OTHER"]:
                    print(f"{csv_file} is {file_type}. Skipping.")
                    skipped_count += 1
                    
            except Exception as e:
                print(f"Error processing {csv_file}: {str(e)}")
                error_count += 1
        
        elapsed_time = time.time() - start_time
        
        print(f"\nProcessing complete in {elapsed_time:.2f} seconds.")
        print(f"Found {tables_description_count} Table Columns Description files.")
        print(f"Found {database_description_count} Database Description files.")
        print(f"Successfully processed: {processed_count}")
        print(f"Skipped (Sample Data or Other): {skipped_count}")
        print(f"Errors: {error_count}")

def main():
    """
    Main function to run the analyzer.
    """
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Analyze CSV files and identify Tables Description files.')
    parser.add_argument('--no-llm', action='store_true', help='Disable LLM-based analysis')
    parser.add_argument('--output-dir', type=str, default='output',
                       help='Directory containing CSV files and where analysis files will be saved')
    parser.add_argument('--model-type', type=str, choices=['openai', 'anthropic', 'deepseek'],
                       default='deepseek', help='Type of model to use')
    parser.add_argument('--model-name', type=str,
                       help='Specific model name (default: deepseek-coder)')
    parser.add_argument('--temperature', type=float, default=0,
                       help='Model temperature (0-1, default: 0)')
    args = parser.parse_args()
    
    # Map model type string to enum
    model_type_map = {
        'openai': ModelType.OPENAI,
        'anthropic': ModelType.ANTHROPIC,
        'deepseek': ModelType.DEEPSEEK
    }
    
    # Create analyzer with specified options
    analyzer = TableDescriptionAnalyzer(
        output_dir=args.output_dir,
        use_llm=not args.no_llm,
        model_type=model_type_map[args.model_type],
        model_name=args.model_name,
        temperature=args.temperature
    )
    
    # Process all files
    analyzer.process_all_files()

if __name__ == "__main__":
    main()