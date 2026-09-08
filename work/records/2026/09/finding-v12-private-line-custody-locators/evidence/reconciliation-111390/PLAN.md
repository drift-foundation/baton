# Plan

Current owner disposition: corrected code checkpoint accepted, eight hashes
revalidated against review-corrected-manifest.json. Release the live-access
consumer to compose that code without waiting for full custody Work closure.
Remaining acceptance is composed runtime evidence and experiment disposition;
do not place the separate detach experiment on the confirmed-stop proof path.
This supersedes earlier full-closure sequencing, not outstanding proof requirements.

## Current state — 2026-09-07

Reviewer planning is complete; owner accepted this nine-path scope on 2026-09-07.
K implements only after the initial access code/interface checkpoint is reviewed.
Do not wait for full runtime-access acceptance: that follows custody composition.
FINDING preserves the
chronology and superseded requirements. Stable modes are 0664 files, 02775
directories and 0775 executables; confirmed shutdown precedes consumption.
No routine recursive permission switching or restrictive-file repair is proposed.

## Exact approved scope

Paths are relative to `baton`. Four production paths and five test paths are
approved. Tests add cases, fixture capabilities and helpers only; no existing
assertion or expected behavior may be weakened or replaced. Return for scope
review if additional changes are necessary.

| Path | Bounded change |
| --- | --- |
| `v12/python/src/baton_v12/worker_manager/review_cycles.py` | Resolve the consumption subject from durable writer, attempt, line, assignment/generation and object pin. Require positive quiescence and exclusive writer state; revalidate at use and before checkpoint/profile reads. Reuse lifecycle checks, no new scheduler state/schema. |
| `v12/python/src/baton_v12/worker_manager/workspaces.py` | Private bounded proof-only traversal/open check under the manager identity, including private metadata. Reuse no-follow/object/limit rules and access-provider helpers; no repair or custody receipt. |
| `v12/python/src/baton_v12/worker_manager/oci.py` | Bind line consumption to the lifecycle resolver and compare actual workspace/object and sibling custody provenance before use. Held roots are not authority. Preserve engine checks and ordinary behavior. |
| `v12/python/src/baton_v12/job_manager/review_driver.py` | Compose the gate after confirmed stop/disposition and before completion/seal reads. Type required capabilities before stop; keep publication before finalization and cleanup last. |
| `v12/python/tests/manager/test_review_cycles.py` | Add subject, generation, replacement, grant, retry/restart and checkpoint-use cases. |
| `v12/python/tests/manager/test_workspaces.py` | Add manager access, unchanged modes/bytes, bounded traversal and inaccessible-entry refusal cases. |
| `v12/python/tests/manager/test_oci.py` | Add root/custody cross-wiring refusal, revalidation, ordinary compatibility and retained-locator cases. |
| `v12/python/tests/job_manager/test_review_driver.py` | Add order, preflight, fail-before-read/publication, uncertain-runtime and reconstructed-adapter cases. Add fixture members if needed; preserve assertions. |
| `v12/python/tests/manager/test_private_line_access_engine.py` | After W105706 creates this module, add consumption/retention assertions to its shared serial proof; do not create a competing harness. |

`custody.py`, `intake.py`, `sealing.py`, worker/source profiles, schemas,
credentials and mount machinery are outside this edit set. Ordinary receipts
remain accurate about ordinary roots. No new public export, registry or dependency
inventory is presumed necessary; return for review if one is actually needed.

## Implementation sequence after owner acceptance

1. Revalidate the latest owner rulings and accepted access-provider candidate.
   Establish exclusive ownership of shared paths; preserve unrelated changes.
2. Compose a trusted lifecycle-to-adapter gate within the existing dependency
   direction. Resolve from control-store identities inside the operation, not
   caller host paths. A resolver capability may carry identities, but a cached
   path/proof cannot substitute for current durable state. Verify actual adapter
   roots and object identity at consuming use, including replaced/cross-wired
   mappings; do not merely prove that some other legitimate line is readable.
3. Positively stop/reconcile the exact runtime before manager traversal. Prove
   current generation, exclusive writer, line pin, actual roots and effective
   manager access. Recheck lifecycle/pin facts after the bounded filesystem proof.
   No engine call runs inside a store write transaction. Existing exclusivity
   persists through publication and the checkpoint transition.
4. Order: stop, disposition, actual-line access gate, completion/seal, correlation,
   intake/retention, live proposal publication, assignment fence/checkpoint, then
   ordinary cleanup. Checkpoint consumption still revalidates the same line.
   The access provider separately prepares manager-created checkpoint metadata
   for the next serial writer.
