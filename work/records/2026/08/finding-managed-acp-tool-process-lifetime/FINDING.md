# Bound managed ACP tool-process lifetime

Date: 2026-08-27

## Finding

**Observed:** `baton.claude` reported `working` on W26328 while the authority
still showed that Work queued and unclaimed. The Claude ACP log had not changed
for roughly 55 minutes even though the runtime lease continued to refresh.
Process inspection found five tool groups left below the same Claude agent:
four polling shells had survived for roughly 36 hours, and one Python unittest
had consumed one CPU continuously for roughly 34 hours.

**Confirmed:** several polling commands can never finish because their
`pgrep -cf PATTERN` predicates match the polling shell's own command line. The
unittest and its pipeline also have no effective external deadline. All five
groups outlived multiple later managed turns. The process-level readiness probe
therefore proves only that the ACP bridge is alive; it does not prove that the
current model turn is progressing or that prior tool children were reaped.

**Impact:** one stale model turn occupies the only `baton.claude` delivery
lane before claim while ready implementation Work accumulates. The runtime
projection misleadingly says `working`, and one runaway test consumes a full
core indefinitely.

## Confirmed boundary

- Every managed tool execution has a bounded lifetime owned outside the model.
- Tool process groups are correlated with their turn and assignment attempt.
- Turn completion, cancellation, failure, session replacement, and managed
  shutdown terminate and reap every surviving correlated process group.
- A self-reporting or process-alive lease is not sufficient progress evidence.
  The adapter publishes a typed stalled/failed condition when a bounded turn
  makes no progress, without inventing a Work claim.
- Recovery may terminate only the enumerated stale tool groups after validating
  their PID, parent, process group, session, age, and command. It must not kill
  the Baton authority, unrelated services, or a valid claimed worker.
- V12 worker containers inherit the same invariant at the container boundary:
  destroying an attempt also destroys every process in its execution scope.

## Immediate recovery evidence

The validated stale process groups are `1433251`, `1433308`, `1433501`,
`1433741`, and pipeline group `1460997`, all descendants of Claude agent PID
`1099234`. The ACP bridge itself is PID `1099205` and is deliberately excluded
from the recovery target.

## Reviewer revalidation — 2026-08-28

**Observed:** the five groups were still alive when reviewer research began.
Each polling shell was its own process-group and session leader, and the
runaway pipeline also occupied a different session from the bridge. Signalling
the infrastructure-owned bridge group therefore could not reach them. A later
snapshot found all five absent while the bridge, bubblewrap launcher, ACP
adapter, and Claude retained the same PIDs. The reviewer issued no signal;
recovery happened externally by an unknown mechanism and does not establish a
lifecycle guarantee. Exact snapshots are in
`evidence/reviewer-research-2026-08-28.md`.

**Confirmed:** the deployed and source `AcpAgentSession` implementations match
at the defect boundary. Setup calls have `setupTimeoutMs`, but prompt turns
deliberately have no deadline. `stop()` signals only the direct configured
child, `runBridge()` retains a healthy agent across successful turns, and the
runtime publisher renews the unchanged `working` state while the bridge is
alive. The deployed bubblewrap launcher creates a mount namespace but not a
PID namespace and has no parent-death boundary.

**Confirmed:** ACP session continuity does not require process continuity. The
bridge already retains one session id across replacement agent processes and
loads it again. A fresh process domain per delivered turn is therefore
compatible with the existing no-rotation contract.

**Confirmed:** ACP activity is not a safe deadline reset. A legitimate tool
may be silent, while an infinite but chatty tool can keep producing updates.
The externally enforceable limit is a wall-clock turn deadline; streamed
updates remain diagnostics and never extend it.

## Proposed exact boundary — awaiting approver ruling

- Add mandatory positive-integer `turnTimeoutMs` deployment configuration,
  with no inferred default. The bridge races each prompt against that fixed
  wall-clock bound.
- One fully initialized agent process domain serves at most one delivered
  readiness turn. On every success, failure, timeout, cancellation, session
  replacement, and bridge shutdown, terminate the domain and positively await
  its exit before reporting settlement or starting another.
- The current Claude deployment's outer owner becomes bubblewrap with
  `--unshare-pid` and `--die-with-parent` in addition to its mount boundary.
  A service-context preflight is mandatory; the managed reviewer sandbox could
  not create even the existing nested bubblewrap namespace and therefore
  cannot certify host support from inside this turn.
- Deadline is terminal for that delivery: after teardown, publish the existing
  typed runtime state `failed/cause=internal` with bounded deadline detail and
  retain `(work, episode, session)` correlation. Do not invent a Work claim or
  add a new runtime state merely to rename a terminal timeout.
- If domain teardown cannot be proved, fail closed: retain the readiness key,
  keep the lane fenced, publish no `idle`, and start no replacement process.
- V12 applies the same rule at its stronger native boundary: force-remove the
  exact execution container and observe positive absence before clean
  settlement or replacement. W6636 owns that destroy/settlement crossing.

**Open:** the approver must confirm that v11 may mandate the PID-namespace
launcher and process-per-turn restart, and that existing
`failed/cause=internal` is the intended timeout classification. The duration
itself remains deployment policy via the mandatory operand rather than a
repository-selected operational guess.

## Acceptance

- Focused regressions prove tool deadline, settlement teardown, cancellation,
  bridge/session restart, self-matching watcher, and runaway-test cases.
- Runtime state distinguishes a progressing turn from a live bridge with a
  stalled turn.
- Exact scoped recovery leaves unrelated services and active assignments
  untouched.
- The invariant is carried into the v12 Worker Manager/container contract.
