# Concrete provisioning proposal for candidate340184

Prepared under W339972 claim341498 / continuation341496. NOT EXECUTED. This
supplements the immutable candidate OPERATOR.md; it does not change its bytes.
Owner selection of this procedure authorizes account, ACL, credential-copy,
original-run custody and cold-store-copy operations explicitly listed below.
It does not arm or start W339626. After independent preparation review and that
selection, the operator executes stages in order, stops on any failed check,
and retains partial output. No automatic retry or removal of existing targets.

Observed read-only: uid/gid61234 currently absent from NSS; Docker group119 exists;
/opt/baton-managed-entry and /var/lib/baton-managed-runs absent; /home/sl is0750;
old instance/db contains authority.sqlite3 and zero-byte
control.sqlite3.authoring.lock only. This observation must be rechecked at execution.
No store contents or credentials were read. Source tooling requires credential
registry AND source file ownership equal to effective uid with no group/other
bits (pinned tools/user_credentials.py:493). Root-owned readable registry files
would FAIL. Proposed registry/source files are uid61234 mode0400 under root-owned
0711 /etc/baton-managed-entry; caller cannot replace them. Landlock denies the
controller content writes there. Root remains the operator trust boundary.

## 1. Quiesce the mapped producer and prove the old instance is unused

Operator first reads canonical v11 work-graph using the supplied deployment CLI
and its own baton.slaw identity; require no active codxpc claim before stopping
its supervised context. If one exists, let its current work release normally.
This is a concrete execution precondition, not another preparation task.

```sh
/home/sl/opt/baton/v11/0650c61/bin/baton --config /home/sl/baton-v11.14aecfb/baton.json --participant baton.slaw work-graph status=open team=baton
python3 /home/sl/src/baton/tools/infra.py stop /home/sl/baton-v11.14aecfb/codx-pc
python3 /home/sl/src/baton/tools/infra.py status /home/sl/baton-v11.14aecfb/codx-pc
sudo lsof -nP +D /tmp/baton-standard-next-run-w339626-339782
sudo docker ps -a --no-trunc --format '{{.ID}} {{.Names}} {{.Labels}}'
```

Require stopped infra, no lsof rows/errors, and no container belonging to run
baton-standard-next-run-w339626-339782 or authority5a2f5ddc15f247e68f1cbe93b4de93d3.
Review process arguments with `ps -Af` for that exact old run; require no
controller/supervisor/worker. lsof exit1 with no diagnostics means no matches;
errors or incomplete visibility are a refusal. Do not infer quiescence from a
lock pathname or delete the lock. No other launcher may start the old run during
this maintenance interval. No broad stop/kill of other Jobs is selected.

## 2. Reserve the identity and snapshot operator metadata

Open an operator root shell (`sudo -i`). The remaining root command blocks run
there, with `set -eu`; commands are not managed-agent grants. Expected absence
checks are explicit. Missing utilities are a stop, not permission to install packages.

```sh
set -eu
command -v setfacl
command -v getfacl
command -v lsof
command -v groupadd
command -v useradd
if getent passwd 61234 || getent passwd baton-w339626; then exit 1; fi
if getent group 61234 || getent group baton-w339626; then exit 1; fi
getent group docker
ps -eo uid,gid,pid,args
find / -path /proc -prune -o -path /sys -prune -o -path /dev -prune -o \( -uid 61234 -o -gid 61234 \) -print
```

Require Docker gid119, no process with uid/gid61234, no owned files from the
find scan, and no scan errors. The search includes mounted storage; inaccessible
mounts make exclusivity unknown and stop this procedure. Recheck immediately
before account creation. These checks are operator-only and were not run broadly
by the reviewer.

```sh
test ! -e /root/baton-managed-entry-340184
mkdir -m 700 /root/baton-managed-entry-340184
getfacl -p /home/sl > /root/baton-managed-entry-340184/home.acl.before
getfacl -R -p /home/sl/src/baton > /root/baton-managed-entry-340184/source.acl.before
stat -c '%u %g %a %n' /tmp/baton-standard-next-run-w339626-339782 > /root/baton-managed-entry-340184/old-root.metadata
getfacl -p /tmp/baton-standard-next-run-w339626-339782 > /root/baton-managed-entry-340184/old-root.acl.before
groupadd --gid 61234 baton-w339626
useradd --uid 61234 --gid 61234 --groups docker --no-create-home --home-dir /var/lib/baton-managed-runs/w339626-custody-v2/home --shell /usr/sbin/nologin --no-user-group baton-w339626
id baton-w339626
```

Require uid/gid61234 and supplementary119 only. Account remains non-login,
exclusive to this selection. Do not add sl to its group or allow caller sudo
as this account. Root-owned directory ancestry is mandatory.

## 3. Install accepted code and empty storage, still disarmed

