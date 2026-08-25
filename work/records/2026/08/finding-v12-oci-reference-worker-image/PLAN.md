# Plan: OCI reference worker image

1. [implementation-ready] Pin the image/base digest, scripted M2 agent and
   posture-specific worker entry contract.
2. [pending] Implement `baton-worker` and its protected framed channel.
3. [pending] Build consent and execution postures without session promotion or
   pre-mounted future capability.
4. [pending] Add reproducibility, inspection, protocol and isolation tests.
5. [pending] Record focused evidence and return for independent review.

## Review correction — 2026-08-24

Status: **changes requested** in
`review-2026-08-24T23-52-15Z.md`.

1. [done — decision 2026-08-25] Use closed per-operation request/response
   shapes with exact posture-session and one-use operation identity on every
   frame; exclusive stdio alone is not the binding. Cancellation remains the
   manager's explicit runtime control path, not clean EOF or a worker-entry
   operation.
2. [required] Own each whole request before dispatch so assignment, workspace,
   output or other unexpected material cannot enter a consent process through
   a frame.
3. [required] Convert invalid/missing startup posture into one bounded fault
   frame and non-zero exit without an uncaught traceback.
4. [required] Define and exercise an actual cancellation path; an input stream
   empty from its first byte is not evidence of intentional cancellation.
5. [required] Build the pinned-platform image, record/prove reproducible image
   identity, inspect actual config/layers/filesystem posture, run real consent
   and execution negative cases and prove every engine resource absent.
6. [verification] Make the additive reviewer cases green, then run focused,
   image/container, full source and locked installed-layout gates before
   returning for independent review.

## Re-review correction — 2026-08-25

Status: **changes requested** in
`review-2026-08-25T03-09-10Z.md`.

1. [done] Refuse unexpected consent-frame material and frame invalid startup
   posture without a traceback; the two first-round additive cases are green.
2. [required] Implement the approved common protocol/session/operation
   identity, exact per-operation request sets, one-use replay fence, echoed
   response identity, and closed answer-object validation.
3. [done — decision 2026-08-25] Latch entrypoint/bootstrap faults while the
   framing loop remains operable, read exactly one bounded request identity
   envelope, and return the normal correlated fault before non-zero exit;
   never dispatch the task or expose capability after the fault. If the
   framing loop itself cannot start, the Worker Manager settles its already
   identified operation as `worker_start_failed`; do not add an uncorrelated
   worker response shape.
4. [required] Replace initial clean EOF as the cancellation fixture with the
   manager's real container stop/termination path and observable settlement.
5. [required] Deliver a self-cleaning pinned-platform build/inspect/run gate;
   record the actual image/config/layer/filesystem/user/capability posture and
   real consent/execution negative evidence.
6. [verification] Run the corrected focused and image/container gates, then
   the full source and locked installed-layout gates before re-review.
