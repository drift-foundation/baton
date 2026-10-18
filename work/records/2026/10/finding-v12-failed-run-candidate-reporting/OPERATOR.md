# W321528 proposed fresh execution packet

Owner selection required by M321528 before live execution. This is one useful
v12 implementation, v11 coordination and separate independent review. No new
provider execution occurred during preparation.

Source /home/sl/src/baton at committed3dcf6dc4bcee97e932d17c93ac13c5811b3af188
(W319114 integrated). New run failed-reporting-w321528-321530; new destination
/home/sl/baton-instances/failed-reporting-w321528-321530 must not exist. Parent
must exist. Execute from /home/sl/src/baton after owner selection:

```sh
python3 -B work/records/2026/10/finding-v12-failed-run-candidate-reporting/prepare.py stage --root /home/sl/baton-instances/failed-reporting-w321528-321530
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/sl/baton-instances/failed-reporting-w321528-321530/code/v12/python/src:/home/sl/baton-instances/failed-reporting-w321528-321530/code/v12/python python3 -B -m tools.bootstrap --inputs /home/sl/baton-instances/failed-reporting-w321528-321530/bootstrap-inputs.json --destination /home/sl/baton-instances/failed-reporting-w321528-321530/instance --distro /home/sl/baton-runs/managed-correction-236087/build/stack/out/distro --no-repositories
python3 -B work/records/2026/10/finding-v12-failed-run-candidate-reporting/prepare.py bind --root /home/sl/baton-instances/failed-reporting-w321528-321530
```

These prepare only. Preserve PREPARED.json and every artifact digest. Use the
new packet/commands.json start argv with its exact environment once; start owns
submission. Do not submit manually, run preflight identity, or invoke installed
justfile start. Do not regenerate a spent identity. Capture supervisor stdout/
stderr, outcome and all referenced artifacts. SIGINT/SIGTERM uses supervisor's
bounded accounting; a held outcome alone is not cessation proof.

Proposed limits:900s provider turn,30s formal verification,1500s total,60s cleanup,
one implementation invocation, no automatic retry. Same limits as W319114 R1,
not a further increase. TASK.md requires stop after focused checks; no whole-tree
discovery. The frozen93-test baseline passes7.332s; additional bounded cases should
remain focused. Missing fixture context is reported, not bypassed or silently skipped.

Existing image baton-v12-claude-worker:w239528-244216, config digest
sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2,
Claude CLI2.1.247, bridge network; credential source reference only
/home/sl/.baton/credential-sources.json, claude operator-file/w202663-development.
No secret contents read. Current authentication not checked. Manager108 modules/
resources frozen separately; complete private candidate repository contains
v12/worker, Python tests, supervisor dossier and canonical fixtures. Explicit
verification imports the candidate's claude_agent and test_baseline sources.
The current runner/image remain unchanged while the worker proposes their future
reporting correction. Its own outcome may therefore still need retained-artifact
inspection on failure. No deployment or image rebuild is included.

Real-provider question: can the adopted fresh pipeline produce and hand back this
bounded reporting correction, finish after focused verification and retain its
result? Fake/replay tests establish reporting correctness; they cannot author the
actual code proposal or establish today's provider authentication/completion. Reuse
prior accepted pipeline/image evidence; no new global certification campaign.

After completion or failure preserve exact runtime cessation, uncertainty and
cleanup, then all sealed outputs (including an unsuccessful retained candidate).
Do not trust the current supervisor's no-proposal wording as artifact inventory.
Collect base/head/tree, full paths, binary patch, object bundle, verification and
known limitations. Route W321528 to baton.rvpc for independent review of immutable
bytes and focused deterministic verification. No review worker is admitted, no
self-acceptance, automatic import or Git authority. Owner controls integration.
