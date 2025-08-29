#!/usr/bin/env python3
"""
Test runner script for the RAG system
Runs all tests and provides a summary
"""

import subprocess
import sys
from pathlib import Path

def run_test(test_file, description):
    """Run a single test file and return success status"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print('='*60)
    
    try:
        if test_file.endswith('.py') and not test_file.startswith('test_'):
            # For non-pytest files (like test_llm.py)
            result = subprocess.run([sys.executable, f"tests/{test_file}"], 
                                  capture_output=False, check=True)
        else:
            # For pytest files
            result = subprocess.run([sys.executable, "-m", "pytest", f"tests/{test_file}", "-v"], 
                                  capture_output=False, check=True)
        print(f"✅ {description} - PASSED")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED (exit code: {e.returncode})")
        return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Running RAG System Test Suite")
    print("=" * 60)
    
    tests = [
        ("test_es_minimal.py", "Elasticsearch Connection Test"),
        ("test_ingestion.py", "PDF Ingestion Test"),
        ("test_llm.py", "Ollama LLM Integration Test"),
        ("test_retrieval.py", "Search & Retrieval Test")
    ]
    
    results = []
    for test_file, description in tests:
        success = run_test(test_file, description)
        results.append((description, success))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print('='*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {description}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! RAG system is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())