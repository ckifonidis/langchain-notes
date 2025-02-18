from typing import List, Dict, Any, Set
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import os
from config import CHUNK_SIZE, CHUNK_OVERLAP
from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredMarkdownLoader,
    Docx2txtLoader,
    TextLoader
)
from markitdown import MarkItDown
from tqdm import tqdm
import logging
from langchain_openai import AzureChatOpenAI
from config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_KEY,
)
# from langchain.output_parsers.openai_tools import JsonOutputToolsParser
# from langchain_community.chat_models import ChatOpenAI
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.runnables import RunnableLambda
# from langchain.chains import create_extraction_chain
# from typing import Optional, List
# from langchain.chains import create_extraction_chain_pydantic
# from langchain_core.pydantic_v1 import BaseModel
# from langchain import hub

# class Sentences(BaseModel):
#     sentences: List[str]
            
class DocumentProcessor:
    def __init__(self):
        # self.obj = hub.pull("wfh/proposal-indexing")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
            # separators=[
            #     "\n#{1,6} ",  # Headers
            #     "\n\n",       # Paragraphs
            #     "\n",         # Lines
            #     ".",          # Sentences
            #     " ",          # Words
            #     ""           # Characters
            # ],
            # add_start_index=True
        )
        # Supported text-based file extensions
        self.supported_extensions = {
            # '.docx',  # Word files
            # '.doc',   # Word doc files
            # '.dotm', # word dotm files
            # '.txt',   # Text files,
            # '.pdf',   # PDF files
            '.md',    # Markdown files
        }
        print(AZURE_OPENAI_API_VERSION)
        self.llm = AzureChatOpenAI(
            model="gpt-4o",
            temperature=0.0,
            api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_KEY,
            )
        # self.runnable = self.obj | self.llm
        # # Pydantic data class

        # # Extraction
        # self.extraction_chain = create_extraction_chain_pydantic(pydantic_schema=Sentences, llm=self.llm)
        # def get_propositions(self, text):
        #     runnable_output = self.runnable.invoke({
        #         "input": text
        #     }).content
            
        #     propositions = self.extraction_chain.run(runnable_output)[0].sentences
        #     return propositions

    def find_all_files(self, directory_path: str, include_extensions: Set[str] = None) -> List[str]:
        """
        Recursively find all files in a directory and its subdirectories.
        
        Args:
            directory_path (str): The root directory to start searching from
            include_extensions (Set[str], optional): Set of file extensions to include (e.g., {'.txt', '.md'})
                                                   If None, includes all files
        
        Returns:
            List[str]: List of full file paths
        """
        all_files = []
        try:
            for root, _, files in os.walk(directory_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if include_extensions is None or os.path.splitext(file)[1].lower() in include_extensions:
                        all_files.append(file_path)
            
            logging.info(f"Found {len(all_files)} files in {directory_path}")
            return sorted(all_files)  # Sort for consistent ordering
        except Exception as e:
            logging.error(f"Error finding files in {directory_path}: {str(e)}")
            raise

    def load_documents(self, directory_path: str) -> List[Document]:
        """
        Load text-based documents from a directory and return a list of Document objects.
        """
        documents = []
        
        # Find all files with supported extensions
        files_to_process = self.find_all_files(
            directory_path, 
            include_extensions=self.supported_extensions
        )
        md = MarkItDown(llm_client=self.llm)
        # Process files with progress bar
        for file_path in tqdm(files_to_process, desc="Loading documents", unit="file"):
            # print(f"\nConverting {file}...")
            try:
                if file_path.lower().endswith('.md'):
                    # Directly load markdown files
                    md_file = file_path
                else:
                    result = md.convert(file_path)
                    md_file = os.path.splitext(file_path)[0] + '.md'
                    with open(md_file, 'w') as f:
                        f.write(result.text_content)
                    
            except Exception as e:
                raise(f"Error converting {file_path}: {str(e)}")
            _, ext = os.path.splitext(md_file)
            try:
                # Load document based on file type
                if ext.lower() == '.pdf':
                    loader = PyPDFLoader(file_path)
                elif ext.lower() == '.md':
                    loader = UnstructuredMarkdownLoader(md_file)
                elif ext.lower() == '.docx':
                    loader = Docx2txtLoader(file_path)
                elif ext.lower() == '.dotm':
                    loader = Docx2txtLoader(file_path)
                elif ext.lower() == '.txt':
                    loader = TextLoader(file_path)
                else:
                    raise ValueError(f"Unsupported file type: {ext}")

                document = loader.load()
                logging.info(f"Successfully loaded {file_path}")
                documents.extend(document)
            except Exception as e:
                logging.error(f"Error loading {file_path}: {str(e)}")
                raise
        
        logging.info(f"Loaded {len(documents)} documents in total")
        return documents

    def process_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into chunks and add metadata
        """
        chunks = self.text_splitter.split_documents(documents)

        # Enhance chunks with additional metadata using tqdm
        for i, chunk in enumerate(tqdm(chunks, desc="Processing chunks", unit="chunk")):
            chunk.metadata.update({
                'id': i,
                'chunk_id': i,
                'chunk_size': len(chunk.page_content),
                'title': os.path.basename(chunk.metadata.get('source', '')),
                'type': os.path.basename(os.path.dirname(chunk.metadata.get('source', ''))),
                'document_type': chunk.metadata.get('source', '').split('.')[-1],
            })

        logging.info(f"Processed {len(chunks)} chunks")
        return chunks

    def extract_metadata(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """
        Extract metadata from documents for search index schema optimization
        """
        metadata_fields = set()
        for doc in tqdm(documents, desc="Extracting metadata", unit="doc"):
            metadata_fields.update(doc.metadata.keys())
        
        metadata_schema = [{'name': field, 'type': 'Edm.String', 'searchable': True} 
                          for field in metadata_fields]
        
        logging.info(f"Extracted {len(metadata_schema)} metadata fields")
        return metadata_schema