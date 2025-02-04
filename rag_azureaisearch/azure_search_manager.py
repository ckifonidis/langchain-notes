from typing import List, Dict, Any
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchFieldDataType,
)
from langchain.schema import Document
from config import (
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_KEY,
    AZURE_SEARCH_INDEX_NAME,
)

class AzureSearchManager:
    def __init__(self):
        self.credential = AzureKeyCredential(AZURE_SEARCH_KEY)
        self.index_client = SearchIndexClient(
            endpoint=AZURE_SEARCH_ENDPOINT,
            credential=self.credential
        )
        self.search_client = SearchClient(
            endpoint=AZURE_SEARCH_ENDPOINT,
            index_name=AZURE_SEARCH_INDEX_NAME,
            credential=self.credential
        )

    def create_search_index(self, metadata_fields: List[Dict[str, Any]]) -> None:
        """
        Create a search index with dynamic fields based on document metadata
        """
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(name="content", type=SearchFieldDataType.String),
            SearchableField(name="source", type=SearchFieldDataType.String),
        ]

        # Add metadata fields dynamically
        for field in metadata_fields:
            fields.append(
                SearchableField(
                    name=field['name'],
                    type=field['type'],
                    searchable=field['searchable']
                )
            )

        index = SearchIndex(name=AZURE_SEARCH_INDEX_NAME, fields=fields)
        self.index_client.create_or_update_index(index)

    def upload_documents(self, documents: List[Document]) -> None:
        """
        Upload processed documents to Azure Search
        """
        search_documents = []
        for i, doc in enumerate(documents):
            search_doc = {
                'id': str(i),
                'content': doc.page_content,
                'source': doc.metadata.get('source', ''),
                **doc.metadata
            }
            search_documents.append(search_doc)

        # Upload in batches of 1000 documents
        batch_size = 1000
        for i in range(0, len(search_documents), batch_size):
            batch = search_documents[i:i + batch_size]
            try:
                self.search_client.upload_documents(documents=batch)
                print(f"Uploaded batch {i//batch_size + 1}")
            except Exception as e:
                print(f"Error uploading batch {i//batch_size + 1}: {str(e)}")

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search documents in Azure Search
        """
        try:
            results = self.search_client.search(
                search_text=query,
                top=top_k,
                highlight_fields="content",
                highlight_pre_tag="<mark>",
                highlight_post_tag="</mark>",
            )
            
            search_results = []
            for result in results:
                search_results.append({
                    'content': result['content'],
                    'source': result['source'],
                    'score': result['@search.score'],
                    'highlights': result.get('@search.highlights', {}).get('content', []),
                    **{k: v for k, v in result.items() if not k.startswith('@')}
                })
            
            return search_results
        except Exception as e:
            print(f"Search error: {str(e)}")
            return []