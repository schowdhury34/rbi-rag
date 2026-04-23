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
    dept_filter = st.text_input("Department filter", placeholder="e.g. Monetary Policy")
    top_k       = st.slider("Sources to retrieve", 3, 10, 5)

st.title("RBI Circular Assistant 🏦")

@st.cache_resource
def load_rag(): return RAGChain()

rag   = load_rag()
query = st.chat_input("Ask about RBI circulars...")
if query:
    filters = {"department": dept_filter} if dept_filter.strip() else None
    result  = rag.answer(query, top_k=top_k, filters=filters)
    st.markdown(result["answer"])
