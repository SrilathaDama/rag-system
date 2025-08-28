from typing import List, Dict
from .search import bm25_search, dense_search, hybrid_search

def smart_search(query: str, k: int = 5) -> List[Dict]:
    """
    Intelligently choose search method based on query type
    """
    query_lower = query.lower()
    
    # Technical/algorithmic queries work better with BM25
    technical_terms = ['algorithm', 'binary', 'search', 'sort', 'code', 'programming', 'technical']
    
    # Conceptual queries work better with dense search
    conceptual_terms = ['what is', 'explain', 'define', 'concept', 'meaning', 'purpose']
    
    # Mixed queries use hybrid
    if any(term in query_lower for term in technical_terms):
        print(f"🔧 Using BM25 for technical query")
        return bm25_search(query, k)
    elif any(term in query_lower for term in conceptual_terms):
        print(f"🧠 Using dense search for conceptual query")
        return dense_search(query, k)
    else:
        print(f"🚀 Using hybrid search")
        return hybrid_search(query, k)