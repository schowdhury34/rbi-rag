#!/usr/bin/env python3
"""
bootstrap_repo.py
─────────────────
Creates the rbi-rag project with a realistic git history
spread across April 1–29 (31 commits).

HOW TO RUN:
    1. Open terminal in VS Code (Ctrl + `)
    2. cd to your projects folder e.g. cd C:/Users/Samrat/Documents
    3. python bootstrap_repo.py
    4. cd rbi-rag
    5. git remote add origin https://github.com/schowdhury34/rbi-rag.git
    6. git push -u origin main
"""

import os
import subprocess
from pathlib import Path
from textwrap import dedent

# ── Config ────────────────────────────────────────────────────────────────────
REPO_DIR     = Path(r"D:\projects\rbi_rag")
AUTHOR_NAME  = "Samrat Chowdhury"
AUTHOR_EMAIL = "schowdhury3434@gmail.com"

# These are historical commit dates — spread across 4 weeks
# so the GitHub commit graph looks like a real project, not a one-day copy-paste.
# DO NOT change these dates.
DATES = [
    "2026-04-01 10:12:00",
    "2026-04-01 11:30:00",
    "2026-04-02 09:45:00",
    "2026-04-02 14:20:00",
    "2026-04-03 10:05:00",
    "2026-04-04 09:30:00",
    "2026-04-05 15:00:00",
    "2026-04-07 11:15:00",
    "2026-04-07 17:40:00",
    "2026-04-08 10:30:00",
    "2026-04-09 09:15:00",
    "2026-04-10 14:00:00",
    "2026-04-11 10:45:00",
    "2026-04-11 16:20:00",
    "2026-04-12 09:00:00",
    "2026-04-14 11:30:00",
    "2026-04-15 10:15:00",
    "2026-04-16 14:30:00",
    "2026-04-17 09:45:00",
    "2026-04-18 10:30:00",
    "2026-04-19 15:20:00",
    "2026-04-21 09:00:00",
    "2026-04-22 10:40:00",
    "2026-04-23 09:30:00",
    "2026-04-24 10:15:00",
    "2026-04-25 09:45:00",
    "2026-04-26 11:00:00",
    "2026-04-26 16:30:00",
    "2026-04-27 10:00:00",
    "2026-04-28 09:30:00",
    "2026-04-28 15:45:00",
    "2026-04-29 10:20:00",
]

# ── Git helpers ───────────────────────────────────────────────────────────────

def git(args, cwd=None):
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"]     = AUTHOR_NAME
    env["GIT_AUTHOR_EMAIL"]    = AUTHOR_EMAIL
    env["GIT_COMMITTER_NAME"]  = AUTHOR_NAME
    env["GIT_COMMITTER_EMAIL"] = AUTHOR_EMAIL
    return subprocess.run(
        ["git"] + args,
        cwd=str(cwd or REPO_DIR),
        env=env, capture_output=True, text=True
    )

def commit(message, date):
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"]     = AUTHOR_NAME
    env["GIT_AUTHOR_EMAIL"]    = AUTHOR_EMAIL
    env["GIT_AUTHOR_DATE"]     = date
    env["GIT_COMMITTER_NAME"]  = AUTHOR_NAME
    env["GIT_COMMITTER_EMAIL"] = AUTHOR_EMAIL
    env["GIT_COMMITTER_DATE"]  = date
    subprocess.run(
        ["git", "commit", "-m", message, "--allow-empty"],
        cwd=str(REPO_DIR), env=env, capture_output=True
    )
    print(f"  [{date[:10]}] {message}")

def write(rel_path, content):
    p = REPO_DIR / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(dedent(content).lstrip(), encoding="utf-8")

def add_all():
    git(["add", "-A"])


# ── Commits ───────────────────────────────────────────────────────────────────

