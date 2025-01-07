from pydantic import Field, BaseModel
import os
from typing import List
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAI
from langchain_core.messages import HumanMessage

load_dotenv()

model = OpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL")
)

model = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL")
)

prompt = """
Based on the following extracted information, provide a comprehensive answer to: 
What are the latest developments in quantum computing?
    
    Extracted information:
    --------------------------------------------------
    Rapid advancements have been made possible based on lessons learned from
previous generations of computing paradigms, not only have we adopted concepts
such as opensource and fabrication and development of enabling hardware and
fabrication techniques. Several companies such as IBM, Google, Rigetti, and
D‑Wave are investing in superconducting qubit technologies because they are
based on fabrication techniques and technologies that overlap greatly with the
traditional semiconductor industry and they can accelerate advancement
leveraging their expertise in the field. Here the main challenge is the
reduction of error per gate layer. In the near term, they are seeing the
potential to find the first wave of utility from this technology. Many
companies are exploring potential application of these technologies and making
initial findings available publicly, a database of over 1000 publications is
available online [56].

## 4 Advancements

### 4.1 Advancements in Quantum Computing Technologies

Recent advancements of enabling technologies over the past two years are
advancing the timeline expected for significant quantum advantage for various
end-users.
    --------------------------------------------------

    Answer:
"""
messages = [ 
    HumanMessage(content= "What are the latest advancements in AI for Code development?" )
]


result = model.invoke(messages)
print(result) 
exit ()

from langchain_community.utilities import GoogleSearchAPIWrapper
# Set up Google Search API credentials
#os.environ["GOOGLE_CSE_ID"] = "your-google-cse-id"
#os.environ["GOOGLE_API_KEY"] = "your-google-api-key"

# Example user query
user_input = "What are the latest advancements in AI for Code development?"

# Initialize the Google Search API Wrapper
search = GoogleSearchAPIWrapper()

from langchain_core.prompts import PromptTemplate

# Define a custom prompt template
search_prompt = PromptTemplate(
    input_variables=["question"],
    template="""You are an assistant tasked with improving Google search results. 
    Generate FIVE Google search queries that are similar to this question: {question}

Please format your response as a numbered list like this:
1. [first query]
2. [second query]
3. [third query]
4. [fourth query]
5. [fifth query]""",
)

# Define a custom output parser
class LineList(BaseModel):
    """List of questions."""
    lines: List[str] = Field(description="Questions")

from langchain_core.output_parsers import PydanticOutputParser
import re

class QuestionListOutputParser(PydanticOutputParser):
    """Output parser for a list of numbered questions."""
    def __init__(self) -> None:
        super().__init__(pydantic_object=str)

    def parse(self, text: str) -> str:
        return text 
        # Updated regex to better handle the numbered list format
        lines = [line.strip() for line in re.findall(r'\d+\.\s*(.+?)(?=\n\d+\.|$)', text, re.DOTALL)]
        if not lines:
            raise ValueError(f"Could not parse questions from text: {text}")
        return LineList(lines=lines)

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

# Initialize the vector store (Chroma) with OpenAI embeddings
vectorstore = Chroma(embedding_function=OpenAIEmbeddings(), persist_directory="./chroma_db_oai")

from langchain.chains.llm import LLMChain
# Initialize the LLMChain
llm_chain = LLMChain(
    llm=model,
    prompt=search_prompt,
    output_parser=QuestionListOutputParser(),
)

result = llm_chain.invoke(user_input)
print (result)
exit() 


from langchain_community.retrievers.web_research import WebResearchRetriever
# Initialize the WebResearchRetriever with the custom LLMChain
web_research_retriever_llm_chain = WebResearchRetriever(
    vectorstore=vectorstore,
    llm_chain=llm_chain,
    search=search,
    allow_dangerous_requests=True
)

# Run the custom retriever
docs = web_research_retriever_llm_chain.get_relevant_documents(user_input)

# Print the retrieved documents
for doc in docs:
    print(doc.metadata["source"], doc.page_content[:200])




# Initialize the WebResearchRetriever
# web_research_retriever = WebResearchRetriever.from_llm(
#     vectorstore=vectorstore,
#     llm=model,
#     search=search,
#     allow_dangerous_requests=True
# )

# Example user query
#user_input = "where is the most beautiful place in earth?"

# Retrieve relevant documents
#docs = web_research_retriever.get_relevant_documents(user_input)

# Print the retrieved documents
# for doc in docs:
#     print(doc.metadata["source"], doc.page_content[:200])  # Print the source and the first 200 characters of the content


#result = model.invoke("where is the best place in the world?")
#print(result)