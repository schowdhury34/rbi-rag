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
QueryRewriter (expand abbreviations)
    ↓
[RAG mode]   Hybrid BM25 + Vector → Re-ranker → Groq LLM
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
| Query Rewriting | Groq Llama 3.1 70B (pre-retrieval) |
| Re-ranking | LLM cross-encoder scoring (post-retrieval) |
| Agent | LangGraph ReAct (3 tools) |
| LLM | Groq API — Llama 3.1 70B (free tier) |
| Evaluation | RAGAS — 4 metrics, 20 Q&A pairs |
| UI | Streamlit (multi-page) |

## Quick Start
```bash
git clone https://github.com/schowdhury34/rbi-rag.git
cd rbi-rag
pip install -r requirements.txt
cp .env.example .env        # add your GROQ_API_KEY
python scripts/run_ingestion.py
python run.py
```

## Scripts
```bash
python scripts/run_ingestion.py            # crawl + parse + embed
python scripts/run_ingestion.py --limit 10 # test on 10 PDFs
python scripts/test_pipeline.py            # smoke test
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
│            query_rewriter.py + reranker.py
├── agent/tools.py + rbi_agent.py
├── eval/eval_dataset.csv + ragas_eval.py + benchmark.py
├── benchmarks/
├── scripts/run_ingestion.py + test_pipeline.py
├── utils/logger.py + filters.py
└── app/streamlit_app.py + pages/ + styles.py
```

## Disclaimer
Educational/research use only.
