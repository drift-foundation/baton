# Proposed v3 custody continuation — NOT selected or executed

W343989 correction claim344059. This procedure supersedes OPERATOR-344007.md
for execution; retain that earlier proposal and manifest as historical evidence. Independent review first; operator selection afterward.
Preparation uses unchanged accepted installer/entry. No source implementation,
installation, account/credential/store operation, arm or start occurred here.
Do not repeat the v2 start or remove either its armed or consumed receipt.

The concrete successor is `/tmp/baton-output-preparation-344007/bundle`:
manifest `f1c3e2d11ec5557c86273a6abc0c0ccb99b61f98acde3dddfcd5b737057f1265`,
selection `436fe9b30f112f11ba50659883024d7cf60270497b59692251342163581febab`,
packet `5dd0195f6958e32889cd30261f0d1de86283d6bd28c2353743ea198473fed795`.
SUCCESSOR-344007.json enumerates all leaf deltas. Only selection, packet and
 deployment configuration differ; 203 of 205 tree members remain byte-identical.
Source, runtime, task, submission, authority UUID, Work, Job, run, base, image,
900s lease and 3600/30/4800/60 limits remain unchanged. V3 is a new admission
selection, not a new authority or an implicit retry. A later explicit invocation
selection is still required. Keep old copies inaccessible to execution.

## Preconditions and exclusive operator interval

All following commands are proposals for an operator root shell with `set -eu`.
Do not run them from a managed agent or infer approval from this document.
Missing tools, failed checks or unexpected state stop the procedure, preserving
partial output. No automatic retries or package installation. Operator must
prevent concurrent provisioning, arming or launching for this authority during
this interval. Check canonical parent/child claims before any runner restart;
no restart is needed for the unchanged existing managed prefix rules.

Before execution verify the independently reviewed PREPARATION-MANIFEST-344059.json
digest from the handoff. SHA256SUMS-344059 binds every prepared artifact including this
procedure; compare its own hash against that manifest, then check its members:

```sh
set -eu
cd /home/sl/src/baton/work/records/2026/10/finding-v12-standard-next-run-path/findings/finding-controller-output-preparation
sha256sum -c SHA256SUMS-344059
test ! -e /root/baton-output-preparation-344059
test ! -L /root/baton-output-preparation-344059
mkdir -m 700 /root/baton-output-preparation-344059
getfacl -p /home/sl > /root/baton-output-preparation-344059/home.acl.before
getfacl -R -p /home/sl/src/baton > /root/baton-output-preparation-344059/source.acl.before
```

Retain complete nonsecret command outputs and exit statuses in that root-only
receipt directory. Check required getfacl availability before running this block.

Stage both public configuration files once, before any privileged publication.
The root-only receipt directory must be uid/gid0 mode0700, non-symlink, below
trusted /root. Its staged files must not exist; never replace a partial stage.
A failed copy/hash/metadata/validation stops with evidence retained. Neither
configuration may subsequently be installed from its mutable repository source.
The operator-exclusive interval excludes concurrent root writers; no claim of
protection from a malicious root administrator is made.

```sh
test "$(stat -c '%u:%g:%a:%F' /root/baton-output-preparation-344059)" = '0:0:700:directory'
for name in sudoers-v3 credential-sources-v3.json; do
  test ! -e "/root/baton-output-preparation-344059/$name"
  test ! -L "/root/baton-output-preparation-344059/$name"
  install -o root -g root -m 400 "/home/sl/src/baton/work/records/2026/10/finding-v12-standard-next-run-path/findings/finding-controller-output-preparation/$name" "/root/baton-output-preparation-344059/$name"
  test "$(stat -c '%u:%g:%a:%F:%h' "/root/baton-output-preparation-344059/$name")" = '0:0:400:regular file:1'
done
printf '%s  %s\n' f103256d2f78f9571d86ada51a6457380038d8e5f2f81aa2ee92f704268e4b48 /root/baton-output-preparation-344059/sudoers-v3 8249bc4a85657a9694db893b86c8875a7f76b90480b39fabac1f58e28426b400 /root/baton-output-preparation-344059/credential-sources-v3.json | sha256sum -c -
visudo -cf /root/baton-output-preparation-344059/sudoers-v3
```

