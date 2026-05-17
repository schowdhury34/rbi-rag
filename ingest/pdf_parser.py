# ingest/pdf_parser.py
import sys, re, logging
import fitz, pandas as pd
from pathlib import Path
from tqdm import tqdm
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
sys.path.append(str(Path(__file__).parent.parent))
from config import PDF_DIR, METADATA_FILE, CHUNK_SIZE, CHUNK_OVERLAP

log = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """
    Clean extracted PDF text:
    - Remove repeated whitespace and newlines
    - Remove page numbers (standalone digits)
    - Remove RBI header/footer boilerplate
    """
    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove standalone page numbers
    text = re.sub(r"(?m)^\s*\d{1,3}\s*$", "", text)
    # Remove common RBI header noise
    text = re.sub(r"Reserve Bank of India\s*", "", text, flags=re.IGNORECASE)
    # Collapse multiple spaces
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


class PDFParser:
    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        self.meta_df = (
            pd.read_csv(METADATA_FILE).set_index("filename")
            if METADATA_FILE.exists() else None
        )

    def extract_text(self, pdf_path: Path) -> list:
        pages = []
        try:
            doc = fitz.open(str(pdf_path))

            # Skip password-protected PDFs
            if doc.needs_pass:
                log.warning(f"Skipping password-protected: {pdf_path.name}")
                doc.close()
                return []

            for num, page in enumerate(doc, 1):
                try:
                    text = clean_text(page.get_text("text"))
                    if len(text) < 50:
                        continue
                    pages.append({"page_num": num, "text": text})
                except Exception as e:
                    log.warning(f"Page {num} error in {pdf_path.name}: {e}")
                    continue
            doc.close()

        except fitz.FileDataError:
            log.error(f"Corrupted PDF, skipping: {pdf_path.name}")
        except Exception as e:
            log.error(f"Unexpected error {pdf_path.name}: {e}")

        return pages

    def _get_meta(self, filename: str) -> dict:
        if self.meta_df is not None and filename in self.meta_df.index:
            r = self.meta_df.loc[filename]
            return {k: r.get(k, "") for k in ["circular_no", "date", "subject", "department"]}
        return {"circular_no": Path(filename).stem, "date": "", "subject": "", "department": ""}

    def parse_pdf_to_documents(self, pdf_path: Path) -> list:
        pages = self.extract_text(pdf_path)
        if not pages:
            return []
        meta = self._get_meta(pdf_path.name)
        docs = []
        for page in pages:
            for idx, chunk in enumerate(self.splitter.split_text(page["text"])):
                docs.append(Document(
                    page_content=chunk,
                    metadata={**meta, "source": pdf_path.name,
                              "page": page["page_num"], "chunk_id": idx}
                ))
        return docs

    def parse_all(self, limit=None) -> list:
        pdfs = sorted(PDF_DIR.glob("*.pdf")) + sorted(PDF_DIR.glob("*.PDF"))
        if limit:
            pdfs = pdfs[:limit]
        log.info(f"Parsing {len(pdfs)} PDFs...")
        all_docs = []
        for p in tqdm(pdfs, desc="Parsing"):
            all_docs.extend(self.parse_pdf_to_documents(p))
        log.info(f"Total chunks: {len(all_docs)}")
        return all_docs
