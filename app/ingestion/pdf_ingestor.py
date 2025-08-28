import re
import PyPDF2
from pathlib import Path
from typing import List, Dict
from uuid import uuid4

CHUNK_SIZE = 300
CHUNK_OVERLAP = 50

def clean_text(t: str) -> str:
    # Fix OCR spacing issues first
    ocr_fixes = {
        r'Binar y Se ar c h': 'Binary Search',
        r'Se ar c hin g': 'Searching', 
        r'Algor ithms': 'Algorithms',
        r'Line ar Se ar c h': 'Linear Search',
        r'C omple xit y': 'Complexity',
        r'element s': 'elements',
        r'arra y': 'array',
        r'v al u e': 'value',
        r'adjac ent': 'adjacent',
        r'uns or t ed': 'unsorted',
        r's or t ed': 'sorted'
    }
    
    for pattern, replacement in ocr_fixes.items():
        t = re.sub(pattern, replacement, t, flags=re.IGNORECASE)
    
    # Standard cleaning
    t = t.replace("\x00", " ")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{2,}", "\n", t)
    return t.strip()

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i:i+chunk_size]
        if not chunk: break
        chunks.append(" ".join(chunk))
        i += max(1, chunk_size - overlap)
    return chunks

def read_pdf(file_path: str) -> str:
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        text = "".join((p.extract_text() or "") for p in reader.pages)
    return clean_text(text)

def process_pdfs(pdf_dir: str) -> List[Dict]:
    documents = []
    for pdf_file in Path(pdf_dir).glob("*.pdf"):
        text = read_pdf(str(pdf_file))
        for i, chunk in enumerate(chunk_text(text)):
            documents.append({
                "id": str(uuid4()),
                "text": chunk,
                "chunk_id": i,
                "source_file": pdf_file.name,
                "file_path": str(pdf_file.resolve()),
                "drive_url": "",
            })
    return documents
