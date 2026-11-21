# W385454 — explicit fixture target permissions

## Confirmed defect and selected correction — 2026-11-21

Owner requested the next step after M385452 independently confirmed ambient-umask-dependent compatibility failures. Evidence: work/records/2026/11/finding-v12-worker-declared-failure-status/evidence/native-attempt-be4fbac0-recovery/umask-probe/. On pristine 7ac02c7f and frozen W385424 bytes, the two TheRealObservationReaderReachesTheView cases pass under 002 and fail under 022/077; captured product refusal names missing group write/traversal on the fixture canonical target.

Bounded outcome: the affected fixtures explicitly establish the target permissions required by their integration scenario. Preserve product posture checks and negative refusal coverage. No worker-wide umask change, broad fixture cleanup or unrelated repairs. Implementer chooses necessary test paths and records reasons. W385424 and W385427 accepted/retained candidate bytes remain immutable; corrections compose later as a distinct reviewed delta.

Verification: exactly the two owner-approved compatibility cases under 002, 022 and 077 with new confined disposable Git repositories, existing guard and logged operations/targets; no mutation of owner checkout or existing repositories. Use focused deterministic checks for any changed fixture behavior. No live models/engine, instance change, host import or Git mutation beyond that narrow fixture exception. Independent review required.
