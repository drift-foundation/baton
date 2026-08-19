# Progress

## 2026-08-19 UTC — `baton.claude` (implementer)

PLAN steps 2 through 5: the first-cut within-pool blocker preference pinned in
`FINDING.md`. Projection 11.1 → 11.2, additive. No schema change, no new verb,
and none of the deferred effective-priority model.

## PLAN step 2 — revalidation of every ordering surface

Read and run against the current tree, not taken from the finding.

| surface | ordering before this Work |
| --- | --- |
| `home` (root rows) | explicit priority, then `created_seq` |
| `children` | explicit priority, then `created_seq` |
| `tree` (roots and every child level) | explicit priority, then `created_seq` |
| `participant_actions` (Work wakes) | **`created_seq` alone — no priority at all** |
| `search` | `created_seq` alone, behind its `next_after` cursor |
| TUI | none of its own; it renders the projection's row order |

Two facts that shaped the implementation:

1. **The readiness wake set did not order by priority at all.** So rule 5 —
   "the same ordering drives human Work lists and participant readiness" — was
   already violated before any blocker preference existed. An agent polling
   `wait` was told its oldest Work first regardless of what the operator had
   marked `high`. That is fixed here as part of the one canonical ordering,
   and it is a bigger behavioural change than the blocker preference itself.
2. **The order fragment was copy-pasted at four sites.** The finding asks for
   "one canonical blocker predicate"; the ordering it lives in was not
   canonical either. Both are now one shared constant, and a test asserts no
   surface keeps a private copy.

Also confirmed: the TUI has no sort of its own, so ordering parity is
structural rather than something a test has to keep in step.

## PLAN step 3 — the one predicate

A Work **blocks** when it is open, `ready`, unclaimed, neither gated nor
parked, and at least one OPEN Work waits on it through a live dependency edge.
Written once as `_BLOCKING_PREDICATE`, used by `WORK_ORDER` and — decided from
facts the row already carries, so there is no second definition to drift — by
`_blocking()` for the published field.

Each clause, and why:

- **ready, unclaimed, not blocked, not parked.** Rule 6. Sorting a claimed,
  gated, or deliberately parked blocker forward advertises Work nobody may
  take. This is the same eligibility test `participant_actions` already
  applies to unclaimed Work, so the board and the wake set cannot disagree
  about who is a candidate. Parking especially: it is an explicit deferral,
  and quietly re-raising it would reverse a decision somebody made on purpose.
- **The consumer must be open.** Rule 4 of the proposed model, retained: a
  satisfied, closed, or removed edge stops counting the instant it stops
  holding anybody. Nothing is rewritten — the predicate simply stops being
  true, and the edge stays in the ledger as history.
- **The consumer need NOT be claimed.** This is the one place I read the
  ruling rather than transcribing it. "A Job holding another agent" could be
  read as requiring a claimant on the consumer, but the stall the finding
  describes was an *unclaimed* W6 sitting behind a ready W101, and requiring a
  claimant would make the preference flicker every time a consumer was claimed
  or released. A flickering order is the opposite of what the ruling asks for.

Deliberately absent, because rule 3 defers them: no transitive walk, no
fan-out weight, no count in the ordering, no cross-pool promotion, no second
priority axis. A test asserts no `effective_priority` or `priority_boost`
field appeared.

`WORK_ORDER` is: explicit pool → blocker preference → `created_seq`. Applied
to `home`, `children`, `tree` (roots and every level), and the
`participant_actions` Work loop.

**`search` is deliberately excluded.** It answers "find this Work", not "what
next", and its documented contract is results riding stable creation order
behind an explicit `next_after` continuation cursor — reordering it would
break paging without helping anyone schedule. It did not order by priority
before this change either, so nothing became inconsistent. There is a test
pinning that exclusion so it reads as a decision rather than an oversight.

## The published fact

Rows and details gain the boolean `blocking`. Binary, because the ruled
preference is binary, and `links.blocks` already names exactly whom a row is
holding — so the reason is inspectable without publishing a count, and a count
is precisely what rule 3 defers. `_row_view` computes it from the
`open_dependents` value it was already reading, so no surface pays a second
query.

## Two things the ruling does not settle — please rule

