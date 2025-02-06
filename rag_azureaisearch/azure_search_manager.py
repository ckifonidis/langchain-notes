from typing import List, Dict, Any
import logging
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain.schema import Document
import requests
import json
from urllib.parse import urlparse
from config import (
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_KEY,
    AZURE_SEARCH_INDEX_NAME,
    OPENAI_API_KEY,
    LOG_FILE,
    LOG_FORMAT,
    LOG_LEVEL
)

# Azure Search API version
API_VERSION = "2023-11-01"

# Configure logging to both file and console
logger = logging.getLogger('AzureSearchManager')
logger.setLevel(logging.getLevelName(LOG_LEVEL))

# Global logging flag
_logging_enabled = True

def enable_logging():
    """Enable logging for AzureSearchManager"""
    global _logging_enabled
    _logging_enabled = True
    log(logging.INFO, "Logging enabled for AzureSearchManager")

def disable_logging():
    """Disable logging for AzureSearchManager"""
    global _logging_enabled
    log(logging.INFO, "Logging disabled for AzureSearchManager")
    _logging_enabled = False

def log(level: int, message: str):
    """Log a message if logging is enabled"""
    if _logging_enabled:
        logger.log(level, message)

# Create formatter
formatter = logging.Formatter(LOG_FORMAT)

# File handler
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Prevent logging from propagating to the root logger
logger.propagate = False

