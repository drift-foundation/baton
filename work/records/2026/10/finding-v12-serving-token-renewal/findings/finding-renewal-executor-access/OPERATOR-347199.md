# Exact operator route for W333485 — proposed, not applied

Owner347193 requested executable operational correction with no broad grants,
restart, stage or launch performed. This route uses Slawomir's existing uid1000
operator terminal for the already reviewed orchestration commands. It grants
nothing to a managed agent and changes no confinement/configuration. It does NOT
restore baton.codxpc shell access: selecting the operator as execution custodian
is an explicit parent handoff decision. The managed implementer keeps Work and
candidate accounting; it must not pretend the terminal is its own executor.

Read-only diagnosis found no installed narrow managed-root grant. Adding the
whole /home/sl/baton-instances directory would expose sibling instances. A chmod
is not a sandbox repair. Do not pre-create the selected root: stage intentionally
requires root absence at continuation-339444/prepare.py:75. Do not install an
allow rule for mutable repository Python or unrestricted python3. No supported
hot application of a new grant to this existing thread was established. This
operator route avoids needing such a claim or a restart.

## 1. Verify from the actual operator terminal (read-only)

Run as sl, not sudo. This command checks uid, canonical parent, write/search
access, absent exact root, accepted amendment digest and all input pins. Exit0
is the required preflight result; exit1 means stop. It does not test actual
creation or prove engine access, and grants no execution authority.

```sh
python3 -B /home/sl/src/baton/work/records/2026/10/finding-v12-serving-token-renewal/findings/finding-renewal-executor-access/preflight-347199.py
```

## 2. Apply the operator execution route only after parent selection

Parent must select this custodian and amendment manifest
8a46facba604ad3c5e2c1c1b7d76eaf91b84ea1e2aad5e904f296c301a7c7394,
including conditional use of three retained partial buffers. Old345625 is
unconsumed but its old manifest is not authorization for these changed bytes.
Parent must also settle the explicitly disclosed effective900s authoring lease;
configured3600/30/4800/60 ceilings do not fix it. W345730 authorizes preparing
these commands only. Run each command separately and stop at any nonzero result.
No automatic retry. No alternate root. The original packet remains immutable.

```sh
python3 -B /home/sl/src/baton/work/records/2026/10/finding-v12-serving-token-renewal/findings/finding-lease-policy-amendment/amendment-345734/prepare.py stage --root /home/sl/baton-instances/serving-renewal-w333485-339444
```

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/sl/baton-instances/serving-renewal-w333485-339444/code/v12/python/src:/home/sl/baton-instances/serving-renewal-w333485-339444/code/v12/python:/home/sl/baton-instances/serving-renewal-w333485-339444/supervisor python3 -B -m tools.bootstrap --inputs /home/sl/baton-instances/serving-renewal-w333485-339444/bootstrap-inputs.json --destination /home/sl/baton-instances/serving-renewal-w333485-339444/instance --distro /home/sl/baton-runs/managed-correction-236087/build/stack/out/distro --no-repositories
```

```sh
python3 -B /home/sl/src/baton/work/records/2026/10/finding-v12-serving-token-renewal/findings/finding-lease-policy-amendment/amendment-345734/prepare.py bind --root /home/sl/baton-instances/serving-renewal-w333485-339444
```

## 3. Verify the applied preparation before any launch

```sh
cat /home/sl/baton-instances/serving-renewal-w333485-339444/PREPARED.json /home/sl/baton-instances/serving-renewal-w333485-339444/packet/commands.json /home/sl/baton-instances/serving-renewal-w333485-339444/packet/PACKET.json
```

```sh
docker image inspect sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2 --format '{{.Id}} {{.Os}}/{{.Architecture}}'
```

Return actual generated authority/Work/PACKET identity and task fixture digests
for independent checking against amendment345734. Do not substitute rehearsal
identities. Expect same root/run/basebc925cf5,image,full four-module gate and
3600/30/4800/60 bounds,one invocation/no retry. Record stdout and status for each
operator command in this dossier without credentials. Any stage/bootstrap/bind
failure preserves the root and requires disposition; never rerun over it.

## 4. Separate launch gate, after joined acceptance and exact selection

Only after the parent approves actual generated identity/pins, operator image and
credential-reference availability, and effective lease disclosure, use the
existing enforced invocation once in a supervised foreground terminal:

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/sl/baton-instances/serving-renewal-w333485-339444/code/v12/python/src:/home/sl/baton-instances/serving-renewal-w333485-339444/code/v12/python:/home/sl/baton-instances/serving-renewal-w333485-339444/supervisor BATON_V12_STAGE_EXECUTION_CONFIG=/home/sl/baton-instances/serving-renewal-w333485-339444/packet/deployment.json python3 -B -m tools.authoring_enforcement --packet /home/sl/baton-instances/serving-renewal-w333485-339444/packet/PACKET.json
```

Compare this with actual generated commands.json before use. Credential source
remains the existing logical operator-file/w202663-development; never copy or
print credentials. Collect existing outcome/controller/manager/progress reports
and exact-runtime cessation as continuation-339444/OPERATOR.md specifies. No
bare supervisor, second invocation, forced cleanup or automatic recovery.

## Evidence and limits

Managed executor345627 recorded uid1000,parent0775 owned1000,W_OK false and no
selected-root grant. Current reviewer347199 independently observes root absent,
same owner/mode and W_OK false; this is not an actual codxpc re-probe. codx-pc
infra.json starts its app-server without writable-root overrides; user config
contains no sandbox_workspace_write grant. codex_client.mjs startThread/resume
sends no permission override. Supported configuration keys are documented in
[official configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference),
but documentation of a key is not proof of live activation or permission to
change deployment. No such change is proposed by these commands.

PROGRESS.md was absent on assignment; no operational repair or executor proof
was silently assumed. This command sheet and its read-only checker are reviewer
research owned by baton.rvpc. Product tests0,stage0,bootstrap0,launch0,restart0,
configuration changes0. Read-only amendment verification passed in0.127s.
