# Document Section Extraction Guidelines

There are cases where we need to extract multiple sections from a document file. In these scenarios, the document_splitter prompt must be adjusted accordingly to handle multiple section extraction.

## Common Use Cases

### Common Types Implementation
Requires extraction of:
- Common Types 


### Types Implementation
Requires extraction of:
- Types Layer

### Database Implementation
Requires extraction of:
- Domain
- Database Layer section
- DB Tables

### Safe Executor Implementation
Requires extraction of:
- Types Layer
- Endpoint Execution Logic

### Controllers Implementation 
Requires extraction of:
- Web API Ground Rules
- Common Types Section  
- Interface Layer
- Controller Layer

When implementing these cases, ensure the document_splitter prompt is configured to handle multiple section extraction and maintain proper context between sections.
