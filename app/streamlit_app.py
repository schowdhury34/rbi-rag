# app/streamlit_app.py
import sys
from pathlib import Path
import streamlit as st
sys.path.append(str(Path(__file__).parent.parent))
from ingest.embedder import Embedder
from config import GROQ_MODEL

try:
    from agent.rbi_agent import run_agent
    AGENT_AVAILABLE = True
except ImportError:
    AGENT_AVAILABLE = False

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


# ── Auto-ingest on first run (for Streamlit Cloud) ────────────────────
@st.cache_resource(show_spinner="Setting up knowledge base...")
def setup_collection() -> int:
    try:
        embedder = Embedder()
        count = embedder.collection.count()
        if count == 0:
            from ingest.pdf_parser import PDFParser
            pdf_dir = Path(__file__).parent.parent / "data" / "pdfs"
            if not any(pdf_dir.glob("*.pdf")) and not any(pdf_dir.glob("*.PDF")):
                return 0
            parser = PDFParser()
            chunks = parser.parse_all()
            if chunks:
                embedder.embed_and_store(chunks)
                count = embedder.collection.count()
        return count
    except Exception as e:
        st.error(f"Setup error: {e}")
        return 0


count = setup_collection()
if count == 0:
    st.warning(
        "No circulars indexed yet. Add PDFs to `data/pdfs/` and restart, "
        "or run: `python scripts/run_ingestion.py --skip-crawl`"
    )
    st.stop()

st.caption(f"📚 {count:,} chunks indexed")


# ── RAG system ────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Loading RAG system...")
def load_rag():
    from retrieval.rag_chain import RAGChain
    return RAGChain()

try:
    rag = load_rag()
except ValueError as e:
    st.error(str(e))
    st.stop()

# ── Session state ─────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Welcome screen ────────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown("### What would you like to know?")
   
   
    sample_questions = [
    "What are the Priority Sector Lending targets for commercial banks?",
    "How are fraud cases classified and reported by banks to RBI?",
    "What are the interest rate guidelines for advances by commercial banks?",
    "What are RBI guidelines for Housing Finance Companies?",
    "What are the prudential norms for income recognition and asset classification?",
    "What are RBI guidelines for bank finance to NBFCs?",
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
                        f"**{s.get('subject', s.get('circular_no','N/A'))[:80]}** "
                        f"({s.get('date','N/A')}) — "
                        f"{s.get('department','N/A')}"
                    )


# ── Shared answer function ────────────────────────────────────────────
def process_query(query: str):
    with st.chat_message("assistant"):
        with st.spinner("Searching circulars..."):
            if mode == "Agent (LangGraph)":
                if not AGENT_AVAILABLE:
                    result = {
                        "answer": "Agent mode is temporarily unavailable. Please use RAG (Hybrid Search) mode.",
                        "sources": []
                    }
                else:
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
                        f"**{s.get('subject', s.get('circular_no','N/A'))[:80]}** "
                        f"({s.get('date','N/A')}) — "
                        f"{s.get('department','N/A')}"
                        f"\n> {s.get('subject','')[:100]}"
                    )
    st.session_state.messages.append({
        "role":    "assistant",
        "content": result["answer"],
        "sources": sources
    })


# Handle sample button clicks
if (st.session_state.messages
        and st.session_state.messages[-1]["role"] == "user"
        and not st.session_state.messages[-1].get("processed")):
    st.session_state.messages[-1]["processed"] = True
    process_query(st.session_state.messages[-1]["content"])

# ── Chat input ────────────────────────────────────────────────────────
if query := st.chat_input("Ask about RBI circulars..."):
    st.session_state.messages.append({"role": "user", "content": query, "processed": True})
    with st.chat_message("user"):
        st.markdown(query)
    process_query(query)
