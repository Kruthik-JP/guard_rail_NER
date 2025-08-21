# app/chroma_client.py
import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
import numpy as np

# ✅ Import unified guardrails
from app.guardrails import apply_guardrails

CHROMA_DIR_ENV = "CHROMA_DB_DIR"

class ChromaClient:
    def __init__(self, persist_dir: Optional[str] = None):
        persist_dir = persist_dir or os.getenv(CHROMA_DIR_ENV, "./chroma_db")
        settings = Settings(chroma_db_impl="duckdb+parquet", persist_directory=persist_dir)
        self.client = chromadb.Client(settings=settings)
        self.collection = self._get_or_create_collection("resumes")

    def _get_or_create_collection(self, name: str):
        if name in [c.name for c in self.client.list_collections()]:
            return self.client.get_collection(name)
        else:
            return self.client.create_collection(name)

    def upsert_documents(self, ids: List[str], embeddings: np.ndarray, metadatas: List[Dict[str, Any]], documents: List[str]):
        # ✅ Apply guardrails to all documents before insertion
        safe_documents = [apply_guardrails(doc) for doc in documents]
        embs_list = embeddings.tolist() if isinstance(embeddings, np.ndarray) else embeddings
        self.collection.add(
            ids=ids,
            embeddings=embs_list,
            metadatas=metadatas,
            documents=safe_documents
        )

    def query_similar(self, query_embedding: np.ndarray, top_k: int = 5):
        q_emb = query_embedding.tolist() if isinstance(query_embedding, np.ndarray) else query_embedding
        results = self.collection.query(
            query_embeddings=[q_emb],
            n_results=top_k,
            include=["metadatas", "documents", "distances"]
        )

        # ✅ Apply guardrails to documents in the results
        for doc_list in results.get("documents", []):
            for i in range(len(doc_list)):
                doc_list[i] = apply_guardrails(doc_list[i])

        return results
