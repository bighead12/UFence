import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
RULES_FILE = CONFIG_DIR / "fencing_rules.json"

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
WINNING_SCORE = int(os.getenv("WINNING_SCORE", "5"))

# RAG / Coach Chat settings
BOOKS_DIR = PROJECT_ROOT / "data" / "books"
VECTORSTORE_DIR = PROJECT_ROOT / "data" / "vectorstore"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))

def get_rules():
    import json
    with open(RULES_FILE, "r") as f:
        return json.load(f)