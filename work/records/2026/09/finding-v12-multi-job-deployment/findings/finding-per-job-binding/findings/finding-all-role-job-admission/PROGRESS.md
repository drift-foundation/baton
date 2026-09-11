# Progress

Implementation entries belong to the participant making changes under its claim.

## claim130258 — every role validated before allocation

Evidence: `evidence/provider-130258.json`, `evidence/run-130258-module.log`.
Candidate, both mode 0664 relative to v12/python:

- tools/stage_execution.py `c4d6231838137e5fa66ee6768ab36d0bbcc112bb4327160d7f166e53c1127ba3`
- tests/tools/test_stage_execution.py `26ada3518b406937e492a4a8da9e63c351ac40a3e53bb3192ad6778ab12b4012`

The reviewed input was revalidated byte-identical before any edit.

**All-role compatibility.** `_job_workers` derives the servable workers for
every role by one rule, and `_disagreements` reads `single_worker._matches`'s
own six operands from the worker's held deployment rather than restating them.
`_job_eligibility` excludes everything outside that set, so only a Job-compatible
worker is reservable, and a stage with none is refused before reserve. The
implementation kind stays bound to the binding's `source_worker_id`; the
integration kind is scoped to the configured `integrator_participant`.

**Reconstruction.** `StageExecution.admit` is now spelled here instead of
delegating, and revalidates a recorded allocation against the same rule before
delegating. It reserves and releases nothing.

**Coherent fixture.** `manifest_for`, `role_worker` and `second_submission`
give each Job its own derived manifest, input digest and Work; both Jobs are
submitted in one submission. Five workers. The 12 inherited cases are unchanged
and still pass.

**A reported boundary, not a workaround.** A second Job's integration stage has
no worker that can serve it: a second integration worker under the same actor is
refused by `scheduler.own_pool` (one participant per worker — observed while
building the fixture, not inferred), and a second actor would be the
multi-integrator provider this Work may not imply. What this cut owes is that
the stage is refused *before* anything is reserved and the message says why.

203 tests pass — the 185 accepted plus this cut's 18.

**Budget, reported over rather than rounded down.** Increment 30s. Timed runs
28.752s; **two class iterations were run untimed** to list failing case names,
about 1.9s by the iterations bracketing them, recorded as uncertain. Total about
**30.65s — roughly 0.65s past the increment.** The overrun is the single
full-module regression run, which is what shows the source change did not
disturb the 185 accepted cases. Campaign carry: about 263.65s of the 400s cap,
with the prior 233s figure's own uncertainty unchanged and not reset.

## claim130926 — the second Job's integration is admitted, not reported

Evidence: `evidence/provider-130926.json`. Candidate, both mode 0664 relative
to v12/python:

- tools/stage_execution.py `5f8de12797d1c47d4926ea6b753e97043cc061b409b8c66ca3e459418f43c9b8`
- tests/tools/test_stage_execution.py `74d33e450020e9486a7f0f49c54a687a62c361760bef373c871db4bb1e66c641`

The reviewed input was revalidated byte-identical before any edit.

**[P1], and the reported boundary was the wrong boundary.** A second Job's
integration stage does not need a second integration worker. What it needs is
its own Work and its own submitted input, and those are operands rather than
capacity. `_served_deployment` answers the held deployment a worker actually
serves a Job's stage under: unchanged for every role but integration and for
the whole one-Job document, and for integration under a bound Job it is the
configured integrator's deployment carrying that Job's producer's
`input_manifest` — the same `source_worker_id` the binding already names and
`Integration.required_tests` already derives from. `_job_workers` reads it for
compatibility and `_integration_operations` composes the provider from it, so
admission and `single_worker._matches` cannot disagree about the document.

**The capacity is still one, and the case says so.** One pool worker, one
`integrator_participant`, one live allocation. With Job A's integration holding
the integrator, Job B's is refused by the SCHEDULER for capacity — its own
sentence about a reserved worker, not this assembly's about a worker that could
never serve the Job. No second integrator, actor, provider, driver or session.
Participant, principal, profile and policy digest are deliberately not derived.

**[P2], and none of it needed new permission.** The Job-store journal scan is
gone: `receipted` reads the canonical admit receipt at the Worker Manager
through `canonical_operation`/`receipt_of`, asking every episode of the stage
rather than only the live one, and every absence is paired with a positive
control. `allocated` reads `scheduler.allocation_of` on the attempt the live
episode names instead of `stage_allocations`. The integration cases go through
`StageExecution.admit` rather than calling `_job_workers`. The fault control
measures the REVIEW worker the incompatible review stage actually threatened.
Reconstruction is a real admission followed by a real recomposition over the
same stores with the two reviewers' Jobs exchanged — no fabricated rows.

**One thing the drive-based case deliberately does not assert.** Both of Job
B's stages name Job B's Work and the Authority allows one live offer per Work,
so job-b/review's canonical offer waits on the implementation stage's. That is
the Authority's rule, not this cut's, and it is recorded rather than asserted
around.

**Verification, and what was NOT verified.** 120 of the module's 203 tests
were run and all passed, covering every changed path. The remaining 83 —
terminal lifecycle, fencing, retention, replay — were NOT run: the full module
is 22.7s and the remaining allocation was 14.35s, and the PLAN forbids a
repeated full-module run here. Those classes reach the composed operations
through the one-binding path, which composes the identical single operations
object it always did; that is an argument, not a measurement, and it is the one
open verification gap in this handback.

**Budget, every run wall-timed.** 1.20 + 1.20 + 0.27 + 0.27 + 1.20 + 1.51 +
2.60 + 3.84 = **12.09s** of the 14.35s remaining. No untimed run and no new
uncertainty; the predecessor's ~1.9s and the 233s planning charge are retained
unchanged. Child total about 42.74s of the approved 45s; campaign carry about
275.74s of 400s. Reviewer probe carry 1.890647/5s untouched.

State: awaiting independent review through baton.bug.
