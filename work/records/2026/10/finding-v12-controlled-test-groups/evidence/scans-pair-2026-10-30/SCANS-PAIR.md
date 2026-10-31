# The two isolated scans failures (CLOSURE-CHECKLIST next handoff), 2026-10-30

K (Claude, interactive copilot as baton.prompt) under the owner-held claim
E384905 (arrangement B); K holds no claim. Owner snapshot commit observed
before this batch: fdc66b4f (2026-10-30 12:16 -0600, "WIP: checkpoint v12
test repairs, inventory coverage and closure plan"). Files:
`tests/manager/test_source_boundary.py`, `tests/manager/test_text_sweep.py`
(CANDIDATE-SHA256.txt). No product change.

## 1. `TheWorkspaceIsStorageAndScratchIsBounded.test_the_runtime_gets_exactly_the_declared_bounded_scratch`

Before: the composed `--tmpfs` list has three entries (`/tmp` 64m, `/dev/shm`
16m, `/run/baton/logs` 16m); the test expected only `SCRATCH_MOUNTS` (two).

Contract traced: `oci.RESTRICTIONS` composes the scratch table and then ONE
more tmpfs at `attempt_logs.LEGACY_LOG_TARGET`, 16 MiB, "W202663 (owner
2026-09-21T05:54:40Z): the legacy room spelling is a disposable decoy ... NOT
part of `SCRATCH_MOUNTS`: that table feeds the declared workspace-capacity
floor, and this decoy is nobody's capacity". The accepted tests agree:
`test_oci` counts `len(SCRATCH_MOUNTS) + 1` tmpfs words in the 51-word vector;
`test_verifier_topology` pins `SCRATCH_MOUNTS` at exactly the two legacy
mounts, the floor at 80 MiB and "the total tmpfs is ninety-six mebibytes:
80 MiB of scratch plus the existing 16 MiB legacy log decoy". So the mismatch
is the TEST: it predates the decoy (last touched 2026-09-26, decoy accepted
2026-09-21 in a later-integrated cut).

Fix: the expectation names the whole composed posture exactly -- the scratch
table's entries, each with its size and flags, PLUS the decoy with its exact
spelling and 16m -- and asserts the decoy's target is not in `SCRATCH_MOUNTS`.
The noexec/nosuid/nodev loop still covers every entry. Nothing is omitted
from comparison.

After: `just test-one` on the class plus `test_oci` and
`test_verifier_topology` (scratch-mount-classes.log): 221 OK (1 optional
skip, the >64 MiB workspace proof) in 1.6 s.

## 2. `EveryExportedOperationRefusesUnstorableText.test_the_table_names_every_exported_callable`

Before: twelve exported callables absent from the table:
`abandoned_gate_discharge_of`, `abandonment_cleanup_of`, `cleanup_of`,
`deadline_cleanup_of`, `deadline_of`, `observe_deadline`, `advance_deadline`,
`discharge_abandoned_quiescence_gate`, `discharge_deadline_quiescence_gate`,
`fence_pre_attach_abandonment`, `writer_for_attempt`, `review_for_attempt`
(intake 6, deadlines 5 incl. two shared names, review_cycles 2).

Fix: twelve rows, each naming its real text operands (attempt id; retention
policy digest; abandonment reason), driven through the real export with the
no-op port/agent/adapter doubles the neighbouring rows use. No exemption.

After: `just test-one tests.manager.test_text_sweep` (text-sweep.log): 3 OK;
the completeness case holds and the surrogate sweep refuses every spoiled
operand with a ContractRefusal, none escaping and none accepted.
text-sweep-boundaries.txt records the boundary each of the 19 new operands
refuses at, by label: `a runtime attempt id` (12), `a retention policy
digest` (3), `a deadline retention policy digest` (3), `an abandonment
reason` (1) -- all `integrity/schema` "carries text that is not encodable",
i.e. the owner the operand belongs to, before any port, agent or adapter is
consulted.

## Scans status

Not rerun in this slice (checklist: run scans once after the six remaining
repairs). Expected from the before/after: 8 → 6 failing ids, the six named in
the checklist's stages A–C.
