import os
import requests
import tempfile
import hashlib
from urllib.parse import urlparse
from pathlib import Path
from dotenv import load_dotenv

# --- LangChain Components ---
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings

# --- Document Loaders ---
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredExcelLoader,
    UnstructuredPowerPointLoader,
    UnstructuredImageLoader,
    TextLoader,
    UnstructuredHTMLLoader
)

load_dotenv()

LINKS_FILE = "links.txt"
FAISS_DIR = "faiss_indexes"

def get_loader(file_path: str, file_ext: str):
    loader_map = {
        ".pdf": PyPDFLoader,
        ".docx": Docx2txtLoader,
        ".xlsx": UnstructuredExcelLoader,
        ".pptx": UnstructuredPowerPointLoader,
        ".txt": TextLoader,
        ".png": UnstructuredImageLoader,
        ".jpg": UnstructuredImageLoader,
        ".jpeg": UnstructuredImageLoader,
        ".html": UnstructuredHTMLLoader
    }
    loader_class = loader_map.get(file_ext.lower())
    if loader_class:
        return loader_class(file_path)
    else:
        print(f" -> ⚠️ Warning: No loader for '{file_ext}'. Skipping file.")
        return None

def create_local_faiss_stores():
    if not os.path.exists(FAISS_DIR):
        os.makedirs(FAISS_DIR)
        print(f"✅ Created directory: '{FAISS_DIR}'")

    try:
        with open(LINKS_FILE, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"❌ Error: '{LINKS_FILE}' not found.")
        return

    embeddings = NVIDIAEmbeddings(model="nvidia/nv-embed-v1")
    print(f"🔎 Found {len(urls)} links. Creating local FAISS indexes...")

    for url in urls:
        try:
            url_hash = hashlib.sha256(url.encode('utf-8')).hexdigest()
            save_path = os.path.join(FAISS_DIR, url_hash)

            if os.path.exists(save_path):
                print(f"👍 Index for {url} already exists. Skipping.")
                continue

            print(f"Processing {url}...")

            path = Path(urlparse(url).path)
            file_extension = path.suffix

            # If no extension, assume it's HTML
            if not file_extension:
                file_extension = ".html"

            # Download content
            with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
                response = requests.get(url, timeout=60)
                response.raise_for_status()

                # If HTML, ensure it's encoded properly
                if file_extension == ".html":
                    temp_file.write(response.text.encode("utf-8"))
                else:
                    temp_file.write(response.content)
                temp_file_path = temp_file.name

            loader = get_loader(temp_file_path, file_extension)
            if loader:
                docs = loader.load()
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
                chunks = text_splitter.split_documents(docs)

                if not chunks:
                    print(f" -> ⚠️ No text extracted from {url}. Skipping.")
                    continue

                vector_store = FAISS.from_documents(chunks, embeddings)
                vector_store.save_local(save_path)
                print(f" -> ✅ Saved FAISS index to '{save_path}'")

        except requests.RequestException as e:
            print(f" -> ❌ FAILED to download {url[:60]}... Error: {e}")
        except Exception as e:
            print(f" -> ❌ FAILED to process {url[:60]}... Error: {e}")
        finally:
            if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    print("\nPre-ingestion complete.")

if __name__ == "__main__":
    create_local_faiss_stores()
