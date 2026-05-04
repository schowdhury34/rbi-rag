# app/pages/stats.py — Streamlit multi-page: Collection Stats
import sys
from pathlib import Path
import streamlit as st
import pandas as pd
sys.path.append(str(Path(__file__).parent.parent.parent))
from ingest.embedder import Embedder
from config import METADATA_FILE

st.set_page_config(page_title="Stats — RBI RAG", page_icon="📊")
st.title("Collection Stats 📊")

# ── Vector store stats ─────────────────────────────────────────────────
try:
    embedder = Embedder()
    count    = embedder.collection.count()
    st.metric("Total chunks indexed", f"{count:,}")
except Exception as e:
    st.error(f"Could not connect to vector store: {e}")
    st.stop()

# ── Metadata breakdown ─────────────────────────────────────────────────
if METADATA_FILE.exists():
    df = pd.read_csv(METADATA_FILE)
    st.subheader("Circulars by Department")
    dept_counts = df["department"].value_counts().reset_index()
    dept_counts.columns = ["Department", "Count"]
    st.bar_chart(dept_counts.set_index("Department"))

    st.subheader("Circulars by Year")
    df["year"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce").dt.year
    year_counts = df["year"].value_counts().sort_index()
    st.bar_chart(year_counts)

    st.subheader("Full Circular Index")
    st.dataframe(
        df[["circular_no", "date", "department", "subject"]],
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("Metadata file not found — run crawler first.")
