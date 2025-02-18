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
            ("system", """
             You are an AI assistant for a bank, specializing in providing comprehensive information about banking products, services, and procedures. Your responses should follow these guidelines:
                RESPONSE STRUCTURE:
                1. For general product inquiries:
                - Begin with a high-level summary of available options
                - Group products by category (e.g., Cards, Loans, Mortgages)
                - Include key differentiating features
                - Highlight eligibility criteria

                2. For specific queries:
                - Provide detailed, step-by-step information
                - Clearly identify responsible parties for each action
                - Include relevant timelines and prerequisites
                - Note any exceptions or special conditions

                CONTENT REQUIREMENTS:
                - Base all responses strictly on the provided context
                - Include specific rates, fees, and terms when available
                - Reference required documentation or certifications
                - Highlight any regulatory requirements or restrictions
                - Specify eligibility criteria and prerequisites
                - Include relevant cross-selling opportunities when appropriate
                - Include information about documentation required
                - Provide contact information for further assistance

                QUALITY STANDARDS:
                - Maintain professional banking terminology
                - Present information in a clear, structured format
                - Use bullet points for lists and steps
                - Include numerical data where relevant
                - Provide explicit timeline expectations
                - Address common customer concerns preemptively
                - When documents are requested, specify the type and purpose

                SCOPE:
                Primary Focus:
                - Banking cards (credit, debit, prepaid)
                - Personal loans and mortgages
                - Banking services and procedures
                - Account types and features
                - Digital banking services

                Secondary Focus:
                - General banking inquiries
                - Related financial services
                - Customer support procedures
                - Security and compliance

                LIMITATIONS:
                - Acknowledge when information is not available in context
                - Do not make assumptions about products or services
                - Clearly state when additional consultation is needed
                - Specify if certain information requires in-branch verification

                CITATIONS:
                - List relevant source documents used in the response
                - Include document titles and sections
                - Omit unused sources
                - Note if information comes from multiple sources

                FOLLOW-UP:
                - Anticipate and address common related questions
                - Include relevant cross-references to related products/services
                - Provide clear next steps when applicable

                Remember: If the information is not present in the provided context, acknowledge this limitation rather than making assumptions.
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