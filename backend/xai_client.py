"""xAI chat completions for one ticket analysis.

The API key is read from the environment at call time. It is not stored on
the client, written to logs, or copied into the trace file. The optional
trace file never stores ticket text: each message is recorded as its role,
length, and SHA-256 hash only. Each call is a single HTTP request. httpx is
not given a retry transport.
"""

import hashlib
import json
import os
import time
from pathlib import Path

import httpx

from backend.config import (
    MAX_XAI_COMPLETION_TOKENS,
    XAI_REASONING_EFFORTS,
    Settings,
)
from backend.ollama_client import ModelCallError

XAI_CHAT_URL = "https://api.x.ai/v1/chat/completions"
COST_TICKS_PER_USD = 10_000_000_000
PROMPT_CACHE_KEY = "tinydesk-analyze-ticket"


def cost_usd_from_usage(usage: dict | None) -> float | None:
    """Convert the API's cost_in_usd_ticks field. One USD is 10^10 ticks."""
    if not isinstance(usage, dict):
        return None
    ticks = usage.get("cost_in_usd_ticks")
    if isinstance(ticks, bool) or not isinstance(ticks, (int, float)):
        return None
    return ticks / COST_TICKS_PER_USD


def _redact(text: str) -> str:
    key = os.environ.get("XAI_API_KEY", "").strip()
    if key and key in text:
        text = text.replace(key, "[redacted]")
    return text


def _request_settings(settings: Settings) -> dict:
    return {
        "endpoint": XAI_CHAT_URL,
        "temperature": 0,
        "stream": False,
        "prompt_cache_key": PROMPT_CACHE_KEY,
        "reasoning_effort": settings.reasoning_effort,
        "max_completion_tokens": settings.max_completion_tokens,
        "response_format": "json_schema",
    }


def _generation_error(settings: Settings) -> str | None:
    if settings.config_error:
        return settings.config_error
    if settings.reasoning_effort not in XAI_REASONING_EFFORTS:
        return "bad_reasoning_effort"
    cap = settings.max_completion_tokens
    if isinstance(cap, bool) or not isinstance(cap, int):
        return "bad_output_cap"
    if not 1 <= cap <= MAX_XAI_COMPLETION_TOKENS:
        return "bad_output_cap"
    return None


def _message_digests(messages: list[dict]) -> list[dict]:
    """Describe messages without keeping their text."""
    digests = []
    for message in messages:
        content = message.get("content") if isinstance(message, dict) else None
        text = content if isinstance(content, str) else ""
        digests.append(
            {
                "role": message.get("role") if isinstance(message, dict) else None,
                "chars": len(text),
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            }
        )
    return digests


def _write_trace(record: dict) -> None:
    raw_path = os.environ.get("TINYDESK_AI_TRACE", "").strip()
    if not raw_path:
        return
    path = Path(raw_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        line = _redact(json.dumps(record, ensure_ascii=False))
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except OSError:
        return


class XaiModelClient:
    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None) -> None:
        self.settings = settings
        self._transport = transport

    def _trace(self, model: str, messages: list[dict], *, error: str | None, **extra) -> None:
        record = {
            "provider": "xai",
            "requested_model": model,
            "messages": _message_digests(messages),
            "request_settings": _request_settings(self.settings),
            **extra,
            "completion_status": error or "complete",
        }
        if error:
            record["error"] = error
        _write_trace(record)

    def complete(self, *, model: str, messages: list[dict], schema: dict, timeout: float) -> str:
        generation_error = _generation_error(self.settings)
        if generation_error:
            self._trace(model, messages, error=generation_error)
            raise ModelCallError(generation_error, "BadConfig")

        key = os.environ.get("XAI_API_KEY", "").strip()
        if not key:
            self._trace(model, messages, error="missing_key")
            raise ModelCallError("missing_key", "MissingKey")

        outbound_schema = dict(schema)
        outbound_schema.setdefault("additionalProperties", False)
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0,
            "stream": False,
            "prompt_cache_key": PROMPT_CACHE_KEY,
            "reasoning_effort": self.settings.reasoning_effort,
            "max_completion_tokens": self.settings.max_completion_tokens,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "ticket_analysis",
                    "strict": True,
                    "schema": outbound_schema,
                },
            },
        }
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        timeout_config = httpx.Timeout(connect=5.0, read=timeout, write=30.0, pool=5.0)
        started = time.perf_counter()
        try:
            with httpx.Client(timeout=timeout_config, transport=self._transport) as client:
                response = client.post(XAI_CHAT_URL, headers=headers, json=payload)
        except httpx.TimeoutException as exc:
            self._trace(model, messages, error="timeout")
            raise ModelCallError("timeout", type(exc).__name__) from None
        except httpx.HTTPError as exc:
            self._trace(model, messages, error="unavailable")
            raise ModelCallError("unavailable", type(exc).__name__) from None

        body: dict = {}
        try:
            parsed = response.json()
            if isinstance(parsed, dict):
                body = parsed
        except json.JSONDecodeError:
            body = {}

        usage = body.get("usage") if isinstance(body.get("usage"), dict) else None
        choices = body.get("choices")
        choice = choices[0] if isinstance(choices, list) and choices and isinstance(choices[0], dict) else None
        finish_reason = choice.get("finish_reason") if isinstance(choice, dict) else None
        capped = finish_reason == "length"
        content = None
        reason = None
        error_type = None
        if response.status_code == 401:
            reason, error_type = "auth", "HTTPStatusError"
        elif response.status_code == 404:
            reason, error_type = "model_missing", "HTTPStatusError"
        elif response.status_code >= 400:
            detail = json.dumps(body) if body else ""
            if "context" in detail.lower() and "token" in detail.lower():
                reason = "context_limit"
            else:
                reason = "bad_response"
            error_type = "HTTPStatusError"
        elif capped:
            # Discard the body. A length stop can still contain a partial JSON object.
            reason, error_type = "output_capped", "LengthFinish"
        elif not isinstance(choice, dict):
            reason, error_type = "invalid_output", "EmptyChoices"
        else:
            message = choice.get("message")
            raw_content = message.get("content") if isinstance(message, dict) else None
            if not isinstance(raw_content, str) or not raw_content.strip():
                reason, error_type = "invalid_output", "EmptyContent"
            else:
                content = raw_content
        self._trace(
            model,
            messages,
            error=reason,
            returned_model=body.get("model"),
            status_code=response.status_code,
            duration_ms=int((time.perf_counter() - started) * 1000),
            finish_reason=finish_reason,
            usage=usage,
            cost_usd=cost_usd_from_usage(usage),
        )
        if reason:
            raise ModelCallError(reason, error_type, response.status_code)
        return content
