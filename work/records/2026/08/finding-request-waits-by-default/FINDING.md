# Finding: directed requests wait by default

## Observed — 2026-08-17

The v11 `say` carrier currently treats two facts as unrelated operations:

- `request=TEAM.KIND` creates a directed obligation; and
- `phase ... to=waiting wait=OBLIGATION` suspends the requesting Work.

That makes the common blocking request unsafe by default. A handler can ask
another endpoint for an answer while its own Work remains active and claimed,
even though no honest progress is possible until that answer arrives. The
sender has to remember the new obligation sequence and issue a second command;
an interruption between the two commits leaves misleading workflow state.

## Confirmed decision — 2026-08-17

**Approved by Slawomir.** A directed `request=` waits by default. The `say`
grammar gains a Boolean `wait=` operand whose effective default is `true` when
`request=` is present. `wait=false` is the explicit asynchronous override.

`include=` remains the ordinary non-blocking attention mechanism. A sender
who wants somebody to see context without owing an answer uses `include=`. A
sender who wants an answer but can continue independently uses
`request=... wait=false` deliberately.

### Atomic blocking form

For effective `wait=true`, one authority transaction must:

1. publish the Message;
2. create its one directed obligation;
3. move the selected `on=` Work to `waiting` on that exact obligation;
4. release the requesting actor's claim; and
5. record the effective `wait=true` value in authoritative event and operation
   evidence.

The Work's Current endpoint does not move. The request is input owed to the
current handler, not a transfer of ownership. When `respond`, `dispose`, or
`accept` terminally resolves that obligation, the exact waiter wakes through
the existing authority transition: its obligation wait is cleared and it
returns to `queued`. Other dependency gates may still leave it not ready.

Only the selected Work's resolved Current handler, holding that Work's active
claim, may perform the blocking form. A missing claim, another claimant, a
stale route resolution, or any failure in Message/obligation/wait/claim-release
processing refuses the whole transaction and leaves no partial publication.

### Explicit asynchronous form

For `wait=false`, `say` publishes the Message and creates the directed
obligation atomically, but does not change the Work's phase, wait condition,
Current endpoint, or claim. Existing Current-handler authorization for the
carrying request remains in force; the override does not grant outsiders
workflow authority.

`wait=` without `request=` is invalid. Omitted `wait=` and explicit
`wait=true` are the same effective operation. Effectively-once identity and
retry comparison use the effective Boolean value: an exact retry may spell the
default explicitly, while changing it to `false` under the same operation id
must fail closed.

## Acceptance boundary

- CLI help, strict grammar, command-mode assistance, JSON results, and Work
  Events expose the effective waiting choice without requiring inference from
  omission.
- Default and explicit-true requests atomically create the obligation, enter
  the exact-obligation wait, and release the actor's claim.
- `wait=false` preserves phase and claim while still creating an actionable
  obligation.
- `wait=` without `request=`, malformed Booleans, unclaimed blocking requests,
  and requests made against somebody else's claim refuse before mutation.
- `respond`, `dispose`, and both forms of `accept` wake the exact waiter once;
  unrelated obligations do not wake it.
- Operation replay, mismatch, concurrent claim/release, response races, and
  injected-failure tests prove all-or-nothing state and no duplicate Message,
  obligation, wake, or assignment episode.
- Canonical JSON and the TUI show the same phase, claimant, waiting condition,
  obligation, and event evidence after every form.

