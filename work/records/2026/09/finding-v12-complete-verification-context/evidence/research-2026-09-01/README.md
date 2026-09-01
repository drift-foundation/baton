# W61981 verification-context baseline — 2026-09-01

Reviewer: `baton.codex`

## Retained run5b input

- Evidence: `/tmp/w52821/run5/evidence.json`
- Proposal:
  `/tmp/w52821/run5/storage/attempt-w52821-run5b/custody/attempt-w52821-run5b/proposal`
- Proposal digest:
  `sha256:416d79a230fe090bf95d9d71e716ff09d67c4efdf2bb3373d618c19937a838aa`
- Frozen task: `/tmp/w52821/run5/task.json`
- Staged source digest:
  `sha256:0b04928d40473ba59c40d2d3521f9f0afbc19ff68c41127e881110a5cf847d34`

The retained artifact was not executed in place. Its candidate was copied to
`/tmp/w61981-review.s8gDxE/candidate`; the exact retained tree remains
untouched.

## Reproduction

From the isolated candidate copy:

```text
PYTHONPATH=src python3 -m unittest -v \
  tests.tools.test_user_credentials \
  tests.tools.test_dogfood_operator.TheDocumentedCommandIsOneGrantsFile.test_help_names_the_credential_source_the_launcher_requires \
  tests.tools.test_dogfood_operator.ThePublicRecoveryEndsAnInterruptedAttempt.test_a_recovery_asks_for_no_credential \
  tests.tools.test_dogfood_operator.TheArcMaterializesBetweenActivationAndRuntimeCreation.test_the_factory_runs_after_activation_and_before_runtime_start \
  tests.tools.test_dogfood_operator.TheDocumentedRecoveryEndsRealAttachedState.test_an_uncertain_runtime_settles_nothing_and_keeps_the_bearer \
  tests.manager.test_credentials.TheTrustedProfileMapsEverySlot.test_the_reference_is_opaque
```

Result: 102 tests, 99 pass, 3 errors. Each error is the same pre-assertion
`FileNotFoundError` from `tests/manager/test_output.py:139`, for a missing
canonical vector derived from repository layout.

## Minimal complete review layout

```text
/tmp/w61981-review.s8gDxE/context/
  v12/python/                         # independent candidate copy
  work/records/2026/08/
    finding-v12-isolated-agent-workers/
      findings/finding-v12-worker-contract/findings/
        finding-worker-control-api-manifests/evidence/vectors.json
```

The immutable vector came from the current canonical repository record. With
working directory `context/v12/python` and explicit `PYTHONPATH=src`, the exact
argv above ran 102 tests in 0.252 seconds and passed. No other repository file
outside the candidate was needed by this measured gate.

This layout is a baseline, not an implementation shortcut. The future worker
and operator must independently materialize it from a manager-copied, sealed,
manifest-described immutable input source; they must not read the host checkout
by absolute path or mutate the retained candidate.

## Exact current seams

- Operator task hold: `v12/python/tools/dogfood_operator.py::held_task`
- Operator staging/manifest: `stage_source`, `input_manifest`,
  `run_dogfood_task`
- Worker task hold: `v12/worker/claude_agent.py::_task`
- Worker candidate/verification: `ClaudeAgent.work`, `ClaudeAgent._verify`
- Independent rerun: `v12/python/tools/dogfood_operator.py::_derived`
- Generic multi-source/root freeze:
  `v12/python/src/baton_v12/worker_manager/workspaces.py::copied_manifest` and
  `compose_input_root`
- Input source uniqueness/overlap rules:
  `v12/python/src/baton_v12/contracts/manifest.py::_check_input_manifest`

