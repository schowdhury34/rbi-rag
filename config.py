# config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file so GROQ_API_KEY is available without manually setting env vars
load_dotenv()

BASE_DIR  = Path(__file__).parent
DATA_DIR  = BASE_DIR / "data"

PDF_DIR    = DATA_DIR / "pdfs"

# On Streamlit Cloud the repo is read-only — use /tmp for ChromaDB
_on_streamlit = (
    os.path.exists("/mount/src") or
    os.environ.get("STREAMLIT_SHARING_MODE") is not None or
    "/mount" in str(Path(__file__).parent)
)
CHROMA_DIR = Path("/tmp/chroma_db") if _on_streamlit else DATA_DIR / "chroma_db"

METADATA_FILE = DATA_DIR / "metadata.csv"

# Create data dirs on import — avoids FileNotFoundError on first run
PDF_DIR.mkdir(parents=True, exist_ok=True)
#CHROMA_DIR.mkdir(parents=True, exist_ok=True)

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

CHUNK_SIZE      = 800
CHUNK_OVERLAP   = 150
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_BATCH = 64
COLLECTION_NAME = "rbi_circulars"
TOP_K           = 5

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are an expert RBI regulations assistant.
Answer using ONLY the context provided below.
Always cite the circular number, date, and department.
If the answer is not in the context, say: "I could not find this in the indexed circulars."

Context:
{context}
"""
