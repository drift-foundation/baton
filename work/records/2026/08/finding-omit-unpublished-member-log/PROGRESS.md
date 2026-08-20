# Progress

Implementer-owned. Work `W1578`, claimed by `baton.claude` 2026-08-19.

## Revalidation of the pinned decision

Checked against the current tree before editing. The synthetic row was the
only thing standing between the ruling and the code: `Console._detail_facts()`
appended a `Log` pair whenever `"log"` was absent from the published inventory,
and nothing else in the renderer, the projection or the adapter contract
referred to it. The parent record
`work/records/2026/08/finding-teams-member-detail-table/FINDING.md` already
carries the matching 2026-08-20 supersession, so the two records agree and
neither needed correcting.

`kv_lines()` already omits a section with no rows, so acceptance 3's
"the renderer MAY omit the empty Operational diagnostics section" needed no
code — only coverage proving it now happens.

## Implemented

`src/baton_work/tui/app.py` — `_detail_facts()` returns exactly the published
facts. Its docstring now states the supersession, W184's original reasoning,
and why the live table retired it, so the next reader learns why the current
rule is not the obvious one.

`docs/BATON-WORK.md` — the "`Log` is always present" paragraph is replaced by
the superseding rule: a published `Log` verbatim with source and age, no row
when absent, no section when a member published nothing.

Presentation only. No projection, adapter contract, runtime fact, poke
response or Teams action changed.

## Regressions

`tests/work/test_w1578_omit_unpublished_log.py`, 24 cases against the
acceptance boundary:

- a published log still carries its exact locator, source and age (1);
- an absent log leaves no row AND no sentence, asserted against the whole
  block rather than the `Log` key, because a sentence moved to another key
  would cost the same row and read the same way (2);
- the real inventory is not thinned — a member with facts but no `log` keeps
  its section and every fact in it;
- a member that published nothing has no diagnostics section, with the rest of
  the block asserted present so "omitted" cannot pass by failing to render;
- no heading anywhere is left standing over nothing;
- mixed members render independently in BOTH directions — the locator does not
  leak into the member without one, and is not dropped from the member with
  one — and the answer does not depend on which was drawn first (3);
- every width W184 pinned still fits, the value column is still ONE column
  (the removed row held the section's longest key/value pair, so dropping it
  is exactly the kind of change that shifts alignment), a narrow block keeps
  every remaining key, and a screen too short still says what it could not
  show (4);
- the projection is byte-identical across renders and still reports which
  member published which fact — "the row is gone" and "the fact is gone" are
  very different failures;
- the documentation states both halves and no longer teaches the retired one;
- a real PTY paints both halves in one session: `ada` without a log shows the
  facts and neither row nor sentence, `j` selects `grace` and her locator is
  painted.

`tests/work/test_w184_member_detail_table.py` — the one test encoding the
retired rule, `test_an_unpublished_log_says_so_rather_than_guessing`, is
replaced by `test_an_unpublished_log_is_not_announced`, which names the
supersession and its date and still asserts the half that stands (nothing
guesses a path). Its module docstring records the partial supersession.
Leaving the old test would have left two authoritative and contradictory
statements of the rule. Editing it is authorised by this record's confirmed
decision and PLAN item 2, which name it directly.

Confirmed non-vacuous: with the synthetic row restored, 6 of the cases fail
(5 new, plus the superseded W184 one).

## Verification

- `test_w1578_omit_unpublished_log.py` — 24 passed.
- Focused Teams/TUI/docs suites (`test_w184`, `test_w25_jobs_teams_inbox`,
  `test_w137_runtime_tables`, `test_w103_public_docs`,
  `test_w104_effective_baton`, `test_tui`) — 359 passed.
- Full v11 gate on the final tree — 2633 parallel, 51 serial, 55 ACP, all
  passed.

## Overlapping tree state

`src/baton_work/tui/app.py` also carries the uncommitted W1568 correction
(`work/records/2026/08/finding-command-submit-opens-next-job/`), which is out
for independent review at `baton.bug`. The two changes are disjoint —
`Console._detail_facts()` here, `run()`/`_read_key()` at the module's input
boundary there — and neither touches the other's code or tests. Noted so a
reviewer of either can see which hunks belong to which record.

## State

Awaiting independent review.
