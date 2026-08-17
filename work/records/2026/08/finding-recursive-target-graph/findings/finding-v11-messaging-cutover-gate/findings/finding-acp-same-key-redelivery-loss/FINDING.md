# Finding: ACP readiness can lose a same-key return handoff

## Observation — 2026-08-17T15:03Z

W27 was delivered to `baton.claude`, claimed, implemented, and passed to
`baton.codex` for review. The reviewer claimed it, requested a second change,
and passed the same open Work back to `baton.impl` at authority event 48
(`2026-08-17T14:51:41Z`). At 15:03Z the canonical W27 detail still reported:

- `current: baton.impl` with handler `claude`;
- `phase: active`, `ready: true`, and no active claimant;
- `pickup: overdue`; and
- `last_change_seq: 48`.

The persistent Claude ACP bridge and its resumed agent process were alive, but
no new prompt reached the agent and no W27 claim followed. Restarting the
bridge would clear its volatile delivery memory and is an available stopgap,
but doing that before recording the defect would hide the failure every other
team would encounter.

## Confirmed mechanism

`DeliveryMemory` keys a delivered Work only by authority UUID, participant, and
the stable readiness `action_key` (`work:<work-id>`). It forgets that key only
when a later `wait` envelope is observed without it.

The review round completed quickly enough that W27 left Claude's actionable
set and returned to it between two bridge observations. From this bridge's
view, `work:92c57e47-W27` therefore never disappeared. `DeliveryMemory.sync()`
continued to treat the returned handoff as the already-delivered episode and
suppressed it indefinitely. The documented claim that an action is "forgotten
when it disappears" is insufficient when absence itself can occur wholly
between polls.

A related live observation is that an already-queued ACP prompt can arrive
after the Work has been claimed, changed, or passed elsewhere. Readiness is an
edge to re-evaluate, not authority to act from an old envelope.

## Product boundary

- Stable Work identity and a deliverable assignment episode are different
  identities. Reassigning the same Work to the same participant must create a
  new deliverable episode even if no consumer observed the intervening state.
- The canonical authority remains the source of truth. A queued prompt must be
  revalidated immediately before it starts an agent turn; stale readiness is
  dropped, not presented as current work.
- Whole-set suppression remains useful within one unchanged assignment
  episode. The correction must not create a prompt storm for an idle, stable
  actionable set.
- Authority UUID and participant isolation remain part of the delivery key.

## Proposed correction

Give each actionable Work assignment episode an authority-derived generation
that changes whenever the Work is handed off or otherwise becomes newly
actionable for a participant. Include that generation in the actionable
locator/key consumed by both external bridges. Do not manufacture a local
poll counter: process restarts and independent clients must agree on the same
episode identity.

Before an ACP prompt starts, refresh or validate that exact episode against the
authority. If it is no longer actionable for the configured participant, drop
it and continue without invoking the agent.

Acceptance must cover:

1. a Work delivered to A, handed to B, and handed back to A between A's polls
   is delivered to A exactly once for the new episode;
2. an unchanged episode returned by repeated waits is delivered only once;
3. a prompt queued from an old episode is refused before the agent turn after
   the Work is claimed, passed, closed, or superseded;
4. a failed agent turn leaves the current episode retryable;
5. bridge restart preserves level-triggered correctness without cross-authority
   or cross-participant delivery; and
6. Codex and ACP bridges consume the same canonical episode semantics rather
   than defining incompatible local heuristics.

## Immediate workaround

After this finding and its Work are durably recorded, restart the affected
participant's ACP bridge with its existing `load` configuration. This clears
the stale in-memory suppression and resumes the selected ACP session. It is a
recovery step for the live trial, not the product fix.

## Reviewer revalidation — 2026-08-17T15:06Z

The proposed correction still matches the current tree, with one important
schema boundary made explicit:

- `work.last_change_seq` is not an assignment episode. Claim, classification,
  ordinary phase, priority, and other visible Work edits may touch it. Using it
  would redeliver work for unrelated edits and could prompt the claimant again
  immediately after their own claim.
- The Work row therefore needs its own authority event sequence for the
  current actionable episode. Creation, pass/return, explicit claim release,
  a readiness transition from false to true, a condition-bound wake, and
  parked-to-queued resume mint a new episode. Claim, heartbeat, ordinary phase
  changes, and descriptive edits do not.
- Endpoint eligibility is also generation-relative. The projected Work action
  identity includes the accepted configuration generation so a participant
  removed and later restored between polls cannot remain suppressed. A config
  acceptance may conservatively redeliver otherwise unchanged actionable Work;
  configuration acceptance is rare and is an honest new resolution episode.
- The Work action key becomes an episode locator rather than just Work
  identity. The Work id remains in `action.work`; consumers never parse the
  key to recover identity.
- Before each queued agent prompt, the bridge performs an immediate read-only
  participant action projection and requires the exact episode key to remain
  present. This closes the observed long queue gap. A mutation can still win
  after that read and before claim; the agent's mandatory atomic claim remains
  the final authority and fails closed.

This is an honest projection-major and authority-schema change during the v11
trial. No compatibility alias or in-place authority migration is required.
