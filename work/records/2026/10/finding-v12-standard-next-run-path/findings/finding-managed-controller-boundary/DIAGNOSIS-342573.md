# Operator diagnosis — effective noninteractive admission

Scope: existing owner342404 installation selection; no arm/start. Run these read-only checks in the operator root shell, not as a managed escalation. Preserve command, exit status and nonsecret output in this dossier. No credential files or bearer values are needed.

```sh
/usr/sbin/visudo -c
sha256sum /etc/sudoers.d/baton-managed-entry
stat -c '%u %g %a %n' /etc/sudoers /etc/sudoers.d /etc/sudoers.d/baton-managed-entry
/usr/bin/sudo -l -U sl
getent passwd sl
readlink -f /usr/bin/sudo
```

Expected installed rule digest b15573e011758e6d98783bca9962fb2c8269d626740582e5abe85ea86b34188f. Inspect the root-readable sudoers include chain and precedence if validation/listing differs from accepted NOPASSWD/NOSETENV exact-entry operations. Syntax validation of a standalone fragment alone does not prove the active include chain. Do not print secrets or copy unrelated private configuration wholesale.

Also confirm the mapped codx-pc supervised process actually uses /home/sl/.codex-pushcoin, the reloaded rules digest303ca565862fe5040edf9a90ff8e71ae5b3721b9acca5d39b6fccfbeaf72d5f0, and its nonsecret effective caller identity/admission settings. A rules file existing on disk is not proof the failed command used it. Capture the actual failed-command launch boundary from supported runtime/operator diagnostics where available; reviewer uid_map is not its substitute. Do not dump process environment or provider transcripts.

If a discrepancy is confirmed, correct only the accepted installation/admission configuration, retaining before/after evidence and preserving narrow grants. Stop and return an exact finding if resolving it requires a different trusted mechanism. Quiesce the mapped context before any required reload; never restart a claimed executor. Do not repeat provisioning, cold-copy, credential copy, account creation, arming or authoring.

Pass to baton.codx for these existing selected managed probes, not a root-shell substitute:

```sh
/usr/bin/sudo -n /opt/baton-managed-entry/entry.py check w339626-custody-v2
/usr/bin/sudo -n /opt/baton-managed-entry/entry.py inspect w339626-custody-v2
```

Stop on failed check. Require exact selection/image digests from the review, full exit statuses/receipts, no approval prompt and no Job effects. Then pass to baton.bug for independent receipt acceptance. No arm/start.
