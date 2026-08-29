# Progress

`PROGRESS.md` has one writer: the implementer (`baton.claude`).

## 2026-08-27 — claimed; PLAN 4, the authority half

Claimed W26328 at seq 27770. PLAN 1–3 were the reviewer's; PLAN 4 is the
implementation and PLAN 5 the independent review this Work is passed back for.

### Revalidating the pinned decisions against the tree

Every pinned decision was re-read against the current source rather than
carried forward from the dossier. Two mattered:

- the approved contract narrows the mandatory `Mine` column to the **ordinary
  Jobs containment tree**, and the tree is exactly where the finding's defect
  bites — the window is three levels deep, so a claimable Job on the fourth
  has no row at all;
- `PROJECTION_VERSION` had already moved to 12.6 under W24755, so this Work
  rolls it to **12.7** rather than to the 12.6 the dossier names.

### The counting predicate is narrower than every neighbour

This repository already has four predicates that look like "actionable", and
none of them is this one:

| where | what it answers |
| --- | --- |
| the TUI's bold Title | also the viewer's own claims and directed `@` obligations, blocked Work included |
| `participant_actions` | deliberately REDELIVERS the viewer's claimed Work, for restart recovery |
| `_first_actionable` | the right predicate, and answers exactly one row |
| W2938 pickup | one participant-level obligation, on Teams, however many Jobs |

W26328 counts Work the viewer could claim RIGHT NOW: open, ready, queued,
unclaimed, and whose exact current Route — including an explicitly selected
alternate — resolves to them. The bold Title rule is UNTOUCHED beside it, and
that is deliberate: the two answer different questions and merging them would
have silently widened the count.

### What was built

`projection.py` grows `_claimable` (the predicate, resolved through the same
endpoint answer the claim authorizes against), `_actionable_rollup` (the
containment count, walking parents with a cycle guard) and `actionable_work`
(the flat, paged, all-team window). Tree rows and active-trail rows carry
`viewer_actionable` and `actionable_descendants`; the tree response carries
`actionable_for_viewer`. The `actionable-work` verb exposes the flat window
through the ordinary grammar, and `EFFECTIVE-BATON.md` gains a section.

### Measured, not read

Harness: `evidence/w26328-mutation-harness.py`. Twelve mutations of the
derivation, each reverted before the next.

**10 of 12 caught.** Two are expected-unseen and named in the harness: with
`phase='queued'` present, removing `handler_team IS NULL` changes nothing,
because W38 makes `active` hold exactly when a Handler does; and with
`ready=1` present, removing `status='open'` changes nothing, because closing
always clears readiness. Both are the finding's predicate written literally,
and `TestThePredicateRestsOnInvariantsThisSuiteChecks` asserts the two
invariants they lean on — so if either stops holding, that case fails rather
than the count quietly drifting.

Six guards were UNESTABLISHED when first measured and are now observed: the
trail roll-up, the flattened view's own predicate, the selected-route reroute,
and a statement bound that was measuring `tree` overall (95 statements against
983) rather than the two functions it claimed to bound.

## State

PLAN 4 authority half done. Console half next.

## 2026-08-27 — PLAN 4, the console half

Evidence: `evidence/w26328-2026-08-27-console.txt`.
Harnesses: `evidence/w26328-mutation-harness.py` (authority),
`evidence/w26328-console-mutation-harness.py` (console).
No Git history or index was mutated.

### Three surfaces, three different jobs

`[Jobs N]` is the total and is ALWAYS spelled, `[Jobs 0]` included. A tab that
went blank at zero is indistinguishable from a build that never carried the
count, so an operator could not tell "nothing is waiting for you" from "this
console does not say". It is a NUMBER rather than the `*` W167 and W2938 use,
because the question here is how much and theirs is whether — and it is read
from the SAME cached window the rows come from, so the header and the table
cannot describe two authority states.

`Mine` is where it is, on the tree the operator is actually reading:
blank / `me` / `+N` / `me+N`. It is MANDATORY — not in `COLUMNS`, not in
`DROP_ORDER`, and carried in the identity allocation beside `Id`. A responsive
column is one you can do without at narrow widths, and the widths where "is
any of this mine" matters most are exactly the ones that would have dropped
it. It never clips either: `me+12` widens the column, because a clipped count
is a smaller NUMBER rather than a visibly cut one.

