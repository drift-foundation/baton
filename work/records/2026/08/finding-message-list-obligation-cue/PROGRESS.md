# Progress

**Implemented by `baton.claude` and returned to `baton.bug` for independent
review on 2026-08-18.** One additive projection field; no schema change, no
change to obligation authority or Message seen semantics.

## Revalidation

A projected Message row carried `seq`, `author_team`, `author`, `body`, `ts`,
`new` and `references` — and nothing about obligations. So the cue could not be
presentation-only: the finding forbids inventing an obligation from a directed
Message, and the only canonical source was the obligations table.

The `obligations` table is keyed by `message_seq`, so the join the cue needs
already exists; nothing had to be recorded that the authority was not already
keeping.

## What changed

**Projection.** `thread()` message rows carry `owed`: null, or the viewer's
pending obligation created by that Message — its seq, the owed endpoint, the
flavor, and the declared completion verbs. Viewer-relative in the same way
every other actionable fact is: the obligation's endpoint must currently
resolve to this member. One batched statement per page, not one per row.

**One definition of the completion verbs.** The expression
`["respond","dispose","accept"] if flavor == "response" else ["report"]`
already existed in two projections, and the cue would have been a third copy —
three places to disagree about what an agent is allowed to do. It is now
`completes_by(flavor)`, stated once.

**Index column.** `Do` shows `@<seq>`. It went in through the seam W49 left:
one entry in `MESSAGE_COLUMNS`, one position in `MESSAGE_DROP_ORDER`, no change
to the painter. It sits second in the visual order and drops last of the
optional fields, because an owed action is the reason to act on the row at all.
The cue is TEXT carrying the sequence, so it is legible without colour, blink
or bold — and a glyph alone could not have said WHICH obligation.

**Selected row.** The reader block states the obligation, its endpoint, and one
ready-to-edit command per completion verb.

## The command guidance comes from the CLI's own grammar

A bare `verb obligation=N` looked right and would have refused for two of the
three verbs: `respond` needs a body, `dispose` a disposition, `accept` a
provider. The finding asks for "enough command context to act without
consulting JSON", and advice that does not work is worse than none.

Each verb's required operands are read from `cli.GRAMMAR` rather than copied
here, so a grammar change cannot leave this line quietly advertising a command
that refuses. `accept`'s provider is the one exception and is marked as such in
the code: it is an exactly-one-of rule, which the `required` flags cannot
express.

## Regressions

`tests/work/test_w228_message_obligation_cue.py` (27 tests): the projection
(one and many pending obligations, foreign obligations, a SAME-TEAM member the
endpoint does not resolve, each of the three terminal actions clearing the cue
while the Message remains, a terminal close withdrawing it, and one read per
page); the index cue (naming the obligation, absent on ordinary Messages,
legible as text, foreign rows unmarked, surviving seven widths, disappearing on
refresh, and leaving order and seen state untouched); the selected row (the
commands, every required operand, and silence when nothing is owed); parity
against the `obligations` verb; and a real-terminal test of cue and guidance
together.

## Break-sweeps

| Reintroduced defect | Result |
| --- | --- |
| Infer the cue from a directed Message rather than pending state | 7 red |
| Drop the viewer-relative handler filter | **green — then 1 red** |
| `Do` drops first instead of last | 12 red (with W49) |
| Bare verb hints without required operands | 2 red |

The second sweep is the one worth recording. My fixture had one member per
team, so a foreign obligation was already excluded by the TEAM check and the
handler check never did any work — two guards overlapping, only one tested. The
fixture now has a second `lang` member the route does not resolve, which is the
case the handler check exists for, and the sweep reds.

## Composition with W49

W49 is in review, and this Work changes what its tests assert — the same
one-tree coupling W154 and W155 had. Its width matrix, its dropped-field case
and its column-set test moved to the composed layout, each with the reason at
the assertion.

Its `test_this_work_adds_no_obligation_cue` was a scope boundary, true until
this Work took the seam. It is replaced by
`test_the_cue_is_absent_when_nothing_is_owed`, which keeps the half that still
means something: the column is empty unless the viewer actually owes an action,
so `Do` never becomes decoration. W49's seam test now also proves the seam
still works for the NEXT column.

## Gate

`just test-v11` at implementation: **1635 passed**, serial **38 passed**, ACP
**41/41**. Re-run at R1 return against the current tree (which other Works have
grown since): **1734 passed**, serial **40 passed**, ACP **41/41**.

## R1 — 2026-08-18, `baton.claude`

`baton.codex` reviewed at seq 301 and added one regression,
`test_the_row_never_truncates_a_large_obligation_selector`. The test was
correct and the defect it named was real.

**The defect.** `Do` was declared at a fixed four cells, so an obligation at
`@1000` rendered as `@100`. That is not a clipped cue — it is a *different*
obligation, and the terminal verbs are typed at whatever selector the row
displays. An operator following the row would have acted on the wrong
obligation with no indication anything had been dropped. Strictly worse than
showing nothing.

**Why it is recorded rather than quietly fixed.** W49 sized `Id` from the page
for exactly this reason and I wrote the sentence justifying it — "never clips
that local selector merely because its sequence crossed a decimal boundary."
Then I added a second selector column one position over and gave it a
constant. The reasoning was already in the file, in the function immediately
above, and I did not carry it across. The guard against that is a sweep in
both directions whenever a Work adds a field beside an existing one: ask what
the neighbour already had to solve.

**The fix.** `message_cue_width(messages)` mirrors `message_id_width`: the
longest visible `@<seq>`, never narrower than its heading, shared by every row
in one paint. `message_columns` takes it as a `cue_width` argument where the
declared width is now a **minimum, not a cap**. Covered at every decimal
boundary from 7 to 999999, plus a page mixing a two-digit and a four-digit cue
to prove the allocation is shared across the page rather than computed per row.

**Break-sweep.** Restoring the fixed width reds 3 —
`test_the_row_never_truncates_a_large_obligation_selector` and both
`test_the_cue_column_grows_with_the_sequence` cases. Re-run against the
current tree at return time, not just when the fix landed.

**One repair to the reviewer's test, which the reviewer should check.** Its
tail referenced `asked` and `_cell` from another test in the file and raised
`NameError` before reaching its own assertion — so it failed, but for the
wrong reason, and never actually exercised the truncation until the
`NameError` was removed. The reviewer's assertion is kept verbatim, with the
heading-alignment check added beside it. The property the copied tail appears
to have meant is already held by `test_the_row_names_the_obligation`.

**Return.** Review seq 310 correctly observed that the fix was in the tree
while W228 was still routed to `baton.impl` with no return event after seq
301 — my seq 311 message said "W228 stays with you" but a Message is not a
transition, and the Work sat unclaimed instead of being returned. Claimed and
returned authoritatively to `baton.bug` this time.
