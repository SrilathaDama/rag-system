# app/ingestion/drive_ingestor.py
import io
import os
from pathlib import Path
from typing import List, Dict, Optional
from uuid import uuid4

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

import PyPDF2

from .pdf_ingestor import chunk_text, clean_text

# ---- Config ----
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
CHUNK_SIZE = 300
CHUNK_OVERLAP = 50
SA_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "service_account.json")


# -------- Google Drive helpers --------
def drive_service(sa_json: str = SA_PATH):
    """Authenticate with Google Drive using a Service Account."""
    if not os.path.exists(sa_json):
        raise FileNotFoundError(
            f"{sa_json} not found. Provide your Service Account key JSON."
        )
    creds = service_account.Credentials.from_service_account_file(sa_json, scopes=SCOPES)
    return build("drive", "v3", credentials=creds)


def list_pdfs_in_folder(
    service,
    folder_id: str,
    drive_id: Optional[str] = None,
    page_size: int = 100,
) -> List[Dict]:
    """
    List PDFs inside a folder. Works for My Drive and Shared Drives.
    If using a Shared Drive, pass drive_id.
    """
    query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
    params = {
        "q": query,
        "fields": "nextPageToken, files(id,name,webViewLink)",
        "pageSize": page_size,
    }
    if drive_id:
        params.update(
            {
                "supportsAllDrives": True,
                "includeItemsFromAllDrives": True,
                "corpora": "drive",
                "driveId": drive_id,
            }
        )

    files, page_token = [], None
    while True:
        if page_token:
            params["pageToken"] = page_token
        resp = service.files().list(**params).execute()
        files.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return files


def download_pdf_text(service, file_id: str) -> str:
    """Download a PDF by fileId and extract text (PyPDF2)."""
    request = service.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, request)

    done = False
    while not done:
        _, done = downloader.next_chunk()

    buf.seek(0)
    reader = PyPDF2.PdfReader(buf)
    text = []
    for page in reader.pages:
        # PyPDF2 returns None sometimes; coalesce to ""
        text.append(page.extract_text() or "")
    return clean_text("".join(text))


# -------- Pipeline entrypoint --------
def process_drive_pdfs(
    folder_id: str,
    drive_id: Optional[str] = None,
    sa_json: str = SA_PATH,
) -> List[Dict]:
    """
    End-to-end:
    - list PDFs in Drive folder
    - download & extract text
    - chunk and attach metadata for indexing
    Returns a list of dicts: {id, text, chunk_id, source_file, drive_url, file_path}
    """
    svc = drive_service(sa_json)
    try:
        pdf_files = list_pdfs_in_folder(svc, folder_id, drive_id)
    except HttpError as e:
        raise RuntimeError(f"Drive list error: {e}") from e

    documents: List[Dict] = []
    for f in pdf_files:
        name = f.get("name", "unknown.pdf")
        file_id = f["id"]
        link = f.get("webViewLink")

        try:
            raw_text = download_pdf_text(svc, file_id)
            if not raw_text.strip():
                # Skip empty docs (often image-only PDFs)
                continue

            chunks = chunk_text(raw_text, CHUNK_SIZE, CHUNK_OVERLAP)
            for i, chunk in enumerate(chunks):
                documents.append(
                    {
                        "id": str(uuid4()),
                        "text": chunk,
                        "chunk_id": i,
                        "source_file": name,
                        "drive_url": link,
                        "file_path": f"drive://{file_id}",
                    }
                )
        except HttpError as e:
            print(f"[Drive error] {name}: {e}")
        except Exception as e:
            print(f"[Parse error] {name}: {e}")

    return documents
