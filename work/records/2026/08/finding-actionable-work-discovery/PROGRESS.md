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
