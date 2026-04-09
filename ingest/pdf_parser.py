# ingest/pdf_parser.py
import sys, logging
import fitz
from pathlib import Path
from langchain.schema import Document
sys.path.append(str(Path(__file__).parent.parent))
from config import PDF_DIR

log = logging.getLogger(__name__)


class PDFParser:
    def __init__(self):
        pass

    def extract_text(self, pdf_path: Path) -> list:
        pages = []
        try:
            doc = fitz.open(str(pdf_path))
            for num, page in enumerate(doc, 1):
                text = page.get_text("text").strip()
                if len(text) < 50:
                    continue    # skip near-empty/scanned pages
                pages.append({"page_num": num, "text": text})
            doc.close()
        except Exception as e:
            log.error(f"{pdf_path.name}: {e}")
        return pages

    def parse_pdf_to_documents(self, pdf_path: Path) -> list:
        # TODO: chunk + metadata
        pass

    def parse_all(self, limit=None) -> list:
        pdfs = sorted(PDF_DIR.glob("*.pdf"))
        if limit: pdfs = pdfs[:limit]
        return [doc for p in pdfs for doc in (self.parse_pdf_to_documents(p) or [])]
