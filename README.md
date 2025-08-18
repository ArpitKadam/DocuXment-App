<div align="center">
<a href="https://ibb.co/1fN1SP6M"><img src="https://i.ibb.co/6RSzdTB8/Gemini-Generated-Image-oimnesoimnesoimn.png" alt="DocuXment-App" border="0"></a>

# DocuXment

**A robust, production-ready platform for complex document analysis, leveraging Retrieval-Augmented Generation (RAG) with NVIDIA LLMs, advanced document ingestion, and multi-format support. It offers both an interactive web interface and an API for real-time insurance Q&A powered by modern vector databases and cloud deployment.**

</div>

<div align="center">

[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE.md)
[![Python Version](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Framework: FastAPI](https://img.shields.io/badge/Framework-FastAPI-green.svg)](https://fastapi.tiangolo.com/)
[![Framework: Flask](https://img.shields.io/badge/Framework-Flask-blue.svg)](https://flask.palletsprojects.com/)
[![GitHub stars](https://img.shields.io/github/stars/ArpitKadam/DocuXment-App?style=social)](https://github.com/ArpitKadam/DocuXment-App/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/ArpitKadam/DocuXment-App?style=social)](https://github.com/ArpitKadam/DocuXment-App/network/members)

</div>

---

## 📋 Table of Contents

- ✨ Features
- 🏛️ Architecture
- 🚀 Getting Started
  - Prerequisites
  - Installation
  - Configuration
  - Running Locally
- ☁️ Deployment
- 🔌 API Usage
- 📂 File Tree Overview
- 🤝 Contributing
- 📜 License

---

## ✨ Features

- **Retrieval-Augmented Generation (RAG):** Combines LLMs (NVIDIA, Qwen, Mistral, Llama) with context retrieval for highly accurate Q&A over insurance documents.
- **Multi-format Ingestion:** Accepts `PDF`, `DOCX`, `PPTX`, `XLSX`, and `TXT`—upload files or provide document links.
- **Hybrid Vector Database:** Integrates **FAISS** for local/ephemeral storage and **Pinecone** for scalable, production-grade retrieval.
- **Web & API Access:** **FastAPI** backend for robust APIs and a **Flask**-powered web UI for user-friendly interaction.
- **Advanced Prompting:** Custom system prompts designed for precise, non-hallucinated, English-only answer generation.
- **Performance Monitoring:** Built-in caching, accuracy, and latency tracking for competition and production analysis.

---

## 🏛️ Architecture

- **Backend:** `FastAPI` (`api.py`) exposes `/api/v1/hackrx/run` for question-answering with authentication, and `/health` for metrics.
- **Frontend:** `Flask` (`flask_app.py`) presents a web UI for file/URL uploads, model/temperature selection, and Q&A display.
- **Retrieval/LLM Integration:** `rag_logic.py` builds RAG chains with NVIDIA LLMs, supporting caching and context compression (reranking).
- **Utils:** Includes modules for logging, database logging for audit/compliance, and document processing helpers.
- **Vector Databases:** Uses both **FAISS** (local, in `faiss_indexes/`) and **Pinecone** (cloud), depending on the data and upload method.
- **Deployment:** `render.yaml` allows one-click deployment on **Render.com** with secure secret management.
- **System Dependencies:** `apt.txt` (for Tesseract OCR) and `requirements.txt` ensure full support for multi-format documents and images.

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- Git
- System libraries (for Ubuntu/Debian):
  ```bash
  sudo apt-get update
  sudo apt-get install -y tesseract-ocr libtesseract-dev tesseract-ocr-eng tesseract-ocr-hin
  ```
### 2. Installation
Clone the repository and set up the Python environment:

```Bash
git clone https://github.com/ArpitKadam/DocuXment-App.git
cd Hackrx-Insurance-App
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Setup Environment Variables
Create a .env file in the root directory and add your secret keys:

Code snippet
```
HACKRX_API_KEY="your_secret_api_key"
NVIDIA_API_KEY="your_nvidia_api_key"
PINECONE_INDEX_NAME="your_pinecone_index"
FLASK_SECRET="your_flask_secret" # Optional, for Flask session security
```
### 4. Run Locally
Start the backend and frontend servers in separate terminals.

Backend (FastAPI):

```Bash
uvicorn api:app --host 0.0.0.0 --port 8000
```
Frontend (Flask):

```Bash
python flask_app.py
```

🌐 Web UI: Visit http://localhost:5000

📚 API Docs: Visit http://localhost:8000/docs

---

### ☁️ Deployment
- Render.com: The easiest way to deploy. Use the render.yaml file for a one-command deployment. Configure your environment variables in the Render dashboard secrets.

- Production: For scaling, upgrade to a paid Render plan.

- Docker: (Optional) You can create a Dockerfile using the system (apt.txt) and Python (requirements.txt) dependencies for containerized deployment.

---

### 🔌 API Usage
Endpoint: POST /api/v1/hackrx/run

Authentication: Bearer Token using your HACKRX_API_KEY.

Example Request:

```JSON
{
  "documents": ["https://example.com/insurance-policy.pdf"],
  "questions": ["What is the claim process for hospitalization?"]
}
```
Example Response:

```JSON
{
  "answers": [
    "You must submit the claim form and required documents to the insurer within 30 days of discharge, as outlined in Section 8 of the policy."
  ]
}
```

---

## 📂 File Tree Overview
<details>
<summary>Click to expand file tree</summary>

```
.
├── api.py              # FastAPI backend for API, RAG logic, and metrics.
├── flask_app.py        # Flask web frontend for interactive demo.
├── rag_logic.py        # RAG pipeline, LLM integration, caching.
├── requirements.txt    # All Python package dependencies.
├── apt.txt             # System libraries for OCR and document processing.
├── render.yaml         # Render.com deployment configuration.
├── .env.example        # Example environment file.
├── faiss_indexes/      # Local vector DB storage (auto-created).
├── static/             # CSS, JS, and image assets for the frontend.
└── templates/          # HTML templates for the Flask app.
```

</details>

---

## 🤝 Contributing
Pull requests and forks are welcome! Please create an issue for any bugs or feature requests. Contributions to model selection logic, vector DB connectors, and UI improvements are highly appreciated.

## 📜 License
This project is under a Proprietary License – intended for internal evaluation and hackathons only. For commercial or research use, please contact the repository owner.

<div align="center">
Made with ❤️ by <a href="https://github.com/ArpitKadam/">Arpit Kadam</a> and Contributors
</div>
