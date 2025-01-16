import os
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain.chains.llm import LLMChain
from extract_prompt_blocks import get_doc_splitter
from dotenv import load_dotenv

load_dotenv()

model = ChatOpenAI(model = "gpt-4o")
model = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL")
)

filename =  os.path.join(os.path.dirname(__file__),"documents","DevPortal API TDD _ BlogTag.md")
with open(filename, 'r', encoding='utf-8') as file:
    text = file.read()

split = LLMChain(llm=model, prompt=get_doc_splitter(), output_key="section")

result = split.invoke({"text": text, "section": "Types Layer Section"})
print(result["section"])