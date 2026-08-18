# Progress

## Step 1 — implementation (2026-08-18)

Four pieces of Console state, all presentation: the bounded `history`
list, a `history_cursor` (None = on the live draft), the `history_draft`
saved before navigation, and `reverse` holding the search query, its
match, and the pre-search draft.

Recording happens in `execute()`, before any refusal path. That is the
single point where "the operator submitted this text" is true — every
one-line submission passes through it, local `filter` included — so
history never has to be inferred from a success status or an authority
event. A refused command is recorded exactly like an accepted one,
because correcting a refusal is the reason the feature exists; deriving
from success would omit the entries most worth recalling.

Up/Down walk older/newer, and Down past the newest restores the saved
draft byte-exactly. Approximate restoration would be worse than none:
the operator cannot see what changed.

`Ctrl-R` opens incremental reverse search. Typing narrows, Backspace
widens, repeated `Ctrl-R` steps to the next older match and stops at the
oldest — no wrap, deliberately, because wrapping hides that the search
has run out. Right and Tab adopt the match into the ordinary buffer
without executing; Enter submits through the existing path; Esc restores
the pre-search draft.

The bar renders the reverse-search prompt with its match while
searching, DIM when nothing matches, with the caret in the query — the
part being edited. Ordinary command rendering, its assistance, and its
horizontal viewport are untouched and simply move under the `else`.

## A contradiction in the contract, resolved toward the ruling

`PLAN.md` says two incompatible things about printable keys during
search:

> Printable input narrows case-sensitively; Backspace widens

> A printable key, Backspace, or Tab likewise adopts the match first and
> then performs the normal editing or completion action

Both cannot hold. I implemented the first, because it is what
`FINDING.md`'s confirmed decision states ("Typing narrows the result")
and because the second makes the feature unusable: if printable input
adopts, there is no way to type a query at all, and `Ctrl-R` degrades to
a plain "recall newest" key.

The "recall, tweak, rerun" workflow the second bullet wants is still
served, through Right or Tab: adopt, then edit in the ordinary buffer
exactly as if the text had been typed. That path is tested directly.
Raised rather than silently chosen.

Tab is accepted as an ADOPT key but calls no completion: W27's Tab verb
does not exist in this tree, and calling an absent method would crash.
Once it lands, the adopted match is an ordinary buffer and completion
applies to it like anything else.

## Step 2 — acceptance

`tests/work/test_w26_command_history.py`, 28 checks: what enters history
(refused, unparseable, cancelled, empty, adjacent-duplicate, the bound
and its eviction end, two-Console isolation); Up/Down (recall, walk,
stop at oldest, byte-exact draft restore, empty history, edit-after-
recall not mutating the stored entry, fresh draft on reopen); reverse
search (narrow, step older, no wrap, widen, no-match, case sensitivity,
Esc restore, Right/Tab adopt without executing, adopted buffer editable,
Enter submits, query never entering history); and that table navigation
and batch line navigation still own their own Up/Down.

One check earns its place separately: navigating and searching must
query the authority ZERO times. History is presentation state, and the
cheapest way for that to stop being true is a well-meaning refresh.

Verified on a real PTY as well as in state, because these are terminal
key sequences: the Up sequence recalls a refused command with its
assistance intact, Ctrl-R plus a query renders the search prompt with
its match, and the Right sequence accepts it back into an ordinary
editable buffer.

Break-sweeps: not recording submissions reds 21; dropping the adjacent
collapse, the draft restore, or case sensitivity each reds exactly its
own check.

## Evidence

- Gate: **1174 passed** + 14 serial + acp 38/38 on 32 cores.
- Whitespace check clean.
- No schema, projection, or public CLI change.

## Step 3 — review round 1 (2026-08-18)

The blocking finding was correct, and the fix was already in the tree
when the review landed: I hit the same defect through W29's gate run and
corrected it there. Enter with no chosen match is inert and stays in
search; Esc still restores the pre-search draft.

