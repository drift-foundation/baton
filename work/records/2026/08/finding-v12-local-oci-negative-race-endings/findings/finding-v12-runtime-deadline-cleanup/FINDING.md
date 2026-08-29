# Define and compose a runtime deadline into exact cleanup

## Discovery and parent

Discovered while implementing W32382 under
`work/records/2026/08/finding-v12-local-oci-negative-race-endings/`.
The parent requires a manager-owned execution deadline to traverse the same
exact runtime/provider cleanup crossing as every other ending.

## Confirmed gap

The current tree has no runtime-attempt deadline. The only durable
`deadline_at` lives in `worker_manager/interrogation.py` and belongs to one
probe/inquiry operation. Its `timed-out` outcome deliberately records only
that the manager stopped waiting: it is not cancellation, is non-terminal, and
permits a later answer. Reusing that field or prose to destroy an execution
runtime would reverse its confirmed meaning.

No current production owner defines who observes an execution deadline, what
clock/generation fixes it, how it orders authority fencing/assignment ending,
or how it enters exact runtime and provider cleanup. The missing product
meaning must be ruled before tests or implementation guess it.

## Required boundary

- Define one explicit runtime-attempt deadline identity, owner, clock and
  durable observation. Do not borrow interrogation timeout semantics.
- Rule whether expiry requests cancellation/fencing or another typed authority
  ending, and preserve that authority-before-destruction ordering.
- Compose expiry through existing exact reconciliation, output custody as
  applicable, force-removal, positive absence, credential/launch teardown and
  cleanup settlement.
- Bind the operation to exact assignment generation, attempt, deadline policy
  generation and observed instant. Restart/retry replays the first accepted
  deadline fact; stale generations and changed policies fail closed.
- Preserve unrelated attempts and forbid replacement while deadline cleanup is
  pending, uncertain or provider-unsettled.

## Open decision

An approver must confirm the runtime deadline's authority meaning before
implementation: the existing interrogation `timed-out` observation cannot
authorize runtime destruction, while silently treating expiry as worker
`cancelled` would attribute a worker disposition the worker never produced.

## Acceptance

- The confirmed deadline rule is pinned here before production edits.
- A real Docker runtime crosses the deadline while present, the authority
  ending/fence occurs first, and the exact container is force-removed with
  positive absence and provider settlement before lane reuse.
- A deadline cannot be caller-backdated, moved by retry, applied to a stale
  generation, or confused with an interrogation timeout.
- Restart, concurrent observation, already-quiescent runtime, uncertain engine
  observation, provider-unresolved retry and sibling preservation are covered.
- Required Docker evidence fails rather than skips; daemon-free policy and
  replay tests remain warning-clean.
