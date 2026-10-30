# Continue already-selected B; do not reinstall or start C

Owner M347196 selects A+B. Independent347232 review matches all207 installed
payload files against the sealed archive (entry/client are documented copies of
their code/tools source), all211 protected-stage files, READY and installation
hash342587c532c9a6aa03ca65d2a664bb79b815812b43619a5a907e0a65a9b0c4ac.
Four nonlogin uid/gid pairs997/986,995/984,994/983,993/982 match receipts.
Managed namespace maps host root to65534; admission.sudoers is unreadable here.
This is a concrete evidence limit, not a failed installation or new approval gate.

Run this read-only receipt check from the normal host operator terminal. It
checks root custody, inventory, literal admission rule and private credential
file metadata without opening credential contents, importing installed code,
allocating, or writing. Stop on any assertion/error; return the output. No
reinstall, overwrite or stronger command follows a refusal.

```sh
sudo /usr/bin/python3 -I -B -c 'import os,stat,json,hashlib,pwd
from pathlib import Path
assert os.geteuid()==0
root=Path("/opt/baton-next-run")
def custody(p,uid=0,private=False):
 s=p.lstat()
 assert not stat.S_ISLNK(s.st_mode) and s.st_uid==uid and not s.st_mode & (0o077 if private else 0o022), str(p)
 return s
raw=(root/"installation.json").read_bytes()
assert hashlib.sha256(raw).hexdigest()=="342587c532c9a6aa03ca65d2a664bb79b815812b43619a5a907e0a65a9b0c4ac"
c=json.loads(raw)
assert json.loads((root/"READY").read_bytes())=={"installation_sha256":hashlib.sha256(raw).hexdigest()}
paths=[root,root/"installation.json",root/"READY",root/"state",root/"runs",Path(c["storage"])]
paths += [root/x for x in c["files"]]
paths += list(Path("/opt/baton-next-run-source-345599").rglob("*"))
for p in paths:
 for a in [*p.parents,p]: custody(a)
for rel,digest in c["files"].items():
 assert hashlib.sha256((root/rel).read_bytes()).hexdigest()==digest,rel
assert {str(x.relative_to(root)) for x in (root/"code").rglob("*") if x.is_file()}=={x for x in c["files"] if x.startswith("code/")}
rule=b"#1000 ALL=(root) NOPASSWD: /opt/baton-next-run/entry.py request\n"
for p in [root/"admission.sudoers",Path("/etc/sudoers.d/baton-next-run")]:
 custody(p);assert p.read_bytes()==rule
for a in c["accounts"]:
 assert pwd.getpwuid(a["uid"]).pw_gid==a["gid"]
 assert pwd.getpwuid(a["uid"]).pw_shell=="/usr/sbin/nologin"
 d=Path(a["credentials"]).parent
 custody(d,a["uid"],True)
 for f in d.iterdir():
  s=custody(f,a["uid"],True);assert stat.S_ISREG(s.st_mode) and s.st_gid==a["gid"]
print(json.dumps({"state":"installation-custody-pass","files":len(c["files"]),"capacity":c["capacity"],"credential_contents_read":False,"writes":0}))
'
```

If it reports installation-custody-pass, independent byte review plus this host
receipt satisfies the installation prerequisite for B. Continue existing
installation-345599/COMMANDS.md Section B, already authorized; no renewed owner
approval required. Execute each step separately and retain stdout/stderr/status:

```sh
/usr/bin/sudo -n -l /opt/baton-next-run/entry.py request
```

```sh
printf '%s\n' '{"action":"status","run":"w339626-live-345599","extra":true}' | /usr/bin/sudo -n /opt/baton-next-run/entry.py request
```

The malformed request MUST refuse with no allocation. A sudo/authentication
failure is not the expected application refusal and does not pass this check.
After that expected refusal only, proceed once:

```sh
/opt/baton-next-run/client.py prepare < /opt/baton-next-run-source-345599/validation-task.json
```

Require exactly w339626-live-345599 in the returned receipt; if a continuation
identity is returned, stop and record it rather than using the old name.

```sh
/opt/baton-next-run/client.py check w339626-live-345599
```

```sh
/opt/baton-next-run/client.py status w339626-live-345599
```

```sh
sudo /usr/bin/python3 -I -B /opt/baton-next-run-source-345599/operator-isolation.py
```

Return these receipts for independent B acceptance: literal admission, malformed
request refusal, one allocated identity/authority/Work, check and prepared status,
negative-access-checks-pass. Preserve the other three identities. No provider call
or start is part of B. C remains UNSELECTED, and broader long-Job support remains
pending lease-policy correction. Do not rerun A or its absent-destination preflight.