Only nonsecret registry configuration is hashed. No bearer is read or hashed
by these staging/verification commands. A source replacement during staging
fails the staged hash unless the resulting bytes are exactly approved; a
replacement after staging cannot affect the protected publication source.


```sh
set -eu
command -v lsof
command -v setfacl
command -v visudo
if getent passwd 61235 || getent passwd baton-w339626-v3; then exit 1; fi
if getent group 61235 || getent group baton-w339626-v3; then exit 1; fi
getent group docker
ps -eo uid,gid,pid,args
find / -path /proc -prune -o -path /sys -prune -o -path /dev -prune -o \( -uid 61235 -o -gid 61235 \) -print
/usr/bin/docker ps -a --no-trunc --format '{{.ID}} {{.Names}} {{.Labels}}'
```

Require Docker gid119, no processes using old execution uid61234 or prospective
uid/gid61235, no files owned by61235, no scan errors, and no container (running
or otherwise unresolved) for authority5a2f5ddc15f247e68f1cbe93b4de93d3 or run
baton-standard-next-run-w339626-339782. Inspect `ps -Af` for exact controller/run
arguments too. Do not stop unrelated Jobs. Any matching or unknown runtime needs
separate reconciliation before copying. Expected old attempt never made a child;
that source inference alone is not the operator's quiescence proof.

```sh
ps -Af
if lsof -nP +D /var/lib/baton-managed-runs/w339626-custody-v2; then exit 1; else test "$?" -eq 1; fi
```

Require no lsof output or diagnostics; status1 alone with diagnostics is not
success. Confirm v2 selection/consumed receipt exist, v3 selection/state/storage
are absent, installer hash matches, and entry hash is unchanged:

```sh
test -f /opt/baton-managed-entry/state/w339626-custody-v2.consumed
for p in /opt/baton-managed-entry/selections/w339626-custody-v3 /opt/baton-managed-entry/state/w339626-custody-v3.armed /opt/baton-managed-entry/state/w339626-custody-v3.consumed /var/lib/baton-managed-runs/w339626-custody-v3; do test ! -e "$p"; test ! -L "$p"; done
printf '%s  %s\n' 76da2696c37f41a1312cdf9e7d8ea322a608479ad802481659bdd4476be6f00c /root/baton-managed-entry-340184/installer.py 7547b27f88873e240f1a0666e6c1cdd7dfc5d2a9064974264aea4be6fcdf1d15 /opt/baton-managed-entry/entry.py | sha256sum -c -
```

Inspect original v2 consumed JSON: it must bind selection04cc16db980abb8c10dbbdcf2d3e589f524c768f2ba1982f479615a232f52227. Preserve it unchanged. Read only that admission JSON, never SQLite contents. Recheck identity availability immediately before creation.

## Register and provision complete private output roots

```sh
groupadd --gid 61235 baton-w339626-v3
useradd --uid 61235 --gid 61235 --groups docker --no-create-home --home-dir /var/lib/baton-managed-runs/w339626-custody-v3/home --shell /usr/sbin/nologin --no-user-group baton-w339626-v3
id baton-w339626-v3
/usr/bin/python3 -I /root/baton-managed-entry-340184/installer.py register /tmp/baton-output-preparation-344007/bundle f1c3e2d11ec5557c86273a6abc0c0ccb99b61f98acde3dddfcd5b737057f1265
/usr/bin/python3 -I /root/baton-managed-entry-340184/installer.py prepare-storage w339626-custody-v3 61235 61235
```

Require uid/gid61235 and supplementary119 only. Keep old61234 reserved and old
registration present; never bypass entry's cross-registration uid check.

The controller's pre-manager lock lives in instance/db; log, manager status,
shutdown request and enforcement receipt all share packet. These parents MUST
exist before consumption. Explicitly create them; also create the declared
runtime base directories with private modes. Per-attempt child directories are
left for the existing owners, avoiding preexisting-attempt refusal.

