# agent/tools.py
# LangGraph tool definitions — each tool wraps one capability of the RAG system.
# The agent decides which tool to call based on the user query.

import sys
from pathlib import Path
from langchain.tools import tool
sys.path.append(str(Path(__file__).parent.parent))
from ingest.embedder import Embedder

_embedder = None

def get_embedder() -> Embedder:
    global _embedder
    if _embedder is None:
        _embedder = Embedder()
    return _embedder


@tool
def vector_search(query: str) -> str:
    """
    Search RBI circulars using semantic similarity.
    Use this for conceptual questions like 'explain MCLR' or 'KYC guidelines'.
    Returns top-5 relevant chunks with circular metadata.
    """
    results = get_embedder().query(query, top_k=5)
    if not results:
        return "No relevant circulars found."
    out = []
    for r in results:
        m = r["metadata"]
        out.append(
            f"Circular: {m.get('circular_no','N/A')} | "
            f"Date: {m.get('date','N/A')} | "
            f"Dept: {m.get('department','N/A')}\n"
            f"{r['text'][:400]}"
        )
    return "\n\n---\n\n".join(out)


@tool
def department_search(query: str, department: str) -> str:
    """
    Search RBI circulars filtered by a specific department.
    Use when the query mentions a department e.g. 'Foreign Exchange', 'Monetary Policy',
    'Payment Systems', 'Banking Regulation'.
    Args:
        query: the user question
        department: exact department name to filter by
    """
    results = get_embedder().query(query, top_k=5, where={"department": department})
    if not results:
        return f"No circulars found for department: {department}"
    out = []
    for r in results:
        m = r["metadata"]
        out.append(
            f"Circular: {m.get('circular_no','N/A')} | "
            f"Date: {m.get('date','N/A')}\n"
            f"{r['text'][:400]}"
        )
    return "\n\n---\n\n".join(out)


@tool
def circular_summary(circular_no: str) -> str:
    """
    Retrieve all chunks from a specific circular by its number.
    Use when the user asks about a specific circular e.g. 'RBI/2023-24/56'.
    Args:
        circular_no: the circular number string
    """
    results = get_embedder().query(
        circular_no, top_k=10,
        where={"circular_no": circular_no}
    )
    if not results:
        return f"Circular {circular_no} not found in index."
    full_text = "\n".join(r["text"] for r in results)
    return f"Content of {circular_no}:\n\n{full_text[:1500]}"


# Registry — imported by the agent
ALL_TOOLS = [vector_search, department_search, circular_summary]
