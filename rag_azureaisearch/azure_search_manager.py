from typing import List, Dict, Any
from logger import log, INFO, ERROR, WARNING
from langchain_openai import OpenAIEmbeddings, ChatOpenAI, AzureOpenAIEmbeddings, AzureChatOpenAI
from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain.chat_models.base import BaseChatModel
from langchain.prompts import PromptTemplate
from langchain.schema import Document
import requests
import json
from urllib.parse import urlparse
from tqdm import tqdm
from config import (
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_KEY,
    AZURE_SEARCH_INDEX_NAME,
    AZURE_SEARCH_API_VERSION,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_KEY,

    OPENAI_API_KEY,
)
import os

from AzureSearchLocation import AzureSearchLocation

class AzureSearchManager:
    vector_store: AzureSearchLocation
    embed_document: callable[Document, List[float]]


    def __init__(self, vector_store: AzureSearchLocation, embedd_document: callable[Document, List[float]]):
        self.vector_store = vector_store
        self.embed_document = embedd_document

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

    def create_search_index(self, metadata_fields: List[Dict[str, Any]]) -> bool:
        """
        Create a search index with vector search capabilities
        Returns:
            bool: True if index was created successfully, False otherwise
        """
        try:
            # Delete existing index first
            if not self.vector_store.delete_index():
                log(ERROR, "Failed to delete existing index")
                return False
                
            log(INFO, f"Creating new search index: {AZURE_SEARCH_INDEX_NAME}")
            
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
                            "m": 10,                    # Recommended for ML embeddings
                            "efConstruction": 600,      # Higher for better accuracy
                            "efSearch": 600,            # Runtime search quality
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
            
            return self.vector_store.update_index_schema(index_schema)

        except Exception as e:
            log(ERROR, f"Error creating index: {str(e)}")
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
                {"name": "chunk_id", "type": "Edm.String", "filterable": True, "sortable": True, "searchable": False},
                {"name": "source", "type": "Edm.String", "filterable": True, "sortable": True, "searchable": False},
                {"name": "type", "type": "Edm.String", "filterable": True, "sortable": True, "searchable": True},
                {"name": "title", "type": "Edm.String", "filterable": True, "sortable": True, "searchable": True}
            ]
            
            # Get current schema
            schema = self.vector_store.get_schema()
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
                    log(INFO, "Index has all required fields")
                    return True
                    
                log(WARNING, f"Missing fields in index: {[f['name'] for f in missing_fields]}")
                
            # Create index with required fields
            return self.create_search_index(required_fields)

        except Exception as e:
            log(ERROR, f"Error ensuring required fields: {str(e)}")
            return False

    def upload_documents(self, documents: List[Document]) -> Dict[str, int]:
        """
        Upload processed documents to Azure Search with embeddings
        Returns:
            Dict[str, int]: Dictionary containing counts of successful and failed uploads
        """
        stats = {"succeeded": 0, "failed": 0}
        
        try:
            log(INFO, f"Adding {len(documents)} documents to vector store")
            
            # Ensure index has required fields
            if not self._ensure_required_fields():
                log(ERROR, "Failed to ensure required fields in index")
                stats["failed"] = len(documents)
                return stats

            # Get existing index schema
            schema = self.vector_store.get_index_schema()
            if not schema:
                log(ERROR, "Failed to get index schema")
                stats["failed"] = len(documents)
                return stats
                
            # Extract field types from schema
            field_types = {
                field['name']: field['type']
                for field in schema.get('fields', [])
            }
            
            log(INFO, f"Found schema fields: {field_types}")
            
            # Convert documents to match schema types
            processed_docs = []
            for idx, doc in enumerate(documents):
                try:
                    # Create a document with properties at the top level (no metadata nesting)
                    processed_doc = {
                        'id': str(idx),  # Use index as stable ID
                        'content': str(doc.page_content),
                        'source': doc.metadata.get('source', ''),
                        'title': os.path.basename(doc.metadata.get('source', '')),
                        'type': os.path.basename(os.path.dirname(doc.metadata.get('source', ''))),
                        'chunk_id': str(doc.metadata.get('chunk_id', idx))
                    }
                    processed_docs.append(processed_doc)
                except Exception as e:
                    log(WARNING, f"Error processing document metadata: {str(e)}")
                    stats["failed"] += 1
                    continue
            
            if processed_docs:
                try:
                    # Generate embeddings for each document with progress bar
                    log(INFO, "Generating embeddings for documents...")
                    embeddings = [ self.embed_document(doc['content']) for doc in tqdm(processed_docs, desc="Generating embeddings")]
                    
                    # Add embeddings to each document
                    for doc, emb in zip(processed_docs, embeddings):
                        doc['content_vector'] = emb

                    # Upload documents in batches
                    batch_size = 100
                    for i in range(0, len(processed_docs), batch_size):
                        batch = processed_docs[i:i + batch_size]

                        if self.vector_store.update_documents(batch):
                            stats["succeeded"] += len(batch)
                        else:
                            stats["failed"] += len(batch)
                        
                    log(INFO, f"Completed document upload - Success: {stats['succeeded']}, Failed: {stats['failed']}")
                    
                except Exception as e:
                    stats["failed"] = len(documents)
                    log(ERROR, f"Failed to process or upload documents: {str(e)}")
            else:
                log(WARNING, "No documents were processed successfully")
                stats["failed"] = len(documents)
            
        except Exception as e:
            stats["failed"] = len(documents)
            log(ERROR, f"Error in document upload process: {str(e)}")
        
        return stats
    # Create prompt template
    def category_prompt(self) -> PromptTemplate:
        prompt = """
        Please act as a robust and well-trained intent classifier that can identify the most 
        likely category that the questions refers to, WITHOUT USING the proper and common noun subject from the user's query. 
        It can be ΚΑΡΤΕΣ (cards), ΚΑΤΑΝΑΛΩΤΙΚΑ (personal loans) and ΣΤΕΓΑΣΤΙΚΑ (mortgage) or ΑΛΛΟ (all the rest).
        ΑΛΛΟ is the category for the queries that do not be classified in the other categories.
        The identified category must be only one word and one of the ΚΑΡΤΕΣ, ΚΑΤΑΝΑΛΩΤΙΚΑ, ΣΤΕΓΑΣΤΙΚΑ or ΑΛΛΟ.

        User's query: {question}

        Category:
        """
        return PromptTemplate(template=prompt, input_variables=['question'])
    
    def category_chain(self, model: BaseChatModel,question: str) -> str:
        """
        Get the category of the question
        """
        output = self.category_prompt() | model
        return output.invoke({"question": question})
    
    def search(self, model: BaseChatModel, query: str, top_k: int = 15) -> List[Dict[str, Any]]:
        """
        Search documents using vector similarity search
        """
        try:
            # log(INFO, f"Executing similarity search for query: '{query}' with top_k={top_k}")
            type_filter = self.category_chain(model, query)
            print(f"Type filter: {type_filter.content}")
            print(50*"#")
            if type_filter.content == "":
                results = self.vector_store.hybrid_search( query, k=top_k )
            elif type_filter.content in ['ΚΑΡΤΕΣ', 'ΚΑΤΑΝΑΛΩΤΙΚΑ', 'ΣΤΕΓΑΣΤΙΚΑ']:
                # Perform similarity search
                results = self.vector_store.hybrid_search( query, k=top_k, filters=f"type eq '{type_filter.content}'" )
            else:
                results = self.vector_store.hybrid_search( query, k=top_k)

            # Format results
            search_results = []
            for doc, score in results:
                result = {
                    'content': doc.page_content,
                    'source': doc.metadata.get('title', ''),
                    'score': score,
                    **{k: v for k, v in doc.metadata.items() if k != 'source'}
                }
                search_results.append(result)
            # print([res['score'] for res in search_results])
            # log(INFO, f"Search completed successfully - Found {len(search_results)} results")
            return search_results

        except Exception as e:
            log(ERROR, f"Search error: {str(e)}")
            return []
        

