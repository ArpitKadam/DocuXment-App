import os
import requests
import tempfile
import time
import asyncio
from typing import Union, List, Optional
from urllib.parse import urlparse
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_core.documents import Document
import pytesseract
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings, NVIDIARerank
from langchain_pinecone import PineconeVectorStore
from langchain.retrievers import ContextualCompressionRetriever

try:
    from langchain_community.document_loaders import Docx2txtLoader
    from langchain_community.document_loaders import UnstructuredPowerPointLoader
    from langchain_community.document_loaders import UnstructuredExcelLoader
    from langchain_community.document_loaders import UnstructuredImageLoader
    from langchain_community.document_loaders import WebBaseLoader
    ADVANCED_LOADERS_AVAILABLE = True
except ImportError:
    ADVANCED_LOADERS_AVAILABLE = False

# Local modules --------------------------------------------------------------
from utils.logger import (
    logger,
    log_request
)
from rag_logic import create_rag_chain, NVIDIA_LLM_MODEL, query_cache
from utils.db_utils import setup_database, log_request

load_dotenv()
setup_database()

# FastAPI init ---------------------------------------------------------------
from fastapi import FastAPI

app = FastAPI(
    title="DocuXment – Legal Document Simplifier",
    description=(
        "An AI-powered platform that uses Generative AI to demystify "
        "complex legal documents. It provides clear summaries, explains complicated "
        "clauses, and answers user questions in simple, accessible language — empowering "
        "users to make informed decisions and reduce legal and financial risks."
    ),
    version="1.0.0",
)

auth_scheme = HTTPBearer()
AUTH_TOKEN = os.getenv("AUTH_TOKEN")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "hackathon-pinecone-index")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")

# Embeddings & caches --------------------------------------------------------
embeddings = NVIDIAEmbeddings(model="nvidia/nv-embed-v1")
FAISS_CACHE = {}

# Performance monitor --------------------------------------------------------
class PerformanceMonitor:
    def __init__(self):
        self.response_times, self.accuracy_estimates = [], []
        self.cache_hits = self.total_requests = 0
        self.question_complexity_stats = {"simple": 0, "medium": 0, "complex": 0}

    def add_response_time(self, t):
        self.response_times.append(t)

    def add_accuracy_estimate(self, s):
        self.accuracy_estimates.append(s)

    def increment_cache_hits(self):
        self.cache_hits += 1

    def increment_requests(self):
        self.total_requests += 1

    def add_complexity_stat(self, lvl):
        self.question_complexity_stats[lvl] += 1

    def get_performance_metrics(self):
        return {
            "avg_response_time": sum(self.response_times) / len(self.response_times) if self.response_times else 0,
            "avg_accuracy_estimate": sum(self.accuracy_estimates) / len(self.accuracy_estimates) if self.accuracy_estimates else 0,
            "cache_hit_rate": self.cache_hits / max(self.total_requests, 1),
            "total_requests": self.total_requests,
            "model_used": NVIDIA_LLM_MODEL,
            "complexity_distribution": self.question_complexity_stats,
        }

perf_mon = PerformanceMonitor()

# Security ------------------------------------------------------------------
def verify_api_key(creds: HTTPAuthorizationCredentials = Security(auth_scheme)):
    if not AUTH_TOKEN or creds.credentials != AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return creds.credentials

# Pydantic models -----------------------------------------------------------
class Request(BaseModel):
    documents: Optional[Union[str, List[str]]] = None
    questions: List[str]

class Response(BaseModel):
    answers: List[str]

# Utility: multi-format loader ----------------------------------------------
def get_document_loader(file_path: str, url: str):
    ext = url.lower().split('.')[-1].split('?')[0]
    logger.info(f"Detected file type .{ext}")
    try:
        if ext == 'pdf':
            return PyPDFLoader(file_path)
        if ext in ['docx', 'doc'] and ADVANCED_LOADERS_AVAILABLE:
            return Docx2txtLoader(file_path)
        if ext in ['pptx', 'ppt'] and ADVANCED_LOADERS_AVAILABLE:
            return UnstructuredPowerPointLoader(file_path)
        if ext in ['xlsx', 'xls'] and ADVANCED_LOADERS_AVAILABLE:
            return UnstructuredExcelLoader(file_path)
        if ext in ['png', 'jpg', 'jpeg', 'gif', 'bmp'] and ADVANCED_LOADERS_AVAILABLE:
            return UnstructuredImageLoader(file_path, mode="elements")
        logger.warning(f"Unsupported format .{ext}")
        return PyPDFLoader(file_path)
    except Exception as e:
        logger.error(f"Loader error for .{ext}: {e}")
        return PyPDFLoader(file_path)

