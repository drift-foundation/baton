# C1–C3 done: vacuous pin made real, stale comment gone, MESSAGES newest-first

All three addressed. C1 was a fair catch and the worse kind: the assertion
could not have failed. C3 is implemented as a presentation-only change with
the two silent hazards it carried fixed and pinned. No protocol, schema or
agent-CLI change; the frozen boundary is intact. No Git operations.

## C1 — the no-History instance pin was vacuous

You are right, and the reason is worth stating: `history_rows`,
`history_cursor` and `history_top` were created in `__init__` and never
existed on the class, so `not hasattr(InboxState, ...)` was already true
BEFORE the removal. It reported a guarantee it had never checked — the same
shape as the footer pins that compared the screen against the constant that
produced it.

It now instantiates the model and asserts all three are absent from the
instance and from `vars(instance)`, keeping the module, class and core checks
beside it. Verified by restoring one field to `__init__` and watching it fail.

## C2 — the last active column-layout comment

`_inbox_pane` no longer says the Sent filter is "the SAME pane at FULL height"
on a pane that is "narrow already". It now says what is true: the same TOP
list pane, full terminal width, about 40% of the body height. Superseded
discussion in TRIAL and FINDING is left as history, as you said.

## C3 — MESSAGES is newest-first, by total order

Implemented exactly as ruled: `(created_ts, id)` descending, the same ordering
discipline the Sent filter already used.

**Presentation only, as specified.** `claim` and `wait` are untouched and
still take the oldest pending message. `list_messages` still returns the
ascending total order; its docstring now says that this is a stable base
rather than a presentation decision, because it previously asserted "the
oldest unanswered work is at the top where it belongs" — a claim about a
screen, made in the core.

Your three constraints, each pinned:

- **Same-sender warning.** It compared `self.rows[:self.cursor]`, which meant
  "older" only under oldest-first. Under the ruling those are the rows NEWER
  than the selection, so it would have inverted itself — silently, and in the
  half that never fires when it should. It compares `(created_ts, id)` now.

  One change beyond your wording, declared: it is now restricted to INBOUND
  rows on both sides. An outbound `pending` row is someone else's queue and
  warning about "skipping" it was meaningless; your own sentence says inbound.
  Say the word and I will drop the restriction.

- **Arrivals at the top without stealing focus.** Preserved by ROW IDENTITY
  across refresh, in MESSAGES and in the Sent filter. This is the wrong-target
  bug from round one arriving through the poll rather than a keystroke. The
  Sent one reads its previous row directly rather than through
  `selected_sent`, which answers only while Sent is the active view while the
  poll runs in both.

- **First/last, paging, exact-fit/overflow, handled and outbound rows** all
  continue to work and are pinned under the reversed order.

**Ties, and a pin that lied before I fixed it.** Baton stamps to the second,
so same-second sends tie and order by id. Two of the new pins needed a real
second of separation to guarantee the arrival sorted ABOVE the selection;
tied, it landed below and the assertion proved nothing. The Sent-cursor pin
PASSED against the deliberately broken implementation until that was
corrected. Reporting it because it is exactly the failure mode you flagged in
C1, found on my own side one round later.

Two existing tests described the superseded order and were rewritten:

- `test_inbox_order_matches_what_claim_would_deliver` →
  `test_messages_is_the_exact_reverse_of_what_claim_would_deliver`. The
  property it was really about — the console and the core break ties on `id`
  identically — is unchanged and is what it asserts now, plus that the newest
  row is the one `claim` takes last.
- `test_skipping_a_senders_earlier_message_warns_but_allows` — the row that
  skips something is the head of the list now. It pins both directions: the
  newer row warns, the oldest pending row does not.

Documents updated: FINDING's "NEWEST FIRST is the default order" replaces the
FIFO bullet and records oldest-first as superseded with the reason; the INBOX
bullet in §3 no longer says FIFO order; PLAN gains three architecture entries
(presentation vs delivery order, compare by total order never by position,
cursor follows the row not the index); TRIAL records the round; README states
the list is newest-first and that delivery order is unaffected. The one
remaining FIFO sentence in TRIAL is a historical entry and now says it was
superseded rather than being rewritten.

## Deliberate-break checks

| Break | What fails |
|---|---|
| a former history field restored to `__init__` | the no-History instance pin |
| sort ascending again | five ordering pins, including reverse-of-delivery |
| cursor restored by index instead of identity | the arrival-at-the-top pin |
| the warning compared by list position again | the same-sender warning pin |
| the Sent cursor restored by index | the Sent-filter identity pin |

## Verification

    just test          1586 passed   (was 1578)
    git diff --check   clean
    bin/baton-tui      975c3f8027a83257c50145dec42ca5a61ab538cb6abadc7aa16e5ef8fbb085c9
                       deterministic: rebuilt twice, byte-identical
    frozen             bin/baton a23461ae7577422f5c4ade86eae370926b2dc41bc93ecd7732c29b2785374566,
                       DISTRIBUTION.json, baton_v6.py, build_zipapp.py unchanged
    docs               test_docs_consistency.py green

README flow executed end to end again; `doctor` reports the instance clean.

## Changed paths since the last handoff

    baton_tui/state.py
    baton_tui/render.py
    baton_core/_impl.py
    bin/baton-tui
    DISTRIBUTION-TUI.json
    README.md
    test_tui_state.py
    test_tui_render.py
    test_core_parity.py
    work/finding-human-console/FINDING.md
    work/finding-human-console/PLAN.md
    work/finding-human-console/TRIAL.md

New tests, all in `test_tui_state.py`:
`test_messages_is_newest_first_by_a_total_order`,
`test_a_notice_sorts_into_the_same_newest_first_order`,
`test_new_mail_arrives_at_the_top_without_moving_the_selection`,
`test_the_sent_filter_keeps_its_row_when_something_is_sent`,
`test_first_and_last_still_reach_the_ends_under_newest_first`,
`test_handled_and_outbound_rows_keep_their_place_in_the_new_order`.

Existing tests deliberately rewritten this round: the two ordering tests named
above, and `test_there_is_no_history_view` (C1). `test_core_parity.py`'s
divergence note lost the word FIFO from a sentence about the console's list;
the authorized divergence itself is unchanged.

## Still outstanding, unchanged

`assets/artwork/baton-tui.png` is now stale in two ways — it shows columns AND
oldest-first — and still needs a real-terminal capture from Slawomir's trial.
Recorded in PLAN under "Remaining before this stage is committed".

References:
- baton_tui/state.py
- baton_tui/render.py
- baton_core/_impl.py
- test_tui_state.py
- test_tui_render.py
- test_core_parity.py
- work/finding-human-console/FINDING.md
- work/finding-human-console/PLAN.md
- work/finding-human-console/TRIAL.md
- README.md
- assets/artwork/baton-tui.png
- DISTRIBUTION-TUI.json
