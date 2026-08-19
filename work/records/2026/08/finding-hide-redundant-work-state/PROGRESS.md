# Progress

## 2026-08-19 UTC — `baton.claude` (implementer)

PLAN steps 3 and 4: the lifecycle-aware Work-list columns ruled 2026-08-18 and
approved by Slawomir. Presentation only — canonical `status`, `phase`,
`outcome`, filtering, detail and Events are untouched, and no projection field
moved or changed meaning.

## Revalidation against the current tree

- `COLUMNS` still carried `("ST", 6)` as a MANDATORY column: it was absent from
  `DROP_ORDER`, so it never yielded even at widths where the table refused
  whole. Six cells plus a separator, spent on a word every visible row shared.
- `visible_columns` and `layout_fits` were pure functions of width and the Id
  column, shared with the parity suite so the two surfaces cannot disagree
  about the layout. Both needed the view's lifecycle question added rather
  than a second layout path.
- `visible_rows` already owned the "can this view contain terminal Work"
  predicate inline. It is now factored as `Console.terminal_visible()` and
  used by both, so the column set and the row set cannot disagree about which
  view this is.
- The TUI has no sort or layout of its own beyond these helpers, so parity
  follows structurally once they agree.

## What changed

| before | after |
| --- | --- |
| `("ST", 6)`, never dropped | `("OUT", 5)`, present only where terminal Work can be seen |
| `status_cell` → `open` / `c/sat` | `outcome_cell` → `-` / `sat` |
| `OUTCOME_COMPACT` = `c/sat`, `c/nsat`, `c/rej`, `c/canc` | `sat`, `nsat`, `rej`, `cancl` |
| `DROP_ORDER` without ST | `DROP_ORDER` + `OUT`, **last** |

`visible_columns(width, id_width=0, terminal=False)` and
`layout_fits(width, id_width=0, terminal=False)`.

Three points worth stating because each was a choice:

**The trigger is the VIEW, not the rows on screen.** `terminal_visible()` is
the ruling's own pair of triggers — revealed with `z`, or a closed-status
filter — and deliberately not "does a closed row happen to be visible". The
sibling `Wait` cue column does derive itself from the rows, so the local
precedent pointed the other way; the difference is that a dependency cue
appears when an edge is added, while a status changes underneath the operator
during ordinary work. A column that came and went on its own would be harder
to read than one dash.

**`Out` drops LAST.** It exists only because the operator asked to see
terminal Work, so dropping it early would make the reveal pointless; Route and
Next are the least interesting facts about a closed row. The old `St` was not
droppable at all, so this is also the first time the column can yield instead
of pushing the table into its too-narrow refusal.

**The `c/` prefix went with the column that needed it.** It encoded "closed",
which is exactly the redundancy the ruling removes — and the only way to see
this column at all is to have asked for terminal Work.

## Regressions — `tests/work/test_w73_outcome_column.py`, 16 tests

Open-only (no `St`, no `Out`, and no row carrying the word `open`); a
collapsed closed row not summoning the column; all four outcomes
distinguishable; the compact vocabulary being exactly the ruled one with no
`c/` survivor; an open row dashing in a mixed view; the closed-status filter
as the second trigger; the column following the view rather than the rows;
Phase still dashing on terminal Work with the outcome in its own column;
canonical status/outcome unchanged in home rows and detail; the freed cells;
`Out` outliving Route and Next; Id and Title outliving `Out`, with a refusal
one cell narrower; and determinism across every width from 20 to 139.

One test defect worth recording: my `Screen` mock replaced the tail of a row
on every `addnstr`, so only the last write survived and every row decoded as
id-plus-title. Three assertions passed for the wrong reason before failing for
the right one. It now paints in place.

## Break-sweeps

Each defect reintroduced alone against the 16-test suite.

| Reintroduced defect | Result |
| --- | --- |
| The State column is restored unconditionally | 4 red |
| `Out` is shown in open-only views too | 2 red |
| `Out` is never shown at all | 8 red |
| An open row shows a word instead of `-` | 1 red |
| The `c/` prefix comes back | 8 red |
| `Out` drops first instead of last | 2 red |
| The column follows the rows rather than the view | 1 red |

## Existing tests updated

All forced by a ruled presentation change — the column set and the compact
vocabulary both moved by ruling — and none weakening what its test proves.

- **`test_parity.py`**: `_parse_rows` reads `terminal` from the painted header
  (`"Out" in header`), which is the same source of truth it already uses for
  the Id width — so the decode cannot drift from what was drawn. The parity
  assertion became an outcome comparison, and gained a case the old one could
  not express: when the column is ABSENT, parity is that the projection agrees
  every row is open. The closed-row assertion also now checks that an open row
  in the same revealed view dashes rather than borrowing the closed row's
  meaning.
- **`test_tui.py`**: the header list drops `St` and gains an explicit assertion
  that neither `St` nor `Out` appears in an open-only view; the narrow-width
  survivor set follows the freed cells; `c/sat` → `sat` plus a new assertion
  that the `Out` column appeared with the reveal; the too-narrow width moved
  30 → 28.
- **`test_w3_priority.py`**: its "first width that drops anything" baseline
  compared against `len(COLUMNS)`, which now includes the conditional `Out`
  entry an open-only view never draws. It compares against the drawn set.
- **`test_w4_selectors.py`**: the overwide-Id refusal happens at 40 rather
  than 44.
- **`test_w15_packaged_no_marker.py`**: selected its rows by the word `open`,
  which no row carries now; it selects by title.
- **`test_w36_msg_my.py`**, **`test_tui_packaged.py`**: column name and
  compact vocabulary.

## Gate

`just test-v11`: **1903 passed**, **1 failed**, serial suites and ACP unaffected.
`tools/codex-event-bridge`: **45 passed**. The whitespace check is clean.

**The one failure is not W73's and not mine to fix under this claim.**
`test_w36_editor_backed_prose.py::test_an_interrupted_editor_restores_the_draft_and_cleans_up`
is a test the W36 review ADDED along with a new clarification in that
finding — an interrupt delivered while the foreground editor runs must be a
safe cancellation rather than escaping and tearing down the TUI. W36 is a
separate Work with changes requested; starting its implementation while
claimed on W73 would be execution without a claim. It fails identically with
W73's changes reverted, so it is not caused by anything here.

## Not done

- Detail and JSON keep the full canonical spellings, unchanged and untested
  here beyond the assertion that they did not move — the ruling scopes this
  Work to the list.
- Nothing deployed. The running set at `/home/sl/baton-v11` is release
  `7bea055` and was not restarted.
