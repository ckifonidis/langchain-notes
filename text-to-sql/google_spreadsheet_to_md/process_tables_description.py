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
from csv_analyzer import CSVAnalyzer
from typing import Dict, Any, List, Optional, Tuple
import time

class TablesDescriptionProcessor:
    """
    Class to process CSV files, identify Tables Description files,
    and output analysis results to text files.
    """
    
    def __init__(self, output_dir: str = "output", use_llm: bool = False):
        """
        Initialize the processor with the output directory path.
        
        Args:
            output_dir: Path to the directory containing CSV files and where analysis files will be saved
            use_llm: Whether to use LLM-based analysis (can be slow and prone to errors)
        """
        self.output_dir = output_dir
        self.analyzer = CSVAnalyzer()
        self.use_llm = use_llm
        
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
            # First perform structural analysis
            structure_analysis = self.analyzer._analyze_structure(csv_filename)
            
            if isinstance(structure_analysis, str):  # Error occurred
                print(f"Error analyzing {csv_filename}: {structure_analysis}")
                return {"error": structure_analysis}
                
            likely_type = structure_analysis["likely_type"]
            
            # Run the LLM-based analysis only if requested
            llm_result = ""
            if self.use_llm:
                try:
                    llm_result = self.analyzer.analyze_csv(csv_filename)
                except Exception as e:
                    llm_result = f"Error in LLM analysis: {str(e)}"
            
            # Additional analysis based on the understanding that in tables descriptions,
            # each CSV row represents a table column and each CSV column represents 
            # some kind of information on the table column
            additional_analysis = self._perform_additional_analysis(csv_filename)
            
            return {
                "filename": csv_filename,
                "structural_analysis": structure_analysis,
                "likely_type": likely_type,
                "llm_analysis": llm_result,
                "additional_analysis": additional_analysis
            }
        except Exception as e:
            print(f"Error analyzing {csv_filename}: {str(e)}")
            return {"error": str(e)}
    
    def _perform_additional_analysis(self, csv_filename: str) -> Dict[str, Any]:
        """
        Perform additional analysis on the CSV file based on the understanding
        that in tables descriptions, each CSV row represents a table column and
        each CSV column represents some kind of information on the table column.
        
        Args:
            csv_filename: Name of the CSV file to analyze
            
        Returns:
            Dictionary containing additional analysis results
        """
        try:
            # Read the CSV file
            csv_path = os.path.join(self.output_dir, csv_filename)
            df = pd.read_csv(csv_path)
            
            # Check if the CSV has columns that typically appear in table descriptions
            column_name_indicators = ['column', 'name', 'field', 'attribute']
            data_type_indicators = ['type', 'datatype', 'data type']
            description_indicators = ['description', 'desc', 'comment', 'notes']
            
            # Check for column name column
            has_column_name = any(
                any(ind in col.lower() for ind in column_name_indicators)
                for col in df.columns
            )
            
            # Check for data type column
            has_data_type = any(
                any(ind in col.lower() for ind in data_type_indicators)
                for col in df.columns
            )
            
            # Check for description column
            has_description = any(
                any(ind in col.lower() for ind in description_indicators)
                for col in df.columns
            )
            
            # Check if rows look like column definitions
            # In a table description, we expect each row to represent a column
            # and the values in each row to be consistent with column metadata
            
            # Get potential column name column
            column_name_col = next(
                (col for col in df.columns if any(ind in col.lower() for ind in column_name_indicators)),
                None
            )
            
            rows_look_like_columns = False
            if column_name_col:
                # Check if values in this column look like valid column names
                column_names = df[column_name_col].astype(str).str.strip()
                valid_column_names = column_names.str.match(r'^[a-zA-Z][a-zA-Z0-9_]*$').mean() > 0.5
                rows_look_like_columns = valid_column_names
            
            # Calculate a score for how likely this is a table description
            table_desc_score = sum([
                3 if has_column_name else 0,
                2 if has_data_type else 0,
                2 if has_description else 0,
                3 if rows_look_like_columns else 0
            ])
            
            # Get column headers that might represent information about table columns
            potential_info_headers = []
            for col in df.columns:
                if col.lower() not in ['', 'unnamed']:
                    potential_info_headers.append(col)
            
            return {
                "has_column_name": has_column_name,
                "has_data_type": has_data_type,
                "has_description": has_description,
                "rows_look_like_columns": rows_look_like_columns,
                "table_desc_score": table_desc_score,
                "potential_info_headers": potential_info_headers
            }
        except Exception as e:
            print(f"Error in additional analysis for {csv_filename}: {str(e)}")
            return {}
    
    def is_tables_description(self, analysis_result: Dict[str, Any]) -> bool:
        """
        Determine if a CSV file is a Tables Description based on analysis results.
        
        Args:
            analysis_result: Dictionary containing analysis results
            
        Returns:
            True if the CSV is a Tables Description, False otherwise
        """
        if "error" in analysis_result:
            return False
            
        # Check structural analysis result
        likely_type = analysis_result.get("likely_type", "")
        if "TABLE_DESCRIPTION" in likely_type:
            return True
            
        # Check additional analysis result
        additional_analysis = analysis_result.get("additional_analysis", {})
        table_desc_score = additional_analysis.get("table_desc_score", 0)
        if table_desc_score >= 5:  # If score is high enough, consider it a table description
            return True
            
        # Check LLM analysis result as a backup if available
        if self.use_llm:
            llm_result = analysis_result.get("llm_analysis", "").upper()
            return "TABLE DESCRIPTION" in llm_result or "TABLE SCHEMA" in llm_result
            
        return False
    
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
    
    def process_tables_description(self, csv_filename: str, analysis_result: Dict[str, Any]) -> Optional[str]:
        """
        Process a Tables Description CSV file and generate analysis text.
        
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
            
            # Add structural analysis reasons
            structural_analysis = analysis_result.get("structural_analysis", {})
            
            if structural_analysis and "table_description_reasons" in structural_analysis:
                analysis_text += "Table Description Indicators:\n"
                for reason in structural_analysis["table_description_reasons"]:
                    analysis_text += f"  - {reason}\n"
                analysis_text += "\n"
            
            # Add additional analysis
            additional_analysis = analysis_result.get("additional_analysis", {})
            if additional_analysis:
                analysis_text += "Additional Analysis:\n"
                for key, value in additional_analysis.items():
                    if key != "potential_info_headers":
                        analysis_text += f"  - {key}: {value}\n"
                analysis_text += "\n"
            
            # Add LLM analysis if available
            llm_analysis = analysis_result.get("llm_analysis", "")
            if llm_analysis and self.use_llm:
                analysis_text += "LLM Analysis:\n"
                analysis_text += f"{llm_analysis}\n\n"
            
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
        processed_count = 0
        skipped_count = 0
        error_count = 0
        
        start_time = time.time()
        
        for i, csv_file in enumerate(csv_files):
            print(f"\nProcessing {i+1}/{len(csv_files)}: {csv_file}...")
            
            try:
                # Analyze the CSV file
                analysis_result = self.analyze_csv(csv_file)
                
                # Check if it's a Tables Description
                if self.is_tables_description(analysis_result):
                    print(f"{csv_file} is a Tables Description. Processing...")
                    tables_description_count += 1
                    
                    # Process the Tables Description
                    analysis_text = self.process_tables_description(csv_file, analysis_result)
                    
                    if analysis_text:
                        # Save the analysis
                        self.save_analysis(csv_file, analysis_text)
                        processed_count += 1
                    else:
                        print(f"Failed to process {csv_file}.")
                        error_count += 1
                else:
                    print(f"{csv_file} is not a Tables Description. Skipping.")
                    skipped_count += 1
            except Exception as e:
                print(f"Error processing {csv_file}: {str(e)}")
                error_count += 1
        
        elapsed_time = time.time() - start_time
        
        print(f"\nProcessing complete in {elapsed_time:.2f} seconds.")
        print(f"Found {tables_description_count} Tables Description files.")
        print(f"Successfully processed: {processed_count}")
        print(f"Skipped (not Tables Description): {skipped_count}")
        print(f"Errors: {error_count}")

def main():
    """
    Main function to run the processor.
    """
    # Set use_llm to False to avoid LLM-related errors and speed up processing
    processor = TablesDescriptionProcessor(use_llm=False)
    processor.process_all_files()

if __name__ == "__main__":
    main()