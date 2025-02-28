from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
import json
import os
import pandas as pd
from typing import Dict, Any, List, Tuple

class CSVAnalyzer:
    def __init__(self):
        self.llm = OpenAI(temperature=0)
        self.tools = self._setup_tools()
        self.agent = self._setup_agent()

    def _setup_tools(self) -> list[Tool]:
        """Setup tools for the agent to use in analysis."""
        return [
            Tool(
                name="read_csv",
                func=self._read_csv,
                description="Read a CSV file and return its contents as a string representation"
            ),
            Tool(
                name="read_analysis",
                func=self._read_analysis,
                description="Read the analysis JSON file for a CSV and return its contents"
            ),
            Tool(
                name="analyze_structure",
                func=self._analyze_structure,
                description="Analyze the structure of a CSV file to determine if it's a database description, table description, or sample data"
            )
        ]

    def _setup_agent(self) -> AgentExecutor:
        """Setup the ReAct agent with prompt and tools."""
        template = """
You are an expert data analyst specializing in database structures. Your task is to determine if a CSV file represents:

1. A DATABASE DESCRIPTION (contains a list of tables in a database with their descriptions)
   - Usually has columns like "Table Name", "Description", "Schema", etc.
   - Each row represents a different table in the database
   - May contain information about relationships between tables

2. A TABLE DESCRIPTION/SCHEMA (contains metadata about columns in a specific table)
   - Usually has columns like "Column Name", "Data Type", "Description", etc.
   - Each row represents a different column in the table
   - Often contains information about primary keys, constraints, etc.

3. SAMPLE DATA (contains actual records/examples)
   - Rows represent individual records or entries
   - Columns represent attributes or fields
   - Contains actual data values rather than metadata

4. Something else (specify what it appears to be)

You have access to:
1. The CSV file contents
2. An analysis JSON file containing metadata about the CSV
3. A structure analysis tool that examines patterns in the data

IMPORTANT: Pay special attention to the column names and the content of the rows.
In database/table descriptions, rows typically contain metadata, not actual data records.

Use these tools to make your determination:
{tools}

Question: {input}
{agent_scratchpad}
"""
        prompt = PromptTemplate(
            template=template,
            input_variables=["input", "tools", "agent_scratchpad"],
            partial_variables={"tool_names": [tool.name for tool in self.tools]}
        )

        agent = create_react_agent(self.llm, self.tools, prompt)
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True, handle_parsing_errors=True)

    def _read_csv(self, filename: str) -> str:
        """Read CSV file and return its contents as a string."""
        try:
            filepath = os.path.join("output", filename)
            df = pd.read_csv(filepath)
            return df.to_string()
        except Exception as e:
            return f"Error reading CSV: {str(e)}"

    def _read_analysis(self, filename: str) -> Dict[str, Any]:
        """Read analysis JSON file for a CSV."""
        try:
            analysis_filename = filename.replace(".csv", "_analysis.json")
            filepath = os.path.join("analysis", analysis_filename)
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            return f"Error reading analysis file: {str(e)}"
    
    def _analyze_structure(self, filename: str) -> Dict[str, Any]:
        """
        Analyze the structure of a CSV file to determine if it's a database description,
        table description, or sample data.
        """
        try:
            filepath = os.path.join("output", filename)
            df = pd.read_csv(filepath)
            
            # Get column names
            column_names = df.columns.tolist()
            
            # Check for database description patterns
            db_description_indicators = self._check_database_description(df, column_names)
            
            # Check for table description patterns
            table_description_indicators = self._check_table_description(df, column_names)
            
            # Check for sample data patterns
            sample_data_indicators = self._check_sample_data(df, column_names)
            
            return {
                "filename": filename,
                "row_count": len(df),
                "column_count": len(column_names),
                "column_names": column_names,
                "database_description_score": sum(db_description_indicators[0]),
                "database_description_reasons": db_description_indicators[1],
                "table_description_score": sum(table_description_indicators[0]),
                "table_description_reasons": table_description_indicators[1],
                "sample_data_score": sum(sample_data_indicators[0]),
                "sample_data_reasons": sample_data_indicators[1],
                "likely_type": self._determine_likely_type(
                    db_description_indicators[0],
                    table_description_indicators[0],
                    sample_data_indicators[0]
                )
            }
        except Exception as e:
            return f"Error analyzing structure: {str(e)}"
    
    def _check_database_description(self, df: pd.DataFrame, column_names: List[str]) -> Tuple[List[int], List[str]]:
        """Check if the CSV looks like a database description."""
        scores = []
        reasons = []
        
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
            table_name_col = next(col for col in column_names
                                if col.lower() in table_name_indicators or
                                any(ind in col.lower() for ind in table_name_indicators))
            table_names = df[table_name_col].astype(str).str.strip()
            valid_table_names = table_names.str.match(r'^[a-zA-Z][a-zA-Z0-9_]*$').mean() > 0.7
            scores.append(2 if valid_table_names else 0)
            if valid_table_names:
                reasons.append("Rows contain values that look like valid table names")
        
        return scores, reasons
    
    def _check_table_description(self, df: pd.DataFrame, column_names: List[str]) -> Tuple[List[int], List[str]]:
        """Check if the CSV looks like a table description/schema."""
        scores = []
        reasons = []
        
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
            type_col = next(col for col in column_names
                           if col.lower() in type_indicators or
                           any(ind in col.lower() for ind in type_indicators))
            sql_types = ['int', 'varchar', 'char', 'text', 'date', 'datetime', 'timestamp',
                        'decimal', 'numeric', 'float', 'boolean', 'bool']
            type_values = df[type_col].astype(str).str.lower()
            has_sql_types = any(type_values.str.contains(t).any() for t in sql_types)
            scores.append(2 if has_sql_types else 0)
            if has_sql_types:
                reasons.append("Type column contains SQL data type values")
        
        return scores, reasons
    
    def _check_sample_data(self, df: pd.DataFrame, column_names: List[str]) -> Tuple[List[int], List[str]]:
        """Check if the CSV looks like sample data."""
        scores = []
        reasons = []
        
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
    
    def _determine_likely_type(self, db_scores: List[int], table_scores: List[int],
                              sample_scores: List[int]) -> str:
        """Determine the most likely type based on scores."""
        db_score = sum(db_scores)
        table_score = sum(table_scores)
        sample_score = sum(sample_scores)
        
        if db_score > table_score and db_score > sample_score:
            return "DATABASE_DESCRIPTION"
        elif table_score > db_score and table_score > sample_score:
            return "TABLE_DESCRIPTION"
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

    def analyze_csv(self, csv_filename: str) -> str:
        """Analyze a CSV file and determine its type."""
        return self.agent.invoke({
            "input": f"Analyze the CSV file '{csv_filename}' and its corresponding analysis "
                    f"file to determine if it contains database descriptions, table descriptions, sample data, or something else."
        })["output"]

