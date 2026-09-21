# The concrete useful real Claude Job — proposal for separate owner authorization

Claim220329, under OWNER-HANDOFF-PR-JOBS item 3. NOTHING HERE LAUNCHES:
this document is the complete proposal the owner authorizes (or trims)
separately. The PR model applies — the Job's deliverable is a durable
reviewed candidate; Slawomir merges.

## The task: the recorded worker-add task, bounded

The dossier already records the first development task
(compose-pool-207219.py `task_document`): user-managed addition of
workers to an existing v12 pool, independently of bootstrap and of any
individual Job — breaking the coupling `tools/bootstrap.py` states out
loud ("A worker is configured WITH the Job it serves") without changing
the image-identity rules W202663 corrected. The owner asked whether it
can be bounded appropriately; this proposal bounds it:

- **Objective (bounded):** a `tools/pool.py` verb `add-worker` that
  admits ONE worker document into an existing instance's deployment —
  validating exactly what bootstrap validates for a worker (image
  digest against its own manifest, participant/principal resolution,
  profile shape), rewriting `deployment.json` and predicting the pool
  generation the scheduler will mint — WITHOUT preparing any Job,
  submitting anything, or touching Works. Explicitly out of scope:
  removing workers (D10's settled-history territory), changing
  bootstrap, UX polish.
- **Why useful:** it is the smallest real step toward the owner's
  operational need (growing a live pool between Jobs) and its absence
  is what forced every capacity change through full bootstrap re-runs
  and the policy-pin dance this Work has been measuring.
- **Tradeoff if trimmed further:** a smaller documentation-only task
  would demonstrate the flow but deliver no capability; this bounded
  verb is the smallest USEFUL cut. The full original task (general
  user-managed pool management) stays open.

## The Job document

- **Base:** the owner-accepted commit current at authorization time,
  supplied EXPLICITLY via the composer's `--base` (an opaque input;
  claim222049 ported the operand to this composer)
  (today: `93da9d62...` on the official line, or the accepted base
  recorded per OWNER-PR-FLOW-220329.md section 4).
- **Repository/path scope:** the v12 checkout; allowed paths
  `v12/python/tools/pool.py` (new), `v12/python/tests/tools/
  test_pool.py` (new), and nothing else — the reviewer refuses
  candidates touching other paths.
- **Verification (the task's own gate):**
  `python3 -m unittest tests.tools.test_pool tests.tools.test_bootstrap`
  — the new verb's own tests plus the existing bootstrap family
  proving the coupling it must not break.
- **Output:** one PR candidate per the result contract — immutable
  commit on the durable line, base, changed paths, patch, bundle,
  verification transcript.
- **Pool:** the heterogeneous Claude pool `compose-pool-207219.py`
  composes, in PR shape (producer `baton.claude-coder` on the provider
  image, reviewer `baton.claude-reviewer` on the provider image; NO
  integration worker), on a fresh instance installed from the reviewed
  candidate current at authorization.
- **Credentials binding:** the deployment's existing `claude` slot;
  the operator supplies what is behind the locator
  (`CREDENTIAL_REFERENCE` in the composer); this Work reads no
  credential.
- **Independent review:** `baton.claude-reviewer` (a separate live
  session under its own participant) applies the recorded review role
  instructions; its verdict is the acceptance gate BEFORE the owner
  ever looks.

## Exact launch commands (run only after owner authorization)

    cd /home/sl/src/baton/work/records/2026/09/finding-v12-initial-claude-worker-pool
    ./install-next-instance.sh && ./verify-next-instance.sh
    DEST="$(cat selected-instance.txt)"
    UUID="$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['authority_uuid'])" "$DEST/authority-identity.json")"
    cd /home/sl/src/baton/v12/python
    PYTHONPATH=src:. python3 ../../work/records/2026/09/finding-v12-initial-claude-worker-pool/compose-pool-207219.py \
      --instance "$DEST" --pr --base <the accepted base current at authorization>
    # (both flags are IMPLEMENTED as of claim220385 -- select_instance reads
    #  the destination's own persisted identity, --pr composes coder+reviewer
    #  only, and the task bytes now request exactly the bounded two-path
    #  add-worker task with its own test gate. Validated with write=False
    #  against the retained instance: two-role manifests and images compose;
    #  bootstrap.held refuses there because that root already holds Jobs the
    #  pool document does not name -- the fresh-instance validation is part
    #  of this authorized run's own step, before start.)
    PYTHONPATH=src:. python3 -m tools.bootstrap --inputs ../../work/records/2026/09/finding-v12-initial-claude-worker-pool/pool-bootstrap-inputs.json
    ../../work/records/2026/09/finding-v12-initial-claude-worker-pool/check-policy-pin.sh
    just --justfile "$DEST/justfile" start
    PYTHONPATH=src:. python3 -m tools.job_manager --store "$DEST/db/jobs.sqlite3" \
      --incarnation w202663-claude-job-submit --authority-uuid "$UUID" \
      submit --document ../../work/records/2026/09/finding-v12-initial-claude-worker-pool/pool-submission.json

Then the OWNER-PR-FLOW-220329.md inspection/acceptance steps over the
resulting candidate. What authorization covers, with the ENFORCED
limits stated exactly (review220364 [2]): one episode per stage by
construction (report-and-hold opens one offer per stage and re-offers
only through recovery, which is not authorized here), each provider
turn bounded by the deployment's own `provider_turn` execution limit
(3600 seconds, compatibility origin, visible in the Job status
projection), verification commands bounded by
`verification_command_seconds`. So the authorized spend is at most one
producer turn and one reviewer turn, each hard-bounded by the
deployment's limits; nothing merges without the owner.
