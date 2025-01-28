from pprint import pprint

from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv

from model_selector import ModelType, OpenAIModels, use_model
from message_printer import print_messages


load_dotenv()

# Load the system prompt from file
with open('databricks_notebook/merchant_insights/api/api_func_design_prompt.md', 'r') as file:
    system_prompt = file.read()

# Load the notebook content
with open('databricks_notebook/merchant_insights/api/notebooks/merchant_promotion_insights/AnalyticalCardsCustomerCharacteristics.py', 'r') as file:
    notebook_content = file.read()

# Load and combine table descriptions
table_description_files = [
    'create_postal_codes.sql',
    'create_customer.sql',
    'create_mcc_categories.sql',
    'create_customer_sector_volumes.sql',
    'create_cards_customer_characteristics.sql'
]

table_descriptions = ""
for filename in table_description_files:
    with open(f'databricks_notebook/merchant_insights/api/table_descriptions/{filename}', 'r') as file:
        table_descriptions += f"\n-- {filename}\n" + file.read()

# Initialize model using model selector
model = use_model(
    ModelType.OPENAI,
    model_name=OpenAIModels.GPT_4O_MINI
)

# Configuration for the prompt template
template_vars = {
    "notebook_content": notebook_content,
    "source_table_descriptions": table_descriptions
}

messages_template = [
    ("system", system_prompt),
    ("human", "Please analyze the following notebook and create a functional specification document:\n\n{notebook_content}\n"),
]

prompt_template = ChatPromptTemplate.from_messages(messages_template)
messages = prompt_template.invoke(template_vars)
result = model.invoke(messages)
print_messages(result)