1. **Containment.** `FINDING.md`'s acceptance questions ask to confirm whether
   containment parents contribute like dependency consumers, and the first-cut
   ruling does not answer it. I implemented **dependency edges only**. The
   evidence both ways: the authority's own `_recompute_ready` treats an open
   child and an open blocker as one conjunction, so they gate identically —
   which argues for including containment. Against it: an open child holding
   its parent open is bookkeeping rather than an agent waiting, dependency
   edges are explicit and rare while nesting is common, and in a nested tree
   almost every open child would become a "blocker" and the preference would
   degenerate to noise. That last point is why I chose the narrow reading for
   a rule the ruling calls "deliberately narrow". If you rule the other way it
   is one added clause in `_BLOCKING_PREDICATE` and one in `_blocking()`,
   plus tests.

2. **The TUI has no visual cue, on purpose.** The finding says the compact TUI
   must distinguish stated priority from a derived boost and that "the exact
   display spelling remains a design decision" — undecided, so I did not
   invent one. The consequence is real and worth naming: the board now
   reorders for a reason the operator cannot see. Two existing TUI tests broke
   for exactly that reason (below). The `blocking` boolean is published and
   waiting whenever the spelling is chosen.

## Existing tests I edited

Six, in two groups, none weakening what its test proves.

**Two TUI tests, steered rather than changed.** `test_tui.py`'s focused-facts
test and `test_w17_deps_label.py`'s footer test each assert about the row that
happens to be focused by default, and neither is about ordering. In both
fixtures a ready unclaimed blocker now leads the pool, so the default focus
moved. Each is steered to the row it always meant with one extra `j`, placed
inside an existing step so no step index moves and **no assertion changes**.
These two breaking is itself evidence the feature works — and evidence for the
visual-cue question above.

**Four projection-version pins** (`test_w136`, `test_w245`, `test_w47`, and
the envelope assertion in `test_w5_conversational_poke`): 11.1 → 11.2. W136
demands 11.0 and 11.2 together, so it still proves an older minor of the live
major succeeds.

## Why 11.2 is a minor, stated because I raised the opposite last time

On W5 I flagged that `jsonapi.py`'s rule — a change a consumer would "silently
misread or refuse" moves the major — arguably pointed at a major. Here it
plainly does not, and the contrast is worth recording because it shows the
rule discriminating rather than being applied by habit:

- `blocking` is a new field; no consumer has it to misread.
- The ORDER of a list is not a field a client reads a value out of. A client
  that took row 0 as "what next" now gets a better answer to the same
  question — which is the entire point of the Work.
- Nothing refuses. On W5 an unwidened bridge would have thrown on the whole
  envelope; nothing here can throw.

## Regressions — `tests/work/test_w7_blocker_preference.py`, 17 tests

Every case PLAN step 4 names, plus the ones that keep the deferred model out:
one blocking versus one free-standing Job; explicit priority unchanged in the
stored column before and after the edge; a LOW blocker holding a HIGH consumer
staying in the low pool; two pools interleaving pool-first; creation order
tie-breaking inside both groups; edge removal and consumer closure each
dropping the preference immediately; claimed, parked, and itself-gated
blockers taking none; ordering making nothing claimable that was not; the
board and the wake set naming the same next Work; children and tree levels
ordering identically; search keeping its cursor contract; the boost being a
published boolean rather than a glyph to parse; and one test asserting the
predicate and the order fragment each exist exactly once in the module.

## Break-sweeps

Each defect reintroduced alone against the 17-test suite.

| Reintroduced defect | Result |
| --- | --- |
| No blocker preference at all (the pre-W7 order) | 9 red |
| Blocker preference outranks the explicit pool (cross-pool promotion) | 2 red |
| A claimed blocker keeps the preference | 2 red |
| A parked blocker keeps the preference | 1 red |
| A closed consumer still confers the preference | 1 red |
| Readiness keeps its own creation-order sort | 1 red |
| One level keeps a private copy of the order fragment | 2 red |

The last one reds the no-second-definition test as well as the parity test,
which is the pair this finding is really about: two orderings is how the human
board and the agent's wake set start disagreeing.

## Gate

`just test-v11`: **1814 passed**, serial **40 passed**, ACP **42/42**.
`tools/codex-event-bridge`: **45 passed**. The whitespace check is clean.

## Not done

