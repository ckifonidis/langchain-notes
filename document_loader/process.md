# PDF RAG System Features

## PDF Document Processing
- Loads single PDF
- Chunks text with configurable size and overlap
- Maintains document metadata

## Advanced Retrieval
- Uses OpenAI embeddings
- Stores vectors in Chroma database
- Retrieves relevant chunks based on similarity

## Smart Question Answering
- Uses GPT-3.5 for lower cost
- Maintains conversation history
- Custom prompt template for better answers
- Returns source citations with page numbers

## Error Handling and Metadata
- Robust error checking
- Tracks document sources
- Returns relevant chunks and sources