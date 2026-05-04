# retrieval/reranker.py
# Cross-encoder re-ranking: takes top-K chunks from hybrid search
# and re-scores them using an LLM relevance check.
#
# Why: hybrid search ranks by similarity, not by answer quality.
# Re-ranking moves the most *answerable* chunks to the top.
#
# Lightweight approach: ask LLM to score each chunk 0-10 for relevance.
# Only run on final top-K (not the full collection).

import sys, logging
from pathlib import Path
from groq import Groq
sys.path.append(str(Path(__file__).parent.parent))
from config import GROQ_API_KEY, GROQ_MODEL

log = logging.getLogger(__name__)

SCORE_PROMPT = """Rate how relevant this passage is for answering the query.
Reply with ONLY a number from 0 to 10. Nothing else.

Query: {query}
Passage: {passage}
Score:"""


class Reranker:
    def __init__(self):
        self.llm = Groq(api_key=GROQ_API_KEY)

    def _score_chunk(self, query: str, text: str) -> float:
        """Ask LLM to score one chunk. Returns 0.0 on failure."""
        try:
            resp = self.llm.chat.completions.create(
                model="llama-3.1-8b-instant",   # use fast model for scoring
                messages=[{"role": "user",
                           "content": SCORE_PROMPT.format(
                               query=query, passage=text[:500]
                           )}],
                temperature=0.0,
                max_tokens=5,
            )
            score_str = resp.choices[0].message.content.strip()
            return float(score_str)
        except Exception:
            return 0.0

    def rerank(self, query: str, chunks: list, top_k: int = 3) -> list:
        """
        Re-ranks chunks by LLM relevance score.
        Returns top_k most relevant chunks.
        Only use when answer quality matters more than speed.
        """
        if not chunks:
            return chunks

        log.info(f"Re-ranking {len(chunks)} chunks...")
        scored = []
        for c in chunks:
            score = self._score_chunk(query, c["text"])
            scored.append({**c, "rerank_score": score})

        scored.sort(key=lambda x: x["rerank_score"], reverse=True)
        log.info(f"Top rerank score: {scored[0]['rerank_score']:.1f}")
        return scored[:top_k]