class AzureSearchManager:
    def _get_index_schema(self) -> dict:
        """
        Get the schema of the existing search index
        Returns:
            dict: Index schema or None if index doesn't exist
        """
        try:
            headers = {
                'Content-Type': 'application/json',
                'api-key': AZURE_SEARCH_KEY
            }
            
            response = requests.get(
                f"{AZURE_SEARCH_ENDPOINT}/indexes/{AZURE_SEARCH_INDEX_NAME}?api-version={API_VERSION}",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                log(logging.INFO, f"Index {AZURE_SEARCH_INDEX_NAME} does not exist")
                return None
            else:
                log(logging.ERROR, f"Failed to get index schema: {response.text}")
                return None
                
        except Exception as e:
            log(logging.ERROR, f"Error getting index schema: {str(e)}")
            return None

    def _convert_to_schema_type(self, value: Any, field_type: str) -> Any:
        """
        Convert a value to the correct type based on the schema
        """
        if value is None:
            return None
            
        if field_type == 'Edm.String':
            return str(value)
        elif field_type == 'Edm.Int32':
            return int(value)
        elif field_type == 'Edm.Int64':
            return int(value)
        elif field_type == 'Edm.Double':
            return float(value)
        elif field_type == 'Edm.Boolean':
            return bool(value)
        else:
            return str(value)  # Default to string for unknown types

    def __init__(self):
        """Initialize Azure Search with OpenAI embeddings"""
        try:
            log(logging.INFO, "Initializing OpenAI embeddings...")
            self.embeddings = OpenAIEmbeddings(
                api_key=OPENAI_API_KEY,
                model="text-embedding-3-small",
                show_progress_bar = True
            )
            
            # Test embeddings
            try:
                self.embeddings.embed_query("test")
            except Exception as e:
                error_msg = (
                    f"OpenAI embeddings failed. Please verify your OpenAI API key. Error: {str(e)}"
                )
                log(logging.ERROR, error_msg)
                raise ValueError(error_msg)

            # Initialize Azure Search vector store
            self.vector_store = AzureSearch(
                azure_search_endpoint=AZURE_SEARCH_ENDPOINT,
                azure_search_key=AZURE_SEARCH_KEY,
                index_name=AZURE_SEARCH_INDEX_NAME,
                embedding_function=self.embeddings.embed_query,
            )
            
            log(logging.INFO, f"Successfully initialized AzureSearchManager with endpoint: {AZURE_SEARCH_ENDPOINT}")
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error connecting to Azure Search: {str(e)}"
            log(logging.ERROR, error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            log(logging.ERROR, f"Error initializing AzureSearchManager: {str(e)}")
            raise

    def _delete_index(self) -> bool:
        """Delete the existing index if it exists"""
        try:
            headers = {
                'api-key': AZURE_SEARCH_KEY
            }
            
            response = requests.delete(
                f"{AZURE_SEARCH_ENDPOINT}/indexes/{AZURE_SEARCH_INDEX_NAME}?api-version={API_VERSION}",
                headers=headers
            )
            
            if response.status_code in [200, 204, 404]:  # Success or already deleted
                log(logging.INFO, f"Index {AZURE_SEARCH_INDEX_NAME} deleted or did not exist")
                return True
            else:
                log(logging.ERROR, f"Failed to delete index: {response.text}")
                return False
                
        except Exception as e:
            log(logging.ERROR, f"Error deleting index: {str(e)}")
            return False

    def _ensure_required_fields(self) -> bool:
        """
        Ensure the index has all required fields, create or update if needed.
        """
        try:
            # Define required fields with full configuration
            required_fields = [
                {"name": "id", "type": "Edm.String", "key": True, "filterable": True},
                {"name": "content", "type": "Edm.String", "filterable": False, "sortable": False, "searchable": True, "analyzer": "standard.lucene"},
                {"name": "chunk_id", "type": "Edm.String", "filterable": True, "sortable": True},
                {"name": "source", "type": "Edm.String", "filterable": True, "sortable": True},
                {"name": "title", "type": "Edm.String", "filterable": True, "sortable": True, "searchable": True}
            ]
            
            # Get current schema
            schema = self._get_index_schema()
            if schema:
                # Check if all required fields exist with correct configuration
                current_fields = {f['name']: f for f in schema.get('fields', [])}
                missing_fields = []
                
                for required_field in required_fields:
                    field_name = required_field['name']
                    if field_name not in current_fields:
                        missing_fields.append(required_field)
                    # We could also check if existing fields have correct configuration
                    # but for now we'll just check existence
                
                if not missing_fields:
                    log(logging.INFO, "Index has all required fields")
                    return True
                    
                log(logging.WARNING, f"Missing fields in index: {[f['name'] for f in missing_fields]}")
                
            # Create index with required fields
            return self.create_search_index(required_fields)

        except Exception as e:
            log(logging.ERROR, f"Error ensuring required fields: {str(e)}")
            return False

    def create_search_index(self, metadata_fields: List[Dict[str, Any]]) -> bool:
        """
        Create a search index with vector search capabilities
        Returns:
            bool: True if index was created successfully, False otherwise
        """
        try:
            # Delete existing index first
            if not self._delete_index():
                log(logging.ERROR, "Failed to delete existing index")
                return False
                
            log(logging.INFO, f"Creating new search index: {AZURE_SEARCH_INDEX_NAME}")
            
            # Define the index schema
            index_schema = {
                "name": AZURE_SEARCH_INDEX_NAME,
                "fields": [
                    {"name": "id", "type": "Edm.String", "key": True, "filterable": True},
                    {"name": "content", "type": "Edm.String", "filterable": False, "sortable": False, "searchable": True, "analyzer": "standard.lucene"},
                    {"name": "chunk_id", "type": "Edm.String", "filterable": True, "sortable": True},
                    {"name": "source", "type": "Edm.String", "filterable": True, "sortable": True},
                    {"name": "title", "type": "Edm.String", "filterable": True, "sortable": True, "searchable": True},
                    # Vector field for embeddings
                    {
                        "name": "content_vector",
                        "type": "Collection(Edm.Single)",
                        "dimensions": 1536,  # OpenAI embedding dimensions
                        "vectorSearchProfile": "my-vector-config"
                    }
                ],
                "vectorSearch": {
                    "algorithms": [{
                        "name": "my-hnsw",
                        "kind": "hnsw",
                        "hnswParameters": {
                            "m": 4,
                            "efConstruction": 400,
                            "metric": "cosine"
                        }
                    }],
                    "profiles": [{
                        "name": "my-vector-config",
                        "algorithm": "my-hnsw"
                    }]
                }
            }
            
            # Add any additional metadata fields
            for field in metadata_fields:
                if field not in index_schema["fields"]:
                    index_schema["fields"].append(field)
            
            # Create the index using REST API
            headers = {
                'Content-Type': 'application/json',
                'api-key': AZURE_SEARCH_KEY
            }
            
            response = requests.put(
                f"{AZURE_SEARCH_ENDPOINT}/indexes/{AZURE_SEARCH_INDEX_NAME}?api-version={API_VERSION}",
                headers=headers,
                json=index_schema
            )
            
            if response.status_code in [200, 201]:
                log(logging.INFO, f"Successfully created index {AZURE_SEARCH_INDEX_NAME}")
                return True
            else:
                log(logging.ERROR, f"Failed to create index: {response.text}")
                return False

        except Exception as e:
            log(logging.ERROR, f"Error creating index: {str(e)}")
            return False

    def upload_documents(self, documents: List[Document]) -> Dict[str, int]:
        """
        Upload processed documents to Azure Search with embeddings
        Returns:
            Dict[str, int]: Dictionary containing counts of successful and failed uploads
        """
        stats = {"succeeded": 0, "failed": 0}
        
        try:
            log(logging.INFO, f"Adding {len(documents)} documents to vector store")
            
            # Ensure index has required fields
            if not self._ensure_required_fields():
                log(logging.ERROR, "Failed to ensure required fields in index")
                stats["failed"] = len(documents)
                return stats

            # Get existing index schema
            schema = self._get_index_schema()
            if not schema:
                log(logging.ERROR, "Failed to get index schema")
                stats["failed"] = len(documents)
                return stats
                
            # Extract field types from schema
            field_types = {
                field['name']: field['type']
                for field in schema.get('fields', [])
            }
            
            log(logging.INFO, f"Found schema fields: {field_types}")
            
            # Convert documents to match schema types
            processed_docs = []
            for idx, doc in enumerate(documents):
                try:
                    # Create a document with properties at the top level (no metadata nesting)
                    processed_doc = {
                        'id': str(idx),  # Use index as stable ID
                        'content': str(doc.page_content),
                        'source': doc.metadata.get('source', ''),
                        'title': doc.metadata.get('title', ''),
                        'chunk_id': str(doc.metadata.get('chunk_id', idx))
                    }
                    processed_docs.append(processed_doc)
                except Exception as e:
                    log(logging.WARNING, f"Error processing document metadata: {str(e)}")
                    stats["failed"] += 1
                    continue
            
            if processed_docs:
                try:
                    # Generate embeddings for each document
                    log(logging.INFO, "Generating embeddings for documents...")
                    embeddings = [self.embeddings.embed_query(doc['content']) for doc in processed_docs]
                    
                    # Add embeddings to each document
                    for doc, emb in zip(processed_docs, embeddings):
                        doc['content_vector'] = emb
                    
                    # Add documents using REST API
                    headers = {
                        'Content-Type': 'application/json',
                        'api-key': AZURE_SEARCH_KEY
                    }
                    
                    # Upload documents in batches
                    batch_size = 100
                    for i in range(0, len(processed_docs), batch_size):
                        batch = processed_docs[i:i + batch_size]
                        
                        response = requests.post(
                            f"{AZURE_SEARCH_ENDPOINT}/indexes/{AZURE_SEARCH_INDEX_NAME}/docs/index?api-version={API_VERSION}",
                            headers=headers,
                            json={
                                "value": batch
                            }
                        )
                        
                        if response.status_code in [200, 201]:
                            stats["succeeded"] += len(batch)
                            log(logging.INFO, f"Successfully added batch of {len(batch)} documents")
                        else:
                            stats["failed"] += len(batch)
                            log(logging.ERROR, f"Failed to add document batch: {response.text}")
                            
                    log(logging.INFO, f"Completed document upload - Success: {stats['succeeded']}, Failed: {stats['failed']}")
                    
                except Exception as e:
                    stats["failed"] = len(documents)
                    log(logging.ERROR, f"Failed to process or upload documents: {str(e)}")
            else:
                log(logging.WARNING, "No documents were processed successfully")
                stats["failed"] = len(documents)
            
        except Exception as e:
            stats["failed"] = len(documents)
            log(logging.ERROR, f"Error in document upload process: {str(e)}")
        
        return stats

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search documents using vector similarity search
        """
        try:
            log(logging.INFO, f"Executing similarity search for query: '{query}' with top_k={top_k}")
            
            # Perform similarity search
            results = self.vector_store.similarity_search_with_score(
                query,
                k=top_k
            )
            
            # Format results
            search_results = []
            for doc, score in results:
                result = {
                    'content': doc.page_content,
                    'source': doc.metadata.get('source', ''),
                    'score': score,
                    **{k: v for k, v in doc.metadata.items() if k != 'source'}
                }
                search_results.append(result)
            
            log(logging.INFO, f"Search completed successfully - Found {len(search_results)} results")
            return search_results

        except Exception as e:
            log(logging.ERROR, f"Search error: {str(e)}")
            return []