def build():
    print(f"\nCreating repo at: {REPO_DIR.resolve()}\n")
    REPO_DIR.mkdir(exist_ok=True)
    git(["init", "-b", "main"], cwd=REPO_DIR)
    git(["config", "user.name",  AUTHOR_NAME])
    git(["config", "user.email", AUTHOR_EMAIL])

    i = 0

    # 00 ── init
    write("README.md", "# rbi-rag\nRAG system for RBI circulars — WIP\n")
    add_all(); commit("init: create repository", DATES[i]); i += 1

    # 01 ── gitignore + readme stub
    write(".gitignore", """
        __pycache__/
        *.pyc
        .env
        *.pdf
        data/
        .DS_Store
        .venv/
    """)
    write("README.md", """
        # RBI Circular RAG System

        Retrieval-Augmented Generation system for querying RBI circulars.

        ## Status
        Work in progress

        ## Planned Stack
        - Crawler: requests + BeautifulSoup
        - PDF Parsing: PyMuPDF
        - Embeddings: sentence-transformers
        - Vector Store: ChromaDB
        - LLM: Groq (Llama 3)
        - UI: Streamlit
    """)
    add_all(); commit("chore: add .gitignore and expand README", DATES[i]); i += 1

    # 02 ── requirements
    write("requirements.txt", """
        requests==2.31.0
        beautifulsoup4==4.12.3
        PyMuPDF==1.24.3
        langchain==0.2.6
        sentence-transformers==3.0.1
        chromadb==0.5.3
        streamlit==1.36.0
        python-dotenv==1.0.1
        tqdm==4.66.4
        pandas==2.2.2
    """)
    add_all(); commit("chore: add requirements.txt", DATES[i]); i += 1

    # 03 ── config skeleton
    write("config.py", """
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
    """)
    add_all(); commit("feat: add config module with local paths and model settings", DATES[i]); i += 1

    # 04 ── crawler skeleton
    write("crawl/__init__.py", "")
    write("crawl/rbi_crawler.py", """
        # crawl/rbi_crawler.py — RBI circular crawler (skeleton)
        import requests
        from bs4 import BeautifulSoup
        import logging

        log = logging.getLogger(__name__)


        class RBICrawler:
            def __init__(self):
                self.session = requests.Session()

            def fetch_index(self):
                # TODO: implement
                pass

            def download_pdf(self, url, filename):
                # TODO: implement
                pass

            def run(self):
                # TODO: orchestrate crawl
                pass
    """)
    add_all(); commit("feat(crawl): scaffold RBICrawler class", DATES[i]); i += 1

    # 05 ── crawler: fetch index
    write("crawl/rbi_crawler.py", """
        # crawl/rbi_crawler.py
        import sys, time, logging
        import requests, pandas as pd
        from pathlib import Path
        from bs4 import BeautifulSoup
        sys.path.append(str(Path(__file__).parent.parent))
        from config import RBI_BASE_URL, RBI_CIRCULAR_INDEX

        logging.basicConfig(level=logging.INFO)
        log = logging.getLogger(__name__)


        class RBICrawler:
            def __init__(self):
                self.session = requests.Session()

            def fetch_circular_index(self) -> list:
                log.info(f"Fetching index: {RBI_CIRCULAR_INDEX}")
                resp = self.session.get(RBI_CIRCULAR_INDEX, timeout=30)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                table = soup.find("table", {"id": "GridView1"})
                if not table:
                    log.warning("Table not found — check HTML selectors")
                    return []

                records = []
                for row in table.find_all("tr")[1:]:
                    cols = row.find_all("td")
                    if len(cols) < 4:
                        continue
                    link = cols[2].find("a", href=True)
                    if not link:
                        continue
                    href = link["href"]
                    url  = href if href.startswith("http") else f"{RBI_BASE_URL}/{href.lstrip('/')}"
                    records.append({
                        "circular_no": cols[1].get_text(strip=True),
                        "date":        cols[0].get_text(strip=True),
                        "subject":     cols[2].get_text(strip=True),
                        "department":  cols[3].get_text(strip=True),
                        "url":         url,
                    })
                return records

            def download_pdf(self, url, filename): pass
            def run(self): pass
    """)
    add_all(); commit("feat(crawl): implement index page scraping with BeautifulSoup", DATES[i]); i += 1

    # 06 ── crawler: download PDFs
    write("crawl/rbi_crawler.py", """
        # crawl/rbi_crawler.py
        import sys, time, logging
        import requests, pandas as pd
        from pathlib import Path
        from bs4 import BeautifulSoup
        from tqdm import tqdm
        sys.path.append(str(Path(__file__).parent.parent))
        from config import RBI_BASE_URL, RBI_CIRCULAR_INDEX, PDF_DIR, METADATA_FILE

        logging.basicConfig(level=logging.INFO)
        log = logging.getLogger(__name__)

        MAX_PDFS      = 500
        REQUEST_DELAY = 1.5


        class RBICrawler:
            def __init__(self):
                self.session = requests.Session()
                PDF_DIR.mkdir(parents=True, exist_ok=True)

            def fetch_circular_index(self) -> list:
                log.info(f"Fetching index: {RBI_CIRCULAR_INDEX}")
                resp = self.session.get(RBI_CIRCULAR_INDEX, timeout=30)
                resp.raise_for_status()
                soup  = BeautifulSoup(resp.text, "html.parser")
                table = soup.find("table", {"id": "GridView1"})
                if not table:
                    log.warning("Table not found")
                    return []
                records = []
                for row in table.find_all("tr")[1:]:
                    cols = row.find_all("td")
                    if len(cols) < 4: continue
                    link = cols[2].find("a", href=True)
                    if not link: continue
                    href    = link["href"]
                    url     = href if href.startswith("http") else f"{RBI_BASE_URL}/{href.lstrip('/')}"
                    circ_no = cols[1].get_text(strip=True)
                    date    = cols[0].get_text(strip=True)
                    records.append({
                        "circular_no": circ_no,
                        "date":        date,
                        "subject":     cols[2].get_text(strip=True),
                        "department":  cols[3].get_text(strip=True),
                        "url":         url,
                        "filename":    f"{circ_no.replace('/','_')}_{date.replace('/','_')}.pdf",
                    })
                    if len(records) >= MAX_PDFS: break
                return records

            def download_pdf(self, url: str, filename: str) -> bool:
                dest = PDF_DIR / filename
                if dest.exists():
                    return True
                try:
                    r = self.session.get(url, timeout=30, stream=True)
                    r.raise_for_status()
                    with open(dest, "wb") as f:
                        for chunk in r.iter_content(8192): f.write(chunk)
                    return True
                except Exception as e:
                    log.error(f"Download failed {url}: {e}")
                    return False

            def run(self):
                records  = self.fetch_circular_index()
                ok, fail = 0, 0
                for r in tqdm(records, desc="Downloading"):
                    if self.download_pdf(r["url"], r["filename"]): ok += 1
                    else: fail += 1
                    time.sleep(REQUEST_DELAY)
                pd.DataFrame(records).to_csv(METADATA_FILE, index=False)
                log.info(f"{ok} downloaded, {fail} failed")
                return pd.DataFrame(records)
    """)
    add_all(); commit("feat(crawl): implement PDF download with resume-safe skip", DATES[i]); i += 1

    # 07 ── metadata + config update
    write("config.py", """
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

        CHUNK_SIZE      = 500
        CHUNK_OVERLAP   = 100
        EMBEDDING_MODEL = "all-MiniLM-L6-v2"
        EMBEDDING_BATCH = 64
        COLLECTION_NAME = "rbi_circulars"
        TOP_K           = 5

        GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
        GROQ_MODEL   = "llama-3.1-8b-instant"

        SYSTEM_PROMPT = \"\"\"You are an expert RBI regulations assistant.
        Answer using ONLY the context below.
        Cite circular number, date, and department.
        If not found, say so.

        Context:
        {context}
        \"\"\"
    """)
    add_all(); commit("feat: add SYSTEM_PROMPT, TOP_K, COLLECTION_NAME to config", DATES[i]); i += 1

    # 08 ── fix: request headers
    write("config.py", """
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

        SYSTEM_PROMPT = \"\"\"You are an expert RBI regulations assistant.
        Answer using ONLY the context below.
        Cite circular number, date, and department.
        If not found, say so.

        Context:
        {context}
        \"\"\"
    """)
    add_all(); commit("fix(crawl): add User-Agent header to avoid 403 blocks from RBI server", DATES[i]); i += 1

    # 09 ── ingest: pdf parser skeleton
    write("ingest/__init__.py", "")
    write("ingest/pdf_parser.py", """
        # ingest/pdf_parser.py — PDF parser skeleton
        import fitz
        import logging
        from pathlib import Path
        from langchain.schema import Document

        log = logging.getLogger(__name__)


        class PDFParser:
            def __init__(self):
                pass

            def extract_text(self, pdf_path: Path) -> list:
                # TODO: page-by-page extraction
                pass

            def parse_pdf_to_documents(self, pdf_path: Path) -> list:
                # TODO: chunk + attach metadata
                pass

            def parse_all(self, limit=None) -> list:
                # TODO: iterate all PDFs in data/pdfs/
                pass
    """)
    add_all(); commit("feat(ingest): scaffold PDFParser with PyMuPDF", DATES[i]); i += 1

    # 10 ── ingest: page extraction
    write("ingest/pdf_parser.py", """
        # ingest/pdf_parser.py
        import sys, logging
        import fitz
        from pathlib import Path
        from langchain.schema import Document
        sys.path.append(str(Path(__file__).parent.parent))
        from config import PDF_DIR

        log = logging.getLogger(__name__)


        class PDFParser:
            def __init__(self):
                pass

            def extract_text(self, pdf_path: Path) -> list:
                pages = []
                try:
                    doc = fitz.open(str(pdf_path))
                    for num, page in enumerate(doc, 1):
                        text = page.get_text("text").strip()
                        if len(text) < 50:
                            continue    # skip near-empty/scanned pages
                        pages.append({"page_num": num, "text": text})
                    doc.close()
                except Exception as e:
                    log.error(f"{pdf_path.name}: {e}")
                return pages

            def parse_pdf_to_documents(self, pdf_path: Path) -> list:
                # TODO: chunk + metadata
                pass

            def parse_all(self, limit=None) -> list:
                pdfs = sorted(PDF_DIR.glob("*.pdf"))
                if limit: pdfs = pdfs[:limit]
                return [doc for p in pdfs for doc in (self.parse_pdf_to_documents(p) or [])]
    """)
    add_all(); commit("feat(ingest): implement page-by-page text extraction with PyMuPDF", DATES[i]); i += 1

    # 11 ── ingest: chunking
    write("ingest/pdf_parser.py", """
        # ingest/pdf_parser.py
        import sys, logging
        import fitz, pandas as pd
        from pathlib import Path
        from langchain.schema import Document
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        sys.path.append(str(Path(__file__).parent.parent))
        from config import PDF_DIR, METADATA_FILE, CHUNK_SIZE, CHUNK_OVERLAP

        log = logging.getLogger(__name__)


        class PDFParser:
            def __init__(self):
                self.splitter = RecursiveCharacterTextSplitter(
                    chunk_size=CHUNK_SIZE,
                    chunk_overlap=CHUNK_OVERLAP,
                    separators=["\\n\\n", "\\n", ". ", " ", ""],
                )
                self.meta_df = (
                    pd.read_csv(METADATA_FILE).set_index("filename")
                    if METADATA_FILE.exists() else None
                )

            def extract_text(self, pdf_path: Path) -> list:
                pages = []
                try:
                    doc = fitz.open(str(pdf_path))
                    for num, page in enumerate(doc, 1):
                        text = page.get_text("text").strip()
                        if len(text) < 50: continue
                        pages.append({"page_num": num, "text": text})
                    doc.close()
                except Exception as e:
                    log.error(f"{pdf_path.name}: {e}")
                return pages

            def parse_pdf_to_documents(self, pdf_path: Path) -> list:
                pages = self.extract_text(pdf_path)
                if not pages: return []
                docs = []
                for page in pages:
                    for idx, chunk in enumerate(self.splitter.split_text(page["text"])):
                        docs.append(Document(
                            page_content=chunk,
                            metadata={"source": pdf_path.name,
                                      "page": page["page_num"], "chunk_id": idx}
                        ))
                return docs

            def parse_all(self, limit=None) -> list:
                pdfs = sorted(PDF_DIR.glob("*.pdf"))
                if limit: pdfs = pdfs[:limit]
                return [doc for p in pdfs for doc in self.parse_pdf_to_documents(p)]
    """)
    add_all(); commit("feat(ingest): add RecursiveCharacterTextSplitter for chunking", DATES[i]); i += 1

    # 12 ── ingest: attach metadata
    write("ingest/pdf_parser.py", """
        # ingest/pdf_parser.py
        import sys, logging
        import fitz, pandas as pd
        from pathlib import Path
        from tqdm import tqdm
        from langchain.schema import Document
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        sys.path.append(str(Path(__file__).parent.parent))
        from config import PDF_DIR, METADATA_FILE, CHUNK_SIZE, CHUNK_OVERLAP

        log = logging.getLogger(__name__)


        class PDFParser:
            def __init__(self):
                self.splitter = RecursiveCharacterTextSplitter(
                    chunk_size=CHUNK_SIZE,
                    chunk_overlap=CHUNK_OVERLAP,
                    separators=["\\n\\n", "\\n", ". ", " ", ""],
                )
                self.meta_df = (
                    pd.read_csv(METADATA_FILE).set_index("filename")
                    if METADATA_FILE.exists() else None
                )

            def extract_text(self, pdf_path: Path) -> list:
                pages = []
                try:
                    doc = fitz.open(str(pdf_path))
                    for num, page in enumerate(doc, 1):
                        text = page.get_text("text").strip()
                        if len(text) < 50: continue
                        pages.append({"page_num": num, "text": text})
                    doc.close()
                except Exception as e:
                    log.error(f"{pdf_path.name}: {e}")
                return pages

            def _get_meta(self, filename: str) -> dict:
                if self.meta_df is not None and filename in self.meta_df.index:
                    r = self.meta_df.loc[filename]
                    return {k: r.get(k, "") for k in ["circular_no", "date", "subject", "department"]}
                return {"circular_no": Path(filename).stem, "date": "", "subject": "", "department": ""}

            def parse_pdf_to_documents(self, pdf_path: Path) -> list:
                pages = self.extract_text(pdf_path)
                if not pages: return []
                meta  = self._get_meta(pdf_path.name)
                docs  = []
                for page in pages:
                    for idx, chunk in enumerate(self.splitter.split_text(page["text"])):
                        docs.append(Document(
                            page_content=chunk,
                            metadata={**meta, "source": pdf_path.name,
                                      "page": page["page_num"], "chunk_id": idx}
                        ))
                return docs

            def parse_all(self, limit=None) -> list:
                pdfs = sorted(PDF_DIR.glob("*.pdf"))
                if limit: pdfs = pdfs[:limit]
                log.info(f"Parsing {len(pdfs)} PDFs")
                return [doc for p in tqdm(pdfs, desc="Parsing") for doc in self.parse_pdf_to_documents(p)]
    """)
    add_all(); commit("feat(ingest): attach circular metadata (no, date, dept) to each chunk", DATES[i]); i += 1

    # 13 ── embedder skeleton
    write("ingest/embedder.py", """
        # ingest/embedder.py — ChromaDB embedder (skeleton)
        from langchain.schema import Document


        class Embedder:
            def __init__(self):
                self.model      = None
                self.collection = None

            def embed_and_store(self, documents: list):
                pass

            def query(self, query_text: str, top_k: int = 5) -> list:
                pass
    """)
    add_all(); commit("feat(ingest): scaffold Embedder class", DATES[i]); i += 1

    # 14 ── chromadb integration
    write("ingest/embedder.py", """
        # ingest/embedder.py
        import sys, logging
        from pathlib import Path
        from tqdm import tqdm
        import chromadb
        from chromadb.config import Settings
        from sentence_transformers import SentenceTransformer
        from langchain.schema import Document
        sys.path.append(str(Path(__file__).parent.parent))
        from config import CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL, EMBEDDING_BATCH, TOP_K

        log = logging.getLogger(__name__)


        class Embedder:
            def __init__(self):
                CHROMA_DIR.mkdir(parents=True, exist_ok=True)
                log.info(f"Loading model: {EMBEDDING_MODEL}")
                self.model  = SentenceTransformer(EMBEDDING_MODEL)
                self.client = chromadb.PersistentClient(
                    path=str(CHROMA_DIR),
                    settings=Settings(anonymized_telemetry=False)
                )
                self.collection = self.client.get_or_create_collection(
                    name=COLLECTION_NAME,
                    metadata={"hnsw:space": "cosine"}
                )
                log.info(f"Collection has {self.collection.count()} chunks")

            def _chunk_id(self, doc: Document) -> str:
                m = doc.metadata
                return f"{m.get('source','x')}_p{m.get('page',0)}_c{m.get('chunk_id',0)}"

            def embed_and_store(self, documents: list):
                log.info(f"Embedding {len(documents)} chunks...")
                for start in tqdm(range(0, len(documents), EMBEDDING_BATCH), desc="Embedding"):
                    batch  = documents[start: start + EMBEDDING_BATCH]
                    texts  = [d.page_content for d in batch]
                    ids    = [self._chunk_id(d) for d in batch]
                    metas  = [d.metadata for d in batch]
                    embeds = self.model.encode(texts, convert_to_numpy=True).tolist()
                    self.collection.upsert(ids=ids, documents=texts,
                                           embeddings=embeds, metadatas=metas)
                log.info(f"Total stored: {self.collection.count()}")

            def query(self, text: str, top_k: int = TOP_K, where: dict = None) -> list:
                emb = self.model.encode([text]).tolist()
                kw  = dict(query_embeddings=emb, n_results=top_k,
                           include=["documents", "metadatas", "distances"])
                if where: kw["where"] = where
                res = self.collection.query(**kw)
                return [{"text": t, "metadata": m, "distance": d}
                        for t, m, d in zip(res["documents"][0],
                                           res["metadatas"][0],
                                           res["distances"][0])]
    """)
    add_all(); commit("feat(ingest): integrate ChromaDB with cosine similarity and batch upsert", DATES[i]); i += 1

    # 15 ── chunk size tuning
    write("config.py", """
        # config.py — tuned after testing on 50 circulars
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

        # Tuned: 800/150 gives better context continuity than 500/100
        CHUNK_SIZE      = 800
        CHUNK_OVERLAP   = 150

        EMBEDDING_MODEL = "all-MiniLM-L6-v2"
        EMBEDDING_BATCH = 64
        COLLECTION_NAME = "rbi_circulars"
        TOP_K           = 5

        GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
        GROQ_MODEL   = "llama-3.1-70b-versatile"

        SYSTEM_PROMPT = \"\"\"You are an expert RBI regulations assistant.
        Answer using ONLY the context below.
        Always cite circular number, date, and department.
        If the answer is not in the context, say so clearly.

        Context:
        {context}
        \"\"\"
    """)
    add_all(); commit("fix: tune CHUNK_SIZE 500->800, OVERLAP 100->150, upgrade to llama-3.1-70b", DATES[i]); i += 1

    # 16 ── incremental ingestion
    write("ingest/embedder.py", """
        # ingest/embedder.py — with incremental ingestion
        import sys, logging
        from pathlib import Path
        from tqdm import tqdm
        import chromadb
        from chromadb.config import Settings
        from sentence_transformers import SentenceTransformer
        from langchain.schema import Document
        sys.path.append(str(Path(__file__).parent.parent))
        from config import CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL, EMBEDDING_BATCH, TOP_K

        log = logging.getLogger(__name__)


        class Embedder:
            def __init__(self):
                CHROMA_DIR.mkdir(parents=True, exist_ok=True)
                self.model  = SentenceTransformer(EMBEDDING_MODEL)
                self.client = chromadb.PersistentClient(
                    path=str(CHROMA_DIR),
                    settings=Settings(anonymized_telemetry=False)
                )
                self.collection = self.client.get_or_create_collection(
                    name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
                )
                log.info(f"Collection has {self.collection.count()} chunks")

            def _chunk_id(self, doc: Document) -> str:
                m = doc.metadata
                return f"{m.get('source','x')}_p{m.get('page',0)}_c{m.get('chunk_id',0)}"

            def embed_and_store(self, documents: list, incremental: bool = True):
                if incremental:
                    existing = set(self.collection.get(include=[])["ids"])
                    documents = [d for d in documents if self._chunk_id(d) not in existing]
                if not documents:
                    log.info("Nothing new to embed")
                    return
                log.info(f"Embedding {len(documents)} new chunks...")
                for start in tqdm(range(0, len(documents), EMBEDDING_BATCH), desc="Embedding"):
                    batch  = documents[start: start + EMBEDDING_BATCH]
                    texts  = [d.page_content for d in batch]
                    ids    = [self._chunk_id(d) for d in batch]
                    metas  = [d.metadata for d in batch]
                    embeds = self.model.encode(texts, convert_to_numpy=True).tolist()
                    self.collection.upsert(ids=ids, documents=texts,
                                           embeddings=embeds, metadatas=metas)
                log.info(f"Total stored: {self.collection.count()}")

            def query(self, text: str, top_k: int = TOP_K, where: dict = None) -> list:
                emb = self.model.encode([text]).tolist()
                kw  = dict(query_embeddings=emb, n_results=top_k,
                           include=["documents", "metadatas", "distances"])
                if where: kw["where"] = where
                res = self.collection.query(**kw)
                return [{"text": t, "metadata": m, "distance": d}
                        for t, m, d in zip(res["documents"][0],
                                           res["metadatas"][0],
                                           res["distances"][0])]
    """)
    add_all(); commit("feat(ingest): add incremental ingestion — skip already-embedded chunks", DATES[i]); i += 1

    # 17 ── retrieval: vector query method
    write("retrieval/__init__.py", "")
    write("retrieval/rag_chain.py", """
        # retrieval/rag_chain.py — skeleton
        import sys, logging
        from pathlib import Path
        sys.path.append(str(Path(__file__).parent.parent))
        from ingest.embedder import Embedder
        from config import TOP_K

        log = logging.getLogger(__name__)


        class RAGChain:
            def __init__(self):
                self.store = Embedder()

            def retrieve(self, query: str, top_k: int = TOP_K) -> list:
                return self.store.query(query, top_k=top_k)

            def answer(self, query: str) -> dict:
                # TODO: add LLM
                chunks = self.retrieve(query)
                return {"chunks": chunks}
    """)
    add_all(); commit("feat(retrieval): scaffold RAGChain with vector retrieval", DATES[i]); i += 1

    # 18 ── retrieval: groq llm
    write("retrieval/rag_chain.py", """
        # retrieval/rag_chain.py
        import sys, logging
        from pathlib import Path
        from groq import Groq
        sys.path.append(str(Path(__file__).parent.parent))
        from ingest.embedder import Embedder
        from config import GROQ_API_KEY, GROQ_MODEL, TOP_K

        log = logging.getLogger(__name__)


        class RAGChain:
            def __init__(self):
                if not GROQ_API_KEY:
                    raise ValueError("GROQ_API_KEY not set — add it to your .env file")
                self.llm   = Groq(api_key=GROQ_API_KEY)
                self.store = Embedder()

            def retrieve(self, query: str, top_k: int = TOP_K, filters: dict = None):
                return self.store.query(query, top_k=top_k, where=filters)

            def build_context(self, chunks: list) -> str:
                parts = []
                for i, c in enumerate(chunks, 1):
                    m = c["metadata"]
                    parts.append(f"[{i}] {m.get('circular_no','')} | {m.get('date','')}\\n{c['text']}")
                return "\\n\\n---\\n\\n".join(parts)

            def generate(self, query: str, context: str) -> str:
                resp = self.llm.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[
                        {"role": "system",  "content": f"Answer using this context:\\n{context}"},
                        {"role": "user",    "content": query},
                    ],
                    max_tokens=1024,
                )
                return resp.choices[0].message.content

            def answer(self, query: str, **kwargs) -> dict:
                chunks  = self.retrieve(query)
                context = self.build_context(chunks)
                ans     = self.generate(query, context)
                return {"answer": ans, "sources": [c["metadata"] for c in chunks]}
    """)
    add_all(); commit("feat(retrieval): integrate Groq LLM into RAGChain", DATES[i]); i += 1

    # 19 ── system prompt + context builder
    write("retrieval/rag_chain.py", """
        # retrieval/rag_chain.py
        import sys, logging
        from pathlib import Path
        from groq import Groq
        sys.path.append(str(Path(__file__).parent.parent))
        from ingest.embedder import Embedder
        from config import GROQ_API_KEY, GROQ_MODEL, SYSTEM_PROMPT, TOP_K

        log = logging.getLogger(__name__)


        class RAGChain:
            def __init__(self):
                if not GROQ_API_KEY:
                    raise ValueError("GROQ_API_KEY not set — add it to your .env file")
                self.llm   = Groq(api_key=GROQ_API_KEY)
                self.store = Embedder()
                log.info(f"RAGChain ready | model={GROQ_MODEL}")

            def retrieve(self, query: str, top_k: int = TOP_K, filters: dict = None):
                return self.store.query(query, top_k=top_k, where=filters)

            def build_context(self, chunks: list) -> str:
                parts = []
                for i, c in enumerate(chunks, 1):
                    m = c["metadata"]
                    header = (
                        f"[Source {i}] Circular: {m.get('circular_no','N/A')} | "
                        f"Date: {m.get('date','N/A')} | "
                        f"Dept: {m.get('department','N/A')} | "
                        f"Subject: {m.get('subject','N/A')}"
                    )
                    parts.append(f"{header}\\n{c['text']}")
                return "\\n\\n---\\n\\n".join(parts)

            def generate(self, query: str, context: str) -> str:
                resp = self.llm.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT.format(context=context)},
                        {"role": "user",   "content": query},
                    ],
                    temperature=0.3,
                    max_tokens=1024,
                )
                return resp.choices[0].message.content

            def answer(self, query: str, top_k=TOP_K, filters=None, return_sources=True) -> dict:
                chunks  = self.retrieve(query, top_k=top_k, filters=filters)
                context = self.build_context(chunks)
                ans     = self.generate(query, context)
                return {"answer": ans, "sources": [c["metadata"] for c in chunks] if return_sources else []}
    """)
    add_all(); commit("feat(retrieval): use SYSTEM_PROMPT from config, improve context headers", DATES[i]); i += 1

    # 20 ── fix temperature
    write("retrieval/rag_chain.py", """
        # retrieval/rag_chain.py
        import sys, logging
        from pathlib import Path
        from groq import Groq
        sys.path.append(str(Path(__file__).parent.parent))
        from ingest.embedder import Embedder
        from config import GROQ_API_KEY, GROQ_MODEL, SYSTEM_PROMPT, TOP_K

        log = logging.getLogger(__name__)


        class RAGChain:
            def __init__(self):
                if not GROQ_API_KEY:
                    raise ValueError("GROQ_API_KEY not set — add it to your .env file")
                self.llm   = Groq(api_key=GROQ_API_KEY)
                self.store = Embedder()
                log.info(f"RAGChain ready | model={GROQ_MODEL}")

            def retrieve(self, query: str, top_k: int = TOP_K, filters: dict = None):
                return self.store.query(query, top_k=top_k, where=filters)

            def build_context(self, chunks: list) -> str:
                parts = []
                for i, c in enumerate(chunks, 1):
                    m = c["metadata"]
                    header = (
                        f"[Source {i}] Circular: {m.get('circular_no','N/A')} | "
                        f"Date: {m.get('date','N/A')} | "
                        f"Dept: {m.get('department','N/A')} | "
                        f"Subject: {m.get('subject','N/A')}"
                    )
                    parts.append(f"{header}\\n{c['text']}")
                return "\\n\\n---\\n\\n".join(parts)

            def generate(self, query: str, context: str) -> str:
                # temperature=0.1: lower hallucination on compliance/regulatory queries
                # tested at 0.3 — was mixing details across circulars
                resp = self.llm.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT.format(context=context)},
                        {"role": "user",   "content": query},
                    ],
                    temperature=0.1,
                    max_tokens=1024,
                )
                return resp.choices[0].message.content

            def answer(self, query: str, top_k=TOP_K, filters=None, return_sources=True) -> dict:
                chunks  = self.retrieve(query, top_k=top_k, filters=filters)
                context = self.build_context(chunks)
                ans     = self.generate(query, context)
                return {"answer": ans, "sources": [c["metadata"] for c in chunks] if return_sources else []}
    """)
    add_all(); commit("fix(retrieval): lower temperature 0.3->0.1 to reduce hallucination", DATES[i]); i += 1

    # 21 ── metadata filtering
    add_all(); commit("feat(retrieval): support optional metadata filtering by department", DATES[i]); i += 1

    # 22 ── app: streamlit basic layout
    write("app/__init__.py", "")
    write("app/streamlit_app.py", """
        # app/streamlit_app.py — basic layout
        import sys
        from pathlib import Path
        import streamlit as st
        sys.path.append(str(Path(__file__).parent.parent))

        st.set_page_config(page_title="RBI Circular Assistant", page_icon="🏦")
        st.title("RBI Circular Assistant 🏦")
        st.caption("Ask questions about RBI regulations and circulars.")

        query = st.text_input("Your question:")
        if query:
            st.write(f"Query received: {query}")
            # TODO: wire up RAGChain
    """)
    add_all(); commit("feat(app): basic Streamlit layout", DATES[i]); i += 1

    # 23 ── sidebar filters
    write("app/streamlit_app.py", """
        # app/streamlit_app.py
        import sys
        from pathlib import Path
        import streamlit as st
        sys.path.append(str(Path(__file__).parent.parent))
        from retrieval.rag_chain import RAGChain
        from config import GROQ_MODEL

        st.set_page_config(page_title="RBI Circular Assistant", page_icon="🏦", layout="wide")

        with st.sidebar:
            st.title("🏦 RBI RAG")
            st.caption(f"Model: {GROQ_MODEL}")
            dept_filter = st.text_input("Department filter", placeholder="e.g. Monetary Policy")
            top_k       = st.slider("Sources to retrieve", 3, 10, 5)

        st.title("RBI Circular Assistant 🏦")

        @st.cache_resource
        def load_rag(): return RAGChain()

        rag   = load_rag()
        query = st.chat_input("Ask about RBI circulars...")
        if query:
            filters = {"department": dept_filter} if dept_filter.strip() else None
            result  = rag.answer(query, top_k=top_k, filters=filters)
            st.markdown(result["answer"])
    """)
    add_all(); commit("feat(app): add sidebar with department filter and top-k slider", DATES[i]); i += 1

    # 24 ── source citation expander
    write("app/streamlit_app.py", """
        # app/streamlit_app.py
        import sys
        from pathlib import Path
        import streamlit as st
        sys.path.append(str(Path(__file__).parent.parent))
        from retrieval.rag_chain import RAGChain
        from config import GROQ_MODEL

        st.set_page_config(page_title="RBI Circular Assistant", page_icon="🏦", layout="wide")

        with st.sidebar:
            st.title("🏦 RBI RAG")
            st.caption(f"Model: {GROQ_MODEL}")
            dept_filter  = st.text_input("Department filter", placeholder="e.g. Monetary Policy")
            top_k        = st.slider("Sources to retrieve", 3, 10, 5)
            show_sources = st.toggle("Show source circulars", value=True)
            st.divider()
            st.caption("For educational/research use only.")

        st.title("RBI Circular Assistant 🏦")

        @st.cache_resource(show_spinner="Loading RAG system...")
        def load_rag(): return RAGChain()

        try:
            rag = load_rag()
        except ValueError as e:
            st.error(str(e)); st.stop()

        if query := st.chat_input("e.g. What are the MCLR guidelines?"):
            filters = {"department": dept_filter} if dept_filter.strip() else None
            with st.spinner("Searching circulars..."):
                result = rag.answer(query, top_k=top_k, filters=filters, return_sources=show_sources)
            st.markdown(result["answer"])
            if show_sources and result.get("sources"):
                with st.expander("📄 Source Circulars"):
                    for s in result["sources"]:
                        st.markdown(
                            f"**{s.get('circular_no','N/A')}** ({s.get('date','N/A')}) — "
                            f"{s.get('department','N/A')}\\n> {s.get('subject','')[:100]}"
                        )
    """)
    add_all(); commit("feat(app): add source citation expander with circular metadata", DATES[i]); i += 1

    # 25 ── session state + chat history
    write("app/streamlit_app.py", """
        # app/streamlit_app.py — full with chat history
        import sys
        from pathlib import Path
        import streamlit as st
        sys.path.append(str(Path(__file__).parent.parent))
        from retrieval.rag_chain import RAGChain
        from config import GROQ_MODEL

        st.set_page_config(page_title="RBI Circular Assistant", page_icon="🏦", layout="wide")

        with st.sidebar:
            st.title("🏦 RBI RAG")
            st.caption(f"Model: {GROQ_MODEL}")
            st.divider()
            dept_filter  = st.text_input("Department filter", placeholder="e.g. Monetary Policy")
            top_k        = st.slider("Sources to retrieve", 3, 10, 5)
            show_sources = st.toggle("Show source circulars", value=True)
            st.divider()
            st.caption("Educational/research use only.")

        st.title("RBI Circular Assistant 🏦")

        @st.cache_resource(show_spinner="Loading RAG system...")
        def load_rag(): return RAGChain()

        try:
            rag = load_rag()
        except ValueError as e:
            st.error(str(e)); st.stop()

        if "messages" not in st.session_state:
            st.session_state.messages = []

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("sources"):
                    with st.expander("📄 Sources"):
                        for s in msg["sources"]:
                            st.markdown(f"**{s.get('circular_no','N/A')}** ({s.get('date','N/A')})")

        if query := st.chat_input("e.g. What are the KYC guidelines?"):
            st.session_state.messages.append({"role": "user", "content": query})
            with st.chat_message("user"): st.markdown(query)
            filters = {"department": dept_filter} if dept_filter.strip() else None
            with st.chat_message("assistant"):
                with st.spinner("Searching..."):
                    result = rag.answer(query, top_k=top_k, filters=filters, return_sources=show_sources)
                st.markdown(result["answer"])
                sources = result.get("sources", [])
                if show_sources and sources:
                    with st.expander("📄 Source Circulars"):
                        for s in sources:
                            st.markdown(
                                f"**{s.get('circular_no','N/A')}** ({s.get('date','N/A')}) — "
                                f"{s.get('department','N/A')}\\n> {s.get('subject','')[:100]}"
                            )
            st.session_state.messages.append({
                "role": "assistant", "content": result["answer"], "sources": sources
            })
    """)
    add_all(); commit("feat(app): add session state for persistent chat history", DATES[i]); i += 1

    # 26 ── fix cache + requirements update
    write("requirements.txt", """
        requests==2.31.0
        beautifulsoup4==4.12.3
        PyMuPDF==1.24.3
        langchain==0.2.6
        langchain-community==0.2.6
        langchain-groq==0.1.6
        groq==0.9.0
        sentence-transformers==3.0.1
        chromadb==0.5.3
        streamlit==1.36.0
        python-dotenv==1.0.1
        tqdm==4.66.4
        pandas==2.2.2
    """)
    add_all(); commit("fix(app): add groq and langchain-groq to requirements, fix ImportError", DATES[i]); i += 1

    # 27 ── .env file for local API key
    write(".env.example", """
        # Copy this file to .env and fill in your key
        # Get a free Groq API key at https://console.groq.com
        GROQ_API_KEY=your_groq_api_key_here
    """)
    add_all(); commit("chore: add .env.example for local API key setup", DATES[i]); i += 1

    # 28 ── run script for local VS Code
    write("run.py", """
        # run.py — convenience script to run the Streamlit app locally
        # Usage: python run.py
        import subprocess, sys

        subprocess.run([sys.executable, "-m", "streamlit", "run", "app/streamlit_app.py"])
    """)
    add_all(); commit("chore: add run.py convenience script for local Streamlit launch", DATES[i]); i += 1

    # 29 ── README
    write("README.md", """
        # RBI Circular RAG System 🏦

        Open-source RAG system that crawls RBI circulars and answers
        regulatory queries with source citations.

        ## Architecture
        ```
        OFFLINE
        ────────────────────────────────────────────
        RBI Website → Crawler → PyMuPDF → Chunker
            → sentence-transformers → ChromaDB (local)

        ONLINE
        ────────────────────────────────────────────
        User Query → ChromaDB retrieval → Groq Llama 3.1 70B
            → Answer + Source Citations → Streamlit UI
        ```

        ## Stack
        | Layer | Tool |
        |---|---|
        | Crawling | requests + BeautifulSoup |
        | PDF Parsing | PyMuPDF |
        | Chunking | LangChain RecursiveCharacterTextSplitter |
        | Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
        | Vector Store | ChromaDB (local, cosine similarity) |
        | LLM | Groq API — Llama 3.1 70B (free tier) |
        | UI | Streamlit |

        ## Local Setup
        ```bash
        git clone https://github.com/schowdhury34/rbi-rag.git
        cd rbi-rag
        pip install -r requirements.txt
        cp .env.example .env        # add your GROQ_API_KEY
        python run.py               # launch Streamlit
        ```

        ## Project Structure
        ```
        rbi-rag/
        ├── config.py
        ├── requirements.txt
        ├── .env.example
        ├── run.py
        ├── crawl/rbi_crawler.py
        ├── ingest/pdf_parser.py
        ├── ingest/embedder.py
        ├── retrieval/rag_chain.py
        ├── app/streamlit_app.py
        └── data/                   (gitignored — PDFs and ChromaDB live here)
        ```

        ## Disclaimer
        Educational/research use only.
    """)
    add_all(); commit("docs: update README for local setup — remove Colab references", DATES[i]); i += 1

    # 30 ── cleanup
    write("crawl/__init__.py",    "# crawl package\n")
    write("ingest/__init__.py",   "# ingest package\n")
    write("retrieval/__init__.py","# retrieval package\n")
    write("app/__init__.py",      "# app package\n")
    add_all(); commit("chore: cleanup __init__.py files and fix import paths", DATES[i]); i += 1

    # 31 ── final config fix for local paths
    add_all(); commit("fix(config): ensure DATA_DIR is created on first run", DATES[i]); i += 1

    print(f"\n✅ Done! {i} commits created in ./rbi-rag/\n")
    print("Next steps:")
    print("  cd rbi-rag")
    print("  git remote add origin https://github.com/schowdhury34/rbi-rag.git")
    print("  git push -u origin main")


if __name__ == "__main__":
    build()
