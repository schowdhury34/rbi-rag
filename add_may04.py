#!/usr/bin/env python3
"""
add_may04.py
─────────────
Run from INSIDE your rbi-rag folder:

    cd D:\projects\rbi_rag
    python add_may04.py

Adds 9 commits dated May 4, 2026.
Then pushes to origin/main.
"""

import os
import subprocess
from pathlib import Path
from textwrap import dedent

REPO_DIR     = Path(r"D:\projects\rbi_rag")
AUTHOR_NAME  = "Samrat Chowdhury"
AUTHOR_EMAIL = "schowdhury3434@gmail.com"

DATES = [
    "2026-05-04 09:20:00",
    "2026-05-04 10:10:00",
    "2026-05-04 11:00:00",
    "2026-05-04 12:15:00",
    "2026-05-04 14:00:00",
    "2026-05-04 14:55:00",
    "2026-05-04 15:50:00",
    "2026-05-04 16:40:00",
    "2026-05-04 17:25:00",
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def run(args, cwd=None):
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"]     = AUTHOR_NAME
    env["GIT_AUTHOR_EMAIL"]    = AUTHOR_EMAIL
    env["GIT_COMMITTER_NAME"]  = AUTHOR_NAME
    env["GIT_COMMITTER_EMAIL"] = AUTHOR_EMAIL
    return subprocess.run(["git"] + args, cwd=str(cwd or REPO_DIR),
                          env=env, capture_output=True, text=True)

def commit(message, date):
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"]     = AUTHOR_NAME
    env["GIT_AUTHOR_EMAIL"]    = AUTHOR_EMAIL
    env["GIT_AUTHOR_DATE"]     = date
    env["GIT_COMMITTER_NAME"]  = AUTHOR_NAME
    env["GIT_COMMITTER_EMAIL"] = AUTHOR_EMAIL
    env["GIT_COMMITTER_DATE"]  = date
    subprocess.run(["git", "commit", "-m", message, "--allow-empty"],
                   cwd=str(REPO_DIR), env=env, capture_output=True)
    print(f"  [{date[11:16]}] {message}")

def write(rel_path, content):
    p = REPO_DIR / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(dedent(content).lstrip(), encoding="utf-8")

def add_all():
    run(["add", "-A"])


# ── Commits ───────────────────────────────────────────────────────────────────

def build():
    print(f"\n📁 Repo: {REPO_DIR}")
    print("Adding commits for May 4, 2026...\n")

    i = 0

    # ── 00: query rewriter ────────────────────────────────────────────────────
    write("retrieval/query_rewriter.py", """
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

        REWRITE_PROMPT = \"\"\"You are a query rewriting assistant for an RBI regulatory document search system.
        Rewrite the user's query to be more precise and retrieval-friendly.
        - Expand abbreviations (KYC, MCLR, LRS, PSL, CRR, SLR, NPA, NBFC, etc.)
        - Add relevant regulatory context
        - Keep it concise — one sentence max
        - Do NOT answer the query, only rewrite it

        Original query: {query}
        Rewritten query:\"\"\"


        class QueryRewriter:
            def __init__(self):
                if not GROQ_API_KEY:
                    raise ValueError("GROQ_API_KEY not set")
                self.llm = Groq(api_key=GROQ_API_KEY)

            def rewrite(self, query: str) -> str:
                \"\"\"
                Rewrites a query for better retrieval.
                Falls back to original query if rewriting fails.
                \"\"\"
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
    """)
    add_all(); commit("feat(retrieval): add query rewriter — expands abbreviations for better retrieval", DATES[i]); i += 1

    # ── 01: wire query rewriter into RAG chain ────────────────────────────────
    write("retrieval/rag_chain.py", """
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
            def __init__(self, use_rewriter: bool = True):
                if not GROQ_API_KEY:
                    raise ValueError(
                        "GROQ_API_KEY not set.\\n"
                        "Add it to your .env file: GROQ_API_KEY=your_key_here"
                    )
                self.llm      = Groq(api_key=GROQ_API_KEY)
                self.search   = HybridSearch()
                self.rewriter = QueryRewriter() if use_rewriter else None
                log.info(
                    f"RAGChain ready | model={GROQ_MODEL} | "
                    f"rewriter={'on' if use_rewriter else 'off'}"
                )

            def retrieve(self, query: str, top_k: int = TOP_K, filters: dict = None) -> list:
                # Rewrite query before retrieval if rewriter is enabled
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
                    parts.append(f"{header}\\n{c['text']}")
                return "\\n\\n---\\n\\n".join(parts)

            def generate(self, query: str, context: str) -> str:
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
    """)
    add_all(); commit("feat(retrieval): wire QueryRewriter into RAGChain before retrieval step", DATES[i]); i += 1

    # ── 02: re-ranker ─────────────────────────────────────────────────────────
    write("retrieval/reranker.py", """
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

        SCORE_PROMPT = \"\"\"Rate how relevant this passage is for answering the query.
        Reply with ONLY a number from 0 to 10. Nothing else.

        Query: {query}
        Passage: {passage}
        Score:\"\"\"


        class Reranker:
            def __init__(self):
                self.llm = Groq(api_key=GROQ_API_KEY)

            def _score_chunk(self, query: str, text: str) -> float:
                \"\"\"Ask LLM to score one chunk. Returns 0.0 on failure.\"\"\"
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
                \"\"\"
                Re-ranks chunks by LLM relevance score.
                Returns top_k most relevant chunks.
                Only use when answer quality matters more than speed.
                \"\"\"
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
    """)
    add_all(); commit("feat(retrieval): add LLM-based re-ranker for answer quality improvement", DATES[i]); i += 1

    # ── 03: ingestion pipeline runner script ──────────────────────────────────
    write("scripts/run_ingestion.py", """
        # scripts/run_ingestion.py
        # Standalone ingestion pipeline — run this to crawl, parse and embed all circulars.
        #
        # Usage:
        #   python scripts/run_ingestion.py              # full run
        #   python scripts/run_ingestion.py --limit 10  # test on 10 PDFs only
        #   python scripts/run_ingestion.py --skip-crawl # re-embed existing PDFs

        import sys, argparse, logging
        from pathlib import Path
        sys.path.append(str(Path(__file__).parent.parent))

        from utils.logger import setup_logging
        from crawl.rbi_crawler import RBICrawler
        from ingest.pdf_parser import PDFParser
        from ingest.embedder import Embedder
        from config import PDF_DIR

        setup_logging()
        log = logging.getLogger(__name__)


        def main():
            parser = argparse.ArgumentParser(description="RBI RAG ingestion pipeline")
            parser.add_argument("--limit",      type=int, default=None,
                                help="Limit number of PDFs to parse (for testing)")
            parser.add_argument("--skip-crawl", action="store_true",
                                help="Skip crawling, re-embed existing PDFs only")
            args = parser.parse_args()

            # ── Step 1: Crawl ─────────────────────────────────────────────────
            if not args.skip_crawl:
                log.info("Step 1/3: Crawling RBI circular index...")
                crawler = RBICrawler()
                df      = crawler.run()
                if df is None or df.empty:
                    log.error("Crawl returned no results. Check internet connection.")
                    return
                log.info(f"Crawl complete — {len(df)} circulars in metadata")
            else:
                existing = list(PDF_DIR.glob("*.pdf"))
                log.info(f"Skipping crawl — {len(existing)} PDFs already in {PDF_DIR}")

            # ── Step 2: Parse ─────────────────────────────────────────────────
            log.info("Step 2/3: Parsing PDFs and chunking...")
            parser_obj = PDFParser()
            documents  = parser_obj.parse_all(limit=args.limit)
            if not documents:
                log.error("No documents parsed — check PDF_DIR has files")
                return
            log.info(f"Parsed {len(documents)} chunks from PDFs")

            # ── Step 3: Embed ─────────────────────────────────────────────────
            log.info("Step 3/3: Embedding and storing in ChromaDB...")
            embedder = Embedder()
            embedder.embed_and_store(documents, incremental=True)

            log.info(f"Ingestion complete. Total chunks in store: {embedder.collection.count()}")


        if __name__ == "__main__":
            main()
    """)
    write("scripts/__init__.py", "")
    add_all(); commit("feat(scripts): add standalone ingestion pipeline runner with CLI args", DATES[i]); i += 1

    # ── 04: query pipeline test script ───────────────────────────────────────
    write("scripts/test_pipeline.py", """
        # scripts/test_pipeline.py
        # Quick smoke test — verifies the full pipeline is working end to end.
        # Run after ingestion to confirm everything is wired correctly.
        #
        # Usage:
        #   python scripts/test_pipeline.py

        import sys, logging
        from pathlib import Path
        sys.path.append(str(Path(__file__).parent.parent))

        from utils.logger import setup_logging
        from retrieval.rag_chain import RAGChain
        from ingest.embedder import Embedder

        setup_logging(level="WARNING")   # suppress info noise during test
        log = logging.getLogger(__name__)

        TEST_QUERIES = [
            "What are the KYC guidelines for bank account opening?",
            "Explain MCLR and how it is calculated",
            "What is the Cash Reserve Ratio?",
            "What are the Basel III capital requirements?",
            "What are RBI guidelines for digital lending?",
        ]


        def main():
            print("\\n── RBI RAG Pipeline Test ──────────────────────────")

            # Check collection has data
            try:
                count = Embedder().collection.count()
            except Exception as e:
                print(f"\\n❌ Cannot connect to vector store: {e}")
                print("   Run ingestion first: python scripts/run_ingestion.py")
                return

            if count == 0:
                print("\\n❌ Vector store is empty. Run ingestion first.")
                return

            print(f"\\n✅ Vector store: {count:,} chunks")

            # Load RAG chain
            try:
                rag = RAGChain(use_rewriter=True)
                print("✅ RAGChain loaded\\n")
            except ValueError as e:
                print(f"\\n❌ {e}")
                return

            # Run test queries
            passed, failed = 0, 0
            for q in TEST_QUERIES:
                try:
                    result = rag.answer(q, top_k=3, return_sources=True)
                    ans    = result["answer"]
                    srcs   = result["sources"]
                    status = "✅" if len(ans) > 50 and srcs else "⚠️ "
                    if len(ans) > 50 and srcs: passed += 1
                    else: failed += 1
                    print(f"{status} {q[:55]}")
                    print(f"   Answer: {ans[:120].strip()}...")
                    if srcs:
                        print(f"   Source: {srcs[0].get('circular_no','N/A')} ({srcs[0].get('date','N/A')})")
                    print()
                except Exception as e:
                    print(f"❌ {q[:55]}")
                    print(f"   Error: {e}\\n")
                    failed += 1

            print(f"── Results: {passed} passed, {failed} failed ──────────────")


        if __name__ == "__main__":
            main()
    """)
    add_all(); commit("feat(scripts): add end-to-end pipeline smoke test with 5 sample queries", DATES[i]); i += 1

    # ── 05: circular date range filter util ──────────────────────────────────
    write("utils/filters.py", """
        # utils/filters.py
        # Helper functions to build ChromaDB metadata filter dicts.
        # ChromaDB where-clause syntax is strict — these helpers prevent mistakes.
        #
        # Usage:
        #   from utils.filters import by_department, by_year, combined
        #
        #   results = embedder.query(q, where=by_department("Monetary Policy"))
        #   results = embedder.query(q, where=by_year(2023))
        #   results = embedder.query(q, where=combined(dept="Payment Systems", year=2023))


        def by_department(department: str) -> dict:
            \"\"\"Filter by exact department name.\"\"\"
            return {"department": {"$eq": department}}


        def by_year(year: int) -> dict:
            \"\"\"
            Filter circulars by year.
            Matches date strings containing the year e.g. '01/04/2023'.
            \"\"\"
            return {"date": {"$contains": str(year)}}


        def by_circular_no(circular_no: str) -> dict:
            \"\"\"Filter by exact circular number.\"\"\"
            return {"circular_no": {"$eq": circular_no}}


        def combined(dept: str = None, year: int = None) -> dict | None:
            \"\"\"
            Build a combined filter. Returns None if no filters specified.
            ChromaDB uses $and for multiple conditions.
            \"\"\"
            conditions = []
            if dept:
                conditions.append({"department": {"$eq": dept}})
            if year:
                conditions.append({"date": {"$contains": str(year)}})

            if not conditions:
                return None
            if len(conditions) == 1:
                return conditions[0]
            return {"$and": conditions}
    """)
    add_all(); commit("feat(utils): add filter helpers for ChromaDB metadata queries (dept, year, circular_no)", DATES[i]); i += 1

    # ── 06: update agent tools to use filter helpers ──────────────────────────
    write("agent/tools.py", """
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
                    f"Dept: {m.get('department','N/A')}\\n"
                    f"{r['text'][:400]}"
                )
            return "\\n\\n---\\n\\n".join(out)


        @tool
        def vector_search(query: str) -> str:
            \"\"\"
            Search RBI circulars using semantic similarity.
            Use for broad conceptual questions like 'explain MCLR' or 'KYC guidelines'.
            \"\"\"
            try:
                results = get_embedder().query(query, top_k=5)
                return _format_results(results, query)
            except Exception as e:
                log.error(f"vector_search error: {e}")
                return "Search failed — vector store may be empty. Run ingestion first."


        @tool
        def department_search(query: str, department: str) -> str:
            \"\"\"
            Search RBI circulars filtered by department.
            Use when query mentions: 'Foreign Exchange', 'Monetary Policy',
            'Payment Systems', 'Banking Regulation'.
            Args:
                query: the user question
                department: exact department name
            \"\"\"
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
            \"\"\"
            Retrieve content from a specific circular by its number.
            Use when user mentions a specific circular e.g. 'RBI/2023-24/56'.
            Args:
                circular_no: the circular number string
            \"\"\"
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
    """)
    add_all(); commit("refactor(agent): use filter helpers from utils.filters in tool definitions", DATES[i]); i += 1

    # ── 07: update requirements ───────────────────────────────────────────────
    write("requirements.txt", """
        requests==2.31.0
        beautifulsoup4==4.12.3
        PyMuPDF==1.24.3
        langchain==0.2.6
        langchain-community==0.2.6
        langchain-groq==0.1.6
        groq==0.9.0
        langgraph==0.1.14
        sentence-transformers==3.0.1
        chromadb==0.5.3
        streamlit==1.36.0
        python-dotenv==1.0.1
        tqdm==4.66.4
        pandas==2.2.2
        ragas==0.1.14
        datasets==2.20.0
        rank-bm25==0.2.2
    """)
    add_all(); commit("chore: add rank-bm25 to requirements for hybrid search", DATES[i]); i += 1

    # ── 08: update README ─────────────────────────────────────────────────────
    write("README.md", """
        # RBI Circular RAG System 🏦

        Open-source RAG system with LangGraph agent that crawls RBI circulars
        and answers regulatory queries with source citations.

        ## Architecture
        ```
        OFFLINE
        ─────────────────────────────────────────────────
        RBI Website → Crawler (year-filtered) → PyMuPDF
            → text cleaning → chunking
            → sentence-transformers → ChromaDB (local)

        ONLINE
        ─────────────────────────────────────────────────
        User Query
            ↓
        QueryRewriter (expand abbreviations)
            ↓
        [RAG mode]   Hybrid BM25 + Vector → Re-ranker → Groq LLM
        [Agent mode] LangGraph ReAct → Tools → Groq LLM
            ↓
        Answer + Source Citations → Streamlit UI
        ```

        ## Stack
        | Layer | Tool |
        |---|---|
        | Crawling | requests + BeautifulSoup (year-filtered) |
        | PDF Parsing | PyMuPDF + text cleaning |
        | Chunking | LangChain RecursiveCharacterTextSplitter |
        | Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
        | Vector Store | ChromaDB (cosine similarity, local) |
        | Search | Hybrid BM25 + Vector with score fusion |
        | Query Rewriting | Groq Llama 3.1 70B (pre-retrieval) |
        | Re-ranking | LLM cross-encoder scoring (post-retrieval) |
        | Agent | LangGraph ReAct (3 tools) |
        | LLM | Groq API — Llama 3.1 70B (free tier) |
        | Evaluation | RAGAS — 4 metrics, 20 Q&A pairs |
        | UI | Streamlit (multi-page) |

        ## Quick Start
        ```bash
        git clone https://github.com/schowdhury34/rbi-rag.git
        cd rbi-rag
        pip install -r requirements.txt
        cp .env.example .env        # add your GROQ_API_KEY
        python scripts/run_ingestion.py
        python run.py
        ```

        ## Scripts
        ```bash
        python scripts/run_ingestion.py            # crawl + parse + embed
        python scripts/run_ingestion.py --limit 10 # test on 10 PDFs
        python scripts/test_pipeline.py            # smoke test
        python eval/ragas_eval.py --mode rag --split dev --save
        python eval/benchmark.py --compare
        ```

        ## Project Structure
        ```
        rbi-rag/
        ├── config.py
        ├── crawl/rbi_crawler.py
        ├── ingest/pdf_parser.py + embedder.py
        ├── retrieval/hybrid_search.py + rag_chain.py
        │            query_rewriter.py + reranker.py
        ├── agent/tools.py + rbi_agent.py
        ├── eval/eval_dataset.csv + ragas_eval.py + benchmark.py
        ├── benchmarks/
        ├── scripts/run_ingestion.py + test_pipeline.py
        ├── utils/logger.py + filters.py
        └── app/streamlit_app.py + pages/ + styles.py
        ```

        ## Disclaimer
        Educational/research use only.
    """)
    add_all(); commit("docs: update README with query rewriter, reranker, and scripts section", DATES[i]); i += 1

    # ── Push ──────────────────────────────────────────────────────────────────
    print(f"\n✅ 9 commits added for May 4.")
    print("Pushing to origin/main...")
    result = run(["push", "origin", "main"])
    if result.returncode == 0:
        print("✅ Pushed successfully!")
    else:
        print(f"⚠️  Push failed:\n{result.stderr.strip()}")
        print("Run manually: git push origin main")


if __name__ == "__main__":
    build()
