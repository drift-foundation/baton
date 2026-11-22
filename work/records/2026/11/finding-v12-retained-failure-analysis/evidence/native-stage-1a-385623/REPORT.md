# W385623 / Stage 1-A — native implementation result

Native Work `905166b2-W1`, template `baton.v12.job-template.implementation-review/3`,
control profile `native-handoff/1`. Assignment:
`evidence/native-kickoff-385631/TASK.txt`, SHA256
`41888451a1c7ff9afbf02ae6cca46caafec2787ef9ec3b9d46694b1424ce1212` (verified in
this candidate). Read before implementing: `AGENTS.md`; `v12/DESIGN.md` REC-8
(lines 862–906); `v12/python/TESTING.md`; this record's `FINDING.md`/`PLAN.md`;
the parent `STAGE-1-CONTRACT.md`
(`52c2c640fdbb791e70ae61edf7ef7db7190bacd767d6d044f678517d2e09e1bc`, verified);
the accepted `review-2026-11-22T05-18-37Z.md`
(`a2346faa809d78a955c464fa4d639e01a974fe859fa049a5947318da2a0988fd`); and the
approved profile definition `evidence/stage-1-contract-385615/stage1-analysis-1.json`
(`a4be8b48e098efc47f770a8b7f941b80eadd22b23c48eebf67863d3a4dc824ab`, verified).

## Candidate

Declared base: `72e1093dccb3ded9763fd2c42f0f713a7ff2c88f` (the preparation
packet's `9f4fbb2e…` plus the owner's checkpoint of the allocation records; REC-8
is applied in this base's `v12/DESIGN.md`).

| Path | Change | SHA256 |
| --- | --- | --- |
| `v12/python/src/baton_v12/job_manager/failure_analysis.py` | added, 1778 lines | `dd20652ee9e96fae7b5b7e1548c300cbddb4c9902b2ef15371c9f57be770d815` |
| `v12/python/tests/job_manager/test_retained_failure_analysis.py` | added, 1666 lines | `e3512ff352dafc8d33c1c1f3afc280320c61876d5b368348f5860f8abe786610` |
| `v12/python/tools/parallel_test.py` | modified (two additive registrations) | `b93b69fa1242f867be2457bf8bee86c557d8d4ef9395f6d8131577ee37b92760` |

`git status --porcelain` in this candidate reports exactly those three paths and
nothing else. No Git state was mutated: no add, commit, branch, tag or push.

### Why `tools/parallel_test.py` changed, and why that is not a test change

TESTING.md §6 requires a new test module to be in exactly one execution
registry, and §9 requires a file consumed outside `v12/` to be in
`CONSUMED_INPUTS` or the run's source identity refuses. Two additive entries:

* `tests.job_manager.test_retained_failure_analysis` into `PARALLEL_MODULES`
  (group `job_manager` by package, no carve-out).
* the one owner-approved profile definition file into `CONSUMED_INPUTS`, named
  by the smallest path actually read — the definition, not the dossier.

No existing registry entry, group, assertion or expectation was edited or
removed. The bounded test-change scope ("this task changes no test") is kept:
the acceptance module is an addition the assignment requires by name, and these
registrations are the mechanical discoverability TESTING.md demands of it.
`tests/tools/test_parallel_runner.py` — the sweep that enforces both rules
against the real tree — passes (73/73).

## What was implemented

`failure_analysis.py` owns Stage 1-A and nothing else. Its eleven sections map
onto the contract:

1. **The owner-approved finite profile.** `stage1-analysis/1` is held as the
   owner's definition document, and its exact UTF-8 bytes (final newline
   included) are reproduced and digested at import; a mismatch raises rather
   than `assert`s, so `-O` cannot strip the check. Every bound and clock origin
   — Job 4800 s including queue from the accepted admission, stage 4800 s from
   stage admission, provider 3600 s from the invocation's real start, zero
   retries and zero corrections — is READ OUT of that document rather than
   restated as integers. `admitted_deadlines` derives the Job deadline once, at
   admission, and persists it in the intent; the stage and provider clocks are
   deliberately NOT derived there, because their origins do not exist yet.
   The profile is **not** an entry in `job_control.PROFILES`: that table is an
   admitted Job's control and projects a verification-command ceiling the
   analysis execution has no use for, and writing one would state a bound the
   owner did not approve. This Job keeps `native-handoff/1`, as instructed.
2. **The declared analysis authority.** `baton.v12.recovery-analysis-worker/1`:
   role, worker, participant, principal, profile, profile digest, capability
   digest and the closed permitted-output set. No adapter, image, model or
   provider name appears anywhere in the module, and the validator refuses a
   declaration that names `implementation` or `review` as its role, selects an
   unapproved profile, misnames the profile digest, widens or narrows the
   permitted outputs, or carries one value as both participant and principal.
   An absent or unusable declaration refuses before anything is journalled.
3. **The failure key.** A digest over the six selectors the contract names —
   authority, Work, execution Job, stage, attempt, terminal-result identity.
