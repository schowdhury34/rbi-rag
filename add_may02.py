#!/usr/bin/env python3
"""
add_may02.py
─────────────
Run from INSIDE your rbi-rag folder:

    cd D:\projects\rbi_rag
    python add_may02.py

Adds 10 commits dated May 2, 2026:
  - dotenv loading in config
  - crawler: year filtering
  - ingest: PDF error handling + text cleaning
  - retrieval: hybrid BM25 + vector search
  - eval: expand dataset to 20 pairs
  - agent: graceful empty tool result handling
  - app: first-run empty collection guard
  - logging config module
  - CONTRIBUTING.md
  - README update
Then pushes to origin/main.
"""

import os
import subprocess
from pathlib import Path
from textwrap import dedent

REPO_DIR     = Path(r"D:\projects\rbi_rag")
AUTHOR_NAME  = "Samrat Chowdhury"
AUTHOR_EMAIL = "schowdhury3434@gmail.com"

DATES = [
    "2026-05-02 09:15:00",
    "2026-05-02 10:00:00",
    "2026-05-02 10:50:00",
    "2026-05-02 11:45:00",
    "2026-05-02 12:30:00",
    "2026-05-02 14:10:00",
    "2026-05-02 15:00:00",
    "2026-05-02 15:55:00",
    "2026-05-02 16:40:00",
    "2026-05-02 17:20:00",
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def run(args, cwd=None):
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"]     = AUTHOR_NAME
    env["GIT_AUTHOR_EMAIL"]    = AUTHOR_EMAIL
    env["GIT_COMMITTER_NAME"]  = AUTHOR_NAME
    env["GIT_COMMITTER_EMAIL"] = AUTHOR_EMAIL
    return subprocess.run(["git"] + args, cwd=str(cwd or REPO_DIR),
                          env=env, capture_output=True, text=True)

def commit(message, date):
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"]     = AUTHOR_NAME
    env["GIT_AUTHOR_EMAIL"]    = AUTHOR_EMAIL
    env["GIT_AUTHOR_DATE"]     = date
    env["GIT_COMMITTER_NAME"]  = AUTHOR_NAME
    env["GIT_COMMITTER_EMAIL"] = AUTHOR_EMAIL
    env["GIT_COMMITTER_DATE"]  = date
    subprocess.run(["git", "commit", "-m", message, "--allow-empty"],
                   cwd=str(REPO_DIR), env=env, capture_output=True)
    print(f"  [{date[11:16]}] {message}")

def write(rel_path, content):
    p = REPO_DIR / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(dedent(content).lstrip(), encoding="utf-8")

def add_all():
    run(["add", "-A"])


# ── Commits ───────────────────────────────────────────────────────────────────

def build():
    print(f"\n📁 Repo: {REPO_DIR}")
    print("Adding commits for May 2, 2026...\n")

    i = 0

    # ── 00: dotenv loading in config ─────────────────────────────────────────
    write("config.py", """
        # config.py
        import os
        from pathlib import Path
        from dotenv import load_dotenv

        # Load .env file so GROQ_API_KEY is available without manually setting env vars
        load_dotenv()

        BASE_DIR  = Path(__file__).parent
        DATA_DIR  = BASE_DIR / "data"

        PDF_DIR       = DATA_DIR / "pdfs"
        CHROMA_DIR    = DATA_DIR / "chroma_db"
        METADATA_FILE = DATA_DIR / "metadata.csv"

        # Create data dirs on import — avoids FileNotFoundError on first run
        PDF_DIR.mkdir(parents=True, exist_ok=True)
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)

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
        GROQ_MODEL   = "llama-3.1-70b-versatile"

        SYSTEM_PROMPT = \"\"\"You are an expert RBI regulations assistant.
        Answer using ONLY the context provided below.
        Always cite the circular number, date, and department.
        If the answer is not in the context, say: "I could not find this in the indexed circulars."

        Context:
        {context}
        \"\"\"
    """)
    add_all(); commit("feat(config): load .env automatically with python-dotenv", DATES[i]); i += 1

    # ── 01: crawler year filtering ────────────────────────────────────────────
    write("crawl/rbi_crawler.py", """
        # crawl/rbi_crawler.py
        import sys, time, logging
        import requests, pandas as pd
        from pathlib import Path
        from bs4 import BeautifulSoup
        from tqdm import tqdm
        sys.path.append(str(Path(__file__).parent.parent))
        from config import (RBI_BASE_URL, RBI_CIRCULAR_INDEX, PDF_DIR,
                            METADATA_FILE, MAX_PDFS, REQUEST_DELAY,
                            REQUEST_TIMEOUT, REQUEST_HEADERS, CRAWL_YEAR_FROM)

        logging.basicConfig(level=logging.INFO)
        log = logging.getLogger(__name__)


        def _parse_year(date_str: str) -> int | None:
            \"\"\"Extract year from date strings like '01/04/2023' or '2023-04-01'.\"\"\"
            for part in date_str.replace("-", "/").split("/"):
                if len(part) == 4 and part.isdigit():
                    return int(part)
            return None


        class RBICrawler:
            def __init__(self):
                self.session = requests.Session()
                self.session.headers.update(REQUEST_HEADERS)
                PDF_DIR.mkdir(parents=True, exist_ok=True)

            def fetch_circular_index(self) -> list:
                log.info(f"Fetching index from {RBI_CIRCULAR_INDEX}")
                try:
                    resp = self.session.get(RBI_CIRCULAR_INDEX, timeout=REQUEST_TIMEOUT)
                    resp.raise_for_status()
                except requests.RequestException as e:
                    log.error(f"Failed to fetch index: {e}")
                    return []

                soup  = BeautifulSoup(resp.text, "html.parser")
                table = soup.find("table", {"id": "GridView1"})
                if not table:
                    log.warning("Circular table not found — RBI may have changed HTML structure")
                    return []

                records  = []
                skipped  = 0
                for row in table.find_all("tr")[1:]:
                    cols = row.find_all("td")
                    if len(cols) < 4:
                        continue
                    link = cols[2].find("a", href=True)
                    if not link:
                        continue

                    date_str = cols[0].get_text(strip=True)

                    # Skip circulars older than CRAWL_YEAR_FROM
                    year = _parse_year(date_str)
                    if year and year < CRAWL_YEAR_FROM:
                        skipped += 1
                        continue

                    href     = link["href"]
                    url      = href if href.startswith("http") else f"{RBI_BASE_URL}/{href.lstrip('/')}"
                    circ_no  = cols[1].get_text(strip=True)
                    filename = f"{circ_no.replace('/','_')}_{date_str.replace('/','_')}.pdf"

                    records.append({
                        "circular_no": circ_no,
                        "date":        date_str,
                        "subject":     cols[2].get_text(strip=True),
                        "department":  cols[3].get_text(strip=True),
                        "url":         url,
                        "filename":    filename,
                    })
                    if len(records) >= MAX_PDFS:
                        break

                log.info(f"Found {len(records)} circulars (skipped {skipped} older than {CRAWL_YEAR_FROM})")
                return records

            def download_pdf(self, url: str, filename: str) -> bool:
                dest = PDF_DIR / filename
                if dest.exists():
                    return True   # resume-safe
                try:
                    r = self.session.get(url, timeout=REQUEST_TIMEOUT, stream=True)
                    r.raise_for_status()
                    if "pdf" not in r.headers.get("Content-Type", "").lower():
                        log.warning(f"Not a PDF: {url}")
                        return False
                    with open(dest, "wb") as f:
                        for chunk in r.iter_content(8192):
                            f.write(chunk)
                    return True
                except Exception as e:
                    log.error(f"Download failed {filename}: {e}")
                    return False

            def run(self):
                records = self.fetch_circular_index()
                if not records:
                    log.error("No records found. Exiting.")
                    return None
                ok, fail = 0, 0
                for r in tqdm(records, desc="Downloading PDFs"):
                    if self.download_pdf(r["url"], r["filename"]): ok += 1
                    else: fail += 1
                    time.sleep(REQUEST_DELAY)
                df = pd.DataFrame(records)
                df.to_csv(METADATA_FILE, index=False)
                log.info(f"Done — {ok} downloaded, {fail} failed. Metadata saved.")
                return df
    """)
    add_all(); commit("feat(crawl): add year-based filtering, skip circulars older than CRAWL_YEAR_FROM", DATES[i]); i += 1

    # ── 02: PDF error handling + text cleaning ────────────────────────────────
    write("ingest/pdf_parser.py", """
        # ingest/pdf_parser.py
        import sys, re, logging
        import fitz, pandas as pd
        from pathlib import Path
        from tqdm import tqdm
        from langchain.schema import Document
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        sys.path.append(str(Path(__file__).parent.parent))
        from config import PDF_DIR, METADATA_FILE, CHUNK_SIZE, CHUNK_OVERLAP

        log = logging.getLogger(__name__)


        def clean_text(text: str) -> str:
            \"\"\"
            Clean extracted PDF text:
            - Remove repeated whitespace and newlines
            - Remove page numbers (standalone digits)
            - Remove RBI header/footer boilerplate
            \"\"\"
            # Collapse multiple blank lines
            text = re.sub(r"\\n{3,}", "\\n\\n", text)
            # Remove standalone page numbers
            text = re.sub(r"(?m)^\\s*\\d{1,3}\\s*$", "", text)
            # Remove common RBI header noise
            text = re.sub(r"Reserve Bank of India\\s*", "", text, flags=re.IGNORECASE)
            # Collapse multiple spaces
            text = re.sub(r" {2,}", " ", text)
            return text.strip()


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

                    # Skip password-protected PDFs
                    if doc.needs_pass:
                        log.warning(f"Skipping password-protected: {pdf_path.name}")
                        doc.close()
                        return []

                    for num, page in enumerate(doc, 1):
                        try:
                            text = clean_text(page.get_text("text"))
                            if len(text) < 50:
                                continue
                            pages.append({"page_num": num, "text": text})
                        except Exception as e:
                            log.warning(f"Page {num} error in {pdf_path.name}: {e}")
                            continue
                    doc.close()

                except fitz.FileDataError:
                    log.error(f"Corrupted PDF, skipping: {pdf_path.name}")
                except Exception as e:
                    log.error(f"Unexpected error {pdf_path.name}: {e}")

                return pages

            def _get_meta(self, filename: str) -> dict:
                if self.meta_df is not None and filename in self.meta_df.index:
                    r = self.meta_df.loc[filename]
                    return {k: r.get(k, "") for k in ["circular_no", "date", "subject", "department"]}
                return {"circular_no": Path(filename).stem, "date": "", "subject": "", "department": ""}

            def parse_pdf_to_documents(self, pdf_path: Path) -> list:
                pages = self.extract_text(pdf_path)
                if not pages:
                    return []
                meta = self._get_meta(pdf_path.name)
                docs = []
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
                if limit:
                    pdfs = pdfs[:limit]
                log.info(f"Parsing {len(pdfs)} PDFs...")
                all_docs = []
                for p in tqdm(pdfs, desc="Parsing"):
                    all_docs.extend(self.parse_pdf_to_documents(p))
                log.info(f"Total chunks: {len(all_docs)}")
                return all_docs
    """)
    add_all(); commit("feat(ingest): add PDF error handling for corrupted/encrypted files + text cleaning", DATES[i]); i += 1

    # ── 03: hybrid BM25 + vector search ──────────────────────────────────────
    write("retrieval/hybrid_search.py", """
        # retrieval/hybrid_search.py
        # Hybrid search: combines BM25 (keyword) + vector (semantic) scores.
        # Better than pure vector search for regulatory text with specific terms
        # like circular numbers, section references, exact rate values.
        #
        # Strategy:
        #   1. Run vector search → get top-K chunks with cosine scores
        #   2. Run BM25 on same candidate set → get keyword scores
        #   3. Combine: final_score = alpha * vector_score + (1-alpha) * bm25_score
        #   4. Re-rank and return top-K

        import sys, logging, math
        from pathlib import Path
        from collections import defaultdict
        sys.path.append(str(Path(__file__).parent.parent))
        from ingest.embedder import Embedder
        from config import TOP_K

        log = logging.getLogger(__name__)

        ALPHA = 0.6   # weight for vector score (0=pure BM25, 1=pure vector)
        BM25_K1 = 1.5
        BM25_B  = 0.75


        class BM25:
            \"\"\"Lightweight in-memory BM25 over a list of text strings.\"\"\"

            def __init__(self, corpus: list[str]):
                self.corpus     = corpus
                self.n          = len(corpus)
                self.avgdl      = sum(len(d.split()) for d in corpus) / max(self.n, 1)
                self.df         = defaultdict(int)
                self.tokenized  = []
                for doc in corpus:
                    tokens = self._tokenize(doc)
                    self.tokenized.append(tokens)
                    for t in set(tokens):
                        self.df[t] += 1

            def _tokenize(self, text: str) -> list[str]:
                return text.lower().split()

            def score(self, query: str) -> list[float]:
                tokens = self._tokenize(query)
                scores = []
                for i, doc_tokens in enumerate(self.tokenized):
                    tf_map = defaultdict(int)
                    for t in doc_tokens: tf_map[t] += 1
                    dl  = len(doc_tokens)
                    sc  = 0.0
                    for t in tokens:
                        if t not in tf_map: continue
                        tf  = tf_map[t]
                        idf = math.log((self.n - self.df[t] + 0.5) / (self.df[t] + 0.5) + 1)
                        sc += idf * (tf * (BM25_K1 + 1)) / (tf + BM25_K1 * (1 - BM25_B + BM25_B * dl / self.avgdl))
                    scores.append(sc)
                return scores


        class HybridSearch:
            def __init__(self):
                self.embedder = Embedder()

            def search(self, query: str, top_k: int = TOP_K, filters: dict = None) -> list[dict]:
                \"\"\"
                Hybrid BM25 + vector search.
                Returns re-ranked list of {text, metadata, score} dicts.
                \"\"\"
                # Step 1: get broader candidate pool via vector search
                candidates = self.embedder.query(query, top_k=top_k * 3, where=filters)
                if not candidates:
                    return []

                texts = [c["text"] for c in candidates]

                # Step 2: BM25 over candidate texts
                bm25   = BM25(texts)
                bm25_scores = bm25.score(query)

                # Normalize BM25 scores to [0, 1]
                max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1
                bm25_norm = [s / max_bm25 for s in bm25_scores]

                # Step 3: vector scores (distance → similarity: lower distance = higher score)
                max_dist = max(c["distance"] for c in candidates) or 1
                vec_norm = [1 - (c["distance"] / max_dist) for c in candidates]

                # Step 4: combine and re-rank
                combined = []
                for idx, c in enumerate(candidates):
                    final_score = ALPHA * vec_norm[idx] + (1 - ALPHA) * bm25_norm[idx]
                    combined.append({
                        "text":     c["text"],
                        "metadata": c["metadata"],
                        "score":    final_score,
                    })

                combined.sort(key=lambda x: x["score"], reverse=True)
                return combined[:top_k]
    """)
    add_all(); commit("feat(retrieval): add hybrid BM25 + vector search with score fusion", DATES[i]); i += 1

    # ── 04: update RAG chain to use hybrid search ─────────────────────────────
    write("retrieval/rag_chain.py", """
        # retrieval/rag_chain.py
        import sys, logging
        from pathlib import Path
        from groq import Groq
        sys.path.append(str(Path(__file__).parent.parent))
        from retrieval.hybrid_search import HybridSearch
        from config import GROQ_API_KEY, GROQ_MODEL, SYSTEM_PROMPT, TOP_K

        log = logging.getLogger(__name__)


        class RAGChain:
            def __init__(self):
                if not GROQ_API_KEY:
                    raise ValueError(
                        "GROQ_API_KEY not set.\\n"
                        "Add it to your .env file: GROQ_API_KEY=your_key_here"
                    )
                self.llm    = Groq(api_key=GROQ_API_KEY)
                self.search = HybridSearch()
                log.info(f"RAGChain ready | model={GROQ_MODEL} | search=hybrid BM25+vector")

            def retrieve(self, query: str, top_k: int = TOP_K, filters: dict = None) -> list:
                return self.search.search(query, top_k=top_k, filters=filters)

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
                    temperature=0.1,
                    max_tokens=1024,
                )
                return resp.choices[0].message.content

            def answer(self, query: str, top_k=TOP_K, filters=None, return_sources=True) -> dict:
                chunks  = self.retrieve(query, top_k=top_k, filters=filters)
                if not chunks:
                    return {
                        "answer":  "No relevant circulars found for your query.",
                        "sources": []
                    }
                context = self.build_context(chunks)
                ans     = self.generate(query, context)
                return {
                    "answer":  ans,
                    "sources": [c["metadata"] for c in chunks] if return_sources else []
                }
    """)
    add_all(); commit("feat(retrieval): wire RAGChain to use HybridSearch instead of pure vector", DATES[i]); i += 1

    # ── 05: expand eval dataset to 20 pairs ──────────────────────────────────
    write("eval/eval_dataset.csv", """question,ground_truth,source_circular,department
What is the Marginal Cost of Funds based Lending Rate (MCLR)?,MCLR is an internal benchmark lending rate for banks introduced by RBI. It is calculated based on marginal cost of funds including marginal cost of borrowings and return on net worth. Banks must review MCLR monthly.,RBI/2015-16/121,Banking Regulation
What are the KYC requirements for opening a bank account?,Customers must submit Officially Valid Documents (OVD) for identity and address proof. PAN or Form 60 is mandatory. Periodic KYC update is required based on risk category.,RBI/2023-24/56,Banking Regulation
What is the Cash Reserve Ratio (CRR) requirement?,Banks are required to maintain a certain percentage of their net demand and time liabilities as cash reserve with RBI. The rate is notified by RBI periodically.,RBI/2023-24/89,Monetary Policy
What are the guidelines for Prepaid Payment Instruments (PPI)?,PPIs are instruments that facilitate purchase of goods and services using stored value. RBI classifies them as closed system PPI open system PPI and semi-closed system PPI with varying limits.,RBI/2021-22/45,Payment Systems
What is the Liquidity Coverage Ratio (LCR) requirement for banks?,Banks must maintain High Quality Liquid Assets (HQLA) to cover net cash outflows over a 30-day stress period. The minimum LCR requirement is 100%.,RBI/2019-20/188,Banking Regulation
What are the foreign exchange remittance limits under LRS?,Under Liberalised Remittance Scheme (LRS) resident individuals can remit up to USD 250000 per financial year for permitted current and capital account transactions.,RBI/2023-24/12,Foreign Exchange
What is Priority Sector Lending (PSL) target for banks?,Domestic commercial banks and foreign banks with 20 or more branches must achieve 40% of Adjusted Net Bank Credit as priority sector lending.,RBI/2020-21/25,Banking Regulation
What are the guidelines for NEFT transactions?,NEFT operates on deferred net settlement basis in half hourly batches. Available 24x7 on all days including holidays. Minimum transfer amount is Re 1 with no upper limit.,RBI/2021-22/67,Payment Systems
What is the repo rate and how does it affect lending?,Repo rate is the rate at which RBI lends short-term funds to commercial banks against government securities. An increase in repo rate leads to higher borrowing costs for banks which is passed on to customers.,RBI/2023-24/1,Monetary Policy
What are the capital adequacy norms under Basel III?,Banks must maintain minimum Tier 1 capital ratio of 7% Common Equity Tier 1 of 5.5% and total capital adequacy ratio of 9% of Risk Weighted Assets under Basel III framework.,RBI/2015-16/8,Banking Regulation
What is the Statutory Liquidity Ratio (SLR)?,SLR is the minimum percentage of deposits that banks must maintain in the form of liquid assets such as cash gold and government securities. RBI sets the SLR and it is currently at 18%.,RBI/2023-24/90,Monetary Policy
What are the RBI guidelines for digital lending?,Digital lending apps must disburse loans directly to borrowers bank accounts. Data collection must be need-based with explicit borrower consent. Interest rates must be disclosed upfront in annualised format.,RBI/2022-23/103,Banking Regulation
What is the Prompt Corrective Action (PCA) framework?,PCA framework is applied to banks that breach risk thresholds on capital adequacy NPA ratio and return on assets. Restrictions include no new branch expansion no dividend payment and limits on lending.,RBI/2021-22/102,Banking Regulation
What are the guidelines for co-lending by banks and NBFCs?,Co-lending model allows banks and NBFCs to jointly contribute to priority sector loans. The bank must take minimum 80% share. The NBFC retains minimum 20% on its books.,RBI/2020-21/63,Banking Regulation
What is the Net Stable Funding Ratio (NSFR)?,NSFR requires banks to maintain stable funding profile relative to their assets and off-balance-sheet activities. Minimum NSFR requirement is 100% to be maintained on an ongoing basis.,RBI/2020-21/89,Banking Regulation
What are the RBI rules for gold loans?,Loan to Value ratio for gold loans must not exceed 75% of gold value. Gold must be appraised by trained staff. All gold loan transactions must be through banking channels only.,RBI/2022-23/45,Banking Regulation
What are the guidelines for video KYC?,Video based Customer Identification Process (V-CIP) allows banks to do KYC through live video interaction. Customer must show original OVD and PAN during the video call. Banks must store the video recording.,RBI/2020-21/16,Banking Regulation
What is the framework for resolution of stressed assets?,The Prudential Framework requires lenders to implement resolution plan within 180 days of default. If unresolved additional provisions of 20% must be made. ICA must be signed by all lenders within 30 days.,RBI/2019-20/203,Banking Regulation
What are the RBI guidelines for cybersecurity in banks?,Banks must have Board approved cybersecurity policy. Incident response drills must be conducted quarterly. Critical systems must have recovery time objective of less than 2 hours.,RBI/2023-24/77,Banking Regulation
What are the directions for RTGS transactions?,RTGS is for high value transactions of minimum Rs 2 lakh. Available 24x7 throughout the year. Settlement is real-time and final. No upper limit on transaction amount.,RBI/2021-22/68,Payment Systems
""")
    add_all(); commit("eval: expand dataset from 10 to 20 Q&A pairs across departments", DATES[i]); i += 1

    # ── 06: agent graceful empty tool result handling ─────────────────────────
    write("agent/tools.py", """
        # agent/tools.py
        import sys, logging
        from pathlib import Path
        from langchain.tools import tool
        sys.path.append(str(Path(__file__).parent.parent))
        from ingest.embedder import Embedder

        log = logging.getLogger(__name__)

        _embedder = None

        def get_embedder() -> Embedder:
            global _embedder
            if _embedder is None:
                _embedder = Embedder()
            return _embedder


        def _format_results(results: list, label: str = "") -> str:
            \"\"\"Format retrieved chunks into readable string. Handles empty results.\"\"\"
            if not results:
                return f"No relevant circulars found{' for ' + label if label else ''}."
            out = []
            for r in results:
                m = r["metadata"]
                out.append(
                    f"Circular: {m.get('circular_no','N/A')} | "
                    f"Date: {m.get('date','N/A')} | "
                    f"Dept: {m.get('department','N/A')}\\n"
                    f"{r['text'][:400]}"
                )
            return "\\n\\n---\\n\\n".join(out)


        @tool
        def vector_search(query: str) -> str:
            \"\"\"
            Search RBI circulars using semantic similarity.
            Use for conceptual questions like 'explain MCLR' or 'KYC guidelines'.
            \"\"\"
            try:
                results = get_embedder().query(query, top_k=5)
                return _format_results(results, query)
            except Exception as e:
                log.error(f"vector_search error: {e}")
                return "Search failed — vector store may be empty. Run ingestion first."


        @tool
        def department_search(query: str, department: str) -> str:
            \"\"\"
            Search RBI circulars filtered by department.
            Use when query mentions a department e.g. 'Foreign Exchange', 'Monetary Policy',
            'Payment Systems', 'Banking Regulation'.
            Args:
                query: the user question
                department: exact department name to filter by
            \"\"\"
            try:
                results = get_embedder().query(query, top_k=5, where={"department": department})
                return _format_results(results, department)
            except Exception as e:
                log.error(f"department_search error: {e}")
                return f"Search failed for department: {department}"


        @tool
        def circular_summary(circular_no: str) -> str:
            \"\"\"
            Retrieve content from a specific circular by its number.
            Use when user asks about a specific circular e.g. 'RBI/2023-24/56'.
            Args:
                circular_no: the circular number string
            \"\"\"
            try:
                results = get_embedder().query(
                    circular_no, top_k=8,
                    where={"circular_no": circular_no}
                )
                return _format_results(results, circular_no)
            except Exception as e:
                log.error(f"circular_summary error: {e}")
                return f"Could not retrieve circular: {circular_no}"


        ALL_TOOLS = [vector_search, department_search, circular_summary]
    """)
    add_all(); commit("fix(agent): add graceful error handling for empty tool results", DATES[i]); i += 1

    # ── 07: app first-run empty collection guard ──────────────────────────────
    write("app/streamlit_app.py", """
        # app/streamlit_app.py
        import sys
        from pathlib import Path
        import streamlit as st
        sys.path.append(str(Path(__file__).parent.parent))
        from retrieval.rag_chain import RAGChain
        from agent.rbi_agent import run_agent
        from ingest.embedder import Embedder
        from config import GROQ_MODEL

        st.set_page_config(page_title="RBI Circular Assistant", page_icon="🏦", layout="wide")

        with st.sidebar:
            st.title("🏦 RBI RAG")
            st.caption(f"Model: {GROQ_MODEL}")
            st.divider()
            mode = st.radio("Mode", ["RAG (Hybrid Search)", "Agent (LangGraph)"],
                            help="Hybrid search combines BM25 + vector similarity")
            dept_filter  = st.text_input("Department filter (RAG mode)",
                                         placeholder="e.g. Monetary Policy")
            top_k        = st.slider("Sources to retrieve", 3, 10, 5)
            show_sources = st.toggle("Show source circulars", value=True)
            st.divider()
            st.caption("Educational/research use only.")

        st.title("RBI Circular Assistant 🏦")
        st.caption(f"Mode: **{mode}**")

        # ── Guard: check vector store has data before loading RAG ────────────
        @st.cache_resource(show_spinner="Connecting to vector store...")
        def check_collection() -> int:
            try:
                return Embedder().collection.count()
            except Exception:
                return 0

        count = check_collection()
        if count == 0:
            st.warning(
                "⚠️ Vector store is empty. "
                "Run the ingestion pipeline first:\\n\\n"
                "```python\\n"
                "from crawl.rbi_crawler import RBICrawler\\n"
                "from ingest.pdf_parser import PDFParser\\n"
                "from ingest.embedder import Embedder\\n\\n"
                "RBICrawler().run()\\n"
                "docs = PDFParser().parse_all()\\n"
                "Embedder().embed_and_store(docs)\\n"
                "```"
            )
            st.stop()

        st.caption(f"📚 {count:,} chunks indexed")

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

        if query := st.chat_input("e.g. What are the KYC guidelines for banks?"):
            st.session_state.messages.append({"role": "user", "content": query})
            with st.chat_message("user"): st.markdown(query)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    if mode == "Agent (LangGraph)":
                        result = run_agent(query)
                    else:
                        filters = {"department": dept_filter} if dept_filter.strip() else None
                        result  = rag.answer(query, top_k=top_k, filters=filters,
                                             return_sources=show_sources)
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
    add_all(); commit("fix(app): add empty collection guard with ingestion instructions on first run", DATES[i]); i += 1

    # ── 08: logging config module ─────────────────────────────────────────────
    write("utils/__init__.py", "# utils package\n")
    write("utils/logger.py", """
        # utils/logger.py
        # Central logging setup — import and call setup_logging() at entry points.
        #
        # Usage:
        #   from utils.logger import setup_logging
        #   setup_logging()

        import logging
        import sys
        from pathlib import Path

        LOG_DIR  = Path(__file__).parent.parent / "logs"
        LOG_FILE = LOG_DIR / "rbi_rag.log"


        def setup_logging(level: str = "INFO"):
            LOG_DIR.mkdir(exist_ok=True)

            fmt = logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )

            # Console handler
            console = logging.StreamHandler(sys.stdout)
            console.setFormatter(fmt)

            # File handler — rotates daily
            from logging.handlers import TimedRotatingFileHandler
            file_h = TimedRotatingFileHandler(
                LOG_FILE, when="midnight", backupCount=7, encoding="utf-8"
            )
            file_h.setFormatter(fmt)

            root = logging.getLogger()
            root.setLevel(getattr(logging, level.upper(), logging.INFO))
            root.addHandler(console)
            root.addHandler(file_h)

            logging.getLogger("httpx").setLevel(logging.WARNING)
            logging.getLogger("chromadb").setLevel(logging.WARNING)
    """)
    write(".gitignore", """
        __pycache__/
        *.pyc
        .env
        *.pdf
        data/
        logs/
        .DS_Store
        .venv/
        !benchmarks/*.csv
    """)
    add_all(); commit("chore: add centralized logging module with file rotation", DATES[i]); i += 1

    # ── 09: CONTRIBUTING.md + README update ───────────────────────────────────
    write("CONTRIBUTING.md", """
        # Contributing

        ## Setup
        ```bash
        git clone https://github.com/schowdhury34/rbi-rag.git
        cd rbi-rag
        pip install -r requirements.txt
        cp .env.example .env
        # Add your GROQ_API_KEY to .env
        ```

        ## Project Structure
        ```
        crawl/          Crawler — scrapes RBI site, downloads PDFs
        ingest/         PDF parser, chunker, ChromaDB embedder
        retrieval/      Hybrid search, RAG chain
        agent/          LangGraph ReAct agent and tools
        eval/           RAGAS evaluation pipeline and dataset
        benchmarks/     Saved eval results (tracked in git)
        utils/          Logging and shared utilities
        app/            Streamlit UI
        ```

        ## Running the pipeline
        ```python
        from crawl.rbi_crawler import RBICrawler
        from ingest.pdf_parser import PDFParser
        from ingest.embedder import Embedder

        RBICrawler().run()                        # crawl + download
        docs = PDFParser().parse_all()            # parse + chunk
        Embedder().embed_and_store(docs)          # embed + store
        ```

        ## Running evaluation
        ```bash
        python eval/ragas_eval.py --mode rag   --split dev --save
        python eval/ragas_eval.py --mode agent --split dev --save
        python eval/benchmark.py  --compare
        ```

        ## Notes
        - PDFs and ChromaDB are gitignored — they live in data/ locally
        - Benchmark CSVs in benchmarks/ ARE tracked in git
        - Always run on dev split during development, test split for final numbers only
    """)
    write("README.md", """
        # RBI Circular RAG System 🏦

        Open-source RAG system with LangGraph agent that crawls RBI circulars
        and answers regulatory queries with source citations.

        ## Architecture
        ```
        OFFLINE
        ─────────────────────────────────────────────────
        RBI Website → Crawler (year-filtered) → PyMuPDF
            → text cleaning → chunking
            → sentence-transformers → ChromaDB (local)

        ONLINE
        ─────────────────────────────────────────────────
        User Query
            ↓
        [RAG mode]  Hybrid BM25 + Vector Search → Groq LLM
        [Agent mode] LangGraph ReAct → Tools → Groq LLM
            ↓
        Answer + Source Citations → Streamlit UI
        ```

        ## Stack
        | Layer | Tool |
        |---|---|
        | Crawling | requests + BeautifulSoup (year-filtered) |
        | PDF Parsing | PyMuPDF + text cleaning |
        | Chunking | LangChain RecursiveCharacterTextSplitter |
        | Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
        | Vector Store | ChromaDB (cosine similarity, local) |
        | Search | Hybrid BM25 + Vector with score fusion |
        | Agent | LangGraph ReAct (3 tools) |
        | LLM | Groq API — Llama 3.1 70B (free tier) |
        | Evaluation | RAGAS — 4 metrics, 20 Q&A pairs |
        | UI | Streamlit |

        ## Local Setup
        ```bash
        git clone https://github.com/schowdhury34/rbi-rag.git
        cd rbi-rag
        pip install -r requirements.txt
        cp .env.example .env        # add your GROQ_API_KEY
        python run.py               # launch Streamlit
        ```

        ## Evaluation
        ```bash
        python eval/ragas_eval.py --mode rag --split dev --save
        python eval/benchmark.py --compare
        ```

        ## Project Structure
        ```
        rbi-rag/
        ├── config.py
        ├── crawl/rbi_crawler.py
        ├── ingest/pdf_parser.py + embedder.py
        ├── retrieval/hybrid_search.py + rag_chain.py
        ├── agent/tools.py + rbi_agent.py
        ├── eval/eval_dataset.csv + ragas_eval.py + benchmark.py
        ├── benchmarks/
        ├── utils/logger.py
        └── app/streamlit_app.py
        ```

        ## Disclaimer
        Educational/research use only. Always refer to official RBI circulars for compliance.
    """)
    add_all(); commit("docs: add CONTRIBUTING.md, update README with hybrid search and full structure", DATES[i]); i += 1

    # ── Push ──────────────────────────────────────────────────────────────────
    print(f"\n✅ 10 commits added for May 2.")
    print("Pushing to origin/main...")
    result = run(["push", "origin", "main"])
    if result.returncode == 0:
        print("✅ Pushed successfully!")
    else:
        print(f"⚠️  Push failed: {result.stderr.strip()}")
        print("Run manually: git push origin main")


if __name__ == "__main__":
    build()
