# Progress — implementer (`baton.claude`)

Work `b06383c8-W17`, claimed 2026-08-19. State: **awaiting review**.

## Revalidation against the current tree (2026-08-19)

The FINDING's observation holds exactly as written. `src/baton_work/tui/`
contained no reference to `poke` at all before this change: the primitive
landed with `aba69d0` and the console was never taught about it. The
authority half is sound and untouched here —
`projection.participant_actions` already returns `kind: "poke"` entries for
the exact participant asked, `projection.pokes` already reports each poke,
its derived state and its one terminal answer, and `_poke_state` already
derives `timed-out` at read time. Nothing in this Work adds a delivery path,
a status write, or a second opinion about what "still owed" means.

Two pinned facts were re-checked before being relied on:

- **Confirmed** — the header already reads `participant_actions` for its
  `oblig`/`due` counters, so counting pokes there costs no extra read and
  cannot disagree with `wait`.
- **Confirmed** — expiry is derived, never stored. The console therefore
  reads `pending` rows the projection still holds and calls them what every
  other reader calls them, rather than deciding staleness itself.

## What was implemented

`src/baton_work/tui/app.py` only; no authority, projection, CLI grammar or
JSON change.

1. **The counter.** `[poke:N]` joins `[oblig:] [park:] [due:]` in the header,
   counted from the same participant projection. It is its own counter by
   ruling in the FINDING: folding it into `oblig` would claim an endpoint
   owes something, and folding it into `New` would make a direct question
   look like ambient traffic. It shows `0` as visibly as `3`.
2. **The cue.** While a poke is owed and the operator's own status row is
   free, the bottom row says `N pokes waiting for you — press p`. A counter
   says something is waiting; it does not say what to press. The operator's
   command feedback always outranks it, and on a narrow terminal — where the
   header suffix clips exactly as `due` already does — this row is what
   still carries the cue.
3. **The view (`p`).** A mode of its own, because a poke is addressed to a
   participant and not to Work: it opens from an empty table too. Rows are
   the pokes asked OF this participant and the ones they asked, owed first
   and then newest-first. Each row carries the action as TEXT (`answer`,
   `withdraw`) beside the canonical state — W228's ruling that an actionable
   row must be legible without colour, blink or bold alone — plus which end
   of the conversation this participant is on, the instant, and the
   question. The block beneath shows the chosen poke whole: request,
   deadline, and its one terminal answer with the agent's own words.
4. **Answering.** `a` opens a one-row chooser whose vocabulary comes from
   the CLI grammar's own `state=` values, so a later state appears without a
   second list to edit; the digit is positional so two states sharing an
   initial cannot collide. The explanation is authored in `EDITOR` through
   W36's existing round trip. The composed command carries the selected
   poke's sequence, which is the whole defect: nothing is copied out of JSON.
5. **Withdrawing.** `x` runs `poke-cancel` with an authored reason.
   Presentation decides only what it can know for certain — a terminal poke
   can never be withdrawn — and leaves WHO may withdraw (the asker, or a
   config-capability holder) to the authority's own refusal.
6. **Bounds, disclosed.** The history page is bounded (`POKE_PAGE`) and says
   so when full; the OWED set never comes from it, so a window of old
   answered pokes can never hide an unanswered question. A detail block
   clipped by a short terminal says how many lines it did not paint.

Both actions run through the same public CLI entry, refusals and
committed-only refresh the typed bar uses. When there is no usable `EDITOR`
the composed command — sequence and state already filled in — is handed back
to the command bar rather than dropped.

## Decisions taken here, for review

- **The `state=` chooser rather than a grammar change.** `poke-answer
  explanation=` is durable human prose and is the only such operand in the
  grammar not marked `prose=True`. Marking it would have routed the answer
  through W36's `missing_prose_operand` automatically — but it would also
  have changed `tests/work/test_w36_editor_backed_prose.py`'s exact prose-name
  set, which is an existing test's assertion and needs Slawomir's explicit
  confirmation under `AGENTS.md`. The console composes the round trip itself
  instead, which changes no CLI or JSON semantics at all. **Open:** whether
  `explanation` should carry the flag is a real grammar question and is left
  to review rather than decided here.
- **Digits for the chooser**, not initials: `working` and `waiting` share a
  first letter, and a positional key survives a vocabulary that grows.
- **`Do` before `State`.** Two different facts, both shown; the action cue
  never borrows a word from the canonical vocabulary.

## Tests

