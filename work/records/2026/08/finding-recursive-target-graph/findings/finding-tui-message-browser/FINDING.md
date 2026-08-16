# Finding: the v11 message preview hides navigation and crowds references

## Observed

The first post-`8450a40` trial can show `New 2` while painting only one whole
message block in the lower preview. The pane labels the selected Thread as
`T1/1`, but does not say that this is a Thread ordinal, does not indicate that
another message page exists, and does not expose the `n`/`p` controls. Reaching
the second message therefore requires prior knowledge rather than discovery.

References are painted directly after the body with the same compact visual
rhythm. In the already-short lower pane they read like a crowded final body
paragraph rather than a separate set of message resources.

## Confirmed requirements — 2026-08-15

**Confirmed by Slawomir during the live v11 trial.** Any paged message surface
must visibly state that more content exists and advertise the controls that
reach it. `New` is a count for the Work scope; the UI must not leave an
operator guessing why fewer message blocks are currently visible. A Thread
ordinal must be identifiable as a Thread ordinal, not easily mistaken for a
message-page count.

References are visually separate from the message body. When present, they
appear under an explicit `Refs` section (or an equivalently unambiguous
separation), one readable reference per line. When absent, the section may be
omitted. Reference text remains canonical and lossless; presentation never
turns it into body content.

Explicit seen semantics remain unchanged: merely viewing or selecting a
message does not mark it seen. The UI must make the seen action and its extent
discoverable rather than relying on remembered keys.

Pane navigation uses the Vim split-window convention instead of consuming a
new single-letter key for every pane or requiring repeated `Tab` cycling.
`Ctrl-W` is the prefix (written with an uppercase `W` by convention; the
keystroke is Ctrl plus lowercase `w`): `Ctrl-W h/j/k/l` and `Ctrl-W` plus the
arrow keys move left/down/up/right, while `Ctrl-W w` and `Ctrl-W Ctrl-W` cycle
panes. The active bindings must be visible in footer/help text.

The preview must not expose its internal pagination cursor as `after #N`.
That value describes a projection request, not the operator's position or an
action they can take; at the initial page, `after #0` is especially
meaningless noise. Remove it from the TUI. If continuation exists, express it
only as clear operator-facing more/page state alongside the controls that
reach it.

## Confirmed navigation model — 2026-08-15

**Confirmed by Slawomir after comparing the hierarchy/detail alternatives.**
This supersedes both the earlier persistent main-screen message split and the
horizontal message-index/body proposal.

The main screen contains Work only. It shows top-level Work and each root's
immediate children as indented `↳` rows—at most two hierarchy levels in one
view. A visible disclosure marker/count identifies a child that itself
contains children. Indentation represents the single-parent containment tree
only; dependency/blocker graph edges never masquerade as children.

The main tree removes `Prog` and `Dep`; it does not add separate graph-count
columns. Indentation/disclosure communicates ordinary containment and its
parent-close gate. Arbitrary many-to-many graph information belongs in Work
details/links. Canonical JSON still exposes child progress and the explicit
live fields `open_blockers`/`open_dependents`; the ambiguous `dep` field is
removed.

`Enter` has one meaning in the Work list: open the selected Work's detail
view. It never drills into children. A separate visible `u` (unfold) action
re-roots the Work list at the selected Work and shows that Work plus its
immediate children. Breadcrumbs identify the re-rooted position and Back/Esc
returns upward. This sliding two-level window covers ordinary parent/child
lists without losing deeper containment.

The Work detail view shows its distinct Threads on top. Each Thread retains
its own subject; Messages do not acquire individual subjects. Moving through
the Thread list updates the Messages pane below to show only that selected
Thread's messages. Threads labelled to several Work remain one canonical
Thread and are not copied or merged into a false timeline. A Thread with
personal New is selected first when present, but selection/viewing marks
nothing seen.

`Ctrl-W` navigation applies to the detail panes: direction keys or arrows move
between Threads and Messages, and `w`/repeated `Ctrl-W` cycles. Normal list and
message scrolling acts within the focused pane. Footer/help text advertises
the active controls. The Messages pane retains formatted message blocks,
explicit seen action, bounded continuation, and the separately ruled `Refs`
section. No `after #N` cursor is displayed.

This is the actionable W71 contract for the final schema-14 batch.
