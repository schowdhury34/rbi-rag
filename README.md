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
