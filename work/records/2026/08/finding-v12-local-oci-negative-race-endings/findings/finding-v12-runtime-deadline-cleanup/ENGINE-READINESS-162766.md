# Prepared real-Docker gate — not executed or authorized in claim162766

Exact selector:

```text
tests.manager.test_runtime_deadline_engine.DeadlineDocker.test_reached_fence_exact_removal_providers_custody_and_discharge
```

The question requiring an engine is whether the production OCI adapter actually
stops/removes only the named running container after the Authority fence, settles
real launch/credential delivery and directory custody, preserves partial output
and a sibling runtime, and carries committed absence to the separate Authority
gate. Deterministic tests cannot establish daemon behavior, mounts, process
quiescence or root normalization. Authority and agent boundaries remain labelled
deterministic fixtures; no live provider/model is needed for this question.

The new selector reuses the existing lifecycle fixture's real input/claim/root
composition. It overrides fixture setup so it cannot build or pull an image.
`BATON_W32577_IMAGE_DIGEST` must name the exact already-present, independently
reviewed reference-worker image. Its ID and reference-worker entrypoint are
checked before starting; the same image is the custodian. Interactive stdin
keeps the real reference worker running while the manager clock reaches the pin.
The gate requires jsonschema4.26.0 and fails on a missing dependency, daemon or
image instead of skipping. Every direct Docker child has at most30s and the
fixture shares a proposed180s cumulative monotonic bound, including setup and
container cleanup. The next authorized executor must also guard the entire
child with the remaining cumulative allowance and preserve its actual spending.

Readiness at this handoff:

- Python3.13.7 is available; selected deterministic tests used jsonschema4.19.2.
  The required4.26.0 pin is unavailable in that environment. No install was run.
- Image digest/provenance has not been selected or validated. No engine command,
  image inspect, pull, build or runtime launch was run in claim162766.
- Production provider implementations are reached by the selector through
  OciAdapter, CredentialHome/launch.materialize and the existing custody owner.
  Actual image/provider/daemon readiness remains to be checked under the next
  assignment. Prepared source is not runtime evidence.
- The source selector still requires independent review. Its180s limit is a
  proposal retained from the design review, not execution authority supplied
  by this document. Missing image/dependency evidence requires an explicit
  bounded readiness assignment, not an implicit install/build.

After candidate review and readiness authorization, invoke the exact selector
from `v12/python` with `PYTHONPATH=src`, `-W error`, the reviewed interpreter and
the recorded image digest. Record source/image digests, dependency versions,
engine version, full result and cumulative time. W32577/W32382/W33755 remain
open until their actual acceptance gates are satisfied.
