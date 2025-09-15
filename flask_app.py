import os
import time
import hashlib
import requests
from pathlib import Path
from urllib.parse import urlparse
from flask import Flask, request, render_template, flash, session
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# LangChain loaders/vectorstores
from langchain_community.document_loaders import (
    PyPDFLoader, Docx2txtLoader, TextLoader,
    UnstructuredPowerPointLoader, UnstructuredExcelLoader, WebBaseLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_pinecone import PineconeVectorStore
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings

# Local utilities
from utils.logger import logger
from utils.db_utils import setup_database, log_request
import rag_logic  # Reuse create_rag_chain

# ----------------- Config -----------------
load_dotenv()
setup_database()

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "pptx", "ppt", "xlsx", "xls", "txt"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

embeddings = NVIDIAEmbeddings(model="nvidia/nv-embed-v1")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "")
app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.getenv("FLASK_SECRET", "devsecret")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 80 * 1024 * 1024  # 80MB

# ----------------- Helpers -----------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_document_loader(file_path):
    ext = file_path.lower().split('.')[-1]
    if ext == "pdf":
        return PyPDFLoader(file_path)
    if ext in ("docx", "doc"):
        return Docx2txtLoader(file_path)
    if ext in ("pptx", "ppt"):
        return UnstructuredPowerPointLoader(file_path)
    if ext in ("xlsx", "xls"):
        return UnstructuredExcelLoader(file_path)
    return TextLoader(file_path, encoding="utf-8")

def build_faiss_for_files(file_paths):
    """Build a fresh FAISS index from uploaded files (no caching)."""
    all_docs = []
    for fp in file_paths:
        try:
            loader = get_document_loader(fp)
            logger.info(f"Loaded {loader} for {fp}")
            all_docs.extend(loader.load())
        except Exception as e:
            logger.error(f"❌ Error loading {fp}: {e}")

    if not all_docs:
        return None

    ts = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=250)
    chunks = ts.split_documents(all_docs)
    vec_store = FAISS.from_documents(chunks, embeddings)
    logger.info(f"✅ Built FAISS index with {len(chunks)} chunks from files")
    return vec_store

def build_faiss_for_urls(urls):
    """Download real files or load webpages, then build FAISS index."""
    all_docs = []

    for link in urls:
        try:
            # HEAD check (ignore errors)
            try:
                head = requests.head(link, allow_redirects=True, timeout=10)
                ctype = (head.headers.get("Content-Type") or "").lower()
            except Exception:
                ctype = ""
            ext = Path(urlparse(link).path).suffix.lower()

            if ext in [".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls", ".txt"] or \
               any(x in ctype for x in ["pdf", "word", "officedocument", "text", "excel", "presentation"]):
                # Download and parse file
                r = requests.get(link, timeout=30)
                if r.status_code == 200 and r.content:
                    filename = os.path.basename(urlparse(link).path) or f"file_{hashlib.md5(link.encode()).hexdigest()}.dat"
                    save_path = os.path.join(UPLOAD_FOLDER, filename)
                    with open(save_path, "wb") as f:
                        f.write(r.content)
                    loader = get_document_loader(save_path)
                    all_docs.extend(loader.load())
                    logger.info(f"📄 Downloaded and loaded {filename} from {link}")
            else:
                # Treat as webpage
                logger.info(f"🌐 Loading webpage content from {link}")
                loader = WebBaseLoader(link)
                all_docs.extend(loader.load())

        except Exception as e:
            logger.error(f"❌ Error processing {link}: {e}")

    if not all_docs:
        logger.warning("⚠️ No valid text extracted from provided URLs")
        return None

    ts = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=250)
    chunks = ts.split_documents(all_docs)
    vec_store = FAISS.from_documents(chunks, embeddings)
    logger.info(f"✅ Built FAISS index with {len(chunks)} chunks from URLs")
    return vec_store

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
        "google/gemma-3n-e4b-it",
        "google/gemma-3n-e2b-it",
    ]
    answer, sources, query_text = None, [], ""
    selected_model = session.get("selected_model", model_choices[0])
    selected_temp = float(session.get("selected_temp", 0.5))

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
        document_links = [link.strip() for link in request.form.get("document_links", "").strip().splitlines() if link.strip()]

        retriever = None

        if uploaded_files and any(f.filename for f in uploaded_files if allowed_file(f.filename)):
            saved_paths = []
            for file in uploaded_files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                    file.save(save_path)
                    saved_paths.append(save_path)
                    logger.info(f"📁 Uploaded {filename}")
            if saved_paths:
                vec_store = build_faiss_for_files(saved_paths)
                if vec_store:
                    retriever = vec_store.as_retriever(search_kwargs={"k": 5})

        elif document_links:
            vec_store = build_faiss_for_urls(document_links)
            if vec_store:
                retriever = vec_store.as_retriever(search_kwargs={"k": 5})

        else:
            try:
                logger.info("📦 Using Pinecone fallback")
                pinecone_store = PineconeVectorStore.from_existing_index(PINECONE_INDEX_NAME, embeddings)
                retriever = pinecone_store.as_retriever(search_kwargs={"k": 5})
            except Exception as e:
                logger.error(f"❌ Pinecone error: {e}")
                flash("Pinecone retriever not available", "danger")

        if not retriever:
            flash("No retriever available", "danger")
        else:
            rag_chain = rag_logic.create_rag_chain(
                retriever=retriever,
                model_name=selected_model,
                temperature=selected_temp
            )
            start = time.time()
            res = rag_chain.invoke({"input": query_text})
            duration = time.time() - start
            answer = res.get("answer", "No answer")
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
    app.run(host="0.0.0.0", port=port, debug=False)
