import re
import PyPDF2
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
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
        r's or t ed': 'sorted',
        r'rn': 'm',  # Common OCR mistake
        r'cl': 'd',  # Another common mistake
        r'\s+': ' '  # Multiple spaces
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

def read_pdf_with_ocr(file_path: str) -> str:
    """Extract text with OCR fallback for scanned/handwritten content"""
    try:
        # Try PyMuPDF first (better than PyPDF2)
        doc = fitz.open(file_path)
        full_text = ""
        
        for page in doc:
            # Extract text normally
            text = page.get_text()
            
            # If little text found, try OCR
            if len(text.strip()) < 50:
                try:
                    pix = page.get_pixmap()
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    ocr_text = pytesseract.image_to_string(img)
                    text += " " + ocr_text
                except:
                    pass  # OCR failed, use what we have
            
            full_text += text + "\n"
        
        doc.close()
        return clean_text(full_text)
        
    except:
        # Fallback to PyPDF2 if PyMuPDF fails
        return read_pdf_fallback(file_path)

def read_pdf_fallback(file_path: str) -> str:
    """Fallback PDF reader using PyPDF2"""
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        text = "".join((p.extract_text() or "") for p in reader.pages)
    return clean_text(text)

def read_pdf(file_path: str) -> str:
    """Main PDF reading function with OCR support"""
    return read_pdf_with_ocr(file_path)

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
