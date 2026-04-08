# ingest/pdf_parser.py — PDF parser skeleton
import fitz
import logging
from pathlib import Path
from langchain.schema import Document

log = logging.getLogger(__name__)


class PDFParser:
    def __init__(self):
        pass

    def extract_text(self, pdf_path: Path) -> list:
        # TODO: page-by-page extraction
        pass

    def parse_pdf_to_documents(self, pdf_path: Path) -> list:
        # TODO: chunk + attach metadata
        pass

    def parse_all(self, limit=None) -> list:
        # TODO: iterate all PDFs in data/pdfs/
        pass
