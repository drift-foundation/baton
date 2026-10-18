# Fresh preparation324377 after the spent authentication-failed invocation

This packet is NOT authorized to launch. M324283 is spent and applies only to
worker-visibility-w324214-324217. Preserve that run and all historical packet files.
Latest review-2026-10-18T16-43-57Z.md confirms exact prior runtime absent, no
candidate head and no verification. PROVENANCE.json links the exact old identity.
The new run/destination below requires independent review and explicit new selection.

Owner reports all credentials refreshed. Before a separately selected launch,
the authorized operator must confirm the configured registry slot
claude operator-file/w202663-development references the refreshed credential source
in /home/sl/.baton/credential-sources.json. This preparation does not inspect secret
contents, copy credentials, change profiles or spend an authentication/model probe.
Reported refresh is not proof of successful authentication; actual selected run
must report authentication failure honestly if it persists. No automatic retry.

Task bytes, committed base,110 manager files,3 supervisors, image and focused test
vector are unchanged and revalidated. Only run/claim/destination and resulting
authority/document bindings are fresh. No sibling working-tree changes are inputs.

# W324214 proposed execution — preparation claim324377

Preparation only; independent packet review and fresh owner live selection required.
No Job/attempt launched. Selected source commit6348161e608187393e45454db63c192a93f6deb3.
TASK.md fixes the separate read-only status-file consumer, output version and exact
focused vector. No change to job-status/6 or stack/bootstrap command registration.
Expected new product paths: tools/worker_visibility.py, tests/tools/test_worker_visibility.py
under v12/python and v12/python/WORKER-VISIBILITY.md. Paths describe the proposed
solution, not a new restriction on necessary nonoverlapping changes. W321528 and
W321689 owned paths named in FINDING/TASK are excluded from concurrent edits.

## Preparation and launch after selection

Execute from /home/sl/src/baton. Final root must not exist. Do not launch the
/tmp disposable preflight authority or reuse an old run identity.

```sh
python3 -B work/records/2026/10/finding-v12-minimum-worker-visibility/preparation-324377/prepare.py stage --root /home/sl/baton-instances/worker-visibility-w324214-324377
env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/sl/baton-instances/worker-visibility-w324214-324377/code/v12/python/src:/home/sl/baton-instances/worker-visibility-w324214-324377/code/v12/python python3 -B -m tools.bootstrap --inputs /home/sl/baton-instances/worker-visibility-w324214-324377/bootstrap-inputs.json --destination /home/sl/baton-instances/worker-visibility-w324214-324377/instance --distro /home/sl/baton-runs/managed-correction-236087/build/stack/out/distro --no-repositories
python3 -B work/records/2026/10/finding-v12-minimum-worker-visibility/preparation-324377/prepare.py bind --root /home/sl/baton-instances/worker-visibility-w324214-324377
```

These commands prepare only. Save PREPARED.json; verify generated packet/commands.json
matches the following proposed launch exactly before executing it once:

```sh
env BATON_V12_STAGE_EXECUTION_CONFIG=/home/sl/baton-instances/worker-visibility-w324214-324377/packet/deployment.json PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/sl/baton-instances/worker-visibility-w324214-324377/code/v12/python/src:/home/sl/baton-instances/worker-visibility-w324214-324377/code/v12/python /usr/bin/python3 -B /home/sl/baton-instances/worker-visibility-w324214-324377/supervisor/baseline.py --packet /home/sl/baton-instances/worker-visibility-w324214-324377/packet/PACKET.json --incarnation worker-visibility-w324214-324377
```

Start owns submission; do not submit manually or invoke installed justfile start.
One fresh Claude invocation:900s provider,30s verification,1500s total,60s cleanup,
no retry. Stop after focused required checks. Reuse image
baton-v12-claude-worker:w239528-244216, image config digest
sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2,
Claude CLI2.1.247, bridge network. Credential source reference only:
/home/sl/.baton/credential-sources.json, claude operator-file/w202663-development.
No credentials read or authentication asserted in preparation.

Runtime110 manager files and3 supervisor helpers are frozen directly from selected
committed Git objects. Six relevant source/test fixtures match that base; no
unaccepted sibling bytes are imported. Historical image/bootstrap evidence is
reused unchanged. Exact pins are in PREPARATION-PINS.json and packet manifest.
Full committed source supplies real status fixtures; new visibility tests come
from the candidate. Formal vector: tests.tools.test_worker_visibility,
tests.tools.test_job_viewer, tests.job_manager.test_status. No broad suite.

The selected provider question would be authorship and handback of this bounded
view in the isolated adopted pipeline, not telemetry/probe correctness. Fake/replay
checks inside v12 prove the latter; no live telemetry probe is needed or selected.
The worker cannot launch another provider or Docker operation. Any live selection
applies only to the one outer implementation invocation.

## Evidence and operational boundary

PREFLIGHT.json records disposable stage/bootstrap/bind, held_packet and imported
source checks; all generated artifact hashes and task instructions rechecked.
No product tests run during preparation. The new behavior remains unimplemented.
Capture actual Job/attempt identities after launch, stdout/stderr, outcome and
retained candidate even on failure. Record exact cessation, uncertainty and cleanup;
SIGINT/SIGTERM requests bounded accounting, not proof of cessation. The historical
supervisor may misreport failed candidate absence (W321528); independently inventory
retained artifacts without relabeling failure. Return immutable candidate/base/head/
tree/path/digests and focused evidence to baton.bug; no automatic acceptance/import.

Known operational limitation from W321528 claim324180: this managed sandbox refused
mkdir under /home/sl/baton-instances with errno30 read-only filesystem. This Work
has not attempted live staging there. Before selected execution, installed policy
must support the exact reviewed commands, or an authorized operator executes them.
Do not substitute /tmp as a live destination or implement directly to bypass it.
This is operational access, not another product-scope decision.

Human checkpoint due after accepted product delivery; suggested commit:
`v12: expose minimum worker visibility from existing status evidence`.
W39649 retains joined acceptance and broader parked telemetry scope.
