# Finding: expose pending conversational pokes in the TUI

## Observation — 2026-08-18

During the first projection-12 deployment smoke, `baton.codex` sent a
conversational poke to every configured participant. The authority committed
poke 10 for `baton.slaw`, and the canonical `pokes` read showed it pending,
but Slawomir's TUI displayed no indication that he had been poked or owed a
response.

This is not a delivery-authority failure: the pending poke is present in the
SQLite authority and visible through the supported CLI. It is a TUI
actionability gap. A human participant cannot discover or answer the request
from the main interface without already knowing to inspect `pokes` manually.

## Confirmed requirement

- The TUI must visibly count and surface pending pokes addressed to the
  current participant.
- The cue must distinguish a poke from Work, Message obligations, and personal
  New counts; a poke carries no workflow authority.
- The participant must be able to inspect the friendly question and answer or
  cancel it through an appropriate TUI action without copying a sequence from
  raw JSON.
- Answered, cancelled, superseded, and timed-out pokes must stop appearing as
  owed action while remaining available through history.
- CLI and JSON semantics remain authoritative; this Work adds presentation
  and interaction, not another delivery mechanism.

## Acceptance boundary

Add focused TUI tests for the summary cue, pending-poke list/detail, response
flow, terminal disappearance, multiple pending pokes, and separation from
obligation/New counters. Preserve the existing protocol-12 poke behavior and
all non-TUI projections.
