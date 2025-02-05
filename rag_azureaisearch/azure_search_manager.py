from typing import List, Dict, Any
import logging
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain.schema import Document
import requests
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

# Configure logging to both file and console
logger = logging.getLogger('AzureSearchManager')
logger.setLevel(logging.getLevelName(LOG_LEVEL))

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
    def __init__(self):
        """Initialize Azure Search with OpenAI embeddings"""
        # Validate required configuration
        # if not all([AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_KEY, OPENAI_API_KEY]):
        #     error_msg = "Missing required configuration. Please check your .env file for:"
        #     if not AZURE_SEARCH_ENDPOINT:
        #         error_msg += "\n- AZURE_SEARCH_ENDPOINT"
        #     if not AZURE_SEARCH_KEY:
        #         error_msg += "\n- AZURE_SEARCH_KEY"
        #     if not OPENAI_API_KEY:
        #         error_msg += "\n- OPENAI_API_KEY"
        #     logger.error(error_msg)
        #     raise ValueError(error_msg)

        # # Validate endpoint format
        # try:
        #     parsed_url = urlparse(AZURE_SEARCH_ENDPOINT)
        #     if not all([parsed_url.scheme, parsed_url.netloc]):
        #         raise ValueError(
        #             f"Invalid Azure Search endpoint format: {AZURE_SEARCH_ENDPOINT}\n"
        #             "Endpoint should be in format: https://<service-name>.search.windows.net"
        #         )
            
        #     # Remove trailing slash if present
        #     self.endpoint = AZURE_SEARCH_ENDPOINT.rstrip('/')
            
        # except Exception as e:
        #     logger.error(f"Error validating endpoint: {str(e)}")
        #     raise

        try:
            # # Test Azure Search connectivity first
            # logger.info(f"Testing Azure Search connectivity to endpoint: {self.endpoint}")
            # headers = {
            #     'Content-Type': 'application/json',
            #     'xcv-key': AZURE_SEARCH_KEY
            # }
            
            # # First try to get service information
            # response = requests.get(
            #     f"{self.endpoint}?api-version=2023-11-01",
            #     headers=headers
            # )
            
            # if response.status_code == 404:
            #     error_msg = (
            #         f"Azure Search service not found at {self.endpoint}. "
            #         "Please verify that:\n"
            #         "1. The service name in the endpoint URL is correct\n"
            #         "2. The service is running and accessible\n"
            #         "3. You're using the correct region in the URL"
            #     )
            #     logger.error(error_msg)
            #     raise ValueError(error_msg)
            # elif response.status_code == 403:
            #     error_msg = (
            #         "Authentication failed. Please verify your AZURE_SEARCH_KEY and ensure "
            #         "it has the correct permissions. Your key should be an admin key, not "
            #         "a query key."
            #     )
            #     logger.error(error_msg)
            #     raise ValueError(error_msg)
            # elif response.status_code != 200:
            #     error_msg = f"Azure Search connection failed with status {response.status_code}: {response.text}"
            #     logger.error(error_msg)
            #     raise ValueError(error_msg)

            # Initialize OpenAI embeddings
            logger.info("Initializing OpenAI embeddings...")
            self.embeddings = OpenAIEmbeddings(
                api_key=OPENAI_API_KEY,
                model="text-embedding-3-small"
            )
            
            # Test embeddings
            try:
                self.embeddings.embed_query("test")
            except Exception as e:
                error_msg = (
                    f"OpenAI embeddings failed. Please verify your OpenAI API key. Error: {str(e)}"
                )
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Initialize Azure Search vector store
            self.vector_store = AzureSearch(
                azure_search_endpoint=AZURE_SEARCH_ENDPOINT,
                azure_search_key=AZURE_SEARCH_KEY,
                index_name=AZURE_SEARCH_INDEX_NAME,
                embedding_function=self.embeddings.embed_query,
            )
            
            logger.info(f"Successfully initialized AzureSearchManager with endpoint: {AZURE_SEARCH_ENDPOINT}")
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error connecting to Azure Search: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            logger.error(f"Error initializing AzureSearchManager: {str(e)}")
            raise

    def create_search_index(self, metadata_fields: List[Dict[str, Any]]) -> bool:
        """
        Create a search index with vector search capabilities
        Returns:
            bool: True if index was created successfully, False otherwise
        """
        try:
            logger.info(f"Creating search index: {AZURE_SEARCH_INDEX_NAME}")
            
            # The vector store will automatically create the index with
            # the required fields including vector embeddings
            self.vector_store.create_index()
            
            logger.info(f"Successfully created index {AZURE_SEARCH_INDEX_NAME}")
            return True

        except Exception as e:
            logger.error(f"Error creating index: {str(e)}")
            return False

    def upload_documents(self, documents: List[Document]) -> Dict[str, int]:
        """
        Upload processed documents to Azure Search with embeddings
        Returns:
            Dict[str, int]: Dictionary containing counts of successful and failed uploads
        """
        stats = {"succeeded": 0, "failed": 0}
        
        try:
            logger.info(f"Adding {len(documents)} documents to vector store")
            
            # Add documents to vector store with embeddings
            self.vector_store.add_documents(documents)
            
            stats["succeeded"] = len(documents)
            logger.info(f"Successfully added {len(documents)} documents to vector store")
            
        except Exception as e:
            stats["failed"] = len(documents)
            logger.error(f"Error adding documents to vector store: {str(e)}")
        
        return stats

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search documents using vector similarity search
        """
        try:
            logger.info(f"Executing similarity search for query: '{query}' with top_k={top_k}")
            
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
            
            logger.info(f"Search completed successfully - Found {len(search_results)} results")
            return search_results

        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return []