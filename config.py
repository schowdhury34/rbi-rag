# config.py — project-wide settings
import os
from pathlib import Path

BASE_DIR  = Path(__file__).parent
DATA_DIR  = BASE_DIR / "data"

PDF_DIR       = DATA_DIR / "pdfs"
CHROMA_DIR    = DATA_DIR / "chroma_db"
METADATA_FILE = DATA_DIR / "metadata.csv"

RBI_BASE_URL       = "https://rbi.org.in"
RBI_CIRCULAR_INDEX = "https://rbi.org.in/Scripts/BS_CircularIndexDisplay.aspx"

CHUNK_SIZE      = 500   # TODO: tune after testing
CHUNK_OVERLAP   = 100

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
GROQ_API_KEY    = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL      = "llama-3.1-8b-instant"
