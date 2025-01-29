from typing import List, Dict, Optional
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain.schema import Document
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from markitdown import MarkItDown
import glob
import os
from pathlib import Path
import yaml
import re
from dotenv import load_dotenv

load_dotenv()

# Function to extract metadata from Markdown headers
def extract_metadata(content):
    # Look for YAML front matter
    match = re.match(r"---\n(.*?)\n---\n", content, re.DOTALL)
    metadata = {}
    if match:
        yaml_content = match.group(1)
        metadata = yaml.safe_load(yaml_content)
    # Remove metadata section from the content
    content = re.sub(r"---\n(.*?)\n---\n", "", content, flags=re.DOTALL)
    return metadata, content

class MarkdownRAGProcessor:
    def __init__(
        self,
        markdown_dir: str,
        openai_api_key: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 100
    ):
        """
        Initialize the Markdown RAG processor.
        
        Args:
            markdown_dir: Directory containing markdown files
            openai_api_key: OpenAI API key for embeddings and chat
            chunk_size: Size of text chunks for splitting
            chunk_overlap: Overlap between chunks
        """
        self.markdown_dir = Path(markdown_dir)
        self.openai_api_key = openai_api_key
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        self.vectorstore = None
        self.docs_processed = []
        # Initialize the language model
        self.llm = ChatOpenAI(
            temperature=0,
            model_name="gpt-4o-mini",
            openai_api_key=self.openai_api_key
        )

    def process_other_files(self, file_path: Path) -> bool:
        md = MarkItDown(llm_client=self.llm)
        supported_extensions = ('.pptx', '.docx', '.pdf', '.jpg', '.jpeg', '.png')
        files_to_convert = [f for f in os.listdir(file_path) if f.lower().endswith(supported_extensions)]
        for file in files_to_convert:
            print(f"\nConverting {file}...")
            try:
                if file.lower().endswith('.md'):
                    # Directly load markdown files
                    continue
                else:
                    result = md.convert(file_path + "/" + file)
                    md_file = os.path.splitext(file)[0] + '.md'
                    with open(file_path + "/" + md_file, 'w') as f:
                        f.write(result.text_content)
                    
            except Exception as e:
                raise(f"Error converting {file}: {str(e)}")
        
    def parse_markdown_with_metadata(self, file_path: Path) -> List[Document]:
        """
        Parse a markdown file and extract both content and metadata.
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            List of Document objects with content and metadata
        """
        MARKDOWN_SEPARATORS = [
                "\n#{1,6} ",
                "```\n",
                "\n\\*\\*\\*+\n",
                "\n---+\n",
                "\n___+\n",
                "\n\n",
                "\n",
                " ",
                "",
            ]
        documents = []
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            metadata, main_content = extract_metadata(content)
            documents.append({"content": main_content, "metadata": metadata})
        return documents
    
    def process_markdown_directory(self, directory: Path) -> List[Document]:
        """
        Process all markdown files in the specified directory.
        
        Returns:
            List of all Document objects
        """
        all_documents = []
        self.process_other_files(directory)
        # Process each markdown file
        for file_path in Path(directory).glob('*.md'):
            try:
                documents = self.parse_markdown_with_metadata(file_path)
                all_documents.extend(documents)
            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")

        proccessed_docs = []
        # Split text into manageable chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        documents = []
        for doc in all_documents:
            chunks = text_splitter.split_text(doc["content"])
            for chunk in chunks:
                proccessed_docs.append(Document(
                                    page_content=chunk,
                                    metadata=doc["metadata"]
                                )
                )
  
        return proccessed_docs
    
    def build_vectorstore(self):
        """
        Build the vector store from processed documents.
        """
        documents = self.process_markdown_directory('markdown_parser[wip]/docs')

        # Create Chroma vectorstore
        self.vectorstore = FAISS.from_documents(
                documents=documents,
                embedding=self.embeddings
            )
        
    def create_rag_chain(self):
        """
        Create a RAG chain for question answering.
        
        Returns:
            A callable chain that can answer questions
        """
        
        # Create retrieval chain
        retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}
        )
        
        # Create prompt template
        template = """Answer the question based on the following context. If you cannot answer the question based on the context, say "I don't have enough information to answer that."

                        Context:
                        {context}

                        Question:
                        {question}

                        Additional Instructions:
                        - Use the metadata information when relevant to provide more context
                        - Cite the source of information when possible
                        - Be concise but comprehensive

                        Answer:"""
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
        
        # Create the RAG chain
        rag_chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | prompt
            | self.llm
        )
        
        return rag_chain
    
    def save_vectorstore(self):
        """
        Save the vector store to disk.
        """
        if self.vectorstore:
            self.vectorstore.save_local("faiss_index")
            
    def load_vectorstore(self):
        """
        Load the vector store from disk.
        """
        self.vectorstore = FAISS.load_local(
            persist_directory="faiss_index",
            embedding_function=self.embeddings
        )

# Example usage
if __name__ == "__main__":
    # Initialize processor
    processor = MarkdownRAGProcessor(
        markdown_dir="./docs",
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Build and save vector store
    processor.build_vectorstore()
    processor.save_vectorstore()
    
    # Create RAG chain
    rag_chain = processor.create_rag_chain()
    
    print("\nAsking questions about the document:")
    while True:
        q = input("Ask a question: ")
        if q == "exit":
            break
        else:
            answer = rag_chain.invoke(q)
            print(f"A: {answer.content }")