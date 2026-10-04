import os

from backend.config import load_local_env, load_settings


def test_defaults(monkeypatch):
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    monkeypatch.delenv("OLLAMA_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("TINYDESK_AI_PROVIDER", raising=False)
    monkeypatch.delenv("XAI_MODEL", raising=False)
    monkeypatch.delenv("XAI_REASONING_EFFORT", raising=False)
    monkeypatch.delenv("XAI_MAX_COMPLETION_TOKENS", raising=False)
    settings = load_settings()
    assert settings.base_url == "http://127.0.0.1:11434"
    assert settings.model == "qwen3:4b-instruct-2507-q4_K_M"
    assert settings.provider == "ollama"
    assert settings.timeout_seconds == 120
    assert settings.config_error is None


def test_environment_overrides(monkeypatch):
    monkeypatch.delenv("TINYDESK_AI_PROVIDER", raising=False)
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:11435/")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.2:1b")
    monkeypatch.setenv("OLLAMA_TIMEOUT_SECONDS", "30")
    settings = load_settings()
    assert settings.base_url == "http://127.0.0.1:11435"
    assert settings.model == "llama3.2:1b"
    assert settings.timeout_seconds == 30


def test_blank_provider_stays_on_ollama(monkeypatch):
    monkeypatch.setenv("TINYDESK_AI_PROVIDER", "  ")
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    settings = load_settings()
    assert settings.provider == "ollama"
    assert settings.model == "qwen3:4b-instruct-2507-q4_K_M"


def test_xai_provider_uses_the_configured_model(monkeypatch):
    monkeypatch.setenv("TINYDESK_AI_PROVIDER", "xai")
    monkeypatch.setenv("XAI_MODEL", "grok-4.7")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.2:3b")
    settings = load_settings()
    assert settings.provider == "xai"
    assert settings.model == "grok-4.7"


def test_xai_provider_defaults_the_model_name(monkeypatch):
    monkeypatch.setenv("TINYDESK_AI_PROVIDER", "XAI")
    monkeypatch.delenv("XAI_MODEL", raising=False)
    monkeypatch.delenv("XAI_REASONING_EFFORT", raising=False)
    monkeypatch.delenv("XAI_MAX_COMPLETION_TOKENS", raising=False)
    settings = load_settings()
    assert settings.provider == "xai"
    assert settings.model == "grok-4.7"
    assert settings.reasoning_effort == "low"
    assert settings.max_completion_tokens == 1200
    assert settings.config_error is None


def test_xai_reasoning_effort_accepts_high(monkeypatch):
    monkeypatch.setenv("TINYDESK_AI_PROVIDER", "xai")
    monkeypatch.setenv("XAI_REASONING_EFFORT", " High ")
    monkeypatch.setenv("XAI_MAX_COMPLETION_TOKENS", "800")
    settings = load_settings()
    assert settings.reasoning_effort == "high"
    assert settings.max_completion_tokens == 800
    assert settings.config_error is None


def test_xai_rejects_an_unknown_reasoning_effort(monkeypatch):
    monkeypatch.setenv("TINYDESK_AI_PROVIDER", "xai")
    monkeypatch.setenv("XAI_REASONING_EFFORT", "max")
    settings = load_settings()
    assert settings.provider == "xai"
    assert settings.config_error == "bad_reasoning_effort"


def test_xai_rejects_an_invalid_output_cap(monkeypatch):
    monkeypatch.setenv("TINYDESK_AI_PROVIDER", "xai")
    monkeypatch.delenv("XAI_REASONING_EFFORT", raising=False)
    for raw in ("0", "-5", "1200.5", "nope", "128001"):
        monkeypatch.setenv("XAI_MAX_COMPLETION_TOKENS", raw)
        assert load_settings().config_error == "bad_output_cap"


def test_ollama_ignores_invalid_xai_generation_settings(monkeypatch):
    monkeypatch.setenv("TINYDESK_AI_PROVIDER", "ollama")
    monkeypatch.setenv("XAI_REASONING_EFFORT", "max")
    monkeypatch.setenv("XAI_MAX_COMPLETION_TOKENS", "nope")
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    settings = load_settings()
    assert settings.provider == "ollama"
    assert settings.model == "qwen3:4b-instruct-2507-q4_K_M"
    assert settings.config_error is None


def test_local_env_fills_missing_values_and_does_not_override(monkeypatch, tmp_path):
    monkeypatch.delenv("TINYDESK_AI_PROVIDER", raising=False)
    monkeypatch.delenv("XAI_MODEL", raising=False)
    monkeypatch.setenv("XAI_API_KEY", "already-set")
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "# comment",
                "export TINYDESK_AI_PROVIDER=xai",
                "XAI_MODEL='grok-4.7'",
                "XAI_API_KEY=test-key",
                "",
            ]
        ),
        encoding="utf-8",
    )
    load_local_env(env_file)
    settings = load_settings()
    assert settings.provider == "xai"
    assert settings.model == "grok-4.7"
    assert os.environ["XAI_API_KEY"] == "already-set"
    # load_local_env writes these directly. Remove the test values when the
    # variables were absent, so a later test does not keep provider=xai.
    os.environ.pop("TINYDESK_AI_PROVIDER", None)
    os.environ.pop("XAI_MODEL", None)


def test_dotenv_skip_does_not_read_the_default_file(monkeypatch):
    monkeypatch.setenv("TINYDESK_LOAD_DOTENV", "0")
    monkeypatch.delenv("TINYDESK_AI_PROVIDER", raising=False)
    load_local_env()
    assert os.environ.get("TINYDESK_AI_PROVIDER") is None


def test_invalid_timeout_uses_the_default(monkeypatch):
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    for raw in ("nope", "0", "-5", "900"):
        monkeypatch.setenv("OLLAMA_TIMEOUT_SECONDS", raw)
        assert load_settings().timeout_seconds == 120
