# indexing/faiss_index.py
import faiss
import pickle
from pathlib import Path
from ingestion.loaders import load_all
from ingestion.chunker import chunk_all
from ingestion.embedder import embed_texts
from config import settings

VECTOR_STORE_PATH = Path(settings.VECTOR_STORE_PATH)
VECTOR_STORE_PATH.mkdir(parents=True, exist_ok=True)


def build_indexes() -> dict[str, list[dict]]:
    
    print(" Loading data from SQLite...")
    raw = load_all()

    print("  Chunking...")
    chunks = chunk_all(raw)

    # group chunks by collection (source_table)
    by_collection: dict[str, list[dict]] = {}
    for c in chunks:
        by_collection.setdefault(c["source_table"], []).append(c)

    for collection_name, docs in by_collection.items():
        texts = [d["text"] for d in docs]

        print(f" Embedding '{collection_name}' ({len(texts)} chunks)...")
        embeddings = embed_texts(texts)
        faiss.normalize_L2(embeddings)

        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)   # Inner Product = cosine after normalize
        index.add(embeddings)

        index_path = VECTOR_STORE_PATH / f"{collection_name}_index.bin"
        docs_path = VECTOR_STORE_PATH / f"{collection_name}_documents.pkl"

        faiss.write_index(index, str(index_path))
        with open(docs_path, "wb") as f:
            pickle.dump(docs, f)

        print(f" {collection_name}: {index.ntotal} vectors, dim={dim}")

    print(f" Built {len(by_collection)} collection indexes: {list(by_collection.keys())}")
    return by_collection


def list_available_collections() -> list[str]:
    """Returns collection names that already have a built index on disk."""
    bin_files = VECTOR_STORE_PATH.glob("*_index.bin")
    return [f.stem.replace("_index", "") for f in bin_files]


def indexes_exist() -> bool:
    """Check if any indexes have been built yet."""
    return len(list_available_collections()) > 0




# # indexing/faiss_index.py
# import faiss
# import pickle
# import numpy as np
# from ingestion.loaders import load_all
# from ingestion.chunker import chunk_all
# from ingestion.embedder import embed_texts
# from config import settings

# def build_index() -> tuple[faiss.Index, list[dict]]:
#     print(" Loading data from SQLite...")
#     raw = load_all()
    
#     print("  Chunking...")
#     chunks = chunk_all(raw)
    
#     texts = [c["text"] for c in chunks]
    
#     print(f" Embedding {len(texts)} chunks...")
#     embeddings = embed_texts(texts)
    
#     # L2-normalize for cosine similarity
#     faiss.normalize_L2(embeddings)
    
#     dim = embeddings.shape[1]
#     index = faiss.IndexFlatIP(dim)   # Inner Product = cosine after normalize
#     index.add(embeddings)
    
#     # Save to disk
#     faiss.write_index(index, settings.FAISS_INDEX_PATH)
#     with open(settings.METADATA_PATH, "wb") as f:
#         pickle.dump(chunks, f)
    
#     print(f" Index built: {index.ntotal} vectors, dim={dim}")
#     return index, chunks


# def load_index() -> tuple[faiss.Index, list[dict]]:
#     index = faiss.read_index(settings.FAISS_INDEX_PATH)
#     with open(settings.METADATA_PATH, "rb") as f:
#         chunks = pickle.load(f)
#     return index, chunks