# Retriever -----------------------------------------------------------------
def get_retriever(request_docs: Optional[Union[str, List[str]]], complexity: str):

    if not request_docs:
        vec_store = PineconeVectorStore.from_existing_index(PINECONE_INDEX_NAME, embeddings)
        k = {"simple": 6, "medium": 8, "complex": 10}.get(complexity, 8)
        return vec_store.as_retriever(search_kwargs={"k": k})

    urls = request_docs if isinstance(request_docs, list) else [request_docs]

    all_docs = []
    with tempfile.TemporaryDirectory() as tmp:
        for u in urls:
            try:
                file_ext = Path(urlparse(u).path).suffix.lower()

                if file_ext in ['.pdf', '.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls', '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.txt']:
                    logger.info(f"Downloading file with extension '{file_ext}' from {u[:60]}…")
                    r = requests.get(u, timeout=30)
                    r.raise_for_status()
                        
                    filename = Path(urlparse(u).path).name
                    fp = os.path.join(tmp, filename)
                    with open(fp, 'wb') as f:
                        f.write(r.content)
                        
                    loader = get_document_loader(fp, u)
                    if loader:
                        all_docs.extend(loader.load())

                else:
                    logger.info(f"No file extension found. Loading as webpage: {u[:60]}…")
                    loader = WebBaseLoader(u)
                    all_docs.extend(loader.load())

            except Exception as e:
                logger.error(f"Failed to process URL {u[:70]}: {e}")

        if not all_docs:
            raise HTTPException(status_code=500, detail="Could not load or extract text from any of the provided documents.")
        
        ts = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=250)
        chunks = ts.split_documents(all_docs)
        vec_store = FAISS.from_documents(chunks, embeddings)
    
    k = {"simple": 6, "medium": 8, "complex": 10}.get(complexity, 8)
    ret = vec_store.as_retriever(search_kwargs={"k": k})

    if complexity == 'complex':
        comp = NVIDIARerank(model="nvidia/llama-3.2-nv-rerankqa-1b-v2", api_key=NVIDIA_API_KEY)
        return ContextualCompressionRetriever(base_compressor=comp, base_retriever=ret)
    
    return ret

# Complexity classifier (unchanged) ----------------------------------------
def classify_question_complexity(question):
    """Enhanced question complexity classification for competition optimization"""
    question_lower = question.lower()
    
    # High complexity indicators
    high_complexity_indicators = [
        "compare", "analyze", "relationship", "interaction", "simultaneously", 
        "while", "also request", "also ask", "both", "multiple", "various", "different",
        "scenario", "interaction", "contrast", "evaluate"
    ]
    
    # Medium complexity indicators  
    medium_complexity_indicators = [
        "covered", "eligible", "benefit", "claim", "waiting period", "exclusion",
        "limitation", "condition", "procedure", "process", "requirement"
    ]
    
    # Simple question indicators
    simple_indicators = ["what is", "define", "meaning", "who is", "when", "where"]
    
    # Calculate complexity score
    complexity_score = 0
    complexity_score += sum(1 for indicator in high_complexity_indicators if indicator in question_lower)
    complexity_score += len([char for char in question if char == "?"]) - 1  # Multiple questions
    complexity_score += question.count(",") // 2  # Multiple clauses
    complexity_score += question.count(" and ") + question.count(" or ")  # Logical operators
    
    # Length-based complexity
    if len(question.split()) > 25:
        complexity_score += 2
    elif len(question.split()) > 15:
        complexity_score += 1
    
    # Determine final complexity
    if complexity_score >= 4:
        return "complex"
    elif complexity_score >= 2 or any(indicator in question_lower for indicator in medium_complexity_indicators):
        return "medium"
    elif any(indicator in question_lower for indicator in simple_indicators):
        return "simple"
    else:
        return "medium"

# FastAPI endpoint ----------------------------------------------------------
@app.post("/api/v1/run", response_model=Response)
async def process_claims(req: Request, api_key: str = Depends(verify_api_key)):
    perf_mon.increment_requests()
    dominant = 'medium'
    retriever = get_retriever(req.documents, dominant)
    rag = create_rag_chain(retriever)
    sem = asyncio.Semaphore(3)

    async def _answer(q):
        async with sem:
            start = time.time()
            res = await rag.ainvoke({"input": q})
            dur = time.time() - start
            perf_mon.add_response_time(dur)
            log_request(req.documents, q, res.get("answer", "error"), dur, NVIDIA_LLM_MODEL)
            return res.get("answer", "error")

    answers = await asyncio.gather(*[_answer(q) for q in req.questions])
    return Response(answers=answers)

# Health --------------------------------------------------------------------
@app.get("/health")
def health():
    return {"metrics": perf_mon.get_performance_metrics()}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=False)