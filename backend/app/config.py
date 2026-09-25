import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434"
)

LLM_MODEL = os.getenv(
    "LLM_MODEL",
    "qwen3:8b"
)

# PostgreSQL / Database Configuration
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "mitraai")

if POSTGRES_PASSWORD:
    DEFAULT_DB_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
else:
    DEFAULT_DB_URL = f"postgresql://{POSTGRES_USER}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)