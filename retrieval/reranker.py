

# retrieval/reranker.py
import logging
from typing import List, Dict, Any
from sentence_transformers import CrossEncoder
from config import settings

logger = logging.getLogger(__name__)


class Reranker:
    """
    Cross-encoder reranker — reranks retrieved chunks by actual
    relevance to the query, not just embedding similarity.
    """

    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.RERANK_MODEL
        self.model = CrossEncoder(self.model_name)
        logger.info(f"Loaded reranker model: {self.model_name}")

    def rerank(self, query: str, chunks: List[Dict[str, Any]], top_k: int = None) -> List[Dict[str, Any]]:
        if not chunks:
            return []

        top_k = top_k or settings.TOP_K_RERANK

        pairs = [(query, chunk["text"]) for chunk in chunks]
        scores = self.model.predict(pairs)

        for chunk, score in zip(chunks, scores):
            chunk["rerank_score"] = float(score)

        reranked = sorted(chunks, key=lambda x: x["rerank_score"], reverse=True)
        final = reranked[:top_k]

        logger.info(f"Reranked {len(chunks)} → kept top {len(final)}")
        for i, chunk in enumerate(final):
            logger.info(
                f"[Reranker] #{i+1} | score={chunk.get('rerank_score', 0):.4f} | "
                f"collection={chunk.get('source_table', 'unknown')} | "
                f"text_preview={chunk.get('text', '')[:100]}"
            )
        return final


# module-level singleton — model loaded once, reused across requests
_reranker_instance = None

def get_reranker() -> Reranker:
    global _reranker_instance
    if _reranker_instance is None:
        _reranker_instance = Reranker()
    return _reranker_instance


# # retrieval/reranker.py
# from sentence_transformers import CrossEncoder
# from config import settings

# _reranker = None

# def get_reranker():
#     global _reranker
#     if _reranker is None:
#         _reranker = CrossEncoder(settings.RERANK_MODEL)
#     return _reranker

# def rerank(query: str, chunks: list[dict]) -> list[dict]:
#     reranker = get_reranker()
#     pairs = [(query, c["text"]) for c in chunks]
#     scores = reranker.predict(pairs)
    
#     for chunk, score in zip(chunks, scores):
#         chunk["rerank_score"] = float(score)
    
#     ranked = sorted(chunks, key=lambda x: x["rerank_score"], reverse=True)
#     return ranked[:settings.TOP_K_RERANK]


