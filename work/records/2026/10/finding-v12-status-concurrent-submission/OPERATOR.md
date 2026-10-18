# W319114 proposed execution selection

Select one useful code correction THROUGH v12, fresh context, source
`/home/sl/src/baton` at `9055843b5d258f5bfbb523815d034ee0c14075d6`.
The complete repository-shaped private clone supplies tests and work fixtures;
TASK.md and the composed verification argv explicitly establish cwd/imports.
Manager code is separately frozen under `code/v12/python`; it is not the worker
candidate. Existing source/distro/image hashes are pinned or validated by prepare.py.

Proposed new destination: `/home/sl/baton-instances/status-race-w319114-319417`.
It must not exist; its parent must already exist. Authorized operator executes
from `/home/sl/src/baton` after owner selection:

```sh
python3 -B work/records/2026/10/finding-v12-status-concurrent-submission/prepare.py stage --root /home/sl/baton-instances/status-race-w319114-319417
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/sl/baton-instances/status-race-w319114-319417/code/v12/python/src:/home/sl/baton-instances/status-race-w319114-319417/code/v12/python python3 -B -m tools.bootstrap --inputs /home/sl/baton-instances/status-race-w319114-319417/bootstrap-inputs.json --destination /home/sl/baton-instances/status-race-w319114-319417/instance --distro /home/sl/baton-runs/managed-correction-236087/build/stack/out/distro --no-repositories
python3 -B work/records/2026/10/finding-v12-status-concurrent-submission/prepare.py bind --root /home/sl/baton-instances/status-race-w319114-319417
```

These steps only prepare. Preserve PREPARED.json, packet/PACKET.json and all
artifact digests in the execution handoff. Fresh bootstrap creates the isolated
UUID; never reuse the disposable preflight authority. Do not invoke the installed
justfile start: the selected runner is the digest-bound Python supervisor.
Execute the exact `start` argv from packet/commands.json with its `environment`
applied to the operator environment. Start alone owns submission; no manual
second submit. Preserve stdout/stderr, outcome.json and every referenced artifact.

Proposed bounds: one implementation invocation, 600-second provider turn,
30-second deterministic verification, 900-second total and 60-second cleanup;
no automatic retry. Existing image
`baton-v12-claude-worker:w239528-244216`, config digest
`sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2`,
Claude CLI2.1.247, bridge network, operator-file credential reference
w202663-development via `/home/sl/.baton/credential-sources.json`.
No credential contents were read. Current authentication is unproved.

The real-provider question is whether the selected fresh worker can produce a
useful code proposal for this actual correction through the adopted v12 pipeline,
with real provider invocation, contained deterministic verification and retained
result/cessation. Fake providers reproduce and verify the defect but cannot author
that actual proposal or establish today's provider authentication. This is not a
new global parallelism/reuse certification run. W247941 proves its recorded fresh
parallel result; W236087 proves its recorded serial reuse result only.

On any refusal, timeout or uncertain cessation, retain evidence and return the
exact checkpoint through v11; do not recycle this run identity. Collect proposal
base/head/tree, complete changed paths, patch and file hashes, verification result,
worker exit and supervisor cleanup evidence. Independently preserve proposal bytes
before releasing mutable storage. Route W319114 to baton.rvpc for review of those
exact bytes and independent deterministic verification. The runner admits no
review worker and issues no independent acceptance; external v11 reviewer review
is the proposed independent path. Human-plus-agent integration stays separate.

Owner selection is required by M319391/E319412 before live execution. This packet
has only been prepared in a disposable local authority; its execution is pending.
