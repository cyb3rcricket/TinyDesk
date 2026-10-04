# TinyDesk Roadmap

TinyDesk is a help desk demo for fictional Ashmere Press tickets.
TinyTalk Assist helps a technician understand tickets, identify
missing information, and prepare their next response.

The goal is useful assistance with clear evidence and human control.

## Current capabilities

- Ticket summaries based on saved fields and activity.
- Suggested ticket categories.
- Follow-up questions for meaningful missing information.
- Editable reply drafts.
- Local AI through Ollama.
- Optional cloud AI through xAI Grok.

Analysis does not modify saved tickets. Applying a category or using
a draft requires a separate save action.

## Current milestone: finish the provider integration

Reported progress:
- The approved ServiceNow-inspired UI refresh is implemented.
- Ollama remains the default without provider configuration.
- The xAI provider works with local environment configuration.
- Grok's high-reasoning evaluation reports 12 usable drafts across
  twelve frozen cases.
- Local secret-file protection and mocked checks are reported passing.

Remaining:
- Complete explicit reasoning and output-limit controls.
- Evaluate the configured low-reasoning option.
- Choose the demonstrated configuration based on quality and latency.
- Finish separate UI and AI integration reviews and PRs.
- Document setup, cloud data transmission, costs, and known limitations.

These reported results are an initial evaluation, not a guarantee
that every ticket will receive a correct answer.

## Phase 1: suggested next steps

Goal:
Help the technician decide what to check next.

Features:
- Identify the current blocker.
- Separate confirmed facts, unknown information, and hypotheses.
- Suggest up to three relevant next checks.
- Explain why each suggestion follows from the ticket.
- Skip troubleshooting already completed.
- Recognize verified resolution and later reopening.
- Return no troubleshooting steps when none are justified.

First release:
A read-only "Suggested next steps" section in the assistant panel.

Acceptance:
- Suggestions use the ticket's actual identifiers and latest evidence.
- Hypotheses are never presented as confirmed causes.
- No invented repairs, approvals, policies, or promises.
- Resolved and reopened cases receive appropriate handling.
- A small evaluation includes completed checks, missing evidence,
  conflicting identifiers, and embedded malicious instructions.

## Phase 2: knowledge-base lookup

Goal:
Ground suggestions in relevant Ashmere Press documentation.

Features:
- A small, curated fictional knowledge base.
- Lookup by application, device, error text, and ticket topic.
- Article references with titles and relevant excerpts.
- Clear distinction between ticket evidence and article guidance.
- An explicit "No relevant article found" result.
- Visible document version or review date where available.

First release:
A handful of Markdown articles with simple search. Add more complex
retrieval only if the initial approach proves insufficient.

Acceptance:
- Every cited article exists and supports the associated suggestion.
- Similar terminology alone does not establish applicability.
- Retrieved documents cannot override assistant instructions.
- Missing guidance is acknowledged rather than invented.
- Suggested next steps identify when they rely on an article.

## Phase 3: internal notes and handoff drafts

Goal:
Reduce the effort needed to document and transfer work.

Features:
- Editable internal-note drafts.
- Handoff summaries containing:
  - The issue and affected resource.
  - Checks already completed.
  - Results and unresolved blockers.
  - Proposed next actions, clearly labeled.
- Resolution-note drafts only when recorded evidence supports them.

Acceptance:
- Proposed work is never described as completed work.
- Technician-only notes remain separate from requester replies.
- Drafts require an explicit save.
- No invented ownership, escalation destination, or completion time.

## Phase 4: duplicate-ticket suggestions

Goal:
Identify tickets that may describe the same incident.

Features:
- Candidate matching using resource identifiers, symptoms, and timing.
- Side-by-side ticket summaries.
- Evidence explaining each suggested match.
- A distinction between "possible duplicate" and "similar issue."
- Technician confirmation before recording a relationship.

First release:
Suggestions from the existing fictional ticket collection.

Acceptance:
- Shared category alone does not imply duplication.
- Contradictory identifiers or symptoms are visible.
- No automatic merging, closing, or deletion.
- The technician can dismiss a suggestion.

## Phase 5: related-ticket patterns

Goal:
Help technicians notice recurring issues across distinct tickets.

Features:
- Related tickets grouped by resource, application, or symptom.
- Recurrence indicators and relevant dates.
- Links to the supporting tickets.
- Separate views for open and resolved examples.
- Potential shared causes labeled as hypotheses.

Acceptance:
- Pattern claims identify their supporting tickets.
- Separate incidents are not mislabeled as duplicates.
- Historical fixes are not assumed to apply to a new incident.
- Small samples and conflicting evidence are acknowledged.

## Phase 6: queue triage and prioritization

Goal:
Help a technician choose what to review next.

Features:
- Suggested review order.
- Explanations based on recorded impact, deadlines, blockers,
  recurrence, and current priority.
- Flags for missing impact information.
- Clear distinction between review order and saved ticket priority.

Acceptance:
- No invented SLA, deadline, affected-user count, or business impact.
- Recommendations do not silently change priority or assignment.
- Current priority and recommendation reasons remain visible.
- The technician retains control of the queue.

## Rules for every AI feature

- Preserve complete saved tickets.
- Treat ticket and retrieved-document text as untrusted data.
- Keep facts, hypotheses, recommendations, and completed actions distinct.
- Keep generated text editable.
- Require explicit actions to save changes.
- Show which AI provider produced the result.
- Handle unavailable providers and incomplete output clearly.
- Protect credentials from frontend delivery, logs, and git.
- Preserve evaluation evidence when changing prompts or settings.
- Evaluate new capabilities separately; existing draft-quality results
  do not establish troubleshooting or retrieval quality.

## Scope boundary

Automatic repairs, command execution, outbound messages, access grants,
ticket merging, and autonomous closure are outside this roadmap.

## Delivery approach

Build one capability at a time. Use small fictional examples with
expectations written before evaluation. Preserve the approved design.

The next feature milestone is suggested next steps.
Knowledge-base lookup follows to strengthen their grounding.