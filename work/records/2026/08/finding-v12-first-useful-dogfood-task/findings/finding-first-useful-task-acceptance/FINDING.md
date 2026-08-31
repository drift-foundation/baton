# Run and accept the first useful dogfood task

Work: W39364
Parent: W38956
Dependency: W39358

## Purpose

Use the accepted supervised operator path for the frozen low-risk repository
task and produce one independently inspected accept/reject result. This is the
milestone demonstration, not implementation of the platform beneath it.

## Frozen task

Use the parent record's `evidence/first-task.md` verbatim and stage only:

- `v12/spike/ping-pong/preflight.py`
- `v12/spike/ping-pong/trial.py`
- `v12/spike/ping-pong/test_harness.py`

The requested candidate adds direct coverage for `_observed_readable`'s exact
engine vector and distinct readable, unreadable, absent and nonzero endings.
The worker does not read credential bytes, call a real Docker daemon from the
test or change production probe behavior unless a test exposes a defect.

## Operator gates

The live run requires two explicit human/operator grants: the exact credential
source operand and the exact network posture. Neither is inferred from W17110
or selected by an implementer. The run does not start until both are supplied.

## Evidence and file ownership

This child owns its retained redacted transcript, collected proposal and
append-only review/acceptance evidence. The worker's candidate is external
output, not an edit to the canonical checkout. This child does not own the
operator, worker image or manager transport files.

## Acceptance

- The real Claude container receives the frozen task and measured read-only
  source subset through W39358 and returns one correlated declared proposal.
- The candidate tree, patch convenience, worker verification and manager
  output identities agree; no undeclared output is accepted.
- A reviewer independently diffs the candidate against the measured input and
  runs `python3 v12/spike/ping-pong/test_harness.py` outside the worker.
- The source subset, canonical checkout, Baton authority and unrelated host
  paths remain unchanged by the worker.
- Runtime absence, credential teardown and retained output custody are proven,
  or the attempt remains unresolved and cannot be accepted.
- The record names an explicit accept or reject disposition. Acceptance earns
  bounded supervised dogfooding only, not production readiness.

## 2026-08-30 — pre-run revalidation (`baton.codex`)

**Observed:** the frozen three-file delivery cannot run its own frozen
verification command. In an independently staged clean root,
`python3 v12/spike/ping-pong/test_harness.py` runs 26 cases but errors in 11
because `test_harness.py:402` reads the omitted sibling `trial.mjs`.

**Confirmed:** adding only `v12/spike/ping-pong/trial.mjs` to the read-only
delivery makes the unchanged command pass all 26 cases. This does not change
the objective, requested production boundary, candidate layout or verification
command. The reproduction is recorded in
`review-2026-08-30T21-10-33Z.md`; its temporary root is
`/tmp/w39364-review.8f4r5s` and is deliberately left for the operator under
managed-turn policy.

**Proposed, not yet authorized:** supersede the three-file frozen delivery
with the same list plus `v12/spike/ping-pong/trial.mjs`. A reviewer cannot
silently amend the parent's frozen task, and a live run against the current
subset would spend a provider turn on a verification known to be impossible.

**Open operator grants:** the exact `--credential-file` source path and the
exact network posture remain required. Neither is inferred, defaulted or
selected by the implementer/reviewer, and no live run starts before both are
supplied.

## 2026-08-30 — approver ruling: correct the subset and authorize one trial

The proposed four-file correction is approved. The current read-only delivery
is the prior three paths plus `v12/spike/ping-pong/trial.mjs`; the original
three-file list is superseded. The objective, prohibitions, candidate layout
and verification command remain unchanged.

The exact live-run grants are:

- credential source: `/run/baton/credentials/claude`;
- Docker network posture: `bridge`.

The credential path may be recorded as an operand; its content must not be
recorded. Both grants apply only to this supervised private-box attempt and do
not establish an inferred or deployment-wide default.

### Operational gate after the ruling

The selected credential source exists as a 509-byte regular file at mode
`0400`, owned by `nobody:nogroup`; `test -r` as the managed uid 1000 operator
returns false. No credential bytes were opened. Because the documented command
must open `--credential-file` before materializing its private delivery, the
live run remains stopped pending an exact readable source or an explicit
operator-owned permission correction. This Work will not copy, chmod or guess
credential material.

## 2026-08-30 — approver ruling: operator owns the credential source

Keep `/run/baton/credentials/claude` as the exact source operand and correct
its external ownership to `sl:sl` at mode `0400`. The operator runs as uid
1000 and must be able to read the nominated source before it can materialize
the attempt-scoped credential slot. The source is not mounted into the worker
under this ownership; the attempt-scoped slot owns the container-facing
delivery. This correction changes metadata only and never reads, rewrites or
records credential bytes.

### Operational verification

After the external correction, `/run/baton/credentials/claude` remains a
regular file at mode `0400`, is owned by `sl:sl`, and `test -r` succeeds as
the managed uid 1000 operator. No credential bytes were opened or recorded.
The credential-source gate is satisfied for the approved supervised attempt.

## 2026-08-31 — first live attempt: explicit rejection

Attempt `attempt-w39364-run2` completed the real supervised platform arc and
resolved cleanup, but its candidate is rejected. The worker disposition is
`unable`; the frozen manifest carries the same four file digests as the
measured input, `change.patch` is empty and independent derivation reports no
changed paths. The 26 passing harness cases are the unchanged baseline and
establish none of the requested new coverage.

Independent review confirms the canonical four source paths remain unmodified
and match the frozen candidate digests byte-for-byte. A fresh reconstruction
of those exact bytes passes the same 26 baseline cases. The actual custody
locator is absent because the operator hard-coded `discard-after-intake`, so
the required direct candidate diff/rerun is impossible and is not relabelled
performed.

The platform result is still material: the real provider conversation,
freeze, intake, retention decision, directory normalization, authority pass,
positive runtime absence, credential/launch teardown and execution-root
removal all completed with `resolved: true` and no unresolved reason. This
earns bounded supervised-path evidence only; it does not accept the task.

Two separately claimable operator follow-ups carry what the run discovered:

- W51473, `work/records/2026/08/finding-dogfood-retention-policy-disposition/`
  — [P0] make retention explicit and make intended retained cleanup resolve;
- W51476, `work/records/2026/08/finding-dogfood-human-contract-preflight/`
  — [P1] hold the whole human contract before any side effect.

Final independent record:
`review-2026-08-31T04-56-33Z.md`.
