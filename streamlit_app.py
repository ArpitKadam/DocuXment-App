import streamlit as st
import os
import time
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

# --- Core LangChain Imports ---
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.output_parsers import StrOutputParser # Replaces Pydantic
from langchain_pinecone import PineconeVectorStore
from langchain_nvidia import NVIDIAEmbeddings

# --- Vector Store Imports ---
from pinecone import Pinecone, ServerlessSpec

# --- Load Environment Variables ---
load_dotenv()
os.environ['LANGCHAIN_API_KEY'] = os.getenv("LANGCHAIN_API_KEY", "")
os.environ['LANGCHAIN_TRACING_V2'] = "true"
os.environ['LANGCHAIN_PROJECT'] = "RAG-Insurance-Production-Streamlit"
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = "insurance-policies-with-nvidia-embeddings"

# --- UI Configuration ---
st.set_page_config(page_title="Insurance Policy Q&A", layout="wide")
st.title("📄 Insurance Policy Q&A Assistant")

# --- Database Functions (formerly db_utils.py) ---
DB_NAME = "claims_log.db"

def setup_database():
    """Create the database and the 'logs' table with the new schema."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL,
            user_query TEXT NOT NULL,
            llm_response TEXT,
            time_taken_sec REAL,
            model_used TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_request(query, response_text, time_taken, model_name):
    """Log the request details to the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO logs (timestamp, user_query, llm_response, time_taken_sec, model_used)
        VALUES (?, ?, ?, ?, ?)
    """, (
        datetime.now(),
        query,
        response_text,
        time_taken,
        model_name
    ))
    conn.commit()
    conn.close()

# --- LLM and Model Configuration ---
OLLAMA_LLM_MODELS = ["gemma3n:e2b", "gemma3n:e4b"]
EMBEDDING_MODEL_NAME = "nvidia/nv-embed-v1"
EMBEDDING_DIMENSION = 4096

def get_llm(model_name, temperature):
    """Initializes the Ollama LLM."""
    return ChatOllama(model=model_name, temperature=temperature)

# --- RAG Chain Creation (formerly rag_logic.py) ---
def create_rag_chain(vector_store):
    """Creates and returns a RAG chain that outputs a simple string."""
    try:
        llm = get_llm(st.session_state.selected_llm, st.session_state.selected_temp)
        
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are an expert insurance policy assistant. Based on the provided context, answer the user's question directly and concisely.
            If the context contains the answer, provide it clearly. If not, state that the information is not available in the provided documents."""),
            ("human", "Context:\n---\n{context}\n---\n\nQuestion: {input}")
        ])

        document_chain = create_stuff_documents_chain(
            llm=llm,
            prompt=prompt_template,
            output_parser=StrOutputParser()
        )
        
        retriever = vector_store.as_retriever(search_kwargs={"k": 5})
        retrieval_chain = create_retrieval_chain(retriever, document_chain)
        return retrieval_chain
    except Exception as e:
        st.error(f"Error creating RAG chain: {e}")
        return None

# --- SQLite Database Setup ---
setup_database()

# --- Sidebar Configuration ---
with st.sidebar:
    st.header("⚙️ Configuration")
    st.subheader("Model Settings")
    st.session_state.selected_llm = st.selectbox("Select LLM Model", options=OLLAMA_LLM_MODELS, index=0)
    st.session_state.selected_temp = st.slider("Temperature", 0.0, 1.0, 0.1, 0.1)

    st.subheader("Data Management")
    if st.button("Upload New Documents"):
        # ... (Upload logic remains the same)
        with st.status("Processing and uploading new documents...", expanded=True) as status:
            if not os.path.exists("pdfs") or not os.listdir("pdfs"):
                status.update(label="Error: 'pdfs' directory is missing or empty.", state="error")
            else:
                try:
                    status.write("Loading PDF files...")
                    loader = PyPDFDirectoryLoader("pdfs")
                    docs = loader.load()
                    status.write("Splitting text into chunks...")
                    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                    chunks = text_splitter.split_documents(docs)
                    status.write("Connecting to embeddings model...")
                    embeddings = NVIDIAEmbeddings(model=EMBEDDING_MODEL_NAME)
                    status.write("Adding new documents to Pinecone index...")
                    PineconeVectorStore.from_documents(chunks, embeddings, index_name=PINECONE_INDEX_NAME)
                    status.update(label="New documents uploaded successfully!", state="complete")
                    st.success("Upload complete! You can now query the new documents.")
                except Exception as e:
                    status.update(label=f"An error occurred: {e}", state="error")

