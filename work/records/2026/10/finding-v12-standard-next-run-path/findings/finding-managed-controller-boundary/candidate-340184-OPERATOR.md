# Operator installation proposal — NOT EXECUTED

Requires independent acceptance of this candidate AND the explicit custody
successor in SUCCESSOR.json. No parent authoring invocation is selected.
Do not install while codxpc holds Work or another mapped consumer is running.
Operator owns sudo/root policy and quiescent stop/start; agents do not install.
Root and the system Python/stdlib/Docker client are trusted administrator inputs.
The managed user never receives a general sudo/interpreter/env command grant.
The proposed entry drops to unique service uid61234/gid61234 with supplementary Docker group119;
that group is a selected execution capability, not a sandbox-wide socket change.

## Digests and root custody

Entry SHA256 `7547b27f88873e240f1a0666e6c1cdd7dfc5d2a9064974264aea4be6fcdf1d15`; installer SHA256 `76da2696c37f41a1312cdf9e7d8ea322a608479ad802481659bdd4476be6f00c`.
Bundle manifest SHA256 `240abf377476e41436c90b12bab70583117cbf81e47efa0079be11876cbf53eb`.
Selection SHA256 `04cc16db980abb8c10dbbdcf2d3e589f524c768f2ba1982f479615a232f52227`.
Original parent packet and instance remain untouched. SUCCESSOR.json records
EVERY packet/deployment change from candidate340058. This correction relocates
operational storage as well as immutable inputs, changes execution identity and
workspace group, and proposes a root-controlled credential registry reference.
It preserves authority/Work/Job/run identifiers and controller/helper/runtime/
submission/task bytes and limits. These are proposed bytes, not a claim that the
referenced private state exists or that a launch is selected.

## Required provisioning decision before installation or arming

The candidate is unprovisioned. Do not run the installation sequence below until
independent review AND an explicit operator provisioning plan resolve:

- Reserve uid/gid61234 exclusively for this selection, with no unrelated owned
  files or running processes. A reused service identity is not acceptable.
- Establish root-owned /var/lib/baton-managed-runs and private0700 selection
  storage, home and tmp. The new prepare-storage command creates EMPTY storage,
  refuses overlap and never copies, opens or changes an existing instance.
- Select how the existing authority/store identity is placed in that storage
  under operator custody, preserving evidence and quiescence. Neither copying
  live SQLite files nor creating a new authority is selected by this proposal.
  This is an unresolved operation outside340055, not a reason to invent state.
- Provision /etc/baton-managed-entry/w339626-credential-sources.json and its
  referenced sources for service-uid readability under operator-controlled
  ancestry. No credential bytes have been inspected, copied or bundled.
- Validate nominated source access and Docker group119 for the new identity.
  Workspace group becomes61234; top-level private storage prevents uid1000 from
  reaching group-shared descendants. Operator must not grant access through
  another account, ACL, process or mount. No account changes have occurred.

A private controller tree and unique identity prevent the managed caller from
racing Docker daemon host-path resolution. Landlock additionally enforces content
write/create/remove confinement for the controller and its child processes,
including already-planted links and replaced ancestors. Linux ABI>=3 is required
for truncate protection; unsupported kernels fail closed. It is NOT a general
sandbox for the Docker daemon, metadata syscalls, or arbitrary code with a Docker
socket. The unchanged, digest-bound controller and selected Docker operations
remain trusted. Root policy, service-identity exclusivity and private ancestors
are mandatory, not substitutes for Landlock. No fallback to the caller's uid or
old /tmp operational paths is permitted.

The following commands are a concrete installation proposal after those
prerequisites, not authority to perform migration or account provisioning.

Use a root-owned copy of the installer so checking a mutable /tmp script and
then executing it as root cannot race. Refuse any pre-existing installation or
selection; do not delete partial output to force a retry. Commands below are
operator actions after acceptance, not actions already performed:

```sh
sudo mkdir -m 700 /root/baton-managed-entry-340184
sudo install -o root -g root -m 500 /tmp/baton-managed-entry-340184/v12/python/tools/managed_entry_install.py /root/baton-managed-entry-340184/installer.py
sudo sha256sum /root/baton-managed-entry-340184/installer.py
```

The output MUST equal installer `76da2696c37f41a1312cdf9e7d8ea322a608479ad802481659bdd4476be6f00c` before the next command.
Stop on mismatch; the protected copy remains evidence.

```sh
sudo /usr/bin/python3 -I /root/baton-managed-entry-340184/installer.py install /tmp/baton-managed-entry-340184/v12/python/tools/managed_entry.py 7547b27f88873e240f1a0666e6c1cdd7dfc5d2a9064974264aea4be6fcdf1d15
sudo /usr/bin/python3 -I /root/baton-managed-entry-340184/installer.py register /tmp/baton-managed-entry-340184/operator-bundle 240abf377476e41436c90b12bab70583117cbf81e47efa0079be11876cbf53eb
sudo /usr/bin/python3 -I /root/baton-managed-entry-340184/installer.py prepare-storage w339626-custody-v2 61234 61234
# Complete the separately selected provisioning plan before check.
sudo /opt/baton-managed-entry/entry.py check w339626-custody-v2
```

