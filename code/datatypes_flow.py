import os
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain.chains.llm import LLMChain
from langchain.chains.sequential import SequentialChain
from extract_prompt_blocks import get_doc_splitter, get_types_writer, get_code_saver
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

split = LLMChain(llm=model, prompt=get_doc_splitter(), output_key="types_description")
types_coder = LLMChain(llm=model, prompt=get_types_writer(), output_key="code")
code_saver = LLMChain(llm=model, prompt=get_code_saver(), output_key="code_json")

write_code = SequentialChain (
    chains=[split, types_coder, code_saver],
    input_variables=["text", "section", "projectname"], 
    output_variables=["types_description", "code", "code_json"],
    verbose=True
)

result = write_code.invoke(
    {
        "text": text, 
        "section": "Types Layer Section",
        "projectname": "DevPortal"
    }
)
print(result["types_description"])
print(result["code"])
print(result["code_json"])