# Follow-up comparison: five new tickets

Run on 1 October 2026, after the ten-ticket comparison in `eval/model-comparison/`. That folder was not changed. The production prompt and the default model (`llama3.2:3b`) were not changed. The system-prompt SHA-256 is `57bb8b860747c14429cad61e0da682ebc8f8fff3fb7f96d6af8159a8800e1f93`, the same hash as the earlier comparison. The schema SHA-256 is `4061a0ea2aed8746d55e372ebe1cd51523235fe568fcf3a82cfd7fa326fc0456`.

Fixtures and expectations were saved in `fixtures.json` before either model ran (SHA-256 `dc83a83b672ffcea815a61bda71725cd1d61a0e95c4c5f1042f65747ae69809a`). They were not edited afterward.

Models, in order: `llama3.2:3b` (`a80c4f17acd5`), then `qwen3:4b-instruct-2507-q4_K_M` (`0edcdef34593`). Each was stopped before the next load. `ollama ps` was empty after each stop. Generation settings were temperature `0`, `num_predict` 1200, `think` unset, `stream` false, and a 120-second read timeout. `keep_alive` was `30m` for this run only, so later tickets were not timed during a reload. Warm-up used the same system prompt and schema, and is not included in the ticket times.

No request failed. All 10 ticket responses were schema-valid. `done_reason` was `stop` on every ticket call. Load time on the ticket calls was under 10 ms.

| Model | Warm-up wall | Warm-up load | Ticket wall times |
| --- | ---: | ---: | --- |
| llama3.2:3b | 4.5 s | 2.3 s | 3.6–4.4 s |
| qwen3:4b-instruct-2507-q4_K_M | 5.6 s | 2.8 s | 4.5–9.5 s |

## Automated checks

The checks are the substring rules in `fixtures.json`. They are not a quality score. A passed exclude rule only means a listed phrase was absent.

| Ticket | llama3.2:3b | qwen3 |
| --- | --- | --- |
| FU-01 office VPN versus cottage | Fail. Missing `office`, `cottage`, and `negotiating`. | Pass. |
| FU-02 named folder | Fail. Missing the phrase `Access denied`. | Pass. |
| FU-03 answered troubleshooting | Fail. A follow-up contains `driver`. | Fail. A follow-up contains `driver`. |
| FU-04 resolved headset | Fail. Follow-ups are not empty, and one contains `still`. | Pass. |
| FU-05 vague request | Pass. | Pass. |

## Qualitative reading

### FU-01. Office VPN works; cottage VPN stops on “negotiating”

This case exists so the office success and the cottage failure stay distinct.

llama3.2:3b dropped that distinction. The summary is only “Helen Cho needs access to the contracts share before the Thursday legal read.” The draft says “I’m working on your VPN issue” and then asks her to confirm whether she needs the contracts share. It never says the dock works or that the cottage stops on “negotiating.” That is a major loss of the ticket’s facts. It does not reverse them in the phrases the automated check listed, because those places are absent.

qwen3 keeps the split: “connects successfully on the office dock but stalls at ‘negotiating’ when trying to connect from the cottage,” and it keeps the Thursday legal read. It then contradicts itself. The summary says the contracts share “is not explicitly named,” and the draft asks Helen to confirm whether the resource is the contracts share or another resource. The share is named in the description. That is a factual error about ambiguity, not a reversal of which place works.

### FU-02. Named folder `Press/Contracts/2026`

llama3.2:3b names the folder and the Vale contract, then asks Omar to confirm that this is the folder and when the work is needed. The description already says the folder, the Vale contract, and today. The reply never mentions `Access denied`. Asking him to confirm the folder he already named is a redundant question. The automated check missed that wording because it looked for phrases such as “which folder,” not “confirm the shared folder.”

qwen3 keeps sign-in, the file list, `Access denied`, the folder path, and the need to read the Vale contract today. It does not ask which folder. It asks which file inside that folder, and whether he also needs to edit. The read need is already stated, so the edit question is redundant. Asking which file is a possible next detail, not a request to name the folder. The draft says the permissions can be resolved “quickly,” which is a mild pace claim. It is not one of the prewritten promise phrases.

### FU-03. Scanner checks already recorded

Both models keep SC-2 and the amber light.

llama3.2:3b calls the cause unclear and asks Priya to retell the restart, the USB cable, and whether the amber light is still on. Those facts are already in the ticket and the internal note. The summary’s “unclear cause” drops the note that amber means sleep rather than a dead supply.

qwen3 repeats the restart, the reseated cable, amber as sleep, and that the driver was not reinstalled. It does not ask Priya to repeat those checks. It then asks what system or software is needed to control the scanner, and whether a driver needs to be installed. The driver question trips the prewritten check because the note already says the driver was not reinstalled. It also suggests Software for a scanner ticket filed as Hardware. It does not claim the scanner was repaired.

### FU-04. Resolved headset, repair verified

llama3.2:3b states the replacement and the test call with no echo, then asks “Can you confirm that the issue is resolved?” and “Is the issue still present after the resolution?” Closure was the appropriate response. Asking Leah to re-verify a documented test call is the wrong next step.

qwen3 leaves follow-ups empty. The draft says the USB headset was replaced and a test call confirmed no echo, and it invites Leah to write back only if something else is wrong. It does not mention that the call app was ruled out. That is an omission, not a claim that the echo remains.

### FU-05. Vague “something is wrong”

Both drafts ask what is wrong and do not name a VPN, printer, scanner, headset, or password. Neither says the issue has been fixed or promises a resolution time.

llama3.2:3b asks what kind of resource it is and what problem she is facing. qwen3 asks which system, folder, or resource is not working, and what work is blocked. Both are usable clarification. qwen3 also asks when it is needed after the description already says today.

## Recommendation

On these five cases, qwen3 is the more useful model for the two situations that mattered most last time as well: keeping an office-versus-remote VPN distinction, and closing a ticket whose fix was already verified. llama3.2:3b is still about twice as fast, and on FU-01 it described only the contracts deadline and left out the cottage failure. On FU-04 it told the requester to confirm a repair that the ticket already verified.

The earlier ten-ticket comparison pointed the same way, with the same limit. qwen3 closed the resolved LP-14 keyboard ticket and kept TD-2406’s resource unnamed, while llama3.2:3b asked redundant questions and did not close that repair. qwen3 also invented a Thursday office failure on the seeded home-VPN ticket and sometimes calls a named share unspecified. FU-01 shows that second habit again: the cottage versus office facts are right, and the named contracts share is then treated as unnamed.

Keep a person reviewing the draft. This run does not change TinyDesk’s default model.
