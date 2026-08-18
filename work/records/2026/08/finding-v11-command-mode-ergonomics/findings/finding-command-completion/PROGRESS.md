# Progress

## 2026-08-18 — `baton.claude` (implementer)

Implemented as W27. Schema and canonical grammar unchanged; the completion
result is analyzer-side and the bar spends it by typing.

### Revalidation against the current tree

The plan's five revalidation claims were re-read against the code rather than
trusted, and all five held: `analyze_partial()` already owns the quote-aware
`_partial_tokens()` interpretation; `assist_text()` is a pure formatter over
it; `_command_key()` had no Tab meaning; and both `_reconcile_say_seed()` and
the `filter` seed fire on *reaching* a state, not on parsing a submitted line.

### What was built

- **`cli.complete_partial(buffer)`** — one pure function beside the grammar,
  returning `{"buffer", "progressed", "candidates"}`. It reuses
  `analyze_partial()`'s state rather than re-tokenizing, and adds
  `_common_prefix()` for the deterministic longest-common-prefix rule. Per
  state: `commands`/`verbs` complete with delimiter `" "`, `values` complete
  the text after `=` with `" "`, `operands` complete with delimiter `""`
  (the candidate already carries its `=`).
- **The effective candidate set**, not the raw `key_matches`: intersected with
  (`required` ∪ `optional` ∪ the names of any `exactly-one` heading that has
  not yet been chosen), so a supplied singular key, a conditionally forbidden
  key, and the unchosen alternative of a satisfied `exactly-one` are all
  absent. Completing to any of them would be completing to a parser refusal.
- **`Console._complete_command()`** — applies the result by *typing* the
  remaining characters through `_command_type()`, stopping if a transition
  rewrites the buffer. This is what preserves the `say` and `filter` seeds:
  assigning the finished string would step over the exact moments those
  transitions watch for.
- **Tab in `_command_key`**, and in `_reverse_key` as `_reverse_adopt()` then
  `_complete_command()`, so W26 search-to-completion is one gesture.

### Regressions — `tests/work/test_w27_command_completion.py`, 33 tests

Analyzer, Console state, purity, and two real-PTY cases. The purity test
digests the database file and compares `last_seq()` across a Tab sequence.

### Break-sweeps

| sweep | defect reintroduced | result |
|---|---|---|
| A | pick the first candidate instead of the common prefix | 2 red |
| B | ignore the effective set, offer raw `key_matches` | 2 red |
| C | assign the completed buffer instead of typing it | 2 red |
| D | remove the `open_quote` early return | **1 red** |

**Sweep D was green on the first attempt, and that was a fault in my tests,
not evidence the guard was dead.** I had assumed the `diagnostic` branch
already caught quoted input. Probing instead of assuming disproved it — every
quoted case I tried returns `open_quote=True` with state `operands`, e.g.

    'close "ou'            tokens=(['close'], 'ou', True)   state=operands
    "close 'outcome=sat"   tokens=(['close'], 'outcome=sat', True) state=operands

My original two cases simply happened to make no progress anyway, so removing
the guard changed nothing about them. `close "ou` is the reachable case: its
live token is a unique prefix of `outcome=`, so without the guard completion
writes `close "outcome=` and strands a quote it would have to reopen.
`test_an_open_quote_is_never_rewritten` is now parametrized over both the
diagnostic-caught pair and the two that reach the guard, and sweep D reds.

### Gate

`just test-v11` green — 1734 parallel, 40 serial, 41 `test-acp`. The
`tools/codex-event-bridge` suite is green at 44.

### Handed to review

`pass work=W27 to=baton.feat`.
