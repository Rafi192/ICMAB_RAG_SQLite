# ingestion/embedder.py
import numpy as np
from FlagEmbedding import BGEM3FlagModel
from config import settings

_model = None

def get_model():
    global _model
    if _model is None:
        _model = BGEM3FlagModel(settings.EMBED_MODEL, use_fp16=True)
    return _model

def embed_texts(texts: list[str]) -> np.ndarray:
    model = get_model()
    result = model.encode(
        texts,
        batch_size=32,
        max_length=512,
        return_dense=True
    )
    return np.array(result["dense_vecs"], dtype=np.float32)