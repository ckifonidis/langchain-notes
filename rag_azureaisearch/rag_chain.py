from typing import List, Dict, Any
# from langchain.chat_models import AzureChatOpenAI
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
import nltk
# from langchain.chains import LLMChain
from config import (
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
)
from azure_search_manager import AzureSearchManager
from tokencounter import TokenCounter
import os


class RAGChain:
    def __init__(self):
        self.search_manager = AzureSearchManager()
        # self.llm = AzureChatOpenAI(
        #     model="gpt-4o",
        #     temperature=0.0,
        #     api_version=AZURE_OPENAI_API_VERSION,
        #     azure_endpoint=AZURE_OPENAI_ENDPOINT,
        #     api_key=AZURE_OPENAI_KEY,
        #     )
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.0, api_key=os.getenv("OPENAI_API_KEY"))
        # self.llm = ChatAnthropic(model="claude-3-sonnet-20240229", temperature=0.0, api_key=os.getenv("ANTHROPIC_API_KEY"))
        # self.llm = AzureChatOpenAI(
        #     openai_api_key=AZURE_OPENAI_API_KEY,
        #     azure_endpoint=AZURE_OPENAI_ENDPOINT,
        #     deployment_name=AZURE_DEPLOYMENT_NAME,
        #     temperature=0,
        # )

        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful AI assistant. Use the following context to answer the user's question. 
            Advice them as clear as possible and be very analytical and detailed in your response.
             Do not miss any important details. Provide response only based on the context given including any special cases or
             exceptions that may arise. In addition, with the response try to cover a wide range of possible questions that the user may 
             want clarification afterwards. if actions are taken, you need to clarify who does what. Make sure that if steps are provided in the answer, 
             the sequence is the correct one as described in the context, who is responsible when. The questions should be answered in a professional manner. 
             The questions should related with actions, products, services, certifications, etc. about banking cards, personal loans or mortgages. 
             But also more general questions can be asked and then answers need to be provided considering the overall range of products, services of the bank.
            If you don't know the answer, just say that you don't know, don't try to make up an answer.
             At the end of the reply, provide a list of the title of the sources used to generate the answer, only the useful ones.
            The context is the following:
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
        # print(context)
        

    #     tc = TokenCounter()
    #     total_tokens = lambda x: print(tc.estimate_tokens_from_chars(x))
    #     messages = [
    #     {"role": "system", "content": ""},
    #     {"role": "user", "content": context},
    #       ]
    #     print(f"Total tokens: {total_tokens(context)}")
        # Generate response using LLM
        response = self.chain.invoke(
            {"context": context,
             "question": question
            })

        return {
            "answer": response.content,
            "sources": [result['source'] + " / " + str(result['score']) for result in search_results],
            "context": context
        }