# C1 — useful correction through reviewed managed import

Work: W180245 (`2b077949-W180245`), queued at baton.ops for execution selection.
Parent for joined acceptance: W161234. Created by W180092 under owner
reroute180210. Blocks W180252 (C2).

Full specification: `baton:work/records/2026/09/finding-v12-c-proof-split/SPLIT.md`
sections 2, 2a, 4 and 5a. Source packet:
`baton:work/records/2026/09/finding-v12-correction-restart-final-proof-preparation/PACKET.md`
section 3.1, sha256 `941b423395e311d668bef62bd3e3be2813f10b113c672bf260207729bbaf136e`.

## What this Work has to show

An initial deterministic provider writes a meaningful function with the wrong
requirement — multiply-by-2. A **genuine** verifier executes those bytes. A
**real** independent changes-requested review produces the next same-line
episode. A fresh attempt writes multiply-by-3, a separately pinned verifier
executes the revised bytes, independent review finishes, and the accepted managed
preparation / judgment / apply / target-receipt / final-outcome path runs to
completion.

**What makes it non-vacuous:** the old and revised code digests differ, the
verifier really executed both, the verdict and routing are the owners' own, and
the target receipt names the revised bytes. **A correction that only changes a
disposition row proves nothing.** Isolation is asserted, not assumed: reviewer
mounts and identities exclude producer context and the writable line.

## The prerequisite is a real product defect, not a fixture problem

This is why the combined C attempt stopped, and it is confirmed independently in
`review-2026-09-15T18-22-50Z.md`. Every symbol below was revalidated against the
current tree at W180092 claim180212.

The preparation worker measured **combined 0, original base 1, isolated revised
0** — exactly the failing-base / passing-candidate shape a useful correction
should produce. Then:

- `v12/worker/reconciliation_task.py:1027 compose_report` deliberately reports the
  **first nonzero** status across the observed sequence, so the aggregate is 1.
- `v12/python/src/baton_v12/integration/reconciliation.py:3145`, inside
  `adopt_prepared_candidate`, decides eligibility with
  `passed = account["kind"] == "measured" and account["status"] == 0`, and at 3147
  reports the failure as *"the retained preparation did not pass its combined
  command"*.

**The combined command passed.** The decision substitutes the sequence aggregate
for a specific measurement and then misdescribes it.

The correction is to **the adoption decision only**, keeping the raw report and
aggregate intact. The individual measurements already arrive:
`_preparation_account` passes the full ordered completed statuses through
`managed_execution.collected_report`. No new wire schema, no fabricated receipt.

**The symbol is `adopt_prepared_candidate`.** `HANDOFF-C-180069.md` named
`adopt_managed_preparation`; both names exist in that module and the handoff named
the wrong one. Do not act on the handoff's name.

### Explicitly not changed

**`compose_report` keeps its first-nonzero aggregate.**
`tests/manager/test_reconciliation_task.py:642
test_a_genuine_base_failure_is_a_real_integer` already pins aggregate 1 for
exactly combined 0 / base 1 / isolated 0. Changing it would break an existing
observation contract in order to fix another module's misuse of it.

Also unchanged: `managed_execution.py`, the fourteen EXECUTION-B paths, the six
W61599 producer paths, `schema.py`, `store.py`, `documents.py`, the frozen
contracts, `review_cycles.py`, `job_manager/review_driver.py`, the scheduler, the
Authority and the accepted integration code.

The legacy `_causal` owner (base-must-fail, isolated-must-succeed) **illustrates**
the distinction. It **must not** be invoked as a fixture bypass, and its
predicate must not be imposed on every managed preparation incidentally.

**The fixture must not be made to pass instead.** The handoff is explicit that no
workaround was implemented and none is authorized: do not skip the original-base
failure, do not fabricate owner evidence.

## Acceptance

1. Initial and revised code digests differ and the verifier really executed both.
2. The changes-requested verdict and routing are the owners' own, obtained through
   the real review cycle rather than synthesized into the artifact.
3. The target receipt names the **revised** bytes.
4. Reviewer mounts and identities exclude producer context and the writable line.
5. The unchanged scheduler-trace digest still validates.
6. Exact candidate hashes, the environment and provenance bundle and the measured
   selectors are recorded in this dossier.