These are the previously reviewed installer operations, with the already-created
root receipt directory (do not repeat its mkdir from the older packet).

```sh
install -o root -g root -m 500 /tmp/baton-managed-entry-340184/v12/python/tools/managed_entry_install.py /root/baton-managed-entry-340184/installer.py
printf '%s  %s\n' 76da2696c37f41a1312cdf9e7d8ea322a608479ad802481659bdd4476be6f00c /root/baton-managed-entry-340184/installer.py | sha256sum -c -
/usr/bin/python3 -I /root/baton-managed-entry-340184/installer.py install /tmp/baton-managed-entry-340184/v12/python/tools/managed_entry.py 7547b27f88873e240f1a0666e6c1cdd7dfc5d2a9064974264aea4be6fcdf1d15
/usr/bin/python3 -I /root/baton-managed-entry-340184/installer.py register /tmp/baton-managed-entry-340184/operator-bundle 240abf377476e41436c90b12bab70583117cbf81e47efa0079be11876cbf53eb
/usr/bin/python3 -I /root/baton-managed-entry-340184/installer.py prepare-storage w339626-custody-v2 61234 61234
```

## 4. Fence the original and cold-copy its exact existing store bytes

Chosen method: retain original at its old pathname under root-only traversal,
then copy its two existing db-directory files into the private destination.
No bootstrap, new authority, SQL, SQLite backup command, schema migration or
store editor. Byte comparison proves preservation; it does not independently
query identity. The accepted packet names existing authority
5a2f5ddc15f247e68f1cbe93b4de93d3. Published old preparation evidence remains the
identity receipt. Do not start either copy in this procedure.

```sh
chown root:root /tmp/baton-standard-next-run-w339626-339782
setfacl -b /tmp/baton-standard-next-run-w339626-339782
chmod 700 /tmp/baton-standard-next-run-w339626-339782
if lsof -nP +D /tmp/baton-standard-next-run-w339626-339782 > /root/baton-managed-entry-340184/open-handles.out 2> /root/baton-managed-entry-340184/open-handles.err; then exit 1; else test "$?" -eq 1; fi
test ! -s /root/baton-managed-entry-340184/open-handles.out
test ! -s /root/baton-managed-entry-340184/open-handles.err
```

Handle lsof's no-match exit1 explicitly as in stage1; require no rows or errors.
Root fencing plus absence of open handles keeps the copy cold. Inspect directory
metadata only using the next command. Require exactly the two named regular,
non-symlink, single-link files; authority size233472 and lock size0. Any extra
store/WAL/SHM/journal or changed size is a changed premise: stop and retain state,
never discard it to fit this plan.

```sh
find /tmp/baton-standard-next-run-w339626-339782/instance/db -mindepth 1 -maxdepth 1 -printf '%f %y %n %s\n'
test ! -e /var/lib/baton-managed-runs/w339626-custody-v2/instance
install -d -o 61234 -g 61234 -m 700 /var/lib/baton-managed-runs/w339626-custody-v2/instance /var/lib/baton-managed-runs/w339626-custody-v2/instance/db
cp --no-clobber --no-dereference /tmp/baton-standard-next-run-w339626-339782/instance/db/authority.sqlite3 /var/lib/baton-managed-runs/w339626-custody-v2/instance/db/authority.sqlite3
cp --no-clobber --no-dereference /tmp/baton-standard-next-run-w339626-339782/instance/db/control.sqlite3.authoring.lock /var/lib/baton-managed-runs/w339626-custody-v2/instance/db/control.sqlite3.authoring.lock
cmp /tmp/baton-standard-next-run-w339626-339782/instance/db/authority.sqlite3 /var/lib/baton-managed-runs/w339626-custody-v2/instance/db/authority.sqlite3
cmp /tmp/baton-standard-next-run-w339626-339782/instance/db/control.sqlite3.authoring.lock /var/lib/baton-managed-runs/w339626-custody-v2/instance/db/control.sqlite3.authoring.lock
chown 61234:61234 /var/lib/baton-managed-runs/w339626-custody-v2/instance/db/authority.sqlite3 /var/lib/baton-managed-runs/w339626-custody-v2/instance/db/control.sqlite3.authoring.lock
chmod 600 /var/lib/baton-managed-runs/w339626-custody-v2/instance/db/authority.sqlite3 /var/lib/baton-managed-runs/w339626-custody-v2/instance/db/control.sqlite3.authoring.lock
```

Successful cmp has no output; preserve exit statuses in the operator receipt.
No missing Job/Control/Integration store is manufactured. The ordinary selected
future controller owns its supported initialization when separately launched.
Original stays fenced, including its packet/log/lock evidence, preventing two
usable deployments of the same authority. No claim of cleanup follows from this.

## 5. Provision the selected credential privately and grant source READ access

