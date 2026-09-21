# Job-4 recovery — composed beside preserved job-3, gated on a FRESH credential (claim227726)

Per owner 2026-09-21T06:40:26Z ("I relogged" / "do it") after
review-2026-09-21T06-37-00Z.md. Prepared THIS claim: the job-4 composition
only. NO apply, no restart, no submission, no live call, no credential
read or mutation, no cleanup. Job-3, its reserved allocation, both older
failed Jobs and all evidence stay preserved exactly as found.

## The measured blocker this package gates on

The registry maps both `w64268-run1` and `w202663-development` to the
operator file `/home/sl/.claude/.credentials.json` (baton.prompt's
read-only metadata inspection, FINDING 06:40:26Z). **That file's mtime is
2026-09-17 09:29:42 -0600 and NOTHING under `~/.claude` or
`~/.config/claude*` changed after job-3's 06:30:25Z failure** (measured
by metadata only at 06:42Z; no contents were read). Whatever the reported
relogin refreshed, it was not the file the workers mount — so submitting
job-4 now would deterministically repeat job-3's
"OAuth session expired and could not be refreshed".

A consistent mechanism, offered as hypothesis and NOT as a proved cause
(review227682: exact expiry timing/cause unproved): the file is from
09-17; Job2's 03:59Z episode authenticated by REFRESHING in-memory, and
OAuth refresh tokens rotate on use — the container cannot write the
rotated token back through a read-only mount, so the mounted file's
refresh token was consumed and job-3's refresh failed. If that is right,
each manual re-export supports the FIRST subsequent real episode
reliably, and persisting refreshed credentials between episodes is
product surface for a separate owner decision.

## What was composed and checked this claim (deterministic, read-only otherwise)

- Current state read through supported read-only surfaces: canonical
  snapshot (job-3 implementation exceptional / review blocked), pool
  generation 1 holding exactly job-3's two workers, ONE live allocation
  (job-3 implementation, reserved), manager RUNNING (pid 2890422).
- `compose-pool-207219.py --instance <dest> --pr --base 446fa8f7…
  --job w202663-first-development-job-4 --work 2` completed with ZERO
  refusals: fresh identities `baton.claude-coder-4`/`baton.claude-reviewer-4`,
  fresh Work `baf2e7fe-W2` (job-3 keeps W1), job input identity
  `sha256:fd273ef0…`, same frozen task semantics and the accepted image
  `d1e2869e…` verified inside the composed worker deployments.
- `pool-submission.json` names job-4 ONLY; `pool-bootstrap-inputs.json`
  carries both jobs' workers (job-3's travel unchanged — the manager
  requires the reserved worker's context, proven in round 1's scheduler
  tests, which also prove the widened pool activates as generation 2
  with the reserved row untouched and job-4 reserving on coder-4).

## The owner's commands — after independent review

`DOSSIER=/home/sl/src/baton/work/records/2026/09/finding-v12-initial-claude-worker-pool`,
`DEST=/home/sl/baton-v12/instance-2026-09-21T06-27-56Z`. Fail-closed:
every block stops at the first refusal.

1. **Credential freshness gate** (metadata only; prints no secret and
   reads no contents). It refuses while the mapped file predates job-3's
   failure — if it refuses, re-authenticate the `claude` CLI **on this
   host** the way the file was originally provisioned (so
   `~/.claude/.credentials.json` itself is rewritten), or re-export the
   fresh credential over the mapped path, then re-run this gate.
   Freshness is NECESSARY, not sufficient — only the live episode proves
   authentication:

       set -euo pipefail
       python3 - <<'PY'
       import json, os, sys
       held = json.load(open("/home/sl/.baton/credential-sources.json"))
       found = [one for one in held["sources"]
                if one.get("reference") == "w202663-development"]
       if len(found) != 1:
           sys.exit("refused: expected exactly one w202663-development "
                    "registry entry")
       place = found[0]["path"]
       modified = os.stat(place).st_mtime
       # job-3's provider failed at 2026-09-21T06:30:25Z = 1789972225 UTC
       if modified <= 1789972225:
           import time
           sys.exit(f"refused: {place} was last modified "
                    f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(modified))}, "
                    f"BEFORE job-3's authentication failure; the reported "
                    f"relogin did not reach this file. Re-authenticate the "
                    f"claude CLI on this host (or re-export the fresh "
                    f"credential over this exact path) and re-run this gate.")
       print("the mapped credential file is newer than the job-3 failure")
       PY

2. **Apply and gate the pin** (the supported apply; the pin gate exits
   nonzero and stops the sequence before any restart):

       set -euo pipefail
       DOSSIER=/home/sl/src/baton/work/records/2026/09/finding-v12-initial-claude-worker-pool
       DEST=/home/sl/baton-v12/instance-2026-09-21T06-27-56Z
       cd /home/sl/src/baton/v12/python
       PYTHONPATH=src:. python3 -m tools.bootstrap \
         --inputs "$DOSSIER/pool-bootstrap-inputs.json"
       "$DOSSIER/check-policy-pin.sh" "$DEST" pool

3. **Restart to activate the widened pool** (activation mints
   generation 2; the reserved job-3 row stays bound to generation 1 —
   proven) **and submit job-4 only**:

       set -euo pipefail
       DOSSIER=/home/sl/src/baton/work/records/2026/09/finding-v12-initial-claude-worker-pool
       DEST=/home/sl/baton-v12/instance-2026-09-21T06-27-56Z
       just --justfile "$DEST/justfile" stop
       just --justfile "$DEST/justfile" start
       cd /home/sl/src/baton/v12/python
       PYTHONPATH=src:. python3 -m tools.job_manager \
         --store "$DEST/db/jobs.sqlite3" \
         --incarnation w202663-claude-job4-submit \
         --authority-uuid baf2e7fe4ec04612aa9d28805cafea78 \
         submit --document "$DOSSIER/pool-submission.json"

4. Signal the implementer; observation to terminal report-and-hold and
   evidence extraction run through supported readers only.

## Limits (unchanged)

One producer + one reviewer episode for job-4; provider_turn 3600 s;
ordinary_verification 900 s; report-and-hold; default model; no automatic
recovery; the old-source log-isolation limitation review227560 recorded
stands. Job-3's reserved attempt is preserved evidence and consumes
nothing.
