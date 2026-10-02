"""Record model output for the evaluation tickets.

Uses the app's Ollama client, model, schema, and generation options.
It does not score the replies.
"""

import json
import sys
import time
from pathlib import Path

from backend.analysis import system_prompt, user_message
from backend.config import load_settings
from backend.ollama_client import CHAT_OPTIONS, OllamaModelClient
from backend.schemas import ANALYSIS_SCHEMA, TicketRequest
from eval.cases import EVAL_CASES


def main() -> None:
    destination = Path(sys.argv[1] if len(sys.argv) > 1 else "eval/outputs.json")
    settings = load_settings()
    client = OllamaModelClient(settings)
    runs = []
    for case in EVAL_CASES:
        ticket = TicketRequest.model_validate(case["ticket"])
        messages = [
            {"role": "system", "content": system_prompt()},
            {"role": "user", "content": user_message(ticket)},
        ]
        for repeat in range(1, int(case["repeats"]) + 1):
            started = time.perf_counter()
            raw = client.complete(
                model=settings.model,
                messages=messages,
                schema=ANALYSIS_SCHEMA,
                timeout=settings.timeout_seconds,
            )
            elapsed = round(time.perf_counter() - started, 1)
            runs.append(
                {
                    "name": case["name"],
                    "repeat": repeat,
                    "elapsed_s": elapsed,
                    "output": raw,
                }
            )
            print(f"{case['name']} #{repeat} {elapsed}s", flush=True)
    destination.write_text(
        json.dumps(
            {
                "model": settings.model,
                "options": CHAT_OPTIONS,
                "system_prompt": system_prompt(),
                "runs": runs,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote {destination}")


if __name__ == "__main__":
    main()
