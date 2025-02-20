import os
from langchain.prompts import PromptTemplate
def get_promt_template(prompt_name:str, input_variables:list[str] ) -> PromptTemplate:
    filename =  os.path.join(os.path.dirname(__file__),"prompts",f"{prompt_name}.prompt.md")
    with open(filename, 'r', encoding='utf-8') as file:
        text = file.read()
    template = PromptTemplate(
        input_variables=input_variables,
        template=text
    )
    return template 

get_doc_splitter = lambda : get_promt_template("doc_splitter", ["text","section"])
get_types_writer = lambda : get_promt_template("types_writer", ["types_description", "projectname"])
get_code_saver = lambda : get_promt_template("code_saver", ["code"])

# Example usage
if __name__ == "__main__":
    doc_splitter_prompt =  get_promt_template("doc_splitter", ["text","section"])