def main():
    analyzer = CSVAnalyzer()
    
    # Get list of CSV files in output directory
    csv_files = [f for f in os.listdir("output") if f.endswith('.csv')]
    
    print("\nAnalyzing CSV files...\n")
    
    results = {}
    
    for csv_file in csv_files:
        print(f"\n=== Analyzing {csv_file} ===")
        
        # First perform structural analysis
        structure_analysis = analyzer._analyze_structure(csv_file)
        
        if isinstance(structure_analysis, str):  # Error occurred
            print(f"Error: {structure_analysis}")
            continue
            
        likely_type = structure_analysis["likely_type"]
        
        # Print detailed analysis
        print(f"File: {csv_file}")
        print(f"Rows: {structure_analysis['row_count']}")
        print(f"Columns: {structure_analysis['column_count']}")
        print(f"Column Names: {', '.join(structure_analysis['column_names'])}")
        print("\nAnalysis Scores:")
        print(f"  Database Description: {structure_analysis['database_description_score']}")
        print(f"  Table Description: {structure_analysis['table_description_score']}")
        print(f"  Sample Data: {structure_analysis['sample_data_score']}")
        print(f"\nLikely Type: {likely_type}")
        
        # Print reasons for the determination
        print("\nReasons:")
        if structure_analysis['database_description_score'] > 0:
            print("  Database Description Indicators:")
            for reason in structure_analysis['database_description_reasons']:
                print(f"    - {reason}")
                
        if structure_analysis['table_description_score'] > 0:
            print("  Table Description Indicators:")
            for reason in structure_analysis['table_description_reasons']:
                print(f"    - {reason}")
                
        if structure_analysis['sample_data_score'] > 0:
            print("  Sample Data Indicators:")
            for reason in structure_analysis['sample_data_reasons']:
                print(f"    - {reason}")
        
        # Also run the LLM-based analysis for comparison
        llm_result = analyzer.analyze_csv(csv_file)
        print(f"\nLLM Analysis Result: {llm_result}\n")
        
        # Store results
        results[csv_file] = {
            "structural_analysis": likely_type,
            "llm_analysis": llm_result
        }
    
    # Print summary
    if results:
        print("\n=== Analysis Summary ===")
        print(f"Total files analyzed: {len(results)}")
        
        type_counts = {
            "DATABASE_DESCRIPTION": 0,
            "TABLE_DESCRIPTION": 0,
            "SAMPLE_DATA": 0,
            "UNKNOWN": 0,
            "DATABASE_OR_TABLE_DESCRIPTION": 0,
            "DATABASE_DESCRIPTION_OR_SAMPLE_DATA": 0,
            "TABLE_DESCRIPTION_OR_SAMPLE_DATA": 0
        }
        
        for file_result in results.values():
            type_counts[file_result["structural_analysis"]] = type_counts.get(
                file_result["structural_analysis"], 0) + 1
        
        print("\nFile Type Distribution:")
        for type_name, count in type_counts.items():
            if count > 0:
                print(f"  {type_name}: {count}")

if __name__ == "__main__":
    main()