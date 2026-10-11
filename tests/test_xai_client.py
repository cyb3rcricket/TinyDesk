import hashlib
import json

import httpx
import pytest

from backend.config import Settings
from backend.ollama_client import ModelCallError
from backend.xai_client import XaiModelClient, cost_usd_from_usage


def settings():
    return Settings("http://127.0.0.1:11434", "grok-4.7", 30, "xai")


def complete(client):
    return client.complete(
        model="grok-4.7",
        messages=[{"role": "user", "content": "ticket"}],
        schema={"type": "object", "properties": {"summary": {"type": "string"}}},
        timeout=30,
    )


def test_cost_ticks_convert_to_dollars():
    assert cost_usd_from_usage({"cost_in_usd_ticks": 37756000}) == pytest.approx(0.0037756)
    assert cost_usd_from_usage({}) is None
    assert cost_usd_from_usage({"cost_in_usd_ticks": True}) is None


def test_one_request_sends_schema_without_retry_and_trace_omits_the_key(monkeypatch, tmp_path):
    monkeypatch.setenv("XAI_API_KEY", "test-key")
    monkeypatch.setenv("TINYDESK_AI_TRACE", str(tmp_path / "trace.jsonl"))
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        assert request.headers["Authorization"] == "Bearer test-key"
        body = json.loads(request.content)
        assert body["model"] == "grok-4.7"
        assert body["temperature"] == 0
        assert body["stream"] is False
        assert body["reasoning_effort"] == "low"
        assert body["max_completion_tokens"] == 1200
        assert "max_tokens" not in body
        assert "reasoning" not in body
        assert "tools" not in body
        assert body["response_format"]["json_schema"]["strict"] is True
        assert body["response_format"]["json_schema"]["schema"]["additionalProperties"] is False
        if calls["n"] == 1:
            return httpx.Response(500, json={"error": {"message": "busy"}})
        return httpx.Response(200, json={"model": "grok-4.7", "choices": []})

    client = XaiModelClient(settings(), transport=httpx.MockTransport(handler))
    with pytest.raises(ModelCallError) as caught:
        complete(client)
    assert calls["n"] == 1
    assert caught.value.reason == "bad_response"
    assert "test-key" not in str(caught.value)
    trace = (tmp_path / "trace.jsonl").read_text(encoding="utf-8")
    assert "test-key" not in trace
    assert "Authorization" not in trace
    assert "Bearer" not in trace
    saved = json.loads(trace)
    assert saved["messages"] == [
        {
            "role": "user",
            "chars": 6,
            "sha256": hashlib.sha256(b"ticket").hexdigest(),
        }
    ]
    assert saved["requested_model"] == "grok-4.7"


def test_success_returns_content_and_records_api_cost(monkeypatch, tmp_path):
    monkeypatch.setenv("XAI_API_KEY", "test-key")
    monkeypatch.setenv("TINYDESK_AI_TRACE", str(tmp_path / "trace.jsonl"))

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "model": "grok-4.7",
                "choices": [{"message": {"content": "{\"summary\":\"Paper out.\"}"}}],
                "usage": {
                    "prompt_tokens": 20,
                    "completion_tokens": 5,
                    "cost_in_usd_ticks": 50000000,
                },
            },
        )

    client = XaiModelClient(settings(), transport=httpx.MockTransport(handler))
    assert complete(client) == "{\"summary\":\"Paper out.\"}"
    saved = json.loads((tmp_path / "trace.jsonl").read_text(encoding="utf-8"))
    assert saved["returned_model"] == "grok-4.7"
    assert saved["cost_usd"] == pytest.approx(0.005)
    assert saved["usage"]["prompt_tokens"] == 20
    assert saved["completion_status"] == "complete"
    assert saved["request_settings"]["endpoint"] == "https://api.x.ai/v1/chat/completions"
    assert saved["request_settings"]["reasoning_effort"] == "low"
    assert saved["request_settings"]["max_completion_tokens"] == 1200


def test_missing_key_does_not_call_the_network(monkeypatch):
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json={})

    client = XaiModelClient(settings(), transport=httpx.MockTransport(handler))
    with pytest.raises(ModelCallError) as caught:
        complete(client)
    assert calls["n"] == 0
    assert caught.value.reason == "missing_key"
    assert str(caught.value) == "missing_key"


