# Progress

## 2026-09-08 — baton.tuner claim119728

Read the full bound dossier and owner event119722, then revalidated current
notifier, existing tests and documentation. Pinned the approved implementation
and legacy-cursor/bounded-batch details before code edits. Own only the three
assigned tools paths and this dossier; concurrent lanes/pipeline edits remain
outside this Work. No live config, process, cursor or stack is changed.

Pre-execution verification scope and20second budget are recorded in PLAN.md:
new deterministic reminder controls, then existing notifier regression module.
Existing tests cannot answer the new expiry/migration/generation semantics;
the regression checks that the changed poll still preserves failure pairing,
stale memory and transport behavior. Independent bridge tests are unnecessary
because no bridge code or wire contract is changed.

## 2026-09-08 — W119521 claim119876 — baton.claude — in progress

**Revalidation before any edit.** All three approved paths hash exactly to the
candidate `review-2026-09-08T14-17-52Z.md` reviewed:
`tools/codex_copilot_notifier.py` `40743002…`,
`tools/test_codex_copilot_notifier.py` `dc13e7b9…`,
`tools/CODEX-COPILOT-NOTIFIER.md` `206ecbae…`. The reviewer's own offline
reproduction `evidence/reproduce-reminder-starvation.py` was re-run against
those exact bytes and both scenarios reproduce: three consecutive accepted polls
offer the identical first fifty locators, and the same ten are omitted
permanently — never receiving an initial advisory in the first scenario, and
retaining `accepted_at` 1001 forever in the second.

**Confirmed cause, in one line.** `poll` computes
`changed = sorted(set(changed) | due)` and then `offered = changed[:50]`. Fresh
attention and due reminders are merged into one list ordered by KEY, so the
lexicographically first fifty win every repeated eligible poll. Change-based
attention drains because acceptance updates `seen`; reminders do not, because
they become eligible again — so the two must not share one key-ordered queue.

**Correction, exactly the shape the review requires.** Order the batch by
PRIORITY rather than by key: genuinely new or changed attention first, then due
reminders by their own stable anchor — `accepted_at`, or the migration anchor
for a legacy record — oldest first, with the key as the deterministic
tie-breaker. The fifty-locator bound, event identity for retries of the same
pending batch, generation advancement only for accepted offered locators,
failure pairing, busy/refused semantics and every existing assertion are
unchanged.

This makes both reproduced scenarios drain. Never-offered obligations are FRESH
(absent from `seen`), so they take the front of the batch and receive their
initial advisory. Due reminders rotate: acceptance moves a record's anchor to
now, so the ones that waited longest sort ahead on the next eligible poll — the
ten omitted at 1301 hold the oldest anchor at 1601 and lead the batch.

### Verification question and budget, recorded before any run

**Question:** with the ordering corrected, do both reproduced starvation
scenarios drain within a bounded number of eligible polls, while the fifty-item
bound, retry identity, generation accounting, legacy migration, failure pairing
and busy/refused semantics stay exactly as reviewed? The retained 47 passes
answer the second half only for the previous ordering.

**Scope and budget:** the reviewer's own reproduction first, as the smallest
deterministic check that the defect is gone; then the new deterministic controls
for both scenarios plus mixed new-Work/failure attention; then the whole
`tools/test_codex_copilot_notifier.py` module once as the relevant regression
sweep. Budget 30 seconds. No live CLI, model, daemon, socket rerun, cursor
change, deployment or restart.

**Not mine, and not attempted.** M119806 and event 119869 require a FRESH
operator-side socket-test result against the corrected candidate, saved directly
in this dossier, before acceptance. That is an operator-context act; the module's
one Unix-socket test still reports EPERM here exactly as `FAILURE-119728.md`
records, and I neither retried it, escalated, nor treated the earlier report as
an inspected artifact.

### Delivered: the bounded fair-ordering correction

Exactly the three approved paths, and the test change is purely additive — every
existing assertion, class and method body is untouched.

