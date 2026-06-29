# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, Header, HTTPException, BackgroundTasks
from pydantic import BaseModel
import asyncio

from indexing.faiss_index import build_index, load_index
from retrieval.retriever import retrieve
from retrieval.reranker import rerank
from llm.generator import generate
from config import settings
import os

# ── State ───────────────────────────────────────────────
class AppState:
    index = None
    metadata = None
    is_reindexing = False

state = AppState()

# ── Startup ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.path.exists(settings.FAISS_INDEX_PATH):
        print("📂 Loading existing index...")
        state.index, state.metadata = load_index()
    else:
        print("🔨 No index found, building fresh...")
        state.index, state.metadata = build_index()
    yield

app = FastAPI(lifespan=lifespan)

# ── Chat Endpoint ────────────────────────────────────────
class ChatRequest(BaseModel):
    query: str

@app.post("/chat")
async def chat(req: ChatRequest):
    if state.index is None:
        raise HTTPException(503, "Index not ready yet")
    
    candidates = retrieve(req.query, state.index, state.metadata)
    top_chunks = rerank(req.query, candidates)
    result = generate(req.query, top_chunks)
    return result

# ── Admin Reindex ────────────────────────────────────────
@app.post("/admin/reindex")
async def reindex(background_tasks: BackgroundTasks,
                  x_api_key: str = Header(...)):
    if x_api_key != settings.ADMIN_API_KEY:
        raise HTTPException(403, "Unauthorized")
    if state.is_reindexing:
        return {"status": "already_running"}
    
    def rebuild():
        state.is_reindexing = True
        try:
            new_index, new_meta = build_index()
            state.index = new_index      # hot-swap
            state.metadata = new_meta
        finally:
            state.is_reindexing = False
    
    background_tasks.add_task(rebuild)
    return {"status": "started"}

@app.get("/admin/reindex/status")
async def reindex_status():
    return {"is_reindexing": state.is_reindexing}

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "chunks_indexed": len(state.metadata) if state.metadata else 0
    }