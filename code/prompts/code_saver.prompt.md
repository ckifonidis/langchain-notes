```name
code_types_saver
```

```prompt
Get the text I give you. This text is C# code. 
In each block you will find two items: a hint for the filename you must create and the code you have to put in the file.
I want you to return a json representation of these code blocks.
The json schema must be as following:
{{
    "files": [
        {{
            "filename": "string",
            "code": "string"
        }},
        ...
    ]
}} 
where filename is the filename you must create and code is the code you have to put in the file.

I want you to return just the json representation, nothing else.
You must be carful to maintain the indentation of the code, and avoid to add
extra spaces or new lines.

I want you to return everything and avoid to omit anything.

The code is here:
{code}
```