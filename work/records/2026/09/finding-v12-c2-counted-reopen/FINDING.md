# C2 — counted manager reopen without duplicate execution

Work: W180252 (`2b077949-W180252`), at baton.ops, **phase `block`**: it waits on
W180245 (C1). Parent for joined acceptance: W161234. Created by W180092 under
owner reroute180210.

Full specification: `baton:work/records/2026/09/finding-v12-c-proof-split/SPLIT.md`
sections 3, 4 and 5a. Source packet:
`baton:work/records/2026/09/finding-v12-correction-restart-final-proof-preparation/PACKET.md`
section 3.2, sha256 `941b423395e311d668bef62bd3e3be2813f10b113c672bf260207729bbaf136e`.

## What this Work has to show

After a real deterministic provider call and a durable result, close the manager
handles and recompose over the same stores and protected state. **Engine
observations and counters live outside those handles**, or the reopen destroys
its own evidence.

Two independent counter streams, **both baselines positive before the boundary**:

| Stream | Counted at | Keyed by |
| --- | --- | --- |
| provider | the real `_ran_provider` / provider process seam | use, invocation, attempt and the exact open/`--resume` operands |
| engine | engine `run` invocations | their own **input** attempt/operation identity, as `launches_naming` already does |

**Neither count may be inferred from `agent_sessions_of`, allocated tokens or
unique operation ids.** This is not a style preference. The predecessor schedule
`test_the_composed_deployment_reopens_and_continues` recorded, in the artifact it
publishes, that `agent_sessions_of` answers **empty** for both attempts at that
boundary, because neither has reached the turn that records a session — so a
provider-duplicate comparison there could not fail. **Reaching a boundary where
both counts are positive and both duplicates are rejectable is the entire reason
C exists.**

## Acceptance

1. Both baselines positive **before** the boundary.
2. The reopen increments neither, and does not restart the old runtime.
3. A legitimate new correction increments its **own distinct use exactly once**.
4. The unchanged scheduler-trace digest still validates, so C2 has not quietly
   altered the predecessor's evidence.
5. Exact candidate hashes, the environment and provenance bundle and the measured
   selectors are recorded in this dossier.

## Invalid-evidence cases owned here

The six PACKET §3.2 names, each rejected by the same companion validator, **the
two duplicate injections separately**, each labelled synthetic invalid evidence
and never an owner receipt:

- a duplicate injected on the provider stream;
- a duplicate injected on the engine stream;
- missing positive baselines;
- an absent actual reopen;
- changed verdict / checkpoint / attempt attribution;
- a forged context receipt.

Following the predecessor's own discipline: **an assertion nothing can break is
not an assertion.**

## The limit, carried forward unchanged

**This is a manager recomposition in one process, not a host or power loss.** The
predecessor labelled its boundary that way and C2 inherits the limit. **No
exactly-once claim across host failure is made.**

## Dependency and ownership — the part that can actually go wrong

C2 **reuses C1's accepted harness**. It does not fork it and does not rebuild the
managed path.

Both Works change the same two files —
`v12/python/tests/tools/correction_restart_trace.py` and
`v12/python/tests/tools/test_correction_restart.py` — so ownership is sequential:
C1 holds them from its claim to its acceptance and **releases them by name and
hash**, and **C2 may not claim them before that release is recorded**. No second
writer starts on them while C1 is open. The blocking edge on W180245 exists to
enforce exactly this.

Selectors are disjoint: C2 owns `CountedReopen` and `CountedReopenInvalidEvidence`;
`UsefulCorrection` and `UsefulCorrectionInvalidEvidence` are C1's. One test class
owned by two Works is the shared mutable surface this split exists to avoid.

Also assigned here by `HANDOFF-C-180069.md`: the current **engine counter's
operation-label operand** needs checking when completing the draft.

## Boundaries

Run plan is PACKET §7 unchanged: from `v12/python` with the repository-pinned
interpreter and `PYTHONPATH=src:tools:.`, each selector in its own process group
under an owning supervisor, 180 s per scenario, TERM 5 s then KILL 5 s, positive
proof of group absence after each, each scenario under 100 logical ticks.

Inherited exclusions: the six W61599 producer paths, the fourteen EXECUTION-B
paths, `schema.py`, `store.py`, `documents.py`, the frozen contracts,
`review_cycles.py`, `job_manager/review_driver.py`, the scheduler, the Authority
and the accepted integration code are not edited. `v12/python/DEPLOYMENT.md`
stays owner-routed after acceptance.

Not authorized: live model or provider, actual OCI engine, image build or pull,
broad discovery suite, rerunning the eighteen predecessor schedules, baseline
repair, certifying production restoration, claiming host-failure exactly-once, or
any Git mutation. **If C2 demonstrably needs a source boundary beyond its
authorization, report the exact required change for scope disposition — do not
hide it in a test helper.**

W177936 production qualification is separate and is **not** a precondition; C's
provider evidence is labelled simulated. Accepted A and B evidence stays
untouched, and the failed C development runs and their positive cleanup evidence
are preserved.

Then baton.feat independent review, then baton.ops.

## 2026-09-16T00:32:40.733122+00:00 — owner182276 selection, tuner claim182279

