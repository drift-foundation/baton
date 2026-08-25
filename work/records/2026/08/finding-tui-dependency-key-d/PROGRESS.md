# Progress: use `d` for the dependency view

Implementer-owned. One writer: `baton.claude`.

## Implementation — 2026-08-23

**Revalidated first, and the reviewer's revalidation held.** Lowercase `d` is
unbound in every live dispatch path — I enumerated every `ord("<lower>")` in
`src/baton_work/tui/app.py` (j k p n s z y x w c b a u t q l i h, no `d`),
checked the `key in (...)` forms the enumeration would miss, and checked the
three `chr(key)` text-entry paths, where `d` is a character an operator types
into the command bar, the batch buffer or the search box and never a binding.
`b` had exactly two bindings and both were the dependency entry.

**The change is four lines of behaviour and their honest prose.** Both
dispatch branches move to `ord("d")`, the one live footer advertises
`[d] deps`, and `docs/BATON-WORK.md`'s three current-contract references
follow. `b` is removed outright. Nothing outside the dispatcher, the footer
string, the guide and key-specific tests was touched: the projection, the
graph renderer, `_open_graph`, breadcrumb navigation and the protocol commands
are all as they were, and Search still has no dependency legend because
inventing one would have been a layout change riding along with a key
correction.

The footer string is the same width in both spellings, so no fit judgment
moved and the narrow-width case needed nothing.

### The removal is asserted, not inferred

Deleting the old positive `b` cases would prove only that nobody tests `b` any
more. An alias — the exact thing the confirmed decision forbids — would leave
every renamed case green. So `tests/work/test_w96_dependency_key_d.py` owns
the half a rename cannot prove: pressing `b` in the Work table and in Search
results moves nothing an operator would notice (mode, breadcrumb trail,
cursor, selection, search page, graph centre), and on a real terminal the
footer is still on screen with no edge drawn until `d` is pressed. Each case
then presses `d` from the state `b` left behind, so the removal did not cost
the action its entry point.

Search is a separate binding and therefore a separate removal: it dispatches
before the table branch ever runs, which is why it needed its own branch when
the action was added and why it needs its own negative case now.

### History kept rather than rewritten

`test_w17_deps_label.py` is the suite W17 wrote to stop the footer reading
`b links`. Its module docstring KEEPS that sentence and the `[b] deps` it
ruled, then says W96 moved the key and why. The reasoning that was superseded
is how the next reader knows the current spelling is not the obvious one. The
same applies to the two dossier records that carry the superseded ruling —
both already had explicit dated supersession markers when I picked this up,
and I added nothing to them.

`test_w1568_command_submit_enter.py` still sends `b"b"`: that is a character
typed into the batch buffer, not the dependency key, and changing it would
have been a rename chasing a substring.

### Five mutations, all witnessed

Both alias forms, both half-reverted bindings, and the footer. The two alias
mutations are the ones this Work exists for and they fail exactly the new
negative cases.

**One thing named rather than omitted.** Under the table-reverts-to-`b`
mutation ONLY, one four-file selection hangs instead of failing, while each
of those files fails fast alone. That mutation leaves the dispatcher in a
state no delivered tree has — `d` bound in Search, unbound in the table — and
it does not reproduce in the delivered tree, where the same selection and the
full gate are green. I did not chase it further; it is recorded because a
hang under mutation deserves a reviewer's eye even when the mutation is
artificial, and it is not offered as a finding against this change.

### Verification

- Focused baseline before any edit: **22 passed** (a superset of the
  reviewer's 10).
- Focused surfaces after, 9 files: **167 passed**.
- `pytest -n auto -m "not serial" tests/work` — **2980 passed, 0 failed**
  (2977 before; the three new W96 cases).
- `pytest -m serial tests/work` — **52 passed, 0 failed**.
- `tools/acp-baton-bridge npm test` — **55 pass**, the gate `just test-v11`
  chains.
- Whitespace clean.

**Every gate this Work touches is green.**

No existing test assertion was edited or weakened. Renamed cases kept their
assertions; only the key they press and the label they read moved.

### State

**Awaiting independent review.** Per the coordination message on T96 this
passes to `baton.tune`, not back to `baton.impl`.
