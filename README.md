# TinyDesk

TinyDesk is a small help desk for working a daily ticket queue. Tickets, edits, and activity stay in this browser. Analyze ticket asks a local Ollama model for a suggestion. The suggestion is labeled for review. TinyDesk does not change the ticket or send a reply unless you save that yourself.

Ashmere Press, and everyone in the sample queue, is fictional.

## Setup

TinyDesk needs Python 3.12 and a local Ollama server. On this Mac, `python3` is older than 3.12, so the virtualenv command uses `python3.12`.

Ollama must already be running. The default model is `qwen3:4b-instruct-2507-q4_K_M`. On a small set of fictional tickets it handled activity history and verified resolutions better than `llama3.2:3b`. It also takes longer, and it can still ask a redundant question or state a fact that is not in the ticket. Review every suggestion before you apply it. TinyDesk does not fall back to another model if Qwen fails.

`llama3.2:3b` and `phi4-mini:latest` can stay installed. To use Llama for one server session:

```bash
OLLAMA_MODEL=llama3.2:3b python -m backend
```

```bash
git clone https://github.com/cyb3rcricket/TinyDesk.git
cd TinyDesk
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
ollama pull qwen3:4b-instruct-2507-q4_K_M
```

## Run

```bash
source .venv/bin/activate
python -m backend
```

Open http://127.0.0.1:8080

That command binds to `127.0.0.1` port `8080`. It serves the help desk pages and `POST /api/analyze-ticket`. It does not serve Python files, tests, or environment files.

Stop anything else already listening on port 8080 first. `python3 -m http.server` only serves the static files, so Analyze ticket cannot reach the model through that process.

To use another port:

```bash
uvicorn backend.app:app --host 127.0.0.1 --port 8081
```

## Configuration

Set these in the environment before starting the server. Each request reads them. There is no shared conversation.

| Variable | Default | Meaning |
| --- | --- | --- |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama server. A trailing slash is removed. |
| `OLLAMA_MODEL` | `qwen3:4b-instruct-2507-q4_K_M` | Model name passed to Ollama. |
| `OLLAMA_TIMEOUT_SECONDS` | `120` | How long to wait for the model to finish. Values outside `0` to `600`, or values that are not numbers, use `120`. |
| `TINYDESK_AI_PROVIDER` | `ollama` | `ollama` or `xai`. A blank value uses Ollama. |
| `XAI_MODEL` | `grok-4.7` | Model name used only when the provider is `xai`. |
| `XAI_API_KEY` | none | xAI credential. Read from the environment or from `.env`. |
| `XAI_REASONING_EFFORT` | `low` | Used only when the provider is `xai`. Accepted values are `low`, `medium`, `high`, and `xhigh`. An unknown value is rejected and no request is sent. |
| `XAI_MAX_COMPLETION_TOKENS` | `1200` | Visible output cap, used only when the provider is `xai`. A whole number from 1 to 128000. An invalid value is rejected and no request is sent. |

Example:

```bash
export OLLAMA_BASE_URL=http://127.0.0.1:11434
export OLLAMA_MODEL=qwen3:4b-instruct-2507-q4_K_M
export OLLAMA_TIMEOUT_SECONDS=120
python -m backend
```

Leave `OLLAMA_MODEL` unset to use the Qwen default. A set value replaces that default for the server process. There is no second model behind Ollama.

`python -m backend` and the app both read a git-ignored `.env` in the project root. Values already set in the environment stay as they are. The HTTP server does not serve that file. With no `TINYDESK_AI_PROVIDER`, analysis uses Ollama. Set `TINYDESK_AI_PROVIDER=xai` and `XAI_API_KEY` to send the same ticket analysis to xAI. The xAI call is one request to `POST https://api.x.ai/v1/chat/completions`, with no automatic retry. Temperature stays `0`.

That request sends `reasoning_effort` and `max_completion_tokens`. `reasoning_effort` defaults to `low` here; `high` remains selectable. If the field is omitted, the API's own default is `high`, so TinyDesk always sends the configured value. `max_completion_tokens` defaults to `1200`. On this endpoint that cap applies to visible output tokens only. It does not include reasoning tokens or function-call tokens. Reasoning tokens are billed separately and are not cut by this cap. `1200` is the room kept for the complete JSON analysis (`summary`, `suggestedCategory`, `followUps`, and `draft`). The deprecated `max_tokens` field is not sent. A response with `finish_reason` `length` is an error. TinyDesk does not show that partial text and does not send the request again.

