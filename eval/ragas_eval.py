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

from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama

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

try:
    from agent.rbi_agent import run_agent
    AGENT_AVAILABLE = True
except ImportError:
    AGENT_AVAILABLE = False
    run_agent = None

from ingest.embedder import Embedder

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

EVAL_CSV  = Path(__file__).parent / "eval_dataset.csv"
BENCH_DIR = Path(__file__).parent.parent / "benchmarks"


def load_eval_data(split: str = "dev") -> pd.DataFrame:
    """
    Returns eval rows.
    split='dev'  -> first 7 rows  (tune on these)
    split='test' -> last 3 rows   (held-out, final eval only)
    split='all'  -> all rows
    """
    df = pd.read_csv(EVAL_CSV)
    if split == "dev":
        return df.iloc[:7].reset_index(drop=True)
    elif split == "test":
        return df.iloc[7:].reset_index(drop=True)
    return df


def build_ragas_dataset(df: pd.DataFrame, mode: str) -> Dataset:
    """
    Runs each question through the RAG system / agent,
    collects (question, answer, contexts, ground_truth).
    RAG answers use Groq (your actual system).
    """
    embedder = Embedder()

    if mode == "rag":
        rag = RAGChain(use_rewriter=False, use_ollama=True)
    elif mode == "agent" and not AGENT_AVAILABLE:
        raise RuntimeError("Agent mode not available — ToolNode import failed.")

    questions, answers, contexts, ground_truths = [], [], [], []

    for _, row in df.iterrows():
        q  = row["question"]
        gt = row["ground_truth"]
        log.info(f"Running: {q[:60]}...")

        if mode == "rag":
            result = rag.answer(q, return_sources=True)
            ans    = result["answer"]
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

    log.info("Setting up Ollama as RAGAS judge (local, free, no rate limits)...")
    evaluator_llm = LangchainLLMWrapper(ChatOllama(model="llama3.2", temperature=0))
    hf_embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    ragas_emb     = LangchainEmbeddingsWrapper(hf_embeddings)

    log.info("Running RAGAS metrics...")
    scores = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
        llm=evaluator_llm,
        embeddings=ragas_emb,
        raise_exceptions=False,
        batch_size=1,
    )

    results_df = scores.to_pandas()
    print("\n" + "=" * 55)
    print(f"  RAGAS Results | mode={mode} | split={split}")
    print("=" * 55)
    print(f"  Faithfulness      : {results_df['faithfulness'].mean():.3f}")
    print(f"  Answer Relevancy  : {results_df['answer_relevancy'].mean():.3f}")
    print(f"  Context Recall    : {results_df['context_recall'].mean():.3f}")
    print(f"  Context Precision : {results_df['context_precision'].mean():.3f}")
    print("=" * 55)

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