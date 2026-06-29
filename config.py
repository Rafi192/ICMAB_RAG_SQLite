from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SQLITE_PATH: str = "/opt/icmab/backend/ICMAB-Backend/db.sqlite3"
    EMBED_MODEL: str = "BAAI/bge-m3"
    RERANK_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    FAISS_INDEX_PATH: str = "data/index.faiss"
    METADATA_PATH: str = "data/metadata.pkl"
    TOP_K_RETRIEVE: int = 10      
    TOP_K_RERANK: int = 5         
    ADMIN_API_KEY: str = "your-secret-key"
    OPENAI_API_KEY: str = ""
    CHUNK_SIZE: int = 400         
    CHUNK_OVERLAP: int = 50

settings = Settings()