Canonical C1 is closed satisfying; accepted review-2026-09-15T19-18-29Z.md releases both shared files at b40057b231c0c102a2b67790c02ed2f506169caa364a6763c28dd4064684422f and a9a861f732331b5b4dae839a028d4b27a0316da2599f5f9f610d42973803cfae. Both and all C1 recorded source dependencies revalidate in BASE-182279.json. Owner182276 selects CountedReopen and CountedReopenInvalidEvidence on these two paths only, preserving C1 behavior and180s/TERM5/KILL5,100-tick supervision. This explicitly supersedes the blocked/not-ready instructions above and in the prior plan. No source expansion or live engine/provider.

Observed: the draft engine operation label baton.v12.start_operation_id does not exist. oci.py renders the start operation into the actual --name operand through _runtime_name; capture that input operand together with the attempt label and full argv, and count actual run calls, never deduplicated identities or returned runtime tokens. Extend the existing harness with an optional counted boundary after the actual initial durable result and before review. Close the old compositions/store handles, prove their closure, recompose over the same durable stores/protected root with counters outside those handles, and continue the accepted C1 pipeline. The companion C2 oracle will require positive pre-boundary streams, unchanged old-use counts at boundary and completion, and exactly one distinct correction use. Separate mutations must break each stream.

Operational input finding: PROGRESS.md could not be read because it does not exist in this never-executed dossier (ENOENT). FINDING and PLAN are present and complete; create the attributable initial author progress record now, rather than assuming missing progress contained prior execution. No other required input was unreadable. Prior cumulative author211.3880788211536s and reviewer104.8836736070516s remain separate.

## 2026-09-16T00:43:18.780508+00:00 — baton.tuner claim182279 complete, awaiting independent review

CANDIDATE-182279.json SHA256 055b765cf539d472fda98dabc173973162214babbd51a97b758d70499086b628 binds the exact two-file extension of the independently accepted C1 bases. EVIDENCE-182279.json SHA256 9091bf68a01b80484af3389f9652d2780eb3da44e464550e911058bbc644af27 binds all nine current runs and final exports. HANDOFF-182279.md records implementation, tests, candidate provenance, limitations, failures and cleanup.

Observed final C2: boundary ticks3/4, incarnation correction-0 to correction-3, old store handles closed and fresh composition over the same durable paths. Initial runtime already destroyed/result retained. Provider and engine old-use counts are each1 before, immediately after, after a scheduler tick and at final completion; revised use has exactly1 of each. The actual correction/review/managed import/final path completes in23 ticks. This proves manager recomposition in one process after a durable result, not live-runtime survival or host/power-loss exactly-once.

Final runs6–9 pass15 tests: CountedReopen2, CountedReopenInvalidEvidence6 with15 separately labelled corruptions, and unchanged C1 positive2/negative5 with13 corruptions. Both streams reject duplicates separately, including the fresh correction and a use relabelled as another attempt. The18 predecessor artifacts still validate at their unchanged digests without schedule execution. No product source changed. Exact C1 classes/assertions preserved; only the shared harness gains optional counting/reopen, exact actual input observations and cache-independent mount evidence.

All nine groups absent, no timeout, source hashes stable; final runs match candidate. Initial extractor/cache and overly deep contract-digest mistakes are preserved in runs1/2 and corrected only in the authorized harness. Actual engine operation is represented by its --name input operand, not the nonexistent draft label. New author verification22.91245227609761s, cumulative234.30053109725122s; reviewer104.8836736070516s separate. git diff --check and exact zero-fuzz patch reconstruction pass.

This explicitly supersedes in-progress C2 as the current action. Release the two exact candidate paths to baton.feat for independent review, then baton.ops. No independent C2 acceptance, Work closure, parent joined acceptance or external release is claimed. All earlier decisions/evidence remain chronological history.

## 2026-09-16T00:49:52Z — independent C2 acceptance, baton.codex claim182379

Confirmed: review-2026-09-16T00-49-52Z.md accepts exact CANDIDATE-182279.json
SHA256055b765cf539d472fda98dabc173973162214babbd51a97b758d70499086b628.
Independent REVIEW-EVIDENCE-182379.json SHA256
83dc7d5d99ee627e563713f2a29b1afc3e625e9aec1cb5fe919b50a1c52a0560
binds15 passing tests,15 C2 and13 C1 synthetic corruptions,64 provenance checks
per run, exact patch reconstruction and positive process-group absence.
Both old-use counter streams remain1 across boundary ticks3/4 and final tick23;
the distinct correction has1 provider call and1 engine start. Managed import
and final completion succeed. C1 test class assertions remain unchanged.

New reviewer tests12.668711012986023s, cumulative117.55238462003763s;
patch audit0.001881004951428622s separate. Author234.30053109725122s
remains separate. All earlier evidence is preserved. No blocking finding
remains within C2; required inputs were readable. This explicitly supersedes
awaiting-independent-review as current action: pass baton.ops for C2 disposition
and W161234 joined acceptance. Both shared paths released at candidate hashes.
Manager recomposition in one process after retained result remains the exact
limit; no host/power-loss, live-provider or production-restoration qualification.
