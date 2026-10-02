"""Record the current TinyDesk prompt across installed local models.

Does not change the default model or the production prompt.
Models are stopped first and run one at a time. The warm-up call is timed
separately from the ticket calls.
"""

import hashlib
import json
import subprocess
import time
from pathlib import Path

from ollama import Client
from pydantic import ValidationError

from backend.analysis import system_prompt, user_message
from backend.config import load_settings
from backend.ollama_client import CHAT_OPTIONS, ModelCallError
from backend.ollama_client import build_client
from backend.schemas import ANALYSIS_SCHEMA, ModelAnalysis, TicketRequest
from eval.model_comparison_cases import REPEATS, SEEDED_TICKETS

MODELS = [
    "llama3.2:3b",
    "phi4-mini:latest",
    "qwen3:4b-instruct-2507-q4_K_M",
]
# Comparison-only. Production leaves keep_alive at the client default so a
# model can unload. This holds one model in memory for the timing runs.
KEEP_ALIVE = "30m"
OUTPUT_DIR = Path("eval/model-comparison")
TIMING_KEYS = (
    "total_duration",
    "load_duration",
    "prompt_eval_count",
    "prompt_eval_duration",
    "eval_count",
    "eval_duration",
)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def stop_models() -> None:
    for name in MODELS:
        subprocess.run(["ollama", "stop", name], check=False, capture_output=True, text=True)


def loaded_models() -> str:
    result = subprocess.run(["ollama", "ps"], check=False, capture_output=True, text=True)
    return (result.stdout or "") + (result.stderr or "")


def ns_to_ms(value):
    if value is None:
        return None
    return round(int(value) / 1_000_000, 1)


def response_record(response) -> dict:
    dumped = response.model_dump() if hasattr(response, "model_dump") else {}
    content = getattr(getattr(response, "message", None), "content", None)
    timings = {}
    for key in TIMING_KEYS:
        raw = dumped.get(key)
        timings[key] = raw
        if key.endswith("duration"):
            timings[f"{key}_ms"] = ns_to_ms(raw)
    schema_error = None
    schema_valid = False
    if isinstance(content, str) and content.strip():
        try:
            ModelAnalysis.model_validate_json(content)
            schema_valid = True
        except ValidationError as exc:
            schema_error = exc.error_count()
    return {
        "content": content,
        "schema_valid": schema_valid,
        "schema_error_count": schema_error,
        "done": dumped.get("done"),
        "done_reason": dumped.get("done_reason"),
        "timings": timings,
    }


def chat(client: Client, model: str, messages: list[dict]):
    return client.chat(
        model=model,
        messages=messages,
        format=ANALYSIS_SCHEMA,
        stream=False,
        options=CHAT_OPTIONS,
        keep_alive=KEEP_ALIVE,
    )


def warmup_messages() -> list[dict]:
    return [
        {"role": "system", "content": system_prompt()},
        {
            "role": "user",
            "content": (
                "Warm-up only. Return JSON matching the schema. "
                'summary: ready. suggestedCategory: Other. followUps: []. draft: ready.'
            ),
        },
    ]


def run_model(model: str, settings, tickets=None, repeats=None) -> dict:
    print(f"\n== {model}", flush=True)
    stop_models()
    before = loaded_models()
    client = build_client(settings, settings.timeout_seconds)
    record = {
        "model": model,
        "loaded_before": before,
        "warmup": None,
        "loaded_after_warmup": None,
        "runs": [],
    }
    try:
        started = time.perf_counter()
        try:
            response = chat(client, model, warmup_messages())
            record["warmup"] = {
                "ok": True,
                "wall_s": round(time.perf_counter() - started, 3),
                **response_record(response),
            }
        except Exception as exc:
            record["warmup"] = {
                "ok": False,
                "wall_s": round(time.perf_counter() - started, 3),
                "error_type": type(exc).__name__,
                "error": str(exc)[:500],
            }
        record["loaded_after_warmup"] = loaded_models()
        print(f"warmup {record['warmup'].get('wall_s')}s ok={record['warmup'].get('ok')}", flush=True)

        ticket_rows = SEEDED_TICKETS if tickets is None else tickets
        repeat_for = REPEATS if repeats is None else repeats
        for raw_ticket in ticket_rows:
            ticket = TicketRequest.model_validate(raw_ticket)
            messages = [
                {"role": "system", "content": system_prompt()},
                {"role": "user", "content": user_message(ticket)},
            ]
            repeats = repeat_for.get(ticket.id, 1)
            for repeat in range(1, repeats + 1):
                started = time.perf_counter()
                item = {
                    "ticket_id": ticket.id,
                    "repeat": repeat,
                    "user_message_sha256": sha256_text(messages[1]["content"]),
                }
                try:
                    response = chat(client, model, messages)
                    item["ok"] = True
                    item["wall_s"] = round(time.perf_counter() - started, 3)
                    item.update(response_record(response))
                except ModelCallError as exc:
                    item["ok"] = False
                    item["wall_s"] = round(time.perf_counter() - started, 3)
                    item["error_type"] = exc.error_type
                    item["reason"] = exc.reason
                    item["status_code"] = exc.status_code
                except Exception as exc:
                    item["ok"] = False
                    item["wall_s"] = round(time.perf_counter() - started, 3)
                    item["error_type"] = type(exc).__name__
                    item["error"] = str(exc)[:500]
                record["runs"].append(item)
                print(
                    f"{ticket.id} #{repeat} {item['wall_s']}s ok={item['ok']} valid={item.get('schema_valid')}",
                    flush=True,
                )
    finally:
        close = getattr(client, "close", None)
        if callable(close):
            close()
        stop_models()
        record["loaded_after_stop"] = loaded_models()
    return record


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    settings = load_settings()
    prompt = system_prompt()
    inputs = []
    for raw_ticket in SEEDED_TICKETS:
        ticket = TicketRequest.model_validate(raw_ticket)
        message = user_message(ticket)
        inputs.append(
            {
                "ticket_id": ticket.id,
                "repeats": REPEATS.get(ticket.id, 1),
                "ticket": raw_ticket,
                "user_message": message,
                "user_message_sha256": sha256_text(message),
            }
        )
    manifest = {
        "default_model_unchanged": settings.model,
        "models": MODELS,
        "options": CHAT_OPTIONS,
        "timeout_seconds": settings.timeout_seconds,
        "keep_alive": KEEP_ALIVE,
        "keep_alive_note": (
            "Production chat calls do not set keep_alive. "
            "This comparison sets 30m so later tickets are not timed while the model reloads."
        ),
        "think": None,
        "stream": False,
        "schema": ANALYSIS_SCHEMA,
        "schema_sha256": sha256_text(json.dumps(ANALYSIS_SCHEMA, sort_keys=True)),
        "system_prompt": prompt,
        "system_prompt_sha256": sha256_text(prompt),
        "ollama_base_url": settings.base_url,
    }
    (OUTPUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (OUTPUT_DIR / "inputs.json").write_text(
        json.dumps(inputs, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    for model in MODELS:
        record = run_model(model, settings)
        safe_name = model.replace(":", "_").replace("/", "_")
        path = OUTPUT_DIR / f"{safe_name}.json"
        path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {path}", flush=True)
    print("COMPARISON COMPLETE", flush=True)


if __name__ == "__main__":
    main()
