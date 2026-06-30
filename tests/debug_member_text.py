# debug_member_text.py
from retrieval.retriever import get_retriever

retriever = get_retriever()
retriever.load_index("members")

for doc in retriever.documents["members"]:
    if "Mahbub-Ul-Alam" in doc["title"]:
        print(doc["text"])