# Preserve the first integration launch refusal

Ledger Work W144813. Discovered in W71879 run2 review claim144777.

## 2026-09-11 — baton.codex — confirmed, deferred

Observed: A integration remained claimed/not-started after both original reviews
completed. Its ordinary launch document and integration bundle survive, while
the final serve report repeatedly refuses an existing launch root. Run2 stopped
at its integration deadline. Primary target provisioning mismatch is recorded
in W71879: target gid1000 versus configured1001. That first specific refusal is
source-inferred, because the first sweep error is not retained.

Confirmed source: `v12/python/tools/integration_worker.py:IntegrationRuntimePort.run`
materializes launch, builds bundle, proves mount boundary, constructs adapter,
then requests runtime start. A refusal after materialization leaves that root;
the same method unconditionally materializes it again on re-entry. The driver
re-enters a not-started waiting delivery, and launch.materialize correctly
refuses the existing root. The secondary refusal masks the first failure.
The successful materialization's exception cleanup cannot handle a failure that
happens after it has returned. No raw deletion/adoption bypass is authorized.

Evidence locator:
`baton:work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/evidence/review-144777/`.
External run2 and every partial delivery are retained. No workaround performed.

This is failure-handling hardening, outside W71830/W71879 containment/dependency.
Correct provisioning avoids this observed failure on the first successful path;
this Work neither changes group requirements nor makes an incompatible target
writable. Keep it deferred with W144335 and other unrelated hardening.
