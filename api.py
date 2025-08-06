import os
import requests
import tempfile
import time
import asyncio
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Union, List, Optional
from utils.logger import logger
import hashlib

# LangChain components
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings, NVIDIARerank
from langchain_pinecone import PineconeVectorStore
from langchain.retrievers import ContextualCompressionRetriever

# Separated Logic
from rag_logic import create_rag_chain, NVIDIA_LLM_MODEL
from utils.db_utils import setup_database, log_request

# --- Initial Setup ---
load_dotenv()
setup_database()

# --- API Configuration ---
app = FastAPI(title="HackRx 6.0 Insurance Analysis API")
auth_scheme = HTTPBearer()
HACKRX_API_KEY = os.getenv("HACKRX_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "insurance-policies-with-nvidia-embeddings")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")

def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(auth_scheme)):
    logger.debug("Verifying API key...")
    if not HACKRX_API_KEY or credentials.credentials != HACKRX_API_KEY:
        logger.warning("API key verification FAILED.")
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    logger.debug("API key verification successful.")
    return credentials.credentials

# --- API Models ---
class HackRxRequest(BaseModel):
    documents: Optional[Union[str, List[str]]] = None
    questions: List[str]

class HackRxResponse(BaseModel):
    answers: List[str]

# --- Global Models & Cache ---
embeddings = NVIDIAEmbeddings(model="nvidia/nv-embed-v1")
FAISS_DIR = "faiss_indexes"
FAISS_CACHE = {} # Cache for pre-loaded local indexes

