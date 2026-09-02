# Progress

## 2026-09-02 — baton.tuner

Claimed W65212 after re-reading the restored dossier and revalidated the ruling
against accepted generation 4 and the live managed manifest. The dedicated
integrator remains absent, and the existing Codex context/target/readiness
pattern is the correct additive deployment boundary.

Implemented the repository-owned portion: durable `baton.merge` identity and
Git boundary in `AGENTS.md`, the exact role/configuration/operation contract in
`docs/PROPOSAL-INTEGRATOR.md`, a fresh integrator context and readiness consumer
in `conf/infra.example.json`, the matching dispatcher target and policy recipe
in `conf/codex-event-bridge.template.json`, and focused topology/boundary tests.

Prepared the complete generation-5 candidate under `evidence/generation-5/`
from the current live inputs. It includes the Baton configuration, lifecycle
manifest, dispatcher template, exact generated policy, recorded SHA-256
digests, and an approver install/restart checklist.

Verification:

- focused integrator topology, contract, candidate-shape, and generator-parity
  guards: 3 passed;
- broader role/configuration/release/lifecycle/context/readiness regression:
  153 passed;
- proposed `baton.json`: JSON and Baton configuration validation passed;
- proposed `infra.json`: lifecycle manifest load passed and projected the new
  stopped `codex-integrator-readiness` service;
- proposed dispatcher/policy: every target passed exact managed-workflow
  preflight and the deployment-wide Docker inspection preflight;
- `git diff --check`: passed.

The live mailbox files and execution policy are outside the managed turn's
writable repository boundary; generation acceptance and stack drain/restart
are also explicitly owned by `baton.slaw`. Pass the exact repository result and
live deployment actions to the approver rather than attempting privileged
configuration or dispatch mutations from this tuner context.
