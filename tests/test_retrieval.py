import sys
import unittest
from pathlib import Path

# Add the project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.retrieval.search import bm25_search, dense_search, elser_search, hybrid_search
from app.indexing.elasticsearch_indexer import create_index, index_documents

class TestRetrieval(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Set up test data"""
        # Sample test documents
        cls.test_docs = [
            {
                "text": "Binary search is an efficient algorithm for finding an item from a sorted list of items.",
                "chunk_id": 0,
                "source_file": "algorithms.pdf",
                "file_path": "/test/algorithms.pdf",
                "drive_url": "https://drive.google.com/test1"
            },
            {
                "text": "Linear search checks every element in the list until it finds the target value.",
                "chunk_id": 1,
                "source_file": "algorithms.pdf", 
                "file_path": "/test/algorithms.pdf",
                "drive_url": "https://drive.google.com/test1"
            },
            {
                "text": "Accounting involves recording, measuring, and communicating financial information.",
                "chunk_id": 0,
                "source_file": "accounting.pdf",
                "file_path": "/test/accounting.pdf", 
                "drive_url": "https://drive.google.com/test2"
            }
        ]
        
        # Index test documents
        try:
            create_index()
            index_documents(cls.test_docs)
        except Exception as e:
            print(f"Setup failed: {e}")
    
    def test_bm25_search(self):
        """Test BM25 keyword search"""
        results = bm25_search("binary search algorithm", k=2)
        self.assertIsInstance(results, list)
        if results:
            self.assertIn("score", results[0])
            self.assertIn("text", results[0])
    
    def test_dense_search(self):
        """Test dense vector search"""
        results = dense_search("efficient searching method", k=2)
        self.assertIsInstance(results, list)
        if results:
            self.assertIn("score", results[0])
            self.assertIn("text", results[0])
    
    def test_elser_search(self):
        """Test ELSER sparse search"""
        results = elser_search("search algorithm", k=2)
        self.assertIsInstance(results, list)
        if results:
            self.assertIn("score", results[0])
            self.assertIn("text", results[0])
    
    def test_hybrid_search(self):
        """Test hybrid search combining all methods"""
        results = hybrid_search("binary search", k=3)
        self.assertIsInstance(results, list)
        if results:
            self.assertIn("score", results[0])
            self.assertIn("text", results[0])
            # Should return results sorted by RRF score
            scores = [r.get("score", 0) for r in results]
            self.assertEqual(scores, sorted(scores, reverse=True))
    
    def test_empty_query(self):
        """Test behavior with empty queries"""
        results = hybrid_search("", k=3)
        self.assertIsInstance(results, list)
    
    def test_no_results_query(self):
        """Test behavior with queries that should return no results"""
        results = hybrid_search("nonexistent_term_xyz123", k=3)
        self.assertIsInstance(results, list)

if __name__ == "__main__":
    unittest.main()