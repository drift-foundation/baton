# The live-launch package — real Claude PR Job, prepared and gated (claim225533)

Owner pass 225531 asked for a concrete reviewed live-launch package on the
instance you installed from reviewed candidate 225452. EVERYTHING BEFORE
"the two authorized commands" below has ALREADY RUN AND PASSED this claim;
what remains is exactly two commands plus observation, and they run only on
your separate authorization. Nothing here has started a stack, reached a
provider, or submitted a Job.

## The deployment this package is bound to

- Instance: `/home/sl/baton-v12/instance-2026-09-21T01-12-21Z`
  (owner-installed from reviewed candidate 225452; executable
  `sha256:786af0d52f7c21b411a96143eda72ff4e6875533355d4ca5ff7117daf766bab2`
  verified equal to `RUNTIME-BUILD-225452.json` on this claim).
- Authority: `4e0bbf3c83824e7ca1d26f9d6b2ec180`.
- The A/B evidence instances (`instance-2026-09-20T15-53-26Z` and earlier)
  are untouched and preserved.

## Preflights that PASSED this claim (each re-runnable, none inferred)

1. **Installed identity** — `verify-next-instance.sh`: executable digest
   equals the reviewed 225452 records; fresh Authority; zero workers before
   configuration.
2. **Source delivery** — the accepted base
   `446fa8f79d9569799a77e888e8236070e1dc78f7`
   (`ACCEPTED-BASE-2026-09-21T01-11-48Z.json`) IS the tip of
   `refs/heads/main` in the nominated source `/home/sl/src/baton`
   (`git rev-parse` + `merge-base --is-ancestor`, read-only): ref-reachable,
   so an ordinary clone carries it — the reachability defect that blocked B
   on the previous instance cannot recur here.
3. **Pool composition** — `compose-pool-207219.py --instance <dest> --pr
   --base 446fa8f7…`: complete, zero refusals; PR shape (coder + reviewer,
   NO integration worker); job binding `line_declared_base = 446fa8f7…`,
   Work `4e0bbf3c-W1`, canonical target `w202663-target`; job input
   identity `sha256:1ad3c142…` stable across recomposition.
4. **Provider image identity** — both roles serve from
   `baton-v12-w202663-provider:e486652c`, engine-held ID equal to the
   configured digest `sha256:9ff3322f…` (the composer's own `image_present`
   contract, re-probed directly).
5. **Applied** — `tools.bootstrap` wrote the deployment: routes
   `impl -> baton.claude-coder`, `rview -> baton.claude-reviewer`; capacity
   one Job, two workers.
6. **Policy pin GATE** — `check-policy-pin.sh <dest> pool`: configured pin
   14 == Authority generation 14. (The gate first REFUSED 9≠8 and caught
   that this composer's prediction had never been ported to the measured
   PR-mode arithmetic; `policy_pin` in `compose-pool-207219.py` now carries
   it — PR costs one less per preparation, "first" means no deployment
   record — and the recomposed apply passed. The gate doing exactly its job.)
7. **Submission document** — two stages, review depends_on implementation,
   `terminal_policy: report-and-hold`; the task bytes request exactly the
   bounded two-path add-worker task (`v12/python/tools/pool.py` +
   `v12/python/tests/tools/test_pool.py`) with its own test gate
   (`tests.tools.test_pool` + `tests.tools.test_bootstrap`).

## Owner input preparation (the ONE thing only you can supply)

The workers' credential slot `claude` resolves through provider
`operator-file`, reference **`w202663-development`**, sources file
`/home/sl/.baton/credential-sources.json`, credential homes under
`<dest>/workers/{implementation,review}/credentials`. Before start, ensure
that reference resolves to a live Claude credential you intend to spend.
This Work read nothing behind the locator and will not.

## The two authorized commands (run only on your authorization)

    DEST=/home/sl/baton-v12/instance-2026-09-21T01-12-21Z
    just --justfile "$DEST/justfile" start
    cd /home/sl/src/baton/v12/python
    PYTHONPATH=src:. python3 -m tools.job_manager \
      --store "$DEST/db/jobs.sqlite3" \
      --incarnation w202663-claude-job-submit \
      --authority-uuid 4e0bbf3c83824e7ca1d26f9d6b2ec180 \
      submit --document /home/sl/src/baton/work/records/2026/09/finding-v12-initial-claude-worker-pool/pool-submission.json

On your signal after submit, I observe to terminal report-and-hold and
extract candidate/verdict/stream evidence through the supported public
readers — the same cadence as A and B.

## Enforced limits (stated exactly, per review220364 [2])

- One episode per stage BY CONSTRUCTION: report-and-hold opens one offer per
  stage; re-offer happens only through recovery, which is not authorized.
- Each provider turn is bounded by the deployment's own `provider_turn`
  execution limit (3600 s, compatibility origin, visible in the Job status
  projection).
- Verification commands are bounded by `verification_command_seconds`.
- So the authorized spend is at most ONE producer turn and ONE reviewer
  turn, each hard-bounded, plus the task's own bounded test commands.
- The reviewer refuses candidates touching paths outside the two allowed;
  nothing merges without you (OWNER-PR-FLOW-220329.md governs acceptance).

## What this package does NOT do

No start, no submission, no provider contact, no credential read has
happened. `REAL-JOB-PROPOSAL-220329.md`'s launch preamble (install + verify
+ compose) is SUPERSEDED by this package — the owner already installed this
instance and the preparation above already ran; only the two commands remain.
Do not rerun deterministic A/B; their instances are evidence.
