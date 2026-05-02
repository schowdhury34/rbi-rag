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
