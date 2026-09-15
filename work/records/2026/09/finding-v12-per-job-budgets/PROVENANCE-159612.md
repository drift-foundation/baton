# W156162 — candidate provenance, 29 paths

Gathered read-only at claim 159612; the machine figures are in
`provenance-159612.json` — per path, its base bytes and SHA256 at `HEAD`, its
candidate bytes and SHA256, its added/removed line counts and its hunk count.
**No Git mutation.** Nothing was removed, imported or absorbed to make this
packet look clean.

`PROVENANCE-158092.md` and `provenance-158092.json` are **retained unchanged** as
the 27-path packet that preceded the owner's M157653 ruling; this supersedes them
without replacing them.

## What changed since the 27-path packet

**Two product paths entered the candidate**, and only because owner ruling
M157653 (2026-09-13T09:19:44Z) approved exactly them:

| Path | Base → candidate | Hunks |
| --- | --- | ---: |
| `src/baton_v12/integration/reconciliation.py` | +324 / −10 | 5 |
| `src/baton_v12/integration/execution.py` | +33 / −0 | 1 |

Both carry only the approved host-failure semantics: the tagged closed failure
answer and its validation, the causal custody and blocked settle, the durable
readback, and the post-import adoption with its target hold. No schema change, no
store migration, and no other owner touched.

## Counts, corrected by the reviewer

`PROVENANCE-REVIEW-159640.md` corrects the prose counts and they are carried
here rather than restated my way: **6 new**, **16 modified product-and-document**
paths and **7 existing tests**. In the two overlapping files: `stage_execution.py`
has **18 hunks — 17 this Work's, 1 W71879's**; `test_stage_execution.py` has
**6 hunks — 5 this Work's, 1 W71879's**.

**And textual separation does NOT establish that nothing depends on it.** That
was my phrasing and the reviewer narrowed it: the hunks do not overlap and no
line of this Work's references them, but no excised tree has ever been built or
run, so dependency is unmeasured either way.

## The rest, unchanged in character

Seven new files wholly this Work's; twelve modified sources and documents inside
its own scope; **five existing Job tests whose expectations changed and which now
carry the owner's approval** (M157653 approved exactly the changes listed in
`PROVENANCE-REVIEW-158105.md`); and two existing test files changed under the
PLAN-scheduled setup-only authority.

## The two `stage_execution` files, and the foreign Work

Unchanged from the 27-path packet and re-verified here:

- `tools/stage_execution.py` — this Work's hunks, plus **one foreign hunk**: the
  read-only integration observation dropping a runtime precondition so a
  reconciled completion with no runtime reaches the outer observer.
- `tests/tools/test_stage_execution.py` — six of this Work's hunks, all additive
  or setup-only with **no existing assertion changed by this Work**, plus **one
  foreign hunk**: `test_readonly_reconciled_completion_without_runtime_reaches_outer_observer`,
  the test for the source hunk above.

**The foreign change is W71879's**, per the reviewer's own attribution at
2026-09-13T05:44:15Z: the completion-observation candidate 153138, whose methods
and base bytes match. It is reported, not removed.

**Separability, and what is still not certified.** The two foreign hunks are one
change and its test, textually separable, with no lines overlapping this Work's.
That is a statement about TEXT and not about dependency: no excised tree has been
built or run, so what remains uncertified is that removing them leaves a passing
tree — the foreign test would fail without its source hunk,
and the long-standing `test_stage_execution` errors have only been compared
against earlier W156162 candidates, never against an excised tree. Integration
still needs its own candidate/base/path/authority preflight.
