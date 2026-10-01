from types import SimpleNamespace

import httpx
import pytest
from ollama import ResponseError

from backend.config import Settings
from backend.ollama_client import CHAT_OPTIONS, ModelCallError, OllamaModelClient, build_client


def settings():
    return Settings("http://127.0.0.1:11434", "llama3.2:3b", 45)


class Stub:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.kwargs = None
        self.closed = False

    def chat(self, **kwargs):
        self.kwargs = kwargs
        if self.error:
            raise self.error
        return self.result

    def close(self):
        self.closed = True


def client_for(stub):
    return OllamaModelClient(settings(), client_factory=lambda active, timeout: stub)


def test_chat_uses_schema_temperature_and_closes_client():
    stub = Stub(result=SimpleNamespace(message=SimpleNamespace(content='{"ok": true}')))
    seen = {}

    def factory(active, timeout):
        seen["host"] = active.base_url
        seen["timeout"] = timeout
        return stub

    client = OllamaModelClient(settings(), client_factory=factory)
    raw = client.complete(
        model="llama3.2:3b",
        messages=[{"role": "user", "content": "ticket"}],
        schema={"type": "object"},
        timeout=45,
    )
    assert raw == '{"ok": true}'
    assert stub.kwargs["model"] == "llama3.2:3b"
    assert stub.kwargs["format"] == {"type": "object"}
    assert stub.kwargs["stream"] is False
    assert stub.kwargs["options"] == CHAT_OPTIONS
    assert seen["host"] == "http://127.0.0.1:11434"
    assert seen["timeout"] == 45
    assert stub.closed is True


def test_build_client_sets_host_and_read_timeout(monkeypatch):
    captured = {}

    class FakeClient:
        def __init__(self, host, timeout):
            captured["host"] = host
            captured["timeout"] = timeout

    monkeypatch.setattr("backend.ollama_client.Client", FakeClient)
    build_client(settings(), 45)
    assert captured["host"] == "http://127.0.0.1:11434"
    assert captured["timeout"].connect == 5
    assert captured["timeout"].read == 45


@pytest.mark.parametrize(
    ("error", "reason", "status"),
    [
        (httpx.ReadTimeout("slow"), "timeout", None),
        (httpx.ConnectTimeout("silent"), "unavailable", None),
        (ConnectionError("down"), "unavailable", None),
        (ResponseError("model 'llama3.2:3b' not found", 404), "model_missing", 404),
        (ResponseError("server error", 500), "bad_response", 500),
    ],
)
def test_ollama_errors_map_to_reasons(error, reason, status):
    stub = Stub(error=error)
    client = client_for(stub)
    with pytest.raises(ModelCallError) as caught:
        client.complete(model="llama3.2:3b", messages=[], schema={}, timeout=45)
    assert caught.value.reason == reason
    assert caught.value.status_code == status
    assert stub.closed is True


def test_empty_model_content_is_invalid_output():
    stub = Stub(result=SimpleNamespace(message=SimpleNamespace(content="  ")))
    client = client_for(stub)
    with pytest.raises(ModelCallError) as caught:
        client.complete(model="llama3.2:3b", messages=[], schema={}, timeout=45)
    assert caught.value.reason == "invalid_output"
    assert stub.closed is True
