import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen3:4b-instruct-2507-q4_K_M"
DEFAULT_XAI_MODEL = "grok-4.7"
DEFAULT_TIMEOUT_SECONDS = 120.0
MAX_TIMEOUT_SECONDS = 600.0
# Chat Completions reasoning_effort. Omitted, the API uses high.
DEFAULT_XAI_REASONING_EFFORT = "low"
XAI_REASONING_EFFORTS = frozenset({"low", "medium", "high", "xhigh"})
# Visible output cap sent as max_completion_tokens. On this endpoint the
# cap does not include reasoning tokens, so 1200 is room for the complete
# analysis JSON. It matches the reply room reserved for Ollama.
DEFAULT_XAI_MAX_COMPLETION_TOKENS = 1200
MAX_XAI_COMPLETION_TOKENS = 128_000
LOCAL_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


@dataclass(frozen=True)
class Settings:
    base_url: str
    model: str
    timeout_seconds: float
    provider: str = "ollama"
    reasoning_effort: str = DEFAULT_XAI_REASONING_EFFORT
    max_completion_tokens: int = DEFAULT_XAI_MAX_COMPLETION_TOKENS
    config_error: str | None = None


def load_local_env(path: Path | None = None) -> None:
    """Load a local env file into the process.

    Existing variables win, so a test or a shell export is left as it is.
    Values are never logged. Tests set TINYDESK_LOAD_DOTENV=0 so the real
    local file, which may hold an API key, is not read.
    """
    if path is None and os.environ.get("TINYDESK_LOAD_DOTENV") == "0":
        return
    file = LOCAL_ENV_FILE if path is None else path
    try:
        text = file.read_text(encoding="utf-8")
    except OSError:
        return
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or not key.replace("_", "").isalnum() or key in os.environ:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ[key] = value


def load_settings() -> Settings:
    load_local_env()
    base_url = os.environ.get("OLLAMA_BASE_URL", DEFAULT_BASE_URL).strip() or DEFAULT_BASE_URL
    provider = os.environ.get("TINYDESK_AI_PROVIDER", "").strip().lower()
    if provider in {"", "ollama"}:
        provider = "ollama"
        model = os.environ.get("OLLAMA_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    elif provider == "xai":
        model = os.environ.get("XAI_MODEL", "").strip() or DEFAULT_XAI_MODEL
    else:
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
    effort, cap, config_error = _xai_generation(provider)
    return Settings(base_url.rstrip("/"), model, timeout, provider, effort, cap, config_error)


def _xai_generation(provider: str) -> tuple[str, int, str | None]:
    """Reasoning effort and visible output cap. Ignored unless provider is xai."""
    effort = DEFAULT_XAI_REASONING_EFFORT
    cap = DEFAULT_XAI_MAX_COMPLETION_TOKENS
    if provider != "xai":
        return effort, cap, None
    raw_effort = os.environ.get("XAI_REASONING_EFFORT", "").strip().lower()
    if raw_effort:
        if raw_effort not in XAI_REASONING_EFFORTS:
            return effort, cap, "bad_reasoning_effort"
        effort = raw_effort
    raw_cap = os.environ.get("XAI_MAX_COMPLETION_TOKENS", "").strip()
    if not raw_cap:
        return effort, cap, None
    if not raw_cap.isdecimal():
        return effort, cap, "bad_output_cap"
    parsed_cap = int(raw_cap)
    if not 1 <= parsed_cap <= MAX_XAI_COMPLETION_TOKENS:
        return effort, cap, "bad_output_cap"
    return effort, parsed_cap, None
