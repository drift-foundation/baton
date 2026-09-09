# Mandatory concise agent reporting

2026-09-08, baton.prompt. Slawomir explicitly directed that concise reporting
be documented in EFFECTIVE-BATON and strictly followed by all agents.
W120425 illustrates the duplication: 1,616 progress words, 513 discussion words
and245 pass-comment words describing one handoff. These counts establish
reporting volume, not the time spent producing it.

Decision: one canonical technical account; short progress deltas, handoffs,
pass comments and operator summaries linking that account. Mandatory self-check
and reviewer enforcement, preserving material limitations, evidence and required
human decision recaps. No new approval stage or reporting-only blocker.

The exact proposed guide text is in REPORTING-GUIDANCE.md. Tuner owns only
docs/EFFECTIVE-BATON.md and this record, preserving unrelated guidance. Replace
the existing verbose handoff explanation with the concise mandatory rule and
example; link it from the evidence section. This is owner-directed documentation
implementation, not new product/test scope. After a focused diff check, close
the documentation Work satisfying and provide the final section locator.

Prompt will send a short adoption notice to the configured Baton agents after
the text lands. Existing required startup reading supplies future contexts.

## 2026-09-08 — Owner-authorized consistency follow-up

After W120660 closed, Slawomir authorized reviewing EFFECTIVE-BATON for stale
guidance in this reporting context. Prompt's focused audit found a handoff
example contradicting its queued-state explanation, progress ownership wording
older than AGENTS.md, and opportunities to make single-location evidence and
current-plan guidance explicit. AUDIT-2026-09-08.md specifies the bounded
documentation corrections; prior completion and evidence remain history.
Adoption notices were sent to claude, codex and merge through conversational
pokes120677/120684/120691; tuner authored the rule and prompt applies it here.

Adoption confirmed by claude at120694, codex at120697 and merge at120699.
Each read the guide and committed to concise linked reports; codex also
confirmed enforcement in existing handoffs. Future report compliance remains
an author/recipient check, not something the acknowledgement proves.

## 2026-09-08T19:45Z — observed adoption audit, baton.prompt

At Slawomir's request, sampled T120425/T121793/T121887/T119114 at snapshot122010.
Whitespace-delimited counts: Claude handoffs M121216/M121823/M121872/M121924
are 193/132/171/132 words against the 100-word limit. They repeat technical
accounts already in progress; the latest progress entry is 266 words including
headings. Reviewer reminders in the 19:20/19:29 reviews have not achieved
consistent adherence. Sampled codex handoffs are 28–78 words, review openings
51/61; tuner handoff69/progress74; prompt handoffs70/71. Merge was not sampled.
This audit measures reporting, not model time. Reinforce the existing rule in
W119114's next reporting: concise delta, canonical link, author count/self-check.
Preserve prior evidence and current execution; no new Work, gate or cleanup.

## 2026-09-08T19:46Z — owner clarification: advisory length, complete essentials

Slawomir clarifies: "the 100 word limit is not hard, it's advisory we cannot
risk skipping essentials". This supersedes the guide/proposal's hard-cap
interpretation for 100-word handoffs, review openings and operator summaries,
and M122020's numeric enforcement. The audit counts remain observations, but
exceeding a target alone is not noncompliance. Repetition remains an issue.

Make numerical lengths guidance rather than grounds to omit essential facts,
caveats, evidence, decisions or next actions. Concision and avoiding duplicate
technical accounts remain required; a recipient must still understand the
decision and act from the report. Longer reporting is appropriate whenever
needed for completeness. Apply the same completeness priority to the other
length targets so the guide does not create a competing omission incentive.
Do not require a new justification or approval merely for exceeding a target.
No historical report rewriting or reporting-only workflow gate. M122028
communicates this immediately; a narrow guide update and live-context notices
make it durable for subsequent reports.
