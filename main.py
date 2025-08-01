import os
import json
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_ollama.embeddings import OllamaEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
load_dotenv()

LANGCHAIN_PROJECT = "OLLAMA-MEDICAL-APP-V2"
os.environ['LANGCHAIN_API_KEY'] = os.getenv("LANGCHAIN_API_KEY")
os.environ['LANGCHAIN_TRACING_V2'] = "true"
os.environ['LANGCHAIN_PROJECT'] = LANGCHAIN_PROJECT

LLM_MODEL = "gemma2-9b-it"
OLLAMA_EMBEDDING_MODEL = "mxbai-embed-large:latest"

PDF_FILES = [
    "pdfs/BAJHLIP23020V012223.pdf",
    "pdfs/HDFHLIP23024V072223.pdf",
    "pdfs/EDLHLGA23009V012223.pdf",
    "pdfs/CHOTGDP23004V012223.pdf",
]
FAISS_INDEX_PATH = "faiss_index_insurance"

class InsuranceAnalysis(BaseModel):
    """Structured data model for the insurance claim analysis."""
    Decision: str = Field(description="The final decision: 'Approved', 'Rejected', or 'Needs More Info'")
    Amount: str = Field(description="The claimable amount as a string (e.g., '50000', 'Up to 2% of Sum Insured', or 'N/A')")
    Justification: str = Field(description="A detailed justification for the decision, citing specific policy clauses or sections from the context provided.")
    Missing_Info: list[str] = Field(default=[], description="A list of specific questions or information needed if the decision is 'Needs More Info'.")

def load_documents(file_paths):
    """Loads multiple PDF documents from the given file paths."""
    all_documents = []
    print("Loading documents...")
    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"Warning: Document not found at {file_path}. Skipping.")
            continue
        try:
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            all_documents.extend(documents)
            print(f"Loaded {len(documents)} pages from {file_path}")
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    print(f"Total pages loaded: {len(all_documents)}.")
    return all_documents

def split_documents(documents, chunk_size=1000, chunk_overlap=200):
    """
    Splits loaded documents into smaller chunks.
    
    IMPROVEMENT NOTE: For legal/policy documents, consider 'semantic chunking'.
    Instead of splitting by character count, split by logical sections (e.g., clauses, 
    paragraphs, tables). This requires custom logic using a library like PyMuPDF to 
    identify document structure (headings, lists) but yields much better context.
    """
    print(f"Splitting documents into chunks (size={chunk_size}, overlap={chunk_overlap})...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks.")
    return chunks

def create_vector_store(chunks, embedding_model, save_path=None):
    """Creates a FAISS vector store from document chunks and saves it."""
    print(f"Creating embeddings and FAISS vector store with {embedding_model}...")
    embeddings = OllamaEmbeddings(model=embedding_model)
    vector_store = FAISS.from_documents(chunks, embeddings)
    print("Vector store created.")

    if save_path:
        vector_store.save_local(save_path)
        print(f"Vector store saved locally to {save_path}")
    return vector_store

def setup_llm(model_name, temperature=0.1):
    """Initializes the LLM for generation."""
    print(f"Setting up LLM with model: {model_name}...")
    llm = ChatGroq(model=model_name, temperature=temperature, api_key=os.getenv("GROQ_API_KEY"))
    print("LLM setup complete.")
    return llm

def setup_rag_chain(retriever, llm):
    """Sets up the RAG chain with Pydantic for robust, structured output."""
    print("Setting up RAG chain with Pydantic Output Parser...")
    
    pydantic_parser = PydanticOutputParser(pydantic_object=InsuranceAnalysis)

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", """You are a world-class insurance policy analysis expert. Your task is to act as a claims adjudicator.
        Based on the provided policy document excerpts (context) and the user's query, you must make a decision.

        Follow these steps meticulously:
        1.  Analyze the user's query to understand the claim (age, procedure, location, policy details).
        2.  Scrutinize the provided context for all relevant clauses, definitions, exclusions, and limits.
        3.  Make a final `Decision` ('Approved', 'Rejected', or 'Needs More Info').
        4.  Determine the `Amount` covered, if applicable. If not, state 'N/A'.
        5.  Write a clear `Justification`, citing the exact clauses from the context that support your decision. Be precise.
        6.  If the context is insufficient to make a decision, your `Decision` MUST be 'Needs More Info', and you must populate the `Missing_Info` list with specific questions for the user.

        Your entire response must be a JSON object that strictly follows the provided format instructions. Do not add any text outside of the JSON structure.

        {format_instructions}
        """),
        ("human", "Policy Documents Context:\n---\n{context}\n---\n\nUser Query: {query}")
    ])
    
    prompt_with_format = prompt_template.partial(
        format_instructions=pydantic_parser.get_format_instructions()
    )

    rag_chain = (
        {"context": retriever, "query": RunnablePassthrough()}
        | prompt_with_format
        | llm
        | pydantic_parser
    )
    print("RAG chain setup complete.")
    return rag_chain

def setup_advanced_rag_chain(chunks, vector_store, llm):
    """
    (Optional) Sets up an advanced RAG chain using Hybrid Search (BM25 + FAISS).
    This combines keyword search with semantic search for more accurate retrieval.
    """
    print("Setting up ADVANCED RAG chain with Hybrid Search...")
    faiss_retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    
    bm25_retriever = BM25Retriever.from_documents(chunks)
    bm25_retriever.k = 5
    
    ensemble_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, faiss_retriever],
        weights=[0.5, 0.5]
    )

    return setup_rag_chain(ensemble_retriever, llm)

def process_insurance_query(query, rag_chain):
    """Processes a query using the RAG chain and returns the structured result."""
    print(f"\nProcessing query: '{query}'")
    try:
        response_obj = rag_chain.invoke(query)
        return response_obj
    except Exception as e:
        print(f"An error occurred during chain invocation: {e}")
        return InsuranceAnalysis(
            Decision="Error",
            Amount="N/A",
            Justification=f"An unrecoverable error occurred: {str(e)}",
            Missing_Info=[]
        )

if __name__ == "__main__":
    if os.path.exists(FAISS_INDEX_PATH):
        print(f"Loading existing FAISS index from {FAISS_INDEX_PATH}")
        embeddings = OllamaEmbeddings(model=OLLAMA_EMBEDDING_MODEL)
        vector_store = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
        documents = load_documents(PDF_FILES)
        chunks = split_documents(documents)
    else:
        print("FAISS index not found. Creating a new one from scratch.")
        documents = load_documents(PDF_FILES)
        if not documents:
            print("No documents loaded. Exiting.")
            exit()
        chunks = split_documents(documents)
        vector_store = create_vector_store(chunks, OLLAMA_EMBEDDING_MODEL, save_path=FAISS_INDEX_PATH)

    llm = setup_llm(LLM_MODEL)

    retriever = vector_store.as_retriever(search_kwargs={"k": 4})
    rag_chain = setup_rag_chain(retriever, llm)

    sample_queries = [
        "10-year-old male, brain surgery in Mumbai, 1-year-old insurance policy",
        "46-year-old male, knee replacement surgery in Pune, 3-month-old insurance policy, what is the waiting period?",
        "Is dental treatment covered for a 30-year-old under policy BAJHLIP23020V012223?"
    ]

    for i, query in enumerate(sample_queries):
        print(f"\n--- Running Sample Query {i+1} ---")
        result = process_insurance_query(query, rag_chain)
        
        print("\nStructured Response:")
        print(json.dumps(result.model_dump(), indent=4))
        print("-" * 50)