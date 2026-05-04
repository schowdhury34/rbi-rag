# retrieval/query_rewriter.py
# Rewrites vague user queries into more precise retrieval-friendly versions
# before sending to the vector store.
#
# Problem: users ask "what about KYC?" — too vague for good retrieval.
# Solution: LLM rewrites it to "KYC requirements and document verification
#           guidelines for bank account opening per RBI circular"
#
# This is a lightweight single LLM call — runs before retrieval.

import sys, logging
from pathlib import Path
from groq import Groq
sys.path.append(str(Path(__file__).parent.parent))
from config import GROQ_API_KEY, GROQ_MODEL

log = logging.getLogger(__name__)

REWRITE_PROMPT = """You are a query rewriting assistant for an RBI regulatory document search system.
Rewrite the user's query to be more precise and retrieval-friendly.
- Expand abbreviations (KYC, MCLR, LRS, PSL, CRR, SLR, NPA, NBFC, etc.)
- Add relevant regulatory context
- Keep it concise — one sentence max
- Do NOT answer the query, only rewrite it

Original query: {query}
Rewritten query:"""


class QueryRewriter:
    def __init__(self):
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set")
        self.llm = Groq(api_key=GROQ_API_KEY)

    def rewrite(self, query: str) -> str:
        """
        Rewrites a query for better retrieval.
        Falls back to original query if rewriting fails.
        """
        try:
            resp = self.llm.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "user",
                     "content": REWRITE_PROMPT.format(query=query)}
                ],
                temperature=0.0,
                max_tokens=100,
            )
            rewritten = resp.choices[0].message.content.strip()
            log.info(f"Query rewrite: '{query}' -> '{rewritten}'")
            return rewritten
        except Exception as e:
            log.warning(f"Query rewrite failed, using original: {e}")
            return query   # graceful fallback
