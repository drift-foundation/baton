# Exact commands — the first Claude-backed v12 development Job

W202663, rewritten at claim207219. **The part-2 template this file used to
carry is gone.** Review206578 and review207096 both refused it as a deliverable
and were right: a schema skeleton with `<one>` placeholders is not a launch
instruction. Every value below is a real one, read out of artefacts that exist.

Three parts: what produced the images, what composed and applied the pool
(both RUN, with their results), and what remains before a Job may be submitted.

## Part 1 — the two images (run; results recorded)

```sh
cd /home/sl/src/baton/v12/python
PYTHONPATH=src:. python3 -m tools.worker_image \
  --engine docker \
  --context /home/sl/src/baton/v12 \
  --dockerfile /home/sl/src/baton/v12/worker/Dockerfile.claude \
  --tag baton-v12-w202663-provider:e486652c
# -> sha256:9ff3322f58f08275bfc4bb2cd511fb7a6b156e991449ee36f365d05e2133529d

docker build --no-cache --platform linux/amd64 \
  --build-arg PROVIDER_BASE=sha256:9ff3322f58f08275bfc4bb2cd511fb7a6b156e991449ee36f365d05e2133529d \
  --tag baton-v12-w202663-integration:e486652c \
  --file /home/sl/src/baton/v12/worker/Dockerfile.integration \
  /home/sl/src/baton/v12
# -> sha256:b9b75acc300170d99649d0497f9f93876ab5d8d73a9157c9861c5763f17c9561
```

Neither builds without this Work's `v12/.dockerignore` correction (`FINDING.md`
D1). Provenance: `PROVENANCE-202663.json`, with every copied path compared
checkout-side and image-side in `COPIED-INPUTS-207111.json`.

## Part 2 — the pool, composed and applied (run; results recorded)

```sh
cd /home/sl/src/baton/v12/python
PYTHONPATH=src:. python3 \
  /home/sl/src/baton/work/records/2026/09/finding-v12-initial-claude-worker-pool/compose-pool-207219.py
# -> complete: true, refused: []

PYTHONPATH=src:. python3 -m tools.bootstrap \
  --inputs /home/sl/src/baton/work/records/2026/09/finding-v12-initial-claude-worker-pool/pool-bootstrap-inputs.json
```

The composer writes `pool-bootstrap-inputs.json`, `pool-submission.json`,
`pool-stage-execution.json`, `pool-task.json` and
`pool-integration-instructions.txt` beside this file, stages the deployment's
own `jobs/w202663-first-development-job/task.json` and
`integration-instructions.txt` at the destination, and calls every accepted
validator — `check_manifest_structure` three times, `bootstrap.held`,
`bootstrap.configuration`, `stage_execution.held_configuration`,
`bootstrap.validated`, `job_manager.documents.owned_submission` — refusing
fail-closed if any declines.

**This is a heterogeneous pool, and it is the first one that could exist.**

| role | worker_id | participant | image | runtime manifest |
| --- | --- | --- | --- | --- |
| implementation | `w202663-first-development-job-implementation` | `baton.claude-coder` | `sha256:9ff3322f…` provider | `sha256:e3bd9547…` |
| review | `w202663-first-development-job-review` | `baton.claude-reviewer` | `sha256:9ff3322f…` provider | `sha256:ecbca685…` |
| integration | `w202663-first-development-job-integration` | `baton.merge` | `sha256:b9b75acc…` integration | `sha256:98ff830f…` |

Three runtime manifests, two images, **one Job input identity**
`sha256:514f591dc9d7fcd6968a1f4262b2de834563f1e8b7cb8da7f97a012c7bdc4960`.

Applied state, read back from
`/home/sl/baton-v12-instance-2026-09-18T10-38-52Z/deployment.json`:

- authority `a92e1d717fcc40fe9972df8b2497c055`, Work `a92e1d71-W1` created on
  `impl`, routes `impl → baton.claude-coder`, `rview → baton.claude-reviewer`,
  `integration → baton.merge`, and the four grants in that Work's own scope;
