from typing import List, Dict, Optional, Union
from pathlib import Path
from dataclasses import dataclass
import math
import json
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
# from langchain.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain.vectorstores import Chroma
from langchain_core.output_parsers import StrOutputParser
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder
import nltk
from nltk.tokenize import word_tokenize
import os
from dotenv import load_dotenv
import sys
from markdown_parser import MarkdownDocumentParser


class HybridDocument:
    def __init__(self, content: str, metadata: Dict):
        self.content = content
        self.metadata = metadata

@dataclass
class SearchResult:
    """Class to store search results with scores"""
    document: Document
    bm25_score: float
    vector_score: float
    combined_score: float
    rerank_score: Optional[float] = None

class HybridSearchRetriever:
    """Implements hybrid search combining BM25 and vector similarity with reranking."""
    
    def __init__(
        self,
        documents: List[Document],
        textsplitter: RecursiveCharacterTextSplitter,
        embeddings: OpenAIEmbeddings,
        bm25_weight: float = 0.3,
        vector_weight: float = 0.7,
        use_reranker: bool = True,
        persist_directory: str = "./docs_db"
    ):
        self.text_splitter = textsplitter
        proccessed_docs = []
        for doc in [Document(page_content=doc['content']['full_text'], metadata={"summary":doc['metadata']['summary']}) for doc in documents]:
            chunks = self.text_splitter.split_text(doc.page_content)
            for chunk in chunks:
                proccessed_docs.append(Document(page_content=chunk, metadata=doc.metadata))
        self.documents = proccessed_docs 
        self.embeddings = embeddings
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self.use_reranker = use_reranker
        self.persist_directory = persist_directory
        
        # Initialize NLTK
        nltk.download('punkt')
        
        # Initialize reranker
        if use_reranker:
            self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-12-v2')
        
        self._initialize_search_engines()
    
    def _initialize_search_engines(self):
        """Initialize BM25 and Chroma indexes."""
        # Prepare documents for BM25
        tokenized_docs = []
        for doc in self.documents:
            tokens = word_tokenize(doc.page_content.lower())
            tokenized_docs.append(tokens)
        
        # Initialize BM25
        self.bm25 = BM25Okapi(tokenized_docs)
        
        # Initialize Chroma vector store with persistence
        self.vector_store = Chroma.from_documents(
            documents=self.documents,
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        # Persist the vector store
        self.vector_store.persist()
    
    def _get_bm25_scores(self, query: str, top_k: int) -> List[SearchResult]:
        """Get BM25 scores for query."""
        # Tokenize query
        tokenized_query = word_tokenize(query.lower())
        
        # Get BM25 scores
        bm25_scores = self.bm25.get_scores(tokenized_query)
        
        # Get top-k indices using Python's sorted
        scored_indices = [(score, idx) for idx, score in enumerate(bm25_scores)]
        top_scored = sorted(scored_indices, reverse=True)[:top_k]
        
        results = []
        for score, idx in top_scored:
            results.append(
                SearchResult(
                    document=self.documents[idx],
                    bm25_score=score,
                    vector_score=0.0,
                    combined_score=0.0
                )
            )
        
        return results
    
    def _get_vector_scores(self, query: str, top_k: int) -> List[SearchResult]:
        """Get vector similarity scores for query."""
        # Use Chroma's similarity search with scores
        vector_results = self.vector_store.similarity_search_with_relevance_scores(
            query, k=top_k
        )
        
        results = []
        for doc, score in vector_results:
            results.append(
                SearchResult(
                    document=doc,
                    bm25_score=0.0,
                    vector_score=float(score),
                    combined_score=0.0
                )
            )
        
        return results
    
    def _rerank_results(
        self,
        query: str,
        results: List[SearchResult],
        top_k: int
    ) -> List[SearchResult]:
        """Rerank results using cross-encoder."""
        if not self.use_reranker:
            return results[:top_k]
        
        # Prepare pairs for reranking
        pairs = [(query, doc.document.page_content) for doc in results]
        
        # Get reranking scores
        rerank_scores = self.reranker.predict(pairs)
        
        # Add reranking scores to results
        for result, score in zip(results, rerank_scores):
            result.rerank_score = float(score)
        
        # Sort by reranking score
        results.sort(key=lambda x: x.rerank_score, reverse=True)
        
        return results[:top_k]
    
    def get_relevant_documents(
        self,
        query: str,
        top_k: int = 20,
        rerank_top_k: Optional[int] = None
    ) -> List[Document]:
        """
        Retrieve relevant documents using hybrid search and reranking.
        
        Args:
            query: Search query
            top_k: Number of documents to retrieve
            rerank_top_k: Number of documents to consider for reranking
        
        Returns:
            List of relevant documents
        """
        if rerank_top_k is None:
            rerank_top_k = top_k * 3
        
        # Get BM25 results
        bm25_results = self._get_bm25_scores(query, rerank_top_k)
        
        # Get vector similarity results
        vector_results = self._get_vector_scores(query, rerank_top_k)
        
        # Combine results using document content as key
        doc_to_scores = {}
        
        # Process BM25 results
        for result in bm25_results:
            key = (result.document.page_content, result.document.metadata.get('source', ''))
            doc_to_scores[key] = result
        
        # Process vector results
        for result in vector_results:
            key = (result.document.page_content, result.document.metadata.get('source', ''))
            if key in doc_to_scores:
                doc_to_scores[key].vector_score = result.vector_score
            else:
                doc_to_scores[key] = result
        
        # Calculate combined scores
        results = list(doc_to_scores.values())
        for result in results:
            result.combined_score = (
                self.bm25_weight * result.bm25_score +
                self.vector_weight * result.vector_score
            )
        
        # Sort by combined score
        results.sort(key=lambda x: x.combined_score, reverse=True)

        # Rerank top results
        if self.use_reranker:
            results = self._rerank_results(query, results[:rerank_top_k], top_k)
        else:
            results = results[:top_k]
        
        # Return documents
        return [result.document for result in results]

class HybridRAGSystem:
    """Enhanced hybrid RAG system with hybrid search and reranking."""
    
    def __init__(
        self,
        openai_api_key: str,
        persist_directory: str = "./docs_db",
        bm25_weight: float = 0.3,
        vector_weight: float = 0.7,
        use_reranker: bool = True
    ):
        self.openai_api_key = openai_api_key
        self.persist_directory = persist_directory
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        self.documents = []
        self.retriever = None
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self.use_reranker = use_reranker
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", "!", "?", ";", ",", " "],
            keep_separator=True
        )

    def load_documents(self, directory_path: str) -> List[HybridDocument]:
        """Load documents from a directory and process them."""
        # loader = DirectoryLoader(directory_path, glob="**/*.md")
        documents = list(Path(directory_path).glob('*.md'))
        # documents = loader.load()
        print(len(documents))
        return [self._process_document(doc) for doc in documents]

    def _process_document(self, raw_document) -> HybridDocument:
        """Process a single document, extracting metadata and citations."""
        doc = MarkdownDocumentParser(raw_document).extract_rag_content()
        return doc
    
    def add_documents(self, directory_path: str):
        """Add documents to the system."""
        self.documents = self.load_documents(directory_path)
        
        # Reinitialize retriever with persistence
        self.retriever = HybridSearchRetriever(
            documents=self.documents,
            textsplitter = self.text_splitter,
            embeddings=self.embeddings,
            bm25_weight=self.bm25_weight,
            vector_weight=self.vector_weight,
            use_reranker=self.use_reranker,
            persist_directory=self.persist_directory
        )
    
    def create_retrieval_chain(self):
        """Create retrieval chain with hybrid search."""
        if not self.retriever:
            raise ValueError("No documents added to the system yet.")
        
        # Initialize LLM
        llm = ChatOpenAI(
            temperature=0,
            model_name="gpt-4o-mini",
            openai_api_key=self.openai_api_key
        )
        
        # Create prompt template
        template = """You are an expert legal research assistant with deep knowledge of banking regulations and procedures. Your role is to provide accurate, well-structured answers based on the provided documentation.

        Task:
        Analyze the provided context and answer the question while following these guidelines:

        Response Requirements:
        1. Accuracy & Sources
           - Base your answer strictly on the provided context
           - Cite specific documents and sections when referencing information
           - If information is not found in the context, explicitly state this
           - Do not make assumptions or provide information beyond the given context

        2. Structure & Clarity
           - Begin with a clear, direct answer to the question
           - Organize information in a logical sequence
           - Use bullet points or numbered lists for complex procedures
           - Highlight key points and requirements

        3. Compliance & Precision
           - Emphasize any regulatory requirements or compliance aspects
           - Note any specific conditions or prerequisites
           - Indicate if information might be outdated or version-specific
           - Highlight any procedural deadlines or time-sensitive elements

        4. Important Caveats
           - Clearly mark any ambiguities in the documentation
           - Note if there are multiple interpretations or approaches
           - Identify any missing critical information
           - Include relevant warnings or cautions

        Context:
        {context}

        Question:
        {question}

        Disclaimer: This response is based on provided documentation only and should not be considered legal advice.

        Response:"""
        
        # prompt = PromptTemplate(
        #     template=template,
        #     input_variables=["context", "question"]
        # )
        # Create the prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", ("""
                        You are an expert legal research assistant with deep knowledge of banking regulations and procedures. Your role is to provide accurate, well-structured answers based on the provided documentation.

                        Task:
                        Analyze the provided context and answer the question while following these guidelines:

                        Response Requirements:
                        1. Accuracy & Sources
                        - Base your answer strictly on the provided context
                        - Cite specific documents and sections when referencing information
                        - If information is not found in the context, explicitly state this
                        - Do not make assumptions or provide information beyond the given context

                        2. Structure & Clarity
                        - Begin with a clear, direct answer to the question
                        - Organize information in a logical sequence
                        - Use bullet points or numbered lists for complex procedures
                        - Highlight key points and requirements

                        3. Compliance & Precision
                        - Emphasize any regulatory requirements or compliance aspects
                        - Note any specific conditions or prerequisites
                        - Indicate if information might be outdated or version-specific
                        - Highlight any procedural deadlines or time-sensitive elements

                        4. Important Caveats
                        - Clearly mark any ambiguities in the documentation
                        - Note if there are multiple interpretations or approaches
                        - Identify any missing critical information
                        - Include relevant warnings or cautions  

                            <context>
                            {context}
                            </context>
                        
                         Disclaimer: This response is based on provided documentation only and should not be considered legal advice.""")),
                        ("human", "{question}")
        ])
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        # Create retrieval chain
        retrieval_chain = (
            {
                "context": lambda x: format_docs(
                    self.retriever.get_relevant_documents(x)
                ),
                "question": RunnablePassthrough()
            }
            | prompt
            | llm
            | StrOutputParser()
        )
        
        return retrieval_chain

# Example usage
if __name__ == "__main__":
    # Initialize system
    hybrid_rag = HybridRAGSystem(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        bm25_weight=0.1,
        vector_weight=0.9,
        use_reranker=True
    )
    
    # Add documents
    hybrid_rag.add_documents("document_loader/docs")
    
    # Create chain
    chain = hybrid_rag.create_retrieval_chain()
    
    print("\nAsking questions about the document:")
    while True:
        q = input("Ask a question: ")
        if q == "exit":
            break
        else:
            response = chain.invoke(q)
            print(f"A: {response}")