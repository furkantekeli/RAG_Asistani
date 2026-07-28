import math
from typing import List, Dict, Any, Tuple
from foundry_local_sdk import Configuration, FoundryLocalManager
import config


class EmbeddingService:
    """
    Handles initialization of Microsoft Foundry Local Embedding Model,
    embedding generation for text snippets/queries, and cosine similarity scoring.
    """

    def __init__(self, model_alias: str = config.EMBEDDING_MODEL_ALIAS, app_name: str = config.APP_NAME):
        self.model_alias = model_alias
        self.app_name = app_name
        self.client = None
        self._initialize_model()

    def _initialize_model(self) -> None:
        """Initializes and loads the Foundry Local embedding model."""
        try:
            cfg = Configuration(app_name=self.app_name)
            FoundryLocalManager.initialize(cfg)
        except Exception:
            pass
        manager = FoundryLocalManager.instance

        model = manager.catalog.get_model(self.model_alias)
        model.download()
        model.load()
        self.client = model.get_embedding_client()

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generates a vector embedding array for a given text string.
        """
        response = self.client.generate_embedding(text)
        return response.data[0].embedding

    @staticmethod
    def calculate_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        Calculates mathematical Cosine Similarity between two vector representations.
        Returns a float between -1.0 and 1.0 (typically 0.0 to 1.0 for embeddings).
        """
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm_a = math.sqrt(sum(a * a for a in vec1))
        norm_b = math.sqrt(sum(b * b for b in vec2))

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def find_top_relevant_chunks(
        self,
        query_vector: List[float],
        all_db_chunks: List[Tuple[int, str, int, str, List[float]]],
        top_k: int = config.TOP_K_RESULTS
    ) -> List[Dict[str, Any]]:
        """
        Calculates cosine similarity scores for all DB chunks against the query vector,
        sorts by score descending, and returns top K matching chunks with metadata.
        """
        scored_chunks = []

        for c_id, dosya_adi, chunk_idx, icerik, db_vector in all_db_chunks:
            score = self.calculate_cosine_similarity(query_vector, db_vector)
            scored_chunks.append({
                "id": c_id,
                "dosya_adi": dosya_adi,
                "chunk_index": chunk_idx,
                "icerik": icerik,
                "score": score
            })

        # Sort by similarity score descending
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        return scored_chunks[:top_k]
