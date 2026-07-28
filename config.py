import os
from pathlib import Path

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Database Config
DB_PATH = os.path.join(BASE_DIR, "rag_bilgi.db")

# Model Configuration
EMBEDDING_MODEL_ALIAS = "qwen3-embedding-0.6b"
LLM_MODEL_ALIAS = "phi-3.5-mini"
APP_NAME = "rag_asistanim"

# RAG & Chunking Parameters
CHUNK_SIZE = 500  # Max characters per chunk
CHUNK_OVERLAP = 50  # Character overlap between chunks
SIMILARITY_THRESHOLD = 0.30  # Cosine similarity cutoff threshold
TOP_K_RESULTS = 3  # Number of top relevant chunks to retrieve
