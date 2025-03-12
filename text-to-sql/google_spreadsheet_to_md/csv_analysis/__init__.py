"""
CSV Analysis package initialization.
"""

# Core analysis functions
from .column_analyzer import analyze_column_names
from .file_operations import get_csv_files, save_analysis, read_csv_file
from .csv_analysis import analyze_structure, determine_likely_type
from .llm_analyzer import analyze_with_llm

# Processors
from .processors import (
    FileProcessor,
    process_table_description,
    process_database_description,
    TableMetadataProcessor
)

__all__ = [
    # Core functions
    'analyze_column_names',
    'get_csv_files',
    'save_analysis',
    'read_csv_file',
    'analyze_structure',
    'determine_likely_type',
    'analyze_with_llm',
    
    # Processors
    'FileProcessor',
    'process_table_description',
    'process_database_description',
    'TableMetadataProcessor'
]