- canonical target `w202663-target` established at
  `e486652c4ddebfb696e030b4b867e914248db542`, read from the instance target's
  own `packed-refs`;
- `policy_generation` **16**.

### The policy-generation pin, measured rather than assumed

W197661's trap is real and this Work hit it. The pin travels INTO the bootstrap
that bumps it, so a composition must predict what the run will LEAVE.

```sh
cd /home/sl/src/baton/v12/python
PYTHONPATH=src:. python3 -c "
import importlib.util
spec = importlib.util.spec_from_file_location('pool', '/home/sl/src/baton/work/records/2026/09/finding-v12-initial-claude-worker-pool/compose-pool-207219.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
print(m.check_policy_pin())"
# -> {'configured_pin': 16, 'authority_generation': 16, 'equal': True}
```

The first prediction was **wrong** — configured 8 against generation 9 — and
this gate is what said so. Measured on this instance: the first capacity
bootstrap moved 1 → 9 (+8) and the repeat moved 9 → 16 (+7). Observations of
this instance, not a contract. **Run this check after any further bootstrap**;
a deployment whose pin is wrong defers at its own integration with the reason
buried in a tick report.

## Part 3 — the instance lifecycle (read-only commands only, for now)

```sh
just --justfile /home/sl/baton-v12-instance-2026-09-18T10-38-52Z/justfile status
just --justfile /home/sl/baton-v12-instance-2026-09-18T10-38-52Z/justfile start
just --justfile /home/sl/baton-v12-instance-2026-09-18T10-38-52Z/justfile monitor
just --justfile /home/sl/baton-v12-instance-2026-09-18T10-38-52Z/justfile stop
```

`status` and `monitor` are read-only and safe. **`start` is not, yet**:
`FINDING.md` D3 measures that this instance's installed runtime was packaged
from a different source state than the corrected tree, so starting it would run
a scheduler whose admission still compares a worker's whole manifest digest and
would refuse the heterogeneous pool above. It submits nothing either way, but
it is not evidence of anything until D3 is resolved.

## What has NOT been done

**The Job has not been submitted, and submitting it is not authorized by this
Work.** `pool-submission.json` is composed, validated by
`job_manager.documents.owned_submission`, and deliberately not handed to
`submit`. The reason is exact rather than cautious: the implementation and
review workers run the **provider image**, whose entrypoint is
`dogfood_entry.py` → `ClaudeAgent` → a real provider. A Job that reaches them
makes a model turn, and owner ruling 206702 says *"No live models"*.

So the deterministic report-and-hold verification (step 8) **cannot use this
pool as composed**. It needs a deterministic provider at the same boundary — a
separately provenanced fixture image, as W197661 used — configured as its own
pool on this instance. That is the remaining work, and it is not a decision the
owner has to make: it is implementation under the existing ruling.

**And it cannot run on this instance.** `FINDING.md` D3: the installed runtime
here was packaged from a different source state than the corrected tree, and
the supported installer refuses to replace a runtime in place. Part 3's
commands drive the INSTALLED runtime, so until that is resolved this file
documents a prepared configuration, not a launch-ready deployment.

When the owner does want the first real Claude-backed Job, the submission is
ready and the command is:

```sh
cd /home/sl/src/baton/v12/python
PYTHONPATH=src:. python3 -c "
import json
from baton_v12.job_manager import JobStore, submit
store = JobStore.open('/home/sl/baton-v12-instance-2026-09-18T10-38-52Z/db/jobs.sqlite3',
                      authority_uuid='a92e1d717fcc40fe9972df8b2497c055',
                      incarnation='w202663-submit')
try:
    submit(store, json.load(open('/home/sl/src/baton/work/records/2026/09/finding-v12-initial-claude-worker-pool/pool-submission.json')))
finally:
    store.close()"
```

That command **starts real model turns** under the credential the operator has
placed behind the `claude` slot at
`~/.baton/credential-sources.json` reference `w202663-development`. Nothing in
this Work has read, staged or verified that credential; the deployment names a
locator and no more. Do not run it as part of verifying this Work.
