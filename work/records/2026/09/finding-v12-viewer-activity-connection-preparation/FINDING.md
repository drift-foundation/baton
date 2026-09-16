# V12: Prepare viewer activity connection

Work: 2b077949-W177937. Consumer: W2 minimum monitor; follows closed W167896.

## 2026-09-15 — owner-selected parallel preparation

Slawomir confirmed the three-task proposal with "I agree with the plan". Owner approved this preparation on 2026-09-15. Assign baton.tuner the narrow plan connecting W61599 trusted activity to the accepted W167896 read-only viewer. Identify exact consumer APIs/source/test/doc paths, focused future verification and no-mutation guarantees. Preserve unknown/stale semantics, injected/restored HOME unknown baseline and historical terminal counts without implying live activity. Read accepted W61599 design and current source; revalidate final reviewed producer bytes before eventual implementation. Dossier-only preparation: no implementation, tests, engine/live calls or shared producer edits. Return baton.ops with implementation-ready packet. Do this before the separately queued C proof preparation; incoming release completion takes priority. Own only this new dossier.

This is preparation for existing required outcomes, not a new release gate. W61599 retains first shared serving-file ownership; W161234 B waits for its independently reviewed final candidate and file release. No backlog copy, authority cutover or v13 expansion.

## Required inputs

- baton:work/records/2026/09/finding-v12-minimal-readonly-job-viewer/PLAN.md
- baton:work/records/2026/09/finding-live-worker-log-observability/ACTIVITY-DOCUMENT-DESIGN-175025.md
- baton:work/records/2026/09/finding-live-worker-log-observability/review-2026-09-15T04-29-53Z.md

## 2026-09-15 — owner reassigns all three preparation packets to Claude

Slawomir subsequently directed: "let's have Claude work on the prep-work, claude is nearly done with her work and she can jump on that". This explicitly supersedes the Codex/tuner assignments in the preceding three-packet selection. Assign W177936, W177937 and W177938 to baton.claude, serially after the current W61599 implementation handoff: production context qualification first, viewer activity connection second, final correction/restart C proof packet third. Do not interrupt or release Claude's W61599 claim. If W61599 returns for an in-scope correction, complete that release work before further preparation. Codex remains available for independent reviews.

The preparation-only scope, durable dossier ownership and acceptance boundaries remain unchanged. No implementation, tests, live provider/actual engine execution or production enabling is added. W161234 B still awaits W61599's independently reviewed shared-file release. Priority selects qualification ahead of the other two; the two remaining low-priority items retain their creation order and explicit serial instruction.

## 2026-09-15 — Claude prepares; tuner implements downstream work

Slawomir added "tuner can do the work" after assigning the preparation packets to Claude. The working division is Claude for W177936/W177937/W177938 preparation and baton.tuner for downstream implementation once the concrete packet is selected and required inputs/file ownership are ready. This clarifies the prior assignment; it does not move the three preparation Works back to tuner. Each preparation handoff must recommend the exact tuner execution scope and evidence references. W161234 B still follows W61599 independently reviewed shared-file release. Preparation-only authority remains unchanged; this role selection is not a claim, an unbounded implementation assignment or authorization for a live qualification experiment.


## 2026-09-15 — resume Claude's approved preparation after owner review

Owner review of the stopped W61599 state is complete: owner178644 accepted correction178427 and released shared files; owner178645 selected W161234 B for tuner. Slawomir now reports that Claude is not picking up work, in the context of the already-approved Claude-prepares/tuner-implements plan. Resume that selected preparation: W177937 viewer activity connection, then W177938 final correction/restart proof packet.

This explicitly supersedes OWNER-STOP-177898.md's temporary prohibition on these two queued preparation tasks and Claude's stop acknowledgment178462. The original implementation claim177898 ended before its deadline and is not resumed. No new W61599 producer edit, implementation, live experiment, broad suite or baseline repair is authorized. Claude owns only each preparation dossier and hands exact concrete execution packets to baton.ops for tuner follow-through. Revalidate accepted W61599 candidate/review and W161234 current state; do not edit tuner's shared source files or active dossier. Existing independent review and scope boundaries remain.

## 2026-09-15 — preparation complete (claim 178694)

**The wiring already exists end to end, and exactly one line ignores it.** That
is the finding worth keeping. `attempts.attempt_activity_of` →
`job_manager/delegation.py:989` → `job_manager/projection.py:703` already carry
the manager's count into the published status document at
`stage["runtime"]["activity"]`. `tools/job_viewer.py:323` then discards it and
writes the constant `UNKNOWN`. The connection is a read, a format and a
predicate — not a new backend, not a second reader, not a protocol change — and
W167896's first stated rule, that the viewer has no backend, survives intact.

**The rule that shapes the display is owner ruling M174788**: the instant is
manager RECEIPT time, never evidence of continued provider activity. So a live
stage may show a relative age and a terminal one may not — it shows the absolute
instant, marked historical. A relative age beside `completed` is the exact
misreading this Work exists to prevent, and it is now a required test rather
than a caution.

**Two absences stay distinct and neither is ever a zero.** No runtime or no
activity member is "nobody looked"; a recorded attempt whose `bytes_observed` is
`None` is "nothing observed yet". The producer cannot emit a zero, and a zero
would read as "observed, and empty" — a claim this manager has no evidence for.

**The injected/restored-HOME unknown needs no viewer special case and must not
acquire one.** An unproved baseline publishes nothing, so the existing `unknown`
branch already covers it; a "baseline unproved" display would be the viewer
reporting a fact it does not hold.

Deliverables: `PACKET.md`
`sha256:aaa30c9dd529d245f89b1d0645a00c85d5769a94b31b8b8d1411751646a7db28`,
`BASELINE-177937.json`
`sha256:74549807f5749f955bdcfc60129db7d5f2107c4e076e2c9b277ce2758522f329`,
`HANDOFF.md`. All three viewer paths revalidated against accepted W167896
`candidate-168326.json`; all six producer paths revalidated against the
**accepted correction** `correction-178427`, not the originally submitted
candidate. Preparation only; new measured verification 0 s.