4. **The trigger.** `classified_failure` validates the retained candidate
   against BYTES, not a commit name: one present `git-change-proposal` output,
   the artifact identity this attempt's own seal composed, the manager's own
   indexed artifact row agreeing with the retained manifest on identity, digest
   and locator, the artifact digest equal to the measured tree digest, and the
   worker's claim agreeing with its own ordinary-test observation about base
   and head. The typed ending is read through
   `worker_manager.failure_cause` — declared ending `verification-failed`, a
   verification attempted with a non-zero status that agrees with the
   observation, and no provider failure reason (the successful provider turn).
5. **The fixed input.** One immutable document, digested once, compared again at
   report time. Custody paths travel as locators, never as authority.
6. **The report contract.** Facts separated from hypotheses as a SHAPE rule,
   options with tradeoffs, a recommendation, and an optional proposed
   correction that is explicitly a proposal.
7. **Five durable records** — failure item, analysis intent, dispatch intent,
   analysis report, owner item — each one operation of the existing Job-store
   journal under a failure-key-derived identity. No schema change, no new
   table. Each reader proves the record's own key against the key it was
   selected by (a signature is not ownership). Replay identities exclude the
   observing clock and include every operand that makes the act the same act,
   so a second observation replays and a changed declaration, input or attempt
   collides.
8. **Reconciliation, cancellation and expiry.** `reconciled_dispatch` answers
   `none`, `launched` or `unknown`; `unknown` is an actionable hold naming the
   operation and attempt, and never a redispatch. Cancellation is rechecked at
   admission and again at dispatch through `cancellation.refuse_fenced`.
   Expiry is evaluated against the PERSISTED deadline.
9. **The automatic path.** `observe_terminal_failure` performs exactly two
   journal acts and no external effect. `admit_dispatch` reconciles, rechecks
   cancellation, proves the execution is the declared analyst's and checks
   expiry, all before it commits. `deliver_analysis` revalidates the original
   evidence, refuses any frozen analysis result carrying an output outside the
   permitted set, journals the report and delivers the owner item in one path.
   `deliver_endpoint` is the finite ending: `analysis-failed`,
   `analysis-expired`, `analysis-cancelled` or `analysis-unknown-cessation`,
   each preserving measured partials and delivering ONE owner item.
10. **Recursion is excluded twice** — by the declared analysis participant
    (configuration) and by this store's own dispatch records (history), so a
    renamed participant loses the first check and keeps the second.
11. **The derived disposition.** The failure record is written once and never
    updated; `recovery_disposition` answers the current state from which
    records exist.

### Deliberately not implemented

No owner decision surface, no successor admission, no corrected verification,
no review handoff and no receipt of any kind. W385624 and W385625 own those and
neither graph is touched. `fresh_attempt.py`, `review_driver.py`,
`job_control.py`, `episodes.py` and `cancellation.py` are unchanged; the
ordinary path asserts their journals are empty. No new launcher, scheduler,
pool control, hierarchy prerequisite, live configuration or historical recovery.

## Verification

Deterministic throughout. No provider, model, adapter, image, container or
Docker daemon; no live instance; no nested live-provider test; no full suite.
Real: the control store, its line, writer and attempts, the retained result
manifests, the MEASURED candidate tree on disk-backed private scratch, the
composed typed failure cause, the Job store with its submission, stages,
cancellation fence and operations journal. Faked only where a deployment
supplies it: the checkpoint profile, the fence port, and the analysis worker
declaration (which is configuration).

Interpreter 3.13.5, `jsonschema` 4.19.2. `BATON_V12_DISK_ROOT` set to
`work/scratch/w385623-verification` (ext4-backed; `/tmp` here is a 32 MiB
tmpfs, which is exactly what the selector exists for). The disk root is empty
after the run — the fixture cleans up what it creates.

### Submitted verification — `submitted-verification.log`

```
mkdir -p work/scratch/w385623-verification
export BATON_V12_DISK_ROOT="$PWD/work/scratch/w385623-verification"
cd v12/python; export PYTHONPATH=src
python3 -m unittest -v tests.job_manager.test_retained_failure_analysis
```

**Ran 87 tests in 1.546 s — OK, exit 0.** 87 collected, 87 passed, 0 failed,
0 errors, 0 skipped. The eleven classes cover: the ordinary end-to-end outcome
and its exact attribution; the trigger's eighteen explicit refusals; the
declared authority; wrong binding; duplicates and concurrent observation;
crash/restart at every fault cut including the lost-launch hold; the four
finite endings; the no-mutation proof (the whole control store compared
byte-for-byte across the path); the cessation axis unknown and positively
established; both recursion exclusions; and the owner-approved profile compared
to the published bytes.

### Focused regressions — per-ID counts and measured durations

Each module in its own process, with a fresh TMPDIR and disk root per module
(`job-manager-group-ledger.tsv`). Touched-seam regressions beyond the group:

