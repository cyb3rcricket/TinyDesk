"""Local Ollama chat.

TinyDesk sends each ticket to the configured local model through Ollama's
Python client. The default model is qwen3:4b-instruct-2507-q4_K_M. Set
OLLAMA_MODEL to use another installed model. Structured output uses the JSON
schema documented for `/api/chat` `format`. Each call is a new request with
no shared memory or conversation history.
"""

import json

import httpx
from ollama import Client, ResponseError

from backend.config import Settings

# Room reserved for the reply inside the runtime context window.
# num_ctx is left unset: Ollama then uses its 4096-token default.
# The model card's 262144 context length is not the window this server uses.
RESPONSE_TOKEN_RESERVE = 1200
CHAT_OPTIONS = {"temperature": 0, "num_predict": RESPONSE_TOKEN_RESERVE}


class ModelCallError(Exception):
    def __init__(self, reason: str, error_type: str, status_code: int | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.error_type = error_type
        self.status_code = status_code


def _is_context_limit(exc: ResponseError) -> bool:
    """True only for Ollama's confirmed context-window rejection.

    The HTTP body is {"error": "<json>"} and the client keeps that inner
    string. A direct JSON object with type exceed_context_size_error is
    accepted as well. Other 400 responses stay generic model errors.
    """
    detail = exc.error
    if not isinstance(detail, str):
        detail = json.dumps(detail)
    return (
        "exceed_context_size_error" in detail
        or "exceeds the available context size" in detail
    )


def build_client(settings: Settings, timeout: float) -> Client:
    return Client(
        host=settings.base_url,
        timeout=httpx.Timeout(connect=5.0, read=timeout, write=30.0, pool=5.0),
    )


class OllamaModelClient:
    def __init__(self, settings: Settings, client_factory=build_client) -> None:
        self.settings = settings
        self._client_factory = client_factory

    def complete(self, *, model: str, messages: list[dict], schema: dict, timeout: float) -> str:
        client = self._client_factory(self.settings, timeout)
        try:
            response = self._chat(client, model, messages, schema)
        finally:
            close = getattr(client, "close", None)
            if callable(close):
                close()

        content = getattr(getattr(response, "message", None), "content", None)
        if not isinstance(content, str) or not content.strip():
            raise ModelCallError("invalid_output", "EmptyContent")
        return content

    def _chat(self, client: Client, model: str, messages: list[dict], schema: dict):
        try:
            return client.chat(
                model=model,
                messages=messages,
                format=schema,
                stream=False,
                options=CHAT_OPTIONS,
            )
        except httpx.ConnectTimeout as exc:
            raise ModelCallError("unavailable", type(exc).__name__) from None
        except httpx.TimeoutException as exc:
            raise ModelCallError("timeout", type(exc).__name__) from None
        except ResponseError as exc:
            if exc.status_code == 404:
                reason = "model_missing"
            elif _is_context_limit(exc):
                reason = "context_limit"
            else:
                reason = "bad_response"
            raise ModelCallError(reason, type(exc).__name__, exc.status_code) from None
        except ConnectionError as exc:
            raise ModelCallError("unavailable", type(exc).__name__) from None
        except httpx.HTTPError as exc:
            raise ModelCallError("unavailable", type(exc).__name__) from None
