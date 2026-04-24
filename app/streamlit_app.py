# app/streamlit_app.py
import sys
from pathlib import Path
import streamlit as st
sys.path.append(str(Path(__file__).parent.parent))
from retrieval.rag_chain import RAGChain
from config import GROQ_MODEL

st.set_page_config(page_title="RBI Circular Assistant", page_icon="🏦", layout="wide")

with st.sidebar:
    st.title("🏦 RBI RAG")
    st.caption(f"Model: {GROQ_MODEL}")
    dept_filter  = st.text_input("Department filter", placeholder="e.g. Monetary Policy")
    top_k        = st.slider("Sources to retrieve", 3, 10, 5)
    show_sources = st.toggle("Show source circulars", value=True)
    st.divider()
    st.caption("For educational/research use only.")

st.title("RBI Circular Assistant 🏦")

@st.cache_resource(show_spinner="Loading RAG system...")
def load_rag(): return RAGChain()

try:
    rag = load_rag()
except ValueError as e:
    st.error(str(e)); st.stop()

if query := st.chat_input("e.g. What are the MCLR guidelines?"):
    filters = {"department": dept_filter} if dept_filter.strip() else None
    with st.spinner("Searching circulars..."):
        result = rag.answer(query, top_k=top_k, filters=filters, return_sources=show_sources)
    st.markdown(result["answer"])
    if show_sources and result.get("sources"):
        with st.expander("📄 Source Circulars"):
            for s in result["sources"]:
                st.markdown(
                    f"**{s.get('circular_no','N/A')}** ({s.get('date','N/A')}) — "
                    f"{s.get('department','N/A')}\n> {s.get('subject','')[:100]}"
                )
