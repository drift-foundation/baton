# Protocol 10 — bulk selection and recoverable Trash

**Status:** Slawomir identified the need and proposed multi-selection plus a
recoverable Trash on 2026-08-10. He subsequently ruled the familiar Gmail
pairing: `x` marks/unmarks and `#` moves the marked set to Trash. `A` selects
all eligible rows in the current filter. He then ruled that recoverability
must not expire through inaction: Trash remains restorable until an explicit
Empty Trash action. Marks are session-only intent, not persisted work. Because
lowercase `x` was already the damaged-content status glyph, he ruled that the
mark key keeps `x`, damaged content moves to `~`, quarantine keeps `X`, and a
regression must cover collisions across the complete status vocabulary. The
feature remains named Trash. Archive is reserved for a distinct future
"move selected to Archive" operation whose contents remain browsable/searchable
without Empty Trash semantics.

## Problem

The human console already has more than one hundred retained messages. A
one-row-at-a-time `x`, each with its own confirmation, makes ordinary cleanup
linear in mailbox history and turns the protocol-10 dismissal feature into a
chore. A mistaken bulk cleanup must also be recoverable.

Humans think of this as clearing completed work from a list, not as editing the
message state machine. The operation should therefore be fast, explicit, and
viewer-local.

## Recommended contract

### Selection

- `x` toggles the highlighted eligible row in a marked set. This replaces the
  earlier ruled use of lowercase `x` as the immediate one-row dismissal
  action; nothing moves to Trash merely because it was marked.
- After toggling, selection advances to the next visible row so repeated `x`
  keystrokes can mark a run without alternating with navigation. On the final
  row it remains there; it never wraps to the top or changes filters. Marking
  and unmarking use the same predictable advance.
- The displayed damaged-content glyph is `~`, not `x`; `X` remains the
  quarantined-state glyph. Selection and status must not reuse the same mark.
- `A` selects all eligible handled rows in the current participant/filter/view;
  a second action may clear that set. A bulk feature without select-all still
  requires one hundred keystrokes and does not solve the reported problem.
- Marks are keyed by stable row identity, never numeric position. Polling,
  arrivals, thread regrouping, and newest-first reorder cannot redirect them.
- Marks do not survive a console restart. They are uncommitted intent, unlike
  drafts, and reopening the console must not leave a forgotten bulk action
  armed.
- Changing filters must either preserve only still-visible identities with an
  explicit count or clear the set visibly; it must never act on hidden rows by
  surprise.
- Pending or claimed inbound obligations, queued/picked-up outbound work,
  unseen notices, and drafts are ineligible. Existing protocol-10 dismissal
  rules already forbid hiding live obligations; bulk selection cannot weaken
  that boundary.
- Seen notices and terminal handled messages are eligible. Drafts keep their
  separate destructive `D` flow.

### One bulk action

`#` acts on the marked set. With no marks it acts on the highlighted eligible
row, preserving the simple one-item path. This follows the familiar Gmail
shortcut, is deliberately harder to type accidentally than a plain letter,
and keeps selection (`x`) distinct from the recoverable Trash action. It is
called Trash rather than Delete because it is recoverable. `D` remains
exclusively the draft-discard action.

The confirmation is one status-line prompt:

```text
Move 83 handled messages and seen notices to Trash? y/N
```

`y`/`Y` confirms. `n`/`N`, Enter, and Esc decline. The default is No. The
authority changes the entire identity set in one transaction: all rows move or
none do. A missing, changed, or newly ineligible member fails closed with no
partial dismissal. The diagnostic names how many members became ineligible
and why, and offers to drop exactly those identities and retry the remaining
explicit set. The retry is still one atomic transaction; it never turns into
partial best-effort cleanup.

### Trash and undo

Trash is a per-participant view over durable dismissal state, not a rewrite of
the shared message:

- moving an item records who hid it and when;
- the item disappears from that participant's Messages view and appears in
  their Trash view;
- restore/undo removes the participant's dismissal and returns the item to its
  normal chronological/thread position;
- the UI should offer an immediate undo after a successful batch in addition
  to the Trash view.

Trash does not expire automatically. An item stays listed and restorable until
the participant explicitly chooses Empty Trash. Irreversible removal from the
participant's view must not happen merely because time passed or the console
was not opened. Empty Trash needs its own explicit selection, confirmation,
audit, and durable dismissal tombstone so an old message cannot reappear in
Messages.

Empty Trash does not silently delete the underlying authority message. It may
still be visible to another participant, anchor replies/threads, or be required
by audit. Physical authority-content retention and GC are a separate policy
with separate referential-integrity criteria; Trash must not smuggle in that
destructive contract.

## Protocol shape

Extend the ruled per-participant dismissal authority rather than add a local
TUI file. The authority needs enough durable state to distinguish recoverable
Trash from the compact post-window tombstone, plus timestamps and batch audit.
The exact schema may be one row whose state advances or an active Trash row
plus an immutable dismissal record, but `doctor` must reconcile it and no
second source of truth may exist beside SQLite.

The batch API accepts explicit message identities and the participant. It does
not accept a query such as “all handled,” because evaluating a query inside a
later transaction can select rows the human never saw. The TUI resolves the
visible set first; the authority validates and commits those exact identities.

## Required regressions

- toggle one, several, and all eligible rows;
- select-all on a filtered participant conversation;
- live obligations, unseen notices, and drafts remain unselectable;
- identity preservation across arrival, reorder, thread regrouping, and poll;
- filter change cannot act on an invisible stale mark;
- `x` only toggles selection and never moves a row by itself;
- each `x` advances to the next visible row, with no wrap at the end;
- no normal, exceptional, notice, damaged-content, draft, or ASCII-fallback
  status glyph collides with an action key whose meaning could mislead or harm;
- `#` without marks retains the one-row Trash behavior;
- one confirmation for the whole batch, default No;
- all-or-nothing transaction when any identity is missing or ineligible;
- viewer-local Trash visibility with no effect on another participant;
- restore at any later time before explicit Empty Trash;
- immediate undo of the last batch;
- marks are absent after restart;
- explicit Empty Trash is separately confirmed and audited;
- its durable tombstone prevents reappearance without deleting shared history;
- shared message, parts, replies, receipts, dispositions, and audit remain
  intact;
- `doctor` detects dismissal/Trash/tombstone inconsistencies;
- narrow packaged TUI shows marked count and confirmation on one status line.