Expected check: selected digest `04cc16db980abb8c10dbbdcf2d3e589f524c768f2ba1982f479615a232f52227`, checked (this observation does not arm or grant a start).
Installer holds all bundle bytes and verifies every digest before publication;
selection is published last. Partial publication remains disarmed. Custody is
root-owned through all ancestors; neither sl nor the managed sandbox can change
code after the check. No namespaces/remapped Docker host paths are introduced.
Operational roots must resolve inside the private storage. Admission rejects
preexisting symlinks/hardlinks/special files and loose ownership/modes. Runtime
writes remain mutable under the selected uid; kernel confinement lasts through
exec and every descendant. TMPDIR is private and umask077 applies.

## Narrow installed policy and reload

Validate sudoers before installing. Root-copy and check its digest before moving
into the live sudoers directory; no broad Python/env/shell grants are included.

```sh
sudo install -o root -g root -m 440 /tmp/baton-managed-entry-340184/operator/managed-entry.sudoers /root/baton-managed-entry-340184/sudoers
sudo sha256sum /root/baton-managed-entry-340184/sudoers
```

Require `b15573e011758e6d98783bca9962fb2c8269d626740582e5abe85ea86b34188f`. Then:

```sh
sudo visudo -cf /root/baton-managed-entry-340184/sudoers
sudo test ! -e /etc/sudoers.d/baton-managed-entry
sudo cp --no-clobber /root/baton-managed-entry-340184/sudoers /etc/sudoers.d/baton-managed-entry
cp --no-clobber /tmp/baton-managed-entry-340184/operator/managed-entry.rules /home/sl/.codex-pushcoin/rules/managed-entry.rules
sha256sum /home/sl/.codex-pushcoin/rules/managed-entry.rules
```

Require rules digest `303ca565862fe5040edf9a90ff8e71ae5b3721b9acca5d39b6fccfbeaf72d5f0`. Do not continue on collision
or mismatch. After quiescence, operator reloads the one mapped supervised context:

```sh
python3 tools/infra.py stop /home/sl/baton-v11.14aecfb/codx-pc
python3 tools/infra.py start /home/sl/baton-v11.14aecfb/codx-pc
python3 tools/infra.py status /home/sl/baton-v11.14aecfb/codx-pc
```

The mapped managed context, under its own operational claim, then runs exactly:

```sh
/usr/bin/sudo -n /opt/baton-managed-entry/entry.py check w339626-custody-v2
/usr/bin/sudo -n /opt/baton-managed-entry/entry.py inspect w339626-custody-v2
```

Require actual correct image digest, no approval, no Job/attempt effects and an
independent receipt. Static rules/tests are not proof of effective policy.
Parser rejects trailing/duplicate/child-entry flags before privileged effects.
Never authorize the installer, arm, arbitrary packet, interpreter or env through
managed rules. Prefix matching is safe only in conjunction with the closed entry.

## Future explicit selection only — do NOT execute now

After separate owner selection of this successor, operator can arm exactly these
bytes with the existing installer `arm` operation. That is intentionally not in
managed policy. The command, reserved for that future decision, is:

```sh
sudo /usr/bin/python3 -I /root/baton-managed-entry-340184/installer.py arm w339626-custody-v2 04cc16db980abb8c10dbbdcf2d3e589f524c768f2ba1982f479615a232f52227
```

Only then may a separately selected managed start invoke:

```sh
/usr/bin/sudo -n /opt/baton-managed-entry/entry.py start w339626-custody-v2
```

Start durably consumes once BEFORE exec. Failure/crash/unknown after consumption
never rearms. No entry restart/recovery or second invocation is implied. Exact
controller token/lock/cleanup semantics are unchanged; exec preserves signal
handling without an extra privileged supervisory wrapper. Independent candidate acceptance ends the
implementation exception before installation; no extra host implementation follows it.

## Rollback / disable admission

Operator-only, after recording any active execution. Disable prevents new entry
operations; it does not stop or declare cessation of an existing controller.
Keep retained code, selection, consumption receipt and operational evidence.

```sh
sudo /usr/bin/python3 -I /root/baton-managed-entry-340184/installer.py disable
mv /home/sl/.codex-pushcoin/rules/managed-entry.rules /home/sl/.codex-pushcoin/rules/managed-entry.rules.disabled
sudo mv /etc/sudoers.d/baton-managed-entry /root/baton-managed-entry-340184/sudoers.disabled
```

Then repeat the same quiescent infra stop/start/status sequence above. Do not
remove source custody while an execution uses it, delete locks, clear consumed
receipts, restore a spent selection, or treat policy removal as worker cessation.
