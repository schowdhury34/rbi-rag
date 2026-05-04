# agent/tools.py
import sys, logging
from pathlib import Path
from langchain.tools import tool
sys.path.append(str(Path(__file__).parent.parent))
from ingest.embedder import Embedder
from utils.filters import by_department, by_circular_no

log = logging.getLogger(__name__)

_embedder = None

def get_embedder() -> Embedder:
    global _embedder
    if _embedder is None:
        _embedder = Embedder()
    return _embedder


def _format_results(results: list, label: str = "") -> str:
    if not results:
        return f"No relevant circulars found{' for ' + label if label else ''}."
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
def vector_search(query: str) -> str:
    """
    Search RBI circulars using semantic similarity.
    Use for broad conceptual questions like 'explain MCLR' or 'KYC guidelines'.
    """
    try:
        results = get_embedder().query(query, top_k=5)
        return _format_results(results, query)
    except Exception as e:
        log.error(f"vector_search error: {e}")
        return "Search failed — vector store may be empty. Run ingestion first."


@tool
def department_search(query: str, department: str) -> str:
    """
    Search RBI circulars filtered by department.
    Use when query mentions: 'Foreign Exchange', 'Monetary Policy',
    'Payment Systems', 'Banking Regulation'.
    Args:
        query: the user question
        department: exact department name
    """
    try:
        results = get_embedder().query(
            query, top_k=5,
            where=by_department(department)
        )
        return _format_results(results, department)
    except Exception as e:
        log.error(f"department_search error: {e}")
        return f"Search failed for department: {department}"


@tool
def circular_summary(circular_no: str) -> str:
    """
    Retrieve content from a specific circular by its number.
    Use when user mentions a specific circular e.g. 'RBI/2023-24/56'.
    Args:
        circular_no: the circular number string
    """
    try:
        results = get_embedder().query(
            circular_no, top_k=8,
            where=by_circular_no(circular_no)
        )
        return _format_results(results, circular_no)
    except Exception as e:
        log.error(f"circular_summary error: {e}")
        return f"Could not retrieve circular: {circular_no}"


ALL_TOOLS = [vector_search, department_search, circular_summary]
