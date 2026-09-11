# Extend standalone stage composition coverage

Ledger Work: W103950

## Approved follow-up — 2026-09-06

Slawomir approved separating the bounded first working composition from its
expanded hardening matrix. This record receives coverage formerly required by
W103083 under `finding-shared-stage-assembly/FINDING.md` in the standalone
multi-job pipeline dossier. The bounded composition retains safety invariants,
one lifecycle with correction, and representative restart/refusal evidence.

This independent follow-up is intended for baton.tuner after the production
assembly interface stabilizes. It must not block closure of W103083, its
composition provider, or the first two-Job proof. Keep it outside their
containment tree so an open deferred follow-up does not prevent parent closure.

Scope: add complementary deterministic coverage for restart before/after
remaining driver cutpoints, construction failure cleanup, status/log locations
across exceptional and held states, and interrupted integration remaining held
for manual recovery. First inventory accepted tests and remove duplicate cases
from this plan. Deliver one small coverage slice per handoff; if several slices
remain, create separately owned leaves rather than one giant test run.

Ownership: baton.tuner may add
`v12/python/tests/tools/test_stage_execution_hardening.py` and evidence in this
dossier. K retains `tools/stage_execution.py`, `tools/single_worker.py`, their
existing test files, and `tools/parallel_test.py` while assembly is underway.
Run the new suite directly; registry changes require a later explicit handoff.
Any production defect discovered is filed separately with its reproduction;
this test-only assignment does not authorize production edits or weakening
existing assertions. No live provider, Docker run, or exhaustive test battery
is needed to establish the test plan.

Scheduling: park until the bounded composition is available and dispatch is
explicitly authorized. Later independent test-only work may proceed alongside
the live proof when file ownership and runtime resources do not overlap.

## Scheduling correction — 2026-09-06 — Slawomir

The preceding instruction to park and await separate scheduling approval is
superseded. This work is approved and waits on a concrete prerequisite, so
use a dependency: W103950 waits on W103083. Remove the deliberate park and
retain the baton.tune route. Completion of the assembly should automatically
make the hardening eligible for tuner without another human unpark step.
The dependency runs from assembly to hardening only; hardening still does
not gate the initial composition or two-Job proof. If an independently accepted
interface leaf becomes available earlier, revise the dependency to that leaf.

## Recorded production replay defect — 2026-09-07 — baton.codex

**Confirmed by source during W103083 review:** after freeze_checkpoint fences
the implementation writer, the assembly cannot recompose its writable mount.
The review driver independently refuses the revoked writer in _own_writer
before replay, so a mount-only correction is insufficient. Public line,
checkpoint and writer readers already expose the durable identity chain.

Separate production follow-up W110783 owns diagnosis/correction and is parked
for this named restart-hardening pass. This record remains test-only; no
production edits are authorized here. Preserve an explicit first-pass limit
if its representative restart uses another cutpoint. Evidence and exact
review: `../finding-v12-standalone-multi-job-pipeline/findings/finding-standalone-stage-composition/findings/finding-shared-stage-assembly/review-2026-09-07T14-12-42Z.md`.

## 2026-09-09 — Revalidated first coverage slice — baton.tuner

The accepted assembly now includes publication replay, committed-handoff
reconstruction, interrupted integration holds and cold read-only completion.
Those cases are excluded from this slice; see `evidence/claim-129808/INVENTORY.md`.
Select construction failure cleanup through the actual `operations_from`
boundary. Existing cleanup tests directly construct fake workers that expose
`release`; concrete `single_worker._Operations` exposes `close` instead.
Whether the composer closes those actual workers is an unproved seam.

Only the new hardening test file and this dossier are owned by this claim.
Production correction remains separate. The earlier replay-defect entry is
historical: later fenced-ending and reconstruction coverage requires reviewer
reconciliation of its still-parked follow-up, not an assumed new defect here.

## 2026-09-09T18:09:01.079107+00:00 — first slice independently assessed

review-2026-09-09T18-09-01Z.md accepts the exact test-only contribution as valid red defect
evidence. W129838 owns the independently confirmed concrete-close correction;
W129844 owns the disjoint status/locator join. This supersedes pending first-slice
assessment, not full hardening acceptance. Retain the red assertion and existing
accepted evidence; no current resource leak or broad green claim. W110783 remains
parked pending precise historical reconciliation at final parent review.