`m` opens the flattened all-team `Awaiting me` page: every Work awaiting this
participant, independent of the current root, each entry its Id and its
COMPLETE containment path. The path WRAPS rather than truncating. Every other
bounded cell in this console clips, and that is right for them — a clipped
Title is still a Title and the Id beside it is the identity. A clipped path is
a DIFFERENT path, and there is no second copy of it on the line.

### What the console half changed under it, and why

- **W167's whole-bar digit sweep is narrowed to the Inbox label.** Its case
  asserted `not any(character.isdigit() for character in bar)` over the entire
  tab row. W167's ruling is about the Inbox label — `total/unseen` emphasised
  unreadness where the question is whether you owe anything — and it never
  ruled that no tab may carry a count. Left as written it would have forbidden
  this one, so the sweep now runs over the label it was always about. Stated
  here rather than quietly deleted.
- **The parity parser learned the new field.** It decodes columns from the
  PAINTED HEADER, and a mandatory field it did not know about was being read
  as part of `Wait`. It now reads `Mine` the same way and COMPARES it to
  `app.mine_cell` of the JSON row — so a console that computed its own
  claimability would fail parity rather than merely look plausible.
- **`m mine` is appended AFTER `[d] deps` in the footer.** W17 rules that the
  deps label survives whole at 60 columns; the footer clips at the terminal
  width, so a hint inserted ahead of it would have pushed a ruled one off
  screen at exactly the width where it was ruled to be present.
- **The contextual Work page's `[Jobs]` is unchanged.** That label means "this
  Work rendered as the tree root", not the global Jobs tab, so a global count
  on it would answer a question the page is not asking. Three existing suites
  already assert its exact spelling, and they still do.

### Measured, not read

Twenty-one console mutations, each reverted before the next, over the new
suite plus parity and the four tab-grammar/navigation suites this touches.

**21 of 21 caught, none expected-unseen.** The one that was UNSEEN on the first
run is worth naming: removing `mine_page` from the captured navigation state
changed nothing, because nothing on the ordinary Enter/Back path disturbs the
page number — so the case guarding it would have passed for a console that
captured no page at all. The case now walks the path that DOES move it (page
two, open a Work, reach that Work's own Jobs tab, open `Awaiting me` again at
page one, walk back out), and the mutation is caught.

### Gates

- the two new suites — 64 cases, green
- full v11 gate — **3226 parallel passed, 54 serial passed, ACP 77 pass / 0 fail**
- authority measurement re-run on the final tree: **10 of 12**, the same two
  expected-unseen

## State

PLAN 4 done. Passed for independent review rather than closed.

### For review

- **The count is the team-wide total at every root.** Re-rooted three levels
  down, `[Jobs N]` still spells everything awaiting you rather than what is
  under the current root. That is what makes it a discovery cue; if the
  reviewer's judgement is that it should be scoped, that is a different
  contract than the one the dossier pins.
- **`Awaiting me` ignores `z` and the Jobs filter, deliberately.** A closed
  Work is never claimable and a filtered-out one is still awaiting you, so
  honouring either would let view state the operator set for a different
  question hide the Work this page exists to surface. I expected this to be
  unmeasurable — the filter it would have to honour does not exist in this
  code — and I was wrong: injecting one into `mine_rows` is caught by four
  cases. Recorded because the measurement, not my reading, is what settled it.
- **The `Mine` roll-up counts through containment only.** Dependency edges are
  not descent; a blocker two graph hops away is not "below" anything. `[d]`
  is still where that question is answered.

## 2026-08-28 — the independent review's [P1] and [P2], corrected

Claimed W26328 at seq 30646. Evidence:
`evidence/w26328-2026-08-28-review-corrections.txt`. The reviewer's
`evidence/w26328-review-pagination.py` is kept byte-for-byte; the corrected
companion is `evidence/w26328-corrected-pagination.py`.
No Git history or index was mutated.

