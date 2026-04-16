# retrieval/rag_chain.py — skeleton
import sys, logging
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from ingest.embedder import Embedder
from config import TOP_K

log = logging.getLogger(__name__)


class RAGChain:
    def __init__(self):
        self.store = Embedder()

    def retrieve(self, query: str, top_k: int = TOP_K) -> list:
        return self.store.query(query, top_k=top_k)

    def answer(self, query: str) -> dict:
        # TODO: add LLM
        chunks = self.retrieve(query)
        return {"chunks": chunks}
