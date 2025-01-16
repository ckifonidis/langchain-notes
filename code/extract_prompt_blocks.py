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
    pattern = r'```name\s*([\s\S]*?)```\s*```prompt\s*([\s\S]*?)```'
    match = re.search(pattern, text)
    
    if not match:
        raise ValueError("Could not find valid prompt blocks in the file")
        
    return PromptInfo(
        name=match.group(1).strip(),
        content=match.group(2).strip()
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

# Example usage
if __name__ == "__main__":
    doc_splitter_prompt =  get_promt_template("doc_splitter", ["text","section"])
