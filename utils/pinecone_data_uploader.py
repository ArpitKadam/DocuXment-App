import os
import re
import sqlite3
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
    UnstructuredExcelLoader,
    UnstructuredImageLoader,
    UnstructuredPowerPointLoader,
    WebBaseLoader,
)
from langchain_nvidia import NVIDIAEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec

# --- Configuration ---
load_dotenv()

# --- Database and Link Extraction ---
DB_FILE = "claim_log.db"
PROCESSED_LINKS_LOG = "utils/processed_links.log"

# --- Pinecone & NVIDIA ---
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
PINECONE_INDEX_NAME = "hackathon-pinecone-index"
EMBEDDING_MODEL_NAME = "nvidia/nv-embed-v1"
EMBEDDING_DIMENSION = 4096

# --- Document Loaders Map ---
# Maps file extensions to their corresponding LangChain loader class.
LOADERS = {
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
    ".pptx": UnstructuredPowerPointLoader,
    ".xlsx": UnstructuredExcelLoader,
    ".xls": UnstructuredExcelLoader,
    ".png": UnstructuredImageLoader,
    ".jpg": UnstructuredImageLoader,
    ".jpeg": UnstructuredImageLoader,
    ".txt": TextLoader,
    ".md": TextLoader,
}

# ==============================================================================
# Helper Functions
# ==============================================================================

def find_all_urls(text_block: str) -> set:
    """Uses a regular expression to find all URLs within a block of text."""
    url_pattern = r'https?://[^\s,"\'\]\[<>]+'
    urls = re.findall(url_pattern, text_block)
    return {url.strip() for url in urls}


def get_links_from_db() -> set:
    """Connects to the SQLite DB and extracts all unique document links."""
    print(f"🔍 Accessing database: {DB_FILE}")
    if not Path(DB_FILE).exists():
        print(f"❌ ERROR: Database file not found at '{DB_FILE}'.")
        return set()

    all_db_links = set()
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            query = "SELECT document_links FROM logs WHERE document_links IS NOT NULL AND document_links != ''"
            cursor.execute(query)
            rows = cursor.fetchall()
            print(f"Found {len(rows)} entries with links.")

            for row in rows:
                urls_found = find_all_urls(row[0])
                all_db_links.update(urls_found)
    except sqlite3.Error as e:
        print(f"❌ DATABASE ERROR: Could not read from '{DB_FILE}'. Details: {e}")
    
    return all_db_links


def load_processed_links() -> set:
    """Loads the set of already processed URLs from the log file."""
    processed_log = Path(PROCESSED_LINKS_LOG)
    if not processed_log.exists():
        return set()
    with open(processed_log, 'r', encoding='utf-8') as f:
        return {line.strip() for line in f}


def mark_link_as_processed(link: str):
    """Appends a successfully processed URL to the log file."""
    with open(PROCESSED_LINKS_LOG, 'a', encoding='utf-8') as f:
        f.write(link + '\n')

# ==============================================================================
# Main Execution
# ==============================================================================

def main():
    """Main function to run the data extraction and uploading pipeline."""
    print("🚀 Starting Intelligent Data Pipeline...")
    print("=" * 50)

    # --- 1. Get Links and Filter for New Ones ---
    all_db_links = get_links_from_db()
    already_processed = load_processed_links()
    
    links_to_process = all_db_links - already_processed

    if not links_to_process:
        print("\n✅ No new links to process. Everything is up to date!")
        return

    print(f"\n✨ Found {len(links_to_process)} new links to process.")
    print("-" * 50)

    # --- 2. Initialize Services ---
    print("🔌 Initializing Pinecone and NVIDIA services...")
    try:
        # Init Pinecone
        pinecone = Pinecone(api_key=PINECONE_API_KEY)
        if PINECONE_INDEX_NAME not in [idx["name"] for idx in pinecone.list_indexes()]:
            pinecone.create_index(
                name=PINECONE_INDEX_NAME,
                dimension=EMBEDDING_DIMENSION,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
            print(f"Pinecone index '{PINECONE_INDEX_NAME}' created.")
        
        # Init Embeddings Model
        embeddings = NVIDIAEmbeddings(model=EMBEDDING_MODEL_NAME, nvidia_api_key=NVIDIA_API_KEY)
        
        # Init Text Splitter
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    except Exception as e:
        print(f"❌ FATAL: Could not initialize services. Error: {e}")
        return

    print("✅ Services initialized successfully.")
    print("-" * 50)

    # --- 3. Process Each New Link ---
    successful_uploads = 0
    with tempfile.TemporaryDirectory() as temp_dir:
        for i, link in enumerate(links_to_process):
            print(f"\nProcessing link {i+1}/{len(links_to_process)}: {link}")
            try:
                docs = None
                parsed_url = urlparse(link)
                file_ext = os.path.splitext(parsed_url.path)[1].lower()

                # A) Handle known file types
                if file_ext in LOADERS:
                    response = requests.get(link, timeout=30)
                    response.raise_for_status() # Raise an exception for bad status codes

                    # Save file temporarily
                    file_name = Path(parsed_url.path).name
                    temp_file_path = Path(temp_dir) / file_name
                    with open(temp_file_path, 'wb') as f:
                        f.write(response.content)
                    
                    print(f"  -> Downloaded as file to '{temp_file_path}'")
                    loader = LOADERS[file_ext](str(temp_file_path))
                    docs = loader.load()
                
                # B) Handle web pages (default)
                else:
                    print("  -> Identified as a web page.")
                    loader = WebBaseLoader(link)
                    docs = loader.load()

                if not docs:
                    print("  -> ⚠️ No content could be loaded. Skipping.")
                    continue

                # C) Chunk and Upload
                chunks = text_splitter.split_documents(docs)
                print(f"  -> Split into {len(chunks)} chunks.")
                
                PineconeVectorStore.from_documents(
                    documents=chunks,
                    embedding=embeddings,
                    index_name=PINECONE_INDEX_NAME
                )

                # D) Log Success
                mark_link_as_processed(link)
                print(f"  -> ✅ Successfully uploaded to Pinecone.")
                successful_uploads += 1

            except Exception as e:
                print(f"  -> ❌ ERROR processing link: {e}")

    # --- 4. Final Report ---
    print("\n" + "=" * 50)
    print("🎉 Pipeline run complete!")
    print(f"Total new links found: {len(links_to_process)}")
    print(f"Successfully processed and uploaded: {successful_uploads}")
    print("=" * 50)


if __name__ == "__main__":
    main()