import os
import requests
import tempfile
import time
import traceback
import logging
import asyncio
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Union, List, Optional

# LangChain components
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings, NVIDIARerank
from langchain_pinecone import PineconeVectorStore
from langchain.retrievers import ContextualCompressionRetriever

# Separated Logic
from rag_logic import create_rag_chain, NVIDIA_LLM_MODEL
from db_utils import setup_database, log_request

# --- Initial Setup ---
load_dotenv()
setup_database()

# --- Logging Configuration ---
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Create a timestamped log file name for this specific run
log_filename = datetime.now().strftime("api_run_%Y-%m-%d_%H-%M-%S.log")
log_filepath = os.path.join(LOG_DIR, log_filename)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
    filename=log_filepath,
    filemode='w'  # Use 'w' to create a new file for each run
)
logger = logging.getLogger(__name__)
logger.info(f"Logging initialized. Log file will be saved to: {log_filepath}")

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
DOCUMENT_CACHE = {}

def get_retriever(request_documents=None):
    """
    Gets the appropriate retriever. Uses a persistent Pinecone index by default,
    or a cached/on-the-fly FAISS index if documents are provided in the request.
    Also wraps the retriever with a Nvidia Re-ranker for improved accuracy.
    """
    logger.info("--- In get_retriever ---")
    base_retriever = None
    if request_documents:
        logger.info("Documents provided in request. Using on-the-fly FAISS retriever.")
        # On-the-fly logic with caching
        doc_urls = request_documents if isinstance(request_documents, list) else [request_documents]
        cache_key = tuple(sorted(doc_urls))
        logger.debug(f"Document URLs: {doc_urls}")
        
        if cache_key in DOCUMENT_CACHE:
            logger.info("Cache hit! Using existing FAISS index.")
            vector_store = DOCUMENT_CACHE[cache_key]
        else:
            logger.info("Cache miss. Processing new documents.")
            with tempfile.TemporaryDirectory() as temp_dir:
                loaded_docs = []
                for i, url in enumerate(doc_urls):
                    logger.debug(f"Downloading document from {url}...")
                    # Download the file
                    response = requests.get(url)
                    response.raise_for_status()
                    
                    # Save it to a temporary path
                    file_path = os.path.join(temp_dir, f"doc_{i}.pdf")
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    
                    logger.debug(f"Loading PDF from temporary path: {file_path}")
                    loader = PyPDFLoader(file_path)
                    loaded_docs.extend(loader.load())

                logger.debug(f"Total pages loaded: {len(loaded_docs)}")
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
                chunks = text_splitter.split_documents(loaded_docs)
                logger.debug(f"Split documents into {len(chunks)} chunks.")
                logger.debug("Creating FAISS vector store from chunks...")
                vector_store = FAISS.from_documents(chunks, embeddings)

                # Check for GPU and move the index if available for performance
                try:
                    import faiss
                    if faiss.get_num_gpus() > 0:
                        logger.info(f"Found {faiss.get_num_gpus()} GPUs. Moving FAISS index to GPU 0.")
                        # Create a standard GPU resource object
                        res = faiss.StandardGpuResources()
                        # Clone the CPU index to the first GPU
                        gpu_index = faiss.index_cpu_to_gpu(res, 0, vector_store.index)
                        vector_store.index = gpu_index
                        logger.info("FAISS index successfully moved to GPU.")
                except ImportError:
                    logger.info("faiss-gpu package not found. Using CPU-based FAISS index.")
                except Exception as e:
                    logger.warning(f"An error occurred while trying to move FAISS index to GPU: {e}")

                DOCUMENT_CACHE[cache_key] = vector_store
                logger.info("FAISS vector store created and cached.")
        base_retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    else:
        logger.info("No documents in request. Using persistent Pinecone index.")
        # Persistent Pinecone logic
        vector_store = PineconeVectorStore.from_existing_index(index_name=PINECONE_INDEX_NAME, embedding=embeddings)
        base_retriever = vector_store.as_retriever(search_kwargs={"k": 5})
        logger.info(f"Connected to Pinecone index '{PINECONE_INDEX_NAME}'.")
    
    # --- ACCURACY ENHANCEMENT: Add a Re-ranker ---
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

        # --- SPEED ENHANCEMENT: Process questions in parallel ---
        async def get_answer(question):
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