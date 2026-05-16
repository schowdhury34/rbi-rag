# retrieval/rag_chain.py
import sys, logging
from pathlib import Path
from groq import Groq
sys.path.append(str(Path(__file__).parent.parent))
from retrieval.hybrid_search import HybridSearch
from retrieval.query_rewriter import QueryRewriter
from config import GROQ_API_KEY, GROQ_MODEL, SYSTEM_PROMPT, TOP_K

log = logging.getLogger(__name__)


class RAGChain:
    def __init__(self, use_rewriter: bool = True, use_ollama: bool = False):
        self.use_ollama = use_ollama

        if use_ollama:
            from langchain_ollama import ChatOllama
            self.ollama_llm = ChatOllama(model="llama3.2", temperature=0)
            self.llm = None
            log.info(
                f"RAGChain ready | model=llama3.2 (Ollama local) | "
                f"rewriter={'on' if use_rewriter else 'off'}"
            )
        else:
            if not GROQ_API_KEY:
                raise ValueError(
                    "GROQ_API_KEY not set.\n"
                    "Add it to your .env file: GROQ_API_KEY=your_key_here"
                )
            self.llm = Groq(api_key=GROQ_API_KEY)
            log.info(
                f"RAGChain ready | model={GROQ_MODEL} | "
                f"rewriter={'on' if use_rewriter else 'off'}"
            )

        self.search   = HybridSearch()
        self.rewriter = QueryRewriter() if use_rewriter else None

    def retrieve(self, query: str, top_k: int = TOP_K, filters: dict = None) -> list:
        search_query = self.rewriter.rewrite(query) if self.rewriter else query
        return self.search.search(search_query, top_k=top_k, filters=filters)

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
        if self.use_ollama:
            from langchain_core.messages import HumanMessage, SystemMessage
            prompt = SYSTEM_PROMPT.format(context=context)
            response = self.ollama_llm.invoke([
                SystemMessage(content=prompt),
                HumanMessage(content=query),
            ])
            return response.content
        else:
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
        chunks = self.retrieve(query, top_k=top_k, filters=filters)
        if not chunks:
            return {"answer": "No relevant circulars found.", "sources": []}
        context = self.build_context(chunks)
        ans     = self.generate(query, context)
        return {
            "answer":  ans,
            "sources": [c["metadata"] for c in chunks] if return_sources else []
        }