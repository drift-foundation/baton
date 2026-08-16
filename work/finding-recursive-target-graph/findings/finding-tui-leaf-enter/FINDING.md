# Finding: Enter on leaf Work opens an unexplained empty table

## Observed

In the first human v11 TUI trial, pressing `Enter` on a leaf Work drills into
its immediate children. Because the Work has no children, the resulting table
is empty. The screen does not explain that the Work is a leaf or tell the
operator how to reach its related discussion messages.

The messages are present: the current prototype exposes the focused Work and
its discussion set with `o`, then opens the selected discussion with `Enter`.
The operator naturally expected `Enter` on the Work row to expose that content.

## Clarification: `New` must be navigable

**Confirmed during the same trial.** A nonzero `New` counter is an actionable
navigation promise. The selected Work must offer an obvious direct route to
the discussions contributing to that count. Requiring the undiscoverable
sequence `Enter`, `o`, `Enter` after first showing an empty child table does
not satisfy that promise. The discussion view retains explicit `s` marking;
viewing alone must still not advance the participant's seen cursor.

## Confirmed finding boundary

This is a navigation/empty-state UX gap, not missing or damaged discussion
data. The correction must make leaf activation and its `New` messages useful
and discoverable while preserving deliberate child drill-down for Work that
has children. The exact interaction is left for focused UX review; do not
silently overload `Enter` without pinning its behavior and covering both leaf
and parent Work.

The immutable `6d1b944` trial remains unchanged. Until corrected, `o` opens
the selected Work's focused discussion view.

The live trial tracks this as v11 Work `26de18dd-W17` with discussion
`26de18dd-D17`.

## Confirmed split-pane navigation

**Confirmed by Slawomir during the trial.** Use a stacked split analogous to
the useful part of v10: the top pane remains the Work table and the bottom pane
shows messages for the Work highlighted above. `Enter` in the Work pane keeps
one stable meaning—drill into child Work—and `Tab` moves focus between Work
and messages. A leaf therefore never requires drilling into an empty table to
discover its communication.

Changing the highlighted Work updates the bottom preview but does not mark
anything seen. The bottom pane selects a discussion with personal `New` first
when one exists; multiple discussions remain distinct and explicitly
switchable rather than being merged. `s` remains the explicit operation that
advances the displayed discussion's seen cursor.

**Vocabulary supersession.** The later confirmed v11 vocabulary is
`Work -> Threads -> Messages`; read `discussion` in the split-pane ruling above
as `Thread`. The behavior is unchanged, and the compact bottom-pane label is
`Msgs`. See `../finding-thread-subject-vocabulary/FINDING.md`.

## Superseded navigation ruling — 2026-08-15

**The “Enter drills into child Work” and persistent main-screen message split
above are superseded by the later live-trial ruling.** See
`../finding-tui-message-browser/FINDING.md`. The main screen now shows a
bounded two-level Work tree; `Enter` always opens Work details, while a
separate visible `u` action unfolds/re-roots deeper containment. Threads and
Messages live in the Work detail view rather than occupying the main Work
list. Explicit seen semantics remain unchanged.
