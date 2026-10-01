# TinyDesk

TinyDesk is a small help desk for working a daily ticket queue. This version is the frontend demo for an IT support portfolio. Tickets, edits, and activity stay in the browser. The assistant shows clearly labeled sample suggestions, not live model output.

Ashmere Press, and everyone in the sample queue, is fictional.

## Run

There is no build step and no package install. Use a local web server so the JavaScript modules can load.

```bash
git clone https://github.com/cyb3rcricket/TinyDesk.git
cd TinyDesk
python3 -m http.server 8080
```

Open http://localhost:8080

## What works

- Search the queue by ticket number or subject.
- Filter by status and category, and clear those filters.
- Open a ticket, then return to the queue.
- Create a ticket. The number, opened time, and updated time are generated. New tickets start as New with Medium priority.
- Change category, priority, and status, then save. A resolution note is required before a ticket can be Resolved. Status changes are written into the activity history.
- Add an internal note or a reply to the requester.
- Ask TinyTalk Assist to analyze a sample ticket, apply the suggested category to the form, or place the draft in the reply composer. If the composer already has text, TinyDesk asks before replacing it.
- Keep the queue after a refresh. The first visit with no saved data loads ten sample tickets. After that, the saved set is used.
- Reset demo data, after a confirmation, back to those sample tickets.

Statuses are New, In Progress, Waiting on User, and Resolved. Priorities are Low, Medium, and High. Categories are Access, Network, Hardware, Software, Email, and Other.

## What is simulated

- Replies are stored on the ticket. TinyDesk does not send email.
- Analyze ticket does not call a model. The ten sample tickets return fixed suggestions from `js/analysis.js`. A ticket you create shows a placeholder that says live analysis is not available yet. That placeholder is not presented as model output.
- There is no sign-in, no attachments, and no SLA clock.

User-entered text is rendered as text.

## Where TinyTalk connects later

TinyTalk will be a separate Python project that talks to Ollama. The screen already awaits `analyzeTicket(ticket)` in `js/analysis.js` and only renders the returned object.

Replace that function with a request to the TinyTalk backend. Keep the same result shape:

- `available: true`, with `summary`, `suggestedCategory`, `followUps`, and `draft`
- `available: false`, with a `message`, when analysis cannot run

The queue, the ticket form, and the `localStorage` store can stay as they are. The assistant panel does not need to know whether the result came from the sample table or from TinyTalk.

Saved tickets live under the `localStorage` key `tinydesk.tickets.v1`.

On a wide window the queue is a table and the assistant sits beside the ticket. On a narrow window the queue becomes a list and the assistant moves below the ticket.