```sh
install -d -o 61235 -g 61235 -m 700 /var/lib/baton-managed-runs/w339626-custody-v3/instance /var/lib/baton-managed-runs/w339626-custody-v3/instance/db /var/lib/baton-managed-runs/w339626-custody-v3/packet /var/lib/baton-managed-runs/w339626-custody-v3/packet/deployment-state /var/lib/baton-managed-runs/w339626-custody-v3/packet/credentials /var/lib/baton-managed-runs/w339626-custody-v3/packet/credentials/implementation /var/lib/baton-managed-runs/w339626-custody-v3/packet/credentials/review /var/lib/baton-managed-runs/w339626-custody-v3/packet/launch /var/lib/baton-managed-runs/w339626-custody-v3/packet/launch/implementation /var/lib/baton-managed-runs/w339626-custody-v3/packet/launch/review /var/lib/baton-managed-runs/w339626-custody-v3/packet/workspaces
```

## Cold authority preservation, no bootstrap

Retain old private root, lock and consumed admission. After positive quiescence,
fence old root from its former service uid, then repeat open-handle check.
Record root metadata before mutation. Original fenced /tmp tree also stays intact.

```sh
stat -c '%u %g %a %n' /var/lib/baton-managed-runs/w339626-custody-v2
getfacl -p /var/lib/baton-managed-runs/w339626-custody-v2 > /root/baton-output-preparation-344059/v2-root.acl.before
chown root:root /var/lib/baton-managed-runs/w339626-custody-v2
setfacl -b /var/lib/baton-managed-runs/w339626-custody-v2
chmod 700 /var/lib/baton-managed-runs/w339626-custody-v2
if lsof -nP +D /var/lib/baton-managed-runs/w339626-custody-v2; then exit 1; else test "$?" -eq 1; fi
find /var/lib/baton-managed-runs/w339626-custody-v2/instance/db -mindepth 1 -maxdepth 1 -printf '%f %y %n %s %u %g %m\n'
```

Require no handles/diagnostics and exactly two non-symlink regular single-link
files: authority.sqlite3 size233472 and control.sqlite3.authoring.lock size0,
uid/gid61234 mode600. Any extra DB/WAL/SHM/journal, changed size, other entry,
mode or ownership stops the proposal. Never delete unexpected state to fit it.
Compare against original fenced source before transfer; no store interpretation.

```sh
cmp /tmp/baton-standard-next-run-w339626-339782/instance/db/authority.sqlite3 /var/lib/baton-managed-runs/w339626-custody-v2/instance/db/authority.sqlite3
cmp /tmp/baton-standard-next-run-w339626-339782/instance/db/control.sqlite3.authoring.lock /var/lib/baton-managed-runs/w339626-custody-v2/instance/db/control.sqlite3.authoring.lock
for name in authority.sqlite3 control.sqlite3.authoring.lock; do
  test ! -e "/var/lib/baton-managed-runs/w339626-custody-v3/instance/db/$name"
  test ! -L "/var/lib/baton-managed-runs/w339626-custody-v3/instance/db/$name"
  cp --no-clobber --no-dereference "/var/lib/baton-managed-runs/w339626-custody-v2/instance/db/$name" "/var/lib/baton-managed-runs/w339626-custody-v3/instance/db/$name"
  cmp "/var/lib/baton-managed-runs/w339626-custody-v2/instance/db/$name" "/var/lib/baton-managed-runs/w339626-custody-v3/instance/db/$name"
  chown 61235:61235 "/var/lib/baton-managed-runs/w339626-custody-v3/instance/db/$name"
  chmod 600 "/var/lib/baton-managed-runs/w339626-custody-v3/instance/db/$name"
done
```

Record successful comparison exit statuses. This preserves accepted authority
bytes and identity; it is not a DB query, migration, new Job or bootstrap. Later
selected controller owns supported initialization of absent stores.

## Credential and source access — operator selection required

The new identity cannot use registry owned by61234; effective-uid private-file
requirements require a separate uid-owned copy. Preserve original credentials.
Use opaque existing protected bearer bytes, never print/hash/decode them.
Before copying inspect metadata only: `/etc/baton-managed-entry` root-owned0711,
old bearer uid/gid61234 mode0400, regular non-symlink single-link, size1..4096;
all ancestors root-owned with no non-root write. Fail on discrepancy. The new
registry is public configuration data prepared here, not credential material.

