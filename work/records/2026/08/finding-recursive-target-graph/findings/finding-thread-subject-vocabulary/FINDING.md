# Finding: replace Discussion with subject-bearing Thread

## Observed

The first human v11 TUI trial exposed two related problems. `Discussion` is a
long label in a space-constrained console, and the current entity has no
subject with which to distinguish several conversations attached to one Work.
Using the Work title is insufficient because a Work may carry several
conversations and one conversation may be labelled with several Work items.

## Confirmed v11 model

**Confirmed by Slawomir during the trial; this supersedes `Discussion` as the
canonical v11 entity name.** Use:

`Work -> Threads -> Messages`

- A Work is the tracked activity.
- A Thread is one subject-oriented conversation and may be labelled with one
  or more Work items.
- A Thread has a required concise subject.
- A Message has a body, author, timestamp, references, and any message
  operators; replies do not repeat or replace the Thread subject.
- The compact TUI pane label is `Msgs`, and a compact selector such as `T1/3`
  identifies which distinct Thread is displayed.

Rename the canonical protocol/schema/JSON/CLI/TUI vocabulary coherently rather
than retaining `Discussion` internally and `Thread` only as presentation
terminology. This is a clean v11 development change: no trial-authority
migration is promised. The immutable `6d1b944` distribution and its authority
remain unchanged.

The live trial tracks this as v11 Work `26de18dd-W31` with Thread-equivalent
prototype discussion `26de18dd-D31`.

## Confirmed trial replacement

**Confirmed by Slawomir.** Do not migrate the `6d1b944` trial authority. The
repository findings are the durable stories and specification. After the next
immutable application distribution is built, initialize a fresh coordination
authority and recreate only the representative Work needed for the next human
test drive.

**Operational disposition.** Slawomir moved the old coordination home to
`/home/sl/baton-v11.6d1b944`; it remains available only for completing and
reviewing the W31 handoff. `/home/sl/baton-v11` is intentionally absent and is
reserved for `init` by the next immutable application distribution.

## Unified Work-title and Thread-subject contract

**Confirmed by Slawomir during W31 review.** Work titles and Thread subjects
use the same normalization and validation contract: non-empty after trimming,
single-line, and at most 80 UTF-8 bytes. Work creation stores the one normalized
value as both the Work title and its automatically born Thread subject.

This supersedes the old behavior in which Work titles could contain newlines
or exceed the Thread-subject bound. Do not add a redundant born-Thread subject
argument and do not silently truncate. The normalized subject participates in
the effectively-once fingerprint before operation lookup.
