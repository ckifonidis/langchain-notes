from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import UnstructuredFileLoader
from langchain.schema import Document
import os
from config import CHUNK_SIZE, CHUNK_OVERLAP

class DocumentProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
        )

    def load_documents(self, directory_path: str) -> List[Document]:
        """
        Load documents from a directory and return a list of Document objects
        """
        documents = []
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.endswith(('.txt', '.pdf', '.docx', '.doc')):
                    file_path = os.path.join(root, file)
                    try:
                        loader = UnstructuredFileLoader(file_path)
                        docs = loader.load()
                        documents.extend(docs)
                    except Exception as e:
                        print(f"Error loading {file_path}: {str(e)}")
        return documents

    def process_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into chunks and add metadata
        """
        chunks = self.text_splitter.split_documents(documents)
        
        # Enhance chunks with additional metadata
        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                'chunk_id': i,
                'chunk_size': len(chunk.page_content),
                'document_type': chunk.metadata.get('source', '').split('.')[-1],
            })
        
        return chunks

    def extract_metadata(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """
        Extract metadata from documents for search index schema optimization
        """
        metadata_fields = set()
        for doc in documents:
            metadata_fields.update(doc.metadata.keys())
        
        return [{'name': field, 'type': 'Edm.String', 'searchable': True} 
                for field in metadata_fields]