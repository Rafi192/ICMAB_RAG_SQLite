# indexing/faiss_index.py
import faiss
import pickle
import numpy as np
from ingestion.loaders import load_all
from ingestion.chunker import chunk_all
from ingestion.embedder import embed_texts
from config import settings

def build_index() -> tuple[faiss.Index, list[dict]]:
    print(" Loading data from SQLite...")
    raw = load_all()
    
    print("  Chunking...")
    chunks = chunk_all(raw)
    
    texts = [c["text"] for c in chunks]
    
    print(f" Embedding {len(texts)} chunks...")
    embeddings = embed_texts(texts)
    
    # L2-normalize for cosine similarity
    faiss.normalize_L2(embeddings)
    
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)   # Inner Product = cosine after normalize
    index.add(embeddings)
    
    # Save to disk
    faiss.write_index(index, settings.FAISS_INDEX_PATH)
    with open(settings.METADATA_PATH, "wb") as f:
        pickle.dump(chunks, f)
    
    print(f" Index built: {index.ntotal} vectors, dim={dim}")
    return index, chunks


def load_index() -> tuple[faiss.Index, list[dict]]:
    index = faiss.read_index(settings.FAISS_INDEX_PATH)
    with open(settings.METADATA_PATH, "rb") as f:
        chunks = pickle.load(f)
    return index, chunks