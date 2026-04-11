# ingest/pdf_parser.py
import sys, logging
import fitz, pandas as pd
from pathlib import Path
from tqdm import tqdm
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
sys.path.append(str(Path(__file__).parent.parent))
from config import PDF_DIR, METADATA_FILE, CHUNK_SIZE, CHUNK_OVERLAP

log = logging.getLogger(__name__)


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
            for num, page in enumerate(doc, 1):
                text = page.get_text("text").strip()
                if len(text) < 50: continue
                pages.append({"page_num": num, "text": text})
            doc.close()
        except Exception as e:
            log.error(f"{pdf_path.name}: {e}")
        return pages

    def _get_meta(self, filename: str) -> dict:
        if self.meta_df is not None and filename in self.meta_df.index:
            r = self.meta_df.loc[filename]
            return {k: r.get(k, "") for k in ["circular_no", "date", "subject", "department"]}
        return {"circular_no": Path(filename).stem, "date": "", "subject": "", "department": ""}

    def parse_pdf_to_documents(self, pdf_path: Path) -> list:
        pages = self.extract_text(pdf_path)
        if not pages: return []
        meta  = self._get_meta(pdf_path.name)
        docs  = []
        for page in pages:
            for idx, chunk in enumerate(self.splitter.split_text(page["text"])):
                docs.append(Document(
                    page_content=chunk,
                    metadata={**meta, "source": pdf_path.name,
                              "page": page["page_num"], "chunk_id": idx}
                ))
        return docs

    def parse_all(self, limit=None) -> list:
        pdfs = sorted(PDF_DIR.glob("*.pdf"))
        if limit: pdfs = pdfs[:limit]
        log.info(f"Parsing {len(pdfs)} PDFs")
        return [doc for p in tqdm(pdfs, desc="Parsing") for doc in self.parse_pdf_to_documents(p)]
