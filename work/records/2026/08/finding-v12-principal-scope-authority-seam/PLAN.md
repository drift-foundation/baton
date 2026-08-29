# Plan

1. [done 2026-08-28] Revalidate W9901 and the W16793 matrix against the current
   authority tree after W5 closed.
2. [next; schema-1 disposition approved by M33752] Pin the smallest versioned
   principal, Work-scope and authorization-decision
   shapes; keep endpoint identity separate and keep hierarchy resolution out.
3. [approved 2026-08-28 by M33752] Version authority persistence and
   configuration/projection APIs around those shapes. Treat schema 2 as a clean
   initialization boundary: refuse schema 1 read-only with an operator-directed
   disposable-store reinitialization diagnostic; never infer missing authority
   facts or interpret, mutate, delete, rewrite, auto-migrate, or partially apply
   a new schema to the old file.
4. Move route/capability decisions through the authority seam and persist their
   provenance on attributable acts.
5. Migrate claim capacity from participant-keyed to principal-keyed while
   preserving atomic one-live-claim enforcement and assignment fencing.
6. Add positive, negative, replay, race and reopen tests, including two endpoint
   addresses for one principal and one endpoint that cannot select another
   scope.
7. Return for independent review before the Worker Manager context correction
   consumes the new projection.

Migration remains separate future product Work only when retained user state
requires it; it is not part of this disposable-proof-store correction.

## 2026-08-28 — implemented

2. [done] `authority/principals.py`: principal, scope and authorization
   decision, with grammars disjoint from `team.member` and a provenance
   vocabulary whose durable shape admits inheritance while this cut refuses to
   produce it.
3. [done] Schema 2, and `store._check_compatibility` refusing an incompatible
   store read-only, byte for byte, with the operator-directed reinitialization
   diagnostic. Proved by four cases, including one that makes the rest of the
   older file unreadable as SQL to show the refusal is decided from the `meta`
   marker alone.
4. [done] `Core.authorize` is the one seam; `claim` and `_require_capability`
   both go through it and both persist what it answered.
5. [done] Claim capacity keyed by principal, with the endpoint kept beside it
   for the Handler, the fence and the assignment identity.
6. [done] `tests/authority/test_principal_scope.py`, 30 cases, and
   `evidence/w16821-mutation-harness.py` — 14 of 14 caught.
7. [next] Independent review. The Worker Manager consuming the new projection
   stays deferred; `PROJECTION_UNREAD` names `scope` without reading it, which
   is what keeps the manager's closed-member contract true.

Open for the reviewer to settle: decision provenance on the four remaining
attributable acts — copy the claim's decision forward, or join to it.

## 2026-08-28 — independent review changes requested

- [required] Derive every capability decision from the exact target Work
  scope; a deployment-scope grant must not authorize receipts or close for a
  differently scoped Work.
- [required] Persist each directly authorized act's exact immutable decision,
  including close and durable refused integration attempts. Assignment-derived
  acts may copy it or durably join through the full assignment identity, but
  every public historical projection must expose it without consulting current
  configuration.
- [required] Project the claim decision from `assignment_events`; raw-SQL tests
  do not establish the public evidence contract.
- [required] Deliberately version or replace `capabilities_of` so scope and
  provenance are not flattened into duplicate names.
- [required] Add positive, negative, restart/reconfiguration, historical-read,
  and mutation regressions listed in
  `review-2026-08-28T20-54-18Z.md`, then return for another independent pass.

## 2026-08-28 — review answered

- [done] Every capability door derives its scope from the exact target — the
  Work being closed, the Work the proposal belongs to — with `scope` a required
  keyword and a lexical guard over `core.py`'s own AST holding every call site
  to it. Positive and negative cross-scope cases for verify, review, approve,
  integrate and close.
- [done] One `authorization_decision` table retains the exact decision for
  every directly authorized act — claim, close, each receipt, and the durably
  journalled refused integration attempt — refusing a second write rather than
  overwriting. Assignment-derived acts join to the claim's decision through the
  full exact assignment identity.
- [done] Every public projection carries the complete typed decision, and every
  case reads the projection rather than the column. History is read, never
  re-derived: proved across release, rebinding, a moved generation, close and a
  store reopen.
- [done] `grants_of` carries scope and provenance; `capabilities_of` is kept as
  an explicitly documented distinct-names helper.
- [done] Measured by removal, 22 of 22, covering all six boundaries the review
  named.
- [next] Independent re-review.

## 2026-08-28 — independent re-review changes requested

- [required] Replace `_claim_decision_for`'s newest-match lookup with a durable
  link from every assignment-derived act to the exact claim event it ran under.
  The current `(work_id, participant, generation)` join is ambiguous for two
  v11 claims by the same endpoint because both generations are null.
- [required] Prove an activity written under the first v11 claim retains that
  claim's principal, scope, role, provenance and policy generation after
  release, endpoint rebinding, a second claim, another activity, store reopen
  and projection of both claim events and both activities.
- [required] Add a removal mutation for the durable act-to-claim binding and
  rerun the focused and full authority gates before returning for re-review.
- [next] Independent re-review after the historical join is exact for both v11
  and v12 assignments.

## 2026-08-28 — re-review answered

- [done] Assignment-derived acts durably name the EXACT claim event they were
  carried out under, captured at the act. The v11 release/rebind/reclaim/reopen
  regression covers both claim events and both activities; the v12 historical
  case is retained beside it.
- [done] Measured by removal, 25 of 25, including three new mutations for the
  durable binding.
- [next] Independent re-review.

## 2026-08-28 — independently signed off

- [done] The retained v11 failure reproduction passes across release, endpoint
  rebinding, reclaim and reopen; equal null-generation assignment documents
  retain distinct exact claim decisions.
- [done] Both public reproductions, 50 focused seam tests, all 277 authority
  tests, 25/25 removal mutations and scoped diff checks pass independently.
- [done] PLAN item 7: independent review completed. W16823 may consume the new
  projection; hierarchy resolution, inherited grants and masks remain deferred
  to their owning later Work.
