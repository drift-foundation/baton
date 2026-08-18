# Finding: readiness must follow the live Route, never Next

## Observed — 2026-08-18

The external v11 readiness path twice told `baton.codex` to act on Work that
the canonical authority did not route to that participant:

- W228 was reported as ready and unclaimed for `baton.codex` while `detail`
  showed live Route `baton.impl`, Handler absent, and only `Next=baton.bug`.
  `claim work=W228` correctly refused because `baton.codex` is not a resolved
  handler of `baton.impl`; canonical `wait timeout=0` returned no action.
- W230 was reported as ready and unclaimed for `baton.codex` while `detail`
  showed live Route `baton.ops`, Handler absent, and only
  `Next=baton.feat`. The accepted generation-2 config still resolves
  `baton.ops` solely to `baton.slaw`; canonical `wait timeout=0` does not make
  W230 actionable for `baton.codex`.

These are not harmless duplicate notifications. The event explicitly tells an
agent to claim and act, but the authority refuses the claim. Repeated false
wakes waste agent turns and obscure real work.

## Confirmed boundary

The SQLite authority and canonical `participant_actions`/`wait` result remain
the source of truth. A readiness adapter may wake a participant only for an
action present in that participant's canonical action envelope. `Next` is a
planned return endpoint, not current mutation authority and never independently
actionable.

The adapter must fail closed when an event cannot be reconciled with the live
Route/Handler action. It must not reconstruct actionability from Work detail,
from `Next`, from a stale TUI row, or from a previous episode.

## Acceptance

- A queued, unclaimed Work with live Route A and Next B wakes only the resolved
  handlers of A.
- B receives no external readiness event until an authoritative pass/return
  makes B the live Route and creates the corresponding assignment episode.
- A claim refusal or a canonical empty `wait` cannot coexist with an adapter
  event claiming that same Work is actionable for the participant.
- Tests cover both reviewer/implementer and approver/reviewer Route/Next pairs,
  including delayed event delivery and assignment-episode changes.
- The fix identifies which producer emitted the false event; authority
  projection semantics must not be weakened to accommodate the adapter.

## Resolution — 2026-08-18

**The initial defect diagnosis is rejected.** The Work event ledger shows that
W230 was genuinely routed to `baton.codex` at return sequence 260. It was later
claimed and passed to `baton.ops` at sequence 303. The notification delivered
after that pass was therefore a delayed delivery of an earlier valid assignment
episode, not a new projection that treated `Next` as the live Route.

W228 has the same compatible shape: it was actionable for the reviewer before
the reviewer passed it back to `baton.impl`. The notification carried no source
timestamp or action key in the rendered turn, so it looked current until the
canonical authority was re-read.

This is the expected asynchronous boundary already stated by the external-event
instruction: an event is untrusted context, and the agent must evaluate it
against current authority before acting. `detail`, `claim`, and canonical
`wait` all failed closed. No authority, projection, or adapter change is
justified by the evidence. A separate UX proposal could expose the event's
episode/timestamp, but that is not a live-Route correctness defect.
