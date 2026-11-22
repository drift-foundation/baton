# W385623 / Stage 1-A — correction result: the automatic path, connected

Canonical owner Work `2b077949-W385623` / `T385623`; template
`baton.v12.job-template.implementation-review/3`; governing Job profile
`baton.v12.native-handoff-heavy/1` (provider 7200 s, stage 9000 s, overall
21600 s including queue, verification 900 s). This is a **separate execution
of the independent reviewer's correction**, not a restart of the prior native
Job `905166b2-W1` and not an acceptance of it: that Job's clocks, allowance and
evidence are untouched, and its review returned changes-requested.

## Base and candidate

**Retained base: `f13e0b1255cfd43e145fe2ced565704e888e3e17`** — the prior
candidate commit `baton candidate: w385623-native-analysis-1`, whose own
declared base is `72e1093dccb3ded9763fd2c42f0f713a7ff2c88f`. This correction
starts from the retained candidate and not from the original base; the three
product/test paths that candidate added are present at its exact bytes:

| Path at the retained base | SHA256 |
| --- | --- |
| `v12/python/src/baton_v12/job_manager/failure_analysis.py` | `dd20652ee9e96fae7b5b7e1548c300cbddb4c9902b2ef15371c9f57be770d815` |
| `v12/python/tests/job_manager/test_retained_failure_analysis.py` | `e3512ff352dafc8d33c1c1f3afc280320c61876d5b368348f5860f8abe786610` |
| `v12/python/tools/parallel_test.py` | `b93b69fa1242f867be2457bf8bee86c557d8d4ef9395f6d8131577ee37b92760` |

`tools/parallel_test.py` is **unchanged by this correction**: no new test
module is added, so no new registry or `CONSUMED_INPUTS` entry is owed.

### Changed paths and why

| Path | Change | Lines | SHA256 |
| --- | --- | --- | --- |
| `v12/python/src/baton_v12/job_manager/failure_analysis.py` | +592: new section 10, the configured production path | 2370 | `93ea0d63b26b93ba91d7b4da2bcb20dcf80a61d0d310be9082636711219b692b` |
| `v12/python/src/baton_v12/job_manager/manager.py` | the one production caller: a level-triggered pass in `sweep` | 1418 | `81d248e45382f2ce31f1266501e2beab6d4764ecbe2bea4eba9c1ee07a8d8dba` |
| `v12/python/src/baton_v12/job_manager/documents.py` | the closed `recovery.analysis` record and the sweep's optional `analysed` | 944 | `98ecc49e4c1703294e218f7dbcfb40e2f9229b4513ed6c5690d995181b5ceb22` |
| `v12/python/src/baton_v12/job_manager/delegation.py` | `ManagerOperations` carries the seam as an optional capability | 1338 | `09540d55ae1bf3348c52abc5f58ca46458bcc72431187549076486e6d7ff0915` |
| `v12/python/src/baton_v12/job_manager/__init__.py` | exports the operation and its configuration contract | 157 | `88ef704bee1ce09f29c6426829b567fe8a4884ea4acdc3ace67261ce9d52ef5f` |
| `v12/python/tools/stage_execution.py` | the deployment producer: configuration, declaration, execution, seam | 7920 | `29527776391475b18277836e96ca4f68660d064cdddf4c7cf9b4830f83958fa6` |
| `v12/python/tools/single_worker.py` | one additive keyword: the non-stage workload document's NAME | 4475 | `a84abfb4cd4b5b2dd3363332c0d1c16ee2a7bd47be44acf1c5705655194e8efb` |
| `v12/python/tests/job_manager/test_retained_failure_analysis.py` | +53 ids: section 12, the configured production path | 2729 | `88dbd90aa85da975d022926f18a093f5c66a6f8a13437a0fedc0347f6d8834c2` |
| `v12/python/tests/tools/test_stage_execution.py` | +9 ids: the deployment producer and the exposed seam | 13559 | `dcad80a5266e5660a01f8f3acdf0458b24ce726c8804aee2d9eb888f4685ce9c` |
| `.../native-stage-1a-385623/REPORT.md` | corrected group accounting + appended Correction section | — | — |
| `.../native-stage-1a-385623/manifest.json` | `owning_group.modules` 32 → 31, `modules_ok` 27, `corrections` | — | — |
| `.../PROGRESS.md` | this correction's attributable entry | — | — |
| `.../PLAN.md` | the current checkpoint and the pending owner Git checkpoint | — | — |
| `.../evidence/native-stage-1a-correction-385623/` | added: this report, its manifest and the retained logs and ledgers | — | — |

