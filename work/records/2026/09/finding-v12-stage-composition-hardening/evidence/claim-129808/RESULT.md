# First slice: two controls pass; concrete worker cleanup fails

baton.tuner, claim129808. The added test-only slice exposes a concrete factory
cleanup gap. It is ready for independent assessment, not passing acceptance.

`v12/python/tests/tools/test_stage_execution_hardening.py` adds three cases over
the existing isolated ServingCase fixture. Real Authority/coordinator opens,
preflight and worker construction run against temporary fixture stores and the
fake engine. Only the selected failure and close observation are injected.

- Review preflight failure: the acquired Authority is disposed; passes.
- Coordinator open failure: the acquired Authority is disposed; passes.
- Review worker construction failure: implementation worker, coordinator and
  Authority are acquired, but only coordinator and Authority are closed; fails.

All three preserve the exact injected exception and stop before pool activation.
Fixture cleanup closes anything the production unwind skipped after assertions;
it does not add a close to the observed journal or mask the failure.
The defect record distinguishes a skipped cleanup method from a resource leak:
the current pooled worker callback is a no-op. Production follow-up W129838 is
bound to `../../findings/finding-concrete-worker-close/`.

`verification.json` and `verification.log` record the exact command, environment,
10-second ceiling, exit1 and **0.280144 seconds** elapsed. No second execution
or broader run followed the confirmed failure. Syntax/whitespace and scoped
Git diff checks pass. Existing production/test/registry bytes stayed unchanged
through verification; the pre-existing modification to the assembly test file
belongs to another change and was not edited here.

The new test candidate is retained as `candidate-test_stage_execution_hardening.py`,
mode0664, SHA256
`92e7478e8ba97b104955715eb14d81b28d6279756bb78860b77a76ea8a32ebd3`.
The exact five-path hash/mode snapshot is in `verification.json`.

The inventory removes covered publication, committed-handoff and interrupted
integration cases from this slice. Remaining composed status/log coverage is
separately accountable as W129844 at
`../../findings/finding-held-status-locators/`. Review should assess this red
regression, allocate the production fix, and reconcile any remaining restart
gap and the older W110783 history against current accepted evidence. W103950
retains joined coverage acceptance and must not close while those children
remain unfinished.
