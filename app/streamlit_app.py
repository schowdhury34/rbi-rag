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
        "Run the ingestion pipeline first:\n\n"
        "```python\n"
        "from crawl.rbi_crawler import RBICrawler\n"
        "from ingest.pdf_parser import PDFParser\n"
        "from ingest.embedder import Embedder\n\n"
        "RBICrawler().run()\n"
        "docs = PDFParser().parse_all()\n"
        "Embedder().embed_and_store(docs)\n"
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
                        f"{s.get('department','N/A')}\n> {s.get('subject','')[:100]}"
                    )
    st.session_state.messages.append({
        "role": "assistant", "content": result["answer"], "sources": sources
    })
