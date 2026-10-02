# TinyDesk local model comparison

Compared on 1 October 2026 with Ollama already running. No models were downloaded. TinyDesk’s default model stayed `llama3.2:3b`. The production prompt was not edited for this run.

Previous files in `eval/` were left in place. This folder is a separate record.

## Setup

Every ticket call used the current `system_prompt()` and `user_message()` from `backend/analysis.py`, and `ANALYSIS_SCHEMA` from `backend/schemas.py`.

| Item | Value |
| --- | --- |
| System prompt SHA-256 | `57bb8b860747c14429cad61e0da682ebc8f8fff3fb7f96d6af8159a8800e1f93` |
| Schema SHA-256 | `4061a0ea2aed8746d55e372ebe1cd51523235fe568fcf3a82cfd7fa326fc0456` |
| Generation options | `temperature` 0, `num_predict` 1200 |
| `think` | unset |
| `stream` | false |
| Read timeout | 120 seconds |
| `keep_alive` | `30m` for this comparison only |

Production chat calls do not set `keep_alive`. The comparison set it to 30 minutes so a model would stay loaded between tickets. That is a residency setting, not a sampling setting.

Models ran one at a time, in this order: `llama3.2:3b`, `phi4-mini:latest`, `qwen3:4b-instruct-2507-q4_K_M`. Each was stopped before the next load. `ollama ps` was empty before each warm-up and empty after each model was stopped.

The warm-up was one short structured request using the same system prompt, schema, and generation options. Ticket timings below are the later calls. Ollama’s `load_duration` on those later calls stayed under 16 ms, so those wall times are generation time rather than another model load.

`ollama ps` showed each model at 100% GPU and a 4096 context. This run did not set `num_ctx`.

Inputs, the full prompt, raw responses, errors, and timings are in `manifest.json`, `inputs.json`, and one JSON file per model.

Ten seeded tickets were sent with their full activity and resolution note. TD-2406 and TD-2408 were repeated three times. That is 14 ticket calls per model, 42 in total.

## Objective results

No request failed. All 42 ticket responses parsed and passed `ModelAnalysis` validation. Every `done_reason` was `stop`, so none hit the 1200-token cap.

Suggested category on the first pass of each ticket:

| Ticket | Filed as | llama3.2:3b | phi4-mini | qwen3 4B instruct |
| --- | --- | --- | --- | --- |
| TD-2401 VPN | Network | Network | Network | Network |
| TD-2402 password | Other | Other | Access | Access |
| TD-2403 printer | Hardware | Hardware | Hardware | Hardware |
| TD-2404 Larkspur | Software | Software | Software | Software |
| TD-2405 outside mail | Email | Email | Email | Email |
| TD-2406 vague access | Access | Access | Access | Access |
| TD-2407 VPN drops | Network | Network | Network | Network |
| TD-2408 resolved keyboard | Hardware | Hardware | Hardware | Hardware |
| TD-2409 bounces | Email | Email | Email | Email |
| TD-2410 unnamed program | Software | Software | Software | Software |

Empty follow-up lists appeared only on qwen3’s three TD-2408 runs. An empty list is allowed. The other two models asked questions on that resolved ticket.

Repeats were stable. For both TD-2406 and TD-2408, each model produced the same summary, category, follow-ups, and draft on all three runs.

Drafts containing the string `Ashmere Press IT`: llama 3 of 14, phi4-mini 5 of 14, qwen3 7 of 14. The prompt asks for that signature. Missing it is an instruction miss, not an invalid response.

Wall-clock time for the 14 ticket calls, after warm-up:

| Model | Warm-up wall | Warm-up load | Ticket wall median | Ticket wall min–max | Generation median | Output tokens median |
| --- | ---: | ---: | ---: | --- | ---: | ---: |
| llama3.2:3b | 4.9 s | 2.6 s | 3.5 s | 3.0–5.2 s | 3.3 s | 124 |
| phi4-mini:latest | 6.2 s | 3.3 s | 6.4 s | 3.7–9.9 s | 5.4 s | 166 |
| qwen3:4b-instruct-2507-q4_K_M | 5.7 s | 2.8 s | 6.7 s | 4.6–10.3 s | 5.9 s | 178 |

Generation time is Ollama’s `eval_duration`. Load time on the ticket calls themselves was a few milliseconds.

## Subjective reading

These notes are judgments about usefulness to a technician. They are not a score.

### Ambiguous access, TD-2406

All three models kept the reading room as the reason for the request and asked which resource Samir means. None asked for the ticket status. None said access was approved. The drafts ask the resource question, so the requester has a next step.

llama3.2:3b said “unspecified resource for reading room” and also asked what work is blocked and when. The draft includes both questions. It omits the signature.