```sh
stat -c '%u %g %a %F %h %s %n' /etc/baton-managed-entry /etc/baton-managed-entry/w339626-credential
for p in /etc/baton-managed-entry/w339626-v3-credential /etc/baton-managed-entry/w339626-v3-credential-sources.json; do test ! -e "$p"; test ! -L "$p"; done
install -o 61235 -g 61235 -m 400 /etc/baton-managed-entry/w339626-credential /etc/baton-managed-entry/w339626-v3-credential
printf '%s  %s\n' 8249bc4a85657a9694db893b86c8875a7f76b90480b39fabac1f58e28426b400 /root/baton-output-preparation-344059/credential-sources-v3.json | sha256sum -c -
install -o 61235 -g 61235 -m 400 /root/baton-output-preparation-344059/credential-sources-v3.json /etc/baton-managed-entry/w339626-v3-credential-sources.json
printf '%s  %s\n' 8249bc4a85657a9694db893b86c8875a7f76b90480b39fabac1f58e28426b400 /etc/baton-managed-entry/w339626-v3-credential-sources.json | sha256sum -c -
test "$(stat -c '%u:%g:%a:%F:%h' /etc/baton-managed-entry/w339626-v3-credential-sources.json)" = '61235:61235:400:regular file:1'
setfacl -m u:61235:--x /home/sl
setfacl -R -P -m u:61235:r-X /home/sl/src/baton
runuser -u baton-w339626-v3 -- test -r /etc/baton-managed-entry/w339626-v3-credential
runuser -u baton-w339626-v3 -- test -r /etc/baton-managed-entry/w339626-v3-credential-sources.json
runuser -u baton-w339626-v3 -- test -r /home/sl/src/baton/.git/HEAD
runuser -u baton-w339626-v3 -- test ! -w /home/sl/src/baton/.git/HEAD
runuser -u baton-w339626-v3 -- test ! -w /home/sl/src/baton
```

Recheck new credential pair metadata: uid/gid61235,0400,nlink1, non-symlink
regular. Record only metadata. Verify registry against the preparation manifest
hash, not a bearer hash. Preserve existing ACLs; capture before/after ACL receipts
before additions in the root-only receipt directory above. Do not
restore a whole old ACL snapshot over concurrent repository changes on rollback.

## Mandatory pre-consumption acceptance

The existing check does NOT enforce output parent existence. This operator gate
is explicit, not a claim of a product fix. Run immediately before any separately
selected arming, with no competing uid61235 execution. Root ancestry and new uid
exclusivity prevent managed callers racing the check. Any concurrent executor
invalidates the observation and requires reconciliation, never a blind start.

```sh
python3 -I - <<'PY'
import json, os, stat
from pathlib import Path
root=Path('/var/lib/baton-managed-runs/w339626-custody-v3')
required=['','home','tmp','instance','instance/db','packet','packet/deployment-state','packet/credentials','packet/credentials/implementation','packet/credentials/review','packet/launch','packet/launch/implementation','packet/launch/review','packet/workspaces']
for rel in required:
    p=root/rel; s=p.lstat()
    assert stat.S_ISDIR(s.st_mode) and not stat.S_ISLNK(s.st_mode)
    assert (s.st_uid,s.st_gid,stat.S_IMODE(s.st_mode))==(61235,61235,0o700),str(p)
for p in root.parents:
    s=p.lstat(); assert stat.S_ISDIR(s.st_mode) and s.st_uid==0 and not s.st_mode&0o022
for suffix in ('armed','consumed'):
    assert not os.path.lexists('/opt/baton-managed-entry/state/w339626-custody-v3.'+suffix)
for folder in Path('/opt/baton-managed-entry/selections').iterdir():
    data=json.loads((folder/'selection.json').read_text())
    if folder.name!='w339626-custody-v3': assert data['uid']!=61235
for p in (root/'packet').rglob('*'):
    assert p.is_dir() and not p.is_symlink(),str(p)
print('private parents present; fresh admission; distinct uid; no output files')
PY
runuser -u baton-w339626-v3 -- test -w /var/lib/baton-managed-runs/w339626-custody-v3/packet
runuser -u baton-w339626-v3 -- test -w /var/lib/baton-managed-runs/w339626-custody-v3/instance/db
runuser -u baton-w339626-v3 -- /usr/bin/python3 -I -c 'import json,hashlib,pathlib; p=json.loads(pathlib.Path("/opt/baton-managed-entry/selections/w339626-custody-v3/tree/config/PACKET.json").read_text()); root=pathlib.Path(p["fixture"]["source_root"]); assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==h for n,h in p["fixture"]["files"].items()); print("selected source inputs match")'
/opt/baton-managed-entry/entry.py check w339626-custody-v3
```

