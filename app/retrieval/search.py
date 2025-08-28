from elasticsearch import Elasticsearch
from typing import List, Dict
from sentence_transformers import SentenceTransformer

ES_URL = "http://localhost:9200"
INDEX = "rag_documents"
es = Elasticsearch(ES_URL)
embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def bm25_search(query: str, k: int = 5) -> List[Dict]:
    body = {
        "size": k,
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["text^2", "source_file"],
                "type": "best_fields"
            }
        }
    }
    try:
        r = es.search(index=INDEX, body=body)
        return [hit["_source"] | {"score": hit["_score"]} for hit in r["hits"]["hits"]]
    except Exception:
        return []

def dense_search(query: str, k: int = 5) -> List[Dict]:
    query_vector = embedder.encode(query, normalize_embeddings=True).tolist()
    
    try:
        body = {
            "size": k,
            "knn": {
                "field": "embedding",
                "query_vector": query_vector,
                "k": k,
                "num_candidates": k * 2
            }
        }
        r = es.search(index=INDEX, body=body)
    except Exception:
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

def elser_search(query: str, k: int = 5) -> List[Dict]:
    body = {
        "size": k,
        "query": {
            "bool": {
                "should": [
                    {"match": {"text": {"query": query, "boost": 2.0}}},
                    {"more_like_this": {
                        "fields": ["text"],
                        "like": query,
                        "min_term_freq": 1,
                        "min_doc_freq": 1,
                        "max_query_terms": 15,
                        "boost": 1.0
                    }}
                ]
            }
        }
    }
    try:
        r = es.search(index=INDEX, body=body)
        return [hit["_source"] | {"score": hit["_score"]} for hit in r["hits"]["hits"]]
    except Exception:
        return []

def _rrf(ranked_lists: List[List[Dict]], weights: List[float] = [3.0, 1.5, 1.0], k: int = 60, top_k: int = 5) -> List[Dict]:
    scores = {}
    
    for weight, lst in zip(weights, ranked_lists):
        if not lst:
            continue
        for rank, item in enumerate(lst):
            key = (item.get("source_file"), item.get("chunk_id"))
            if key not in scores:
                scores[key] = {"doc": item, "score": 0.0}
            scores[key]["score"] += weight / (k + rank + 1)
    
    merged = sorted(scores.values(), key=lambda x: x["score"], reverse=True)
    return [m["doc"] | {"score": m["score"]} for m in merged[:top_k]]

def hybrid_search(query: str, k: int = 5) -> List[Dict]:
    bm25_results = bm25_search(query, k)
    dense_results = dense_search(query, k)
    sparse_results = elser_search(query, k)
    
    return _rrf([bm25_results, dense_results, sparse_results], top_k=k)