phi4-mini said he needs “a resource from last week for urgent work in the reading room” and asked what that resource is and what the deadline is. The draft asks both. It omits the signature.

qwen3 said the resource is unspecified and that the urgency is tied to the reading room. It quotes “the thing.” The draft asks which system, folder, or resource, and does not ask for the ticket status. It also omits a direct “what work is blocked?” question. The second follow-up asks for a deadline even though the ticket already says the need is for the reading room and is urgent.

### Resolved keyboard, TD-2408

qwen3 is the only model that closed the ticket. The summary says the keyboard was replaced and typing was confirmed. Follow-ups are empty. The draft tells Theo the E and O keys, the tilt, the replacement, and the facilities log, and invites him to reply if something else is wrong. It does not ask whether the ticket is resolved.

llama3.2:3b mentions the replacement, then asks Theo to confirm whether it is still broken. It also asks “What is the loaner laptop LP-14?” after the ticket has already named it.

phi4-mini states that the keyboard was replaced, then asks whether a technician did the swap and what the laptop’s current status is. The draft repeats those questions instead of closing.

### Other tickets, in brief

Password reset, TD-2402. phi4-mini and qwen3 suggest Access and ask which system. llama3.2:3b leaves the category as Other, which matches the filed field and is a weaker suggestion for “please reset.” All three drafts ask which system. None claims the reset is done.

Unnamed program, TD-2410. All three keep the tonight deadline, say the program name is missing, and ask for the name in the draft. phi4-mini and qwen3 also ask whether the flash is a window or an error, which matches the internal note. llama3.2:3b also asks when it is needed, which the ticket already answers with “tonight.”

Larkspur install, TD-2404. All three keep DS-14, Larkspur Layout 4, and Friday in the draft or summary, then ask the requester to confirm details already written. llama3.2:3b asks for the machine name. phi4-mini asks whether DS-14 is the right machine and which version, after the ticket says Layout 4. qwen3’s summary stops at “installation of Lark,” while the draft has the full product name and then asks Cole to confirm Larkspur and DS-14.

Printer, TD-2403. All three keep the Vale galley and the restart, and ask for the printer name and panel message that the earlier reply already requested and the requester has not answered. That repeat question is still useful while the ticket is Waiting on User. llama3.2:3b also asks what work is blocked, although the galley is named.

VPN from home, TD-2401. The useful missing fact is the home error text. The internal note already says the client is installed. llama3.2:3b asks about the error and also asks what the style guide share is, after the ticket named it. phi4-mini asks for the error text and misstates the office history as working from home on Thursday. qwen3 asks for the error text and also says the same failure happened Thursday at the office. The ticket says Thursday at the office worked.

Outside mail, TD-2405. All three keep internal mail, junk, and the missing bounce. phi4-mini’s draft says “We are committed to resolving this issue as soon as possible,” which is a time promise the ticket does not support, and it asks what has already been done after the gateway note answers that. qwen3 treats the mailbox as an “unspecified resource” and asks which system or folder, which the description does not leave unnamed. llama3.2:3b asks for a sender address, which is useful, and also for “the name of the spam threshold,” which is not a thing the ticket offers.

VPN drops, TD-2407. The archive share and public-library wifi are already in the ticket. llama3.2:3b still asks what system is failing. phi4-mini asks for the VPN product name and the library wifi name. qwen3 says the needed resource is unspecified even though the archive share is named, and then asks whether the drop happens only on public wifi. That second question is not answered by the ticket.

Partner bounces, TD-2409. All three ask for one full bounce, which the saved reply already requested and the activity does not contain. That is a useful repeat. qwen3 adds a question about which email client, which the ticket does not require for the next step.

## Which model looks most useful here

For these ten tickets, qwen3:4b-instruct-2507-q4_K_M is the more useful drafting model. It is the one that closed the resolved LP-14 ticket without asking Theo to reconfirm the repair, and it kept the unnamed resource unnamed on TD-2406 while still asking Samir what it is. It also moved the vague password ticket to Access and asked which system.

That usefulness costs time. After warm-up, its median ticket took 6.7 seconds of wall time and about 5.9 seconds of generation, against 3.5 seconds and 3.3 seconds for llama3.2:3b. phi4-mini sat next to qwen3 on speed, at a 6.4 second median, and handled the vague access ticket cleanly, but it still questioned the resolved keyboard ticket and promised a fast resolution on the outside-mail ticket.

llama3.2:3b is the quick model and every response was valid JSON. On this set it more often asked for a name or deadline the ticket already contained, left the password ticket as Other, and did not close the resolved ticket.

qwen3 still invented a Thursday office failure on the VPN ticket and sometimes applied the “unspecified resource” rule to problems that already name the share or the mailbox. Those are reasons to keep a person in the review step no matter which model is connected. This comparison does not change TinyDesk’s default model.
