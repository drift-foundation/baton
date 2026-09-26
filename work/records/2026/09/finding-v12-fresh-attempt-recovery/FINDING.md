# W266337 — V12 micro-stage 3: failed Job to successful fresh attempt

Own dossier, bound in claim 269137 as thread T266337 directs ("Bind own dossier at
start"), before any implementation work.

## Scope, as selected

Owner 269130 and thread T266337: through supported interfaces FAIL one small
disposable Job, SETTLE its resources, then complete a FRESH isolated attempt with
correct effects and result attribution. Real affected machinery with a
deterministic provider and an accurately labelled controlled adapter. ONE bounded
runnable command with explicit pass/fail evidence. Minimal demonstrated fixes
only. Reuse accepted stages 1 (W266329) and 2 (W266336).

EXPLICITLY NOT IN SCOPE, and the thread says so: no comprehensive planning loop,
no broad suites, no live providers, no deployed-store access or cleanup, no
version-control mutation, no preserved-run recovery, and NO claim that two-Job
adoption passes. The final recovery packet and the unmet R3/R4/R5 requirements
stay outstanding.

## Preserve

Unknown-outcome holds stay as stages 1 and 2 left them: a pending or unknown
submission keeps its reservation, and nothing here clears an unknown by
assertion. Stage 2's release gate and stage 1's reservation ordering are
preconditions of this stage, not things it may relax.

## Cross-references

- W257624 `work/records/2026/09/finding-v12-failed-run-resource-hold/` — the
  2026-09-25 short-transaction/fenced-lease ruling and the lease preparation.
- W266329 `work/records/2026/09/finding-v12-reserve-before-launch/` — accepted
  stage 1: the reservation is committed before the launch.
- W266336 `work/records/2026/09/finding-v12-delayed-launch-cancellation/` —
  accepted stage 2: a pending submitter keeps the resource; release follows the
  submitter returning plus runtime accounting.

## 2026-09-25T21:28:53Z — independent stage-3 correction

Confirmed by baton.rvpc under claim 269180: the five supplied cases pass, but
exercise review-correction episodes with fixture-written completed attempts and
frozen outputs. They do not execute a failed Job, settle its runtime resources,
or execute the successful fresh attempt. The assertion that this is complete
stage-3 evidence is superseded by the independent changes-requested disposition
in `review-2026-09-25T21-28-53Z.md`; the useful narrower correction-loop evidence
and author disclosure remain preserved. Current next step is in PLAN.md.

Operational finding: PLAN.md was absent and unreadable at review start; the
reviewer created the bounded continuation checkpoint. Return to implementation
under existing authority, without an additional owner gate. No product defect
is inferred solely from this missing proof, and stages 1/2 remain accepted.

## 2026-09-25T21:36:31Z — resource schedule proved; result acceptance remains

Confirmed under reviewer claim 269244: the sixth case exercises controlled
abandonment, exact runtime cleanup, lane exclusion/release and a fresh runtime
start. This supersedes the earlier finding that resource settlement was entirely
absent. Successful fresh Job/result acceptance remains unproved: the test records
worker completion directly and leaves the freeze identity mismatch unresolved.
See `review-2026-09-25T21-36-31Z.md`.

Correcting the local fixture identity set is ordinary authorized test work under
existing scope and standing policy. The handoff's proposed owner-selection gate
for that change does not apply. Continue directly to implementation, preserving
narrower passing evidence and unknown holds. No live execution is selected.

## 2026-09-25T21:48:53Z — output freeze reached using a still-live fenced generation

Confirmed under review claim 269320: the new candidate reaches request_freeze
with a manifest derived from workspace bytes, superseding the prior absence of
output acceptance coverage. Using delivered() resolves the earlier prefix issue;
no validator change or separate identity rewrite is required.

The composed proof is still invalid as recovery evidence: old and fresh attempts
both bind generation 1, and its fake cancellation reports fenced without ending
that live assignment. The independent saved probe ends it and observes the real
stale-assignment/ended refusal with no frozen successor output. See
`review-2026-09-25T21-48-53Z.md` and `review_fenced_generation_20260925.py`.
Product liveness refusal works in this probe; no product defect is asserted.

Continue under existing authority with faithful fence/gate settlement and a new
live assignment generation, carrying the same Job/recovery identity chain into
accepted artifact assertions. PLAN records the exact checkpoint. Preserve prior
resource/output progress, immutable reviewer evidence and unknown holds.

## 2026-09-25T21:56:23Z — generation corrected; gate discharge still absent

Review claim269376 confirms generation2 and stored accepted-artifact assertions,
plus stale-generation refusal. This supersedes the prior same-generation defect
for candidate93a4d8bd. The old FenceProbe remains historical evidence and is not
a current acceptance gate; no owner decision is needed to stop expecting its old
candidate-specific refusal.

Public abandoned_gate_discharge_of returns None after the current success case.
The fake resets Work queued without the supported discharge operation; actual
recovery requires that receipt. Follow review-2026-09-25T21-56-23Z.md and PLAN:
exercise discharge_abandoned_quiescence_gate and retain its matching receipt
before successor admission, with faithful fake gate state and the same recovery
identity chain. This continues the prior gate-settlement correction, without
additional scope or owner approval. Product defect not established.

## 2026-09-25T22:18:41Z — gate settlement accepted; bounded Job composition clarified

Review269513 confirms the real discharge receipt, replay, refusal before discharge
and generation2 accepted output for candidate39c7d102. This supersedes the previous
missing-gate finding. Nine tests pass independently. These are accepted bounded
worker-manager facts, not yet complete Job recovery acceptance.

restore_abandoned_correction requires a writer based on a checkpoint, as the
author's applicability probe and source establish. Clarification: the prior round
can be explicit fixture setup using accepted helpers; the tested failure,
restoration, Job episode replacement and successor result must share the same
identity chain and exercise supported transitions. No full prior-round runtime
replay or comprehensive lifecycle loop is required. Thus no new owner selection
is needed solely for this applicability boundary. Follow the four-step bounded
milestone in review-2026-09-25T22-18-41Z.md and current PLAN. Stage3 stays open.

## 2026-09-26T00:26:46Z — Job recovery accepted; successor ending premature

Review claim269933 confirms candidate0392e8e now composes the failed correction,
restoration and episode replacement on one Job/line chain, then runs a fresh
generation3 attempt with attributed frozen output and intake. This supersedes
the previous absence of that recovery composition.

Stage3 completion remains unproved: the candidate directly settles its ending
after intake while cleanup is pending, the successor still holds its lane and
the line remains writing at the old checkpoint. The preserved observation probe
confirms pending_endings is empty despite those outstanding acts. The journal
records the caller's completion assertion; it does not perform those acts.
The handoff's characterization of this attempt's checkpoint/fence as only later
round business is superseded by this review's source-backed correction.

Follow `review-2026-09-26T00-26-46Z.md`: finish this successor's supported ending
and applicable discharge/routing before settling it. No later full review loop,
new owner gate or production defect is inferred. Accepted recovery evidence,
unknown holds and broader W257624 gaps remain preserved.

## 2026-09-26T00:56:56Z — bounded stage 3 independently accepted

Confirmed under claim270195: candidate164a06ad completes the successor's supported
implementation ending, fenced routing, cleanup-bound gate discharge and only
then its Job-ending settlement. This explicitly supersedes the outstanding
premature-settlement finding in review-2026-09-26T00-26-46Z.md. Independent focused
verification:12 cases OK0.319s. No product change or blocking finding remains for
the selected deterministic micro-stage.

Exact evidence and limits: `review-2026-09-26T00-56-56Z.md`. Real manager/Job
operations run against declared controlled engine, authority, profile and
publication seams. The successor's implementation ending is complete; no whole
two-stage Job terminal, later review verdict, real authority admission, live run
or two-Job adoption is claimed. Prior setup, unknown holds and W257624's broader
outstanding requirements retain their classifications. Accepted delivery goes
to owner; current checkpoint is in PLAN.md.
