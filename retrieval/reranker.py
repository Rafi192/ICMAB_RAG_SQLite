# retrieval/reranker.py
from sentence_transformers import CrossEncoder
from config import settings

_reranker = None

def get_reranker():
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder(settings.RERANK_MODEL)
    return _reranker

def rerank(query: str, chunks: list[dict]) -> list[dict]:
    reranker = get_reranker()
    pairs = [(query, c["text"]) for c in chunks]
    scores = reranker.predict(pairs)
    
    for chunk, score in zip(chunks, scores):
        chunk["rerank_score"] = float(score)
    
    ranked = sorted(chunks, key=lambda x: x["rerank_score"], reverse=True)
    return ranked[:settings.TOP_K_RERANK]