def test_trace_redacts_a_key_that_appears_in_ticket_text(monkeypatch, tmp_path):
    monkeypatch.setenv("XAI_API_KEY", "test-key")
    monkeypatch.setenv("TINYDESK_AI_TRACE", str(tmp_path / "trace.jsonl"))

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "model": "grok-4.7",
                "choices": [{"message": {"content": "{\"summary\":\"ok\"}"}}],
                "usage": {"cost_in_usd_ticks": 0},
            },
        )

    client = XaiModelClient(settings(), transport=httpx.MockTransport(handler))
    client.complete(
        model="grok-4.7",
        messages=[{"role": "user", "content": "the note says test-key"}],
        schema={"type": "object"},
        timeout=30,
    )
    trace = (tmp_path / "trace.jsonl").read_text(encoding="utf-8")
    assert "test-key" not in trace
    assert "the note says" not in trace


def test_trace_never_stores_ticket_text(monkeypatch, tmp_path):
    monkeypatch.setenv("XAI_API_KEY", "test-key")
    monkeypatch.setenv("TINYDESK_AI_TRACE", str(tmp_path / "trace.jsonl"))
    ticket_text = "Mara at Ashmere Press cannot reach the VPN from home since Tuesday."

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": {"message": "busy"}})

    client = XaiModelClient(settings(), transport=httpx.MockTransport(handler))
    with pytest.raises(ModelCallError):
        client.complete(
            model="grok-4.7",
            messages=[
                {"role": "system", "content": "You are TinyDesk's ticket assistant."},
                {"role": "user", "content": ticket_text},
            ],
            schema={"type": "object"},
            timeout=30,
        )
    trace = (tmp_path / "trace.jsonl").read_text(encoding="utf-8")
    assert ticket_text not in trace
    assert "Mara" not in trace
    assert "VPN" not in trace
    saved = json.loads(trace)
    assert [m["role"] for m in saved["messages"]] == ["system", "user"]
    assert saved["messages"][1]["chars"] == len(ticket_text)
    assert saved["messages"][1]["sha256"] == hashlib.sha256(ticket_text.encode("utf-8")).hexdigest()
    assert set(saved["messages"][1]) == {"role", "chars", "sha256"}


def test_configured_effort_and_cap_are_sent(monkeypatch):
    monkeypatch.setenv("XAI_API_KEY", "test-key")
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "model": "grok-4.7",
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": "{\"summary\":\"Paper out.\"}"},
                    }
                ],
            },
        )

    configured = Settings("http://127.0.0.1:11434", "grok-4.7", 30, "xai", "high", 800)
    client = XaiModelClient(configured, transport=httpx.MockTransport(handler))
    assert complete(client) == "{\"summary\":\"Paper out.\"}"
    assert seen["body"]["reasoning_effort"] == "high"
    assert seen["body"]["max_completion_tokens"] == 800
    assert seen["body"]["temperature"] == 0
    assert "max_tokens" not in seen["body"]


def test_length_finish_discards_partial_analysis_and_does_not_retry(monkeypatch, tmp_path):
    monkeypatch.setenv("XAI_API_KEY", "test-key")
    monkeypatch.setenv("TINYDESK_AI_TRACE", str(tmp_path / "trace.jsonl"))
    calls = {"n": 0}
    partial = '{"summary":"The printer is out of paper","suggestedCategory":"Hardware","followUps":[],"draft":"Hello'

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(
            200,
            json={
                "model": "grok-4.7",
                "choices": [
                    {
                        "finish_reason": "length",
                        "message": {"content": partial},
                    }
                ],
                "usage": {"completion_tokens": 1200, "cost_in_usd_ticks": 10000000},
            },
        )

    client = XaiModelClient(settings(), transport=httpx.MockTransport(handler))
    with pytest.raises(ModelCallError) as caught:
        complete(client)
    assert calls["n"] == 1
    assert caught.value.reason == "output_capped"
    assert partial not in str(caught.value)
    saved = json.loads((tmp_path / "trace.jsonl").read_text(encoding="utf-8"))
    assert saved["finish_reason"] == "length"
    assert saved["completion_status"] == "output_capped"
    assert partial not in json.dumps(saved)
    assert saved["request_settings"]["reasoning_effort"] == "low"
    assert saved["request_settings"]["max_completion_tokens"] == 1200


def test_invalid_generation_settings_make_no_request(monkeypatch):
    monkeypatch.setenv("XAI_API_KEY", "test-key")
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json={"choices": []})

    configured = Settings(
        "http://127.0.0.1:11434",
        "grok-4.7",
        30,
        "xai",
        "low",
        1200,
        "bad_reasoning_effort",
    )
    client = XaiModelClient(configured, transport=httpx.MockTransport(handler))
    with pytest.raises(ModelCallError) as caught:
        complete(client)
    assert calls["n"] == 0
    assert caught.value.reason == "bad_reasoning_effort"