For the source correction, all five checks from the review: measured combined 0 /
base nonzero / isolated 0 reaches awaiting-evidence with original statuses and
custody retained; a genuinely failing combined command stays blocked and retained
with the actual reason reported, and isolated failure is never promoted merely
because combined passed; missing, unrun, timed-out and untagged-invalid evidence,
wrong command identity or order, harness/source/content mismatch and changed
retained custody remain refused or held through their owners; accepted ordinary
all-zero preparation behaviour is preserved unless the owner explicitly selects a
broader causal-admission policy; and the real retained-object adoption path and
its replay are exercised before C1 consumes it for the target receipt.

## Invalid-evidence cases owned here

Each rejected by the same companion validator, each labelled synthetic invalid
evidence, none ever an owner receipt:

- revised code byte-identical to the initial code;
- a verifier that did not actually execute the revised bytes;
- a target receipt naming the initial bytes;
- an absent or forged changes-requested verdict;
- reviewer isolation breached, with producer context or the writable line
  reachable.

## Baseline — released partial work, preserved

From `HANDOFF-C-180069.md`, re-verified on disk at claim180212 and matching
`partial-C-180069/`:

| Path | sha256 |
| --- | --- |
| `v12/python/tests/tools/correction_restart_trace.py` | `e0dc7a466c184f3e72ace320045f26a5e14af7874f855f8d7cd83e56d283506c` |
| `v12/python/tests/tools/test_correction_restart.py` | `ef7ad4379977bab317e1e2b3fdca7fc2b9e96c4c20e07eb8713303a308a6d3e3` |

**These are unaccepted drafts.** The companion validator is a schema/predecessor
placeholder; the invalid-evidence selectors do not exist; the post-preparation
collection branch is unexecuted. Their envelope is **not** verified evidence.
All five UsefulCorrection development runs failed — runs 3–5 reached the
exceptional preparation and run 5 captured the cause — and those failures and
their positive cleanup evidence are preserved, not erased. Start from these
bytes; do not reset or delete for a clean start.

