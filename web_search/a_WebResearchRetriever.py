#langchain web research retriever example

import os
import json 
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain_community.llms import OpenAI
from langchain.prompts import PromptTemplate

load_dotenv()
def test_credentials():
    try:
        search = GoogleSearchAPIWrapper()
        results = search.run("test")
        print("Credentials are valid. Test search succeeded.")
    except Exception as e:
        print("Credentials are invalid or there was an error:", e)

def format_document(document):
    return {
        "page_content": document.page_content,
        "type": document.type,
        "metadata": document.metadata
    }


model = ChatOpenAI(
    model_name="gpt-4o-mini",  # or your specific model name
    temperature=0.7
)

model = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL")
)

# Define a prompt template for the LLM chain
question_template = """
You are a helpful assistant that summarizes web content.

Question: {question}
Content: {content}

Summary:
"""

prompt = PromptTemplate(
    input_variables=["question"],  # Need both variables
    template=question_template
)

# Create the LLM chain
#llm_chain = LLMChain(prompt=prompt, llm=model)
llm_chain = prompt | model 

#from langchain_community.vectorstores import Chroma
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

# Initialize the vector store (Chroma) with OpenAI embeddings
vectorstore = Chroma(embedding_function=OpenAIEmbeddings(), persist_directory="web_research_db")

#from langchain_google_community import GoogleSearchAPIWrapper 
# this is a newer version not yet integrated in GoogleSearchAPIWrapper
# so it generates conflicts

#from langchain_google_community import GoogleSearchAPIWrapper
from langchain_community.utilities.google_search import GoogleSearchAPIWrapper
# Set up Google Search API credentials
#os.environ["GOOGLE_CSE_ID"] = "your-google-cse-id"
#os.environ["GOOGLE_API_KEY"] = "your-google-api-key"

from langchain_community.retrievers import WebResearchRetriever

google_cse_id = os.getenv("GOOGLE_CSE_ID")
google_api_key = os.getenv("GOOGLE_API_KEY")

if not google_cse_id or not google_api_key:
    raise ValueError("Missing Google API credentials. Please set GOOGLE_CSE_ID and GOOGLE_API_KEY")

os.environ["GOOGLE_CSE_ID"] = os.getenv("GOOGLE_CSE_ID", "")
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "")

test_credentials()

search = GoogleSearchAPIWrapper()

print("Initializing vectorstore:", vectorstore)
print("Initializing llm_chain:", llm_chain)

# Initialize the WebResearchRetriever
web_retriever = WebResearchRetriever.from_llm(
    vectorstore=vectorstore,
    llm=model,
    search=search,
    num_search_results=5,
    allow_dangerous_requests=True
)

def simple_search(query: str):
    results = web_retriever.invoke(query)
    return results 

def generate_answers(query: str):
    from langchain.chains import RetrievalQAWithSourcesChain

    qa_chain = RetrievalQAWithSourcesChain.from_chain_type(retriever=web_retriever, llm=model)

    result = qa_chain({"question": query})
    return result

if __name__ == "__main__":
    query = "What are the latest trends in artificial intelligence?"

    results = simple_search(query)
    for result in results:
        print("-" * 120)
        from pprint import pprint, pformat
        print(pformat(format_document(result)).replace("\\n", ""))
    
    
    input("Press Enter to continue...")
    
    result = generate_answers(query)
    dresult = { "question": result["question"], "answer": result["answer"], "sources": result["sources"] }
    from pprint import pprint, pformat
    print(pformat(dresult).replace("\\n", ""))
