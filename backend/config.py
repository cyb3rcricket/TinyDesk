import os
from dataclasses import dataclass

DEFAULT_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "llama3.2:3b"
DEFAULT_TIMEOUT_SECONDS = 120.0
MAX_TIMEOUT_SECONDS = 600.0


@dataclass(frozen=True)
class Settings:
    base_url: str
    model: str
    timeout_seconds: float


def load_settings() -> Settings:
    base_url = os.environ.get("OLLAMA_BASE_URL", DEFAULT_BASE_URL).strip() or DEFAULT_BASE_URL
    model = os.environ.get("OLLAMA_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    timeout = DEFAULT_TIMEOUT_SECONDS
    raw_timeout = os.environ.get("OLLAMA_TIMEOUT_SECONDS", "").strip()
    if raw_timeout:
        try:
            parsed = float(raw_timeout)
        except ValueError:
            parsed = 0
        if 0 < parsed <= MAX_TIMEOUT_SECONDS:
            timeout = parsed
    return Settings(base_url.rstrip("/"), model, timeout)
