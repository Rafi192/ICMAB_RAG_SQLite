# test_retrieval.py
from indexing.faiss_index import build_indexes, indexes_exist
from retrieval.retriever import get_retriever
from config import settings

# Build indexes only if none exist yet on disk
if not indexes_exist():
    print("No indexes found, building...")
    build_indexes()

retriever = get_retriever()

query = "who is the director of ICMAB"

print(f"\n{'='*60}")
print(f"Query: {query}")
print(f"{'='*60}\n")

print("--- Multi-collection retrieval (fair per-collection share) ---")
candidates = retriever.retrieve(query, top_k=10)
for c in candidates:
    print(f"{c['retrieval_score']:.4f} | {c['source_table']:12} | {c['title']}")

print("\n--- Single-collection retrieval (members only) ---")
member_results = retriever.retrieve(query, top_k=5, collection_name="members")
for c in member_results:
    print(f"{c['retrieval_score']:.4f} | {c['source_table']:12} | {c['title']}")