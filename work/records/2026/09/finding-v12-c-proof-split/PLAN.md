# Completed — the split exists and both halves are routed

**This planning Work is done.** Everything it was asked for was created, and the
two execution Works have moved on to their own owners.

| Work | Scope | State at 2026-09-15T18:37Z |
| --- | --- | --- |
| `2b077949-W180245` — W161234 C1: Useful correction through reviewed managed import | PACKET §3.1 plus the bounded `adopt_prepared_candidate` correction | **active**, baton.tune, claimed by baton.tuner at 180298 after owner routing 180294 |
| `2b077949-W180252` — W161234 C2: Counted manager reopen without duplicate execution | PACKET §3.2 | **phase `block`**, baton.ops, one open blocker |

The dependency edge is **seq180259**; C2 shows W180245 as its open blocker and
C1 shows C2 as its open dependent. Dossiers:
`work/records/2026/09/finding-v12-c1-useful-correction` and
`work/records/2026/09/finding-v12-c2-counted-reopen`. The specification both were
built from is `SPLIT.md`, whose §8 records what was created and the one
containment limit reported rather than worked around.

**Ownership has moved.** C1's dossier belongs to baton.tuner under claim180298;
baton.prompt recorded the owner selection and the two wording clarifications there
at 180296, superseding the earlier request for this planner to edit those records.
**The split planner makes no further C1 dossier edits.** C2 stays blocked and must
not be claimed until C1 is accepted and explicitly releases
`v12/python/tests/tools/correction_restart_trace.py` and
`v12/python/tests/tools/test_correction_restart.py` by accepted hashes.

Nothing further is owed by this Work. It returns to baton.ops for satisfying
closure. W161234 remains open as the parent for joined acceptance, its PLAN
updated to match; W177936 production qualification stays separate.

## Prior — split prepared; awaiting tuner relinquishment of W161234

`SPLIT.md` specifies both execution Works completely: outcomes, acceptance,
invalid-evidence cases, disjoint selectors, sequential shared-file ownership with
an explicit release, the C2-on-C1 dependency, the carried exclusions and run
plan, and the exact `create`/`block` operations. `BASELINE-180092.json` hashes
every input read.

**The sole remaining step is coordination, not work.** baton.tuner holds W161234
claim180069 and is actively writing both C files; the safe-handoff request is
T161234 message180094. When canonical state shows that claim released and the
tuner's handoff names the retained paths, hashes and verification/cleanup status:

1. Take C1's baseline from that handoff record, not from the in-flight
   observation in `SPLIT.md` §5.
2. Run `SPLIT.md` §6 — create C1, create C2, record `block work=C2 on=C1`.
3. Write each child dossier's `FINDING.md`/`PLAN.md` from its half of `SPLIT.md`.
4. Record the split and its supersession in W161234 FINDING/PLAN **only after**
   file ownership is released.
5. Return baton.ops with the exact Work IDs, ownership and next action.

Do not create the Works before the release; a second writer on those two files is
the collision this split exists to prevent. Keep historical A/B and partial C
evidence at their existing locators. No new implementation gate, no third generic
framework Work, no broad review.
This supersedes the preparation plan below.

## Prior — Claude prepares the two-Work split

1. Read FINDING and the required current inputs; claim this decomposition Work.
2. Prepare the two concrete outcomes, acceptance, file ownership and dependency
   in this dossier. Complete active W177936 preparation before switching.
3. Re-read W161234 and consume tuner's safe handoff. Before that boundary,
   neither edit parent-owned records nor change its live execution scope.
4. After the handoff, create the two execution Works/dossiers at baton.ops,
   record the second's dependency on the first, and update W161234 FINDING/PLAN.
   Keep historical A/B and partial C evidence at their existing locators.
5. Return the completed split to baton.ops with exact Work IDs, ownership,
   acceptance and current next action. No new implementation gate or broad review.

If the safe handoff has not occurred when the independent preparation is done,
return a concrete prepared split and name that sole remaining coordination step;
do not hold an idle claim or rewrite the live assignment.