- The broader effective-priority model — inheritance, transitive fan-out,
  weighted scoring — remains deferred by the ruling and is untouched.
- No TUI presentation of the boost (spelling undecided; see above).
- Nothing deployed. The running set at `/home/sl/baton-v11` is release
  `7bea055` and was not restarted or activated.

## 2026-08-19 UTC — `baton.claude` (implementer), second pass

W7 came back to `baton.impl`. Recording what the repository records show,
because that is where the answer to "what should I do now" lives.

### What the return contained

The pass at seq 64 restates the contract — "explicit Hi/No/Lo remains the
primary pool; within one pool, ready Work that DIRECTLY unblocks another agent
precedes free-standing Work; binary signal only, stable creation-order
tie-break, no fanout/transitive scoring or cross-pool promotion, identical TUI
and readiness order."

Against that:

- **There is no `review-YYYY-MM-DDTHH-MM-SSZ.md` in this record**, so nothing
  states a disposition on the delivered implementation.
- **`PLAN.md` steps 2 through 5 still read `[pending]`**, unchanged from
  before the first pass. (I did not set them myself then and have not now:
  the plan is reviewer-owned and a status flip is the reviewer's disposition,
  not the implementer's claim.)
- **`FINDING.md` is unchanged**, so the two questions the first pass raised
  are still open.

I have not rebuilt the implementation. It is in the tree, and this file
records it; re-implementing would duplicate it and destroy the evidence trail.

### Revalidation of the tree, done rather than assumed

`projection.py` still carries `_BLOCKING_PREDICATE` and the shared
`WORK_ORDER`, applied to `home`, `children`, `tree` at every level and the
`participant_actions` Work loop; rows and detail still publish `blocking`;
`tests/work/test_w7_blocker_preference.py` is present. Full gate re-run on the
current tree: `just test-v11` **1845 passed**, serial **40**, ACP **42/42**,
`codex-event-bridge` **45**.

### One phrase in the return that corroborates an open question

"ready Work that **directly** unblocks another agent" is the same narrow
reading I implemented — direct dependency edges, no containment, no transitive
walk. That is corroboration, not a ruling: it appears in a restated assignment
rather than in `FINDING.md`, whose acceptance question ("confirm whether
containment parents contribute exactly like dependency consumers") is still
formally unanswered. I have left the predicate as it is and left the question
open rather than quietly promoting a phrase in a handoff comment to a pinned
decision.

### The gap the return did surface — "identical TUI and readiness order"

The first pass argued TUI parity was STRUCTURAL: the console has no sort of
its own, so it renders whatever order the projection returns. That argument is
true, and it is not evidence. The generic parity suite does compare drawn rows
to projected rows one for one, but no test exercised a BLOCKER on a real
screen; the two existing TUI tests that broke when this ordering landed were
indirect evidence at best.

`test_the_drawn_table_leads_with_the_blocker` closes it: a fixture whose
blocker is created LAST — so creation order alone would put it at the bottom —
driven through the real console on a pty, with the drawn table read back and
compared to the projection's own answer, and the blocker asserted above both
free-standing rows.

Break-sweep: removing the blocker clause from `WORK_ORDER` reds it. Suite is
now 18 tests.

If the board and the wake set could ever disagree about what to do next, that
disagreement is the whole defect this Work exists to remove — so it is worth
one test whose subject is a human's screen rather than an argument about
layering.

### Still open, and still not mine to decide

1. **Containment.** `FINDING.md`'s acceptance questions ask whether
   containment parents contribute like dependency consumers; the first-cut
   ruling does not answer it. Implemented as dependency edges only. Evidence
   both ways is in the first-pass section above: `_recompute_ready` treats an
   open child and an open blocker as one conjunction, which argues for
   including containment; but in a nested tree nearly every open child would
   become a "blocker" and the preference would degenerate to noise, which is
   why the narrow reading fits a rule the ruling itself calls "deliberately
   narrow". One clause each way if ruled otherwise.
2. **No TUI cue, on purpose.** The finding says the display spelling remains a
   design decision, so none was invented — which means the board reorders for
   a reason the operator cannot see. The `blocking` boolean is published and
   waiting for whatever spelling is chosen.

### State

Implemented, gated, and **awaiting review**. Nothing deployed: the running set
at `/home/sl/baton-v11` is release `7bea055` and was not restarted.
