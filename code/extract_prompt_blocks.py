import re
from typing import NamedTuple

class PromptInfo(NamedTuple):
    name: str
    content: str

def extract_prompt_blocks(filename: str) -> PromptInfo:
    """Extract prompt name and content blocks from a markdown file.
    
    Args:
        filename: Path to the markdown file containing prompt blocks
        
    Returns:
        PromptInfo: Named tuple containing name and content strings
    """
    with open(filename, 'r', encoding='utf-8') as file:
        text = file.read()
        
    # Regex pattern to capture name and content blocks
    name_pattern = r'```name\s*\n([\s\S]*?)\n```'
    prompt_pattern = r'```prompt\s*\n([\s\S]*?)\n```'
    
    name_match = re.search(name_pattern, text)
    prompt_match = re.search(prompt_pattern, text)
    
    if not name_match or not prompt_match:
        raise ValueError("Could not find valid prompt blocks in the file")
        
    return PromptInfo(
        name=name_match.group(1).strip(),
        content=prompt_match.group(1).strip()
    )

import os
from langchain.prompts import PromptTemplate
def get_promt_template(prompt_name:str, input_variables:list[str] ) -> PromptTemplate:
    filename =  os.path.join(os.path.dirname(__file__),"prompts",f"{prompt_name}.prompt.md")
    blocks= extract_prompt_blocks(filename)
    template = PromptTemplate(
        input_variables=input_variables,
        template=blocks.content
    )
    return template 

get_doc_splitter = lambda : get_promt_template("doc_splitter", ["text","section"])
get_types_writer = lambda : get_promt_template("types_writer", ["types_description", "projectname"])
get_code_saver = lambda : get_promt_template("code_saver", ["code"])

# Example usage
if __name__ == "__main__":
    doc_splitter_prompt =  get_promt_template("doc_splitter", ["text","section"])
