# flask_app.py
import os
import time
import hashlib
import requests
from pathlib import Path
from urllib.parse import urlparse
from flask import Flask, request, render_template, flash, session, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# LangChain loaders/vectorstores
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, UnstructuredPowerPointLoader, UnstructuredExcelLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_pinecone import PineconeVectorStore
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings

# Local utilities
from utils.logger import logger
from utils.db_utils import setup_database, log_request
import rag_logic  # Reuse create_rag_chain and query_cache

load_dotenv()
setup_database()

# ----------------- Config -----------------
UPLOAD_FOLDER = "data"
ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "pptx", "ppt", "xlsx", "xls", "txt"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

FAISS_DIR = "faiss_indexes"
os.makedirs(FAISS_DIR, exist_ok=True)

# Embeddings setup
EMBEDDING_MODEL_NAME = "nvidia/nv-embed-v1"
embeddings = NVIDIAEmbeddings(model=EMBEDDING_MODEL_NAME)
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
API_KEY = os.getenv("HACKRX_API_KEY", "")

# Cache for FAISS indexes
FAISS_CACHE = {}

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.getenv("FLASK_SECRET", "devsecret")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 80 * 1024 * 1024  # 80MB

# ----------------- Preload FAISS -----------------
def preload_faiss():
    for name in os.listdir(FAISS_DIR):
        path = os.path.join(FAISS_DIR, name)
        try:
            FAISS_CACHE[name] = FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)
            logger.info(f"Loaded FAISS index {name}")
        except Exception as e:
            logger.error(f"Failed to load FAISS {name}: {e}")

preload_faiss()

# ----------------- Helpers -----------------
def allowed_file(filename):
    logger.info(f"Checking file extension for {filename}")
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_document_loader(file_path):
    ext = file_path.lower().split('.')[-1]
    if ext == "pdf":
        logger.info(f"Loading PDF {file_path}")
        return PyPDFLoader(file_path)
    if ext in ("docx", "doc"):
        logger.info(f"Loading DOCX {file_path}")
        return Docx2txtLoader(file_path)
    if ext in ("pptx", "ppt"):
        logger.info(f"Loading PPTX {file_path}")
        return UnstructuredPowerPointLoader(file_path)
    if ext in ("xlsx", "xls"):
        logger.info(f"Loading XLSX {file_path}")
        return UnstructuredExcelLoader(file_path)
    return PyPDFLoader(file_path)

def build_faiss_for_files(file_paths):
    all_docs = []
    for fp in file_paths:
        try:
            loader = get_document_loader(fp)
            logger.info(f"Loaded {loader} for {fp}")
            all_docs.extend(loader.load())
        except Exception as e:
            logger.error(f"Error loading {fp}: {e}")

    if not all_docs:
        return None, None

    ts = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=250)
    logger.info(f"Splitting {len(all_docs)} documents into chunks")
    chunks = ts.split_documents(all_docs)
    logger.info(f"Split into {len(chunks)} chunks")
    vec_store = FAISS.from_documents(chunks, embeddings)
    logger.info(f"Built FAISS index for {len(chunks)} chunks")

    url_hash = hashlib.sha256("".join(sorted(file_paths)).encode()).hexdigest()
    logger.info(f"URL hash: {url_hash}")
    outdir = os.path.join(FAISS_DIR, url_hash)
    os.makedirs(outdir, exist_ok=True)
    vec_store.save_local(outdir)
    logger.info(f"Saved FAISS index to {outdir}")
    FAISS_CACHE[url_hash] = FAISS.load_local(outdir, embeddings, allow_dangerous_deserialization=True)
    logger.info(f"Loaded FAISS index from {outdir}")
    return vec_store, url_hash

