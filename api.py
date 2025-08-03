import os
import requests
import tempfile
import time
import traceback
import asyncio
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Union, List, Optional

# LangChain components
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.retrievers import ContextualCompressionRetriever
from langchain_cohere import CohereRerank # For the re-ranking step

# Separated Logic
from rag_logic import create_rag_chain, NVIDIA_LLM_MODEL
from db_utils import setup_database, log_request

# --- Initial Setup ---
load_dotenv()
setup_database()

# --- API Configuration ---
app = FastAPI(title="HackRx 6.0 Insurance Analysis API")
auth_scheme = HTTPBearer()
HACKRX_API_KEY = os.getenv("HACKRX_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "insurance-policies-with-nvidia-embeddings")
COHERE_API_KEY = os.getenv("COHERE_API_KEY") # Needed for the re-ranker

def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(auth_scheme)):
    if not HACKRX_API_KEY or credentials.credentials != HACKRX_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return credentials.credentials

# --- API Models ---
class HackRxRequest(BaseModel):
    documents: Optional[Union[str, List[str]]] = None
    questions: List[str]

class HackRxResponse(BaseModel):
    answers: List[str]

# --- Global Models & Cache ---
embeddings = NVIDIAEmbeddings(model="nvidia/nv-embed-v1")
DOCUMENT_CACHE = {}

def get_retriever(request_documents=None):
    """
    Gets the appropriate retriever. Uses a persistent Pinecone index by default,
    or a cached/on-the-fly FAISS index if documents are provided in the request.
    Also wraps the retriever with a Cohere Re-ranker for improved accuracy.
    """
    base_retriever = None
    if request_documents:
        # On-the-fly logic with caching
        doc_urls = request_documents if isinstance(request_documents, list) else [request_documents]
        cache_key = tuple(sorted(doc_urls))
        
        if cache_key in DOCUMENT_CACHE:
            print("Cache hit! Using existing FAISS index.")
            vector_store = DOCUMENT_CACHE[cache_key]
        else:
            print("Cache miss. Processing new documents.")
            # --- KEY FIX: Save the downloaded file to disk before loading ---
            with tempfile.TemporaryDirectory() as temp_dir:
                loaded_docs = []
                for i, url in enumerate(doc_urls):
                    # Download the file
                    response = requests.get(url)
                    response.raise_for_status()
                    
                    # Save it to a temporary path
                    file_path = os.path.join(temp_dir, f"doc_{i}.pdf")
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    
                    # Now load it from the path
                    loader = PyPDFLoader(file_path)
                    loaded_docs.extend(loader.load())

                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
                chunks = text_splitter.split_documents(loaded_docs)
                vector_store = FAISS.from_documents(chunks, embeddings)
                DOCUMENT_CACHE[cache_key] = vector_store
        base_retriever = vector_store.as_retriever(search_kwargs={"k": 10})
    else:
        # Persistent Pinecone logic
        vector_store = PineconeVectorStore.from_existing_index(index_name=PINECONE_INDEX_NAME, embedding=embeddings)
        base_retriever = vector_store.as_retriever(search_kwargs={"k": 10})
    
    # --- ACCURACY ENHANCEMENT: Add a Re-ranker ---
    compressor = CohereRerank(cohere_api_key=COHERE_API_KEY, top_n=3, model="rerank-v3.5",)
    compression_retriever = ContextualCompressionRetriever(base_compressor=compressor, base_retriever=base_retriever)
    return compression_retriever

# --- API Endpoint ---
@app.post("/api/v1/hackrx/run", response_model=HackRxResponse)
async def process_claims(request: HackRxRequest, api_key: str = Depends(verify_api_key)):
    try:
        retriever = get_retriever(request.documents)
        rag_chain = create_rag_chain(retriever)
        if not rag_chain:
            raise HTTPException(status_code=500, detail="Failed to create RAG chain.")

        doc_links = request.documents if isinstance(request.documents, list) else [request.documents] if request.documents else []

        # --- SPEED ENHANCEMENT: Process questions in parallel ---
        async def get_answer(question):
            start_time = time.time()
            result = await rag_chain.ainvoke({"input": question})
            answer_text = result.get("answer", "Error: No answer generated.").strip()
            end_time = time.time()
            log_request(doc_links, question, answer_text, end_time - start_time, NVIDIA_LLM_MODEL)
            return answer_text

        tasks = [get_answer(q) for q in request.questions]
        answers = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check for exceptions that might have occurred during parallel execution
        processed_answers = [str(ans) if not isinstance(ans, Exception) else f"Error: {str(ans)}" for ans in answers]

        return HackRxResponse(answers=processed_answers)

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred: {e}")