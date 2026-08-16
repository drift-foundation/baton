# Progress

Owner: `baton.implementer` only.

## 2026-08-10 — implemented, compared against this contract

State: **complete, pending review**. No mismatch found.

Implementation: `InboxState.enter_selected`, dispatched from `K.OPEN` in
`baton_tui/driver.py`.

Compared clause by clause:

- Enter enters/focuses DETAIL from LIST focus — yes;
- on a pending directed row whose dwell has not completed, Enter claims THAT
  message immediately and focuses DETAIL, never the FIFO head or a neighbour
  — yes: `enter_selected` clears the dwell and calls `open_selected`, which
  claims by the highlighted message id;
- already-claimed/open rows reopen and focus with no second claim — yes;
- handled and outbound rows open their read-only detail and focus with no
  authority write — yes, through the existing `open_received`/`open_sent`
  paths, which `enter_selected` does not bypass;
- unseen notice keeps its atomic mark-seen/open and then focuses; seen notice
  focuses without a second receipt — yes, pinned by pressing Enter twice and
  asserting one receipt;
- Enter from DETAIL does not toggle back — yes;
- modal Enter unchanged — yes, `enter_selected` returns immediately unless the
  mode is browse;
- an empty/detail-less selection fails visibly and focuses nothing — yes,
  focus moves only when `detail` is not None.

Focus stays pure UI state: `enter_selected` writes nothing itself; only the
pre-existing open/claim/see path does.

Evidence 1-7 covered, including the packaged PTY close test, which now reaches
DETAIL through Enter alone — its previous `Enter` + `Tab` would toggle back.

Break-checked: removing the focus move and removing the dwell commit each fail
named tests.

## 2026-08-10 — corrected after review R1 and R2

State: **corrected, pending re-review**.

**R1.** `enter_selected` decided success by `self.detail is not None`. On a
lost claim race the open refreshes and PREVIEWS the row it could not take, so
`detail` becomes non-None while `opened` stays None — and Enter moved focus
into a pane that cannot show the body the human asked for, contradicting this
method's own documented rule.

`open_selected` now RETURNS whether it opened, and `enter_selected` focuses on
that. A preview is not an open, and only the open can say. Twelve return paths
classified individually: delegation to the sent/draft openers counts as
success, guard failures and the lost race do not.

**R2.** The seen-notice half was tautological: the second Enter happened while
already in DETAIL, so it was governed by the one-way rule and never exercised
the seen-notice LIST path.

Pressing Enter again in the SAME console cannot test it either — the `open`
affordance is false for an already-open row, so the key is correctly
swallowed. The regression now constructs a FRESH session against the same
store, which is the honest way to reach that path, and asserts one receipt,
DETAIL focus, and that the detail says `already_seen`.

Added focus assertions to the handled-inbound and outbound opening tests,
which already covered the authority boundary.

Break-checked: restoring the `detail is not None` test fails
`test_a_lost_claim_race_at_enter_keeps_list_focus` by name.

## 2026-08-10 — corrected after re-review

State: **corrected, pending final re-review**.

One branch still bypassed the explicit open-success result. `open_selected`
delegated the whole SENT view to `open_sent_selected` and returned True
unconditionally, so a REFUSED sent read still focused DETAIL over the
lightweight preview.

That hole is mine and it is specific: converting the twelve return paths, I
classified the two DELEGATIONS as success without checking whether the
delegate could fail. `reopen_draft` cannot. `open_sent_selected` can — a
damaged pin or an authority failure returns without content.

`open_sent_selected` returns a bool now and `open_selected` propagates it.

Evidence: `test_a_failed_sent_read_at_enter_keeps_list_focus`, driving a store
whose `open_sent` raises, asserting LIST focus and a visible failure; and
`test_a_successful_sent_read_at_enter_still_focuses`, so the fix cannot become
"never focus from SENT", with a claim-count assertion keeping the zero-write
property.

Break-checked: restoring the unconditional `return True` fails the first by
name.

## 2026-08-10 — live-trial defect corrected

State: **corrected, pending re-review.** 2282 passed. `bin/baton-tui` rebuilt.

The defect and my part in it:

`affordances()["open"]` was false once `_already_open` was true, and dispatch
refuses a key whose affordance is false — so `enter_selected` never ran after
the dwell had opened a row, and the most ordinary sequence in the console
(pause on a message until it opens, press Enter to read it) left focus in the
list.

**I recorded that behaviour as correct.** When my seen-notice regression hit
this gate, I wrote that pressing Enter again "cannot test it because the row
is already open, so the key is correctly swallowed" and built the test around
the obstacle. The finding's already-open clause said the opposite in writing —
"reopen or retain its detail and focus it without another claim" — and I read
past it because the gate's own comment offered a reason that sounded right.

"Opening again is redundant" is true. "Enter has nothing to do" does not
follow.

The fix, in two parts:

- the affordance now offers the key when EITHER opening is available or a pure
  focus transfer is: browse mode, LIST focus, detail already showing this
  row. One predicate still serves dispatch and the legend, so they cannot
  drift;
- `enter_selected` returns early on an already-open row: focus moves, and the
  store is not called at all. "Without another claim" is the ruled wording,
  and a reopen would also be a second read of what is already on screen.

Evidence:

- `test_enter_after_the_dwell_opens_enters_the_detail_without_a_second_claim`
  — the exact live sequence, with a claim count either side;
- `test_entering_an_open_row_touches_the_store_not_at_all` — driven with a
  store that raises on any attribute access, so "makes no call" is proved
  rather than asserted;
- `test_enter_is_still_offered_once_the_row_is_open` — REPLACES the test that
  pinned the wrong rule, and says so in its docstring;
- a packaged PTY regression that waits out the real two seconds and then
  presses Enter, because every in-process test passed while the packaged
  console was broken.

`_in_detail` in the driver suite pressed `Tab` unconditionally to reach the
detail pane; with Enter now entering, that toggled straight back out. It
asserts the state it needs and presses `Tab` only if required — a fixture
that counts keystrokes does not survive a keystroke changing meaning.
