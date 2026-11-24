# W385695 internal checkpoint 2 — delivery evidence

2026-11-23, base 6079ad78 (checkpoint 1 accepted). CONTRACT-PROPOSED-385720.md
section 8 checkpoint 2 only: the deterministic publication worker, read-only
staging, deadline enforcement and real fresh-assignment custody/intake, with
the review gate demonstrably closed until an exact handoff exists. Normative
v12/DESIGN.md REC-9 governs; the proposal's pending-approval wording is
superseded by FINDING.md "Consolidated owner selection — 2026-11-22".

Production review delivery, the reviewer's own tests and verdict, and the
packaged installed-CLI acceptance are checkpoint 3 and are neither implemented
nor claimed here.

## What was delivered

| Path | Role |
|---|---|
| `v12/python/src/baton_v12/job_manager/publication_execution.py` | NEW. The four acts: read-only staging of the approved original, the deterministic adoption under the fresh assignment inside the absolute bound, the ordinary freeze/intake custody comparison, and the one handoff record that opens review. Plus the absolute-deadline read, the review gate and the level-triggered pass. |
| `v12/python/tools/publication_worker.py` | NEW. `PublicationWriter` — the production deterministic adapter that adopts the staged bytes, writes the separate provenance and publishes the completion envelope, bounded by the absolute instant. `PublicationSeam` / `publication_seam()` / `staging_root()`. No `subprocess`, no provider, no credential. |
| `v12/python/src/baton_v12/job_manager/publication_recovery.py` | The admission became real: durable reservation, Authority assignment ending, Work reuse, deployment binding and servability, the `/4` submission, the completion record. Corrected the misleading guard documentation and the `refused/limit` hold pairing; removed the fabricated publication attempt identity. |
| `v12/python/src/baton_v12/job_manager/documents.py` | `baton.v12.job-submission/4`, the `publication` stage kind, `ORDINARY_STAGE_KINDS`, the `/4` shape rule, `stage.publication-handoff` and `publication.execution` contracts, the two optional publication-gate members. |
| `v12/python/src/baton_v12/job_manager/scheduler.py` | `baton.v12.worker-pool/2`, the publication lane, `STAGE_LANES`/`lane_of` (the implementation fallthrough is gone), per-generation lane/kind admission, and reviewer independence extended to the ORIGINAL producer's Job. |
| `v12/python/src/baton_v12/job_manager/schema.py` | Store generation 10: the 9→10 step rebuilds `pool_workers`, `stage_allocations` and `worker_affinity` to admit the publication lane, copying every row forward. `REBUILT_OBJECTS`/`REBUILD_VERBS`. |
| `v12/python/src/baton_v12/job_manager/store.py` | `JobStore.schema_version`, and the proof that a declared rebuild step replaces only objects an earlier step created. |
| `v12/python/src/baton_v12/job_manager/job_control.py` | The enforced `output-publication-review/1` profile, `SUB_BOUNDS` (the publication stage's absolute 900 s from its persisted execution admission), its enforcement inside `evaluate`, and `require_ordinary_profile` widened to every recovery profile. |
| `v12/python/src/baton_v12/job_manager/projection.py` | The publication gate, scoped to the review stage, ANDed with the dependency gates where eligibility is decided. |
| `v12/python/src/baton_v12/job_manager/templates.py` | An ordinary template cannot name the publication stage. |
| `v12/python/tools/publication_ports.py` | `PriorAssignment` — the minimal public seam for the supported `Session.end` ending, over the holder's own participant-bound session. |
| `v12/python/tools/fresh_attempt_ports.py` | `DeploymentBinding.publication_worker()` — the deployment's own answer about the installed worker, `None` for every instance that has not installed one. |
| `v12/python/tools/publication_decision.py` | The eighth, optional `ending` port composed and passed to the admission. |
| `v12/python/src/baton_v12/job_manager/__init__.py` | The publication-execution surface. |
| `v12/python/tests/job_manager/test_publication_recovery_execution.py` | NEW. 85 focused cases, registered in `tools/parallel_test.py`. |

## Acceptance

```
env BATON_V12_DISK_ROOT=/scratch BATON_V12_STACK_TEST_ROOT=/scratch \
  TMPDIR=/scratch PYTHONPATH=v12/python/src:v12/python \
  python3 -m unittest -v tests.job_manager.test_publication_recovery_execution \
    tests.job_manager.test_publication_recovery_admission \
    tests.job_manager.test_retained_recovery_admission \
    tests.job_manager.test_role_contract
```

302 tests, zero failures, zero errors, zero skips, 14.346 s. The prior
217-test coverage is PRESERVED EXACTLY: the three checkpoint-1 modules still
answer 66 + 74 + 77 = 217 together, and the new module adds 85. `focused.log`
is the verbatim run.

Neighbour regressions at this base: `tests/job_manager` whole directory 2203
tests OK; `tests.tools.test_stack`/`test_creation_ports`/
`test_connected_creation`/`test_parallel_runner`/`test_bootstrap` 447 OK;
`tests.manager.test_workspaces`/`test_output`/`test_intake`/
`tests.integration.test_managed_storage` 501 OK (3 skips);
`tests.manager.test_contracts_inventory` 15 OK.

## Pre-existing failures NOT introduced here

Measured on a `git archive HEAD` extraction of 6079ad78 and on this tree, with
identical results:

* `tests.tools.test_stage_execution` — 8 failures
  (`OrdinaryTerminalLifecycle`'s 7 and
  `ANewJobCreatedAfterAFollowsTheAdvancedTarget.test_the_successor_materializes_publishes_and_completes`).
* `tests.manager.test_dependencies` — 1 failure,
  `review_cycles.py:freeze_recovered_checkpoint` takes an undeclared
  `candidate` operand. Checkpoint 1's own report records the same one.

## Defects in checkpoint-1 source corrected here

1. **The vacuous scope assertion.**
   `test_publication_recovery_admission.OnlyTheAuthorizedOwnerDecidesAndOnlyInTheWorksScope.test_the_scope_is_the_works_own_and_is_not_an_operand`
   searched `publication_decision.main.__module__` — the string
   `'tools.publication_decision'`, a module NAME — so every `assertNotIn`
   in it was vacuously true and a surface that really grew an `--actor`
   operand would have passed. It now reads the real source through
   `inspect.getsource` and searches the argument parser's own operands.
2. **The misleading guard documentation.** The module docstring claimed
   `require_ordinary_profile` was "this module's own guard" over the recovery
   profile, template, role descriptor and stage set. It is `job_control`'s,
   it guards exactly the control profile, and at checkpoint 1 it named only
   REC-8's — so it would not have refused this recovery's own profile. The
   sentence is corrected and `job_control.RECOVERY_PROFILES` now holds both.
3. **`refused/limit` is not a pairing this build admits.** `_shape` raised
   its two ceiling holds as `refused/limit`, and `decide`/`admit_publication`
   re-raise the first hold under its own category and code — so an original
   over the selected declaration produced an `AssertionError` out of the
   error constructor instead of a refusal. Measured by driving a real
   101-entry original at it; the holds are now `integrity/limit`.
4. **A fabricated publication attempt identity.** `publication_attempt_id`
   derived a name that no claim would ever produce. Harmless while nothing
   executed; a durable admission record carrying it would have bound the
   handoff to an execution that does not exist. Removed;
   `publication_execution.fresh_assignment_of` reads the live episode.
5. **A per-Job gate would have deadlocked the publication stage.** REC-8's
   recovery Job has one stage, so its gate is per-Job; a publication recovery
   Job has two, and a gate answering for both holds the publication stage shut
   behind a handoff only the publication can produce. The gate is scoped to
   the review stage.
