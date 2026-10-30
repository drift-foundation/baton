# W338305 — bounded authoring shutdown and honest final outcomes

Author only inside this isolated v12 Job's private candidate, based on
fb48797903160aa764229d58f3a5beaf29648bfc. Read v12/DESIGN.md. This is one coupled
shutdown correction, not renewal, diagnostics UX or a general supervisor refactor.
No host edits, live verification providers/engines, token-policy increases or
candidate hot-patching of this Job's running manager. Framework source acquisition
and proposal publication belong to the runtime; do not issue Git mutations.

Confirmed defect: tools/authoring_enforcement.py supervise_process gives shutdown
cleanup_seconds but reserves min(12, cleanup_seconds/2) for its own final steps.
It kills/reaps the manager before RemoteGuard.stop reads the finished snapshot.
The real baseline in work/records/2026/09/finding-v12-single-implementation-proof/
baseline.py starts a new full cleanup_seconds window at line1293 after SIGTERM,
admission closure and accounting. child_main reaches Guard.stop only after baseline
returns. Thus cooperative cleanup can lose both workload and enforcement outcomes.
RemoteGuard.stop's timeout is not a waiting guarantee. Revalidate against your input.

Implement one propagated bounded shutdown allowance/deadline across this composition,
reserving accounting, guard stop/join and publication time. No new cleanup window
may exceed the remaining outer allowance. Bound potentially blocking steps themselves,
not only checks between them. Cooperative cleanup must publish honest outcomes before
cutoff; stalled cleanup/publication must end boundedly with attributable partial or
unknown evidence. Preserve total/provider/token limits, manager exclusivity, once-only
admission, cancellation fencing and exact-runtime/launch uncertainty holds. Confirmed
execution cessation/status must not acquire a new report-quality release gate.
Report presence, process death and expiry are not proof of runtime cessation or success.

The accepted seven-case diagnostic proved this failure with real processes and fake
engine/provider boundaries. A 4s cleanup allowance gave the manager about2s before
outer kill, while baseline's new4s window was still running. Blocked serving and
absent-writer/pending-cleanup cases lost both reports. A6s publication stall lost the
guard report; a0.01s control finished. Unknown engine state retained a revoked,
unreturned token even with reports. Pre-serving SIGTERM fenced admission; serving
SIGTERM raised; repeated cleanup SIGTERM deferred. Normal diagnostic return was an
orderly create refusal, not a successful authored workload.

Those historical diagnostic scripts are NOT delivered by this declared base.
Do not access host evidence or archive the old base to test your changed candidate.
Implement native reusable regressions importing the candidate controller and baseline.
Existing tests.manager.test_authoring_manager_guard replaces the baseline workload:
that suite alone cannot establish the full correction. Exercise real baseline,
controller, child_main, guard, admission, store and token paths with only external
engine/provider behavior simulated. Retain the original diagnostic unchanged.

## Verification contract

Create v12/python/tests/manager/test_authoring_shutdown_deadline.py with FastContract
and Composition unittest classes. These names are a test-entry contract, not an edit
allowlist. Choose necessary source/test paths and record them. Standing authority
permits test changes for the selected behavior; retain genuine defect coverage.

FastContract uses controlled clocks for deadline propagation, reserved finalization
time, no fresh window, original limit preservation and bounded-operation arguments.
The frozen30s formal gate runs FastContract plus existing OwnerLane, LateLaunch and
UnboundLaunch classes from test_authoring_enforcement. Missing classes, failures,
skips and timeout are non-acceptance. Gate fit is unmeasured at packet preparation.
Do not remove cases to manufacture a passing gate.

Composition must independently prove:

- Normal return and cancellation before serving, with no forbidden admission.
- Expiry during a blocked serving sweep and an absent writer with pending cleanup:
  cooperative ending publishes workload/enforcement outcomes before outer cutoff.
- Delayed and permanently stalled final publication, both before and beyond cutoff:
  bounded result with exact step/attempt attribution and honest unknowns.
- Unknown engine cessation and uncertain launch remain held; positive exact
  cessation/status releases execution ownership without waiting for output quality.
- Repeated signal during deferred cleanup; original total/provider/token limits;
  all spawned processes reaped and manager guard released without invented cessation.

Run the full new module plus existing test_authoring_enforcement and
test_authoring_manager_guard inside this same isolated authoring invocation as
supplemental verification, with a120s command ceiling and at most5s termination/reap
allowance. Use shortened test deadlines and real process/signal composition, not
900s wall waits. This suite is required even if the formal gate passes. The historical
40.302216334s matrix cannot fit unchanged in30s; supplemental verification is not an
extension of the runtime's formal verifier limit. Independent review must rerun the
candidate-native real-composition cases through a separately selected isolated v12
verification Job. No direct host fixture exception exists.

For both commands start at candidate root; change cwd to v12/python and explicitly
set Python import roots to its absolute cwd and cwd/src, including PYTHONPATH for
children. Derive the historical baseline location from the candidate root. Use
test-owned disk-backed temporary state, not a path or import inherited from the host.
Record commands, case counts, skips, durations and failures against exact candidate
bytes in a safe plain-text report without credentials or private transcripts.

## Completion and partial work

The host runs the unchanged accepted controller being corrected. Its token initially
lasts900s from acquisition, with no renewal caller. Provider3600/total4800/cleanup60
are ceilings, not promised useful time. One invocation, no automatic retry. Persist
candidate files and a concise continuation checkpoint early; prioritize the bounded
coupled correction and required evidence. Do not claim you can guarantee completion
inside the available token. Do not patch the running host or extend permission.

Return candidate provenance, changed paths/digests, actual tests, remaining obligations
and exact continuation if incomplete. A green fast gate alone is not acceptance.
Missing final reports may require later independent consumption after exact-runtime
cessation; neither expiry nor controller exit grants that proof. Preserve partial
work. Independent review remains in v11; no self-acceptance or automatic integration.
