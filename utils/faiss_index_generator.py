import os
import requests
import tempfile
import hashlib
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from dotenv import load_dotenv

load_dotenv()

LINKS_FILE = "links.txt"
FAISS_DIR = "faiss_indexes"

def create_local_faiss_stores():
    """Reads links from links.txt and creates a local FAISS index for each."""
    if not os.path.exists(FAISS_DIR):
        os.makedirs(FAISS_DIR)

    try:
        with open(LINKS_FILE, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: {LINKS_FILE} not found.")
        return

    embeddings = NVIDIAEmbeddings(model="nvidia/nv-embed-v1")
    print(f"Found {len(urls)} links. Creating local FAISS indexes...")

    for url in urls:
        try:
            # --- KEY FIX: Create a safe filename using a hash of the URL ---
            # This creates a short, unique, and valid filename for any URL.
            url_hash = hashlib.sha256(url.encode('utf-8')).hexdigest()
            save_path = os.path.join(FAISS_DIR, url_hash)

            if os.path.exists(save_path):
                print(f"Index for {url[:50]}... already exists. Skipping.")
                continue

            print(f"Processing {url[:50]}...")
            
            with tempfile.TemporaryDirectory() as temp_dir:
                response = requests.get(url)
                response.raise_for_status()

                # We can use a generic temp name as it's deleted afterwards
                temp_file_path = os.path.join(temp_dir, "temp_doc.pdf")

                with open(temp_file_path, "wb") as f:
                    f.write(response.content)

                loader = PyPDFLoader(temp_file_path)
                docs = loader.load()
            
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
            chunks = text_splitter.split_documents(docs)
            
            vector_store = FAISS.from_documents(chunks, embeddings)
            vector_store.save_local(save_path)
            print(f" -> Saved local FAISS index to '{save_path}'")
        except Exception as e:
            print(f" -> FAILED to process {url[:50]}... Error: {e}")
            
    print("\nPre-ingestion complete.")

if __name__ == "__main__":
    create_local_faiss_stores()