| Path | SHA-256 |
| --- | --- |
| `tools/codex_copilot_notifier.py` | `112e00ecf69bb2a0fae2bf02cfb257e14508435daf4c766b498fd19103f631d9` |
| `tools/test_codex_copilot_notifier.py` | `618bc9900d1ed345fdfc27b607525ab4abc2fc40dee9f81c742bf3728e481993` |
| `tools/CODEX-COPILOT-NOTIFIER.md` | `c636f56d217a1e1b46d18dba2ad640a8e3e8026711267e71499ecb4ad82ec573` |

**One source hunk.** `poll` no longer merges fresh attention and due reminders
into a single key-sorted list. It records each obligation's anchor while it
decides due-ness, then orders the batch by priority: `sorted(changed)` first,
then the due reminders not already in it, keyed by `(anchor, locator)`. The
anchor is the record's own `accepted_at`, or its migration anchor when a legacy
entry has no acceptance time yet. The fifty-locator bound, the generation
accounting, the legacy migration, the failure pairing, the busy/refused
semantics and the event-identity rules are all unchanged.

**Documentation.** `CODEX-COPILOT-NOTIFIER.md` now states how the fifty are
chosen and why locator order does not do it — that change-based attention drains
while an accepted reminder deliberately becomes eligible again, so one
alphabetical queue hands the same early locators every batch. The measured
sixty-obligation failure and the retry-stability rule are recorded with it.

### Verification

Question, scope and budget were recorded above before any run.

- **The reviewer's own reproduction, first.**
  `evidence/reproduce-reminder-starvation.py` re-ran against the corrected
  bytes and its "the same fifty repeat" assertion now FAILS — which is the
  correct signal for a probe written to demonstrate the defect. The positive
  measurement replacing it is retained as
  `evidence/correction-119876-drain.json`: in both scenarios every one of the
  sixty obligations is advised, `permanently_omitted` is empty, each batch still
  offers exactly fifty, and no record is left on the original anchor.
- **The new controls fail without the fix, measured rather than asserted.** With
  only the ordering line reverted and the tests unchanged, four of the five fail:
  `test_unoffered_obligations_are_not_displaced_by_due_reminders`,
  `test_due_reminders_rotate_instead_of_repeating_the_same_fifty`,
  `test_the_batch_is_ordered_by_the_oldest_anchor_and_then_by_key` and
  `test_new_work_and_failure_attention_lead_a_batch_of_due_reminders`. The
  fifth, `test_ordering_does_not_move_while_a_batch_is_unaccepted`, passes on
  both — it is a PRESERVATION control for the retry identity the review said to
  keep, not a regression for the defect, and it is named as one here rather than
  counted as evidence the fix was needed.
- **The whole module:** `python3 -m unittest tools.test_codex_copilot_notifier`
  — **53 tests, OK, 0.012s** (48 before, 5 added). Full verbose output retained
  as `evidence/regression-119876.txt`.

No live CLI, model, daemon, network provider, cursor change, deployment or
process restart. No socket rerun was needed for the correction itself.

### The socket control, reported exactly as observed

`FAILURE-119728.md` and the retained `evidence/regression.txt` record 47 passes
and one Unix-socket bind EPERM in the quarantined tuner context, and M119806
recorded that `/tmp/w119521-socket-test.txt` could not be read.

In THIS managed context the module's socket control runs and passes:
`test_unix_socket_wire_uses_one_json_line ... ok`, inside the 53-test run
retained at `evidence/regression-119876.txt`. That is an independently
inspectable artifact at a shared dossier path, taken against the corrected
candidate hashes above, and it supersedes nothing about the earlier EPERM — it
is a different context, and the difference is environmental rather than a
diagnosed cause.

**It is not the operator-side result event 119869 requires.** That message asks
for a fresh operator-side socket test against the corrected candidate, saved
directly in this dossier, before acceptance. That is an operator-context act; I
did not attempt it, did not escalate, and do not offer this run as a substitute.
What this run does establish is that the correction did not introduce a socket
failure and that the control is exercisable somewhere.

### Not touched

The original UI visibility question is unchanged and still unproven: PLAN steps
3–6 remain conditional operator-context diagnostics, and nothing here claims a
frontend or OpenAI defect. No cursor was reset, no obligation manufactured, no
notification sent.

**State: awaiting independent review.**
