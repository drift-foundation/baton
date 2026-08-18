# Plan

**Status — independently signed off 2026-08-18.** No schema or canonical
grammar change. All five plan steps are complete; see `PROGRESS.md` for the
break-sweep table and `review-2026-08-18T20-53-53Z.md` for review evidence.

## Revalidation — 2026-08-18

- `cli.analyze_partial()` already owns the quote-aware `_partial_tokens()`
  interpretation and returns structured verb, key-prefix, and closed-value
  matches from `GRAMMAR`. `tui.assist_text()` is only a formatter over that
  state. Completion must extend the analyzer's structured result with an
  effective candidate set and live-token replacement span; curses must not
  inspect `GRAMMAR` or tokenize independently.
- The raw `key_matches` list is not by itself sufficient. Effective candidates
  must exclude already supplied singular and conditionally forbidden keys,
  retain repeatable keys, and include applicable `exactly-one` choices such as
  `accept create=` / `into=`. The same condition pass that produces visible
  assistance owns this answer.
- `_command_key()` has no Tab meaning today. Completion edits only the live
  final token at the end of the one-line bar; it does not introduce general
  mid-line cursor editing or change `::` batch input.
- Two existing command-bar behaviors are triggered by reaching an exact verb,
  not by parsing the final submitted line: `_reconcile_say_seed()` inserts the
  selected `thread=`, and the first literal space after `filter` seeds the
  active filter clauses. Verb completion must pass through those same state
  transitions. `sa<Tab>` may not produce an unseeded `say `, and `fi<Tab>` may
  not bypass editable current-filter seeding.

## Bounded implementation contract

- Add one pure analyzer-side completion result containing the unchanged or
  completed buffer, whether progress occurred, and the canonical candidate
  list. Use deterministic longest-common-prefix behavior; equality with a
  unique candidate appends its ruled delimiter (` ` for verbs/values, `=` for
  keys).
- Operate on Unicode strings but restrict candidates to canonical grammar
  spellings. Preserve the raw prefix before the live token byte-for-byte;
  refuse/no-op inside an open quoted value rather than rewriting its quoting.
- An ambiguous candidate set never cycles by repeated Tab. First and repeated
  Tab make only common-prefix progress; when no progress is possible the
  existing assist line remains the candidate display.
- Diagnostics, a trailing escape, dynamic values, and a line with no matching
  candidate leave the buffer and caret unchanged. Completion schedules no
  refresh and performs no authority/config/filesystem read.
- When W26 reverse search is active, Tab first adopts the displayed history
  match into the normal buffer and then runs this same completion operation.

1. Extend the shared partial analyzer with enough token-span/candidate data for
   editing, rather than re-tokenizing or copying grammar metadata in curses.
2. Implement deterministic common-prefix completion for verbs, operand names,
   and closed-vocabulary values in the one-line `:` bar.
3. Preserve the selected-Thread `say` seed, quoted values, embedded `=`, the
   visible caret/viewport, and the existing diagnostic/assistance behavior.
4. Add analyzer, state, virtual-screen, and real-PTY regressions for unique,
   ambiguous, invalid, quoted, narrow, resized, and cancelled completion, plus
   proof that Tab performs no authority read or mutation.
5. Cover supplied-singular exclusion, repeatable keys, conditional and
   exactly-one forms, unique exact candidate delimiters, no-progress repeated
   Tab, contextual `say`, active `filter`, W26 search-to-completion, and batch
   isolation.
