# Evals

These are the records of how I checked the assistant's output. All tickets are fictional. Each folder has the inputs, the raw outputs, and (where written) a `REPORT.md` explaining what passed and what didn't. "Valid JSON" is never counted as "good answer". Drafts were reviewed by hand.

| Folder | What it checked |
| --- | --- |
| `model-comparison/` | `llama3.2:3b`, `phi4-mini`, and `qwen3:4b` on the same ten tickets. Covers speed and answer quality. |
| `followup-five/` | Llama and Qwen on five new tickets built to catch redundant follow-up questions. |
| `qwen-quality-eight/` | Eight harder tickets through the real app route with the Qwen default. |
| `ambiguity-instruction-check/` | A prompt fix for "which resource?" questions, re-run on the eight tickets plus four fresh ones. |
| `xai-grok-4.7-once/`, `xai-grok-4.7-low-once/` | The same twelve tickets on Grok 4.7 at high and then low reasoning effort. Low gave 10 usable drafts and 2 needing edits, at about half the cost and time. See `review-findings.json`. |

The `run_*.py` scripts reproduce the local runs. They need Ollama running and are not part of the test suite.

## What the files are

The raw files are kept on purpose, so anyone can check a report against what the model actually said. You don't need to read them to follow the reports.

| File | What's in it |
| --- | --- |
| `REPORT.md` | The plain-language write-up. Start here. |
| `fixtures.json`, `inputs.json`, `fresh-fixtures.json` | The fictional tickets that were sent. |
| `expectations.json`, `fresh-expectations.json` | What a good answer should and shouldn't say. These were written before the run. |
| `pre-run-hashes.txt`, `manifest.json` | Hashes showing the inputs and expectations weren't edited after the run. |
| `<model>.json`, `raw-results.json` | The model's raw answers, exactly as returned. |
| `automated-checks.json`, `review-findings.json` | Pass/fail on the simple text checks, plus my hand review of each draft. |
| `run-meta.json`, `timings.json`, `budget-check.json` | Settings, timings, and the context-size estimate for that run. |
| `prompt.diff`, `prompt-after.txt` | The prompt change tested in `ambiguity-instruction-check/`. |
| `smoke-request.json`, `smoke-response.json` | A single first call to check that the xAI setup worked. |
| `submitted-messages.json`, `trace.jsonl` | The exact messages sent to xAI and the per-call trace. These runs happened before the trace switched to hash-and-length only, so they include the full prompt text. That's fine here because every ticket is fictional. |
| `old-prompt-outputs.json`, `new-prompt-outputs.json` (top level) | Before and after outputs from an early prompt revision, made with `run_cases.py` and the tickets in `cases.py`. |

Older run logs (dated live checks and history-limit checks) used to live in the main README. They're still in git history from before PR #8.
