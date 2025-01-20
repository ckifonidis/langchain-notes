import os
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.callbacks.base import BaseCallbackHandler
from dotenv import load_dotenv, find_dotenv

load_dotenv()

class PDFQuestionAnswerer:
    def __init__(self, openai_api_key):
        """Initialize the RAG system with OpenAI API key."""
        os.environ["OPENAI_API_KEY"] = openai_api_key
        
        # Initialize OpenAI components
        self.embeddings = OpenAIEmbeddings()
        self.llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")
        
        # Initialize the text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )
        
        self.vector_store = None
        self.qa_chain = None

    def load_pdf(self, pdf_path):
        """Load and process a PDF file."""
        # Load PDF
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()
        
        # Split the text into chunks
        texts = self.text_splitter.split_documents(pages)
        
        # Create vector store
        self.vector_store = Chroma.from_documents(
            documents=texts,
            embedding=self.embeddings
        )
        
        # Create QA chain
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever(
                search_kwargs={"k": 3}
            )
        )
        
        return f"Processed PDF with {len(texts)} text chunks"

    def ask_question(self, question):
        """Ask a question about the loaded PDF."""
        if not self.qa_chain:
            return "Please load a PDF first"
        
        response = self.qa_chain.invoke(question)
        return response

def main():
    """Example usage of the PDF Question Answerer."""
    
    # Replace with your OpenAI API key
    OPENAI_API_KEY =os.getenv("OPENAI_API_KEY")
    
    # Initialize the system
    qa_system = PDFQuestionAnswerer(OPENAI_API_KEY)
    
    # Load a PDF file
    print("Loading PDF...")
    result = qa_system.load_pdf("document_loader/docs/test_privacy_policy.pdf")
    print(result)
    
    # Example questions to ask
    questions = [
        "What is the main topic of this document?",
        "Can you summarize the key points?"
    ]
    
    # Ask questions
    print("\nAsking questions about the document:")
    for question in questions:
        print(f"\nQ: {question}")
        answer = qa_system.ask_question(question)
        print(f"A: {answer['result']}")

if __name__ == "__main__":
    main()