Require selection436fe9b3... and revalidate all bundle seals. No write probe,
provider call, bootstrap or store read is needed to establish these parents.

## Narrow admission and managed receipts

Publish the already staged, digest-verified root-private `sudoers-v3` as a new
fragment; do not reread the repository source after staging; preserve old fragment/receipt. Full configuration
validation is required, including effective policy for sl. sudo-rs requires
exact selection arguments, not the predecessor wildcard rule. Existing mapped
Codex prefix rules already cover the fixed entry's check/inspect/start verbs;
no broader rule, interpreter grant or socket change is proposed.

```sh
test ! -L /etc/sudoers.d
test "$(stat -c '%u:%g:%a:%F' /etc/sudoers.d)" = '0:0:755:directory'
test ! -e /etc/sudoers.d/baton-managed-entry-v3
test ! -L /etc/sudoers.d/baton-managed-entry-v3
printf '%s  %s\n' f103256d2f78f9571d86ada51a6457380038d8e5f2f81aa2ee92f704268e4b48 /root/baton-output-preparation-344059/sudoers-v3 | sha256sum -c -
visudo -cf /root/baton-output-preparation-344059/sudoers-v3
install -o root -g root -m 440 /root/baton-output-preparation-344059/sudoers-v3 /etc/sudoers.d/baton-managed-entry-v3
printf '%s  %s\n' f103256d2f78f9571d86ada51a6457380038d8e5f2f81aa2ee92f704268e4b48 /etc/sudoers.d/baton-managed-entry-v3 | sha256sum -c -
test "$(stat -c '%u:%g:%a:%F:%h' /etc/sudoers.d/baton-managed-entry-v3)" = '0:0:440:regular file:1'
visudo -c
/usr/bin/sudo -l -U sl
```

Then assign managed codxpc under its own claim to run exact check then inspect,
stopping on failed check, and retain full receipts for independent review:

```sh
/usr/bin/sudo -n /opt/baton-managed-entry/entry.py check w339626-custody-v3
/usr/bin/sudo -n /opt/baton-managed-entry/entry.py inspect w339626-custody-v3
```

Expected selection436fe9b30f112f11ba50659883024d7cf60270497b59692251342163581febab
and image sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2.
Successful receipts alone do not establish the missing-parent gate; retain the
operator metadata/check receipt too. Stop here, disarmed. A later explicit
owner selection can authorize one v3 invocation and operator arming:

```sh
/usr/bin/python3 -I /root/baton-managed-entry-340184/installer.py arm w339626-custody-v3 436fe9b30f112f11ba50659883024d7cf60270497b59692251342163581febab
```

Only after that selection/arming and a claimed handoff may the executor run:

```sh
/usr/bin/sudo -n /opt/baton-managed-entry/entry.py start w339626-custody-v3
```

No old consumed receipt is removed or changed. New registration alone authorizes
neither invocation nor rearming. Failure preserves all partial state.

## Disable and retention

On a failed provisioning check keep original/v2 fenced and v3 disarmed. Operator
may disable admission using the accepted installer `disable` (global to this
entry, so coordinate other selections first), or move only the new v3 sudoers
fragment to a root-only evidence location outside sudoers.d after confirming no
other selection depends on it; validate full sudoers afterward. Neither action
stops a running process. Preserve all stores, locks, consumed/armed receipts,
credentials, accounts and bundles. After positive quiescence revoke only added
uid61235 ACL entries if needed; do not delete outputs or reactivate an old copy.
Any recovery/reactivation requires its own selected disposition.
