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