| module | collected | outcome | duration |
| --- | --- | --- | --- |
| `tests.tools.test_parallel_runner` | 73 | OK | 16.34 s |
| `tests.manager.test_attempt_failure_cause` | 117 | OK | 0.78 s |

Owning group `job_manager`, all 30 existing modules plus the new one — 31
modules, 1809 ids total (**corrected**; see "Correction" below). Twenty-seven
modules OK. **Four fail for the environment and
not for this change**, proved by running each one in this same candidate with
`failure_analysis.py` and the acceptance module moved aside and
`tools/parallel_test.py` restored from the declared base — the failing id sets
are IDENTICAL in both directions:

| module | collected | with the change | without the change | identical ids |
| --- | --- | --- | --- | --- |
| `test_fresh_attempt` | 159 | 85 failures | 85 failures | yes |
| `test_native_permission` | 20 | 1 error | 1 error | yes |
| `test_store_readonly` | 31 | 1 failure | 1 failure | yes |
| `test_tool` | 72 | 2 failures | 2 failures | yes |

Their cause is recorded rather than waived: these cases need a disk-backed
directory OUTSIDE the checkout, and in this isolated candidate the checkout IS
`/output`, `/var/tmp` and `~/.cache` are not writable by this process, and
`/tmp` is a tmpfs the workspace boundary correctly refuses. The refusal text is
in `baseline-*.log` and `candidate-*.log`. `BATON_V12_STACK_TEST_ROOT`, which
the refusal itself names as the fix, cannot be satisfied here. This is an
unaccounted shortfall of the environment, not a passed run: it is reported, not
reported as green.

Full-group ids: 1809 collected, 1720 passed, 88 failed, 1 error, 0 skipped —
all 89 non-passes in the four modules above and none in any module this change
touches or in the new one.

### What was NOT run, and why

* `just test-group job_manager` / `just test-all`: `just` is not installed in
  this candidate and the prepared interpreter at
  `~/.local/state/baton-v12-venv` is absent (`python3 -m tools.environment
  interpreter` refuses: "it has not been prepared yet"). The accounted runner
  and its JSON ledger and content-bound source identity are therefore
  unavailable here. Every module was instead run on the ambient 3.13.5 with the
  hash-locked `jsonschema` 4.19.2 already present, one process per module, and
  the counts above are per-ID from each run's own output. The submitted
  verification command is itself plain `python3 -m unittest`, so it is
  unaffected.
* A full suite, a Docker-daemon campaign, nested live-provider tests, live
  instance changes and main-checkout Git mutation: all excluded by the
  assignment and none attempted.

## Open items for the reviewer, stated rather than resolved

* **Unavailable accounted runner.** The absence of `just` and the prepared
  environment in this candidate means no `--account` ledger, no content-bound
  source-identity document and no `OPTIONAL_SKIPS` enforcement for this run.
  The per-module counts above are honest but are not that artefact.
* **Four pre-existing environmental failures** in the owning group, bounded and
  proved orthogonal above. They were not "fixed" by widening a boundary or
  adding a skip, and no entry was added to `OPTIONAL_SKIPS`.

No unresolved product or authority question arose, so no
`handoff/request.json` was written and nothing was escalated to `baton.slaw`.
Every semantic in the module traces to the contract, REC-8 or an existing
owner's vocabulary; nothing was invented and no refusal was retried blindly.

## Correction — 2026-11-22, W385623 correction Job

This section is appended, not a rewrite: the run, its logs, its ledger and
every other claim above are the original ones and are unchanged.

**The group accounting above was wrong and is corrected here.** The owning
`job_manager` group holds **31 modules in total — 30 existing plus the one
this Work adds — not 32**, and **27 of them were OK, not 28**. The correct
figures are now in the paragraph above and in `manifest.json`
(`owning_group.modules`, corrected from `32` to `31`, with `owning_group.modules_ok` added as `27`).

The source of truth for both is `job-manager-group-ledger.tsv`, whose bytes are
unchanged: it has exactly 31 rows, one per module, summing to 1809 collected
ids, of which 4 rows report `FAILED`. 31 − 4 = 27. The original text said "all
31 existing modules plus the new one", which double-counted the new module and
implied 32, and then reported 28 OK from that same error.

Nothing else in this report changes. The per-ID counts (1809 collected, 1720
passed, 88 failures, 1 error, 0 skipped), the four environmentally failing
modules and their orthogonality proof, the submitted verification (87/87) and
the two focused regressions are all as originally measured.

The independent review of this candidate returned **changes-requested**: the
module `failure_analysis.py` was library-only, with no production caller for
`observe_terminal_failure`, `admit_dispatch`, `deliver_analysis` or
`deliver_endpoint`, and no deployment producer for
`baton.v12.recovery-analysis-worker/1`. That correction is a separate Job and
its own result is at `../native-stage-1a-correction-385623/REPORT.md`; the
candidate bytes described above remain its exact declared base.
