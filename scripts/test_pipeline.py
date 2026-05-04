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
    print("\n── RBI RAG Pipeline Test ──────────────────────────")

    # Check collection has data
    try:
        count = Embedder().collection.count()
    except Exception as e:
        print(f"\n❌ Cannot connect to vector store: {e}")
        print("   Run ingestion first: python scripts/run_ingestion.py")
        return

    if count == 0:
        print("\n❌ Vector store is empty. Run ingestion first.")
        return

    print(f"\n✅ Vector store: {count:,} chunks")

    # Load RAG chain
    try:
        rag = RAGChain(use_rewriter=True)
        print("✅ RAGChain loaded\n")
    except ValueError as e:
        print(f"\n❌ {e}")
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
            print(f"   Error: {e}\n")
            failed += 1

    print(f"── Results: {passed} passed, {failed} failed ──────────────")


if __name__ == "__main__":
    main()
