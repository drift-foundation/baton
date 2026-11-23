# W385695 internal checkpoint 1 — delivery evidence

2026-11-23, base 580b85a8. CONTRACT-PROPOSED-385720.md section 8 checkpoint 1
only: trust-root inspection, the exact owner decision and the CLOSED admission
boundary. No publication worker, staging, deadline enforcement, custody,
intake, review handoff or verdict is implemented, claimed or stubbed.

## What was delivered

| Path | Role |
|---|---|
| `v12/python/src/baton_v12/job_manager/publication_recovery.py` | the owner module: selected identities, approved profile, trust-root inspection, decision, prerequisite evaluation, closed gate |
| `v12/python/tools/publication_decision.py` | installed `manager publication-inspect` and `manager publication-decide` |
| `v12/python/tools/publication_ports.py` | `HostOutput` and `SourceCorrespondence`, the two owner ports this capability adds |
| `v12/python/src/baton_v12/worker_manager/workspaces.py` | `retained_output_of`, the proved and measured read of an attempt's ORIGINAL output |
| `v12/python/src/baton_v12/job_manager/documents.py` | `stage.publication-gate`, the closed review gate's own contract |
| `v12/python/tools/job_manager.py` | dispatch of the two verbs from the installed command |
| `v12/python/tests/job_manager/test_publication_recovery_admission.py` | 66 focused cases, registered in `tools/parallel_test.py` |

## Acceptance

```
env BATON_V12_DISK_ROOT=/scratch BATON_V12_STACK_TEST_ROOT=/scratch \
  TMPDIR=/scratch PYTHONPATH=v12/python/src:v12/python \
  python3 -m unittest -v tests.job_manager.test_publication_recovery_admission \
    tests.job_manager.test_retained_recovery_admission \
    tests.job_manager.test_role_contract
```

217 tests, zero failures, zero errors, zero skips, 8.556 s. `focused.log` is
the verbatim run; `evidence.sha256` and `candidate.sha256` pin it and the
delivered bytes.

Neighbour regressions also run clean at this base: `test_retained_recovery_
execution`, `test_retained_failure_analysis`, `test_proposal_output_limit`,
`test_templates` (371 tests), `test_tool`/`test_submission`/`test_creation`
(201), `tests.manager.test_workspaces` (148), `test_documents`/
`test_contracts_inventory`/`test_store`/`test_scheduling`,
`tests.tools.test_parallel_runner` (73).

## Pre-existing failures NOT introduced here

`tests.manager.test_dependencies` fails one case at this base and at
580b85a8 identically: `review_cycles.py:freeze_recovered_checkpoint` takes an
undeclared `candidate` operand (W385625's surface). `tests.manager.
test_boundary_inventory` fails the same 5 cases of
`CallerResolvedReadsClosuresAndReplays` on the unmodified base tree and on
this one; both were measured by extracting 580b85a8 with `git archive` and
running the same command. Neither is in this slice's scope.

## Limits this checkpoint states about itself

A checkpoint is partial evidence, never "resume supported". An approval
returns a HELD PREREQUISITE naming the `/4` publication stage vocabulary, the
`worker-pool/2` publication lane, Job store generation 10, the deterministic
publication worker and the enforced `output-publication-review/1` control
profile. Nothing is reserved, bound, submitted or offered; the review gate is
closed and non-runnable. No live provider, engine or container; no
existing-instance migration or schema upgrade; no deployment change; no
mainline Git operation; the original failed Job remains failed and
`native-w385624-admission-1`'s retained output is untouched.
