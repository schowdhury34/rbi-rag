# app/streamlit_app.py — basic layout
import sys
from pathlib import Path
import streamlit as st
sys.path.append(str(Path(__file__).parent.parent))

st.set_page_config(page_title="RBI Circular Assistant", page_icon="🏦")
st.title("RBI Circular Assistant 🏦")
st.caption("Ask questions about RBI regulations and circulars.")

query = st.text_input("Your question:")
if query:
    st.write(f"Query received: {query}")
    # TODO: wire up RAGChain