5. Wrong roots/pins/generation, denied traversal or uncertain runtime refuse before
   dependent reads/publication. Preserve the line and failure evidence; do not
   repair modes, claim custody success or admit another writer. Retries/restart
   re-observe runtime and resolve current subjects; neither ordinary receipts nor
   memory acknowledgements substitute. Preserve existing operation replay rather
   than silently redesigning it.
6. Verify retained sibling custody stays outside writable mounts and survives
   ordinary cleanup. Run focused checks and hand the exact candidate and evidence
   to independent review, then owner disposition.

## Focused verification

Add cases distinguishing the unused ordinary workspace from the actual line:
proof of the former cannot authorize the latter. Instrument the first completion
read, seal, profile read and publication so omitted/failed gates cannot pass.
Include another attempt/line, stale generation, replaced inode/symlink or parent,
wrong adapter roots, retry after refusal, restart/uncertain runtime and no second
writer. Assert unchanged modes/bytes and no traversal into outside symlink targets.
Reuse existing valid-source symlink rules; do not invent a new profile restriction.
Fixtures may model denied access, but the engine proof must observe effective
uid/gid access rather than rely on `os.access` or mode inspection.

Use W105706's approved dedicated group and exact-image boundary. A fixed-identity
runtime cooperatively writes nested payload and private Git metadata, then is
positively stopped. Exercise the real gate and sealing/checkpoint flow, read-only
review and next serial writer on the same line pin. Independently capture launched,
consumed, retained and cleaned paths; reopen retained bytes after ordinary cleanup.
A restrictive-entry case proves refusal, not repair. No model session, credential,
mount privilege or detach mechanism is required.

From `v12/python`, use `PYTHONPATH=src python3 -m unittest` for the four scoped
unit modules and the shared serial engine module under its approved deployment
boundary. Audit existing passing evidence before reruns; add checks for uncovered
risks. Record commands, counts, image/group observations and skips. Finish with
`git diff --check` and exact changed-path/byte review. Planning runs no runtime suite.

## Ownership and owner decision

W105706 owns initial provisioning, stable-mode launch compatibility and the engine
harness. Schedule its accepted changes first, then custody; serialize
`workspaces.py`, `review_cycles.py`, their tests and the shared engine module.
Serialize `oci.py` and its tests if the revised launch gate touches them too.
M106747 communicates the proposed boundary; provider acceptance is not presumed.
The planning claim owns no production path for editing.

W103068 remains blocked on W105982. W106673 is an open experimental child:
stop-path implementation need not await detach adoption, but parent closure waits
for child disposition. Busy after completion requires shutdown; failed/omitted/
uncertain detach cannot authorize consumption/reassignment, including after restart.
Production adoption requires independently reviewed proof and a new owner ruling.

Owner approved the proof-only correction, nine-path additive scope and access-first
serial ownership. Resolve exact group/image execution authority through the access provider.
Planning completion is not implementation sign-off or live runtime evidence.
Exceptional restrictive-file recovery remains separately scoped.

## Current actionable checkpoint — 2026-09-07 — independent review

The initial implementation state above is superseded by **changes requested**
in `review-2026-09-07T05-03-18Z.md`. Correct the checkpoint-use pin revalidation,
writer-assignment principal/participant binding and symlink entry ceiling inside
the accepted four production paths, with additive regressions in the already
approved test modules. Revalidate both initial use and checkpoint preparation
resume without requiring an already revoked checkpoint writer to become active.

Owner approved this bounded K correction on 2026-09-07. Supply the actual retained
job-driver test predecessor/diff for the remaining additive-only audit; report
missing evidence honestly if unavailable. Keep new helper APIs private (owner
selected this option; no public-surface expansion).
No broader test expectation edits or inventory expansion is authorized here.
Return corrected candidate hashes and evidence for independent review before
W105706 consumes the code checkpoint. Full runtime proof and the open experimental
child remain separate outstanding acceptance work.

## Current actionable checkpoint — corrected code signed off

The changes-requested checkpoint above is superseded by independent code sign-off
in review-2026-09-07T05-16-52Z.md. All three reproduced gaps and the additive-only
job-test byte audit are resolved; helpers remain private. Seven bounded reviewer
checks pass and the corrected manifest binds all eight candidate paths.

Next: baton.ops dispositions this reviewed code checkpoint and coordinates its
consumption by W105706. Full exact-image/dedicated-group runtime composition and
retained-result survival still need their approved proof. W106673 remains an open
experimental child; parent closure must await its disposition. Production uses
confirmed shutdown throughout. No repeat full test campaign or live execution is
authorized merely by this source sign-off.
