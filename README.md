# TinyDesk

A tiny help desk where the AI only suggests and a human decides.

I'm Cricket ([@Cyb3rCricket](https://x.com/Cyb3rCricket)). I built TinyDesk to practice the part of AI work I care about most: getting useful help from a model without letting it quietly make things up or act on its own.

Ashmere Press, and everyone in the sample queue, is fictional.

## What it does

- Works a daily ticket queue: search, filter, open, edit, add notes and replies, and resolve tickets. A resolution note is required to resolve.
- **Analyze ticket** asks an AI model for four things: a short summary, a suggested category, up to three follow-up questions, and a draft reply.
- You decide what to use. **Apply category** only changes the form. **Use draft** only fills the reply box, and it asks before overwriting text. Nothing is saved until you click save, and no email is ever sent.

Tickets live in your browser's `localStorage`. **Reset demo data** brings back the ten sample tickets.

## Run it

You need Python 3.12+ and [Ollama](https://ollama.com) running locally.

```bash
git clone https://github.com/cyb3rcricket/TinyDesk.git
cd TinyDesk
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
ollama pull qwen3:4b-instruct-2507-q4_K_M
python -m backend
```

Then open http://127.0.0.1:8080.

Want the cloud instead? Put `TINYDESK_AI_PROVIDER=xai` and `XAI_API_KEY=...` in a `.env` file. The panel will then tell you the ticket is being sent to xAI.

| Setting | Default |
| --- | --- |
| `OLLAMA_MODEL` | `qwen3:4b-instruct-2507-q4_K_M` |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` |
| `OLLAMA_TIMEOUT_SECONDS` | `120` |
| `TINYDESK_AI_PROVIDER` | `ollama` (or `xai`) |
| `XAI_MODEL` / `XAI_REASONING_EFFORT` / `XAI_MAX_COMPLETION_TOKENS` | `grok-4.7` / `low` / `1200` |
| `TINYDESK_AI_TRACE` | unset. Set it to a file path to log each xAI call. |

## How it works

1. You click Analyze. The browser sends only the **saved** ticket to a small FastAPI backend.
2. The backend builds a fresh prompt for that one ticket. Nothing carries over between tickets. Ticket text is treated as data, so "ignore your instructions" inside a ticket does nothing.
3. Long histories get shortened in the copy sent to the model, never in your saved ticket.
4. The model must answer in a fixed JSON shape. TinyDesk checks it again, and the category must be one of Access, Network, Hardware, Software, Email, or Other.
5. If anything goes wrong (the model is down, slow, confused, or the input is too big), you get a plain error and a Try again button. There is no fake fallback answer and no silent switch to another model.

The optional trace file records settings, timing, cost, and the outcome of each xAI call. It **never** stores ticket text: each message is saved only as its role, length, and a SHA-256 hash.

### Testing the AI, not just the code

I didn't want to just trust a model, so I tested a few. The write-ups live in [`eval/`](eval/README.md). Short version:

- I compared three small local models (`llama3.2:3b`, `phi4-mini`, `qwen3:4b`) on the same fictional tickets. Qwen was slower, but it was better at reading ticket history and noticing a ticket was already fixed, so it became the default.
- Grok 4.7 at low reasoning effort gave usable drafts on 10 of 12 test tickets. The other 2 needed editing, none were rejected, and the whole run cost about 11 cents.

## The honest catch

- Small models still slip. Qwen sometimes asks a question the ticket already answers, or states a "fact" that isn't there. That's why every suggestion is labeled for review.
- The context-size math is an estimate tuned for the default Qwen setup. A different model or setting can still reject a big ticket. TinyDesk will tell you when that happens.
- It's a demo. There's no sign-in, no attachments, no SLA clock, and no real email.
- With xAI turned on, the ticket's contents leave your computer. Use fictional tickets.

## Tests

```bash
source .venv/bin/activate
python -m pytest
```

That's 67 tests (as of 11 October 2026), all with mocked providers, so they never call Ollama, xAI, or the network.
