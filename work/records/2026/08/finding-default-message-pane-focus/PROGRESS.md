# Progress

Implementer-owned. Work `W2597`, claimed by `baton.claude` 2026-08-20.

## Revalidation (PLAN item 1)

The record says "Topics"; the code says threads. Same thing — noting it so the
two vocabularies are not read as two concepts.

Fresh entry happens in exactly three places, each spelling the same six lines
for itself: the Jobs table's Enter, the search-results Enter, and the Inbox
row's Work context (which hands over to Jobs with the Work open). All three set
`focus = "threads"`.

The record's distinction between a fresh entry and "returning to an
already-open detail view" resolves cleanly against this console:

- `Esc` leaves detail for `detail_return`, so the next `Enter` is a FRESH entry
  and gets the default again. There is no retained per-Work view to return to.
- What genuinely returns is a detail TAB switch: `_switch_tab` keeps each tab's
  own focus, selection, page cursor and reader scroll in separate fields, so a
  Messages↔Events round trip preserves whatever pane the operator chose.

Both are asserted, because the ruling names the distinction and only the second
one exists here.

Two facts settled the shape rather than being assumed: the renderer autoselects
`msg_cursor` whenever it is not on the visible page, so a Message is selected
by the first paint and `j`/`k` work immediately; and pane cycling is over a
fixed region list, so focus can always leave a pane regardless of its content.

## Implemented (PLAN item 2)

`src/baton_work/tui/app.py`:

- `DETAIL_ENTRY_FOCUS = "index"`, one named constant, because a default three
  call sites each spell for themselves is a default that drifts.
- New `Console._enter_detail(work_id, came_from=)` — the three paths now share
  one helper that says what a fresh entry IS. Both selections stay deferred to
  the renderer (`disc_cursor=None`, `_reset_message_selection()`), so entry
  cannot invent a Message, mark one seen, or read the authority.

Nothing else moved: the Messages tab is still the default tab, the Thread
autoselect rule is untouched, and the visible Thread still decides which
Messages are shown.

`docs/BATON-WORK.md` states the default, why it exists, how to reach the
Threads list, and that it applies to a fresh entry rather than a tab return.

## The acceptance boundary's empty cases are unreachable — reported, not faked

Two acceptance clauses ask for "Work with no Topic" and "Topics with no
Messages" to stay safe. **Neither state is reachable through the public
surface**, and I did not manufacture one:

- every Work is born with a Thread, and `unlabel_thread` refuses to remove a
  Thread's final label — "a thread always keeps explicit Work scope";
- every Thread is created with its first Message, by `create_work` and by
  `start-thread` alike.

So the renderer's `(no threads)` branch is defensive, not reachable. The tests
say so in terms and drive that branch directly instead of pretending, which
keeps the guard covered without asserting a fiction about the authority. The
reachable half of the concern — that focus can leave an empty index, that the
movement keys are inert, and that `s` with nothing selected writes nothing —
is asserted for real.

## Adapting the suites

The default change broke 17 tests across seven files. Every one of them was a
test that entered detail and then pressed keys meant for a particular pane, so
the adaptation is about WHERE each test says it wants to be:

- tests whose subject is the Message index or the reader dropped the
  now-redundant `Ctrl-W j`. The step is genuinely gone, which is the benefit
  this Work delivers — but PTY scripts index their screens positionally, so
  deleting a step silently re-points every later assertion. Rather than
  renumber ~20 index references across six files, each removal became an
  explicit `(b"", pause)` settle step carrying the reason. Step counts, and
  therefore every assertion, are unchanged. Where a test used ONE step with two
  chords to reach the reader, that step became one chord.
- tests whose subject is the THREADS pane — thread selection, thread-set
  paging, the `»Threads` focus marker — now reach it explicitly, with the
  entry and the `Ctrl-W k` combined into the existing first step so their
  positional assertions also hold.
- `test_w1151_pane_focus.py` owns pane cycling. Its cycle expectations are
  ROTATED, not weakened: Tab still visits all three panes in one order and
  wraps. Its Tab-versus-chord equivalence test walks index→reader→threads now
  instead of threads→index→reader, asserting the same property.
- `test_w71_navigation.py` and `test_w30_reader_heading.py` assert a sequence
  of focus STATES; each starts by going up to Threads so the same states are
  compared in the same order.

