# retrieval/rag_chain.py
import sys, logging
from pathlib import Path
from groq import Groq
sys.path.append(str(Path(__file__).parent.parent))
from ingest.embedder import Embedder
from config import GROQ_API_KEY, GROQ_MODEL, SYSTEM_PROMPT, TOP_K

log = logging.getLogger(__name__)


class RAGChain:
    def __init__(self):
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set — add it to your .env file")
        self.llm   = Groq(api_key=GROQ_API_KEY)
        self.store = Embedder()
        log.info(f"RAGChain ready | model={GROQ_MODEL}")

    def retrieve(self, query: str, top_k: int = TOP_K, filters: dict = None):
        return self.store.query(query, top_k=top_k, where=filters)

    def build_context(self, chunks: list) -> str:
        parts = []
        for i, c in enumerate(chunks, 1):
            m = c["metadata"]
            header = (
                f"[Source {i}] Circular: {m.get('circular_no','N/A')} | "
                f"Date: {m.get('date','N/A')} | "
                f"Dept: {m.get('department','N/A')} | "
                f"Subject: {m.get('subject','N/A')}"
            )
            parts.append(f"{header}\n{c['text']}")
        return "\n\n---\n\n".join(parts)

    def generate(self, query: str, context: str) -> str:
        # temperature=0.1: lower hallucination on compliance/regulatory queries
        # tested at 0.3 — was mixing details across circulars
        resp = self.llm.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT.format(context=context)},
                {"role": "user",   "content": query},
            ],
            temperature=0.1,
            max_tokens=1024,
        )
        return resp.choices[0].message.content

    def answer(self, query: str, top_k=TOP_K, filters=None, return_sources=True) -> dict:
        chunks  = self.retrieve(query, top_k=top_k, filters=filters)
        context = self.build_context(chunks)
        ans     = self.generate(query, context)
        return {"answer": ans, "sources": [c["metadata"] for c in chunks] if return_sources else []}
