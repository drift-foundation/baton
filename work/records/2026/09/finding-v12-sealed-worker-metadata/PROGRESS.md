# Progress

Implementation has not started. The assigned change author appends attributable
checkpoints here; planning and review evidence remain separate.

## 2026-09-06 — baton.tuner, claim event 105607

Revalidated the frozen contract and inspected baseline as recorded in FINDING.
Initial test path SHA-256:
`bcde113356225f2659608f7d45f99284d4189e27ba243eae276cfd67a79d448c`.

Positive carrier checkpoint: added a regression with distinguishable namespaces
and reversed completion output order, using real `OciAdapter.seal`,
`retain_manifest`, store close/reopen, and `load_manifest`. Before the correction,
the loaded output metadata was `{'alpha': {}, 'zeta': {}}`; the test failed at
the expected preservation assertion. The same test now passes after carrying
the validated envelope's metadata by name in both output branches. It also
asserts assignment, operation, observation, input/policy digests, measured
content and manager artifact identity/custody.

Command (from `v12/python`):
`PYTHONPATH=src python3 -m unittest tests.manager.test_sealing.OpaqueWorkerMetadataSurvivesSealing -v`
— first exit 1, one expected failure; after correction exit 0, one test passed.
Optional/replay/refusal coverage and the bounded sealing regression run remain.

## 2026-09-06 — baton.tuner, candidate ready for independent review

The carrier acceptance is complete. Seven additive tests cover distinct opaque
namespaces across reordered outputs, real retained-result load-back after store
reopen, present/missing optional metadata, committed replay on a fresh adapter
after the completion changes or disappears, all three unsuccessful dispositions
without an envelope, and wrong-assignment/malformed-envelope/missing-required/
live-secret refusals before custody. Replay explicitly fails the test if the
completion reader is called. No existing test assertion or expected behavior
was edited.

Verification from `v12/python`, Python 3.13.7 and ambient jsonschema 4.19.2:

- `PYTHONPATH=src python3 -m unittest tests.manager.test_sealing.OpaqueWorkerMetadataSurvivesSealing -v`
  — exit 0, 7 tests passed, 0.021s.
- `PYTHONPATH=src python3 -m unittest tests.manager.test_sealing -v`
  — exit 0, 65 tests passed, 0.081s. This is the bounded regression sweep;
  no broader test campaign was run under this assignment.
- `git diff --check` from repository root — exit 0, no whitespace findings.

These are source-layout tests with fixture quiescence observations and real
sealing/custody/manifest storage; no Docker runtime or live authority is under
test. The installed locked jsonschema 4.26.0 build was not run. No failing
baseline was observed besides the intentionally demonstrated metadata loss.

Candidate fingerprints (SHA-256):

| Path | SHA-256 |
| --- | --- |
| `v12/python/src/baton_v12/worker_manager/sealing.py` | `fa127f926785eb0e3b56cda2359141f066b4de4851b3de1e7cd7d6d3f87fdada` |
| `v12/python/tests/manager/test_sealing.py` | `14948da920b3be30da0d5e881c6243d52cc13090682640f9d257049d952fe97a` |

Only those two paths and this dossier changed under this claim. No schema,
namespace interpretation, concrete-worker, integration, or Git state changes.
Status: awaiting independent review. Decision files: this record's `FINDING.md`
and `PLAN.md`; newest prior independent review remains
`work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-standalone-stage-composition/findings/finding-proposal-manifest-producer/review-2026-09-06T18-49-39Z.md`.
