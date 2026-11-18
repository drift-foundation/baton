# G2 — test_correction_restart: cause found, corrected, 26/26 (M385104, review 2026-11-18T05-42-59Z)

K, copilot under owner claim E384905, no claim held. Test-side correction only: no product byte changed
(`v12/worker/`, `v12/python/src/` untouched). Candidate over committed 314e067c: `candidate.diff`
(2 files, +97/-4), `CANDIDATE-SHA256.txt`. Group: tools-pure (module `tests.tools.test_correction_restart`,
the only importer of `tests/tools/correction_restart_trace.py`). No live/Docker/group/scans/full run.

## Initial failure, reproduced and traced before any edit

`01-positive-initial-failure.log`: `just test-one ...UsefulCorrection.test_useful_correction_reaches_managed_target`
fails in 3 s with `"failure": "preparation did not answer"`, child `runtime-single-5` exit 1, `"log": ""`,
exchange terminal `faulted` / `fault_code: agent` / `describe` answered, `work` faulted — identical to the
five-group run and to B0. The child's log was empty because the prepare branch of the fixture's
`MANAGED_CHILD` printed nothing on an agent exception (the apply branch already did), and `baton_worker`
reports an agent exception as a bounded code, never a message.

`02-traced-child-initial-failure.log` (`trace-child.py`, a scratch harness patching only the child source
and the fixture, product untouched): the retained trace is
`reconciliation_task.PreparationRefusal: the preparation harness changed the derived candidate; its output
cannot substitute for the Git tree`, raised by `export_derived_objects` (`v12/worker/reconciliation_task.py`
line 443) from `reconciliation_entry._written`.

`03-traced-child-measure-diff.log`: `measure(exported-candidate)` vs `measure(states["combined"])` differ by
exactly one entry: `__pycache__/scale.cpython-313.pyc` (281 bytes) in the combined tree. The pinned harness
(`from scale import scale`) was run by `run_bounded` with the inherited environment; the simulated child
runs under `python -B`, which covers only the child's own imports, not the harness it starts.

CONFIRMED cause: the fixture's simulated container (`ProcessEngine.__call__` Popen) did not carry the image
environment. `Dockerfile.reconciliation` and `Dockerfile.integration` declare `ENV PYTHONDONTWRITEBYTECODE=1`,
inherited by every process in a real container, so there the harness writes no bytecode and the exported
tree equals the measured one. The product refused correctly (a harness-mutated derived tree must not
substitute for the Git tree); the simulation lacked the environment that makes the harness non-mutating.
Product bytes of `reconciliation_task.py`/`reconciliation_entry.py` are unchanged since 3700408c (2026-09-14).
OPEN: why the 2026-09-15 green runs (run-C-180423-7/9/10/11) passed with the same product bytes is not
established from retained evidence; the test-shell environment of that day is not recorded.

## Second layer, exposed once the preparation answered

`04-positive-after-environment-fix-wrapper-drift.log`: with the environment alone, both positive scenarios
run to `completed` and fail only in the validator: `C1-incomplete-evidence` detail `'role'`. The validator
read the review and apply launch documents as bare containers (`launch["role"]`, `schema != /4`,
`"provider_context" not in launch`) while the product delivers the accepted `baton.worker-launch/5` wrapper
(AMENDMENT-376531) around a `/3` Job container — the same test-side drift G1 repaired in test_launch.
`scenario-artifact-c1-before-validator-fix.json` is the completed artifact (reviews[*].launch and
apply.launch: wrapper `/5`, wire profile `typed-adapter-file-exchange/1`, payload `/3` with `role`,
`job_execution`, no `provider_context`).

## Changes (test fixtures only)

`tests/tools/correction_restart_trace.py`:
- `CONTAINER_ENVIRONMENT = {"PYTHONDONTWRITEBYTECODE": "1"}`; `ProcessEngine` launches the simulated
  child with `dict(os.environ, **CONTAINER_ENVIRONMENT)`.
- prepare branch of `MANAGED_CHILD` traces `PreparationAgent.work`/`consider` and `baton_worker.handle`
  exceptions to the child's log (as the apply branch already did), so a fault is never an empty log.
- `validate`: new `launched(document, role, code)` requires the exact `/5` wrapper members, wrapper schema and
  wire profile from `launch_owner`, a `/3` payload with the expected `role`, no `provider_context` at either
  level, and returns the payload; used for `C1-review-context` (job_execution attempt still checked) and
  `C1-apply-context`. Nothing else in the oracle changed.

`tests/tools/test_correction_restart.py`:
- `test_preparation_fault_reports_terminal_before_fixture_cleanup` now also requires the child's exit 1 and
  that its log carries the injected message and a traceback (retention proved, not assumed).
- NEW `test_a_harness_that_writes_into_the_derived_tree_is_refused_and_the_reason_is_retained`: removes
  `CONTAINER_ENVIRONMENT` and the ambient variable, runs the real scenario, and requires the original
  symptom (`preparation did not answer`, terminal `faulted`/`agent`, child exit 1) WITH the retained
  `PreparationRefusal ... the preparation harness changed the derived candidate` in the log. Product refusal
  of a harness-mutated tree and fixture retention of the cause, in one measured case.
- `test_reviewer_context_or_writable_line_access_is_rejected`: the producer-context mutation now targets the
  `/5` payload (the product-faithful place) and adds two rows: context bolted onto the wrapper, and a bare
  `/4` context document in place of the wrapper; all three refuse `C1-review-context`.

## Outcomes, in the order the review asked

| step | command | result | time |
|---|---|---|---|
| positive pair after both fixes | `just test-one` UsefulCorrection.test_useful_correction_reaches_managed_target + CountedReopen.test_manager_recomposition_preserves_both_positive_counts | OK 2/2 (`05-positive-after-both.log`) | 7.2 s |
| negatives + transaction boundary (module) | `just test-one tests.tools.test_correction_restart` | OK 25/25 (`07-module-25-after-validator-fix.log`) | 20.2 s |
| two witnesses | injected fault + harness-mutation refusal | OK 2/2 (`06-witnesses.log`) | 4.4 s |
| final module | `just test-one tests.tools.test_correction_restart` | OK 26/26 (`08-module-26-final.log`) | 22.1 s |

The useful correction reaches the verified corrected target (C1-target-bytes/receipt/revision through the
real `git show refs/heads/main:scale.py`), and the counted manager reopen preserves both positive counts
with no duplicate provider or engine invocation (C2 oracle unchanged). All 22 G2 ids pass; the two
InvalidEvidence classes now start all 19 of their tests. No negative case was weakened or disabled; no
receipt or final outcome is mocked: the provider and engine simulations and the connected scenario are as
before.

Source identity (`tools.source_identity --declared v12`): HEAD 314e067c, changed 2 (the two test files),
consumed 41, digest `26132d98114df7e5c7b5e933176eebc4a89e0804afbf9345cc2cbca620aa49f6`, identical before
and after the final module run (`source.json`, `source-after.json`). `/var/tmp` 376 before and after every
run here (`var-tmp-before.txt`, `var-tmp-after.txt`); the fixtures of this module leave nothing.

## Not done, per the ruling

The two queued test issues (diagnostic-rendering pin, operator-view shared-root residue), the nine fixture
leak sites, any group retry and the final suite. No product change was needed, so no owner decision arose.
