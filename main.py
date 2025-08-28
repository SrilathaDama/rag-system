import sys
sys.path.append('app')
from app.ingestion.drive_ingestor import process_drive_pdfs
from app.indexing.elasticsearch_indexer import index_documents

# Your Google Drive folder ID
FOLDER_ID = "1h6GptTW3DPCdhu7q5tY-83CXrpV8TmY_"

if __name__ == "__main__":
    print(f"🔄 Processing PDFs from Google Drive folder: {FOLDER_ID}")
    docs = process_drive_pdfs(FOLDER_ID)
    print(f"✅ Extracted {len(docs)} chunks from Google Drive")
    
    print("🔄 Indexing documents...")
    n = index_documents(docs)
    print(f"✅ Indexing complete! Indexed {n} documents.")
    
    # Show sample with Drive URL
    if docs:
        sample = docs[0]
        print(f"\n📄 Sample: {sample['source_file']}")
        print(f"🔗 Drive URL: {sample['drive_url']}")
