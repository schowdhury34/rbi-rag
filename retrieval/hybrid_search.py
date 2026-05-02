# retrieval/hybrid_search.py
# Hybrid search: combines BM25 (keyword) + vector (semantic) scores.
# Better than pure vector search for regulatory text with specific terms
# like circular numbers, section references, exact rate values.
#
# Strategy:
#   1. Run vector search → get top-K chunks with cosine scores
#   2. Run BM25 on same candidate set → get keyword scores
#   3. Combine: final_score = alpha * vector_score + (1-alpha) * bm25_score
#   4. Re-rank and return top-K

import sys, logging, math
from pathlib import Path
from collections import defaultdict
sys.path.append(str(Path(__file__).parent.parent))
from ingest.embedder import Embedder
from config import TOP_K

log = logging.getLogger(__name__)

ALPHA = 0.6   # weight for vector score (0=pure BM25, 1=pure vector)
BM25_K1 = 1.5
BM25_B  = 0.75


class BM25:
    """Lightweight in-memory BM25 over a list of text strings."""

    def __init__(self, corpus: list[str]):
        self.corpus     = corpus
        self.n          = len(corpus)
        self.avgdl      = sum(len(d.split()) for d in corpus) / max(self.n, 1)
        self.df         = defaultdict(int)
        self.tokenized  = []
        for doc in corpus:
            tokens = self._tokenize(doc)
            self.tokenized.append(tokens)
            for t in set(tokens):
                self.df[t] += 1

    def _tokenize(self, text: str) -> list[str]:
        return text.lower().split()

    def score(self, query: str) -> list[float]:
        tokens = self._tokenize(query)
        scores = []
        for i, doc_tokens in enumerate(self.tokenized):
            tf_map = defaultdict(int)
            for t in doc_tokens: tf_map[t] += 1
            dl  = len(doc_tokens)
            sc  = 0.0
            for t in tokens:
                if t not in tf_map: continue
                tf  = tf_map[t]
                idf = math.log((self.n - self.df[t] + 0.5) / (self.df[t] + 0.5) + 1)
                sc += idf * (tf * (BM25_K1 + 1)) / (tf + BM25_K1 * (1 - BM25_B + BM25_B * dl / self.avgdl))
            scores.append(sc)
        return scores


class HybridSearch:
    def __init__(self):
        self.embedder = Embedder()

    def search(self, query: str, top_k: int = TOP_K, filters: dict = None) -> list[dict]:
        """
        Hybrid BM25 + vector search.
        Returns re-ranked list of {text, metadata, score} dicts.
        """
        # Step 1: get broader candidate pool via vector search
        candidates = self.embedder.query(query, top_k=top_k * 3, where=filters)
        if not candidates:
            return []

        texts = [c["text"] for c in candidates]

        # Step 2: BM25 over candidate texts
        bm25   = BM25(texts)
        bm25_scores = bm25.score(query)

        # Normalize BM25 scores to [0, 1]
        max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1
        bm25_norm = [s / max_bm25 for s in bm25_scores]

        # Step 3: vector scores (distance → similarity: lower distance = higher score)
        max_dist = max(c["distance"] for c in candidates) or 1
        vec_norm = [1 - (c["distance"] / max_dist) for c in candidates]

        # Step 4: combine and re-rank
        combined = []
        for idx, c in enumerate(candidates):
            final_score = ALPHA * vec_norm[idx] + (1 - ALPHA) * bm25_norm[idx]
            combined.append({
                "text":     c["text"],
                "metadata": c["metadata"],
                "score":    final_score,
            })

        combined.sort(key=lambda x: x["score"], reverse=True)
        return combined[:top_k]
