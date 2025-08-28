from typing import List, Dict
from .search import bm25_search, dense_search, hybrid_search

def multi_strategy_search(query: str, k: int = 5) -> List[Dict]:
    """
    Enhanced search that tries multiple strategies to find related content
    """
    all_results = []
    
    # Strategy 1: Direct search
    results = hybrid_search(query, k)
    all_results.extend(results)
    
    # Strategy 2: Extract key terms and search individually
    key_terms = extract_key_terms(query)
    for term in key_terms:
        term_results = bm25_search(term, 2)
        all_results.extend(term_results)
    
    # Strategy 3: Semantic expansion
    expanded_queries = generate_related_queries(query)
    for exp_query in expanded_queries:
        exp_results = dense_search(exp_query, 2)
        all_results.extend(exp_results)
    
    # Deduplicate and rank
    return deduplicate_results(all_results, k)

def extract_key_terms(query: str) -> List[str]:
    """Extract key terms from query"""
    import re
    
    # Remove common words
    stop_words = {'what', 'is', 'are', 'how', 'the', 'a', 'an', 'and', 'or', 'but'}
    words = re.findall(r'\b\w+\b', query.lower())
    
    key_terms = [word for word in words if word not in stop_words and len(word) > 2]
    return key_terms[:3]  # Top 3 key terms

def generate_related_queries(query: str) -> List[str]:
    """No query expansion - return empty list"""
    return []

def deduplicate_results(results: List[Dict], k: int) -> List[Dict]:
    """Remove duplicates and return top k results"""
    seen = set()
    unique_results = []
    
    for result in results:
        key = (result.get('source_file'), result.get('chunk_id'))
        if key not in seen:
            seen.add(key)
            unique_results.append(result)
    
    # Sort by score if available
    unique_results.sort(key=lambda x: x.get('score', 0), reverse=True)
    return unique_results[:k]