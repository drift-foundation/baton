# Finding: Work details need a usable message index and reading pane

## Observed — 2026-08-16

The first fresh-authority trial opened W2's detail view with one Thread and
three personal-new Messages. The screen correctly exposed the Work summary,
Thread, formatted message bodies, and references, but rendered all message
blocks vertically in one dense lower stream. Slawomir ruled the result not
usable: message boundaries compete for height, references dominate the
reading area, and there is no compact overview from which to select one
message for focused reading.

This is a new live-acceptance defect after completed W71. W71 is not reopened.

## Confirmed redesign — 2026-08-16

**Approved by Slawomir during the fresh-authority trial.** Retain the Work
detail screen and its distinct Thread list, but supersede W71's flat
formatted-message stream with three navigable regions:

1. the compact Work summary remains at the top;
2. the Thread list remains below it and selects one canonical Thread;
3. the lower region contains a compact Message index and a selected-message
   reader.

At usable width, the Message index is on the left and the selected Message is
on the right. The index shows the existing stable message sequence as a
compact `M<seq>` label, author, time, and personal new/seen state. It does not
invent another persisted identifier. The reader shows exactly one selected
Message body with its `Refs` separated from body text.

At narrow width, the same two regions stack with the Message index above the
selected-message reader. Narrow fallback must not merge messages back into a
flat body stream or lose canonical text/references.

`Ctrl-W` navigation extends across Threads, Message index, and reader; normal
selection/scrolling acts only within the focused region. Moving through
Threads selects that Thread's personal-new Message first when one exists;
moving through the Message index updates the reader. Viewing and selection
remain read-only. Explicit `s` advances the selected Thread's per-participant
cursor through the selected Message and no later Message.

The redesign preserves canonical Threads, message chronology, bounded paging,
explicit seen semantics, multi-Work labels, and source/packaged parity. It is
a projection/presentation change and must not require a new authority schema.

The earlier horizontal index/body proposal was superseded before this live
screen existed. This dated ruling restores it only inside Work details based
on direct acceptance evidence; the main screen remains Work-only and `Enter`
continues to open Work details.