if __name__ == "__main__":



    """Initialize Azure Search with OpenAI embeddings"""
    try:

        log(INFO, "Initializing OpenAI embeddings...")
        # self.embeddings = OpenAIEmbeddings(
        #     api_key=OPENAI_API_KEY,
        #     model="text-embedding-3-small"
        # )
        embeddings = AzureOpenAIEmbeddings(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            model="text-embedding-3-small"
        )
        # Test embeddings
        try:
            embeddings.embed_query("test")
        except Exception as e:
            error_msg = (
                f"OpenAI embeddings failed. Please verify your OpenAI API key. Error: {str(e)}"
            )
            log(ERROR, error_msg)
            raise ValueError(error_msg) 

        def embed_document(doc: Document) -> List[float]:
            return embeddings.embed_documents([doc.page_content])[0]

        location = AzureSearchLocation( AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_KEY, AZURE_SEARCH_INDEX_NAME, AZURE_SEARCH_API_VERSION, embeddings)

        llm = AzureChatOpenAI(
            model="gpt-4o",
            temperature=0.0,
            api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_KEY,
        )
               
        log(INFO, f"Successfully initialized AzureSearchManager with endpoint: {AZURE_SEARCH_ENDPOINT}")
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Network error connecting to Azure Search: {str(e)}"
        log(ERROR, error_msg)
        raise ValueError(error_msg)
    except Exception as e:
        log(ERROR, f"Error initializing AzureSearchManager: {str(e)}")
        raise
