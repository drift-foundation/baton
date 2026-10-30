# W359718 — submission identity ownership

## 2026-10-23 — bounded decomposition from W358969

**Confirmed:** parent review `../../review-2026-10-23T22-41-20Z.md` R12 and
`../../evidence/review-359705/PROBE.json` show a reserved submission ID can be
consumed by an ordinary submission for a different Job. The Job-only reservation
query misses it; the retry subsequently collides after publishing a binding.
Authority is existing DESIGN REC-7 and DB-3–5, not a specification change.

**Outcome:** reserve Job identity AND submission identity/intended document
atomically across ordinary and fresh-attempt writers; preserve exact replay and
interrupted admission recovery. No new generic submission framework is selected.
Ordinary conflict rejection that does not poison the intended operation is an
accepted implementation choice; no new owner decision on durability is required.

**Acceptance:** nonoverlapping ordinary Job using reserved submission ID refuses
before publication/insertion; ordinary-first collision refuses retry before
external effects; two retry intents sharing a submission ID cannot both reserve
incompatible content; same/different Job IDs and changed content are covered.
Intended submission and exact replay still succeed after a rejected collision.
Preserve previous specification, limits, linked evidence and binding behavior.
Focused real disposable store/race/cut evidence, no live provider or engine.

Initial baseline: parent candidate-359603, manifest
`ad9a63db1fb83e015cfbe17f73d386d3f2a4ba92087e322cf9fb3d1cb43cab4d`.
Its host defects are explicitly outside this child's acceptance and remain
required in W359719. Parent W358969 owns joined acceptance before W325959.

**Ownership:** claimed baton.impl author owns this child's new isolated cumulative
candidate, test changes and PROGRESS; baton.rvpc owns FINDING/PLAN/review/evidence.
Parent candidates and canonical product bytes stay untouched. Evidence locations
in the review are not an exclusive files-to-edit restriction. Record actual
changed paths and base/candidate digests; no shared-path parallel execution.

## 2026-10-23T22:52:41Z — journal ownership remains a collision source

Claim359803 independently verifies candidate359749 manifestb7287b7b and all
candidate/base pins. All84 focused tests pass; concurrent incompatible retry
intents correctly produce one winner. R12's nonoverlapping Job bypass is fixed.
However a prior durable ordinary-submission refusal owns the operation identity
without a submissions row. The retry misses it, publishes binding and collides
irrecoverably at submission. R15 and exact evidence are in
`review-2026-10-23T22-52-41Z.md` and `evidence/review-359803/PROBE.json`.
This qualifies the author's corrected status: partial behavior accepted, slice
not yet accepted. Correct the same atomic ownership boundary without changing
host scope or prior journal semantics. W359719 remains gated.

## 2026-10-23T23:03:46Z — submission ownership slice accepted

Independent claim359879 accepts candidate359821 manifest9f06dbe3 for this
bounded outcome. Journalled refusal is now detected before reservation/effects;
alternate submission identity recovery works, conflicting retry names serialize,
and an actual post-submission/pre-completion interruption resumes with one
binding effect. All90 focused tests pass. Exact pins, evidence, two measured
probe runs and limits: `review-2026-10-23T23-03-46Z.md`.
This supersedes R15's changes-requested disposition. Close this child satisfying
to release W359719; preserve accepted bytes in its successor candidate. Parent
W358969 still owes combined acceptance; no pilot, import or live-run gate is waived.
