# app/pages/about.py — Streamlit multi-page: About
import streamlit as st

st.set_page_config(page_title="About — RBI RAG", page_icon="🏦")

st.title("About This Project 🏦")

st.markdown("""
## RBI Circular RAG System

This system uses **Retrieval-Augmented Generation (RAG)** to answer questions
about RBI (Reserve Bank of India) regulations and circulars.

### How it works

**Offline pipeline (run once)**
1. Crawler scrapes RBI website and downloads circular PDFs
2. PyMuPDF extracts text from each PDF
3. Text is split into overlapping chunks
4. sentence-transformers encodes each chunk into a vector
5. Vectors are stored in ChromaDB with circular metadata

**Online (per query)**
1. Your query is embedded using the same model
2. Hybrid search combines BM25 (keyword) + vector (semantic) similarity
3. Top-K relevant chunks are retrieved with source metadata
4. Groq Llama 3.1 70B generates an answer grounded in the chunks
5. Answer is returned with citations to original circulars

### Search modes
| Mode | Best for |
|---|---|
| RAG (Hybrid) | Specific regulatory questions, exact terms |
| Agent (LangGraph) | Complex multi-step questions, dept-specific queries |

### Tech stack
- **Embeddings**: `all-MiniLM-L6-v2` (sentence-transformers)
- **Vector DB**: ChromaDB with cosine similarity
- **LLM**: Groq Llama 3.1 70B (temperature = 0.1)
- **Agent**: LangGraph ReAct with 3 tools

---
*For educational and research purposes only.*
*Always refer to original RBI circulars for compliance decisions.*
""")