### Both defects were reproduced on the tree before anything was changed

The reviewer's file runs and prints the skip: page one `W2 W3`, W2 claimed,
page two `W5` — and `W4`, still actionable, in no page at all. The narrow
refusal was reproduced the same way, by reading what it actually draws: at the
widest refusing width it said `need 29 cells` for a table that needs 35.

### [P1] The continuation is a POSITION, and the order had to be total first

`next_after` was `start + len(page)` and the next page was a slice of the set
as it stands THEN. Those are two different sets whenever anything happens
between two reads, which on a shared Route is the ordinary case rather than a
race to be tolerated — so every row after a departed one slid one place
forward and the second slice began one row too late.

`actionable_work` now walks a keyset. `projection.py` names the two rank
expressions `WORK_ORDER` is built from once, publishes them as
`WORK_ORDER_KEY` columns so the position is SELECTED rather than recomputed in
Python beside the SQL, and orders by `WORK_ORDER_TOTAL`.

**The tie-break is the part worth pinning.** A cursor compares positions, so
an order that calls two rows equal is an order a page can skip or repeat
across. `WORK_ORDER` stops at `created_seq`, and no mint produces a tie today
only because the identity is minted FROM that sequence. That is a fact about
how ids are spelled, and the cursor depends on the ORDERING — so the identity
is the final tie-break now, which refines the canonical order and can never
reorder it. The regression for it constructs a tie directly, and says so: the
guarantee is a property of the ordering rather than of today's mint.

**A token this authority did not mint is refused, not rounded to page one.**
That was the tempting shortcut and it is the same defect in different clothes:
the client believes it walked past a boundary it was actually sent back
behind. The scheme tag is checked first, so a later position shape refuses an
old token rather than misreading it.

The CLI declares `after=` a string with no default — it was declared `int`,
which both invited the arithmetic and made the grammar itself a place the
opaque contract could be contradicted. The TUI holds `mine_after` as
`str | None` and never reads, increments or invents one. `EFFECTIVE-BATON.md`
loses the `after=25` example and states the pass-through rule and why it
holds.

### [P2] The refusal names a width that works, and it is the smallest one

`layout_minimum` derives the number from `layout_fits`' own expression against
the same lead the failing judgment was given, so the mandatory `Mine`
allocation and the wait cue are counted because they were counted there. It is
EXACT, not merely sufficient: a number safely above the requirement would
satisfy the review's letter while telling an operator to surrender cells the
table does not need, and a mutation asserts that too.

### Why thirty-three caught mutations missed both defects

Worth stating, because it is about what was chosen to break rather than how
much:

- **No mutation moved the set between two pages.** Every paging case walked an
  undisturbed set, where an offset and a position are the same answer.
  `test_paging_traverses_every_match_once` is a real case and it PASSES on the
  defective code. The defect exists only at the boundary between two reads and
  no case crossed one.
- **The narrow cases asked whether the table refused, never what it said.**
  `test_no_width_that_draws_a_table_drops_it` explicitly skips the widths
  where the refusal is drawn, so the one line carrying the number was never
  read. The refusal was measured as a behaviour and never as a statement, and
  the whole defect was in the statement.

### Measured, not read

- authority: **16 of 18 caught**, the same two expected-unseen and still named
- console: **27 of 27 caught**, none expected-unseen
- against the PRE-FIX source: 15 of the 17 new authority cases fail, and 2 of
  the 3 new console cases fail. The four that pass either way are boundary
  guards rather than the defect, and are named in the evidence rather than
  counted.

**A test that hung rather than failed.** The first corrected harness run did
not finish: the "continuation is ignored" mutation makes `next_after` never
`None`, so the walk looped and the harness aborted on its own 900-second
subprocess timeout. The source was restored by its `finally` and that was
verified before continuing. Both walks now go through one bounded `walk()`
helper whose page bound is its own assertion — an unbounded walk over a
continuation does not fail when the continuation stops advancing, it hangs,
and a suite that hangs reports nothing. That was loop control added to an
existing case, not a change to an assertion it makes.

### Gates

