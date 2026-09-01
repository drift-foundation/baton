# Finalize quiescent v12 assignments before cleanup

Ledger Work: W61984

## Finding

W52821 run5b ended with the worker disposition `unable` and Docker reporting
the runtime quiescent. The operator retained the proposal, but the Worker
Manager refused cleanup because `attempt-w52821-run5b` remained the live
assignment for `baton.claude` generation 1. No container remained, while the
authority still represented the assignment as authorized to execute.

This is a lifecycle-finalization gap. Quiescence proves that the observed
runtime is not executing; it does not by itself decide whether work is
accepted, rejected or recoverable. Nevertheless, an operator must have a
public, journaled transition that ends or fences the exact assignment before
cleanup. Leaving the claim live consumes capacity and makes a later worker
look concurrent with an execution that no longer exists.

The evidence is retained at `/tmp/w52821/run5/evidence.json`. It records
`worker_disposition=unable`, ordered quiescence, no cleanup receipt, no review
pass, and the exact live-assignment refusal.

## Confirmed scheduling decision — 2026-09-01

This defect is separate from W52821's credential-delivery implementation. Do
not hide it with raw authority-store mutation or an operator-side cleanup
workaround. Address it later in its own isolated v12 container.

The correction must not automatically accept, discard or import worker output.
It ends or fences execution authority while preserving custody and exposing
the unresolved result for an operator decision. Every transition is scoped to
the exact attempt, participant, generation and runtime evidence and remains
idempotent across retries or manager restart.

## Acceptance

- A terminal worker disposition plus proved runtime quiescence can move the
  exact live assignment to an explicit ended or fenced state through the
  public Worker Manager boundary.
- The transition releases participant capacity without declaring the proposal
  accepted, trustworthy or disposable.
- Retained output, logs and custody locators remain available for operator
  inspection after assignment finalization.
- Cleanup requires the finalized exact assignment and cannot affect another
  generation, participant or runtime.
- Repeated finalization and crash-recovery attempts are idempotent and preserve
  a durable explanation of who or what ended the assignment.
- The correction is produced by a fresh isolated v12 attempt and independently
  reviewed before import.

## Reviewer revalidation — 2026-09-01

### Observed

The retained run5b evidence is internally consistent with the current code.
The manager had already recorded `worker_disposition=unable`, the exact
runtime was positively `quiescent`, output was frozen and intake had placed the
proposal in custody. Independent verification failed, so the operator neither
made a retention decision nor passed the assignment. Its unconditional ending
then reached `authorize_cleanup`, which correctly refused because the exact
assignment was still live. Detailed evidence and symbols are in
`evidence/research-2026-09-01/README.md`.

**Clarification of the opening account:** “No container remained” is too
strong if read as positive absence. The evidence carries the exact runtime in
`observed_after.candidates` as `quiescent` and still lists its mounts. What is
confirmed is that no worker was running. The v12 specification explicitly says
a quiescent runtime may still exist and only `destroyed` is positive absence;
all finalization, cleanup and gate decisions below use that stronger reading.

The focused current-tree baseline passes two cases: the dogfood failure case
pins that an unverified candidate is not passed and remains live, while the
manager cancellation case pins fence-agent-stop ordering for a cancellation
that initiates quiescence. Both assertions are true today; together they expose
the unowned interval between them.

### Confirmed

The assignment-state-machine specification already decides the authority
effect. Cancellation fences and ends the exact generation atomically, frees
the participant's global claim slot immediately, and leaves the Work blocked
behind `runtime-quiescence:<generation>`. A quiescent runtime is not absent and
cannot satisfy that gate. Recoverable output remains pending until explicit
trusted intake/retention disposition; cleanup never decides authority state.

The existing `request_cancellation` is still required and must retain its
current semantics for a running attempt: fence first, then ask the agent, then
stop the runtime. It is not the new already-quiescent operation. Reusing it
unchanged after the worker conversation has ended would add two unnecessary
external acts and can fault after the authority fence even though the manager
already holds the quiescence fact.

### Proposed

Add one public, journaled **already-quiescent assignment finalization**
operation. It takes an attempt id and bounded operator reason, derives rather
than accepts the fixed assignment, runtime identity, terminal disposition and
quiescence state, and calls the existing exact authority fence. It makes no
agent or runtime call and no output, intake, retention, review, approval,
integration or cleanup decision.

The durable manager operation binds the exact attempt, four-part assignment,
runtime identity, recorded terminal disposition, reason and distinct authority
operation id. A crash or restart reissues that one authority act; an exact
retry replays, and changed operands collide. No new attempt-table axis is
needed: the manager journal records why finalization was requested, while the
authority journal is authoritative for whether the assignment ended.

Expose this as an explicit dogfood recovery/finalization mode over the retained
evidence and grants. Do not silently finalize every failed ordinary run. The
v12 specification says an `unable` result remains for an explicit
pass/release/close decision, and changing that into automatic cancellation is
a separate policy decision, not an implementation detail.

### Required explicit supersession

If the proposed explicit mode is approved, it supersedes only one clause in
`EveryPostStartBranchEntersTheEnding.
test_failed_independent_verification_never_passes_to_review`: after an operator
invokes finalization, the assignment must no longer remain live. The stronger
and still-current rule is that failed verification never earns a review pass.
The ordinary attempt may remain live until the explicit decision is made.

### Open approver decisions

1. Approve or reject a distinct already-quiescent manager finalization
   operation that reuses the authority cancellation effect but performs no
   agent/runtime stop and no artifact decision.
2. Approve the explicit operator mode rather than automatic finalization in
   `_ended_however`; an automatic policy would contradict the current “explicit
   decision after inability” specification.
3. Confirm the operation accepts every recorded terminal worker disposition,
   not only `unable`. A `completed` worker whose independent verification
   fails reaches the same lifecycle state, while `none` still refuses.

## Confirmed finalization policy — 2026-09-01

The three approver decisions above are accepted. Add a distinct public
already-quiescent assignment-finalization operation. It is an explicit
operator action, never an automatic consequence of a worker stopping or
returning a terminal disposition. The operation accepts any recorded terminal
worker disposition, including `completed` and `unable`, and refuses when the
disposition is still `none`.

The operation fences the exact live assignment and releases the participant's
claim slot without contacting the agent or runtime. It makes no decision about
whether retained output is accepted, rejected, trustworthy, importable or
disposable. Custody and logs remain available for inspection; the Work remains
subject to its runtime-quiescence gate, and cleanup still requires positive
runtime absence. Exact retries are idempotent and changed attempt, assignment,
generation, runtime or reason operands fail closed.

### Scheduling and overlap

Implementation remains a fresh isolated v12 attempt. W52821 is now accepted
and closed at checkpoint `7456ac385ad76c5d8092dfadf3abe9bcf07f00a5`.
Implementation must still revalidate W61599's overlapping `attempts.py`, schema
and dogfood-operator changes against the current tree. This ruling authorizes
no raw authority/store workaround.
