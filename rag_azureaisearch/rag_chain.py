from typing import List, Dict, Any
# from langchain.chat_models import AzureChatOpenAI
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
# from langchain.chains import LLMChain
from config import (
    OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_DEPLOYMENT_NAME,
)
from azure_search_manager import AzureSearchManager

class RAGChain:
    def __init__(self):
        self.search_manager = AzureSearchManager()
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.0, api_key=OPENAI_API_KEY)
        # self.llm = AzureChatOpenAI(
        #     openai_api_key=AZURE_OPENAI_API_KEY,
        #     azure_endpoint=AZURE_OPENAI_ENDPOINT,
        #     deployment_name=AZURE_DEPLOYMENT_NAME,
        #     temperature=0,
        # )

        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful AI assistant. Use the following context to answer the user's question.
            If you don't know the answer, just say that you don't know, don't try to make up an answer.
            
            Context:
            {context}
            """),
            ("human", "{question}")
        ])

        self.chain = self.prompt_template | self.llm 
        # LLMChain(llm=self.llm, prompt=self.prompt_template)

    def _format_context(self, search_results: List[Dict[str, Any]]) -> str:
        """
        Format search results into a context string
        """
        context_parts = []
        for i, result in enumerate(search_results, 1):
            context_part = f"[Document {i}]\n"
            context_part += f"Source: {result['source']}\n"
            context_part += f"Content: {result['content']}\n"
            context_parts.append(context_part)
        
        return "\n\n".join(context_parts)

    async def generate_response(self, question: str) -> Dict[str, Any]:
        """
        Generate a response using RAG:
        1. Search for relevant documents
        2. Format context from search results
        3. Generate response using LLM
        """
        # Get relevant documents from Azure Search
        search_results = self.search_manager.search(question)
        
        if not search_results:
            return {
                "answer": "I couldn't find any relevant information to answer your question.",
                "sources": [],
                "context": ""
            }

        # Format context from search results
        context = self._format_context(search_results)

        # Generate response using LLM
        response = await self.chain.invoke(
            {context:context,
            question:question
        })

        return {
            "answer": response,
            "sources": [result['source'] for result in search_results],
            "context": context
        }