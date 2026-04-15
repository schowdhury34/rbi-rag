# ingest/embedder.py — with incremental ingestion
import sys, logging
from pathlib import Path
from tqdm import tqdm
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from langchain.schema import Document
sys.path.append(str(Path(__file__).parent.parent))
from config import CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL, EMBEDDING_BATCH, TOP_K

log = logging.getLogger(__name__)


class Embedder:
    def __init__(self):
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        self.model  = SentenceTransformer(EMBEDDING_MODEL)
        self.client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
        )
        log.info(f"Collection has {self.collection.count()} chunks")

    def _chunk_id(self, doc: Document) -> str:
        m = doc.metadata
        return f"{m.get('source','x')}_p{m.get('page',0)}_c{m.get('chunk_id',0)}"

    def embed_and_store(self, documents: list, incremental: bool = True):
        if incremental:
            existing = set(self.collection.get(include=[])["ids"])
            documents = [d for d in documents if self._chunk_id(d) not in existing]
        if not documents:
            log.info("Nothing new to embed")
            return
        log.info(f"Embedding {len(documents)} new chunks...")
        for start in tqdm(range(0, len(documents), EMBEDDING_BATCH), desc="Embedding"):
            batch  = documents[start: start + EMBEDDING_BATCH]
            texts  = [d.page_content for d in batch]
            ids    = [self._chunk_id(d) for d in batch]
            metas  = [d.metadata for d in batch]
            embeds = self.model.encode(texts, convert_to_numpy=True).tolist()
            self.collection.upsert(ids=ids, documents=texts,
                                   embeddings=embeds, metadatas=metas)
        log.info(f"Total stored: {self.collection.count()}")

    def query(self, text: str, top_k: int = TOP_K, where: dict = None) -> list:
        emb = self.model.encode([text]).tolist()
        kw  = dict(query_embeddings=emb, n_results=top_k,
                   include=["documents", "metadatas", "distances"])
        if where: kw["where"] = where
        res = self.collection.query(**kw)
        return [{"text": t, "metadata": m, "distance": d}
                for t, m, d in zip(res["documents"][0],
                                   res["metadatas"][0],
                                   res["distances"][0])]
