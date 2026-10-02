"""Run the five follow-up tickets through the existing comparison runner.

Reads eval/followup-five/fixtures.json and does not rewrite it.
"""

import json
from pathlib import Path

from backend.analysis import system_prompt, user_message
from backend.config import load_settings
from backend.ollama_client import CHAT_OPTIONS
from backend.schemas import ANALYSIS_SCHEMA, TicketRequest
from eval.run_model_comparison import KEEP_ALIVE, run_model, sha256_text

FIXTURE_PATH = Path("eval/followup-five/fixtures.json")
OUTPUT_DIR = Path("eval/followup-five")
MODELS = [
    "llama3.2:3b",
    "qwen3:4b-instruct-2507-q4_K_M",
]


def combined_text(content: dict) -> str:
    followups = content.get("followUps") or []
    parts = [content.get("summary") or "", content.get("draft") or "", "\n".join(followups)]
    return "\n".join(parts).casefold()


def apply_checks(expectations: dict, content: dict) -> list[dict]:
    checks = expectations["automated_checks"]
    text = combined_text(content)
    followups = "\n".join(content.get("followUps") or []).casefold()
    draft = (content.get("draft") or "").casefold()
    results = []

    for needle in checks.get("text_must_include_all", []):
        results.append({
            "check": f"includes {needle}",
            "passed": needle.casefold() in text,
        })
    for needle in checks.get("text_must_not_include_any", []):
        results.append({
            "check": f"excludes {needle}",
            "passed": needle.casefold() not in text,
        })
    for needle in checks.get("followups_must_not_include_any", []):
        results.append({
            "check": f"follow-ups exclude {needle}",
            "passed": needle.casefold() not in followups,
        })
    any_of = checks.get("draft_must_include_any", [])
    if any_of:
        results.append({
            "check": "draft includes one of " + ", ".join(any_of),
            "passed": any(needle.casefold() in draft for needle in any_of),
        })
    if checks.get("closure_followups_must_be_empty"):
        results.append({
            "check": "follow-ups empty for closure",
            "passed": content.get("followUps") == [],
        })
    return results


def main() -> None:
    fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    tickets = [item["ticket"] for item in fixtures["tickets"]]
    settings = load_settings()
    prompt = system_prompt()
    inputs = []
    for raw_ticket in tickets:
        ticket = TicketRequest.model_validate(raw_ticket)
        message = user_message(ticket)
        inputs.append({
            "ticket_id": ticket.id,
            "user_message": message,
            "user_message_sha256": sha256_text(message),
        })
    manifest = {
        "default_model_unchanged": settings.model,
        "models": MODELS,
        "options": CHAT_OPTIONS,
        "timeout_seconds": settings.timeout_seconds,
        "keep_alive": KEEP_ALIVE,
        "think": None,
        "stream": False,
        "schema": ANALYSIS_SCHEMA,
        "schema_sha256": sha256_text(json.dumps(ANALYSIS_SCHEMA, sort_keys=True)),
        "system_prompt": prompt,
        "system_prompt_sha256": sha256_text(prompt),
        "ollama_base_url": settings.base_url,
        "fixtures_sha256": sha256_text(FIXTURE_PATH.read_text(encoding="utf-8")),
    }
    (OUTPUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (OUTPUT_DIR / "inputs.json").write_text(
        json.dumps(inputs, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    saved = []
    for model in MODELS:
        record = run_model(model, settings, tickets=tickets, repeats={})
        safe_name = model.replace(":", "_").replace("/", "_")
        path = OUTPUT_DIR / f"{safe_name}.json"
        path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        saved.append(record)
        print(f"wrote {path}", flush=True)

    expectations = {item["id"]: item for item in fixtures["tickets"]}
    automated = []
    for record in saved:
        for run in record["runs"]:
            entry = {
                "model": record["model"],
                "ticket_id": run["ticket_id"],
                "ok": run.get("ok"),
                "schema_valid": run.get("schema_valid"),
                "error_type": run.get("error_type"),
                "checks": [],
            }
            if run.get("ok") and run.get("schema_valid") and isinstance(run.get("content"), str):
                content = json.loads(run["content"])
                entry["checks"] = apply_checks(expectations[run["ticket_id"]], content)
                entry["checks_passed"] = all(item["passed"] for item in entry["checks"])
            else:
                entry["checks_passed"] = False
            automated.append(entry)
    (OUTPUT_DIR / "automated-checks.json").write_text(
        json.dumps(automated, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print("FOLLOWUP COMPLETE", flush=True)


if __name__ == "__main__":
    main()
