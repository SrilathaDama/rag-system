# app/api/server.py
from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Optional

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.drive_ingestor import process_drive_pdfs
from indexing.elasticsearch_indexer import index_documents
from retrieval.search import hybrid_search, elser_search

from llm.generate import build_prompt, ollama_generate

app = FastAPI()

# ---------- Models ----------
class QueryIn(BaseModel):
    question: str
    top_k: int = 5
    mode: str = "hybrid"  # "hybrid" | "elser"
    min_score: float = 0.0  # grounding threshold (0-1 if you normalize)

class IngestOut(BaseModel):
    downloaded_docs: int
    indexed_docs: int

# ---------- Health ----------
@app.get("/healthz")
def healthz():
    return {"ok": True}

# ---------- Ingestion ----------
@app.post("/ingest", response_model=IngestOut)
def ingest_from_drive(
    folder_id: str = Query(..., description="Drive folder ID"),
    drive_id: Optional[str] = Query(None, description="Shared Drive ID if applicable")
):
    docs = process_drive_pdfs(folder_id=folder_id, drive_id=drive_id)
    if not docs:
        return {"downloaded_docs": 0, "indexed_docs": 0}
    n = index_documents(docs)  # implement inside elasticsearch_indexer.py
    return {"downloaded_docs": len(docs), "indexed_docs": n}

# ---------- Query / RAG ----------
@app.post("/query")
def query(body: QueryIn):
    # Guardrails: reject empty/off-topic quickly
    q = (body.question or "").strip()
    if not q:
        return {"answer": "I don't know.", "citations": []}

    # Retrieval
    if body.mode == "elser":
        hits = elser_search(q, k=body.top_k)
    else:
        hits = hybrid_search(q, k=body.top_k)

    if not hits:
        return {"answer": "I don't know.", "citations": []}

    # Optional grounding filter (keep only sufficiently relevant chunks)
    scored = [h for h in hits if h.get("score", 1.0) >= body.min_score]
    if not scored:
        return {"answer": "I don't know.", "citations": []}

    contexts = [h["text"] for h in scored]
    prompt = build_prompt(q, contexts)

    # LLM generation with safety fallback
    try:
        answer = ollama_generate("llama3", prompt)
    except Exception as e:
        answer = f"Retrieved context, but LLM failed: {e}"

    # Citations with link + file + chunk id
    citations = [{
        "idx": i + 1,
        "source_file": h.get("source_file"),
        "chunk_id": h.get("chunk_id"),
        "link": h.get("drive_url"),
        "snippet": (h.get("text") or "")[:300]
    } for i, h in enumerate(scored)]

    return {"answer": answer, "citations": citations, "used_mode": body.mode}

