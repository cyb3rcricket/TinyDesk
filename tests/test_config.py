from backend.config import load_settings


def test_defaults(monkeypatch):
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    monkeypatch.delenv("OLLAMA_TIMEOUT_SECONDS", raising=False)
    settings = load_settings()
    assert settings.base_url == "http://127.0.0.1:11434"
    assert settings.model == "llama3.2:3b"
    assert settings.timeout_seconds == 120


def test_environment_overrides(monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:11435/")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.2:1b")
    monkeypatch.setenv("OLLAMA_TIMEOUT_SECONDS", "30")
    settings = load_settings()
    assert settings.base_url == "http://127.0.0.1:11435"
    assert settings.model == "llama3.2:1b"
    assert settings.timeout_seconds == 30


def test_invalid_timeout_uses_the_default(monkeypatch):
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    for raw in ("nope", "0", "-5", "900"):
        monkeypatch.setenv("OLLAMA_TIMEOUT_SECONDS", raw)
        assert load_settings().timeout_seconds == 120
