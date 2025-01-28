import os
from markitdown import MarkItDown
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain import hub
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import UnstructuredMarkdownLoader
# from langchain.chains import GraphQAChain
# from langchain_community.graphs.networkx_graph import NetworkxEntityGraph
import pacmap
import pandas as pd
import plotly.express as px
import numpy as np
import nltk
nltk.download('averaged_perceptron_tagger_eng')
from dotenv import load_dotenv

load_dotenv()

class FileQuestionAnswerer:
    def __init__(self, openai_api_key, chunk_size = 1000, chunk_overlap = 100):
        """Initialize the RAG system with OpenAI API key."""
        os.environ["OPENAI_API_KEY"] = openai_api_key
        
        # Initialize OpenAI components
        self.embeddings = OpenAIEmbeddings()
        self.llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini")
        
        MARKDOWN_SEPARATORS = [
                "\n#{1,6} ",
                "```\n",
                "\n\\*\\*\\*+\n",
                "\n---+\n",
                "\n___+\n",
                "\n\n",
                "\n",
                " ",
                "",
            ]
        # Initialize the text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, # The maximum number of characters in a chunk: we selected this value arbitrarily
            chunk_overlap=chunk_overlap, # The number of characters to overlap between chunks
            add_start_index=True,  # If `True`, includes chunk's start index in metadata
            strip_whitespace=True,  # If `True`, strips whitespace from the start and end of every document
            separators=MARKDOWN_SEPARATORS,
        )
        
        self.vector_store = None
        self.qa_chain = None
        self.docs_processed = []
        self.llm_transformer = None

    def load_file(self, file_path, vector_store = "Chroma"):
        """Load and process a PDF file."""
        # Load PDF
        docs = []
        md = MarkItDown(llm_client=self.llm)
        supported_extensions = ('.pptx', '.docx', '.pdf', '.jpg', '.jpeg', '.png')
        files_to_convert = [f for f in os.listdir(file_path) if f.lower().endswith(supported_extensions)]
        for file in files_to_convert:
            print(f"\nConverting {file}...")
            try:
                if file.lower().endswith('.md'):
                    # Directly load markdown files
                    docs.append(UnstructuredMarkdownLoader(file_path + "/" + file).load()[0])
                else:
                    result = md.convert(file_path + "/" + file)
                    md_file = os.path.splitext(file)[0] + '.md'
                    with open(file_path + "/" + md_file, 'w') as f:
                        f.write(result.text_content)
                    docs.append(UnstructuredMarkdownLoader(file_path + "/" + md_file).load()[0])
                
                print(f"Successfully converted {file}")
            except Exception as e:
                raise(f"Error converting {file}: {str(e)}")

        print("\nAll conversions completed!")

        # Split the text into chunks
        # docs_processed = []
        for doc in docs:
            self.docs_processed += self.text_splitter.split_documents([doc])
        
        if vector_store.lower() == "chroma":
            # Create vector store Chroma
            self.vector_store = Chroma.from_documents(
                documents=self.docs_processed,
                embedding=self.embeddings
            )
        else:
            # Create vector store FAISS
            self.vector_store = FAISS.from_documents(
                documents=self.docs_processed,
                embedding=self.embeddings
            )

        # Create QA chain
        system_prompt = (
            "Use the given context to answer the question. "
            "If you don't know the answer, say you don't know. "
            "keep the answer as detailed as possible. "
            "Context: {context}"
        )
        retrieval_qa_chat_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{input}"),
            ]
        )
        # retrieval_qa_chat_prompt = hub.pull("langchain-ai/retrieval-qa-chat")

        question_answer_chain = create_stuff_documents_chain(self.llm, retrieval_qa_chat_prompt)

        self.qa_chain = create_retrieval_chain(
            self.vector_store.as_retriever(
                            search_kwargs={"k": 10}
                        ), 
            question_answer_chain)

        return f"Processed file with {len(docs)} text chunks"

    def ask_question(self, question):
        """Ask a question about the loaded PDF."""
        if not self.qa_chain:
            return "Please load a file first"
        
        response = self.qa_chain.invoke({"input": question})
        # response = self.qa_chain.run(question)
        return response
        
def plot_projections(qa_system, question):
    query_vector = qa_system.embeddings.embed_query(question)
    embedding_projector = pacmap.PaCMAP(
        n_components=2, n_neighbors=None, MN_ratio=0.5, FP_ratio=2.0, random_state=1
    )

    embeddings_2d = [
        list(qa_system.vector_store.index.reconstruct_n(idx, 1)[0])
        for idx in range(len(qa_system.docs_processed))
    ] + [query_vector]

    # Fit the data (the index of transformed data corresponds to the index of the original data)
    documents_projected = embedding_projector.fit_transform(
        np.array(embeddings_2d), init="pca"
    )
    df = pd.DataFrame.from_dict(
        [
            {
                "x": documents_projected[i, 0],
                "y": documents_projected[i, 1],
                "source": qa_system.docs_processed[i].metadata["source"].split("/")[1],
                "extract": qa_system.docs_processed[i].page_content[:100] + "...",
                "symbol": "circle",
                "size_col": 4,
            }
            for i in range(len(qa_system.docs_processed))
        ]
        + [
            {
                "x": documents_projected[-1, 0],
                "y": documents_projected[-1, 1],
                "source": "User query",
                "extract": question,
                "size_col": 100,
                "symbol": "star",
            }
        ]
    )

    # Visualize the embedding
    fig = px.scatter(
        df,
        x="x",
        y="y",
        color="source",
        hover_data="extract",
        size="size_col",
        symbol="symbol",
        color_discrete_map={"User query": "black"},
        width=1000,
        height=700,
    )
    fig.update_traces(
        marker=dict(opacity=1, line=dict(width=0, color="DarkSlateGrey")),
        selector=dict(mode="markers"),
    )
    fig.update_layout(
        legend_title_text="<b>Chunk source</b>",
        title="<b>2D Projection of Chunk Embeddings via PaCMAP</b>",
    )
    fig.show()

def main():
    """Example usage of the file Question Answerer."""
    debug = False
    # Replace with your OpenAI API key
    OPENAI_API_KEY =os.getenv("OPENAI_API_KEY")
    
    # Initialize the system
    qa_system = FileQuestionAnswerer(OPENAI_API_KEY)
    
    # Load a PDF file
    print("Loading file...")
    result = qa_system.load_file("document_loader/docs", vector_store='FAISS')
    print(result)
    
    # Ask questions
    print("\nAsking questions about the document:")
    while True:
        q = input("Ask a question: ")
        if q == "exit":
            break
        else:
            answer = qa_system.ask_question(q)
            print(f"A: {answer['answer']}")
            # print(f"A: {answer}")
            if debug:
                plot_projections(qa_system, q)

            

if __name__ == "__main__":
    main()