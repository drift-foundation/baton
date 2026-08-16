# Finding: v11 TUI thread view is an unformatted message list

## Observed

The first human v11 TUI trial renders each discussion message as one clipped
line:

`#sequence team.author: body`

There is no wrapped body, visual separation between messages, compact metadata
header, new/seen cue, or readable treatment of references. The canonical data
is present, but the thread is substantially harder to scan and review than the
v10 message presentation.

## Confirmed requirement

The v11 TUI needs a deliberately formatted discussion reader, not a raw list.
It must remain borderless and space-efficient while making authorship,
chronology, message boundaries, wrapped body text, references, and personal
new state legible. Formatting must not merge separate discussions or alter the
canonical JSON projection, pagination, or explicit seen semantics.

The exact visual treatment and navigation require a focused UX pass informed
by the useful parts of v10. The immutable `6d1b944` trial remains unchanged.

The live trial tracks this as v11 Work `26de18dd-W23` with discussion
`26de18dd-D23`.

## Confirmed split-pane presentation

**Confirmed by Slawomir during the trial.** The message reader is the bottom
pane of a stacked Work/messages layout, analogous to v10 without importing its
outbox model. It renders one selected discussion for the highlighted Work;
distinct discussions are switchable and never flattened into one timeline.

Messages use compact, borderless blocks with clear author and time metadata,
visible message boundaries, wrapped bodies, readable references, and personal
new-state treatment. `Tab` changes pane focus. Preview is read-only and `s`
explicitly marks only the displayed bounded discussion page seen.

**Vocabulary supersession.** The later confirmed v11 vocabulary is
`Work -> Threads -> Messages`; read `discussion` above as `Thread`. Each Thread
has a required subject, while each Message retains its body. The bottom pane is
labelled `Msgs` and identifies the selected Thread compactly. See
`../finding-thread-subject-vocabulary/FINDING.md`.
