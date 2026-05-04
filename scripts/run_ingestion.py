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
