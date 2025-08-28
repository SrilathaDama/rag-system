# RAG System with Elasticsearch + Ollama

A Retrieval-Augmented Generation (RAG) system that ingests PDFs from Google Drive and provides grounded Q&A using Elasticsearch and Ollama.

## Features

- **Google Drive Integration**: Ingest PDFs from shared Google Drive folders
- **Hybrid Search**: ELSER sparse embeddings + Dense vectors + BM25 keyword search
- **Local LLM**: Ollama with Llama3 for answer generation
- **FastAPI**: REST API with `/query`, `/ingest`, `/healthz` endpoints
- **Streamlit UI**: Web interface with citations and Drive links
- **Guardrails**: Grounded responses, says "I don't know" when uncertain

## Prerequisites

- Python 3.8+
- Elasticsearch 8.x running on `localhost:9200`
- Ollama with Llama3 model installed
- Google Cloud Service Account JSON file

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start Elasticsearch
```bash
# Using Docker
docker run -d --name elasticsearch -p 9200:9200 -e "discovery.type=single-node" -e "xpack.security.enabled=false" elasticsearch:8.12.0
```

### 3. Install Ollama & Llama3
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull Llama3 model
ollama pull llama3
```

### 4. Google Drive Setup
1. Create Google Cloud Project
2. Enable Google Drive API
3. Create Service Account
4. Download JSON key as `service_account.json` in project root (**Note: This file is gitignored for security**)
5. Share your Google Drive folder with the service account email

### 5. Configure Google Drive Folder
Update `main.py` with your folder ID:
```python
FOLDER_ID = "your_google_drive_folder_id_here"
```

## Usage

### Index Documents
```bash
python3 main.py
```

### Start Complete System (API + UI)
```bash
python3 start_app.py
```

**Or start services separately:**

### Start API Server
```bash
cd app
uvicorn api.server:app --reload --port 8000
```

### Start UI
```bash
streamlit run ui/app_ui.py
```

## API Endpoints

### Query Documents
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is binary search?", "mode": "hybrid", "top_k": 3}'
```

### Ingest from Google Drive
```bash
curl -X POST "http://localhost:8000/ingest?folder_id=YOUR_FOLDER_ID"
```

### Health Check
```bash
curl http://localhost:8000/healthz
```

## Project Structure

```
rag-system/
├── app/
│   ├── api/server.py           # FastAPI endpoints
│   ├── indexing/elasticsearch_indexer.py  # ES indexing
│   ├── ingestion/
│   │   ├── drive_ingestor.py   # Google Drive integration
│   │   └── pdf_ingestor.py     # PDF processing
│   ├── llm/generate.py         # Ollama LLM integration
│   └── retrieval/search.py     # Hybrid search (ELSER+Dense+BM25)
├── ui/app_ui.py               # Streamlit interface
├── tests/                     # Unit tests
├── main.py                    # Document indexing script
├── requirements.txt           # Dependencies
└── service_account.json       # Google Drive credentials
```

## Search Modes

- **hybrid** (default): ELSER + Dense + BM25 with weighted RRF
- **elser**: ELSER sparse embeddings only

## Example Queries

- "What is binary search algorithm?"
- "What is accounting?"
- "What are design patterns?"
- "What is DevOps?"

## Troubleshooting

### Elasticsearch not running
```bash
curl http://localhost:9200
# Should return cluster info
```

### Ollama not responding
```bash
ollama list
# Should show llama3 model
```

### Google Drive access denied
- Verify service account email has access to the folder
- Check `service_account.json` file exists and is valid

## Technical Details

- **Chunking**: ~300 tokens with 50 token overlap
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2 (384 dims)
- **ELSER**: Simulated sparse embeddings with keyword extraction
- **RRF**: Weighted fusion (BM25: 3.0x, Dense: 1.5x, ELSER: 1.0x)
- **OCR Fixes**: Automatic text cleaning for PDF extraction issues

## License

MIT License