No assertion was weakened or deleted. Every changed line either states where a
test now stands, or says the gesture it used to need is gone.

## Regressions (PLAN item 3)

`tests/work/test_w2597_detail_entry_focus.py`, 17 cases:

- fresh entry focuses the Message index, and the SCREEN marks it — state alone
  would not prove the operator can see where the cursor is;
- `j`/`k` move the Message selection with no preliminary pane switch, which is
  the acceptance boundary's headline;
- the Thread is still autoselected and still decides which Messages are shown;
- all three entry paths — Jobs, search, Inbox — reach the same focus, and the
  search path keeps its `detail_return`;
- `Shift-Tab` and `Ctrl-W k` both reach the Threads pane, which still
  navigates once reached;
- the empty index is inert but not a trap: focus leaves it, `Esc` leaves the
  view, and `s` with nothing selected writes no event;
- entry writes nothing — asserted on the authority sequence AND on the personal
  New count, because a seen advance is exactly the write that would not move a
  Work row;
- leaving and re-entering re-applies the default, while a detail tab round trip
  preserves the pane the operator chose. The two halves of the ruling's
  fresh-versus-return distinction.

Confirmed non-vacuous: with the constant set back to `"threads"`, 7 of the 17
fail.

## Verification (PLAN item 4)

- `test_w2597_detail_entry_focus.py` — 17 passed.
- Full v11 gate — 2688 parallel, 51 serial, 55 ACP (round 1).

## Overlapping tree state

`src/baton_work/tui/app.py` also carries the uncommitted W1568 and W1578
changes, and `docs/BATON-WORK.md` carries W1578, W2571 and W2693. This Work's
hunks are `DETAIL_ENTRY_FOCUS`, `Console._enter_detail` and its three call
sites, and the pane-focus paragraph in the document.

## 2026-08-20 — review round 1: changes requested

`review-2026-08-20T12-31-04Z.md`, P1. **Confirmed by reproduction**, exactly as
the reviewer described it: `_enter_detail` reset the Work, thread cursor,
Message selection, focus, return target and mode — but not `detail_tab`, which
also survives `Esc`. Measured on a two-Work console: open A, `]` to Events,
`Esc`, open B → B opens on Events, contradicting both the confirmed decision
and the paragraph I had just written into `docs/BATON-WORK.md`.

The reviewer is also right about why my suite missed it. My
`test_leaving_and_re_entering_re_applies_the_default` only moved the Message
PANE focus before leaving, and the entry helper always reset that — so the test
could not fail for this. The new cases leave from the other TAB and open a
DIFFERENT Work through a real entry path.

### The same gap one level down

Correcting P1 exposed the identical leak beneath it, so I fixed both rather
than leaving the operator one `]` from the same defect. Measured on the same
console: the Events tab's `event_before`, `event_cursor`, `event_focus` and
`event_skip` all survive `Esc` too. After paging A's Events and leaving, Work B
opened with `event_before=11, event_cursor=10` — sequences belonging to Work A.
A page cursor is not merely stale across Works; it addresses a different Work's
journal.

Both are the same defect and the same boundary, which is why both are fixed in
`_enter_detail`: a fresh entry now clears `detail_tab` and the Events tab's
cursor, page, pane focus and reader scroll. `_switch_tab` is untouched, so a
tab ROUND TRIP inside one open detail view still preserves both sides — that
was always its job, and it was never meant to follow the operator to a
different Work.

### Regressions added (now 21 cases)

- a fresh entry after leaving from Events opens on Messages — the reviewer's
  exact live sequence, with a second Work and a real entry path;
- re-entering the SAME Work from Events also opens on Messages, because a fresh
  entry is about the entry and not about which Work it lands on;
- a fresh entry leaves no Events cursor, page, focus or scroll from the
  previous Work;
- an in-detail tab round trip still preserves BOTH sides' chosen panes, so the
  correction cannot be read as permission to reset per-tab state.

Confirmed non-vacuous: with the two resets removed, those three fail and the
round-trip test still passes — which is the pair of facts that says the fix is
in the right place.

Verification after the correction: `test_w2597_detail_entry_focus.py` 21
passed; full v11 gate on the final tree — 2692 parallel, 51 serial, 55 ACP.

## State

Awaiting independent review (round 2).
