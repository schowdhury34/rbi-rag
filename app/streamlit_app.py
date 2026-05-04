# app/streamlit_app.py
import sys
from pathlib import Path
import streamlit as st
sys.path.append(str(Path(__file__).parent.parent))
from retrieval.rag_chain import RAGChain
from agent.rbi_agent import run_agent
from ingest.embedder import Embedder
from config import GROQ_MODEL

st.set_page_config(
    page_title="RBI Circular Assistant",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Sidebar ───────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🏦 RBI RAG")
    st.caption(f"Model: {GROQ_MODEL}")
    st.divider()
    mode = st.radio(
        "Search Mode",
        ["RAG (Hybrid Search)", "Agent (LangGraph)"],
        help=(
            "**Hybrid Search**: BM25 + vector similarity combined\n\n"
            "**Agent**: LangGraph ReAct agent with tool selection"
        )
    )
    dept_filter  = st.text_input(
        "Department filter (RAG mode)",
        placeholder="e.g. Monetary Policy"
    )
    top_k        = st.slider("Sources to retrieve", 3, 10, 5)
    show_sources = st.toggle("Show source circulars", value=True)
    st.divider()
    st.caption(
        "⚠️ For educational/research use only.\n"
        "Always refer to official RBI circulars for compliance."
    )

# ── Main header ───────────────────────────────────────────────────────
st.title("RBI Circular Assistant 🏦")
st.caption(f"Mode: **{mode}**")

# ── Collection check ──────────────────────────────────────────────────
@st.cache_resource(show_spinner="Connecting to vector store...")
def check_collection() -> int:
    try:
        return Embedder().collection.count()
    except Exception:
        return 0

count = check_collection()
if count == 0:
    st.warning(
        "Vector store is empty. Run the ingestion pipeline first.\n\n"
        "See README.md for setup instructions."
    )
    st.stop()

st.caption(f"📚 {count:,} chunks indexed")

# ── RAG system ────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Loading RAG system...")
def load_rag(): return RAGChain()

try:
    rag = load_rag()
except ValueError as e:
    st.error(str(e)); st.stop()

# ── Session state ─────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Welcome screen — shown only before first message ──────────────────
if not st.session_state.messages:
    st.markdown("### What would you like to know?")
    sample_questions = [
        "What are the KYC guidelines for bank account opening?",
        "Explain MCLR and how it affects loan interest rates",
        "What is the Liquidity Coverage Ratio requirement?",
        "What are the RBI guidelines for digital lending apps?",
        "What is Priority Sector Lending target for banks?",
        "What are the Basel III capital adequacy requirements?",
    ]
    cols = st.columns(2)
    for idx, q in enumerate(sample_questions):
        col = cols[idx % 2]
        if col.button(q, use_container_width=True, key=f"sample_{idx}"):
            st.session_state.messages.append({"role": "user", "content": q})
            st.rerun()

# ── Chat history ──────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("📄 Sources"):
                for s in msg["sources"]:
                    st.markdown(
                        f"**{s.get('circular_no','N/A')}** "
                        f"({s.get('date','N/A')}) — "
                        f"{s.get('department','N/A')}"
                    )

# ── Chat input ────────────────────────────────────────────────────────
if query := st.chat_input("Ask about RBI circulars..."):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Searching circulars..."):
            if mode == "Agent (LangGraph)":
                result = run_agent(query)
            else:
                filters = {"department": dept_filter} if dept_filter.strip() else None
                result  = rag.answer(
                    query, top_k=top_k,
                    filters=filters,
                    return_sources=show_sources
                )
        st.markdown(result["answer"])
        sources = result.get("sources", [])
        if show_sources and sources:
            with st.expander("📄 Source Circulars"):
                for s in sources:
                    st.markdown(
                        f"**{s.get('circular_no','N/A')}** "
                        f"({s.get('date','N/A')}) — "
                        f"{s.get('department','N/A')}"
                        f"\n> {s.get('subject','')[:100]}"
                    )
    st.session_state.messages.append({
        "role":    "assistant",
        "content": result["answer"],
        "sources": sources
    })
