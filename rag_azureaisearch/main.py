import asyncio
from document_processor import DocumentProcessor
from azure_search_manager import AzureSearchManager
from rag_chain import RAGChain
import argparse

async def setup_knowledge_base(docs_directory: str):
    """
    Process documents and set up the Azure Search index
    """
    print("Setting up knowledge base...")
    
    # Initialize components
    doc_processor = DocumentProcessor()
    search_manager = AzureSearchManager()
    
    # Load and process documents
    print("Loading documents...")
    documents = doc_processor.load_documents(docs_directory)
    print(f"Loaded {len(documents)} documents")
    
    # Process documents into chunks
    print("Processing documents...")
    processed_docs = doc_processor.process_documents(documents)
    print(f"Created {len(processed_docs)} chunks")
    
    # Extract metadata fields for index schema
    metadata_fields = doc_processor.extract_metadata(processed_docs)
    
    # Create search index
    print("Creating search index...")
    search_manager.create_search_index(metadata_fields)
    
    # Upload documents to search index
    print("Uploading documents to Azure Search...")
    search_manager.upload_documents(processed_docs)
    
    print("Knowledge base setup complete!")

async def chat_loop():
    """
    Interactive chat loop using the RAG system
    """
    rag_chain = RAGChain()
    
    print("\nRAG System Ready! Type 'quit' to exit.")
    print("Ask your question:")
    
    while True:
        question = input("> ").strip()
        
        if question.lower() in ['quit', 'exit']:
            break
            
        if not question:
            continue
            
        try:
            response = await rag_chain.generate_response(question)
            
            print("\nAnswer:", response["answer"])
            print("\nSources:")
            for source in response["sources"]:
                print(f"- {source}")
            print()
            
        except Exception as e:
            print(f"Error: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="RAG System with Azure AI Search")
    parser.add_argument(
        "--setup",
        type=str,
        help="Path to documents directory for initial setup",
    )
    
    args = parser.parse_args()
    
    if args.setup:
        asyncio.run(setup_knowledge_base(args.setup))
    else:
        asyncio.run(chat_loop())

if __name__ == "__main__":
    main()