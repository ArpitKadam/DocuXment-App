import streamlit as st
import os
from dotenv import load_dotenv

# --- Core LangChain and Pydantic Imports ---
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from langchain_pinecone import PineconeVectorStore


# --- Database & Vector Store Imports ---
from pinecone import Pinecone, ServerlessSpec
from db_utils import setup_database, log_claim

# --- Load Environment Variables ---
load_dotenv()
os.environ['LANGCHAIN_API_KEY'] = os.getenv("LANGCHAIN_API_KEY", "")
os.environ['LANGCHAIN_TRACING_V2'] = "true"
os.environ['LANGCHAIN_PROJECT'] = "RAG-Insurance-Production"
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = "insurance-policies"

# --- UI Configuration ---
st.set_page_config(page_title="Insurance Policy Q&A", layout="wide")
st.title("📄 Insurance Policy Q&A Assistant")

# --- Pydantic Data Model ---
class InsuranceAnalysis(BaseModel):
    """Structured data model for the insurance claim analysis."""
    Decision: str = Field(description="The final decision: 'Approved', 'Rejected', or 'Needs More Info'")
    Amount: str = Field(description="The claimable amount as a string (e.g., '50000', 'Up to 2% of Sum Insured', or 'N/A')")
    Justification: str = Field(description="A detailed justification for the decision, citing specific policy clauses or sections from the context provided.")
    Confidence_Score: float = Field(description="A score from 0.0 to 1.0 indicating the model's confidence in its decision.")
    Missing_Info: list[str] = Field(default=[], description="A list of specific questions or information needed if the decision is 'Needs More Info'.")

# --- LLM and Model Configuration ---
OLLAMA_LLM_MODELS = ["gemma3n:e4b", "gemma3n:e2b"] # Updated to common Ollama model names
EMBEDDING_MODEL_NAME = "mxbai-embed-large:latest"
EMBEDDING_DIMENSION = 1024  # Dimension for mxbai-embed-large

def get_llm(model_name, temperature, max_tokens):
    """Initializes the Ollama LLM."""
    return ChatOllama(model=model_name, temperature=temperature) # Max tokens often handled by model defaults

# --- SQLite Database Setup ---
# KEY CHANGE: Simplified setup. It's safe to call this on every run.
setup_database()

# --- Sidebar Configuration ---
with st.sidebar:
    st.header("⚙️ Configuration")
    st.subheader("Model Settings")
    selected_llm = st.selectbox("Select LLM Model", options=OLLAMA_LLM_MODELS, index=0)
    selected_temp = st.slider("Temperature", 0.0, 1.0, 0.1, 0.1)
    selected_tokens = st.slider("Max Tokens", 100, 4096, 1500, 100) # Optional: Ollama often manages this well

# --- Session State Initialization ---
# KEY CHANGE: Using a dictionary to store last run details to prevent inconsistencies.
if 'last_run' not in st.session_state:
    st.session_state.last_run = None

# --- Main Application Logic ---
vector_db = None

if not PINECONE_API_KEY:
    st.error("PINECONE_API_KEY not found in environment variables. Please add it to your .env file.")
else:
    try:
        pinecone = Pinecone(api_key=PINECONE_API_KEY)
        embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL_NAME)

        if PINECONE_INDEX_NAME not in pinecone.list_indexes().names():
            st.warning(f"Pinecone index '{PINECONE_INDEX_NAME}' not found. Please add PDFs and click below to create it.")
            if st.button("Create Index and Upload Documents"):
                with st.status("Processing documents...", expanded=True) as status:
                    # ... Document loading and chunking logic ...
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
        placeholder="e.g., 46-year-old male, knee surgery in Pune, 3-month-old insurance policy"
    )

    if st.button("Submit Query") and prompt_text:
        llm = get_llm(model_name=selected_llm, temperature=selected_temp, max_tokens=None)
        pydantic_parser = PydanticOutputParser(pydantic_object=InsuranceAnalysis)
        
        # KEY CHANGE: Enhanced prompt to encourage more detailed reasoning.
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are a world-class insurance policy analysis expert. Your task is to act as a claims adjudicator.
            Based on the provided policy document excerpts (context) and the user's query, you must make a decision.
            First, reason step-by-step about the user query and the context. Then, provide your final answer in the requested JSON format.
            Your entire response must be a JSON object that strictly follows the provided format. Do not add any text outside of the JSON structure.
            {format_instructions}
            """),
            ("human", "Policy Documents Context:\n---\n{context}\n---\n\nUser Query: {input}")
        ]).partial(format_instructions=pydantic_parser.get_format_instructions())

        document_chain = create_stuff_documents_chain(llm, prompt_template, output_parser=pydantic_parser)
        retriever = vector_db.as_retriever(search_kwargs={"k": 7})
        retrieval_chain = create_retrieval_chain(retriever, document_chain)

        with st.spinner("Analyzing your query... 🕵️‍♂️"):
            try:
                response = retrieval_chain.invoke({"input": prompt_text})
                # Store both query and response together in session state
                st.session_state.last_run = {"query": prompt_text, "response": response}
            except Exception as e:
                st.error(f"An error occurred while processing your request: {e}")
                st.session_state.last_run = None

if st.session_state.last_run:
    query = st.session_state.last_run["query"]
    response = st.session_state.last_run["response"]
    
    st.subheader("Analysis Result")
    parsed_result = response.get("answer")

    if isinstance(parsed_result, InsuranceAnalysis):
        try:
            # Log the successful result using the query stored in session state
            log_claim(query, parsed_result, selected_llm)
            st.toast("Analysis logged to database!")
        except Exception as e:
            st.error(f"Failed to log to database: {e}")

        # Display logic
        col1, col2 = st.columns(2)
        col1.metric("Decision", parsed_result.Decision)
        col2.metric("Amount", str(parsed_result.Amount))

        justification = parsed_result.Justification
        if parsed_result.Missing_Info:
            justification += "\n\n**Information Needed:**\n" + "\n".join(f"- {info}" for info in parsed_result.Missing_Info)
        st.info(f"**Justification:** {justification}")

    with st.expander("View Source Document Chunks"):
        if response.get("context"):
            for doc in response["context"]:
                st.markdown("---")
                st.write(f"**Source:** {doc.metadata.get('source', 'Unknown')} | **Page:** {doc.metadata.get('page', 'Unknown')}")
                st.write(doc.page_content)
        else:
            st.write("No source documents were retrieved for this query.")