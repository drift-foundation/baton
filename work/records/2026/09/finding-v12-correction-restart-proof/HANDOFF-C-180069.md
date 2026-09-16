# W161234 C incomplete — managed preparation source disposition

Author: baton.tuner, claim180069, owner selection180064. Destination baton.bug,
next baton.ops. This is a reproduction and partial-work handoff, not a candidate
for independent acceptance. The accepted B candidate179255 remains unchanged.

## Blocking observation

The selected useful correction reaches the real managed preparation after a
real changes-requested review, manager handle close/recomposition, and revised
multiply-by3 provider/verifier execution. The preparation worker reports:

| State | Actual verifier exit |
| --- | --- |
| combined | 0 |
| original base, with pinned revised harness added | 1 (scale module absent) |
| isolated revised candidate | 0 |

`v12/worker/reconciliation_task.py:compose_report` takes the first nonzero
command exit as aggregate status. The managed adoption in
`v12/python/src/baton_v12/integration/reconciliation.py:adopt_managed_preparation`
requires aggregate zero and blocks this result, claiming the combined command
failed. The actual combined command passed. The existing causal observation
validator in that module requires base failure and isolated success.

Run5 preserves the real retained result, exact content/verifier digests,
phase reports and causal output in `run-C-180069-5.log` and its verbatim parsed
diagnostic in `OBSERVATION-C-180069.json`. No owner report was replaced. The
provider is a deterministic local subprocess; OCI engine observations are
simulated. The real preparation worker executes as a local child.

## Requested disposition

Select a bounded correction of preparation status interpretation and managed
adoption, with focused tests for base nonzero / isolated zero / combined zero.
Keep measured statuses and failure/timeout/absence gates honest. This requires
product source outside C's two-file authorization. Do not make this fixture skip
the original-base failure or fabricate owner evidence to get a pass. No such
workaround has been implemented. FINDING records the observed behavior,
confirmed source boundary, proposed correction and scope stop.

## Preserved partial work and remaining C scope

Only these new test files plus this dossier were written:

- `v12/python/tests/tools/correction_restart_trace.py`, SHA256
  `e0dc7a466c184f3e72ace320045f26a5e14af7874f855f8d7cd83e56d283506c`.
- `v12/python/tests/tools/test_correction_restart.py`, SHA256
  `ef7ad4379977bab317e1e2b3fdca7fc2b9e96c4c20e07eb8713303a308a6d3e3`.

Matching snapshots are in `partial-C-180069/`. They are incomplete drafts:
the companion validator is only a schema/predecessor placeholder;
CountedReopen/InvalidEvidence selectors do not exist yet; the successful
post-preparation collection branch is unexecuted. Do not treat these files as
accepted tests or publish their envelope as verified evidence.

After the source prerequisite, complete the accepted C packet: managed
preparation/judgment/apply/import/target/final receipts; exported owner and
review-isolation evidence; provider and engine input counters with positive
before/reopen/after baselines; distinct corrected use counted exactly once;
independent companion rejection of each synthetic duplicate, missing baseline,
absent reopen, changed verdict/checkpoint/attempt attribution and forged receipt;
unchanged predecessor artifact validation; all three selected supervised runs;
exact candidate provenance and independent baton.feat review, then baton.ops.

The current engine counter's operation-label operand and the successful result
collector's per-Job integration wrapper access also need checking when completing
the draft. No complete counter/duplicate assertion or end-to-end C acceptance
is claimed by the preparation reproduction.

## Verification and custody

`BASE-C-180069.json` records all21 read-only input hashes/modes and both new-file
absences before implementation. All still match, including all14 accepted B
files. `EVIDENCE-C-180069.json` SHA256
`6f25ed30f1bb28474465262795cf3165cc089a3b16101c6199f89ebb9b2f6e14`
binds the partial snapshots, logs, run receipts and static source observations.

Five UsefulCorrection development runs failed. Run1 hit a fixture report-digest
depth limit, run2 a fixture method/Path name collision; both were corrected in
the new harness only. Runs3–5 reached the exceptional preparation; run5 captures
the precise owner cause. Each used the pinned interpreter and source hashes,
180s maximum with TERM5/KILL5 and subreaping; each stayed within100 logical
ticks and proved the owned process group absent. Total new author15.190110625029774s;
cumulative author162.0071183030086s; prior reviewer93.48170357503113s is separate.

No live model, actual OCI, build/pull, broader suite, predecessor schedule rerun,
baseline repair, B edit, DEPLOYMENT.md edit or repository Git mutation occurred.
No target/final receipt or valid C trace was produced. W177936 production
qualification and whole-Work closure remain separate.

Exploratory guessed DESIGN.md and baton_reconciliation.py paths were absent;
FINDING records that operational observation and the successfully read canonical
design and reconciliation_task.py replacements. No required input is unreadable.

Current action is in `PLAN.md`; attributable implementation history is in
`PROGRESS.md`; newest independent review remains the accepted B review
`review-2026-09-15T16-15-23Z.md`. This partial C has not had independent review.
