# Finding: pass requires the current Work claim

## Parent and discovery

`finding-active-work-claim` owns the invariant that execution begins only
after an atomic claim and that Handler names the exact participant executing
Work. This defect was exposed while using the `impl2` route to independently
review W1568 (`bcbb9dbf-W1568`).

## Observed — 2026-08-20

At event 2544, W1568 was unclaimed and rerouted to `baton.impl` through route
`impl2`, resolving to `baton.gemini`. Readiness successfully delivered that
assignment. Gemini inspected the implementation, ran `just test-v11`, and
reported runtime state `working` without ever issuing `claim work=W1568`.

The Work event journal contains no Gemini claim. Nevertheless, Gemini's
`pass work=W1568 to=baton.bug ...` committed as event 2555 using route-handler
authorization alone. The Work remained unclaimed throughout Gemini's turn.

This was not an accidental missing guard. The W171 reviews in
`finding-v11-messaging-cutover-gate/findings/finding-pass-is-work-event`
explicitly preserved the older unclaimed-pass behavior while correcting the
different case where a route peer passed underneath another participant's
active claim.

## Confirmed contradiction

The current active-work contract says that picking up Work means successfully
claiming it, and that implementation, review, tests, or other execution owned
by the route cannot begin before that claim. Allowing an eligible route handler
to pass unclaimed Work lets an agent complete the entire assignment lifecycle
without ever becoming Handler. Canonical state then says nobody worked while
runtime logs and filesystem effects say otherwise.

The existing behavior also makes `pass` and `reroute` overlap. Baton already
has a separately authorized operation for moving open unclaimed Work. `pass`
is the holder's handoff: it releases one exact claim while transferring the
route and recording the handoff comment.

## Decision — 2026-08-20

The previously approved unclaimed-pass behavior is **superseded**.

- `pass` requires an active claim held by the exact actor. Route eligibility
  without that claim grants no pass authority.
- An unclaimed `pass` refuses atomically, creates no event, changes no route,
  phase, Handler, Next, or assignment episode, and does not consume an
  operation id as a committed mutation.
- A different handler of the same route continues to refuse while somebody
  else owns the claim.
- The current claimant continues to release and transfer the Work atomically,
  preserving the threadless Work-event and durable `comment=` contract.
- Moving unclaimed Work is `reroute`, subject to its owning-team authority and
  durable `reason=`. Callers do not fake a claim merely to redirect a queue.
- Readiness adapters never claim or pass on behalf of a model.

This correction does not retroactively make Gemini W1568's Handler. Event 2555
remains evidence of the accepted old behavior and the defect that superseded
it.

## Acceptance

- Focused tests prove an eligible handler cannot pass ready unclaimed Work.
- The refusal is side-effect-free across Work state, events, episodes, retry
  identity, messages, and personal counters.
- Existing tests continue proving the exact claimant can pass and a route peer
  cannot pass underneath that claimant.
- `reroute` continues moving eligible unclaimed Work through owning-team
  authority and remains distinct from claimant handoff.
- CLI help, protocol documentation, Effective Baton guidance, and workflow
  stories no longer describe or imply unclaimed pass authority.
- The complete v11 gate passes before independent review.
