# app/embedder.py
import os
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

# ✅ Import updated guardrails
from app.guardrails import apply_guardrails

MODEL_NAME_ENV = "SBERT_MODEL"


class SBERTEmbedder:
    """
    Sentence-BERT Embedder with Guardrails.
    Ensures all text is sanitized (Presidio + Semantic) before embedding.
    """

    def __init__(self, model_name: str = None, batch_size: int = 32, debug: bool = False):
        self.model_name = model_name or os.getenv(MODEL_NAME_ENV, "all-MiniLM-L6-v2")
        self.model = SentenceTransformer(self.model_name)
        self.batch_size = batch_size
        self.debug = debug

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Sanitize input texts using guardrails and generate embeddings.
        """
        # ✅ Apply guardrails to every text
        safe_texts = [apply_guardrails(t) for t in texts]

        # 🛠 Optional debug logging
        if self.debug:
            for original, sanitized in zip(texts, safe_texts):
                if original != sanitized:
                    print("[Guardrails] Redaction applied before embedding:")
                    print(" - Original:", original[:200])  # show snippet
                    print(" - Sanitized:", sanitized[:200])

        # ✅ Encode with Sentence-BERT
        embs = self.model.encode(
            safe_texts,
            convert_to_numpy=True,
            show_progress_bar=False,
            batch_size=self.batch_size
        )
        return embs
