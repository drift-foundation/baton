# Accepted assembly consumer handoff — 2026-09-09

W103083 independent joined acceptance: review-2026-09-09T17-57-08Z.md. Exact current five-file
hashes/modes: evidence/review-129777/manifest.json. Full bytes and newest
independent terminal/custody readback are retained at
../finding-composed-one-job-proof/evidence/review-129744/.

## Repeatable bounded fixture

From v12/python:

```sh
PYTHONPATH=src:tests:. python3 -m unittest tests.tools.test_stage_execution.OrdinaryTerminalLifecycle.test_one_job_completes_correction_integration_and_terminal_handoff
PYTHONPATH=src:tests:. python3 -m unittest tests.tools.test_stage_execution.OrdinaryTerminalLifecycle.test_the_recovered_job_finishes_and_its_manifest_reopens
```

These are exact selectors, not a request to rerun unchanged evidence. Full module
selector tests.tools.test_stage_execution passed160 cases. W119114 provider
reports are evidence/provider-129718.json and provider-129636.json in that dossier.
The newest reviewer probe.py additionally records actual terminal/result/pin
identities; run from v12/python with PYTHONPATH=src:.:tools and its absolute path.
The existing test fixture owns disposable root allocation and cleanup. Recorded
absolute roots in verification.json are historical locators, not reusable live
fixture installations; rerunning creates fresh roots.

ComposedOneJobCase in tests/tools/test_stage_execution.py owns the actual setup,
submission and task/input documents. OrdinaryTerminalLifecycle supplies the
accepted integration port, actual child integration entry and target verification.
The task is baton.dogfood-task/2, task_id w119114-composed-lifecycle;
source profile git-line, checkpoint/integration profile Git, declared base from
that fixture's own initial commit; verification argv is python3 harness.py.
One Job job-a carries implementation/review/integration stages for the same
Work and shared input digest, with optional role-specific output union. Actor
identities, instructions digest and fixture policy generation are configured
and validated against actual owner stores; no credential bytes are configuration.

Artifact selectors come from intake_receipt_of(control, corrected_attempt):
artifacts[].custody_locator/content_digest. Retained manifest selector comes from
frozen_output_of(control, corrected_attempt), then load_manifest(..., resultManifest).
Use publication_for_attempt for committed history after integration changes the
canonical target. Persistent line comes from deployment.line(), accepted
checkpoint from review_cycles.integration_checkpoint, and pin validation from
the accepted profile. Do not substitute the old fixture's absolute paths.

## Production composition entry points for later approved deployment

The configuration is BATON_V12_STAGE_EXECUTION_CONFIG naming the closed
baton.v12.stage-execution-deployment/1 document. Serving factory is
 tools.stage_execution:factory; status factory is
 tools.stage_execution:observing_factory. tools.job_manager accepts these
existing explicit inputs (placeholders require the later deployment's own values):

```text
python3 -m tools.job_manager --store <job-store> --incarnation <incarnation> --authority-uuid <uuid> submit --document <submission-json>
python3 -m tools.job_manager --store <job-store> --incarnation <incarnation> --authority-uuid <uuid> serve --control <control-store> --operations tools.stage_execution:factory
python3 -m tools.job_manager --store <job-store> --incarnation <incarnation> --authority-uuid <uuid> status --control <control-store> --observe tools.stage_execution:observing_factory
```

The bounded fixture uses a recording OCI boundary and real child workloads,
Authority/control/Job/coordinator stores and disposable Git. The retained serial
lane separately covers actual engine scenarios. These templates grant no live
launch authority and provide no multi-Job configuration before its approved cuts.
Ordinary lifecycle needs no operator transition; exceptional abandonment uses
accepted public A/B/C operations in W119114's recover helper.

## Carry forward

W122060's RESTART-ACCEPTANCE-2026-09-09.md owns the narrowed restart contract.
Reuse ordinary lifecycle and actual committed-handoff reconstruction/read-only
proof before additional hardening. Keep uncertain integration held.
W119403's worker-pool cut and the per-Job binding cut remain serial before their
joined acceptance and final two-Job proof freeze. W103950 owns expanded coverage.
Custody cross-link discharges the transferred assembly proof, while W105982's
experimental child/disposition remains independent.31 parallel failures across13
scan shards stay with W115981/W48697; no full-suite green claim. Apply standing
W71830 test-change authority, exact source ownership, independent review and
existing budgets. Diagnose a repeatedly failing handoff before another allocation.