The reasoning is worth stating because it is the whole point of the
finding. `_reverse_adopt()` deliberately does nothing when there is no
match, so the buffer still held the draft — and the row was showing the
search prompt. Submitting would have executed text the operator could
not see and had not selected. Refusing visibly is the only reading that
matches what the screen says.

### The terminal coverage the review asked for

Two PTY cases, because the review's point is precisely that the painted
state and the submitted command must not diverge — and only a terminal
can show that:

- `Ctrl-R`, a query matching nothing, Enter: the row STILL shows the
  reverse-search prompt afterwards, the hidden draft is not painted
  back, and the authority's last sequence is unchanged — nothing the
  operator could not see reached it;
- the same sequence followed by Esc: the draft returns exactly.

The authority-sequence assertion is the load-bearing one. A state check
proves `execute()` was not called; only this proves nothing was
committed.

Break-sweep: reverting the guard reds all three — the state check and
both terminal cases.

### The contradictory PLAN clause

Marked superseded in place, per the review, rather than deleted. It said
printable keys and Backspace adopt the match; the bullet above it and
`FINDING.md` both say typing narrows. Recorded why the conflict is not
stylistic: if printable input adopted, no query could ever be typed and
`Ctrl-R` would collapse into a plain "recall newest" key.

### Evidence

- Focused W26: 31 passed (2 of them serial PTY).
- Gate: **1213 passed** + 16 serial + acp 38/38 on 32 cores.
- Whitespace check clean.

## Round 2 — the over-width reverse-search viewport (2026-08-18)

The finding is correct. Reverse search painted `row[:avail]` — the fixed prompt
and the query's OLDEST prefix — and then clamped the terminal caret to the
final cell. Two failures compounding: every character being typed was
off-screen, and the caret claimed an insertion point on unrelated text. The
second half is the worse one, because a wrong caret is not a missing signal but
a false one.

Reverse search now obeys the same viewport rule as ordinary entry, because it
IS ordinary entry: typing appends to the query, so the insertion point is the
query's end, `<` marks the clipped left, and the stored query is never cut — a
wider resize recomputes the viewport from the intact value and shows it whole.

### The ranking, and why the row needed one

Three things compete for one row, so they are ranked rather than balanced.

1. **The identity.** An operator who cannot see `(reverse-i-search)` does not
   know which mode Enter will act in. Ranked first for that reason, and it
   survives the clip.
2. **The live query tail.** The input being edited.
3. **The match.** It is the RESULT; a result that crowds out the input it came
   from is backwards, so it yields the row first.

The ranking is enforced at one place — `room` is computed from the fixed parts
alone, so the query is given its space before the match is considered at all.

At 32 columns the full prompt leaves nine cells, one short of the tail the
regression requires. Rather than shorten the prompt, the separator gives way:
`': ` becomes `':` when there is no match. That space exists to separate the
query from the match, and with no match there is nothing to separate.

Below the width where even the prompt fits, the identity alone paints and the
caret sits at its end. The alternative — a second, shorter spelling of the
prompt — would make the mode unrecognizable exactly when the row is hardest to
read, so it was not taken.

### A redundant branch removed rather than kept

My first version tracked the remaining cells and appended `shown[:rest]`. The
break-sweep that let the match take the row first came back green, which was
the tell: the final paint already clips the row to the cell, so the bookkeeping
said the same thing twice and no test could distinguish the two. It is gone,
and the sweep now targets the ranking where it is actually decided — reserving
the match's length inside `room` — which reds correctly.

### Regressions

Eight added beside the review's own, all in `tests/work/test_w26_command_history.py`:
the caret lands on the last typed character rather than the edge; the clip is
disclosed with `<`; the identity survives the clip; the match is clipped before
the query is; a fitting query and match both paint whole with nothing marked; a
wider resize restores the whole query; a degenerate width keeps the mode
recognizable; and the round-1 DIM no-match distinction survives the viewport.

Break-sweeps: the original defect reds 5; dropping the identity reds 5;
ranking the match above the query reds 1.

### Gate

`just test-v11`: **1227 passed**, 32 serial, ACP 38/38. Clean — the two W47
failures that were red beside this one are fixed under W47 and returned to
review.
