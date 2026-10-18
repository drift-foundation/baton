# Rehearsal step 1 — native staging through the installed command

Claim 324772, 2026-10-18. Disposable Job store under `/tmp`; no engine, no
provider, no container, no deployment, no Git command. Nothing in this step
needs any of them, which is why it is the first one.

## What was run

    R=$(mktemp -d)
    PYTHONPATH=src python3 -m tools.stack_command manager \
        --store "$R/jobs.sqlite3" --incarnation inc-1 \
        --authority-uuid 0123456789abcdef0123456789abcdef \
        submit --document submission.json

    PYTHONPATH=src python3 -m tools.stack_command manager \
        --store "$R/jobs.sqlite3" --incarnation inc-1 \
        --authority-uuid 0123456789abcdef0123456789abcdef status

`submission.json` and the captured answer `status-after-submit.json` are
beside this file.

## What it establishes

- The submission document contract, pinned for the packet:
  `baton.v12.job-submission/1`, members `schema`/`submission_id`/`jobs`, each
  Job `job_id`/`input_digest`/`policy_digest`/`test_scope`/`terminal_policy`/
  `stages`, each stage `kind`/`work_id`/`profile_name`/`profile_digest`/
  `depends_on`. Closed in both directions.
- The submission answers its own canonical signature, the Job list and the
  stage list (`quickstart-a/implementation`, `quickstart-a/review`), so a
  submission is replayable by exact operands rather than by name.
- **The review stage is NATIVE, GATED and BOUND.** The readback shows
  `quickstart-a/implementation` `queued` and `quickstart-a/review` `blocked`,
  both bound to Work `01234567-W1`, each with its own offer and attempt
  identity (`offer-599b1521…`/`attempt-599b1521…` and `attempt-5e2d52d2…`).
  That is the structural half of T321690 M324395 proof 1: the review
  assignment exists in the Job graph with exact Work/Job/stage/attempt
  binding, rather than being a status row.
- The effective limits a deployment would serve under are reported per Job and
  per boundary with their origin: `provider_turn` 3600s,
  `ordinary_verification` 900s, `integration_verification` 1800s,
  `host_verification` 300s, all `origin: compatibility`, generation 1. Those
  are the packet's pinned limits, read from the instance rather than quoted.
- `status` answers `canonical: false` for a store with no control-store
  reader attached, which is the honest distinction between an observation and
  the canonical record.

## What it does NOT establish, and is not claimed to

No candidate is produced, no stage is admitted, no attempt runs, and no
review verdict exists: this step submits and reads back. The eligible-act
derivation, the ending obligation, the review claim and the owner disposition
joined to this instance are the remaining proofs recorded in `PROGRESS.md`.
