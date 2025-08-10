import os
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredPowerPointLoader,
    UnstructuredExcelLoader,
    UnstructuredImageLoader,
    TextLoader
)
from langchain_nvidia import NVIDIAEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

# --- Load environment variables ---
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
EMBEDDING_MODEL_NAME = "nvidia/nv-embed-v1"
PINECONE_INDEX_NAME = "hackathon-pinecone-index"
EMBEDDING_DIMENSION = 4096
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

# --- Init Pinecone ---
pinecone = Pinecone(api_key=PINECONE_API_KEY)

# Create index if not exists
if PINECONE_INDEX_NAME not in [idx["name"] for idx in pinecone.list_indexes()]:
    pinecone.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=EMBEDDING_DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )

# --- Embeddings ---
embeddings = NVIDIAEmbeddings(model=EMBEDDING_MODEL_NAME, nvidia_api_key=NVIDIA_API_KEY)

# --- File loaders map ---
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
    ".md": TextLoader
}

# --- Data folder path ---
DATA_FOLDER = "data"

# --- Load and process all files ---
all_docs = []
for file_name in os.listdir(DATA_FOLDER):
    ext = os.path.splitext(file_name)[1].lower()
    loader_class = LOADERS.get(ext)
    if not loader_class:
        print(f"⚠️ Skipping unsupported file: {file_name}")
        continue

    file_path = os.path.join(DATA_FOLDER, file_name)
    try:
        loader = loader_class(file_path)
        docs = loader.load()
        all_docs.extend(docs)
        print(f"✅ Loaded {file_name}")
    except Exception as e:
        print(f"❌ Failed to load {file_name}: {e}")

# --- Chunk documents ---
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=250)
chunks = text_splitter.split_documents(all_docs)
print(f"📄 Total chunks created: {len(chunks)}")

# --- Store in Pinecone ---
PineconeVectorStore.from_documents(
    chunks,
    embeddings,
    index_name=PINECONE_INDEX_NAME
)

print("🎯 All documents uploaded to Pinecone successfully!")
