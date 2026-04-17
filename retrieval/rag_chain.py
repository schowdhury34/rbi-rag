# retrieval/rag_chain.py
import sys, logging
from pathlib import Path
from groq import Groq
sys.path.append(str(Path(__file__).parent.parent))
from ingest.embedder import Embedder
from config import GROQ_API_KEY, GROQ_MODEL, TOP_K

log = logging.getLogger(__name__)


class RAGChain:
    def __init__(self):
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set — add it to your .env file")
        self.llm   = Groq(api_key=GROQ_API_KEY)
        self.store = Embedder()

    def retrieve(self, query: str, top_k: int = TOP_K, filters: dict = None):
        return self.store.query(query, top_k=top_k, where=filters)

    def build_context(self, chunks: list) -> str:
        parts = []
        for i, c in enumerate(chunks, 1):
            m = c["metadata"]
            parts.append(f"[{i}] {m.get('circular_no','')} | {m.get('date','')}\n{c['text']}")
        return "\n\n---\n\n".join(parts)

    def generate(self, query: str, context: str) -> str:
        resp = self.llm.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system",  "content": f"Answer using this context:\n{context}"},
                {"role": "user",    "content": query},
            ],
            max_tokens=1024,
        )
        return resp.choices[0].message.content

    def answer(self, query: str, **kwargs) -> dict:
        chunks  = self.retrieve(query)
        context = self.build_context(chunks)
        ans     = self.generate(query, context)
        return {"answer": ans, "sources": [c["metadata"] for c in chunks]}