Also assigned here by the handoff: the successful result collector's per-Job
integration wrapper access needs checking. (The engine counter's operation-label
operand is C2's.)

## Ownership and boundaries

C1 holds both files above from claim to acceptance and **releases them by name
and hash** in its handoff; C2 may not claim them before that release is recorded.
Selectors are disjoint: C1 owns `UsefulCorrection` and
`UsefulCorrectionInvalidEvidence`.

Run plan is PACKET §7 unchanged: from `v12/python` with the repository-pinned
interpreter and `PYTHONPATH=src:tools:.`, each selector in its own process group
under an owning supervisor, 180 s per scenario, TERM 5 s then KILL 5 s, positive
proof of group absence after each, each scenario under 100 logical ticks.

Not authorized: live model or provider, actual OCI engine, image build or pull,
broad discovery suite, rerunning the eighteen predecessor schedules, baseline
repair, certifying production restoration, claiming host-failure exactly-once,
editing `v12/python/DEPLOYMENT.md` before acceptance, or any Git mutation. **If
C1 demonstrably needs a source boundary beyond the one scoped above, report the
exact required change for scope disposition — do not hide it in a test helper.**

W177936 production qualification is separate and is **not** a precondition: C's
default provider is the deterministic fake/replay seam and its provider evidence
is labelled simulated. Accepted A and B evidence stays untouched.

Then baton.feat independent review, then baton.ops.

## 2026-09-15T18:35:37Z — owner selects C1 execution by baton.tuner

Slawomir explicitly agreed to the proposed bounded C1 correction and proof scope
after confirming that W180245 is at baton.ops for the owner decision. This selects
baton.tuner for execution, then baton.feat independent review and baton.ops for
acceptance. Claude released the completed split and dossiers at pass180284;
baton.prompt records the selection after that release. This supersedes the
pending-owner-selection wording above and in the original plan.

Two inherited combined-C statements are explicitly superseded for C1:

- The exclusion of "accepted integration code" has one selected exception:
  `v12/python/src/baton_v12/integration/reconciliation.py`, limited to the
  `adopt_prepared_candidate` managed-preparation eligibility correction described
  above. Preserve the raw aggregate/report, ordinary all-zero behavior and all
  failure, timeout, identity, custody and replay checks. Focused regression paths
  are `v12/python/tests/integration/test_managed_storage.py` and, where needed for
  the retained-object path, `v12/python/tests/tools/test_managed_preparation.py`
  or `v12/python/tests/tools/test_managed_apply.py`. Other source exclusions stand.
- C1 selects `UsefulCorrection` and `UsefulCorrectionInvalidEvidence`, plus the
  focused correction tests. The original plan's "three supervised selectors"
  does not apply after the split. `CountedReopen` and
  `CountedReopenInvalidEvidence` remain exclusively C2's scope.

Revalidate current source and the released partial hashes before implementation.
Complete the real reviewed correction/import path and its negative evidence;
do not substitute fixture results for owner evidence. Preserve accepted A/B and
prior failures. The existing per-run supervision and positive cleanup checks
remain required. No live provider, actual OCI, broad/predecessor suite, Git
mutation or W177936 dependency is added. C2 stays blocked until C1 acceptance
and explicit release of both shared files by accepted hashes. New decisions
outside this bounded scope require a concrete finding, not an expanded C1 job.

## 2026-09-15T18:38:00.194687+00:00 — claim180298 revalidation

Released C partial hashes and all21 prior read-only inputs match. Reviewed the exact current adopt_prepared_candidate boundary and owner180294 selection. BASE-180298.json snapshots six potentially selected files before changes, including optional retained-path tests; only paths actually changed will enter the candidate. Preserve worker aggregate1 for base failure; eligibility requires complete measured combined/isolated success while allowing either base status. Retain incomplete/failure reports as blocked with accurate reasons; existing owners keep identity, command, custody and timeout validation. C1 executes no manager reopen; preserve the old draft reopen helper for C2 without calling or claiming it. Focused storage adoption tests and the two C1 selectors are selected; no predecessor schedules run. Shared files remain exclusively C1-owned until accepted release.

## 2026-09-15T18:44:27.975363+00:00 — claim180298: adoption corrected; apply context-declaration blocker

**Observed and measured:** the selected adoption correction preserves raw aggregate1 and advances combined0/base1/isolated0 to awaiting-evidence. The focused `PreparedEligibilityUsesCandidateMeasurements` selector passes17 tests (run1), including retained-object custody/replay, all-zero behavior, actual combined and isolated failure reasons, incomplete/timed-out holds and inherited identity/harness/source/custody guards. Synthetic storage fixtures are explicitly labelled unit inputs. C1's separate real worker path reaches managed result state `authorized` with independent judgments after the genuine reviewed multiplier correction. It then faults before ManagedApplyAgent.work. No target/final receipt or C1 acceptance exists.

**Exact new failure:** run7's apply child traceback ends at `v12/worker/baton_worker.py:1709` in handle, calling context_declaration, then line2565: `WorkerFault: context receipt is reserved for implementation and isolated review`. The real apply input retains the optional reserved declaration from the Job input; apply's integration role is rejected merely because that declaration is present. The agent work wrapper emits no failure because the workload has not been entered. `OBSERVATION-180298.json` is a verbatim parsed diagnostic from `run-C-180298-7.log`, including actual managed result and stage/exchange observations. Describe answered, work faulted with input; managed preparation aggregate1 remains retained and state authorized.

**Confirmed source interaction:** handle calls context_declaration for any declared provider-context-receipt, even without a context-bearing launch. context_declaration allows only implementation or review. B intentionally made the optional receipt part of the shared input, while ordinary managed integration consumes that input under an integration launch. C1 now reaches this unexercised consumer. The source byte hash of baton_worker.py still matches accepted B. This is distinct from the corrected adoption decision and requires a new bounded source assignment. No omission of the shared declaration, role relabelling, context guard monkeypatch or owner-result substitution is used to bypass it. Existing fake-engine context-qualification seam remains labelled simulation; the new traceback wrapper only observes and rethrows the real exception.

**Proposed scope disposition:** choose the manager/worker contract for a context-free managed apply consuming the shared optional declaration. A correction must retain mandatory implementation context, isolated review absence, no producer private-state delivery to integration, reserved-declaration integrity, and receipt provenance. Revalidate whether the normal manager should derive a context-free runtime declaration or the worker should allow the exact optional declaration absent for integration; this claim selects neither design without authority. The smallest demonstrated entry is baton_worker.py context_declaration/handle, an explicitly excluded accepted-B path. Focused tests for context-free apply and existing implementation/review guards would accompany the selected correction.

Current C1 execution is **incomplete**, superseding the in-progress action: return baton.bug, next baton.ops, for this exact source disposition. The adoption fix and17 passing focused tests are preserved for independent review; no independent acceptance has occurred. `partial-180298.patch`, base snapshots, partial snapshots and EVIDENCE-180298.json bind the three changed files. The original five failed combined-C runs remain untouched. The current C1 harness calls no manager reopen; its old draft reopen method is retained for C2 but unexecuted. UsefulCorrectionInvalidEvidence and the companion validator remain unfinished, and successful target-result collection remains unexecuted. C2 remains blocked and receives no accepted release.

Measured this claim: seven supervised runs, run1 passes17 and runs2–7 fail; run3 was an error in the diagnostic extractor (implementation-only helper used for integration), corrected in the owned new harness. Other C1 runs fault in apply; run7 establishes the exact cause. Every process group is absent, no timeout, each scenario stayed within100 logical ticks. New author 17.276815144054126s, cumulative author 179.28393344706274s; prior reviewer93.48170357503113s remains separate. No further runtime verification follows the confirmed source stop. All read-only inputs including accepted B and the worker aggregate remain unchanged. Optional selected managed-preparation/apply test files and test_correction_restart.py are unchanged.

Source-search note: an exploratory `v12/worker/managed_apply*` glob matched no file; actual integration_entry.py and integration_workload.py were read. No required dossier, policy, handoff or source input is unreadable.

## 2026-09-15T18:48:11Z — independent source-stop assessment180371

review-2026-09-15T18-48-11Z.md confirms the real manager/worker declaration
mismatch. single_worker._held accepts the exact optional reserved receipt for
context-free integration; baton_worker.context_declaration rejects integration
merely for declaring it, before ManagedApplyAgent.work. The apply workload
already answers its unused declarations missing-optional. Launch/context owners
continue to restrict actual provider context to implementation.

TRIAGE-180371.json checks55 current/base/snapshot/evidence hashes and recorded
current modes, all matching, including21 read-only inputs and14 B paths.
OBSERVATION-180298.json equals the parsed run7 diagnostic: complete measured
combined0/base1/isolated0 with aggregate1, managed state authorized, integration
describe answered/work input-faulted, no ending or completion digest. The source
and preserved deterministic child evidence agree. No independent test rerun or
old process-group inspection occurred; cleanup remains author-receipt evidence.

Proposed disposition: select only baton_worker.py context_declaration/handle to
permit the exact optional declaration on a validated context-free integration
launch, preserving all declaration checks and refusing actual context delivery
or a produced/present context receipt. Prefer this to manifest rewriting; it
matches the manager's existing representation of absence. The review specifies
focused test_single_worker/test_managed_apply/test_claude_context cases and
remaining C1 acceptance. This is a proposal requiring the actual source-scope
exception; no product/test changes or fixture bypass were performed by reviewer.

Static assessment found no further adoption defect; the17-test pass remains
author evidence and the partial has not received independent final acceptance.
Preserve all partial bytes and old failures. C1 still owes target/final receipts,
review isolation and companion validator/invalid-evidence completion. C2 remains
blocked without accepted shared-file release. W177936 is independent.

This completes pending independent triage and supersedes it with baton.ops
selection as the current action. New reviewer test runtime0s; author cumulative
179.28393344706274s and reviewer93.48170357503113s unchanged and separate. No
required input was unreadable. No live provider/OCI or Git mutation occurred.

## 2026-09-15T18:54:42.709050+00:00 — owner180421 source exception selected, claim180423

Owner180421 selects review-2026-09-15T18-48-11Z.md SHA25647d596a85008f34c1ebf8960718e5cd31ff5a9f4d7533248bb7763303b7d9bb3. This explicitly supersedes the accepted-B source exclusion only for baton_worker.py context_declaration/handle: allow the exact optional reserved declaration for a validated ordinary integration launch with no context schema/member, while rejecting delivered context (including null), a present receipt, or a physically produced reserved path before completion. Preserve mandatory implementation delivery/receipt, review isolation and exact declaration checks. The focused regression paths are test_single_worker.py, test_managed_apply.py and applicable test_claude_context.py guards; use existing cases where adequate. Other B source stays unchanged. No context manifest rewrite, live provider/OCI, C2 execution or broadened design is selected.

All partial180298 and immutable input hashes revalidate. BASE-180423.json snapshots the resumed and newly selected files. Continue the adoption partial and complete C1 real target/final receipts, isolation and independent invalid-evidence validation. This supersedes worker-boundary awaiting-selection as current action. Prior cumulative author179.28393344706274s and reviewer93.48170357503113s remain separate.

## 2026-09-15T19:13:35.729375+00:00 — baton.tuner claim180423 candidate complete, awaiting independent review

CANDIDATE-180423.json SHA256 2e7107ecbfc133374e1811e33e99e3764924c20f90ceb22ab71683a00d834499 binds seven exact files and reconstructible baseline-relative bytes. EVIDENCE-180423.json SHA256 7ebf7dcf65b6e2242cb8ced6d200da7f6f94486c259b6e9f6f92d5a7a3932659 binds all eleven current run receipts. HANDOFF-180423.md records the two selected source corrections, exact test changes, provenance, failures, cleanup and review scope.

Final run9 passes5 negative test groups rejecting13 labelled synthetic corruptions; run10 passes2 positive/artifact tests including18 unchanged predecessor schedule artifacts without schedule execution; run11 passes36 focused regressions. Actual C1 reaches revised multiplier3 target bytes through independent review and managed preparation/judgments/apply/import, final completion and root-ended capacity in23 ticks. The original aggregate1 remains measured; no fixture bypass. All run groups are absent, no timeout, source bytes stable. This author claim32.104145374090876s, cumulative author211.3880788211536s; prior reviewer93.48170357503113s separate.

Reviewer source isolation is checked at the actual frozen checkpoint head and read-only /input/source mount, with private-context absence. The source checkout may reuse the former producer host path read-only; an exploratory assertion incorrectly rejected that accepted configuration and is corrected. This clarification does not authorize writable producer-line or private-context access. Deterministic provider/simulated OCI evidence exercises actual worker children and owner transitions; no physical OCI isolation or live-provider qualification is claimed.

This explicitly supersedes claim180423 in-progress and earlier incomplete worker/C1 status as the current action. Pass baton.feat for independent review, then baton.ops. No independent acceptance yet. Release the seven candidate paths for review at their manifest hashes; C2 stays blocked pending C1 acceptance and explicit accepted release of both shared files. No C2 execution or external release.

## 2026-09-15T19:18:29Z — independent C1 acceptance180553

review-2026-09-15T19-18-29Z.md independently accepts candidate180423 manifest
2e7107ecbfc133374e1811e33e99e3764924c20f90ceb22ab71683a00d834499 under
owner180294/180421. The selected adoption and context-free integration fixes
resolve both source blockers without changing raw aggregate, mandatory
implementation context, isolated review or custody/provenance contracts.

Independent43 tests pass:2 positive/artifact tests,5 negative groups rejecting13
synthetic corruptions,36 focused source/context regressions. The actual
deterministic correction reaches imported/completed and ended capacity in23
ticks, with distinct attempts and revised multiplier3 target bytes; the target
receipt names the actual target revision. Both real verifier subprocesses are
attributed to their measured code. Review source is frozen and read-only with
private context excluded; OCI isolation remains simulated.18 unchanged predecessor
artifacts validate without schedule execution. No C2/live provider/OCI work.

REVIEW-EVIDENCE-180553.json SHA256
715d34ff5b04673dccb7971b275666ca9ef2d0a84d774ed917c58b18b46761dc
binds independent exports and receipts.75 provenance checks match per run;
zero-fuzz patch reconstruction matches all seven paths. Source bytes/modes
remain as reviewed, all process groups absent, no timeout. New reviewer test
time11.401970032020472s, cumulative104.8836736070516s; author cumulative
211.3880788211536s separate; reconstruction0.002610712981550023s separate audit.

The shared correction_restart_trace.py is accepted/released at
b40057b231c0c102a2b67790c02ed2f506169caa364a6763c28dd4064684422f and
test_correction_restart.py at
a9a861f732331b5b4dae839a028d4b27a0316da2599f5f9f610d42973803cfae.
These become C2's baseline after ops acceptance/closure and C2 selection/claim;
the dependency remains until that transition. Return baton.ops with no further
C1 correction requested. This explicitly supersedes pending independent review,
not historical failures or W161234's remaining C2/joined acceptance.
