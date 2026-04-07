# config.py
import os
from pathlib import Path

BASE_DIR  = Path(__file__).parent
DATA_DIR  = BASE_DIR / "data"

PDF_DIR       = DATA_DIR / "pdfs"
CHROMA_DIR    = DATA_DIR / "chroma_db"
METADATA_FILE = DATA_DIR / "metadata.csv"

RBI_BASE_URL       = "https://rbi.org.in"
RBI_CIRCULAR_INDEX = "https://rbi.org.in/Scripts/BS_CircularIndexDisplay.aspx"
CRAWL_YEAR_FROM    = 2020
MAX_PDFS           = 500
REQUEST_DELAY      = 1.5
REQUEST_TIMEOUT    = 30
REQUEST_HEADERS    = {
    "User-Agent": (
        "Mozilla/5.0 (educational research bot; "
        "RBI circular RAG; schowdhury3434@gmail.com)"
    )
}

CHUNK_SIZE      = 500
CHUNK_OVERLAP   = 100
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_BATCH = 64
COLLECTION_NAME = "rbi_circulars"
TOP_K           = 5

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = "llama-3.1-8b-instant"

SYSTEM_PROMPT = """You are an expert RBI regulations assistant.
Answer using ONLY the context below.
Cite circular number, date, and department.
If not found, say so.

Context:
{context}
"""
