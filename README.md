# RBI Circular RAG System 🏦

An open-source Retrieval-Augmented Generation system that indexes Reserve Bank of India regulatory circulars and answers compliance queries with source citations.

Built as part of MTech AI & Data Science coursework at IIT Jodhpur.

---

## What it does

- Crawls and indexes RBI Master Circulars and year-archive circulars
- Answers natural language queries about RBI regulations
- Returns answers grounded in actual circular text with circular number, date, and department citations
- Runs a hybrid BM25 + vector search pipeline with LLM-based query rewriting and re-ranking

---

## Architecture

```
OFFLINE
────────────────────────────────────────────
RBI Website → Playwright downloader
→ PyMuPDF text extraction
→ RecursiveCharacterTextSplitter (chunking)
→ sentence-transformers (all-MiniLM-L6-v2)
→ ChromaDB (local vector store)

ONLINE
────────────────────────────────────────────
User Query
↓
QueryRewriter (Groq Llama 3.3 70B)
↓
Hybrid BM25 + Vector Search
↓
LLM Re-ranker (cross-encoder scoring)
↓
Groq Llama 3.3 70B → Answer + Citations
↓
Streamlit UI
```

---

## Stack

| Layer | Tool |
|---|---|
| PDF Crawling | Playwright (headless Chromium) |
| PDF Parsing | PyMuPDF |
| Chunking | LangChain RecursiveCharacterTextSplitter |
| Embeddings | sentence-transformers all-MiniLM-L6-v2 |
| Vector Store | ChromaDB (local, persistent) |
| Keyword Search | BM25 (rank-bm25) |
| LLM | Groq API — Llama 3.3 70B |
| Evaluation | RAGAS 0.4.3 (4 metrics, 20 Q&A pairs) |
| UI | Streamlit |

---

## Setup

```bash
git clone https://github.com/schowdhury34/rbi-rag.git
cd rbi-rag
pip install -r requirements.txt
cp .env.example .env        # add your GROQ_API_KEY
```

Install Playwright browser for PDF downloading:
```bash
playwright install chromium
```

---

## Usage

### Download RBI circulars
```bash
python crawl/pdf_downloader.py --limit 21
```
Uses a headless browser to bypass bot protection on rbidocs.rbi.org.in.

### Ingest into vector store
```bash
python scripts/run_ingestion.py --skip-crawl
```

### Launch the UI
```bash
python run.py
```
Opens at http://localhost:8501

### Run evaluation
```bash
python eval/ragas_eval.py --mode rag --split dev --save
```

---

## Evaluation Results

Evaluated on 7 dev-split questions using RAGAS with Llama 3.3 70B as judge:

| Metric | Score |
|---|---|
| Faithfulness | 0.639 |
| Answer Relevancy | 0.596 |
| Context Recall | 0.361 |
| Context Precision | 0.876 |

*Evaluated on 7 dev-split questions using RAGAS 0.4.3 with Mistral 7B as local judge.*

---

## Project Structure

```
rbi-rag/
├── config.py
├── run.py
├── crawl/
│   ├── rbi_crawler.py          # year-archive circular crawler
│   └── pdf_downloader.py       # Playwright-based PDF downloader
├── ingest/
│   ├── pdf_parser.py           # PyMuPDF text extraction + chunking
│   └── embedder.py             # sentence-transformers + ChromaDB
├── retrieval/
│   ├── hybrid_search.py        # BM25 + vector fusion
│   ├── rag_chain.py            # RAG pipeline (Groq or Ollama)
│   ├── query_rewriter.py       # LLM query expansion
│   └── reranker.py             # LLM cross-encoder re-ranking
├── agent/
│   └── rbi_agent.py            # LangGraph ReAct agent (WIP)
├── eval/
│   ├── eval_dataset.csv        # 20 Q&A pairs
│   └── ragas_eval.py           # RAGAS evaluation pipeline
├── benchmarks/                 # saved eval results
├── scripts/
│   ├── run_ingestion.py        # end-to-end ingestion pipeline
│   └── test_pipeline.py        # smoke test
├── app/
│   └── streamlit_app.py        # multi-mode chat UI
└── utils/
    ├── logger.py
    └── filters.py
```

---

## Notes

- RBI's PDF infrastructure uses Akamai bot protection. Direct HTTP downloads return challenge pages. The Playwright downloader handles this by running a real browser session.
- `data/pdfs/` and `data/chroma_db/` are gitignored. Run the downloader and ingestion pipeline after cloning.
- Agent mode (LangGraph ReAct) is functional in architecture but has a pending dependency issue with `langgraph.prebuilt.ToolNode` in langgraph 1.x.

---

## Contributors

- [Samrat Chowdhury](https://github.com/schowdhury34) — RAG pipeline, crawler, evaluation
- [Nisha Chowdhury](https://github.com/G24AIT101) — Streamlit UI

---

## Disclaimer

Educational and research use only. Always refer to official RBI circulars at rbi.org.in for compliance decisions.
