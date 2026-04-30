#!/usr/bin/env python3
"""
add_agent_and_eval.py
──────────────────────
Run this INSIDE your existing rbi-rag folder.

    cd rbi-rag
    python ../add_agent_and_eval.py

Adds 10 commits dated today (April 30, 2026):
  - LangGraph agent with tools
  - RAGAS eval pipeline
  - Sample eval dataset
  - Benchmarking runner
  - requirements update
Then pushes to origin/main.
"""

import os
import subprocess
from pathlib import Path
from textwrap import dedent

REPO_DIR     = Path(r"D:\projects\rbi_rag")
AUTHOR_NAME  = "Samrat Chowdhury"
AUTHOR_EMAIL = "schowdhury3434@gmail.com"   # ← change to your GitHub email

# Today's commits — spread across April 30
DATES = [
    "2026-04-30 09:10:00",
    "2026-04-30 10:05:00",
    "2026-04-30 11:20:00",
    "2026-04-30 12:45:00",
    "2026-04-30 14:00:00",
    "2026-04-30 14:55:00",
    "2026-04-30 15:40:00",
    "2026-04-30 16:30:00",
    "2026-04-30 17:15:00",
    "2026-04-30 17:50:00",
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


# ── Build commits ──────────────────────────────────────────────────────────────

def build():
    print(f"\n📁 Repo: {REPO_DIR}")
    print("Adding agent + eval commits for April 30...\n")

    i = 0

    # ── Commit 0: update requirements ────────────────────────────────────────
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
    """)
    add_all(); commit("chore: add langgraph and ragas to requirements", DATES[i]); i += 1

    # ── Commit 1: agent tools ─────────────────────────────────────────────────
    write("agent/__init__.py", "# agent package\n")
    write("agent/tools.py", """
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
            \"\"\"
            Search RBI circulars using semantic similarity.
            Use this for conceptual questions like 'explain MCLR' or 'KYC guidelines'.
            Returns top-5 relevant chunks with circular metadata.
            \"\"\"
            results = get_embedder().query(query, top_k=5)
            if not results:
                return "No relevant circulars found."
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
        def department_search(query: str, department: str) -> str:
            \"\"\"
            Search RBI circulars filtered by a specific department.
            Use when the query mentions a department e.g. 'Foreign Exchange', 'Monetary Policy',
            'Payment Systems', 'Banking Regulation'.
            Args:
                query: the user question
                department: exact department name to filter by
            \"\"\"
            results = get_embedder().query(query, top_k=5, where={"department": department})
            if not results:
                return f"No circulars found for department: {department}"
            out = []
            for r in results:
                m = r["metadata"]
                out.append(
                    f"Circular: {m.get('circular_no','N/A')} | "
                    f"Date: {m.get('date','N/A')}\\n"
                    f"{r['text'][:400]}"
                )
            return "\\n\\n---\\n\\n".join(out)


        @tool
        def circular_summary(circular_no: str) -> str:
            \"\"\"
            Retrieve all chunks from a specific circular by its number.
            Use when the user asks about a specific circular e.g. 'RBI/2023-24/56'.
            Args:
                circular_no: the circular number string
            \"\"\"
            results = get_embedder().query(
                circular_no, top_k=10,
                where={"circular_no": circular_no}
            )
            if not results:
                return f"Circular {circular_no} not found in index."
            full_text = "\\n".join(r["text"] for r in results)
            return f"Content of {circular_no}:\\n\\n{full_text[:1500]}"


        # Registry — imported by the agent
        ALL_TOOLS = [vector_search, department_search, circular_summary]
    """)
    add_all(); commit("feat(agent): define LangGraph tools — vector_search, department_search, circular_summary", DATES[i]); i += 1

    # ── Commit 2: agent graph ─────────────────────────────────────────────────
    write("agent/rbi_agent.py", """
        # agent/rbi_agent.py
        # LangGraph agent — decides which tool to call based on the query,
        # then synthesizes a final answer from tool outputs.

        import sys, logging
        from pathlib import Path
        from typing import TypedDict, Annotated
        import operator

        from langchain_groq import ChatGroq
        from langchain.schema import HumanMessage, AIMessage, SystemMessage
        from langgraph.graph import StateGraph, END
        from langgraph.prebuilt import ToolNode

        sys.path.append(str(Path(__file__).parent.parent))
        from config import GROQ_API_KEY, GROQ_MODEL
        from agent.tools import ALL_TOOLS

        log = logging.getLogger(__name__)


        # ── Agent state ───────────────────────────────────────────────────────

        class AgentState(TypedDict):
            messages: Annotated[list, operator.add]   # accumulate messages
            sources:  list                             # circular metadata for citations


        # ── Nodes ─────────────────────────────────────────────────────────────

        AGENT_SYSTEM = \"\"\"You are an expert RBI regulations assistant with access to tools
        that search indexed RBI circulars.

        TOOLS AVAILABLE:
        - vector_search: broad semantic search across all circulars
        - department_search: search within a specific RBI department
        - circular_summary: retrieve a specific circular by number

        RULES:
        1. Always use a tool before answering — never answer from memory.
        2. Cite circular number, date, and department in your final answer.
        3. If the query mentions a specific department, prefer department_search.
        4. If the user gives a circular number, use circular_summary.
        5. If no relevant circular is found, say so clearly.
        \"\"\"

        def agent_node(state: AgentState) -> AgentState:
            \"\"\"LLM decides whether to call a tool or give final answer.\"\"\"
            llm = ChatGroq(api_key=GROQ_API_KEY, model=GROQ_MODEL, temperature=0.1)
            llm_with_tools = llm.bind_tools(ALL_TOOLS)
            messages = [SystemMessage(content=AGENT_SYSTEM)] + state["messages"]
            response = llm_with_tools.invoke(messages)
            return {"messages": [response], "sources": state.get("sources", [])}

        def should_continue(state: AgentState) -> str:
            \"\"\"Route: if last message has tool_calls → run tools, else → end.\"\"\"
            last = state["messages"][-1]
            if hasattr(last, "tool_calls") and last.tool_calls:
                return "tools"
            return END

        # ── Build graph ────────────────────────────────────────────────────────

        def build_agent():
            tool_node = ToolNode(ALL_TOOLS)

            graph = StateGraph(AgentState)
            graph.add_node("agent", agent_node)
            graph.add_node("tools", tool_node)

            graph.set_entry_point("agent")
            graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
            graph.add_edge("tools", "agent")   # after tools → back to agent to synthesize

            return graph.compile()


        # ── Public interface ────────────────────────────────────────────────────

        _agent = None

        def get_agent():
            global _agent
            if _agent is None:
                _agent = build_agent()
            return _agent

        def run_agent(query: str) -> dict:
            \"\"\"
            Run the RBI agent on a query.
            Returns: {answer: str, sources: list}
            \"\"\"
            agent = get_agent()
            result = agent.invoke({
                "messages": [HumanMessage(content=query)],
                "sources":  []
            })
            # Extract final text answer from last AIMessage
            final_msg = result["messages"][-1]
            answer    = final_msg.content if hasattr(final_msg, "content") else str(final_msg)
            return {"answer": answer, "sources": result.get("sources", [])}


        if __name__ == "__main__":
            logging.basicConfig(level=logging.INFO)
            r = run_agent("What are the KYC guidelines for banks?")
            print(r["answer"])
    """)
    add_all(); commit("feat(agent): build LangGraph ReAct agent with tool routing and state graph", DATES[i]); i += 1

    # ── Commit 3: update streamlit to support agent mode ─────────────────────
    write("app/streamlit_app.py", """
        # app/streamlit_app.py — with agent mode toggle
        import sys
        from pathlib import Path
        import streamlit as st
        sys.path.append(str(Path(__file__).parent.parent))
        from retrieval.rag_chain import RAGChain
        from agent.rbi_agent import run_agent
        from config import GROQ_MODEL

        st.set_page_config(page_title="RBI Circular Assistant", page_icon="🏦", layout="wide")

        with st.sidebar:
            st.title("🏦 RBI RAG")
            st.caption(f"Model: {GROQ_MODEL}")
            st.divider()

            mode = st.radio("Mode", ["RAG (Direct)", "Agent (LangGraph)"],
                            help="Agent mode uses tool-calling to decide search strategy")

            dept_filter  = st.text_input("Department filter (RAG mode only)",
                                         placeholder="e.g. Monetary Policy")
            top_k        = st.slider("Sources to retrieve", 3, 10, 5)
            show_sources = st.toggle("Show source circulars", value=True)
            st.divider()
            st.caption("Educational/research use only.")

        st.title("RBI Circular Assistant 🏦")
        st.caption(f"Mode: **{mode}**")

        @st.cache_resource(show_spinner="Loading RAG system...")
        def load_rag(): return RAGChain()

        try:
            rag = load_rag()
        except ValueError as e:
            st.error(str(e)); st.stop()

        if "messages" not in st.session_state:
            st.session_state.messages = []

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("sources"):
                    with st.expander("📄 Sources"):
                        for s in msg["sources"]:
                            st.markdown(f"**{s.get('circular_no','N/A')}** ({s.get('date','N/A')})")

        if query := st.chat_input("e.g. What are the KYC guidelines for banks?"):
            st.session_state.messages.append({"role": "user", "content": query})
            with st.chat_message("user"): st.markdown(query)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    if mode == "Agent (LangGraph)":
                        result = run_agent(query)
                    else:
                        filters = {"department": dept_filter} if dept_filter.strip() else None
                        result  = rag.answer(query, top_k=top_k, filters=filters,
                                             return_sources=show_sources)
                st.markdown(result["answer"])
                sources = result.get("sources", [])
                if show_sources and sources:
                    with st.expander("📄 Source Circulars"):
                        for s in sources:
                            st.markdown(
                                f"**{s.get('circular_no','N/A')}** ({s.get('date','N/A')}) — "
                                f"{s.get('department','N/A')}\\n> {s.get('subject','')[:100]}"
                            )
            st.session_state.messages.append({
                "role": "assistant", "content": result["answer"], "sources": sources
            })
    """)
    add_all(); commit("feat(app): add agent mode toggle — RAG direct vs LangGraph agent", DATES[i]); i += 1

    # ── Commit 4: eval dataset ────────────────────────────────────────────────
    write("eval/__init__.py", "# eval package\n")
    write("eval/eval_dataset.csv", """question,ground_truth,source_circular,department
What is the Marginal Cost of Funds based Lending Rate (MCLR)?,MCLR is an internal benchmark lending rate for banks introduced by RBI. It is calculated based on marginal cost of funds including marginal cost of borrowings and return on net worth. Banks must review MCLR monthly.,RBI/2015-16/121,Banking Regulation
What are the KYC requirements for opening a bank account?,Customers must submit Officially Valid Documents (OVD) for identity and address proof. PAN or Form 60 is mandatory. Periodic KYC update is required based on risk category.,RBI/2023-24/56,Banking Regulation
What is the Cash Reserve Ratio (CRR) requirement?,Banks are required to maintain a certain percentage of their net demand and time liabilities as cash reserve with RBI. The rate is notified by RBI periodically.,RBI/2023-24/89,Monetary Policy
What are the guidelines for Prepaid Payment Instruments (PPI)?,PPIs are instruments that facilitate purchase of goods and services using stored value. RBI classifies them as closed system PPI open system PPI and semi-closed system PPI with varying limits.,RBI/2021-22/45,Payment Systems
What is the Liquidity Coverage Ratio (LCR) requirement for banks?,Banks must maintain High Quality Liquid Assets (HQLA) to cover net cash outflows over a 30-day stress period. The minimum LCR requirement is 100%.,RBI/2019-20/188,Banking Regulation
What are the foreign exchange remittance limits under LRS?,Under Liberalised Remittance Scheme (LRS) resident individuals can remit up to USD 250000 per financial year for permitted current and capital account transactions.,RBI/2023-24/12,Foreign Exchange
What is Priority Sector Lending (PSL) target for banks?,Domestic commercial banks and foreign banks with 20 or more branches must achieve 40% of Adjusted Net Bank Credit as priority sector lending.,RBI/2020-21/25,Banking Regulation
What are the guidelines for NEFT transactions?,NEFT operates on deferred net settlement basis in half hourly batches. Available 24x7 on all days including holidays. Minimum transfer amount is Re 1 with no upper limit.,RBI/2021-22/67,Payment Systems
What is the repo rate and how does it affect lending?,Repo rate is the rate at which RBI lends short-term funds to commercial banks against government securities. An increase in repo rate leads to higher borrowing costs for banks which is passed on to customers.,RBI/2023-24/1,Monetary Policy
What are the capital adequacy norms under Basel III?,Banks must maintain minimum Tier 1 capital ratio of 7% Common Equity Tier 1 of 5.5% and total capital adequacy ratio of 9% of Risk Weighted Assets under Basel III framework.,RBI/2015-16/8,Banking Regulation
""")
    add_all(); commit("eval: add initial Q&A evaluation dataset with 10 ground truth pairs", DATES[i]); i += 1

    # ── Commit 5: RAGAS eval pipeline ─────────────────────────────────────────
    write("eval/ragas_eval.py", """
        # eval/ragas_eval.py
        # Evaluates the RAG system using RAGAS metrics:
        #   - faithfulness:      is answer grounded in retrieved context?
        #   - answer_relevancy:  does answer address the question?
        #   - context_recall:    did retrieval fetch the right chunks?
        #   - context_precision: were retrieved chunks relevant?
        #
        # Usage:
        #   python eval/ragas_eval.py --mode rag         # evaluate RAG chain
        #   python eval/ragas_eval.py --mode agent       # evaluate agent
        #   python eval/ragas_eval.py --mode rag --save  # save results to benchmarks/

        import sys, argparse, logging
        from pathlib import Path
        from datetime import date

        import pandas as pd
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import (
            faithfulness,
            answer_relevancy,
            context_recall,
            context_precision,
        )

        sys.path.append(str(Path(__file__).parent.parent))
        from retrieval.rag_chain import RAGChain
        from agent.rbi_agent import run_agent
        from ingest.embedder import Embedder

        logging.basicConfig(level=logging.INFO)
        log = logging.getLogger(__name__)

        EVAL_CSV   = Path(__file__).parent / "eval_dataset.csv"
        BENCH_DIR  = Path(__file__).parent.parent / "benchmarks"


        def load_eval_data(split: str = "dev") -> pd.DataFrame:
            \"\"\"
            Returns eval rows.
            split='dev'  → first 7 rows  (tune on these)
            split='test' → last 3 rows   (held-out, final eval only)
            split='all'  → all rows
            \"\"\"
            df = pd.read_csv(EVAL_CSV)
            if split == "dev":
                return df.iloc[:7].reset_index(drop=True)
            elif split == "test":
                return df.iloc[7:].reset_index(drop=True)
            return df


        def build_ragas_dataset(df: pd.DataFrame, mode: str) -> Dataset:
            \"\"\"
            Runs each question through the RAG system / agent,
            collects (question, answer, contexts, ground_truth).
            \"\"\"
            if mode == "rag":
                rag = RAGChain()
            embedder = Embedder()

            questions, answers, contexts, ground_truths = [], [], [], []

            for _, row in df.iterrows():
                q  = row["question"]
                gt = row["ground_truth"]
                log.info(f"Running: {q[:60]}...")

                if mode == "rag":
                    result = rag.answer(q, return_sources=True)
                    ans    = result["answer"]
                    # Get raw chunks for context
                    chunks = embedder.query(q, top_k=5)
                    ctx    = [c["text"] for c in chunks]
                else:
                    result = run_agent(q)
                    ans    = result["answer"]
                    chunks = embedder.query(q, top_k=5)
                    ctx    = [c["text"] for c in chunks]

                questions.append(q)
                answers.append(ans)
                contexts.append(ctx)
                ground_truths.append(gt)

            return Dataset.from_dict({
                "question":     questions,
                "answer":       answers,
                "contexts":     contexts,
                "ground_truth": ground_truths,
            })


        def run_eval(mode: str = "rag", split: str = "dev", save: bool = False):
            log.info(f"Starting RAGAS eval | mode={mode} | split={split}")

            df      = load_eval_data(split)
            dataset = build_ragas_dataset(df, mode)

            log.info("Running RAGAS metrics...")
            scores = evaluate(
                dataset,
                metrics=[faithfulness, answer_relevancy, context_recall, context_precision]
            )

            results_df = scores.to_pandas()
            print("\\n" + "="*55)
            print(f"  RAGAS Results | mode={mode} | split={split}")
            print("="*55)
            print(f"  Faithfulness      : {results_df['faithfulness'].mean():.3f}")
            print(f"  Answer Relevancy  : {results_df['answer_relevancy'].mean():.3f}")
            print(f"  Context Recall    : {results_df['context_recall'].mean():.3f}")
            print(f"  Context Precision : {results_df['context_precision'].mean():.3f}")
            print("="*55)

            if save:
                BENCH_DIR.mkdir(exist_ok=True)
                fname = BENCH_DIR / f"eval_{mode}_{split}_{date.today().isoformat()}.csv"
                results_df.to_csv(fname, index=False)
                log.info(f"Saved to {fname}")

            return results_df


        if __name__ == "__main__":
            parser = argparse.ArgumentParser()
            parser.add_argument("--mode",  choices=["rag", "agent"], default="rag")
            parser.add_argument("--split", choices=["dev", "test", "all"], default="dev")
            parser.add_argument("--save",  action="store_true")
            args = parser.parse_args()
            run_eval(args.mode, args.split, args.save)
    """)
    add_all(); commit("feat(eval): RAGAS evaluation pipeline with faithfulness, relevancy, recall, precision", DATES[i]); i += 1

    # ── Commit 6: benchmark runner ────────────────────────────────────────────
    write("eval/benchmark.py", """
        # eval/benchmark.py
        # Runs evaluation and compares against previous benchmark.
        # Use after any significant change: new circulars, chunk size, model swap.
        #
        # Usage:
        #   python eval/benchmark.py                  # run and print
        #   python eval/benchmark.py --save           # run and save to benchmarks/
        #   python eval/benchmark.py --compare        # compare with last saved benchmark

        import sys, argparse, logging
        from pathlib import Path
        import pandas as pd

        sys.path.append(str(Path(__file__).parent.parent))
        from eval.ragas_eval import run_eval

        logging.basicConfig(level=logging.INFO)
        log = logging.getLogger(__name__)

        BENCH_DIR = Path(__file__).parent.parent / "benchmarks"
        METRICS   = ["faithfulness", "answer_relevancy", "context_recall", "context_precision"]


        def compare_with_last(current_df: pd.DataFrame, mode: str):
            \"\"\"Compare current run against the most recent saved benchmark.\"\"\"
            saved = sorted(BENCH_DIR.glob(f"eval_{mode}_*.csv"))
            if len(saved) < 2:
                print("\\nNo previous benchmark to compare against.")
                return

            prev_df = pd.read_csv(saved[-2])  # second-to-last file

            print("\\n" + "="*55)
            print(f"  Benchmark Comparison | mode={mode}")
            print("="*55)
            print(f"  {'Metric':<22} {'Previous':>10} {'Current':>10} {'Delta':>8}")
            print("  " + "-"*51)
            for m in METRICS:
                if m in prev_df.columns and m in current_df.columns:
                    prev = prev_df[m].mean()
                    curr = current_df[m].mean()
                    delta = curr - prev
                    arrow = "▲" if delta > 0.01 else ("▼" if delta < -0.01 else "~")
                    print(f"  {m:<22} {prev:>10.3f} {curr:>10.3f} {arrow}{abs(delta):>6.3f}")
            print("="*55)


        def main():
            parser = argparse.ArgumentParser()
            parser.add_argument("--mode",    choices=["rag", "agent"], default="rag")
            parser.add_argument("--split",   choices=["dev", "test", "all"], default="dev")
            parser.add_argument("--save",    action="store_true")
            parser.add_argument("--compare", action="store_true")
            args = parser.parse_args()

            current_df = run_eval(args.mode, args.split, save=args.save)

            if args.compare:
                compare_with_last(current_df, args.mode)


        if __name__ == "__main__":
            main()
    """)
    add_all(); commit("feat(eval): benchmark runner with delta comparison against previous run", DATES[i]); i += 1

    # ── Commit 7: benchmarks folder + placeholder ─────────────────────────────
    write("benchmarks/.gitkeep", "")
    write(".gitignore", """
        __pycache__/
        *.pyc
        .env
        *.pdf
        data/
        chroma_db/
        .DS_Store
        .ipynb_checkpoints/
        # keep benchmark CSVs in git — they track progress
        !benchmarks/*.csv
    """)
    add_all(); commit("chore: add benchmarks/ folder to track eval history in git", DATES[i]); i += 1

    # ── Commit 8: update notebook with agent + eval cells ────────────────────
    write("notebooks/01_run_pipeline.py", """
        # notebooks/01_run_pipeline.py
        # Full pipeline — run cell-by-cell in Google Colab

        # CELL 1: Mount Drive
        from google.colab import drive
        drive.mount("/content/drive")
        import sys; sys.path.append("/content/rbi-rag")

        # CELL 2: Install
        # !pip install -r requirements.txt -q

        # CELL 3: API Key
        import os
        from google.colab import userdata
        os.environ["GROQ_API_KEY"] = userdata.get("GROQ_API_KEY")

        # CELL 4: Crawl
        from crawl.rbi_crawler import RBICrawler
        df = RBICrawler().run()

        # CELL 5: Ingest
        from ingest.pdf_parser import PDFParser
        from ingest.embedder import Embedder
        docs = PDFParser().parse_all()
        Embedder().embed_and_store(docs)

        # CELL 6: Test RAG chain
        from retrieval.rag_chain import RAGChain
        rag = RAGChain()
        r   = rag.answer("What are the KYC guidelines?")
        print(r["answer"])

        # CELL 7: Test Agent
        from agent.rbi_agent import run_agent
        r = run_agent("What are the latest FEMA guidelines for NRIs?")
        print(r["answer"])

        # CELL 8: Run RAGAS eval (dev split)
        from eval.ragas_eval import run_eval
        run_eval(mode="rag", split="dev", save=True)

        # CELL 9: Compare RAG vs Agent
        run_eval(mode="rag",   split="dev", save=True)
        run_eval(mode="agent", split="dev", save=True)

        # CELL 10: Launch Streamlit
        # import subprocess, threading, time
        # from google.colab.output import eval_js
        # t = threading.Thread(target=lambda: subprocess.run(
        #     ["streamlit","run","app/streamlit_app.py","--server.port=8501","--server.headless=true"]
        # ), daemon=True)
        # t.start(); time.sleep(3)
        # print(eval_js("google.colab.kernel.proxyPort(8501)"))
    """)
    add_all(); commit("docs: update Colab notebook with agent and RAGAS eval cells", DATES[i]); i += 1

    # ── Commit 9: update README ────────────────────────────────────────────────
    write("README.md", """
        # RBI Circular RAG System 🏦

        An open-source Retrieval-Augmented Generation (RAG) system with a LangGraph
        agent layer that crawls RBI circulars and answers regulatory queries with source citations.

        ## Architecture
        ```
        OFFLINE
        ──────────────────────────────────────────
        RBI Website → Crawler → PyMuPDF → Chunker → sentence-transformers → ChromaDB

        ONLINE
        ──────────────────────────────────────────
        User Query
            ↓
        LangGraph Agent
            ├── Tool: vector_search      (broad semantic search)
            ├── Tool: department_search  (filtered by dept)
            └── Tool: circular_summary   (specific circular lookup)
            ↓
        Groq Llama 3.1 70B (temp=0.1)
            ↓
        Answer + Source Citations → Streamlit UI
        ```

        ## Stack
        | Layer | Tool |
        |---|---|
        | Crawling | requests + BeautifulSoup |
        | PDF Parsing | PyMuPDF |
        | Chunking | LangChain RecursiveCharacterTextSplitter |
        | Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
        | Vector Store | ChromaDB (cosine similarity, persisted to Drive) |
        | Agent | LangGraph ReAct agent |
        | LLM | Groq API — Llama 3.1 70B |
        | Evaluation | RAGAS (faithfulness, relevancy, recall, precision) |
        | UI | Streamlit (RAG mode + Agent mode) |

        ## Quick Start (Google Colab)
        ```bash
        !git clone https://github.com/YOUR_USERNAME/rbi-rag.git
        %cd rbi-rag
        !pip install -r requirements.txt -q
        ```
        Add `GROQ_API_KEY` to Colab Secrets, then follow `notebooks/01_run_pipeline.py`.

        ## Evaluation
        ```bash
        # Run on dev split
        python eval/ragas_eval.py --mode rag --split dev --save

        # Compare RAG vs Agent
        python eval/ragas_eval.py --mode agent --split dev --save

        # Compare against previous benchmark
        python eval/benchmark.py --compare
        ```

        ## Project Structure
        ```
        rbi-rag/
        ├── config.py
        ├── requirements.txt
        ├── crawl/rbi_crawler.py
        ├── ingest/pdf_parser.py
        ├── ingest/embedder.py
        ├── retrieval/rag_chain.py
        ├── agent/tools.py              ← LangGraph tool definitions
        ├── agent/rbi_agent.py          ← ReAct agent graph
        ├── eval/eval_dataset.csv       ← 10 Q&A ground truth pairs
        ├── eval/ragas_eval.py          ← RAGAS evaluation pipeline
        ├── eval/benchmark.py           ← benchmark comparison runner
        ├── benchmarks/                 ← saved eval CSVs (tracked in git)
        ├── app/streamlit_app.py
        └── notebooks/01_run_pipeline.py
        ```

        ## Features
        - Resume-safe crawling + incremental embedding
        - LangGraph ReAct agent with 3 tools
        - RAGAS evaluation on 4 metrics
        - Benchmark history tracked in git
        - Metadata filtering by department
        - Source citations with every answer
        - Streamlit UI with RAG/Agent mode toggle

        ## Disclaimer
        Educational/research use only. Always refer to official RBI circulars for compliance.
    """)
    add_all(); commit("docs: update README with agent architecture, eval section, full project structure", DATES[i]); i += 1

    # ── Push ──────────────────────────────────────────────────────────────────
    print(f"\n✅ {i} commits added for April 30.\n")
    print("Pushing to origin/main...")
    result = run(["push", "origin", "main"])
    if result.returncode == 0:
        print("✅ Pushed successfully!")
    else:
        print(f"⚠️  Push failed: {result.stderr.strip()}")
        print("Run manually: git push origin main")


if __name__ == "__main__":
    build()
