# RBI Circular RAG System 🏦

An open-source Retrieval-Augmented Generation (RAG) system with a LangGraph
agent layer that crawls RBI circulars and answers regulatory queries with source citations.

## Architecture
```
OFFLINE
──────────────────────────────────────────
RBI Website → Crawler → PyMuPDF → Chunker → sentence-transformers → ChromaDB

ONLINE
──────────────────────────────────────────
User Query
    ↓
LangGraph Agent
    ├── Tool: vector_search      (broad semantic search)
    ├── Tool: department_search  (filtered by dept)
    └── Tool: circular_summary   (specific circular lookup)
    ↓
Groq Llama 3.1 70B (temp=0.1)
    ↓
Answer + Source Citations → Streamlit UI
```

## Stack
| Layer | Tool |
|---|---|
| Crawling | requests + BeautifulSoup |
| PDF Parsing | PyMuPDF |
| Chunking | LangChain RecursiveCharacterTextSplitter |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Vector Store | ChromaDB (cosine similarity, persisted to Drive) |
| Agent | LangGraph ReAct agent |
| LLM | Groq API — Llama 3.1 70B |
| Evaluation | RAGAS (faithfulness, relevancy, recall, precision) |
| UI | Streamlit (RAG mode + Agent mode) |

## Quick Start (Google Colab)
```bash
!git clone https://github.com/YOUR_USERNAME/rbi-rag.git
%cd rbi-rag
!pip install -r requirements.txt -q
```
Add `GROQ_API_KEY` to Colab Secrets, then follow `notebooks/01_run_pipeline.py`.

## Evaluation
```bash
# Run on dev split
python eval/ragas_eval.py --mode rag --split dev --save

# Compare RAG vs Agent
python eval/ragas_eval.py --mode agent --split dev --save

# Compare against previous benchmark
python eval/benchmark.py --compare
```

## Project Structure
```
rbi-rag/
├── config.py
├── requirements.txt
├── crawl/rbi_crawler.py
├── ingest/pdf_parser.py
├── ingest/embedder.py
├── retrieval/rag_chain.py
├── agent/tools.py              ← LangGraph tool definitions
├── agent/rbi_agent.py          ← ReAct agent graph
├── eval/eval_dataset.csv       ← 10 Q&A ground truth pairs
├── eval/ragas_eval.py          ← RAGAS evaluation pipeline
├── eval/benchmark.py           ← benchmark comparison runner
├── benchmarks/                 ← saved eval CSVs (tracked in git)
├── app/streamlit_app.py
└── notebooks/01_run_pipeline.py
```

## Features
- Resume-safe crawling + incremental embedding
- LangGraph ReAct agent with 3 tools
- RAGAS evaluation on 4 metrics
- Benchmark history tracked in git
- Metadata filtering by department
- Source citations with every answer
- Streamlit UI with RAG/Agent mode toggle

## Disclaimer
Educational/research use only. Always refer to official RBI circulars for compliance.