def build_faiss_for_urls(urls):
    url_hash = hashlib.sha256("".join(sorted(urls)).encode()).hexdigest()
    logger.info(f"URL hash: {url_hash}")
    if url_hash in FAISS_CACHE:
        logger.info(f"Using cached FAISS for URLs {urls}")
        return FAISS_CACHE[url_hash], url_hash

    saved_files = []
    for link in urls:
        try:
            response = requests.get(link, timeout=30)
            logger.info(f"Downloaded {link}")
            if response.status_code == 200:
                filename = os.path.basename(urlparse(link).path) or f"file_{hashlib.md5(link.encode()).hexdigest()}.dat"
                save_path = os.path.join(UPLOAD_FOLDER, filename)
                logger.info(f"Saving {filename} to {save_path}")
                with open(save_path, "wb") as f:
                    f.write(response.content)
                saved_files.append(save_path)
                logger.info(f"Saved {filename} to {save_path}")
                logger.info(f"Downloaded {filename} from {link}")
        except Exception as e:
            logger.error(f"Error downloading {link}: {e}")

    if saved_files:
        return build_faiss_for_files(saved_files)
    return None, None

# ----------------- Routes -----------------
@app.route("/", methods=["GET", "POST"])
def index():
    model_choices = [
        "qwen/qwen2.5-7b-instruct",
        "mistralai/mistral-small-3.1-24b-instruct-2503",
        "meta/llama-4-maverick-17b-128e-instruct",
        "meta/llama-4-scout-17b-16e-instruct",
        "nvidia/llama-3.3-nemotron-super-49b-v1",
        "mistralai/mistral-small-24b-instruct",
        "qwen/qwen2.5-coder-32b-instruct",
        "meta/llama-3.3-70b-instruct",
        "nvidia/llama-3.1-nemotron-70b-instruct",
        "mistralai/mistral-small-24b-instruct",
        "google/gemma-3n-e4b-it",
        "google/gemma-3n-e2b-it",
    ]
    answer, sources, query_text = None, [], ""
    selected_model = session.get("selected_model", model_choices[0])
    logger.info(f"Selected model: {selected_model}")
    selected_temp = float(session.get("selected_temp", 0.5))
    logger.info(f"Selected temperature: {selected_temp}")

    if request.method == "POST":
        selected_model = request.form.get("model") or selected_model
        session["selected_model"] = selected_model
        try:
            selected_temp = float(request.form.get("temperature", selected_temp))
        except ValueError:
            selected_temp = 0.5
        session["selected_temp"] = selected_temp

        query_text = request.form.get("question", "").strip()
        uploaded_files = request.files.getlist("documents")
        document_links = request.form.get("document_links", "").strip().splitlines()
        document_links = [link.strip() for link in document_links if link.strip()]

        retriever = None

        if uploaded_files and any(f.filename for f in uploaded_files if allowed_file(f.filename)):
            # Case 1: File upload → FAISS only
            saved_paths = []
            for file in uploaded_files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                    file.save(save_path)
                    saved_paths.append(save_path)
                    logger.info(f"Uploaded {filename}")
            if saved_paths:
                vec_store, _ = build_faiss_for_files(saved_paths)
                if vec_store:
                    retriever = vec_store.as_retriever(search_kwargs={"k": 5})

        elif document_links:
            # Case 3: URL(s) → Check FAISS → Download if missing
            vec_store, _ = build_faiss_for_urls(document_links)
            if vec_store:
                retriever = vec_store.as_retriever(search_kwargs={"k": 5})

        else:
            # Case 2: No upload + No link → Pinecone only
            try:
                logger.info("Initializing Pinecone")
                pinecone_store = PineconeVectorStore.from_existing_index(PINECONE_INDEX_NAME, embeddings)
                logger.info("Initialized Pinecone")
                retriever = pinecone_store.as_retriever(search_kwargs={"k": 5})
                logger.info("Created Pinecone retriever")
            except Exception as e:
                logger.error(f"Pinecone error: {e}")
                flash("Pinecone retriever not available", "danger")

        if not retriever:
            flash("No retriever available", "danger")
        else:
            rag_chain = rag_logic.create_rag_chain(
                retriever=retriever,
                model_name=selected_model,
                temperature=selected_temp
            )
            logger.info(f"Created RAG chain for {selected_model}")
            start = time.time()
            res = rag_chain.invoke({"input": query_text})
            duration = time.time() - start
            answer = res.get("answer", "No answer")
            logger.info(f"Answer: {answer}")
            sources = res.get("context", []) or []
            log_request(None, query_text, answer, duration, selected_model)

    return render_template(
        "index.html",
        model_choices=model_choices,
        selected_model=selected_model,
        selected_temp=selected_temp,
        answer=answer,
        sources=sources,
        query_text=query_text
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)
