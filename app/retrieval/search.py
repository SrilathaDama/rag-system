from elasticsearch import Elasticsearch
from typing import List, Dict
from sentence_transformers import SentenceTransformer
import re

ES_URL = "http://localhost:9200"
INDEX = "rag_documents"
es = Elasticsearch(ES_URL)
embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def get_sparse_query(text: str) -> Dict[str, float]:
    words = re.findall(r'\b\w+\b', text.lower())
    word_counts = {}
    for word in words:
        if len(word) > 2:
            word_counts[word] = word_counts.get(word, 0) + 1
    
    if not word_counts:
        return {}
    
    max_count = max(word_counts.values())
    return {word: count/max_count for word, count in word_counts.items()}

def elser_search(query: str, k: int = 5) -> List[Dict]:
    sparse_query = get_sparse_query(query)
    
    if not sparse_query:
        return []
    
    # Use more_like_this for better sparse matching
    body = {
        "size": k,
        "query": {
            "more_like_this": {
                "fields": ["text"],
                "like": query,
                "min_term_freq": 1,
                "min_doc_freq": 1,
                "max_query_terms": 10
            }
        }
    }
    r = es.search(index=INDEX, body=body)
    return [hit["_source"] | {"score": hit["_score"]} for hit in r["hits"]["hits"]]

def bm25_search(query: str, k: int = 5) -> List[Dict]:
    # Multi-match with fuzzy to handle OCR issues
    body = {
        "size": k,
        "query": {
            "bool": {
                "should": [
                    {"match": {"text": query}},
                    {"match": {"text": {"query": query, "fuzziness": "AUTO"}}}
                ]
            }
        }
    }
    r = es.search(index=INDEX, body=body)
    return [hit["_source"] | {"score": hit["_score"]} for hit in r["hits"]["hits"]]

def dense_search(query: str, k: int = 5) -> List[Dict]:
    query_vector = embedder.encode(query, normalize_embeddings=True).tolist()
    
    body = {
        "size": k,
        "query": {
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                    "params": {"query_vector": query_vector}
                }
            }
        }
    }
    r = es.search(index=INDEX, body=body)
    return [hit["_source"] | {"score": hit["_score"]} for hit in r["hits"]["hits"]]

def _rrf(ranked_lists: List[List[Dict]], k: int = 60, top_k: int = 5) -> List[Dict]:
    scores = {}
    weights = [2.0, 1.5, 1.0]  # Balanced weights: BM25, Dense, ELSER
    
    for i, lst in enumerate(ranked_lists):
        if not lst:  # Skip empty lists
            continue
        weight = weights[i] if i < len(weights) else 1.0
        for rank, item in enumerate(lst):
            key = (item.get("source_file"), item.get("chunk_id"))
            scores.setdefault(key, {"doc": item, "score": 0.0})
            scores[key]["score"] += weight * (1.0 / (k + rank + 1))
    
    merged = sorted((v for v in scores.values()), key=lambda x: x["score"], reverse=True)
    return [m["doc"] | {"score": m["score"]} for m in merged[:top_k]]

def hybrid_search(query: str, k: int = 5) -> List[Dict]:
    try:
        b = bm25_search(query, k)
    except Exception:
        b = []
    try:
        d = dense_search(query, k)
    except Exception:
        d = []
    try:
        s = elser_search(query, k)
    except Exception:
        s = []
    
    # Get hybrid results
    hybrid_results = _rrf([b, d, s], top_k=k)
    
    # Fallback: if few results, try BM25 with more results
    if len(hybrid_results) < 2 and b:
        fallback = bm25_search(query, k*2)
        return fallback[:k] if fallback else hybrid_results
    
    return hybrid_results