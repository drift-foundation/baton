# Recovery from the pre-runtime launch failure — the reviewed path (claim226458)

Per owner 226456 and review-2026-09-21T03-30-36Z.md. NOTHING LIVE RAN this
claim: no credential mutation, no restart, no submission. Everything below
"the owner's commands" is prepared, applied and gate-checked; the commands
are yours.

## Why a FRESH JOB, not a retry of the failed attempt

Established from the product's own closed sets (review226363's correction
accepted):

- The failed attempt's allocation is RELEASED
  (`launch-failed-before-runtime`); reservation refuses re-reserving a
  released assignment. Ordinary ticks do not retry it.
- Its episode is LIVE (ended_state null) and a live episode earns a
  successor only through an ending in `REPLACEABLE_ENDINGS =
  ("abandoned-after-restart", "abandoned-after-exclusion")`.
  `abandoned-after-restart` settles only ISSUED offers from another manager
  incarnation — ours was CLAIMED. `abandoned-after-exclusion` is the
  W128698 operator-abandonment machinery (fence, runtime destruction,
  checkout restore, writer exclusion) built for attempts whose CONTAINER
  RAN; no packaged operator command exists for this pooled composition, and
  building one now would be new product surface on the critical path.
- The FRESH-JOB cadence is this Work's own accepted correction path
  (review208349; verification composer's `select_job`, claim208777): the
  failed Job stays preserved evidence under its own identities; a new Job
  composes beside it under fresh identities.

## Prior assignment disposition (verified, preserved)

- `w202663-first-development-job`: implementation exceptional, allocation
  released 03:21:27Z, episode 1 live-but-unfinishable, review blocked. NO
  runtime ever existed; nothing to destroy. Kept in the deployment and the
  Job store verbatim — the apply printed "work 13c91b69-W1 already exists;
  left alone" and its workers/routes travel as recorded.

## What was prepared and gate-checked THIS claim (no live acts)

- `compose-pool-207219.py` gained the verification composer's reviewed
  two-Job support (ported: `select_job`/`--job`, `prepared_workers`,
  `prepared_jobs`, pool-generation prediction from the durable pool,
  per-job pin arithmetic, retained-participant principals). One measured
  defect caught by the composer's own validator on the first run
  (`KeyError: 'baton.claude-coder'` — the narrow principals document) and
  corrected the same way the verification composer had.
- Fresh Job `w202663-first-development-job-2`, Work `13c91b69-W2`, actors
  `baton.claude-coder-2` / `baton.claude-reviewer-2`, SAME frozen task
  content (corrected argv), SAME candidate image `448c98c9…`, SAME accepted
  base `446fa8f7…`, composed and APPLIED beside the preserved Job:
  4 workers, 2 bindings, ONE shared store, job input identity
  `sha256:28e095f0…`, submission document names job-2 only.
- Policy pin GATE: 26 → 38 predicted and equal (6 per job × 2 jobs — the
  ported arithmetic's first live check).
- Pool membership changed → the next activation mints pool generation 2
  (predicted from the durable pool; activation itself checks it at start).

## The owner's commands, in order

1. **Credential mapping** (REVIEW226502 [R1] FORM. Resolves
   `w202663-development` to the SAME file the existing `w64268-run1`
   entry names; prints no secret and reads none. It REFUSES a conflicting
   or ambiguous destination — an existing `w202663-development` entry
   no-ops ONLY when it already carries exactly the owner-selected mapping
   (provider `operator-file`, the `w64268-run1` entry's own path);
   anything else stops the sequence. The replacement registry is created
   EXCLUSIVELY (`O_CREAT|O_EXCL`, mode 0600, unpredictable name), so no
   pre-existing or attacker-placed file is truncated or followed. Exit
   status is the gate: 0 = mapped or already exactly mapped, nonzero =
   refused, and the fail-closed shell below stops on it):

       set -euo pipefail
       python3 - <<'PY'
       import json, os, secrets, sys

       place = "/home/sl/.baton/credential-sources.json"
       held = json.load(open(place))
       sources = held["sources"]
       origin = [one for one in sources
                 if one.get("provider") == "operator-file"
                 and one.get("reference") == "w64268-run1"]
       if len(origin) != 1:
           sys.exit(f"refused: expected exactly one operator-file/"
                    f"w64268-run1 entry, found {len(origin)}; select the "
                    f"source mapping yourself before rerunning")
       wanted = {"path": origin[0]["path"], "provider": "operator-file",
                 "reference": "w202663-development"}
       standing = [one for one in sources
                   if one.get("reference") == "w202663-development"]
       if standing:
           if len(standing) == 1 and standing[0] == wanted:
               print("w202663-development already carries exactly the "
                     "selected mapping; nothing changed")
               sys.exit(0)
           sys.exit("refused: w202663-development already exists with a "
                    "DIFFERENT provider/path (or more than once); resolve "
                    "that conflict yourself -- this command overwrites "
                    "nothing")
       sources.append(wanted)
       fresh = f"{place}.{secrets.token_hex(8)}.new"
       descriptor = os.open(fresh,
                            os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
       try:
           with os.fdopen(descriptor, "w") as out:
               json.dump(held, out, indent=1, sort_keys=True)
               out.write("\n")
           os.replace(fresh, place)
       except BaseException:
           os.unlink(fresh)
           raise
       print("mapped w202663-development -> the w64268-run1 file")
       PY

   (Two entries naming one file under DIFFERENT references is fine; the
   registry defect the resolver refuses is two entries for one
   (provider, reference) pair. The default provider model is untouched.
   This command's three behaviours — append, exact-match no-op, conflict
   refusal — are demonstrated on TEMPORARY metadata fixtures in
   `registry-command-fixture-226516.json`; no real registry or credential
   was read by that demonstration.)

2. **Restart to activate the two-Job pool** (fail-closed: `set -e` stops
   the sequence at the first refusal; activation mints pool generation 2
   and refuses if the prediction is wrong — nothing else is touched):

       set -euo pipefail
       DEST=/home/sl/baton-v12/instance-2026-09-21T01-28-41Z
       just --justfile "$DEST/justfile" stop
       just --justfile "$DEST/justfile" start

3. **Submit the fresh Job** (job-2 only; the preserved Job is not
   resubmitted; absolute store path, same fail-closed shell):

       set -euo pipefail
       cd /home/sl/src/baton/v12/python
       PYTHONPATH=src:. python3 -m tools.job_manager \
         --store /home/sl/baton-v12/instance-2026-09-21T01-28-41Z/db/jobs.sqlite3 \
         --incarnation w202663-claude-job2-submit \
         --authority-uuid 13c91b695bfe4625b4f22dabd35a54a4 \
         submit --document /home/sl/src/baton/work/records/2026/09/finding-v12-initial-claude-worker-pool/pool-submission.json

4. Signal me; I observe to terminal report-and-hold and extract candidate,
   verification, verdict and retained-log evidence through the supported
   readers.

## Limits (unchanged)

One producer episode + one reviewer episode for job-2; `provider_turn`
3600 s per provider invocation; `ordinary_verification` 900 s per
verification run; report-and-hold; no automatic recovery. The preserved
failed Job consumes nothing.
