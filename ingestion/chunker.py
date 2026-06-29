# ingestion/chunker.py
from config import settings

def chunk_text(text: str, size: int = settings.CHUNK_SIZE,
               overlap: int = settings.CHUNK_OVERLAP) -> list[str]:
    """Word-based chunker with overlap."""
    words = text.split()
    if len(words) <= size:
        return [text]          # short enough — keep as one chunk
    chunks = []
    start = 0
    while start < len(words):
        end = start + size
        chunks.append(" ".join(words[start:end]))
        start += size - overlap
    return chunks


def chunk_all(raw_chunks: list[dict]) -> list[dict]:
    """
    For short entries (FAQ, members, admissions) → keep as-is.
    For long entries (notices, events, articles) → split with overlap.
    """
    final = []
    SHORT_TABLE = {"faq", "members", "admission", "cpd"}

    for chunk in raw_chunks:
        if chunk["source_table"] in SHORT_TABLE:
            final.append(chunk)
        else:
            sub_texts = chunk_text(chunk["text"])
            for i, sub in enumerate(sub_texts):
                new_chunk = chunk.copy()
                new_chunk["text"] = sub
                new_chunk["chunk_index"] = i   # track position
                final.append(new_chunk)
    return final