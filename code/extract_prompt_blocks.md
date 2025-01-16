# Prompt Block Extractor Documentation

## Overview
The `extract_prompt_blocks` function extracts named prompt blocks from markdown files using regular expressions. It looks for specially formatted code blocks containing prompt names and content.

## Regular Expression Patterns

### Name Block Pattern
```python
r'```name[\s\S]*?\n(.*?)\n```'
```
- Matches markdown code blocks tagged with "name"
- Captures the content between the code block markers
- Uses [\s\S]*? to match any characters (including newlines) before the content
- Uses non-greedy matching to capture only the name content

### Prompt Content Pattern  
```python
r'```prompt[\s\S]*?\n(.*?)\n```'
```
- Matches markdown code blocks tagged with "prompt"
- Captures the content between the code block markers
- Uses [\s\S]*? to match any characters (including newlines) before the content
- Uses non-greedy matching to capture only the prompt content

## Input Format
The function expects markdown files with the following format:
```markdown
```name
Prompt Name
```

```prompt
Prompt Content
```
```

## Function Signature
```python
def extract_prompt_blocks(filename: str) -> PromptInfo
```

### Parameters
- `filename`: Path to the markdown file containing the prompt blocks

### Returns
A `PromptInfo` named tuple with two fields:
- `name`: The extracted prompt name (string)
- `content`: The extracted prompt content (string)

## Example Usage
```python
from extract_prompt_blocks import extract_prompt_blocks

# Extract prompt from file
prompt_info = extract_prompt_blocks("example.md")

print(f"Prompt Name: {prompt_info.name}")
print(f"Prompt Content: {prompt_info.content}")
```

## Error Handling
The function will raise a `ValueError` if:
- The input file cannot be read
- The required code blocks are not found
- The code blocks are not properly formatted

## Requirements
- Python 3.6+
- Standard library only (no external dependencies)

## References
### Official Documentation
- [Python re module documentation](https://docs.python.org/3/library/re.html)
- [Regular Expression HOWTO](https://docs.python.org/3/howto/regex.html)

### Learning Resources
- [Regex101 - Interactive regex tester](https://regex101.com/)
- [Regular-Expressions.info](https://www.regular-expressions.info/)
- [Regexr - Learn, Build & Test Regex](https://regexr.com/)

### Cheat Sheets
- [Python Regex Cheat Sheet](https://www.debuggex.com/cheatsheet/regex/python)
- [Regex Cheat Sheet](https://cheatography.com/davechild/cheat-sheets/regular-expressions/)
