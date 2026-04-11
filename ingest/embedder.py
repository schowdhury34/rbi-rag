# ingest/embedder.py — ChromaDB embedder (skeleton)
from langchain.schema import Document


class Embedder:
    def __init__(self):
        self.model      = None
        self.collection = None

    def embed_and_store(self, documents: list):
        pass

    def query(self, query_text: str, top_k: int = 5) -> list:
        pass
