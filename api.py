import os
import requests
import tempfile
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Union, List
import traceback

# LangChain components for document processing
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_nvidia import NVIDIAEmbeddings

# Import your separated logic
from rag_logic import create_rag_chain, InsuranceAnalysis
from db_utils import setup_database, log_claim

# --- Initial Setup ---
load_dotenv()
setup_database()

# --- API Configuration ---
app = FastAPI(
    title="HackRx 6.0 Insurance Analysis API",
    description="Processes insurance documents and questions to provide structured analysis."
)

# --- Authentication ---
auth_scheme = HTTPBearer()
HACKRX_API_KEY = os.getenv("HACKRX_API_KEY")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(auth_scheme)):
    """Verify the bearer token against the secret key."""
    if not HACKRX_API_KEY or credentials.credentials != HACKRX_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return credentials.credentials

# --- API Request and Response Models ---
class HackRxRequest(BaseModel):
    ## --- FIX 1: Allow 'documents' to be a single string OR a list of strings ---
    documents: Union[str, List[str]]
    questions: List[str]

class HackRxResponse(BaseModel):
    ## --- FIX 2: The response 'answers' field must be a list of simple strings ---
    answers: List[str]

# --- Global Models (initialized once) ---
if not NVIDIA_API_KEY:
    raise ValueError("NVIDIA_API_KEY not found in environment variables.")
# The model name comes from your NVIDIA NIM example
embeddings = NVIDIAEmbeddings(model="nvidia/nv-embed-v1", nvidia_api_key=NVIDIA_API_KEY)

# --- API Endpoint ---
@app.post("/api/v1/hackrx/run", response_model=HackRxResponse)
async def process_claims(request: HackRxRequest, api_key: str = Depends(verify_api_key)):
    """
    This endpoint processes a list of documents and questions and returns structured answers.
    """
    all_answers_str = []

    ## --- FIX 1 (Logic): Normalize the 'documents' input into a list ---
    document_urls = []
    if isinstance(request.documents, str):
        document_urls.append(request.documents)
    else:
        document_urls = request.documents

    with tempfile.TemporaryDirectory() as temp_dir:
        # 1. Download and load all documents
        loaded_docs = []
        for i, doc_url in enumerate(document_urls):
            try:
                response = requests.get(doc_url, timeout=20)
                response.raise_for_status()
                
                file_path = os.path.join(temp_dir, f"doc_{i}.pdf")
                with open(file_path, "wb") as f:
                    f.write(response.content)
                
                loader = PyPDFLoader(file_path)
                docs = loader.load()
                loaded_docs.extend(docs)
            except requests.RequestException as e:
                raise HTTPException(status_code=400, detail=f"Failed to download document from {doc_url}: {e}")

        if not loaded_docs:
            raise HTTPException(status_code=400, detail="No valid documents could be processed.")

        # 2. Create a temporary vector store for this request
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(loaded_docs)
        vector_store = FAISS.from_documents(chunks, embeddings)

        # 3. Create the RAG chain
        rag_chain = create_rag_chain(vector_store)
        if not rag_chain:
            raise HTTPException(status_code=500, detail="Failed to create RAG processing chain.")

        # 4. Process each question
        for question in request.questions:
            # --- KEY CHANGE: Capture and print the specific exception ---
            try:
                result = rag_chain.invoke({"input": question})
                answer_obj = result.get("answer")
                
                if isinstance(answer_obj, InsuranceAnalysis):
                    all_answers_str.append(answer_obj.Justification)
                    log_claim(question, answer_obj, "google/gemma-3n-e2b-it")
                else:
                    all_answers_str.append("Error: Failed to generate a valid analysis object.")
            except Exception as e:
                # This will now print the detailed error to your terminal
                print("--- ERROR DURING RAG INVOCATION ---")
                traceback.print_exc() 
                print("--- END OF ERROR ---")
                all_answers_str.append(f"Error: An exception occurred: {str(e)}")

    return HackRxResponse(answers=all_answers_str)