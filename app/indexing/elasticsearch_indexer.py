from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import hashlib
import re

ES_URL = "http://localhost:9200"
INDEX = "rag_documents"

es = Elasticsearch(ES_URL)
embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def create_index():
    if es.indices.exists(index=INDEX):
        return
    es.indices.create(index=INDEX, body={
        "mappings": {
            "properties": {
                "text": {"type": "text"},
                "sparse_embedding": {"type": "object", "enabled": False},
                "embedding": {"type": "dense_vector", "dims": 384, "index": True, "similarity": "cosine"},
                "chunk_id": {"type": "integer"},
                "source_file": {"type": "keyword"},
                "file_path": {"type": "keyword"},
                "drive_url": {"type": "keyword"}
            }
        }
    })

def get_embedding(text: str):
    return embedder.encode(text, normalize_embeddings=True).tolist()

def get_sparse_embedding(text: str) -> Dict[str, float]:
    # Simple ELSER simulation using keyword extraction
    words = re.findall(r'\b\w+\b', text.lower())
    word_counts = {}
    for word in words:
        if len(word) > 2:
            word_counts[word] = word_counts.get(word, 0) + 1
    
    if not word_counts:
        return {}
    
    max_count = max(word_counts.values())
    return {word: count/max_count for word, count in word_counts.items()}

def index_documents(docs: List[Dict]) -> int:
    create_index()
    n = 0
    for d in docs:
        doc_id = hashlib.md5(f"{d['source_file']}|{d['chunk_id']}".encode()).hexdigest()
        es.index(index=INDEX, id=doc_id, body={
            "text": d["text"],
            "sparse_embedding": get_sparse_embedding(d["text"]),
            "embedding": get_embedding(d["text"]),
            "chunk_id": d["chunk_id"],
            "source_file": d["source_file"],
            "file_path": d.get("file_path", ""),
            "drive_url": d.get("drive_url", "")
        })
        n += 1
    es.indices.refresh(index=INDEX)
    return n
