# Committed ordinary cleanup reader

W120762, provider for W120425. Created by baton.codex under claim120753.
**Confirmed authority:** Slawomir event120736 approves Provider A in
`baton:work/records/2026/09/finding-v12-composed-ending-recovery/findings/finding-historical-implementation-proof/PROVIDER-SPLIT-PROPOSAL-2026-09-08.md`.
Read that exact section and the originating review-2026-09-08T16-18-42Z.md
before implementation; they own the technical explanation and full acceptance
matrix. The proposal's unallocated status is superseded by that owner ruling.

**Confirmed gap:** historical driver recovery currently calls serving cleanup
on missing journal evidence, reaching Authority; empty nested custody is also
accepted. The public owner must read committed ordinary runtime.destroy
evidence locally and validate complete ownership before returning it.

Exact scope under v12/python:

- src/baton_v12/worker_manager/intake.py
- src/baton_v12/worker_manager/__init__.py (public export only)
- tests/manager/test_intake.py (additive; preserve all existing assertions)

Approved interface: cleanup_of(store, *, attempt_id, retention_policy_digest).
Genuine absence answers None; present invalid or foreign evidence refuses.
No port/adapter, external operation, write, schema/store change or other cleanup
family. Revalidate ordinary owner helpers and pin the exact receipt contract
before editing. No duplicate private custody protocol in the driver.

Acceptance includes actual retain/discard cleanup, reopened local replay,
zero external acts/writes, absence and all malformed/foreign/nested ownership
controls listed in Provider A. About20s focused budget, declared before running.
Further expansion requires a concrete failure of the agreed demonstration.

High serial baton.impl execution returns baton.bug. Independent acceptance
releases W120763's serial allocation; W120425 waits for both providers.

## Independent review — 2026-09-08, claim120847

**Changes requested.** review-2026-09-08T16-43-59Z.md supersedes the delivered/
awaiting-acceptance disposition. Independent reopened-fixture probes confirm
seven false-success cases across signature ownership, ending relationships,
complete retention and the ordinary receipt's member set. Exact snapshots and
results are retained in evidence/review-120847-*. The approved interface and
local custody composition remain; correct this bounded adoption result before
either dependent proceeds. The review owns the technical correction account.

## Technical correction verified — 2026-09-08, claim120907

review-2026-09-08T16-51-10Z.md supersedes the outstanding four technical
corrections: seven negative and two positive independent probes pass. Overall
acceptance remains pending one exact existing-test replacement described in
that review. Recommend owner approval of the replacement, which preserves the
two relevant refusal boundaries under the corrected ordering. No new code or
broad verification is requested; keep both dependent gates until disposition.

## Bounded owner exception and acceptance — 2026-09-08, owner121008

Slawomir approves only the test replacement and companion kept-list control
enumerated in review-2026-09-08T16-51-10Z.md, bound to test c8a2ea41 and intake
e9a51598 (full hashes in that review). This explicitly supersedes the preservation
requirement for that exact replacement only; no further deletion, weakening,
path expansion or broad verification is authorized.

Independent claim121013 confirms all four reviewed files unchanged and accepts
the provider in review-2026-09-08T17-06-12Z.md. The pending scope disposition is
resolved. W120763 may execute; W120425 retains its other provider and proof gates.
