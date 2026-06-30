# retrieval/retriever.py
import numpy as np
import faiss
import pickle
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from ingestion.embedder import embed_texts
from config import settings

logger = logging.getLogger(__name__)

VECTOR_STORE_PATH = Path(settings.VECTOR_STORE_PATH)


class Retriever:

    def __init__(self):
        self.indexes: dict[str, faiss.Index] = {}
        self.documents: dict[str, list[dict]] = {}

    # ==========================================================
    # Index Loading (lazy — only loads what's requested)
    # ==========================================================

    def load_index(self, table_name: str) -> bool:
        index_path = VECTOR_STORE_PATH / f"{table_name}_index.bin"
        metadata_path = VECTOR_STORE_PATH / f"{table_name}_documents.pkl"

        if not index_path.exists():
            logger.warning(f"No index found for '{table_name}' at {index_path}")
            return False

        self.indexes[table_name] = faiss.read_index(str(index_path))
        with open(metadata_path, "rb") as f:
            self.documents[table_name] = pickle.load(f)

        logger.info(f"Loaded '{table_name}' ({self.indexes[table_name].ntotal} vectors)")
        return True

    def load_all_indexes(self):
        bin_files = VECTOR_STORE_PATH.glob("*_index.bin")
        table_names = [f.stem.replace("_index", "") for f in bin_files]

        if not table_names:
            logger.warning(f"No index files found in {VECTOR_STORE_PATH}. Run /admin/reindex first.")
            return

        for name in table_names:
            self.load_index(name)

        logger.info(f"Loaded {len(self.indexes)} indexes")

    # ==========================================================
    # Core Search (per table)
    # ==========================================================

    def search_table(self, query: str, table_name: str, top_k: int = 10) -> List[Dict[str, Any]]:
        if table_name not in self.indexes:
            loaded = self.load_index(table_name)
            if not loaded:
                return []

        q_emb = embed_texts([query])
        faiss.normalize_L2(q_emb)

        index = self.indexes[table_name]
        actual_k = min(top_k, index.ntotal)

        scores, indices = index.search(q_emb, actual_k)

        docs = self.documents[table_name]
        results = []

        for idx, score in zip(indices[0], scores[0]):
            if idx < 0 or idx >= len(docs):
                continue
            chunk = docs[idx].copy()
            chunk["retrieval_score"] = float(score)
            results.append(chunk)

        logger.info(f"[{table_name}] hits={len(results)} query='{query}'")
        return results

    # ==========================================================
    # Single Table Retrieval
    # ==========================================================

    def retrieve_single_table(self, query: str, table_name: str, top_k: int = 10) -> List[Dict[str, Any]]:
        clean_query = query.strip()
        results = self.search_table(clean_query, table_name, top_k=top_k)
        results.sort(key=lambda x: x["retrieval_score"], reverse=True)
        return results[:top_k]

    # ==========================================================
    # Multi Table Retrieval — fair per-table representation
    # ==========================================================

    def retrieve_multi_table(self, query: str, top_k: int = 10, min_per_table: int = 3) -> List[Dict[str, Any]]:
        clean_query = query.strip()

        if len(clean_query.split()) < 1:
            logger.warning("Query too vague")
            return []

        if not self.indexes:
            self.load_all_indexes()

        if not self.indexes:
            logger.error("No indexes available.")
            return []

        # reserve slots per table so small tables (e.g. members)
        # are never drowned out by larger ones (e.g. notices/events)
        per_table_k = max(min_per_table, top_k // len(self.indexes))

        all_results = []
        for table_name in self.indexes.keys():
            hits = self.search_table(clean_query, table_name, top_k=per_table_k)
            all_results.extend(hits)

        all_results.sort(key=lambda x: x["retrieval_score"], reverse=True)
        final = all_results[:top_k]

        logger.info(f"Retrieved {len(final)} chunks across {len(self.indexes)} tables")
        return final

    # ==========================================================
    # Entry point
    # ==========================================================

    def retrieve(self, query: str, top_k: int = None, table_name: Optional[str] = None) -> List[Dict[str, Any]]:
        top_k = top_k or settings.TOP_K_RETRIEVE

        if table_name:
            return self.retrieve_single_table(query, table_name, top_k=top_k)

        return self.retrieve_multi_table(query, top_k=top_k)


# module-level singleton — reused across requests, loads indexes lazily
_retriever_instance = None

def get_retriever() -> Retriever:
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = Retriever()
    return _retriever_instance