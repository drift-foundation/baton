# Progress — Messages view exposes unrelated Work actions

Owned exclusively by the implementer (`baton.claude` under v11).

## Step 1 — W90 implemented (2026-08-17)

Claimed W90. Revalidation confirmed the defect is still present after
W76 and W123: `_facts()` appended `available_transitions` as a
`can: ...` line, and the facts block paints directly above the Threads
list.

### The change

One line removed from `_facts()`. Nothing else: outcome and durable
rationale, active claimant, binding, contract revision, duplicate and
follow-up identity all remain. The canonical `available_transitions`
stays in the JSON detail for every client and the command grammar is
untouched — `prioritize` still works, and a regression proves it.

The docstring now records WHY, because the removal otherwise reads as
hiding something useful: the capability is real, but it belongs to the
Work and is open to any configured member of the owning team, so
repeating it above a conversation invited reading it as a message
operation.

### A boundary question the finding did not have to answer

W123 added an Events tab after this finding was written, and the facts
block is shared by both tabs. The finding's remedy is scoped to
`_facts()`, which is the only production renderer of that text, so the
line disappears from both surfaces. That is the right outcome: Events
is the operational journal of what HAPPENED, not a control panel of
what may happen.

The finding anticipates "a genuine Work-actions/help surface" as the
place it should reappear. There is no such surface today — the `o` view
the module prose still describes was superseded by W71's
Enter-to-detail, and no `o` handler exists — so nothing was displaced.
Recorded here so the next reader does not go looking for it.

### Evidence

New `tests/work/test_w90_message_action_noise.py` (10): the pure
renderer for an authorized viewer and for a configured member the route
does not resolve; every other fact surviving, including a bound and
claimed Work and a terminal one with its rationale; the canonical
projection still declaring authority; the command grammar still
executing `prioritize`; no capability text on the painted screen at
wide and narrow widths; the reading context — Threads, Messages, and
the message body — intact at both; and the Events tab equally free of
it while still rendering.

Packaged parity in `tests/work/test_tui_packaged.py` runs the deployed
console at both widths against a Work the viewer genuinely handles, so
the projection really does declare authority the screen must not
repeat.

Break-sweep: restoring the `can:` line reds 5.

### One superseded test converted

`test_tui.py::test_the_focused_view_exposes_the_projection_declared_transitions`
asserted the opposite — that the TUI shows every declared transition.
Its principle (a human must not discover authority by attempting
invisible operations) survives in the JSON, which is exactly what W90
preserves, so the test is converted rather than deleted: it now proves
the canonical projection still declares the authority AND that the
reading surface omits it, with the reading context intact. Renamed to
say what it checks.
