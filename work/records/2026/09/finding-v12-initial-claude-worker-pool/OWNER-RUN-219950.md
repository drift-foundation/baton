# The exact A-then-B experiment commands — claim219950, for owner219700

Every artefact these commands launch is bound by digest: host runtime
`a6dbd963...` (RUNTIME-BUILD-219702.json, carries the D9 live-prior
attachment), emitting producer image `4638bae6...` and silent producer
`3c43c4e3...` (FIXTURE-IMAGES-219950.json, carry the task-derived
candidate; each proved on itself for two successive distinct tasks in
IMAGE-TASK-DERIVATION-*-219950.json). Nothing here touches
instance-2026-09-20T09-21-58Z, its held verification-3 episode, or the
queued verification-4 — those stay preserved for your disposition.

All commands run from this dossier unless a `cd` says otherwise.

## 1. Install and verify the corrected instance

    cd /home/sl/src/baton/work/records/2026/09/finding-v12-initial-claude-worker-pool
    ./install-next-instance.sh
    ./verify-next-instance.sh

`install-next-instance.sh` verifies the bundle against the 219702
records before and after copying, and retains the destination in
`selected-instance.txt`; every later command reads it from there.

## 2. Job A, to completion

    DEST="$(cat selected-instance.txt)"
    UUID="$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['authority_uuid'])" "$DEST/authority-identity.json")"
    cd /home/sl/src/baton/v12/python
    PYTHONPATH=src:. python3 ../../work/records/2026/09/finding-v12-initial-claude-worker-pool/compose-verification-208217.py \
      --instance "$DEST" --job verification-1 --emitting
    PYTHONPATH=src:. python3 -m tools.bootstrap \
      --inputs ../../work/records/2026/09/finding-v12-initial-claude-worker-pool/pool-bootstrap-inputs.json
    ../../work/records/2026/09/finding-v12-initial-claude-worker-pool/check-policy-pin.sh
    just --justfile "$DEST/justfile" start
    PYTHONPATH=src:. python3 -m tools.job_manager --store "$DEST/db/jobs.sqlite3" \
      --incarnation w202663-verification-1-submit --authority-uuid "$UUID" \
      submit --document ../../work/records/2026/09/finding-v12-initial-claude-worker-pool/pool-submission.json

Poll until all three of verification-1's allocations read `released`
(implementation and review `cleanup-retained`, integration
`integration-completed`; the claim219702 run took under a minute):

    PYTHONPATH=src:. python3 -m tools.job_manager --store "$DEST/db/jobs.sqlite3" \
      --incarnation w202663-status --authority-uuid "$UUID" status \
      | python3 -c "import json,sys; [print(j['job_id'], [(s['kind'], (s.get('allocation') or {}).get('allocation_state'), (s.get('allocation') or {}).get('release_reason')) for s in j['stages']]) for j in json.load(sys.stdin)['jobs']]"

Then the capture proof:

    python3 ../../work/records/2026/09/finding-v12-initial-claude-worker-pool/assert-capture-208916.py

## 3. Job B, composed AFTER A completed, on the SAME deployment

    just --justfile "$DEST/justfile" stop
    PYTHONPATH=src:. python3 ../../work/records/2026/09/finding-v12-initial-claude-worker-pool/compose-verification-208217.py \
      --instance "$DEST" --job verification-2 --emitting
    PYTHONPATH=src:. python3 -m tools.bootstrap \
      --inputs ../../work/records/2026/09/finding-v12-initial-claude-worker-pool/pool-bootstrap-inputs.json
    ../../work/records/2026/09/finding-v12-initial-claude-worker-pool/check-policy-pin.sh
    just --justfile "$DEST/justfile" start
    PYTHONPATH=src:. python3 -m tools.job_manager --store "$DEST/db/jobs.sqlite3" \
      --incarnation w202663-verification-2-submit --authority-uuid "$UUID" \
      submit --document ../../work/records/2026/09/finding-v12-initial-claude-worker-pool/pool-submission.json

B's composed task declares A's ADVANCED base (the composer reads the
canonical target at call time); its checkout materializes at that base
through the supplement, and its candidate file is task-derived
(`w197661-fixture-verification-2.txt`), so the base already carrying
A's file stages a real change. Poll with the same status command until
B's three allocations release.

## 4. What completion establishes, each checked separately

- A's history preserved across the restart: the same released
  allocations with the same reasons, no new episodes for A's attempts.
- Ref agreement twice: after each Job,
  `GIT_DIR="$DEST/repo/target.git" git for-each-ref` shows
  `refs/heads/main` equal to the Authority's `canonical_target`.
- Separate delivery roots:
  `$DEST/deployment-state/integration/integration-deliveries` holds one
  64-hex leaf per completed integration attempt under the mode-700
  managed ancestor.
- Cleanup with retention: `assert-capture-208916.py` passes again after
  B, and both Jobs' streams remain readable.

Stopping when done: `just --justfile "$DEST/justfile" stop` — stores
and evidence are retained.
