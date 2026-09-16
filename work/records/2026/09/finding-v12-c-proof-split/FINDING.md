# Split the remaining W161234 C proof

Work: W180092 (2b077949-W180092), assigned to baton.impl for baton.claude.
Safe-handoff request: T161234 message180094; tuner poke180100.

## 2026-09-15 — owner assigns the split to Claude

Slawomir asked whether W161234 needed splitting because he does not want another
mega job, then directed: "assign the split to claude". Assign baton.claude a
bounded decomposition task. Accepted A/B evidence stays in W161234; W177936
qualification stays separately owned. This is preparation and coordination,
not an implementation assignment or an additional release requirement.

The selected division is:

1. Useful correction through import: wrong code, genuine changes-requested
   review, corrected code, verifier execution and independent review, then the
   accepted managed path to a target receipt naming the revised bytes.
2. Counted restart without duplicates: reuse the first result's accepted harness;
   positive provider/runtime baselines survive actual manager-handle reopening,
   with no old-use increment and exactly one increment for a legitimate new use.
   Deliberate duplicate evidence must fail the same validator.

Each owns its relevant invalid-evidence cases and independent acceptance.
The second depends on the first. Do not create a third generic framework
implementation job. W161234 remains the parent for joined acceptance, preserving
the existing finish line rather than adding another implementation campaign.

At snapshot180083 tuner holds W161234 claim180069, episode180064, for combined C.
The split takes effect only at a safe handoff. Request that tuner stop new C
implementation at the next safe boundary, preserve any partial work, exact
paths/hashes and measured verification/cleanup evidence, and pass to baton.ops.
Do not release or reroute its live claim externally. Existing operations must
finish or be cleaned up by their owner; no second writer starts on those files.

Claude may prepare the split in this separate dossier before the handoff, after
completing its active W177936 identity-preparation handoff. Once canonical state
confirms tuner has relinquished C, create exactly two bounded execution Works
under W161234, with their own canonical dossiers, shared-harness ownership,
acceptance and explicit dependency. Queue them at baton.ops for execution
selection rather than automatically starting implementation. Reflect the split
and supersession in W161234 FINDING/PLAN only after file ownership is released.
Any required production change gets an explicitly bounded scope disposition.

Required inputs:

- baton:work/records/2026/09/finding-v12-correction-restart-proof/FINDING.md
- baton:work/records/2026/09/finding-v12-correction-restart-proof/PLAN.md
- baton:work/records/2026/09/finding-v12-correction-restart-proof/review-2026-09-15T16-15-23Z.md
- baton:work/records/2026/09/finding-v12-correction-restart-final-proof-preparation/PACKET.md
- Current W161234 handoff and any tuner safe-handoff record.

Preserve accepted B bytes and predecessor evidence. No product/test edits,
test runs, live provider/engine, image work, marker reset, broad suites,
architecture restart or Git mutation belongs to this split task.

## 2026-09-15T18:14:49Z — split prepared, creation gated (claim180137)

The two execution Works are specified exactly in `SPLIT.md`
(sha256 `17b18faf4dbd9991760dadd6b4a2f122f2653bac7fae2979a8fa745a4f407cc2`) and
are **deliberately not created**. `BASELINE-180092.json` records all six read
inputs by hash; all five required inputs were present and readable, so none is
reported as an operational finding.

**THE SPLIT IS NOT A NEW DECOMPOSITION, AND THAT IS THE POINT.** The accepted
`PACKET.md` already specifies these two scenarios as §3.1 and §3.2, with separate
non-vacuity arguments, separate counter designs and separate invalid-evidence
lists; `review-2026-09-15T16-15-23Z.md` lists what C owes in a sentence that
divides on its own conjunction. What this task adds is two owners, two
acceptances and one dependency, so neither half waits on the other's review. The
packet hash I read, `941b4233…`, is the same one the tuner pinned in
`BASE-C-180069.json`, so both halves are specified against identical bytes.

**C1** carries useful, different, working code through a genuine
changes-requested verdict and the accepted managed path to a target receipt
naming the revised bytes, with five invalid-evidence cases. **C2** depends on
C1, reuses its accepted harness, and proves both counter baselines positive
before a real manager recomposition that increments neither, with the six §3.2
invalid-evidence cases including the two duplicate injections rejected
separately. C2 carries the predecessor's limit forward unchanged: one process,
not a host or power loss.

**Shared-file ownership is the part that can actually go wrong.** Both Works
change the same two paths, so ownership is sequential with an explicit release —
C1 holds both from claim to acceptance, releases them by name and hash, and only
then may C2 claim them. The packet's single `InvalidEvidence` class is split into
`UsefulCorrectionInvalidEvidence` and `CountedReopenInvalidEvidence`, because one
class owned by two Works is exactly the shared mutable surface this division
exists to avoid.

