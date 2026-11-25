# Exact commands — Q4 packet q4-386227

From `/home/sl/src/baton`, prepared interpreter only. Payload manifest `1eb7ff182c623dfecfe1fed97b9176da441f80e13da2b7b007b1b85c6d3097dd`.

Read-only check (no engine, credential or provider):

```sh
/home/sl/.local/state/baton-v12-venv/bin/python -B work/records/2026/11/finding-v12-native-provider-selection/evidence/q4-packet-386227/owner-run.py --check
```

Deterministic checks (fake engine, synthetic logins; each removes its own `/var/tmp` root on success):

```sh
P=work/records/2026/11/finding-v12-native-provider-selection/evidence/q4-packet-386227
/home/sl/.local/state/baton-v12-venv/bin/python -B $P/check_registry.py
/home/sl/.local/state/baton-v12-venv/bin/python -B $P/check_observe.py
for s in offline-pass build-fail wrong-version image-drift accepted uncertain wrong-contributor no-report no-edit launch-fail stall oversize-claude-login; do /home/sl/.local/state/baton-v12-venv/bin/python -B $P/check_execute.py $s; done
```

## Selection A — offline (no credential, no provider)

Only after review of this packet and an owner selection of the offline phase. Replace `Q4_OFFLINE_SELECTION` with the selection message locator.

```sh
env -u GIT_PAGER /home/sl/.local/state/baton-v12-venv/bin/python -B work/records/2026/11/finding-v12-native-provider-selection/evidence/q4-packet-386227/owner-run.py --offline --selection Q4_OFFLINE_SELECTION --packet 1eb7ff182c623dfecfe1fed97b9176da441f80e13da2b7b007b1b85c6d3097dd
```

Fresh private root `/var/tmp/baton-q4-386227` and fresh public destination `evidence/q4-execution-386227`; both must be absent. One build, three inventory runs, no worker container. No retry. Public output: `evidence/q4-execution-386227/OFFLINE-RESULT.json`.

After it, for the reviewer:

```sh
sha256sum /var/tmp/baton-q4-386227/OFFLINE-RESULT.json        # -> OFFLINE_RESULT_SHA256
```

## Selection B — live (one Codex turn, one Claude review turn)

Only after review of the offline result and a separate owner selection that includes real credential access. Replace both placeholders.

```sh
env -u GIT_PAGER /home/sl/.local/state/baton-v12-venv/bin/python -B work/records/2026/11/finding-v12-native-provider-selection/evidence/q4-packet-386227/owner-run.py --live --selection Q4_LIVE_SELECTION --packet 1eb7ff182c623dfecfe1fed97b9176da441f80e13da2b7b007b1b85c6d3097dd --offline-result-sha256 OFFLINE_RESULT_SHA256
```

Uses the instance the offline phase prepared. One run only; a second is refused. The script stops itself at 20 minutes and then cleans up (up to 150 s more). Public output: `evidence/q4-execution-386227/RESULT.json`. Exit 0 means the capture ended in a recorded verdict, an uncertainty owner item, or a held review, with both containers gone; it never means acceptance.

Owner queue after the run (also saved privately as `live/owner-items.json`):

```sh
python3 -c "import json;print(json.load(open('/var/tmp/baton-q4-386227/live/owner-items.json')))"
```

## Optional, separate owner act — the alias in your ordinary registry

Not needed for Q4 (the packet uses its own private registry) and not run by me. It reads and writes only the registry document, refuses a different existing mapping, and never opens the login file:

```sh
/home/sl/.local/state/baton-v12-venv/bin/python -B work/records/2026/11/finding-v12-native-provider-selection/evidence/q4-packet-386227/registry.py --registry /home/sl/.baton/credential-sources.json --map operator-file:claude-primary-subscription=/home/sl/.claude/.credentials.json
```
