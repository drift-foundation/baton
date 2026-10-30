# Operator commands — PROPOSED, not executed or selected

Run only after owner selects the corresponding boundary below. Run from the normal host shell, outside the managed user namespace. Stop on every refusal; no cleanup/retry/overwrite is selected.

## A. One-time protected source staging and installation

Exact archive SHA256 `413e2846cd22f9350371151eccaa5bde877f9bf0ba8fb98b2dfae59a9fca93a3`. The inline standard-library loader reads the full archive, verifies this digest before processing members, refuses an occupied root, and writes only closed regular members. It executes no mutable checkout code as root.

```sh
sudo /usr/bin/python3 -I -B -c 'import hashlib,io,tarfile,os
from pathlib import Path
raw=Path('"'"'/home/sl/src/baton/work/records/2026/10/finding-v12-standard-next-run-path/installation-345599/source.tar'"'"').read_bytes()
assert hashlib.sha256(raw).hexdigest()=='"'"'413e2846cd22f9350371151eccaa5bde877f9bf0ba8fb98b2dfae59a9fca93a3'"'"', '"'"'archive drift'"'"'
root=Path('"'"'/opt/baton-next-run-source-345599'"'"')
assert os.geteuid()==0
assert not os.path.lexists(root), '"'"'preserve existing staging'"'"'
with tarfile.open(fileobj=io.BytesIO(raw)) as t:
 members=t.getmembers(); names=[m.name for m in members]
 assert len(names)==len(set(names))
 assert all(m.isfile() and not Path(m.name).is_absolute() and '"'"'..'"'"' not in Path(m.name).parts for m in members)
 root.mkdir(mode=0o755)
 for m in members:
  path=root/m.name;path.parent.mkdir(parents=True,exist_ok=True,mode=0o755)
  with path.open('"'"'xb'"'"') as f:f.write(t.extractfile(m).read())
  os.chmod(path,0o755 if m.name=='"'"'runtime/baton-v12-stack'"'"' else 0o644)
print('"'"'protected source staged; installation not performed'"'"')
'
```

Read-only host prerequisite check (source custody, exact inventory/image/base, identity/group/socket metadata, credential metadata, absent destinations, Landlock ABI):

```sh
sudo /usr/bin/python3 -I -B /opt/baton-next-run-source-345599/operator-preflight.py
```

Only after the prerequisite check succeeds, exact supported installer:

```sh
sudo /usr/bin/python3 -I -B -c 'import sys;sys.path[:0]=['"'"'/opt/baton-next-run-source-345599/code/src'"'"','"'"'/opt/baton-next-run-source-345599/code'"'"'];from tools.next_run_managed import main;raise SystemExit(main())' install --inputs /opt/baton-next-run-source-345599/installation-inputs.json --sha256 c49fe2e6c5f71f044646e6fdc900f274ad352b56ac39a67b22e84d210d80896f
```

Expected: installed, capacity4, root /opt/baton-next-run. This copies the selected credential once per pool identity and publishes the literal sudo rule. Any partial failure is retained; do not rerun or remove it. Return receipts for independent inspection before B.

## B. Admission and allocation validation; no provider invocation

Select one task preparation under caller sl/uid1000. Preserve stdout from each command. Negative malformed request must refuse without allocation:

```sh
/usr/bin/sudo -n -l /opt/baton-next-run/entry.py request
printf '%s\n' '{"action":"status","run":"w339626-live-345599","extra":true}' | /usr/bin/sudo -n /opt/baton-next-run/entry.py request
/opt/baton-next-run/client.py prepare < /opt/baton-next-run-source-345599/validation-task.json
/opt/baton-next-run/client.py check w339626-live-345599
/opt/baton-next-run/client.py status w339626-live-345599
```

Expect malformed-request refusal, one returned uid/authority/Work receipt, checked and prepared. If preparation returns a continuation run identity, stop and record it for exact selection; never start the historical name. `check` actually drops to the assigned uid, applies Landlock and reads its Work. It does not prove provider authentication or negative isolation by itself. Keep one prepared identity and all remaining capacity. No automatic recovery invocation is selected.

After successful check and before selecting live start, operator runs the protected negative-access probe. It forks once, drops to the allocated uid/groups and applies the installed Landlock boundary; it attempts descriptor opens only, without creation, truncation, writes or reading credential bytes. Required refusals cover installed code, the group-writable source checkout, original credential and another pool identity's private registry. Any missing refusal stops validation. This is a bounded explicit isolation check, not a general root shell for the worker.

```sh
sudo /usr/bin/python3 -I -B /opt/baton-next-run-source-345599/operator-isolation.py
```

## C. Separately selected one live invocation

After B is independently accepted, select exactly w339626-live-345599, protected task SHA256 `5fc07524d1255a92d0f4b94a31317fa338013eb3997c7b70c989f19059bbd9dd`, one invocation, provider300s, verifier30s, total600s, cleanup60s, existing resource lease900s, no retry. Under a mapped executor claim run once:

```sh
/opt/baton-next-run/client.py start w339626-live-345599
/opt/baton-next-run/client.py status w339626-live-345599
```

Do not bypass the entry or call the composer/controller directly. A failed/unknown start is consumed/held until positive owner cessation evidence; no duplicate start. Collect nonsecret final reports from /var/lib/baton-next-run/w339626-live-345599/packet/outcome.json and its enforcement/manager siblings through the operator if private. Actual Job/attempt/candidate and cleanup receipts are mandatory. Candidate result is not independent acceptance.