def load_local_faiss_indexes():
    """
    Loads all pre-generated FAISS indexes from the local directory into memory.
    The key for the cache is the hash of the original URL.
    """
    if not os.path.exists(FAISS_DIR):
        logger.warning(f"'{FAISS_DIR}' directory not found. No local indexes will be pre-loaded.")
        return
    
    logger.info("Pre-loading local FAISS indexes into memory...")
    # Read the links file to map hashes back to URLs
    try:
        with open("links.txt", 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        hash_to_url_map = {hashlib.sha256(url.encode('utf-8')).hexdigest(): url for url in urls}

        for index_hash in os.listdir(FAISS_DIR):
            if index_hash in hash_to_url_map:
                try:
                    index_path = os.path.join(FAISS_DIR, index_hash)
                    vector_store = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
                    FAISS_CACHE[index_hash] = vector_store
                    original_url = hash_to_url_map[index_hash]
                    logger.info(f" -> Successfully loaded index '{index_hash}' for URL: {original_url}...")
                except Exception as e:
                    logger.error(f" -> FAILED to load index from {index_path}. Error: {e}")
    except FileNotFoundError:
        logger.warning("links.txt not found. Cannot map hashes to URLs for pre-loading.")

# --- Load indexes on API startup ---
load_local_faiss_indexes()

def get_retriever(request_documents: Optional[Union[str, List[str]]] = None):
    """
    Gets the appropriate retriever with a unified caching strategy.
    1. Checks for a pre-loaded/cached local FAISS index.
    2. Processes and caches new documents on-the-fly if not found.
    3. Falls back to a persistent Pinecone index if no documents are specified.
    """
    base_retriever = None

    if request_documents:
        doc_urls = request_documents if isinstance(request_documents, list) else [request_documents]
        url_string = "".join(sorted(doc_urls))
        url_hash = hashlib.sha256(url_string.encode('utf-8')).hexdigest()

        # Check the unified cache first
        if url_hash in FAISS_CACHE:
            logger.info(f"Cache hit for hash {url_hash}... Using in-memory FAISS index.")
            vector_store = FAISS_CACHE[url_hash]
        else:
            # If not in cache, process it on-the-fly and add it to the cache
            logger.info(f"Cache miss for hash {url_hash}... Processing new document on-the-fly.")
            with tempfile.TemporaryDirectory() as temp_dir:
                loaded_docs = []
                for i, url in enumerate(doc_urls):
                    response = requests.get(url, timeout=30)
                    response.raise_for_status()
                    file_path = os.path.join(temp_dir, f"doc_{i}.pdf")
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    loader = PyPDFLoader(file_path)
                    loaded_docs.extend(loader.load())
                
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
                chunks = text_splitter.split_documents(loaded_docs)
                vector_store = FAISS.from_documents(chunks, embeddings)
                FAISS_CACHE[url_hash] = vector_store # Add the new index to the cache
                logger.info(f"New index for hash {url_hash[:10]}... created and cached.")
        
        base_retriever = vector_store.as_retriever(search_kwargs={"k": 10})
    else:
        # Fallback to Pinecone if no documents are in the request
        logger.info("No documents in request. Using persistent Pinecone index.")
        vector_store = PineconeVectorStore.from_existing_index(
            index_name=PINECONE_INDEX_NAME,
            embedding=embeddings
        )
        base_retriever = vector_store.as_retriever(search_kwargs={"k": 10})
        logger.info(f"Connected to Pinecone index '{PINECONE_INDEX_NAME}'.")
    
    logger.debug("Initializing NVIDIARerank for compression.")
    compressor = NVIDIARerank(model="nvidia/llama-3.2-nv-rerankqa-1b-v2", api_key=NVIDIA_API_KEY)
    compression_retriever = ContextualCompressionRetriever(base_compressor=compressor, base_retriever=base_retriever)
    logger.info("Retriever setup complete with re-ranker.")
    return compression_retriever

# --- API Endpoint ---
@app.post("/api/v1/hackrx/run", response_model=HackRxResponse)
async def process_claims(request: HackRxRequest, api_key: str = Depends(verify_api_key)):
    logger.info(f"--- Received request in /api/v1/hackrx/run for {len(request.questions)} questions ---")
    logger.debug(f"Request body: {request.model_dump_json(indent=2)}")
    try:
        logger.debug("Getting retriever...")
        retriever = get_retriever(request.documents)
        logger.debug("Retriever obtained.")
        
        logger.debug("Creating RAG chain...")
        rag_chain = create_rag_chain(retriever)
        if not rag_chain:
            logger.error("RAG chain creation failed.")
            raise HTTPException(status_code=500, detail="Failed to create RAG chain.")
        logger.info("RAG chain created successfully.")

        doc_links = request.documents if isinstance(request.documents, list) else [request.documents] if request.documents else []

        semaphore = asyncio.Semaphore(4)

        # --- SPEED ENHANCEMENT: Process questions in parallel ---
        async def get_answer(question):
            async with semaphore:
                logger.info(f"Processing question: '{question}'")
                start_time = time.time()
                result = await rag_chain.ainvoke({"input": question})
                logger.debug(f"Raw result from RAG chain for '{question}': {result}")
                answer_text = result.get("answer", "Error: No answer generated.").strip()
                end_time = time.time()
                logger.info(f"Final answer for '{question}' generated in {end_time - start_time:.2f}s")
                log_request(doc_links, question, answer_text, end_time - start_time, NVIDIA_LLM_MODEL)
                return answer_text

        logger.debug(f"Creating {len(request.questions)} parallel tasks for questions.")
        tasks = [get_answer(q) for q in request.questions]
        answers = await asyncio.gather(*tasks, return_exceptions=True)
        logger.debug(f"Raw answers from asyncio.gather: {answers}")
        
        # Check for exceptions that might have occurred during parallel execution
        processed_answers = [str(ans) if not isinstance(ans, Exception) else f"Error: {str(ans)}" for ans in answers]
        logger.debug(f"Processed answers: {processed_answers}")

        logger.info("Returning final response.")
        return HackRxResponse(answers=processed_answers)

    except Exception as e:
        logger.error(f"An unexpected server error occurred in process_claims", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred: {e}")