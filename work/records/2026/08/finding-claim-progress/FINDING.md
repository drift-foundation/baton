# Append-only claim progress

Protocol 10. **Not implemented in the current stage.**

## The problem

A claim is either held or disposed of. Between those two states the holder is
opaque: a sender watching `[P]` cannot tell working from wedged, and the only
honest thing the queue can say is "someone took this".

## Contract

The lifecycle is UNCHANGED: `pending -> claimed -> completed|closed`. Progress
is an APPEND-ONLY STREAM attached to a claim, not a mutable working state on
the message. That distinction is the whole design:

- a mutable state would be a second thing to keep consistent with the claim,
  and the first inconsistency would be silent;
- an append-only stream cannot contradict the claim, only describe it.

Each progress update carries a timestamp and an optional short note. It reports
work performed on THIS claim. `blocked` is not a claim phase: the live trial
showed that a participant can have several runnable findings while questions
about later findings are pending, and may become blocked only when one of
those questions reaches the critical path.

**An update neither disposes of, extends, nor recovers a claim.** Progress is
not a heartbeat that keeps ownership alive; recovery stays exactly as it is.

## What the UI may say, and what it must not

Project the LATEST update and its AGE:

    remote is working · updated 3m ago — running integration tests

When updates stop, say so and nothing more:

    last update 47 minutes ago

The console must NOT assert current liveness from a stale update. An update is
evidence that something was true once, not that it is true now.

The full sequence is retained for audit.

## Blocked is a targeted event, not a claim phase or mood

A blocker is an explicit append-only event in the SQLite authority. It names
the blocked participant and the participant/audience able to unblock them,
plus a timestamp, the concrete action needed, and references. It may reference
a claim, but it does not require one: the blocked work may be a repository
finding rather than one Baton claim.

It is HIGH PRIORITY and may be atomic with a directed message:

- append the targeted blocker event, AND
- publish its linked directed blocker message to the participant identified
  as able to unblock it,

in one operation. The blocker uses ordinary claim/reply/close semantics, so it
is actionable and terminally dispositioned like anything else. Its reply stays
linked to the blocker and any referenced claim/thread.

**No automatic unblock and no automatic recovery.** A machine deciding that a
human's obstacle has cleared is a machine guessing. The blocked participant
explicitly resumes/cancels the blocker; the remote party cannot declare
someone else unblocked merely by replying or closing.

A blocker requires a non-empty responsible participant/audience and concrete
action needed. "Blocked" alone is not a report. It is visible only to the
blocked participant and the responsible endpoint(s), not as a global presence
status. Ordinary unanswered messages never create a blocker.

## Priority and queue order

Message priority enters the protocol with this. `wait` selects high-priority
pending messages before normal ones, FIFO within a priority class. The
fairness consequences belong in the protocol-10 review: a priority tier that
anyone can set is a tier that becomes meaningless.

## UI contract

- Unresolved high-priority rows sort ABOVE normal rows, FIFO within the tier.
- An explicit `[!]` marker plus a bold subject. Colour is an enhancement only:
  **never rely on colour or bold alone**, for the same reason the severity
  markers are text.
- The unresolved high-priority count appears in the status bar.
- Elevation persists while pending or claimed, and is REMOVED after
  reply/close -- the row stays in history with its terminal status. A resolved
  emergency that still shouts is how people learn to ignore the marker.

## Convention, when the verb exists

Publish progress immediately after claiming. For a long-running task, publish
progress at least every five minutes until reply or close. Publish a targeted
blocker immediately when genuinely unable to proceed, never merely because a
normal question remains unanswered and never at the next interval.

Belongs in `AGENTS-MAILBOX-PROTO.md` under `## Conventions`, stating what
happens when it is ignored: the sender cannot distinguish working from wedged,
and will eventually ask -- which is the cost the convention exists to avoid.
