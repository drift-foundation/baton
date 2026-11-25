# Exact commands and pending values

From `/home/sl/src/baton`, prepared interpreter only. Draft read-only checks:

```sh
/home/sl/.local/state/baton-v12-venv/bin/python -B work/records/2026/11/finding-v12-native-provider-selection/evidence/readiness-386214/q1/owner-run.py --check
/home/sl/.local/state/baton-v12-venv/bin/python -B work/records/2026/11/finding-v12-native-provider-selection/evidence/readiness-386214/q2/owner-run.py --check
```

After independent review and the actual human checkpoint, bind the exact source into a fresh durable successor:

```sh
/home/sl/.local/state/baton-v12-venv/bin/python -B work/records/2026/11/finding-v12-native-provider-selection/evidence/readiness-386214/finalize.py --repository /home/sl/src/baton --checkpoint FULL_HUMAN_CHECKPOINT --output /home/sl/src/baton/work/records/2026/11/finding-v12-native-provider-selection/evidence/readiness-final-386214
```

`FULL_HUMAN_CHECKPOINT` is presently unresolved, not2eb55622 or a synthetic test commit. Exact source mismatch refuses. Preserve FINALIZATION.json and compare its `preparation_manifest_sha256` with the reviewed packet manifest. It supplies the two exact digests below; do not substitute a current working-tree hash.

Only after separate owner selection of one build/offline run and README settings:

```sh
env -u GIT_PAGER /home/sl/.local/state/baton-v12-venv/bin/python -B work/records/2026/11/finding-v12-native-provider-selection/evidence/readiness-final-386214/q1/owner-run.py --execute --selection Q1_OWNER_SELECTION --packet-digest FINALIZATION_Q1_MANIFEST_SHA256
```

Select actual owner message locator and FINALIZATION.json.q1_manifest_sha256. Source finalization is not build authority. No retry. Inspect full promoted RESULT/cleanup/worker/image receipts and manifest under q1-execution-386214. Independent review then prepares the exact reduced bundle:

```sh
/home/sl/.local/state/baton-v12-venv/bin/python -B work/records/2026/11/finding-v12-native-provider-selection/evidence/readiness-386214/bundle-image.py --evidence /home/sl/src/baton/work/records/2026/11/finding-v12-native-provider-selection/evidence/q1-execution-386214 --manifest-sha256 REVIEWED_FULL_MANIFEST_SHA256 --review Q1_REVIEW_MESSAGE --finalized-q2 /home/sl/src/baton/work/records/2026/11/finding-v12-native-provider-selection/evidence/readiness-final-386214/q2 --output /home/sl/src/baton/work/records/2026/11/finding-v12-native-provider-selection/evidence/q1-execution-386214/reviewed-image-bundle.json
```

The bundle command validates existing ordinary evidence; it does not approve it. Retain its printed bundle SHA256. It checks exact final source/worker identity as well as the Q2 gate. It must not be used to relabel old observations.

Only after separate Q2 owner selection including real credential access/copy and the fixed README settings:

```sh
env -u GIT_PAGER /home/sl/.local/state/baton-v12-venv/bin/python -B work/records/2026/11/finding-v12-native-provider-selection/evidence/readiness-final-386214/q2/owner-run.py --execute --selection Q2_OWNER_SELECTION --payload FINALIZATION_Q2_PAYLOAD_SHA256 --image-evidence /home/sl/src/baton/work/records/2026/11/finding-v12-native-provider-selection/evidence/q1-execution-386214/reviewed-image-bundle.json --image-evidence-sha256 REVIEWED_BUNDLE_SHA256
```

Q2 choices remain gpt-6-astra, fast unset and codex-pushcoin-subscription at ~/.codex-pushcoin/auth.json; no reselection requested. The unresolved values are actual human checkpoint, resulting payload digests, Q1 execution authorization/evidence review and Q2 execution authorization. No credential/provider execution is authorized by preparation or by a placeholder string. Future private evidence review is separately selected; no native acceptance follows from exit0.
