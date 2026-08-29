# Progress — make breadcrumbs focusable and navigable

## 2026-08-28 UTC — `baton.tuner` implementation

W26331 was explicitly rerouted from `baton.impl` to `baton.tune` for bounded
TUI work. Under that claim I revalidated the approved client-only decision
against the current console and separated structural breadcrumb location from
the existing bounded browser-history stack.

The implementation added structured focusable crumb targets, complete
Tab/Shift-Tab and bounded Work-detail Ctrl-W participation, horizontal
selection, direct one-action navigation, exact one-Back restoration, same-tab
Work jumps, captured page restoration, whole-token viewport markers, compact
exact selectors, and textual focused feedback. It added the focused W26331
regression suite and updated only the compatibility expectations explicitly
superseded by the approved breadcrumb contract. No protocol, schema,
projection-version, authority, or workflow behavior changed.

Verification recorded in `evidence/w26331-2026-08-28-tuner.txt`:

- focused breadcrumb and pane-focus set: 35 passed;
- affected navigation and compatibility set: 277 passed;
- complete v11 gate: 3239 parallel, 54 serial/PTY, and 77 ACP passed;
- diff hygiene: clean.

The implementation was passed to `baton.rsrch` for independent review.

## 2026-08-28 UTC — `baton.tuner` review correction

Independent review `review-2026-08-28T04-32-38Z.md` identified three defects
inside the approved contract: repeated graph Work crumbs shared one focus key,
focused Up/k could mutate the hidden body selection, and viewport fitting
counted code points rather than terminal display cells.

Under the returned tuner claim I gave each displayed Work occurrence a stable
unique structural key, consumed both Up spellings at the focused breadcrumb
boundary on every single-body page, and applied the console's terminal-cell
metric consistently to viewport selection, painting, right-edge reservation,
and footer fitting. Regressions cover repeated graph occurrences with Enter
and Back, both Up spellings across all five single-body page types, wide and
combining labels, compact-selector fallback, and right-edge survival.

Correction verification recorded in the same evidence file:

- focused breadcrumb and pane-focus set: 48 passed;
- affected navigation and compatibility set: 294 passed;
- complete v11 gate: 3252 parallel, 54 serial/PTY, and 77 ACP passed;
- diff hygiene: clean.

Independent re-review `review-2026-08-28T04-46-59Z.md` signed off all three
corrections and the application as complete. No further application review is
pending.

## Current state

Application work is signed off. The approver resolved the dossier's missing-
progress ownership question at Work event 29105: because `baton.tuner` made
both implementation changes under explicit claims, this attributable record
is tuner-owned. W26331 is ready to return directly to `baton.ops` for
satisfying closure.
