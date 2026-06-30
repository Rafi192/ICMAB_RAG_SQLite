# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, Header, HTTPException, BackgroundTasks
from pydantic import BaseModel

from indexing.faiss_index import build_indexes, indexes_exist
from retrieval.retriever import get_retriever
from retrieval.reranker import get_reranker
from llm.generator import generate
from config import settings

from fastapi import FastAPI, Header, HTTPException, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

GREETINGS = {"hi", "hello", "hey", "hi!", "hello!", "good morning", "good evening"}

logger = logging.getLogger(__name__)
@asynccontextmanager
async def lifespan(app: FastAPI):
    if not indexes_exist():
        print("🔨 No indexes found, building fresh...")
        build_indexes()
    # warm up the retriever singleton (loads all per-table indexes lazily on first query)
    get_retriever()
    get_reranker()
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

retriever = get_retriever()
reranker = get_reranker()


@app.post("/api/chat/")
def chat(query: str = Form()):
    try:
        query_clean = query.strip().lower()

        if query_clean in GREETINGS:
            answer = "Hello! I'm ICMAB's AI assistant. How can I help you today?"
        else:
            chunks = retriever.retrieve(query, top_k=10)
            reranked = reranker.rerank(query, chunks, top_k=5)
            result = generate(query, reranked)
            answer = result["answer"]

        return JSONResponse(
            status_code=200,
            content={
                "status": True,
                "statuscode": 200,
                "text": {
                    "query": query,
                    "answer": answer
                }
            }
        )

    except Exception as ex:
        logger.exception("Chat endpoint failed")
        return JSONResponse(
            status_code=500,
            content={"status": False, "error": str(ex)}
        )


@app.post("/admin/reindex")
async def reindex(background_tasks: BackgroundTasks, x_api_key: str = Header(...)):
    global is_reindexing
    if x_api_key != settings.ADMIN_API_KEY:
        raise HTTPException(403, "Unauthorized")
    if is_reindexing:
        return {"status": "already_running"}

    def rebuild():
        global is_reindexing
        is_reindexing = True
        try:
            build_indexes()
            retriever.indexes.clear()
            retriever.documents.clear()
            retriever.load_all_indexes()
        finally:
            is_reindexing = False

    background_tasks.add_task(rebuild)
    return {"status": "started"}


@app.get("/admin/reindex/status")
async def reindex_status():
    return {"is_reindexing": is_reindexing}



@app.get("/health")
async def health():
    retriever = get_retriever()
    return {
        "status": "ok",
        "tables_loaded": list(retriever.indexes.keys()),
        "total_vectors": sum(idx.ntotal for idx in retriever.indexes.values())
    }