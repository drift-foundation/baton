# Commands and execution dependencies

Preparation only, from `/home/sl/src/baton`:

```sh
/home/sl/.local/state/baton-v12-venv/bin/python -B work/records/2026/11/finding-v12-native-provider-selection/evidence/q2-phase-ending-386207/owner-run.py --check
/home/sl/.local/state/baton-v12-venv/bin/python -B work/records/2026/11/finding-v12-native-provider-selection/evidence/q2-phase-ending-386207/check_preflight.py
/home/sl/.local/state/baton-v12-venv/bin/python -B work/records/2026/11/finding-v12-native-provider-selection/evidence/q2-phase-ending-386207/check_image_gate.py
/home/sl/.local/state/baton-v12-venv/bin/python -B work/records/2026/11/finding-v12-native-provider-selection/evidence/q2-phase-ending-386207/check_collection.py
/home/sl/.local/state/baton-v12-venv/bin/python -B work/records/2026/11/finding-v12-native-provider-selection/evidence/q2-phase-ending-386207/check_execute.py launch-fail
/home/sl/.local/state/baton-v12-venv/bin/python -B work/records/2026/11/finding-v12-native-provider-selection/evidence/q2-phase-ending-386207/check_execute.py oversize
/home/sl/.local/state/baton-v12-venv/bin/python -B work/records/2026/11/finding-v12-native-provider-selection/evidence/q2-phase-ending-386207/check_execute.py fault-terminal
/home/sl/.local/state/baton-v12-venv/bin/python -B work/records/2026/11/finding-v12-native-provider-selection/evidence/q2-phase-ending-386207/check_execute.py provider-seam
```

Payload SHA256 `5ce02041df3b6795a6e093157b6c073fe410687ccd65f775c76bcbee012d7567`. Seven selected checks passed; default check is also exercised by preflight. `checks/account.json` binds their exact payload and timings. Docker is substituted before subprocess execution in the four execute scenarios, Git is confined to their fresh disposable fixture, only synthetic login files are read, and the provider seam deliberately throws after a labelled edit. No fabricated successful provider stream. Successful synthetic roots are removed.

## Future owner command — NOT selected

Prerequisites: independent candidate acceptance/checkpoint, separately authorized build and offline qualification of the changed image, independent review of that exact evidence, and explicit one-turn execution selection. Preserve the old image/packet. No build or engine command is authorized by this document.

The next image review must produce a Q1-format bundle with `review`, `manifest_files_verified` and `retained` members (the seven retained document names in q1-accepted-evidence.json). Verify the full offline evidence manifest before creating the reduced bundle; retain it with the bundle, rather than inventing observations. Its image_files must match q1-build.json here exactly. Record the actual future checkpoint and source manifest in image/observed identity. Never edit an old receipt to describe a new build. Select the resulting absolute bundle path, exact SHA256 and review locator with the execution instruction. No binding exists yet.

After those prerequisites, substitute the actual three values in this exact argv template:

```sh
env -u GIT_PAGER /home/sl/.local/state/baton-v12-venv/bin/python -B work/records/2026/11/finding-v12-native-provider-selection/evidence/q2-phase-ending-386207/owner-run.py --execute --selection OWNER_MESSAGE_ID --payload 5ce02041df3b6795a6e093157b6c073fe410687ccd65f775c76bcbee012d7567 --image-evidence /ABSOLUTE/REVIEWED/NEW-IMAGE-EVIDENCE.json --image-evidence-sha256 REVIEWED_SHA256
```

The script refuses missing/mismatched/old-image evidence before engine access or credential delivery. Owner selection is audit evidence, not a permission service. UID:GID1000:1000, fresh `/var/tmp/baton-codex-q2-386207`, fresh dossier `evidence/q2-execution-386207`, at least4GiB free, prepared interpreter and no other GIT_* overrides are required. Bounds: one CLI turn180s, verification15s, capture240s, outer300s plus90s cleanup. No retry. Fixed model/account/tier and accepted sandbox/egress posture are detailed in README.

Exit0 means terminal capture and cleanup, not successful authentication/edit/task/review. Acceptance always remains held. Raw evidence and refreshed home remain private; only the fixed RESULT is promoted. Future private-evidence review is separately authorized.