`tests/work/test_w17_poke_visibility.py` — 31 focused cases covering the
acceptance boundary: the summary cue and its personal scope, the counter's
separation from obligation and New counters (asserted against unchanged
`obligations` and `tree` reads), the list and its detail, the response flow
including the chooser vocabulary, cancellation, the no-editor and
empty-prose refusals, withdrawal, each of the four terminal states ceasing
to be owed while staying visible, multiple pending pokes, a full history
window, selection stability across a refresh, narrow and short terminals,
and one real-pty run driving `p` end to end.

## Operational finding for review — NOT fixed here

The `poke` primitive shipped in `aba69d0` with **no documentation at all**:
before this change `poke`, `pokes`, `poke-answer` and `poke-cancel` appeared
in no file under `docs/`, and `docs/BATON-WORK.md`'s `wait` paragraph listed
three actionable kinds where the projection returns four. This Work's own
console paragraph and that one correction are in, because the console text
could not be written truthfully around the gap — but the primitive's own
operator documentation is W5's scope, not W17's, and is still missing. It is
reported here rather than absorbed silently.

## Response to review `review-2026-08-19T05-10-20Z.md` (changes requested)

**R1 accepted in full; the defect was real and the reviewer's reading of it
is exact.** `projection.pokes` pages in canonical ascending sequence, so
`after=0, limit=POKE_PAGE` returned the OLDEST hundred rows. Sorting that
page newest-first produced a window that *looked* recent and was not, and
the disclosure I wrote — `oldest beyond 100 not shown` — described the
opposite end from the one actually dropped. A false disclosure is worse than
none, because it is believed. I knew the read was ascending when I designed
this and drew the wrong conclusion from it; the owed set was protected and
the history was not.

Fixed by making the window the newest **in fact rather than by assumption**:

- `_poke_window(side)` walks the narrowing forward to its end and keeps only
  the tail (`POKE_PAGE` rows), so memory is the window and not the history.
  `POKE_FETCH` (500) is deliberately larger than the kept window because the
  walk's cost is the number of PAGES — and the walk happens only while the
  poke view is open; nothing else in the console reads this projection.
- Both narrowings go through that one helper, so `target=` and `asker=` can
  no longer differ. The sent-poke window matters on its own: it is where
  withdrawal is offered.
- The self-poke — the only row appearing in BOTH narrowings, and the
  authority's deliberate end-to-end diagnostic — is counted once. Each walk
  returns a `mutual` count so the merged total is distinct pokes, not a
  double count that would invent omitted rows.
- The disclosure now states the exact number of distinct older pokes left
  out (`N older not shown`) and says **nothing at all** when the window
  holds everything.

The owed set is unchanged and still comes from `participant_actions`, so no
bound here can hide an unanswered question — that part of R1's reasoning
held and is now belt-and-braces rather than load-bearing.

Six tests were added beside the reviewer's regression, covering what R1
asked for: the `asker=` window, the multi-page walk itself (with
`POKE_FETCH`/`POKE_PAGE` patched small, since a single large fetch would
prove nothing about the loop), the exact omission count, the
nothing-omitted case, and the self-poke merge boundary in both the empty and
the full-window cases. No existing assertion was edited or weakened.

**Considered and not done:** adding a `newest=`/`before=` operand to
`projection.pokes`, mirroring `thread`'s existing paging idiom. That is the
durable fix and it belongs to the projection surface — but it changes the
JSON contract and its version, and this Work's acceptance boundary is
presentation. Raised here for the reviewer rather than taken unilaterally.

State: **awaiting review** (second round).

## Verification

Round 1 (2026-08-19, before review): focused suite 31 passed; `just test-v11`
exited 0 — 1943 parallel, 40 serial, 44 ACP.

Round 2 (2026-08-19, after R1): the reviewer's regression
`test_a_full_history_window_keeps_the_newest_terminal_pokes` was reproduced
red on the returned tree, then made green by the fix rather than by touching
the test.

- Focused: `.venv/bin/python -m pytest tests/work/test_w17_poke_visibility.py`
  — **38 passed** (31 original, the reviewer's regression, six added for the
  coverage R1 named), including one real-pty run.
- The complete v11 gate, `just test-v11`, exits 0 on this tree:
  **1950 passed** (parallel, `-m "not serial"`), **40 passed** (serial), and
  the external ACP bridge acceptance **44 pass / 0 fail**.

Nothing in this Work was verified by inspection alone.
