# Preserve opaque worker metadata through sealing

Ledger Work: W105574. Created 2026-09-06 by baton.prompt for Slawomir.

## Confirmed defect and approved disposition

The validated completion envelope contains worker metadata, but sealing replaces
it with `{}`. Real result retention/load-back and exact replay preserve that loss.
This violates worker-control SPEC sections 7.3 and 8.4. Restoring opaque carriage
does not make worker claims manager-authored or trusted.

Independent evidence and adjacent reproduction:
`work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-standalone-stage-composition/findings/finding-proposal-manifest-producer/review-2026-09-06T18-49-39Z.md`.

Slawomir approved this separate first-demonstration prerequisite on 2026-09-06.
baton.tuner owns only these implementation paths plus this dossier:

- `v12/python/src/baton_v12/worker_manager/sealing.py`
- Additive cases in `v12/python/tests/manager/test_sealing.py`.

Carry metadata from the already validated, assignment-bound envelope by declared
output NAME, never list position. Retain it in the committed result and replay
that account. Keep measured integrity, custody and assignment members manager-owned.
Preserve existing unsuccessful/no-envelope behavior. Do not interpret namespaces,
add arbitrary custody reads, change the schema, or reopen mutable completion
output on committed replay. Existing assertion or expected-behavior changes beyond
additive coverage require separate approval.

Focused acceptance: two distinguishable opaque namespaces with reordered outputs;
optional-output behavior; actual result retention/load-back; replay with original
completion changed or unavailable. Preserve wrong-assignment, malformed-envelope,
missing-required-output and no-secret refusals. Prove the positive carrier path
first, then focused regressions, without an unrelated broad test campaign.
Do not edit the concrete-worker or integration paths owned by other providers.

## Revalidation — 2026-09-06, baton.tuner

Confirmed under claim event 105607: `sealing.py` still matches the independent
review's SHA-256 `52dc096e4edac36ffd8b787d7bf5ec8e4654582d1b9a72cee64cf6ee21540276`.
Both assigned code/test paths were clean in the inspected working-tree baseline;
unrelated existing changes remain outside this assignment. `_completion_envelope`
already validates the envelope and compares the exact assignment and declarations
before custody changes, but its returned document is discarded. Both output
branches substitute empty metadata. Committed replay precedes this read.

The frozen worker-control SPEC sections 7.3 and 8.4 still require opaque carriage,
including explicit missing-optional answers. The approved correction remains
current: index validated output metadata by name and carry it in both result
branches; retain empty metadata when no envelope exists. Namespace contents do
not supply any manager-owned result member. Existing validation and replay order
remain the boundaries; no additional completion retention is needed.

## Independent review — 2026-09-06, baton.codex

Accepted the bounded two-path correction in
`review-2026-09-06T23-42-49Z.md`, with exact candidate fingerprints and an
audit of all seven additive tests. No blocking findings. The implementation
preserves worker metadata by output name through both sealed output branches
and existing committed replay while retaining manager ownership of measured
integrity, custody and assignment facts. No existing assertion was changed.

The recorded positive baseline failure, seven focused passes and full 65-test
sealing run satisfy the approved verification boundary; review did not repeat
those commands. This signs off the opaque carrier only. Concrete proposal-head
production and retained proposal-manifest composition remain separate scope.
Recommended next action: owner acceptance and satisfying closure.

## Owner acceptance — 2026-09-07 — baton.prompt for Slawomir

Slawomir accepted satisfying closure after the clean independent review
`review-2026-09-06T23-42-49Z.md`. Both implementation-file SHA-256 values were
rechecked and still match that review. The seven additive cases and complete
65-test sealing result are accepted as recorded, without duplicate reruns.
This accepts the opaque carrier only, not the proposal-head producer or composer.
No Git operation is authorized by this acceptance.
