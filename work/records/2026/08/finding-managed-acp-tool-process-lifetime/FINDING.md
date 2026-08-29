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

## Approver ruling — confirmed 2026-08-28 UTC

Slawomir approved the proposed exact boundary in full. V11 may require an
explicit positive `turnTimeoutMs`, use one PID-namespace process domain per
delivered turn, and restart the agent process while preserving the ACP session
identity. Every settlement path must positively terminate and reap that
domain before the lane is reused. A deadline is terminal for the delivery and
is reported as the existing correlated `failed/cause=internal`; inability to
prove teardown keeps the lane fenced and fails closed. The timeout duration
remains explicit deployment policy rather than a repository-selected default.

This ruling resolves the preceding open approval question. Implementation may
now proceed through the existing `baton.impl` handoff and must retain the
service-context PID-namespace preflight and focused teardown matrix.

## Acceptance

- Focused regressions prove tool deadline, settlement teardown, cancellation,
  bridge/session restart, self-matching watcher, and runaway-test cases.
- Runtime state distinguishes a progressing turn from a live bridge with a
  stalled turn.
- Exact scoped recovery leaves unrelated services and active assignments
  untouched.
- The invariant is carried into the v12 Worker Manager/container contract.

## Implementation clarifications — 2026-08-28

Recorded by `baton.claude` at implementation. Neither changes the approved
boundary; both answer a question the ruling left to the implementer, and are
written here rather than only in code so a later reader does not have to
re-derive them.

**Confirmed placement: the launcher requirement is enforced by the
DEPLOYMENT's verifier, not by the bridge.** The ruling says a direct
executable or a mount-only bubblewrap command is not an accepted managed
configuration. The bridge cannot be the enforcer of that: it is deliberately
ACP-generic, it does not parse `agent.command`, and teaching it to recognise
one deployment's launcher vocabulary would undo the property that makes it
agent-generic at all. The staged set's own `verify.mjs` refuses a launcher
missing `--unshare-pid` or `--die-with-parent` and requires the preflight to
ship beside it; the bridge owns killing the domain owner and proving its exit,
which is what it can actually observe.

**Confirmed: the two teardown windows are supervisor constants, not a fifth
operator operand.** `TERM_GRACE_MS` (500) and `KILL_PROOF_MS` (5000) bound how
long this supervisor waits for a signal it sent. They describe the supervisor
rather than a deployment's workload, which is exactly the distinction that
makes `turnTimeoutMs` deployment policy — so adding a fourth and fifth timeout
to the configuration surface would be spending an operator decision on
something the operator has no information about.

**Confirmed, on acceptance clause 2** ("runtime state distinguishes a
progressing turn from a live bridge with a stalled turn"): that distinction is
now made by the deadline rather than by a new state. A stalled turn stops
being reported as `working` within the configured bound and becomes correlated
`failed/cause=internal`, which is what the ruling directed; a separate
`stalled` state would rename a terminal timeout without adding information.

**Open, unchanged:** whether an operator-visible PRE-deadline warning is
wanted. The ruling said a separate `stalled` state/cause is unnecessary unless
the approver wants one, and nothing here adds it.

## 2026-08-28 — second independent review

**Confirmed P0:** the strengthened descendant preflight still admits a
vacuous trial. Its `pgrep -f` tokens occur in the outer `bwrap` argv, so that
owner satisfies both descendant-start checks. A stand-in `bwrap` that only
sleeps — no namespace and no descendants — makes the unchanged preflight exit
0 and claim successful reaping. Exact evidence and the retained reproduction
path are in `review-2026-08-28T07-51-55Z.md`.

**Confirmed P1:** the fresh-cutover rollback restores a launcher backup that
only the reconciliation path creates. A mandatory preflight failure on the
fresh path therefore cannot execute the documented rollback as written.

**Confirmed P1:** failure correlation is retained across the per-envelope
action loop and assigned only after replacement setup succeeds. A later
action's early failure can therefore be published with the preceding action's
Work, episode, and session.

## 2026-08-28 — third independent review

**Confirmed P1:** the corrected preflight snapshots heartbeat counts before
terminating the domain. A final write between that snapshot and teardown is
later called evidence of a surviving process even after every exact PID in the
recorded descendant tree is proved absent. A stand-in that recursively reaps
the complete tree is refused with exit 6. Exact evidence and the retained
reproduction path are in `review-2026-08-28T08-41-58Z.md`.

## Operator service-context acceptance — 2026-08-28

**Observed:** Slawomir ran the exact staged `preflight-process-domain.sh` from
the normal host shell, outside the managed agent sandbox. The probe created the
PID namespace, ran an escaped `setsid` descendant and a busy descendant inside
it, observed six host processes below the owner, removed all of them when the
owner exited, and proved an unrelated control remained alive.

**Confirmed:** The mandatory service-context gate passed. The shell's trailing
`Killed` diagnostic is the probe's EXIT cleanup terminating its own unrelated
control after that survival assertion, not a failed invariant. Exact output is
preserved in
`evidence/operator-service-context-preflight-2026-08-28.txt`.
