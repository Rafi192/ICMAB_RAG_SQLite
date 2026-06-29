# ICMAB_RAG_SQLite

## Model Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                          INGESTION PIPELINE                                 │
│                   (Runs at startup and /admin/reindex)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ SQLite Database                                                             │
│        │                                                                    │
│        ▼                                                                    │
│ Table Loaders (Admission, News, Circular, etc.)                             │
│        │                                                                    │
│        ▼                                                                    │
│ HTML/Text Cleaning (Strip HTML, Normalize Text)                             │
│        │                                                                    │
│        ▼                                                                    │
│ Document Chunking                                                           │
│        │                                                                    │
│        ▼                                                                    │
│ Embedding Generation (BAAI/bge-m3)                                          │
│        │                                                                    │
│        ▼                                                                    │
│ FAISS Index Builder                                                         │
│        │                                                                    │
│        ├────────────► faiss.index                                           │
│        └────────────► metadata.pkl (Chunk Text + Source Metadata)           │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          KNOWLEDGE INDEX                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ • FAISS Vector Index (Embeddings)                                           │
│ • metadata.pkl (Chunk Text, Table Name, Record ID, URL, etc.)               │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          RETRIEVAL PIPELINE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ User Query                                                                  │
│        │                                                                    │
│        ▼                                                                    │
│ Query Preprocessing                                                         │
│        │                                                                    │
│        ▼                                                                    │
│ Query Embedding (BAAI/bge-m3)                                               │
│        │                                                                    │
│        ▼                                                                    │
│ FAISS Similarity Search (Top-20)                                            │
│        │                                                                    │
│        ▼                                                                    │
│ Cross-Encoder Reranking                                                     │
│ (cross-encoder/ms-marco-MiniLM-L-6-v2)                                      │
│        │                                                                    │
│        ▼                                                                    │
│ Select Top-5 Context Chunks                                                 │
│        │                                                                    │
│        ▼                                                                    │
│ Prompt Construction                                                         │
│        │                                                                    │
│        ▼                                                                    │
│ LLM (GPT-4.1 / GPT-5 / Compatible Model)                                    │
│        │                                                                    │
│        ▼                                                                    │
│ Final Answer + Source References                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```