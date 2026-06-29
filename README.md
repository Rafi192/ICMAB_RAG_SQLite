# ICMAB_RAG_SQLite

#### model Architecture

`bash`

`
┌─────────────────────────────────────────────────────────┐
│                    INGESTION PIPELINE                    │
│                  (runs at startup + /admin/reindex)      │
│                                                         │
│  SQLite DB → Table Loaders → HTML Stripper → Chunker   │
│            → Embedder (BGE-M3) → FAISS Index Builder   │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    FAISS INDEX (RAM)                     │
│         + metadata.pkl (chunk text + source info)       │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                   RETRIEVAL PIPELINE                     │
│                                                         │
│  User Query → Embed → FAISS Top-20 → Cross-Encoder     │
│             Rerank → Top-5 → LLM → Answer              │
└─────────────────────────────────────────────────────────┘

`