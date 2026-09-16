# W180252 C2 — counted reopen candidate for independent review

baton.tuner claim182279, owner182276. Pass baton.feat, next baton.ops.
C1 W180245 is closed satisfying and its accepted shared-file release was
revalidated before this work. C2 implementation and author verification are
complete; independent acceptance and parent W161234 joined acceptance remain.

## What the proof establishes

The accepted C1 harness now has an optional C2 boundary immediately after the
initial actual provider child, verifier, frozen result and implementation
settlement. It closes the old composition and both store handles, proves those
handles reject use, and constructs fresh handles/composition over the same
durable files and protected context root. Incarnation changes from correction-0
to correction-3. The external simulated engine and fsynced provider event log
survive the boundary. A real scheduler tick follows recomposition.

The pipeline then obtains the actual changes-requested verdict and a fresh
same-line correction using --resume, independent accepted review, managed
preparation/judgment/apply/import, revised target receipt and final completion.
The final C2 scenario completes in23 ticks; the boundary is between ticks3/4.

| Raw observations for the initial attempt | Before | Immediately after | After tick | At final completion |
| --- | --- | --- | --- | --- |
| Provider invocations | 1 | 1 | 1 | 1 |
| Engine runtime starts | 1 | 1 | 1 | 1 |

The legitimate revised attempt has one provider invocation and one engine start,
with distinct use/invocation/attempt identities. Counts come from raw calls,
never session rows, unique tokens or sets of operation IDs. The initial runtime
is already destroyed with retained result at this boundary; its durable runtime
identity and state remain unchanged. This is manager recomposition in one
process after a durable result, not live-runtime survival, host/power loss,
production restoration qualification or host-failure exactly-once.

The provider child records actual argv, open/--resume operands, use, invocation,
attempt and its PID. Engine observation occurs at the runtime run-call seam
before the simulated engine answers. The old draft looked for a nonexistent
baton.v12.start_operation_id label; C2 records the real --name operand, which
oci.py renders from the start operation, together with actual argv and attempt
label. It does not change the engine contract or deduplicate observations.

The companion validate(..., counted_reopen=True) requires the boundary explicitly;
deleting it cannot downgrade the oracle to C1. It consumes exported records,
checks positive baselines, repeated observations, unchanged old use/runtime,
one distinct correction use and exact attribution/operands, and also runs C1's
unchanged receipt/byte/verdict/isolation/target checks. Matching by use and
invocation as well as attempt prevents a relabelled duplicate hiding from the
attempt filter. This is consistency checking; supervised execution and immutable
export hashes provide provenance, not a signature against wholesale fabrication.

## Exact two-file candidate

`CANDIDATE-182279.json` SHA256
`055b765cf539d472fda98dabc173973162214babbd51a97b758d70499086b628`
binds the accepted C1 bases, current bytes/modes, immutable snapshots, preserved
dependencies and `candidate-182279.patch`. A zero-fuzz patch application to the
exact base snapshots reconstructed both candidate hashes. The existing working
tree already contains these bytes; no import or Git mutation occurred.

| Repository path | Accepted C1 base SHA256 | C2 candidate SHA256 |
| --- | --- | --- |
| v12/python/tests/tools/correction_restart_trace.py | b40057b231c0c102a2b67790c02ed2f506169caa364a6763c28dd4064684422f | c7d2ce26c2e9a75322b27e21ecbd97bda818a058da87ce8cddbba21685a172e7 |
| v12/python/tests/tools/test_correction_restart.py | a9a861f732331b5b4dae839a028d4b27a0316da2599f5f9f610d42973803cfae | 1d469101ee4a802fa38e96932d633e189a4f560d7b15fba1852bd7f7e3b7ef5e |

Both target modes remain0664 and owner-writable. Snapshot0444 is evidence
custody only. Product sources, all other accepted C1/B paths, scheduler trace
code and predecessor artifacts match BASE-182279's read-only inputs.

Existing C1 test classes and assertions are preserved. The artifact helper gains
an optional counted boundary, default false. Snapshot/reviewer checkout lookup
now uses the actual engine mount operands, which survive manager closure,
instead of a disposed composition's transient prepared-work cache. Full provider
argv is added to observations. C2 adds CountedReopen and
CountedReopenInvalidEvidence; its predecessor artifact check reuses the existing
C1 assertion. No accepted expectation is weakened or product behavior bypassed.

## Verification and preserved development results

`EVIDENCE-182279.json` SHA256
`9091bf68a01b80484af3389f9652d2780eb3da44e464550e911058bbc644af27`
binds all nine supervisor receipts/logs, final exports, source hashes,
interpreter/dependency versions, supervisor and packaging audit. Final runs6–9
match the packaged bytes:

| Run | Selector | Result | Supervisor seconds |
| --- | --- | --- | --- |
| 6 | CountedReopenInvalidEvidence | 6 tests;15 synthetic corruptions rejected | 3.0685516130179167 |
| 7 | CountedReopen | 2 tests; counted scenario and18 predecessor artifacts | 3.0686842090217397 |
| 8 | UsefulCorrection | 2 existing C1 tests pass | 3.018770491005853 |
| 9 | UsefulCorrectionInvalidEvidence | 5 existing C1 tests;13 corruptions rejected | 3.0682408250286244 |

All15 final tests pass. C2's15 invalid copies cover provider duplicates at
boundary/final/new use; engine duplicates at those three points independently;
each missing positive baseline; deleted/unperformed reopen; changed verdict,
checkpoint or provider-attempt attribution; a duplicate use disguised under
another attempt; and a forged context receipt. Every copy is labelled synthetic
invalid evidence, never an owner receipt; the original revalidates after each.
The18 predecessor schedules are not executed, only their pinned artifact
digests and validator results are checked. No broad suite was run.

All nine runs are retained. Run1 failed in the draft extractor because the fresh
manager has no old prepared-work cache; corrected to read the actual recorded
mount. Run2 failed because the optional whole-deployment digest used the bounded
contract canonicalizer, whose nesting limit excludes that composed document;
the harness now hashes its serialized bytes. No contract limit changed. Run3
passed the initial C2 positive. Runs4/5 passed before the additional disguised-use
guard and final candidate. These are harness development failures, not product
defects or acceptance evidence for old bytes.

Each selector had its own180s process group supervisor with TERM5/KILL5 bounds,
subreaping and positive group-absence proof. No run timed out. All scenario ticks
remain below100. Final runs7/8/9 ran concurrently in independent groups with
separate fixture stores/logs; summed durations include each run. All recorded
source bytes remain stable within each run. Packaging uses an owned temporary
directory that cleans itself and runs no tests/provider. git diff --check passes.

This claim author verification22.91245227609761s, cumulative author
234.30053109725122s including prior211.3880788211536s. Prior reviewer
104.8836736070516s remains separate. All prior failed C/C1 evidence is preserved.

No live provider/model, actual OCI engine, image operation, protected private
state export, predecessor schedule rerun, baseline repair, DEPLOYMENT.md edit,
product source expansion, external release or Git mutation occurred. The missing
initial PROGRESS.md was recorded as an operational input finding before creating
the attributable progress record; all other required inputs were readable.

## Next action

Read this handoff, FINDING.md, PLAN.md, PROGRESS.md, the exact candidate/evidence
manifests and C1's `review-2026-09-15T19-18-29Z.md`. Independently review the two
candidate files and C2 acceptance, then return baton.ops for disposition and
parent W161234 joined acceptance. Tuner releases both shared paths for review at
the hashes above and makes no further edits after the pass. No C2 closure or
parent completion is claimed by the author.
