# TinyDesk review — 5 November 2026

The backend analysis path is careful and covered by tests. The real problems are ticket state in the browser, a couple of guards that do not hold, and one context limit that is applied to both providers.

No code was changed.

## Critical

**Reopening a ticket leaves a hidden resolution in place.** `js/store.js`, `saveTicketFields`. The note is written only when the new status is Resolved. Changing the status to In Progress, Waiting on User, or New leaves `resolutionNote` as it was. The resolution field is then hidden, so the queue no longer shows it, and there is no way to clear it. Analyze still sends that note as `currentFields.resolutionNote`, which the prompt treats as the saved resolution and as permission to say the issue was fixed. Clear the note when saving any non-resolved status, and record that in the activity line.

**Two open tabs overwrite each other.** `js/store.js`, `load` and `commit`. The first read is cached for the life of the page, and every save writes that whole cache back to `localStorage`. There is no `storage` listener. A ticket created or edited in the other tab is dropped on the next save here. Read `localStorage` on each update instead of keeping a private cache. This data is small enough that the cache is not earning its keep.

## Important

**The 200 KB analyze limit is skipped when `Content-Length` is absent.** `backend/app.py`, `limit_analyze_body`. The check runs only when the header is present and greater than 200000. A chunked request has no header, and a negative length also passes. Field limits still apply, but those limits allow 5000 activity entries of 200000 characters each, so one request can force a very large parse. Reject a missing or non-positive length, and enforce the same cap on the bytes actually read.

**The `.env` loader mishandles two common file shapes.** `backend/config.py`, `load_local_env`. It reads UTF-8 and skips any key that is not strictly alphanumeric, so a leading BOM makes the first variable disappear. It also keeps a trailing `# comment` as part of the value. On Windows, Notepad’s UTF-8 save is enough to leave `TINYDESK_AI_PROVIDER` unset while the rest of the file loads, so the panel stays on Ollama. Read with `utf-8-sig`, and strip an unquoted trailing comment.

**Routing and stored tickets can throw and stop the page.** `js/app.js`, `parseRoute`, calls `decodeURIComponent` on the hash. A fragment such as `#/ticket/%` raises `URIError`, and `hashchange` does not catch it. `js/store.js`, `getTickets`, calls `updatedAt.localeCompare` with no check, and `renderActivity` does the same with `at`. `load` only replaces storage when the JSON itself is invalid. One object with an id and no timestamps takes down the queue; one bad activity entry takes down that ticket. Catch the decode error and show the queue, and in `normalizeTicket` require string timestamps or drop that record.

**xAI requests follow ambient proxy settings.** `backend/xai_client.py`, the `httpx.Client(...)` call. `trust_env` defaults to true, so `HTTPS_PROXY` receives the ticket body and the `Authorization` header. The assistant panel only says the ticket is sent to xAI. Pass `trust_env=False`.

**Long tickets are cut to the local 4096-token window even when the provider is xAI.** `backend/analysis.py`, `PROMPT_TOKEN_BUDGET` and `build_model_payload`. That budget is `4096 - 1200`, and `user_message` always shrinks to it before the provider is considered. Grok then never sees the dropped history or the cut-off note, and the panel does not say the copy was shortened. Shrink only for Ollama. If xAI rejects the input, the existing context-limit error already covers that.

**The page asks for a font that is not in the repo.** `css/styles.css` loads `fonts/manrope.woff2`. `css/fonts/` contains only `OFL.txt`. Every page load 404s that file, and the UI falls back to Segoe UI or Avenir. Add the woff2 file, or remove the `@font-face` rule and the unused license.

**A page on this machine can call the API.** `backend/__main__.py` binds to `127.0.0.1`, and there is no Host check. A normal public website is blocked by CORS. A DNS-rebinding page is same-origin to the browser and can POST `/api/analyze-ticket`, which spends the local model or the xAI key. Reject a `Host` other than `127.0.0.1:8080` and `localhost:8080`. The test client sends `testserver`, so keep that allowance in the tests only.

## Simplify

Nothing here needs a new structure. The dense part is `estimate_tokens` and the shrink loop in `backend/analysis.py`. It is hard to read, and it should stay: it is matched to the measured Qwen window, and the tests lock that budget. A shorter character heuristic would be a behavior change.

The `.env` path blocker in `backend/app.py` is more code than the current routes need, because the repo root is not mounted. It is small, tested, and aimed at a real file. Leave it.

## Minor

**CI and the README name different Python versions.** `.github/workflows/ci.yml` runs 3.11. The README requires 3.12+. The code itself runs on 3.11. Pick one and use it in both places.

**Follow-ups are capped at 6, while the prompt asks for 3.** `backend/schemas.py`, `clean_followups`, stops at 6. `system_prompt` says at most 3. Truncate to 3 so the panel matches the instruction.

**A bad timeout is ignored.** `backend/config.py`, `load_settings`. Values that are not a positive number up to 600 become 120, with no log. Log the rejection so a typo is visible.

**The storage warning disappears on the next navigation.** `js/app.js`, `renderRoute`, clears the banner unless `keepBanner` is set, and that flag lasts for one route change. Show `getStorageWarning()` again while it is still set.

**A failed browser save still says it succeeded.** `js/store.js`, `commit`, updates the memory cache even when `localStorage.setItem` throws, and the callers still return success. `onSaveFields` then sets “Changes saved.” Return a failure from `commit`, and show that on the form. The banner text is already the right explanation.

**xAI context errors are detected by substring.** `backend/xai_client.py`. Any 400 body containing both “context” and “token” becomes `context_limit`. Match the API’s actual error code, and leave other 400s as `bad_response`.

**Ollama truncation is reported as a bad result.** `backend/ollama_client.py`, `complete`. A non-empty body is returned even when the reply was cut at `num_predict`. The user then gets “could not use” from JSON validation. If `done_reason` is `length`, use the same capped-output failure xAI already has.

**Ticket ids are written into logs unchanged.** `backend/analysis.py`, `_log_failure`. An id may contain a newline, which forges a second log line. Strip CR and LF from the id before logging.

## Leave alone

The prompt is long and repeats a few rules in the user message. That repetition is there so ticket text is treated as data. Shortening it is a model-quality change, not a cleanup.

Model failures return HTTP 200 with `available: false`. The page and the tests both use that contract. Unhandled exceptions are logged and turned into the same kind of response, without the ticket text.

There is no login, no email, and no server-side ticket store. The README states that, and the page labels simulated replies and cloud sends.

Ollama’s context math will still be wrong for a different local model. The README already says a rejected ticket surfaces as an error rather than a silent fallback.

The frontend is one module and the backend has no client interface type. At this size, splitting them would add structure without removing a bug.

The duplicated category lists are checked by `test_categories_match_the_frontend_store`. The eval JSON is recorded output, not dead code.
