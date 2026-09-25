import os
import secrets

from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
CHROMA_DIR = os.environ.get("CHROMA_DIR", "./chroma_store")
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "./uploads")
DB_PATH = os.environ.get("DB_PATH", "./paperpilot.db")
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "150"))
CORS_ORIGIN = os.environ.get("CORS_ORIGIN", "http://localhost:3000")

SECRET_KEY = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY:
    # dev fallback so a missing .env doesn't hard-crash local runs; every
    # restart invalidates existing tokens, which is fine for dev but not
    # for prod, so deployments must set a real SECRET_KEY explicitly.
    SECRET_KEY = secrets.token_hex(32)


def require_groq_key() -> str:
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    return GROQ_API_KEY