`git status --porcelain` reports exactly those paths — thirteen modified files
and one new evidence directory — and nothing else. No Git state was mutated:
no add, commit, branch, tag, push, checkout or reset.

### Test-change accounting, stated rather than assumed

The Job template carries a generic "bounded test-change scope: none", and the
assignment says in as many words to **extend
`tests.job_manager.test_retained_failure_analysis` or connected tests for
actual production behavior**. The assignment governs, and AGENTS.md's standing
test-change authority (owner ruling 2026-09-13) supplies the authority without
a further per-test approval. What was actually done, so a reviewer can check
it rather than take it:

* **Added**, never edited: 53 ids in a new section 12 of the acceptance
  module, and 9 ids in `tests/tools/test_stage_execution.py` — in the class
  that already owns the equivalent judgment-configuration cases.
* **No existing assertion, expected behaviour or registry entry was changed
  or removed.** `tools/parallel_test.py` is untouched.
* Three fixture helpers in the acceptance module were extended or moved,
  with every prior default unchanged: `failed_attempt` and `analysed_attempt`
  gained an optional `attempt_id` (a production case must use the episode's
  own derived identity and the pass's own derived analysis identity);
  `analysis_outputs` was extracted out of `analysed_attempt` verbatim so a
  replay worker can start on one tick and freeze on a later one; and
  `submission`'s control profile became an overridable class attribute so one
  case can submit a Job that selects no finite control and isolate the
  analysis's own bound.
* The proof that none of that weakened anything: **all 87 prior ids are
  present and pass, by name.**

## The reviewed finding, and what closes it

> `failure_analysis.py` is library-only. No production caller triggers
> `observe_terminal_failure` / `admit_dispatch` / `deliver_analysis` /
> `deliver_endpoint`, and no deployment producer supplies
> `baton.v12.recovery-analysis-worker/1`.

Both halves are now connected through existing owners.

### 1. The production caller is the Job manager's own tick

`manager.sweep` gained `_analyse`, placed **after** `_recover_endings` and
before the capacity settlement. It is reached by every `tools/job_manager.py
serve` tick, every `--once` reconcile and every resume; nothing else in this
tree had to change to reach it.

`failure_analysis.advance_recovery(store, seam, *, now)` is the pass:

1. **Observe.** `settled_trigger_endings` enumerates, from the Job store's own
   owned identities, every SETTLED `ending.settled` record of an
   `implementation` episode whose disposition is the trigger's `unable`.
   `triggered_ending` then asks the one consequence-free question — did the
   worker declare `verification-failed` — and `observe_terminal_failure` does
   the rest. An ending this store has already attributed is recognised by its
   derived failure KEY (`_attributed`) rather than by re-observing it.
2. **Dispatch.** For a failure at `analysis-intended`: the Job's own fence,
   then the admitted deadline, then the evidence revalidation, then
   `admit_dispatch` — and only then the launch. The dispatch intent is
   committed BEFORE the external effect it authorizes, which is the whole of
   REC-3 here and is asserted directly by a case that reads the journal from
   inside the launch.
3. **Deliver.** For a failure at `analysis-dispatched`/`analysis-reported`: a
   frozen result is read first (a completed one delivers the report; the other
   three dispositions are the finite endings they name), then an unaccounted
   launch, then the fence, then the admitted deadline, and otherwise the
   execution is re-entered under **the same attempt identity**.

**Level-triggered, not edge-triggered**, and that is the point. An edge hook
on the ending would see exactly the endings a live process saw, and the fault
cuts this contract enumerates are precisely the moments a process is not
there. Everything the pass decides comes from durable state, so a restarted
incarnation with no cache and no live exchange continues the same recovery.

`ManagerOperations` carries `recovery_analysis` as an optional capability
beside the runtime start and the three exchange halves. **Absent is an
answer**: a deployment that declares no analyst reaches none of this and its
sweep report carries no `analysed` member, which is what leaves every accepted
operations object in this tree — including the read-only status surface —
behaving exactly as before.

### 2. The declared worker and profile are PRODUCED by the deployment

`failure_analysis.declared_analysis_worker` is the producer:
`check_analysis_declaration` was the validator and had no maker. A deployment
states the four facts that are its own — `worker_id`, `participant`,
`principal`, `capability_digest` — and the schema, the role, the
owner-approved `stage1-analysis/1`, its digest and the permitted output set
come from the definition the module holds and digests at import. **An operator
cannot select an unapproved profile by typing one**, and nobody transcribes
`a4be8b48…` into a configuration file.

`tools/stage_execution.py` is the deployment:

* `analysis_worker` is a new **optional** configuration member, held by
  `_held_analysis` before anything is opened — the worker identity against
  every stage worker and judge, the complete worker deployment through
  `single_worker._held`, this Authority, the accepted `review` launch
  contract, a participant that serves **no stage of this deployment**,
  retained reports, the one configured workspace storage, and every path
  outside the checkout. It then produces and validates the declaration.
* `AnalysisExecution` composes the turn over the **accepted non-stage worker
  lifecycle** — `single_worker.worker_operations`, the same one
  `JudgmentExecution` uses — with the Job manager's own derived attempt
  identity as its intent. No new launcher, launch protocol, credential
  posture or mount rule.
* `RecoveryAnalysis` is the seam, exposed as `recovery_analysis` on the
  composed operations object the serving loop already hands to `sweep`.
* `single_worker` gained ONE additive keyword, `workload_document_name`,
  defaulting to the accepted `judgment.json`. The analysis input is delivered
  as `analysis-input.json`: a future analysis image reading
  `/input/judgment.json` for a verification failure would be reading a path
  that lies about what is in it. Every existing deployment composes the same
  bytes at the same name (`tests.tools.test_single_worker` 255/255).

### 3. The analysis attempt identity is DERIVED

`analysis_attempt_id(key)` derives it from the failure key, so an exact retry
reuses it, a restart composes the same execution, and no seam is ever handed a
fresh identity to order a second turn with.

## What is preserved, and how it is proved

| Guarantee | Where the production path keeps it |
| --- | --- |
| Exact approved profile | The intent's `profile`/`profile_digest`/`policy` come from the held definition; a case asserts 4800 s, queue-included, 0 retries, the derived deadline and the digest `a4be8b48…`. |
| Validated immutable evidence | `_fixed_input` recomposes the failure's own input and refuses a digest mismatch **before the launch**, as well as before delivery. An invalid retained candidate is REPORTED every tick and never used. |
| Task attribution | The six-selector key, the episode, the candidate base/head/tree digest, the verification argv and status, and the executing participant all travel in the failure record; a case compares them to the real retained ending. |
| Role limits | `_analysis_result` still refuses a frozen analysis result carrying any output outside `PERMITTED_OUTPUTS`; a production case replaces the frozen result with one carrying a `git-change-proposal` and the tick refuses `policy/denied` with no owner item. |
| Cancellation | A Job cancelled before its ending is attributed earns no admission, is reported as a visible hold on every later tick, and orders nothing. One cancelled mid-turn delivers `analysis-cancelled`. |
| Expiry | Delivered as `analysis-expired` both before any dispatch and mid-turn; the original Job's own fence is read first and its TRIGGER decides the word, so a Job expiry is never reported as a cancellation. |
| Unknown cessation | A launch the control store cannot account for HOLDS — never read as "nothing was launched", never relaunched — and the owner-approved bound is what makes the hold finite: one `analysis-unknown-cessation` item, qualified, with no replacement. |
| No retry, no recursion | A delivered owner item is terminal; ten ticks produce one turn, one dispatch record and one item. The analysis attempt has no Job-store ending record to be observed, and an ending by the declared analyst is refused by the tick. |
| No mutation | The candidate's custody bytes and the whole ending record are compared across the path; no fresh attempt, successor or correction round is opened. |

W385624's owner decision and successor admission and W385625's
verification/review recovery remain unimplemented and their graphs untouched.
`fresh_attempt.py`, `review_driver.py`, `job_control.py`, `episodes.py` and
`cancellation.py` are unchanged.

## Verification

Deterministic throughout. No provider, model, adapter, image, container or
Docker daemon; no live instance; no nested live-provider test; no full suite.
Interpreter 3.13.5, `jsonschema` 4.19.2, `BATON_V12_DISK_ROOT` =
`work/scratch/w385623-verification`.

**What is real**: the Job store with its submission, stages, episodes,
`ending.register_ending`/`settle_ending` records, cancellation fence, finite
control and operations journal; the control store, its line, writer and
attempts; the retained result manifests; the MEASURED candidate and analysis
trees on disk-backed storage; the composed typed failure cause; and every act
of `failure_analysis` driven by the real `manager.sweep`/`reconcile`.

**What is faked, and only at its normal boundary**: the DEPLOYMENT, and the
analysis worker's TURN. The deployment is `fixtures.FakeOperations` — the same
stand-in `test_sweep` drives the tick with, and whose composition against the
real operations object is `test_delegation`'s — for most cases, and the REAL
`ManagerOperations` over an Authority-bound port for the case that drives the
whole path through the production surface. The turn is a deterministic replay
that writes its frozen result into the real control store and real custody;
there is no provider, model, adapter, image or container in this module at
all, which is what the contract asks for: "scripted analysis demonstrates
orchestration/evidence fidelity, not live diagnostic quality".

**Nothing in the acceptance module calls `observe_terminal_failure`,
`admit_dispatch`, `deliver_analysis` or `deliver_endpoint`** — mechanically
checked: those four names appear exactly once in section 12, in a comment
saying so. Every trigger, dispatch and delivery below happens because the
tick derived that it was owed.

Affected logical groups (TESTING.md's nine): **`job_manager`** and **`tools`**.

### Submitted verification — `submitted-verification.log`

The configured command, run exactly as configured:

```
bash -c 'set -euo pipefail; mkdir -p work/scratch/w385623-verification;
  export BATON_V12_DISK_ROOT="$PWD/work/scratch/w385623-verification";
  cd v12/python; export PYTHONPATH=src;
  exec python3 -m unittest -v tests.job_manager.test_retained_failure_analysis'
```

**Ran 140 tests in 3.312 s — OK, exit 0.** 140 collected, 140 passed, 0
failed, 0 errors, 0 skipped (`acceptance-command.log` is that exact command's
own log; `submitted-verification.log` is the same module, measured separately
at 3.288 s).

**All 87 prior ids are present and passing, by name** — the prior run's id set
is a strict subset of this one, checked name by name against
`../native-stage-1a-385623/submitted-verification.log`. The 53 new ids are
section 12 and they drive the real tick:

* the whole path in two ticks, one owner item, exact retained lineage, the
  owner-approved profile and deadline, `reconcile` reaching the same pass, and
  the SAME path driven through the real `ManagerOperations` with an
  Authority-bound port rather than a stand-in;
* a deployment with no seam observing nothing, and a misconfigured or
  incomplete seam contained as a condition that does not stop the tick;
* only a SETTLED producer failure observed — not a registered-but-unsettled
  ending, a completed ending, a provider failure or a review ending — and an
  invalid retained candidate reported rather than used;
* ten ticks producing one turn; a second incarnation continuing from the
  durable records; an in-flight analysis re-entered under one identity;
* every finite ending reached by the tick itself, including the lost launch's
  hold and its qualified unknown-cessation item, the analysis's own admitted
  bound in isolation, and a finite ending never retried;
* the no-mutation proof, both recursion exclusions, the producer's refusals,
  the derived identity, the seam contract and the closed tick-report document.

### Focused regressions — per-ID counts and measured durations

Each module in its own process with a fresh TMPDIR and disk root
(`touched-seam-ledger.tsv`).

| module | collected | outcome | duration | why it is here |
| --- | --- | --- | --- | --- |
| `tests.tools.test_stage_execution` | 508 | 8 failures (environmental, identical to baseline) | 353.1 s | the deployment producer, the seam and the configuration boundary |
| `tests.tools.test_single_worker` | 255 | OK | 23.1 s | the one additive `workload_document_name` keyword |
| `tests.tools.test_parallel_runner` | 73 | OK | 18.9 s | the registry, group and consumed-input sweep over the real tree |
| `tests.manager.test_attempt_failure_cause` | 117 | OK | — | the typed worker declaration and cessation axis the trigger reads |
| `tests.tools.test_job_task_delivery` | 87 | OK | — | the input-root delivery the new document name reaches |
| `tests.job_manager.test_sweep` | 48 | OK | 0.3 s | the tick the new pass was added to |

`tests.tools.test_stage_execution`: **baseline 481 collected / 8 failures;
candidate 508 collected / 8 failures, and the eight failing ids are
IDENTICAL** (`baseline-stage-execution.log` vs
`candidate-stage-execution.log`). They are the integration-stage lifecycle
cases, which need engine/target facts this environment does not supply; the
baseline was measured on the retained candidate before any change here.

The verbose candidate log above was captured one comment-only edit before the
submitted bytes; `touched-seam-ledger.tsv` is the re-run **on the submitted
bytes** and reports the same 508 collected and the same 8 failures.

### Owning group `job_manager` — `job-manager-group-ledger.tsv`

**31 modules** (30 existing + 1 this Work added), **1862 collected, 1773
passed, 88 failures, 1 error, 0 skipped. 27 modules OK.**

**Four fail for the environment and not for this change** — the same four, with
the same counts, that the prior run reported and proved orthogonal by running
each with the change moved aside:

| module | collected | non-passes now | non-passes in the prior run |
| --- | --- | --- | --- |
| `test_fresh_attempt` | 159 | 85 failures | 85 failures |
| `test_native_permission` | 20 | 1 error | 1 error |
| `test_store_readonly` | 31 | 1 failure | 1 failure |
| `test_tool` | 72 | 2 failures | 2 failures |

Their cause is recorded rather than waived: these cases need a disk-backed
directory OUTSIDE the checkout, the checkout here IS `/output`, `/var/tmp` and
`~/.cache` are not writable by this process, and `/tmp` is a tmpfs the
workspace boundary correctly refuses. `BATON_V12_STACK_TEST_ROOT`, which the
refusal itself names as the fix, cannot be satisfied here. **No
`OPTIONAL_SKIPS` entry was added and no coverage was weakened.** An existing
unrelated failure is not acceptance of any new behaviour here.

### Corrected group accounting

The prior REPORT/manifest said the owning group holds **32** modules and that
**28** were OK. Both are wrong: `job-manager-group-ledger.tsv` has 31 rows —
30 existing plus the one this Work adds — of which 4 report `FAILED`, so 27
were OK. `../native-stage-1a-385623/REPORT.md` now carries the corrected
paragraph plus an appended **Correction** section, and its `manifest.json`
carries `owning_group.modules: 31`, `owning_group.modules_ok: 27` and a
`corrections` member naming exactly what changed and why. No measured count,
log or ledger byte was rewritten.

### What was NOT run, and why

* `just test-group job_manager` / `just test-all`: `just` is not installed and
  the prepared interpreter at `~/.local/state/baton-v12-venv` is absent, so
  this run has **no `--account` ledger and no content-bound source-identity
  document**. Every module was run one process per module on the ambient 3.13.5
  with the hash-locked `jsonschema` 4.19.2 already present, and the counts
  above are per-ID from each run's own output. The submitted verification
  command is itself plain `python3 -m unittest`, so it is unaffected.
* A full suite, a Docker-daemon campaign, nested live-provider tests, live
  instance or configuration changes, mainline import and main-checkout Git
  mutation: all excluded by the assignment and none attempted. No Stage 1-B or
  1-C behaviour and no W385635 task-preflight work.

## Open items for the reviewer, stated rather than resolved

* **The container half of `AnalysisExecution` is not re-proved here.** It
  composes the accepted non-stage worker lifecycle — the same
  `single_worker.worker_operations` path `JudgmentExecution` uses, whose launch
  document, credential boundary and mount posture are owned by
  `tests/tools/test_single_worker.py` — and what this Work's own cases prove is
  the CONFIGURATION, the produced declaration, the exposed seam and the whole
  ordering above it. Driving a real container for an analysis turn needs a
  Docker daemon campaign the assignment excludes.
* **A dispatch whose very first launch refuses is an unknown, not a retry.**
  The dispatch intent is committed before the launch, so a launch that refused
  without creating its attempt is indistinguishable from one that launched and
  lost its reply. The reviewed module's ruling is that `unknown` HOLDS; this
  pass honours it and makes the hold finite with the owner-approved bound,
  rather than re-ordering a turn. If the owner wants a transient launch refusal
  distinguished from a lost reply, that is a new decision about
  `reconciled_dispatch` and not something this correction took.
* **Unavailable accounted runner** and the **four pre-existing environmental
  failures** above, carried forward unchanged from the prior run.

No unresolved product or authority decision arose, so no
`handoff/request.json` was written and nothing was escalated to `baton.slaw`.