TinyDesk calls Ollama's Python client at `http://127.0.0.1:11434` and sends a JSON schema in the `/api/chat` `format` field, which is Ollama's documented structured-output mechanism (https://docs.ollama.com/capabilities/structured-outputs). Temperature is `0`. TinyTalk's `SOUL.md`, MemPalace memories, conversation history, and knowledge graph are not loaded. TinyTalk itself is not modified.

## Request flow

1. You open a saved ticket and click Analyze ticket. The button stays disabled until that request finishes.
2. The browser sends the saved subject, description, requester, department, category, priority, status, resolution note, and activity to `POST /api/analyze-ticket`. Unsaved composer text and unsaved field edits are not sent.
3. FastAPI checks the body. A missing or invalid field returns `available: false` and a message that names the field, not the ticket text.
4. The server builds one new system message and one new user message. It does not keep those messages for the next ticket.
5. The user message includes the current fields and recent activity. TinyDesk builds that text as a copy, and the saved ticket stays complete. The copy is an estimate sized for the default Qwen context window, including the system instructions and room for the reply. Older activity entries are counted, not copied. Text that does not fit keeps its beginning and ends with `[shortened]`. `omittedEarlierActivityCount` is the number of older entries left out. A saved resolution stays in `currentFields`. Ticket text is sent as data, with instructions to ignore any commands inside it.
6. Ollama returns JSON constrained by the schema. TinyDesk checks that JSON again. `suggestedCategory` must be Access, Network, Hardware, Software, Email, or Other.
7. A usable result is `available: true` with `summary`, `suggestedCategory`, `followUps`, and `draft`. The panel calls it a local AI suggestion that still needs review.
8. If Ollama is down, the model is missing, the request takes too long, the input exceeds the context window, or the JSON is not usable, the panel shows `message` and Try again. TinyDesk does not substitute a sample suggestion or another model.
9. Apply category only changes the category menu. Use draft only fills the reply composer, and asks before replacing text that is already there. Save changes and Save reply are separate.

Saved tickets remain in `localStorage` under `tinydesk.tickets.v1`.

## What works

- Search the queue by ticket number or subject.
- Filter by status and category, and clear those filters.
- Open a ticket, then return to the queue.
- Create a ticket. The number, opened time, and updated time are generated. New tickets start as New with Medium priority. Analyze ticket works on those tickets as well as the sample tickets.
- Change category, priority, and status, then save. A resolution note is required before a ticket can be Resolved. Status changes are written into the activity history.
- Add an internal note or a reply to the requester.
- Ask TinyTalk Assist to analyze the saved ticket, apply the suggested category to the form, or place the draft in the reply composer. If the composer already has text, TinyDesk asks before replacing it. You can edit the draft before saving.
- Keep the queue after a refresh. The first visit with no saved data loads ten sample tickets. After that, the saved set is used.
- Reset demo data, after a confirmation, back to those sample tickets.

Statuses are New, In Progress, Waiting on User, and Resolved. Priorities are Low, Medium, and High. Categories are Access, Network, Hardware, Software, Email, and Other. The same lists live in `js/store.js` and `backend/schemas.py`.

On a wide window the queue is a table and the assistant sits beside the ticket. On a narrow window the queue becomes a list and the assistant moves below the ticket.

## Limits

- This phase analyzes and drafts only. It does not change tickets, call tools, or send messages.
- Replies are stored on the ticket. TinyDesk does not send email.
- There is no sign-in, no attachments, and no SLA clock.
- There is no retrieval index, long-term memory, database, or extra workflow service. Ollama is the default model provider. xAI is used only when `TINYDESK_AI_PROVIDER=xai`.
- Each analysis is independent. Switching tickets clears the panel. A response that arrives after you leave, or after a newer request, is not shown. The browser cancel does not stop an Ollama call that has already started.
- Saved tickets stay complete in the browser. Analyze builds a separate copy for the model, and only that copy is shortened. A shortened field keeps its beginning and ends with `[shortened]`. `omittedEarlierActivityCount` counts older activity left out of the copy. The copy keeps the current ticket fields and the resolution note ahead of older activity.
- The size of that copy is a token estimate calibrated for the default model, `qwen3:4b-instruct-2507-q4_K_M`, at a 4096-token runtime context when `num_ctx` is unset. The estimate leaves 1200 tokens for the reply. It does not guarantee that every input fits. Another model, or a different Ollama context setting, can still reject the request. TinyDesk then says the input exceeds the context window and does not switch models.
- The request may still include up to 5000 activity entries and up to 200,000 characters in one activity body or resolution note. Subject is limited to 200 characters and description to 5000. A body over 200,000 bytes is rejected.
- At most six follow-up questions are shown.
- The default Qwen model can still ask a question the ticket already answers, or state a fact that is not in the ticket. That is why the panel says the suggestion needs review. Invalid JSON is shown as a failure. TinyDesk does not substitute another model or a sample answer.
- User-entered text is rendered as text.

## Tests

Automated tests mock Ollama. They do not call the local model.

```bash
source .venv/bin/activate
python -m pytest
```

On 1 October 2026 that command passed 32 tests. They cover request validation, the allowed categories, a valid model result, invalid JSON and a disallowed category, connection failures, timeouts, a missing model, unexpected errors, and logs that record the ticket id and reason without the ticket text. They also check that backend files such as `requirements.txt` and `backend/app.py` are not served.

On 2 October 2026 the same command passed 44 tests. The 12 added tests are mocked. They cover more than 30 activity entries, an activity note longer than 4000 characters, a 4000-character resolution whose `Resolution: ` activity line is longer than the model copy, a saved ticket that stays unchanged while the copy is built, a combined input estimate inside the default Qwen budget, and a confirmed context-limit error. They do not call Ollama, and they do not prove that every ticket fits the context window.

## Live model check

These checks used `llama3.2:3b`, which was the default at the time. The default is now `qwen3:4b-instruct-2507-q4_K_M`. They are separate from the mocked tests. Port 8080 was already taken by `python3 -m http.server`, so the browser used http://127.0.0.1:8081. The unavailable check used a second server on port 8082 with `OLLAMA_BASE_URL=http://127.0.0.1:9`.

- Seeded VPN ticket TD-2401 returned a Network suggestion, a summary about the home VPN, a follow-up for the error text, and a draft addressed to Mara. The panel labeled it a local AI suggestion. Apply category changed the form and said to save it. The saved category, activity, and updated time did not change. Use draft filled the composer, switched it to a reply, and said no email was sent. Using draft again opened the replacement confirmation. Cancel left the text. The draft could be edited, and that edit was not written into activity.
- Newly created ticket TD-2411, "Second monitor stays black," returned a Hardware suggestion and a draft for Lena. It was not the old placeholder. The activity stayed the single "Ticket created" entry, and the composer stayed empty.
- Vague seeded ticket TD-2402, "Can't get in. Please reset," suggested Access and listed follow-up questions. The form stayed Other until someone applies the suggestion. Nothing was saved.
- With Ollama unreachable, the panel said TinyDesk could not reach the local model and offered Try again. Retry showed the same error. No sample suggestion appeared.
- Analysis was started on TD-2402 and the view was switched to TD-2406 while the button still said Analyzing. Eight seconds later TD-2406 had an empty assistant panel and an enabled Analyze button. Returning to TD-2402 also showed an empty panel, so the late result did not appear.

The `llama3.2:3b` replies were usable JSON, and they did not claim the VPN or password issue was fixed. They were not perfect. On the VPN ticket the model also asked whether the profile had been updated, although an internal note already said the client was installed. On the password ticket one follow-up asked about a "password reset status" the ticket never mentioned. Those are reasons to review the draft before saving it.

## History-limit check

These checks are separate from the mocked tests and from the `llama3.2:3b` checks above. On 2 October 2026 they used the default `qwen3:4b-instruct-2507-q4_K_M` with `OLLAMA_MODEL` unset. `ollama ps` showed that model alone at a 4096-token context. The comparisons under `eval/` were not rerun.

- A normal VPN-shaped ticket returned a Network suggestion. Its measured prompt was 1178 tokens.
- A ticket with 40 ordinary English notes returned a Network suggestion. Its measured prompt was 2016 tokens.
- A resolved ticket with a 4000-character repeated-character resolution, that same text copied into the status activity line, and a 2000-character repeated description returned a suggestion. Its measured prompt was 2597 tokens. Before this bound, that shape was 5551 prompt tokens, and Ollama rejected it with `exceed_context_size_error`.
- In the browser, seeded ticket TD-2401 showed a local AI suggestion. Saved activity stayed at 4 entries, and the stored category stayed Network. At a 390 by 844 window the Analyze button was visible and the assistant sat below the ticket. A stored ticket with 32 activity entries and a 4000-character resolution note also showed a suggestion. After analysis it still had 32 entries and the full resolution note.

The repeated-character ticket was categorized Network, and the summary described the note as truncated. That suggestion still needs review. The token estimate for these three prompts was under the 2896-token budget and above the measured prompt size. Other tickets, models, or context settings can still exceed the window.