# --- Session State Initialization ---
if 'last_run' not in st.session_state:
    st.session_state.last_run = None

# --- Main Application Logic ---
vector_db = None
if not PINECONE_API_KEY:
    st.error("PINECONE_API_KEY not found.")
else:
    try:
        pinecone = Pinecone(api_key=PINECONE_API_KEY)
        embeddings = NVIDIAEmbeddings(model=EMBEDDING_MODEL_NAME)

        if PINECONE_INDEX_NAME not in pinecone.list_indexes().names():
            st.warning(f"Pinecone index '{PINECONE_INDEX_NAME}' not found. Please add PDFs and click below to create it.")
            if st.button("Create Index and Initial Upload"):
                with st.status("Processing documents for the first time...", expanded=True) as status:
                    loader = PyPDFDirectoryLoader("pdfs")
                    docs = loader.load()
                    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                    chunks = text_splitter.split_documents(docs)
                    status.update(label="Creating Pinecone index...")
                    pinecone.create_index(
                    name=PINECONE_INDEX_NAME, dimension=EMBEDDING_DIMENSION, metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region="us-east-1")
                    )
                    status.update(label="Uploading documents to Pinecone...")
                    PineconeVectorStore.from_documents(chunks, embeddings, index_name=PINECONE_INDEX_NAME)
                    status.update(label="Upload complete!", state="complete")
                    st.rerun()
        else:
            vector_db = PineconeVectorStore.from_existing_index(PINECONE_INDEX_NAME, embeddings)
    except Exception as e:
        st.error(f"Failed to initialize Pinecone: {e}")

if vector_db:
    st.success(f"Connected to Pinecone index '{PINECONE_INDEX_NAME}'. Ready for questions.")
    prompt_text = st.text_input(
        "Enter your query:",
        placeholder="e.g., What is the waiting period for cataract surgery?"
    )

    if st.button("Submit Query") and prompt_text:
        rag_chain = create_rag_chain(vector_db)
        if rag_chain:
            with st.spinner("Analyzing your query... 🕵️‍♂️"):
                try:
                    start_time = time.time()
                    response = rag_chain.invoke({"input": prompt_text})
                    end_time = time.time()
                    
                    time_taken = end_time - start_time
                    answer_text = response.get("answer", "No answer found.")

                    log_request(prompt_text, answer_text, time_taken, st.session_state.selected_llm)
                    
                    st.session_state.last_run = {
                        "query": prompt_text, 
                        "response": response,
                        "time_taken": time_taken
                    }
                except Exception as e:
                    st.error(f"An error occurred: {e}")
                    st.session_state.last_run = None

if st.session_state.last_run:
    st.subheader("Analysis Result")
    
    answer = st.session_state.last_run["response"].get("answer")
    time_taken = st.session_state.last_run["time_taken"]

    st.info(f"**Answer:**\n{answer}")
    st.caption(f"Time taken: {time_taken:.2f} seconds")

    with st.expander("View Source Document Chunks"):
        context = st.session_state.last_run["response"].get("context", [])
        if context:
            for doc in context:
                st.markdown("---")
                st.write(f"**Source:** {doc.metadata.get('source', 'Unknown')} | **Page:** {doc.metadata.get('page', 'Unknown')}")
                st.write(doc.page_content)
        else:
            st.write("No source documents were retrieved.")