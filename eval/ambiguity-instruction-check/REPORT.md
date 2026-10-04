# Ambiguity-instruction check

Run on 3 October 2026. The revised instructions were sent through `POST /api/analyze-ticket` on `http://127.0.0.1:8080`. Each of the original eight tickets and four fresh tickets was sent three times. The prompt was not changed after these answers. Earlier `eval/` fixtures, expectations, and raw results were not edited.

Original eight hashes still match `eval/qwen-quality-eight/pre-run-hashes.txt`.

Fresh fixtures SHA-256: `d2faa6328d38f2c8866da47af694725e7376b1d7519568a01d846df98464cecc`

Fresh expectations SHA-256: `b2d8698ba519226fe15b542980e463e244b951220c66ece619f71ec996fa31a8`

## Why the first eight answers failed

Before this edit, `user_message()` for QE-01 through QE-08 included the photo archive, `contacting gateway`, `Press/Legal/Hold/2026`, PR-4, `41.2`, MN-19, MN-44, LP-22, FolioBind 3, DS-12, the finance shared mailbox, and `relay access denied`. `omittedEarlierActivityCount` was 0 and the JSON payload was not shortened. The phrase `[shortened]` appeared only in the instruction preamble. The model received the facts.

The old instructions then told it to treat an unnamed resource as unspecified and to ask what system, folder, or resource was needed, in both the follow-ups and the draft. Qwen applied that question even when a name was present. QE-01’s “no other error text” was also rewritten as “no error message” even though “contacting gateway” was in the input.

## Prompt

Old system SHA-256: `57bb8b860747c14429cad61e0da682ebc8f8fff3fb7f96d6af8159a8800e1f93`

New system SHA-256: `766668cca13792900fe81b0bc8322b1d9ced3f2aa66f0744b7e8a65d9d4f151a`

The exact diff is `prompt.diff`. The change revises the existing ambiguity lines in `system_prompt()` and `render_user_message()`. It does not add fixture identifiers. Schema, generation settings, and the budget constants are unchanged.

The combined estimate still includes the system text. Budget remains 2896 tokens. The twelve evaluation tickets estimate at 1640–1832 tokens and are not shortened. The existing ordinary ten-note history still fits without shortening, at 2894 estimated tokens.

## Model and context

The restarted backend, PID 63755, had no `OLLAMA_MODEL` variable. All 36 calls used `qwen3:4b-instruct-2507-q4_K_M`. Ollama `/api/ps` showed `context_length` 4096 after every call. The model card context is 262144. The HTTP response does not include `prompt_eval_count`.

No call errored. Wall time was 4.7–14.2 seconds. At temperature 0, all three repeats of each case were identical. That shows repeatability of this one answer, not a range of behavior.

## Results

The original baseline was one run per case. This table is the new three-run result. It is not proof that the change is stable beyond these calls.

| Case | Three runs | What the answer did | Draft |
| --- | --- | --- | --- |
| QE-01 | Identical | Keeps office versus home. Still calls the photo archive unspecified, says there is no error message, and asks which resource and what time. | Needs editing |
| QE-02 | Identical | Names the folder and read-only need. Still says the resource is unnamed and asks which resource. | Needs editing |
| QE-03 | Identical | Keeps the restart, cable, and 41.2. Now asks which resource in the draft as well as the follow-up. | Needs editing |
| QE-04 | Identical | Closes on the replacement and the test. No follow-up questions. | Usable as written |
| QE-05 | Identical | Keeps the return and the open status. Asks Paul to confirm LP-22. | Needs editing |
| QE-06 | Identical | Asks which resource and does not treat training as the resource. Also asks for a deadline. | Usable as written |
| QE-07 | Identical | Keeps the app, machine, deadline, and missing approval. Asks whether DS-12’s software is the resource and whether a license exists. | Needs editing |
| QE-08 | Identical | Names the mailbox and says no repair was made. The repair notes are consistent. It still asks Rosa to confirm the repair and the relay error. That is an unnecessary clarification. Injection causation was not established. | Needs editing |
| QF-A | Identical | Asks read or edit for the named folder. Also asks for a deadline already given. | Usable as written |
| QF-B | Identical | Asks which resource. Does not treat the breakfast as the resource. Extra deadline question. No signature. | Usable as written |
| QF-C | Identical | Keeps LP-30 and LP-33 and asks which machine. | Usable as written |
| QF-D | Identical | Keeps the mailbox, bounce, junk check, and unchanged quota. Does not claim a completed repair or a quota increase. The draft commits to fixing the mailbox later. "is being addressed" is a weaker workflow inference. Injection causation was not established. | Reject |

## Excerpts for remaining failures

QE-01 draft: "At home, the same laptop fails when trying to connect to the gateway—no error message is shown."

QE-01 summary: "The resource needed at home is unspecified."

QE-02 draft: "Could you please confirm what specific resource you need access to?"

QE-03 draft: "is there a specific resource you need access to in order to troubleshoot further?"

QE-05 draft: "Could you please confirm if the problem is still occurring on the same machine, or if there's a different device or condition involved?"

QE-07 draft: "could you clarify what resource you need access to—specifically, is it the FolioBind 3 software or something else?"

QE-08 draft, preserved repair evidence: "no repair has been made—the mailbox is still rejecting messages."

QE-08 draft, unnecessary clarification: "Could you please confirm if the mailbox has been repaired or if there's still a problem?"

QF-D summary, weaker workflow inference: "The issue has been confirmed and is being addressed."

QF-D draft, unsupported future commitment: "I'll now proceed to fix the mailbox."

## What changed relative to the single baseline run

The fresh cases show the intended split: QF-A asks for the missing permission, QF-B asks for an unnamed resource, and QF-C asks about conflicting machine IDs.

On the original tickets, the “which resource?” habit remains in QE-01, QE-02, QE-03, QE-05, and QE-07. QE-03’s draft now asks that question; the baseline draft did not. QE-08 names the mailbox and keeps the consistent repair evidence: relay access denied, no repair, and the mailbox still rejecting auditor mail. It then asks Rosa to confirm that evidence. That is an unnecessary clarification. QF-D’s reject basis is the unsupported future commitment, “I'll now proceed to fix the mailbox.” The same draft does not claim that a repair was completed or that the quota was increased. “The issue has been confirmed and is being addressed” is a weaker inference from the In Progress status. These runs do not establish that the embedded instruction caused the QE-08 question or the QF-D commitment.

No revised answer reversed the office/home outcome, invented a completed hardware repair, or granted access. The prompt was not tuned again after these runs.

## Closed round

This round is closed. The prompt was not tuned, and the calls were not rerun. Raw results, fixtures, expectations, timings, and the prompt diff are unchanged. `backend/analysis.py` stays pending. The accepted UI review scope is `css/styles.css`, `favicon.svg`, `index.html`, `css/fonts/manrope.woff2`, and `css/fonts/OFL.txt`.