**The tuner's partial work is observed and deliberately not bound.** The harness
is already substantial — 17966 bytes carrying the schema, both counter streams,
the reopen record and `validate` — and should be carried forward rather than
rewritten. Its hashes were read at 18:16:15Z **while the tuner was writing them**,
so they are recorded as an observation with that caveat, and C1's baseline must
come from the tuner's own safe-handoff record instead. **Corrected at claim180212:** I also wrote that a
later read found the harness grown from 17966 to 18337 bytes "while the section
describing it was being written". The detail was wrong — the growth happened at
mtime 18:16:14Z, one second *before* the hash was taken, and that hash turned out
to be exactly the one the safe handoff released. Declining to bind a hash read
from a live writer's file remains right; the evidence I gave for it did not say
what I said it said.

**THE GATE IS THE ONLY THING LEFT.** At snapshot180137 baton.tuner still holds
W161234 claim180069, episode180064, agent state `working`, last contact
18:14:08Z, with `run-C-180069-4` written at 18:12Z and exiting 1. The safe-handoff
request is T161234 message180094. Nothing in `SPLIT.md` §6 may run before
canonical state shows that claim released: creating the two Works while a live
writer holds both files is precisely the second-writer collision the split exists
to prevent, and an idle claim here would help no one.

Not done: no Work created, no dependency recorded, no parent-owned record edited,
no product or test file touched, no test run, no live provider or engine, no image
work, no reroute or release of the tuner's claim, no Git operation. New measured
verification 0 s. All writes are inside this dossier.

## 2026-09-15T18:25:23Z — split finalized (claim180212)

The gate cleared: baton.tuner relinquished W161234 at pass180164 and owner
reroute180210 selected finalization. `HANDOFF-C-180069.md` and
`review-2026-09-15T18-22-50Z.md` are incorporated — the released baseline in
`SPLIT.md` §5a and the bounded adoption correction C1 now carries in §2a.

**C1 is `2b077949-W180245`** (baton.ops, queued, ready, blocks C2) and **C2 is
`2b077949-W180252`** (baton.ops, phase `block`, one open blocker), with the
dependency at seq180259. Both dossiers are written; the parent FINDING/PLAN are
updated now that the files are released.

**C1 carries a real product defect as its prerequisite.** Measured combined 0,
base 1, isolated 0 — and `adopt_prepared_candidate` decided eligibility from the
sequence aggregate while describing it as the combined command, which passed.
`compose_report`'s aggregate is deliberately left alone because an existing test
pins it. The tuner handoff named the wrong symbol; I revalidated every line
before binding it into the Work.

**One limit reported rather than worked around:** the Work-graph parent edge was
refused for authority reasons and containment is creation-time only. I declined
to reroute W161234 to myself to obtain it. The relationship is carried the way
this campaign has always carried it, and `SPLIT.md` §8 states what baton.ops
would have to do for true containment edges. The dependency edge needed the same
authority and was recoverable: C2 was transiently rerouted, the edge recorded,
and C2 returned to baton.ops, with every move in its event log.

**A correction to my own earlier record**, made in place: the previous entry
claimed the harness "changed while the section describing it was being written".
The growth happened one second *before* the hash I took, and that hash turned out
to be exactly the one the handoff released. Declining to bind an in-flight hash
was still right; the evidence I cited for it was not what I said it was.

## 2026-09-15T18:37:55Z — documentation completion (claim180313)

Owner reroute180310 asked for a documentation-only completion. Two files changed,
both PLANs, with every historical block preserved beneath the new current one:

- `PLAN.md` here, marked **completed** with W180245, W180252 and dependency
  seq180259.
- `work/records/2026/09/finding-v12-correction-restart-proof/PLAN.md`, updated to
  C1 owner-selected and routed at 180294, tuner claim180298 active, C2 blocked.

Canonical state was read rather than assumed: W180245 is active at baton.tune
under baton.tuner since 18:36:44Z and blocks W180252, which sits at baton.ops in
phase `block` with one open blocker. The parent records were byte-identical to
what claim180212 left, so no concurrent writer had touched them.

**C1's dossier is the tuner's now and I did not edit it.** Message180296 records
that baton.prompt already applied the owner selection and both wording
clarifications there, superseding the earlier request at180280 for this planner to
make those edits. Reading it to check my own wording was the right use of it.

Two clarifications from180280 are carried into the parent PLAN because that is
where they will be read: the selected `adopt_prepared_candidate` correction is the
**explicit exception** to the broad accepted-integration-code exclusion, and C1
runs `UsefulCorrection` and `UsefulCorrectionInvalidEvidence` plus focused
correction tests — **not** the three old combined-C selectors and not C2.

Not done: no C1-owned file edited, no product or test file touched, no test run,
no execution altered, no Git operation. `reconciliation.py` has changed since
claim180212 — that is the tuner implementing C1 under its own claim, not this
Work. New measured verification 0 s.
