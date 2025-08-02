import os
import requests
import tempfile
import time
import traceback
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Union, List, Optional
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from rag_logic import create_rag_chain, NVIDIA_LLM_MODEL
from db_utils import setup_database, log_request
load_dotenv()
setup_database()

app = FastAPI(
    title="HackRx 6.0 Insurance Analysis API",
    description="Processes insurance documents and questions to provide structured analysis."
)

auth_scheme = HTTPBearer()
HACKRX_API_KEY = os.getenv("HACKRX_API_KEY")
PINECONE_INDEX_NAME = "insurance-policies-with-nvidia-embeddings"

def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(auth_scheme)):
    if not HACKRX_API_KEY or credentials.credentials != HACKRX_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return credentials.credentials

# --- API Request and Response Models ---
class HackRxRequest(BaseModel):
    documents: Optional[Union[str, List[str]]] = None
    questions: List[str]

class HackRxResponse(BaseModel):
    answers: List[str]

embeddings = NVIDIAEmbeddings(model="nvidia/nv-embed-v1", nvidia_api_key=os.getenv("NVIDIA_API_KEY"))

# --- API Endpoint ---
@app.post("/api/v1/hackrx/run", response_model=HackRxResponse)
async def process_claims(request: HackRxRequest, api_key: str = Depends(verify_api_key)):
    vector_store = None
    
    if request.documents:
        # If documents are provided, process them on-the-fly with FAISS
        print("Processing documents provided in the request...")
        document_urls = request.documents if isinstance(request.documents, list) else [request.documents]
        with tempfile.TemporaryDirectory() as temp_dir:
            loaded_docs = []
            for i, doc_url in enumerate(document_urls):
                try:
                    response = requests.get(doc_url)
                    response.raise_for_status()
                    file_path = os.path.join(temp_dir, f"doc_{i}.pdf")
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    loader = PyPDFLoader(file_path)
                    loaded_docs.extend(loader.load())
                except requests.RequestException as e:
                    raise HTTPException(status_code=400, detail=f"Failed to download document from {doc_url}: {e}")
            
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            chunks = text_splitter.split_documents(loaded_docs)
            vector_store = FAISS.from_documents(chunks, embeddings)
    else:
        from langchain_pinecone import PineconeVectorStore
        print("No documents provided. Using persistent Pinecone index.")
        vector_store = PineconeVectorStore.from_existing_index(
            index_name=PINECONE_INDEX_NAME,
            embedding=embeddings
        )

    if not vector_store:
        raise HTTPException(status_code=500, detail="Failed to initialize a vector store.")
        
    rag_chain = create_rag_chain(vector_store)
    if not rag_chain:
        raise HTTPException(status_code=500, detail="Failed to create RAG processing chain.")

    all_answers_str = []
    for question in request.questions:
        try:
            start_time = time.time()
            
            result = rag_chain.invoke({"input": question})
            answer_text = result.get("answer", "Error: No answer was generated.")
            
            end_time = time.time()
            time_taken = end_time - start_time
            
            all_answers_str.append(answer_text)
            
            log_request(question, answer_text, time_taken, NVIDIA_LLM_MODEL)
            
        except Exception as e:
            traceback.print_exc()
            error_msg = f"Error: An exception occurred: {str(e)}"
            all_answers_str.append(error_msg)
            log_request(question, error_msg, 0, NVIDIA_LLM_MODEL)

    return HackRxResponse(answers=all_answers_str)