Copy the prepared helper into root custody and verify it before execution.
It reads the existing registry, selects exactly operator-file/w202663-development,
and copies opaque bearer bytes without printing, decoding or hashing them. It
creates only the two private files in /etc/baton-managed-entry and refuses any
existing destination or ambiguous registry. Existing source credentials stay
untouched. This is an explicit credential-copy operation for operator approval.

```sh
install -o root -g root -m 500 /home/sl/src/baton/work/records/2026/10/finding-v12-standard-next-run-path/findings/finding-managed-controller-boundary/provisioning-341498/provision-credential.py /root/baton-managed-entry-340184/provision-credential.py
printf '%s  %s\n' 4c8d430dbd7748836df2a25cf0fc83c5364749f8c171a8de86c7b67a88c32848 /root/baton-managed-entry-340184/provision-credential.py | sha256sum -c -
/usr/bin/python3 -I /root/baton-managed-entry-340184/provision-credential.py
setfacl -m u:61234:--x /home/sl
setfacl -R -P -m u:61234:r-X /home/sl/src/baton
runuser -u baton-w339626 -- test -r /home/sl/src/baton/.git/HEAD
runuser -u baton-w339626 -- test -r /home/sl/src/baton/v12/DESIGN.md
runuser -u baton-w339626 -- test -r /etc/baton-managed-entry/w339626-credential-sources.json
runuser -u baton-w339626 -- test -r /etc/baton-managed-entry/w339626-credential
runuser -u baton-w339626 -- test ! -w /home/sl/src/baton/.git/HEAD
runuser -u baton-w339626 -- test ! -w /home/sl/src/baton
/opt/baton-managed-entry/entry.py check w339626-custody-v2
```

The ACL deliberately grants read/traverse access to the nominated repository,
including Git objects and pinned task inputs, not write access. -P avoids walking
symlink targets. It grants no other home-directory read permission. Record this
access change explicitly; do not broaden to group sl. The new identity must read
all packet.fixture.files and their SHA256 must match the protected packet before
any future start (ordinary controller enforces pins too). Run this read-only
check from the operator root shell:

```sh
runuser -u baton-w339626 -- /usr/bin/python3 -I -c 'import json,hashlib,pathlib; p=json.loads(pathlib.Path("/opt/baton-managed-entry/selections/w339626-custody-v2/tree/config/PACKET.json").read_text()); root=pathlib.Path(p["fixture"]["source_root"]); assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==h for n,h in p["fixture"]["files"].items()); print("all selected source inputs match")'
```
 Re-run ownership/type
checks on credential files (uid61234,0400,nlink1; parent uid0,0711). Do not invoke
credential resolve merely to demonstrate access: that would unnecessarily read
bearer values. Entry check must report selection SHA256
04cc16db980abb8c10dbbdcf2d3e589f524c768f2ba1982f479615a232f52227.

## 6. Install narrow policy and validate in the actual managed context

Follow immutable candidate OPERATOR.md section "Narrow installed policy and
reload" exactly: root-copy/digest-check sudoers b15573e0..., visudo validation,
no-clobber installation, rules303ca565... in the mapped Codex home, and infra
start/status for codx-pc after quiescence. Do not arm. Then the assigned codxpc
handler, under its own claim, runs only:

```sh
/usr/bin/sudo -n /opt/baton-managed-entry/entry.py check w339626-custody-v2
/usr/bin/sudo -n /opt/baton-managed-entry/entry.py inspect w339626-custody-v2
```

Require check digest above, inspect image
sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2,
no approval prompt, no Job/attempt/store creation, and an independent receipt.
inspect exercises Linux Landlock ABI>=3 and actual nested Docker access; root
shell success alone is insufficient. A denial is a finding, not a fallback to
broad sudo, uid1000, another image, or arbitrary Python. W339626 remains blocked
until these receipts pass review. This procedure ends here, unarmed.

## Disable / rollback without losing evidence or duplicating authority

On any failure leave partial artifacts in place and keep the old run fenced.
If installed, run the accepted installer's `disable`. Remove admission by moving
only this selection's sudoers/rules to their .disabled evidence names as in the
immutable OPERATOR.md, then quiescent infra reload. This stops admission, not an
existing execution; do not claim cessation from it.

After no process uses uid61234, revoke only that uid's added source/home ACL
entries (`setfacl -R -P -x u:61234 /home/sl/src/baton` and
`setfacl -x u:61234 /home/sl`). Retain initial ACL receipts; do not apply a broad
--restore over concurrent repository changes. Lock the account with
`usermod --lock baton-w339626`; leave uid reserved, private storage and credentials
in custody. Do not delete stores, locks, accounts, credentials or consumed receipts,
change code modes, restore the original path's caller access, or activate either
copy. Returning the original authority to use would be a separately selected
recovery, never an automatic rollback. Thus disable is reversible admission
removal while preserving evidence; it is intentionally not automatic data rollback.
