# Keep Handler activity and runtime visibility consistent

## Observed — 2026-08-20

The managed `baton.codex` dispatcher repeatedly failed to claim review Work
because of the known approval-policy defect. The foreground reviewer manually
polled and successfully claimed W76 through the same participant identity.

While that foreground review was actively running, the Jobs `Run` column
showed `idle`. That value was accurate only for the managed background Codex
Thread whose adapter owns the current runtime lease. The foreground execution
context performing the canonical Work did not publish runtime state, so one
participant identity represented two execution contexts while only one was
observable.

## Confirmed expectation

- `Handler` remains canonical workflow authority: W76 is held by
  `baton.codex` because that participant claimed it.
- `Run` remains adapter-reported runtime evidence and must not be fabricated
  from the claim.
- Nevertheless, a participant must not silently execute Work through a second
  context that its runtime lease does not describe. An operator must not see
  `Handler=baton.codex, Run=idle` while an unreported foreground context is
  actively executing that Work.
- A deliberate manual takeover must be explicit and atomic enough to prevent
  the managed context and foreground context from both acting as the same
  participant. It either supersedes/pauses the managed runtime lease and
  publishes its own context, or uses a distinct configured participant.
- Ending the takeover restores the managed path deliberately; a stale runtime
  publisher must fail closed rather than overwrite its replacement's state.

The known approval defect explains why manual fallback was needed, but fixing
automatic pickup does not make this ambiguity safe. Diagnostics and emergency
takeover still require an honest ownership model.

## Revalidation — 2026-08-20

**Confirmed:** the current projection is not fabricating the wrong runtime
state. `Handler=baton.codex, Run=idle` combines two independently authoritative
facts: the Work claim belongs to that participant, while the one published
runtime lease belongs to the managed background Thread and says it is idle.
The disagreement is exactly what the runtime projection was designed to expose.

**Confirmed:** runtime replacement already has a strong incarnation boundary.
`runtime-start` can supersede a lease explicitly, and later `runtime-state` or
`runtime-end` writes from the displaced incarnation fail closed through the
exact-incarnation gate.

**Confirmed limitation:** workflow mutations, including `claim`, authenticate
the participant only. They carry no runtime incarnation. Replacing the runtime
lease therefore does not prevent an already-running managed Thread from issuing
workflow mutations as the same participant. A TUI label or a lease replacement
alone cannot provide the promised exclusion.

**Proposed boundary:** do not implement a presentation-only correction. A
same-participant takeover needs an enforceable adapter/authority handshake:
the dispatcher proves its live incarnation immediately before delivery and
becomes undeliverable when superseded, while a foreground takeover publishes
its own incarnation. Any stronger guarantee that also fences an already-running
model turn requires workflow mutations to carry a runtime/assignment token and
belongs with the v12 Worker Manager contract. The lower-risk v11 alternative is
a distinct configured participant for manual execution, whose atomic Work claim
then prevents duplicate execution normally.

W415 changes this same runtime/dispatcher boundary and must settle before this
implementation is frozen; otherwise both Works review a moving authority and
adapter surface.

## Acceptance boundary

- One participant has at most one runtime context authorized to execute at a
  time, including foreground/manual operation.
- A manual takeover is visible in Teams and in the claimed Work's `Run` cell,
  with its adapter/session and start instant.
- The displaced managed runner cannot publish state or act under the
  superseded incarnation until explicitly restored.
- The takeover and restoration are journaled and do not themselves claim,
  release, pass, or close Work.
- Losing the foreground context derives `unknown` through the normal lease
  deadline; it never silently falls back to a still-running second context.
- Regressions cover managed-to-manual takeover, stale managed writes,
  restoration, crash/expiry, and distinct-participant operation.

## Confirmed minimal v11 disposition — 2026-08-20

The same-participant takeover boundary and the acceptance items immediately
above are superseded for v11. They would require substantially stronger
runtime fencing while v12 is already designing isolated, discardable workers
with assignment generations. V11 instead receives one narrow recovery rule:

- Any configured member of the Work's owning team may `release` a claim. The
  actor does not need to be a resolved handler of the Work's current Route.
- `expect=team.member` remains mandatory and is compared atomically with the
  recorded Handler. A stale or mistaken recovery refuses rather than releasing
  a different execution.
- A non-empty durable reason remains mandatory. Events retain the recovery
  actor, released Handler, reason, derived landing phase, and new assignment
  episode.
- A participant from another team remains unauthorized. Team participation,
  discussion, or an `@` obligation never grants recovery authority.
- `release` only clears the claim and derives `queued` or `block`; it does not
  reroute, close, revise, or otherwise act on the Work.
- Release cannot stop an external process. Operational guidance requires the
  recovering team member to stop or otherwise quiesce the displaced runner
  before releasing its claim.

This is an authorization correction over existing authority state and event
fields. It requires no new SQLite schema, runtime takeover protocol, lease
replacement, or TUI surface. Strong same-participant execution fencing is
deferred to v12.

### Revised acceptance boundary

- The recorded Handler may release its own claim as before.
- Another configured member of the owning team may force-release it with an
  exact `expect=` and durable reason even when that member is not a Route
  handler.
- An unrelated team member, wrong `expect=`, unclaimed Work, and terminal Work
  all fail closed.
- Existing scheduler landing, gate retargeting, assignment-episode minting,
  event evidence, and effectively-once retry behavior remain unchanged.
- Documentation states the required stop/quiesce-before-release sequence.
