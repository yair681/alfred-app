import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

def _require(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise RuntimeError(f"Missing required env var: {key}")
    return val

GROQ_API_KEY = _require("GROQ_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/conversations.db")
MAX_HISTORY = int(os.getenv("MAX_HISTORY", "20"))

_spec_path = Path(__file__).parent.parent / "spec.json"
with open(_spec_path, encoding="utf-8") as f:
    SPEC = json.load(f)
