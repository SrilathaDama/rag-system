import sys
from pathlib import Path

# Add the project root (one level up) to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.ingestion.pdf_ingestor import process_pdfs
from app.indexing.elasticsearch_indexer import create_index, index_documents

docs = process_pdfs("docs")
print(f"\n✅ Total Chunks: {len(docs)}")
print("🧩 First Chunk:")
print(docs[0])

create_index()
index_documents(docs)
print("Documents indexed into Elasticsearch.")