- the two focused suites — 84 cases, green (64 before)
- full v11 gate — **3272 parallel passed, 54 serial passed, ACP 89 pass / 0 fail**

## State

The reviewed [P1] and [P2] are corrected and measured. Passed back for
independent review rather than closed.

### For review

- **The refusal sentence itself still truncates on a very narrow terminal.**
  It is drawn with `addnstr` at `width - 1`, so below about twenty-one columns
  the message is cut and below about twenty-nine the number goes with it. That
  is pre-existing presentation, it is not what [P2] raised, and widening or
  wrapping it is a question this Work did not open. Named rather than quietly
  fixed or quietly ignored.
- **A row whose own rank changes across a page boundary is the one case the
  cursor cannot follow.** It moved, so continuing past its old position would
  mean something different. The contract already names deliberate refresh as
  the path for a snapshot that has moved, and that is what this rests on; if
  the reviewer's judgement is that reprioritization needs more than that, it
  is a contract question rather than an implementation one.
- **`WORK_ORDER_TOTAL` is a new shared name in `projection.py` and only
  `actionable_work` uses it.** Every other reader still uses `WORK_ORDER`
  unchanged, deliberately: adding the tie-break globally would be a change to
  the canonical order's SQL on every list in the repository, measured by
  nothing here.

## 2026-08-28 — the re-review's [P1], corrected

Claimed W26328 at seq 31000. Evidence:
`evidence/w26328-corrected-forged-cursor.py`. The reviewer's
`evidence/w26328-review-forged-cursor.py` is kept byte-for-byte.
No Git history or index was mutated.

### Reproduced first, and the finding is fair

The reviewer's file runs and prints it: a token composed by hand with ranks 99,
sequence 999999999 and the id `not-this-authority-W999999999` is accepted, and
the page comes back empty while `fefefefe-W2` is still actionable.

The uncomfortable part is that the previous round RECORDED a decision that a
token this authority did not mint is refused, and then checked only that it
decoded and carried the scheme tag. The decision was true of one member of the
token and false of everything else in it. I wrote that sentence believing it
described the code, which is the failure mode the whole "measured, not read"
discipline exists for — and no mutation caught it because every mutation I
wrote broke a rule that was there rather than asserting one that was not.

### The binding, and the thing it must not break

`_cursor_bound` runs inside the read snapshot and proves the token's named Work
exists and that its CURRENT total-order position is the one the token names.
Refusal names the refresh.

**The lookup is over `work`, deliberately, and that is the load-bearing
choice.** A claim or a reroute moves a row out of the actionable set without
moving it in the canonical order, so continuing after it means exactly what it
meant — the ordinary case the first [P1] correction exists for. A binding
written against claimability would pass every forged-cursor case and break that
one, so a mutation makes exactly that mistake; it is caught by the ORDINARY
continuation cases, not by the new ones, which is the shape of the risk.

### A consequence that narrows the accepted case, named rather than hidden

The blocking preference is part of the canonical order and one of its clauses
is `handler_team IS NULL`. So a cursor row that was holding somebody up ranks 0
while unclaimed and 1 once claimed: on that one kind of row an ordinary
shared-route claim genuinely MOVES the position, and the continuation is now
refused instead of followed.

That is a real narrowing of the inter-page claim case the first correction was
about, and it has its own named case rather than being left to surface as a
surprise. It narrows toward the honest answer — continuing past a position a
row no longer occupies skips or repeats the rows between the two places, and a
client cannot detect either — but the reviewer should see it stated, because
the required correction and the previously accepted behaviour meet exactly
here.

Closing the cursor row, by contrast, does NOT move it when it has no open
dependents, so that continuation stays valid. It has its own case because it
reads like it should refuse.

### Measured, not read

- **20 of 22 caught**, the same two expected-unseen. Four added: never bound at
  all; looked up but the position not compared; a cursor naming no Work
  followed; and the binding written against the actionable set.
- against the PRE-FIX source: **4 of the 6 new cases fail**. The two that pass
  are the must-still-continue guards, which hold either way by design and are
  named rather than counted.

### Gates

