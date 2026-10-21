# Operator installation proposal — NOT EXECUTED

Requires independent acceptance of this candidate AND the explicit custody
successor in SUCCESSOR.json. No parent authoring invocation is selected.
Do not install while codxpc holds Work or another mapped consumer is running.
Operator owns sudo/root policy and quiescent stop/start; agents do not install.
Root and the system Python/stdlib/Docker client are trusted administrator inputs.
The managed user never receives a general sudo/interpreter/env command grant.
The fixed entry drops to uid1000/gid1000 with only supplementary Docker group119;
that group is a selected execution capability, not a sandbox-wide socket change.

## Digests and root custody

Entry SHA256 `d05aeecf9a5ec5bbac63e894c524d3873ed1df7103b938a8a1c2640316ace2cd`; installer SHA256 `5b7505f2714a72710d3b970342abb2e394fb004f9eea806e5a5721a93ece8a18`.
Bundle manifest SHA256 `b3f24c7ffa26e8f741dd58cf5f924762f9c9cf507a4c246a19b4fa3f165548ef`.
Selection SHA256 `b7be91909475f27051f13d27e5ad7e977ad3172a97c6c2839077d0512e1598da`.
Original parent packet remains byte-for-byte intact. The successor changes
only protected source/runtime/config locations and resulting config digest;
source/controller/helper/runtime/task bytes, original limits and instance/
authority/run/Job/lock/output bindings are retained. It is NOT silently accepted
as the old packet. Review SUCCESSOR.json and the complete manifest before install.
This selection stays disarmed: check/inspect/registration cannot start a Job.

Use a root-owned copy of the installer so checking a mutable /tmp script and
then executing it as root cannot race. Refuse any pre-existing installation or
selection; do not delete partial output to force a retry. Commands below are
operator actions after acceptance, not actions already performed:

```sh
sudo mkdir -m 700 /root/baton-managed-entry-340058
sudo install -o root -g root -m 500 /tmp/baton-managed-entry-340058/v12/python/tools/managed_entry_install.py /root/baton-managed-entry-340058/installer.py
sudo sha256sum /root/baton-managed-entry-340058/installer.py
```

The output MUST equal installer `5b7505f2714a72710d3b970342abb2e394fb004f9eea806e5a5721a93ece8a18` before the next command.
Stop on mismatch; the protected copy remains evidence.

```sh
sudo /usr/bin/python3 -I /root/baton-managed-entry-340058/installer.py install /tmp/baton-managed-entry-340058/v12/python/tools/managed_entry.py d05aeecf9a5ec5bbac63e894c524d3873ed1df7103b938a8a1c2640316ace2cd
sudo /usr/bin/python3 -I /root/baton-managed-entry-340058/installer.py register /tmp/baton-managed-entry-340058/operator-bundle b3f24c7ffa26e8f741dd58cf5f924762f9c9cf507a4c246a19b4fa3f165548ef
sudo /opt/baton-managed-entry/entry.py check w339626-custody-v1
```

Expected check: selected digest `b7be91909475f27051f13d27e5ad7e977ad3172a97c6c2839077d0512e1598da`, checked (this observation does not arm or grant a start).
Installer holds all bundle bytes and verifies every digest before publication;
selection is published last. Partial publication remains disarmed. Custody is
root-owned through all ancestors; neither sl nor the managed sandbox can change
code after the check. No namespaces/remapped Docker host paths are introduced.
Existing mutable operational data is still governed by the unchanged controller;
this entry does not claim to make /tmp stores immutable or repair their state.

## Narrow installed policy and reload

Validate sudoers before installing. Root-copy and check its digest before moving
into the live sudoers directory; no broad Python/env/shell grants are included.

```sh
sudo install -o root -g root -m 440 /tmp/baton-managed-entry-340058/operator/managed-entry.sudoers /root/baton-managed-entry-340058/sudoers
sudo sha256sum /root/baton-managed-entry-340058/sudoers
```

Require `b15573e011758e6d98783bca9962fb2c8269d626740582e5abe85ea86b34188f`. Then:

```sh
sudo visudo -cf /root/baton-managed-entry-340058/sudoers
sudo test ! -e /etc/sudoers.d/baton-managed-entry
sudo cp --no-clobber /root/baton-managed-entry-340058/sudoers /etc/sudoers.d/baton-managed-entry
cp --no-clobber /tmp/baton-managed-entry-340058/operator/managed-entry.rules /home/sl/.codex-pushcoin/rules/managed-entry.rules
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
/usr/bin/sudo -n /opt/baton-managed-entry/entry.py check w339626-custody-v1
/usr/bin/sudo -n /opt/baton-managed-entry/entry.py inspect w339626-custody-v1
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
sudo /usr/bin/python3 -I /root/baton-managed-entry-340058/installer.py arm w339626-custody-v1 b7be91909475f27051f13d27e5ad7e977ad3172a97c6c2839077d0512e1598da
```

Only then may a separately selected managed start invoke:

```sh
/usr/bin/sudo -n /opt/baton-managed-entry/entry.py start w339626-custody-v1
```

Start durably consumes once BEFORE exec. Failure/crash/unknown after consumption
never rearms. No entry restart/recovery or second invocation is implied. Exact
controller token/lock/cleanup semantics are unchanged; exec preserves signal
handling without an extra privileged supervisory wrapper. Installation ends the
implementation exception; no extra host implementation follows it.

## Rollback / disable admission

Operator-only, after recording any active execution. Disable prevents new entry
operations; it does not stop or declare cessation of an existing controller.
Keep retained code, selection, consumption receipt and operational evidence.

```sh
sudo /usr/bin/python3 -I /root/baton-managed-entry-340058/installer.py disable
mv /home/sl/.codex-pushcoin/rules/managed-entry.rules /home/sl/.codex-pushcoin/rules/managed-entry.rules.disabled
sudo mv /etc/sudoers.d/baton-managed-entry /root/baton-managed-entry-340058/sudoers.disabled
```

Then repeat the same quiescent infra stop/start/status sequence above. Do not
remove source custody while an execution uses it, delete locks, clear consumed
receipts, restore a spent selection, or treat policy removal as worker cessation.