- the two focused suites — 90 cases, green (84 before)
- full v11 gate — **3278 parallel passed, 54 serial passed, ACP 89 pass / 0 fail**
- `evidence/w26328-corrected-forged-cursor.py` and
  `evidence/w26328-corrected-pagination.py` — both OK, exit 0
- the reviewer's `w26328-review-forged-cursor.py` now raises the refusal where
  it asserted an empty page, which is the correction landing

## State

The re-reviewed [P1] is corrected and measured. Passed back for independent
review rather than closed.

### For review

- **An ordinary claim of a BLOCKING cursor row now refuses.** Named above and
  covered by `test_claiming_a_BLOCKING_cursor_row_moves_it_and_refuses`. The
  required correction says a changed position must be refused; the previously
  accepted correction says an inter-page claim must continue. On a blocking row
  those are the same event, and this implementation follows the required
  correction. If that is the wrong trade, the alternative is binding to the
  immutable part of the position only — and that reintroduces silent skipping
  when the blocking rank moves, which is why it was not chosen.
- **The refusal is a `WorkError`, the same shape every other pagination refusal
  in this projection uses.** No new taxonomy, and no client has to distinguish
  it from a malformed token except by reading the message.

## 2026-08-28 — the third review's [P1], corrected

Claimed W26328 at seq 31306. Evidence:
`evidence/w26328-corrected-cross-view.py`. The reviewer's
`evidence/w26328-review-cross-view-cursor.py` is kept byte-for-byte.
No Git history or index was mutated.

### Reproduced first

The reviewer's file runs and prints it: Grace's page `['W4']`, Ada's actionable
set `['W2', 'W3']`, and Ada through Grace's cursor `[]`. The token is genuine,
minted by this authority, and unedited — which is why the row binding from the
previous round does nothing about it.

### The correction, and the two choices inside it

The token carries the resolved viewer under a bumped `w2` scheme, and
`_cursor_view` compares it.

**The scheme had to move with the shape.** A `w1` token names a position and no
viewer, so reading one as current would strip the participant binding off
exactly the tokens that predate it. A mutation asserts the tag moved.

**The view check runs before the row is looked up, and deliberately does not
say "refresh".** Another participant's cursor is not a snapshot that moved;
sending its holder to refresh would put them in a loop that cannot terminate,
because their next page would be this page again. A case asserts the two
refusals stay different words.

### A gap in my own case, found by the harness rather than by reading

`test_a_token_from_the_previous_scheme_is_refused` used a real `w1` token — and
`w1` and `w2` differ in ARITY, so the length check refuses it before the scheme
tag is ever consulted. The mutation deleting the tag comparison stayed UNSEEN
against it. A scheme tag nothing tests is a tag that will not be there when two
shapes do coincide in arity, so there is now a case at this build's exact
member count carrying a scheme this build has never minted. Worth naming
because the case READ correctly and measured nothing.

### Measured, not read

- **24 of 26 caught**, the same two expected-unseen. Four added: the view
  binding removed; the view check skipped at its call site; a token that
  carries a viewer it does not read back; and the scheme bump reverted.
- against the PRE-FIX source — the view check removed and the scheme returned
  to `w1` — the two cases that are about the defect fail. The other five in
  that class pass either way BY DESIGN: they are the same-viewer guards, and
  they are named rather than counted.

### Gates

- the two focused suites — 96 cases, green (90 before)
- full v11 gate — **3284 parallel passed, 54 serial passed, ACP 89 pass / 0 fail**
- all three corrected reproductions exit 0; the reviewer's cross-view file now
  raises the refusal where it asserted an empty page

## State

The third-reviewed [P1] is corrected and measured. Passed back for independent
review rather than closed.

### For review

- **The viewer rides in the token in the clear.** The review is explicit that
  this is query integrity rather than tamper resistance, and the token is
  opaque by contract rather than by construction — so a participant who edits
  one can still name themselves. That is the same trust level as passing
  `team=`/`member=` on the call, which is what the CLI already does, and no
  more.
- **Every `w1` token in flight is now refused.** There is no migration path and
  none was built: the tokens are page cursors held for the length of one
  paging session, and the correct response to a refusal is a refresh.
