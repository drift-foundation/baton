# Job-5 — the explicit fail-closed sequence (claim230107, for owner execution after review)

Review230027 R2 asked for one concrete package with exact operands and no
placeholders or references to prior blocks. This is it, complete. Nothing
here ran this claim. Preconditions it assumes: independent review has
accepted the narrowed-collection candidate image
`sha256:5c2eb55d64a775cf939425941960289c3c98a49689f841a335bdf03f69afd5b6`
(the composer pins it), and the owner selects execution. The host runtime
is unchanged by D10, so there is no build and no install anywhere below.
Every block is `set -e` fail-closed: the first refusal stops everything
after it. Jobs 1–4 stay preserved; job-5 runs beside them under fresh
identities (`baton.claude-coder-5` / `baton.claude-reviewer-5`, Work
`baf2e7fe-W3`).

1. **Compose job-5 on the existing instance** (writes the job-5 documents
   and prepares its worker homes; the composer's own validators refuse on
   any mismatch, including the pinned image being absent from the local
   daemon):

       set -euo pipefail
       cd /home/sl/src/baton/v12/python
       PYTHONPATH=src:. python3 /home/sl/src/baton/work/records/2026/09/finding-v12-initial-claude-worker-pool/compose-pool-207219.py \
         --instance /home/sl/baton-v12/instance-2026-09-21T06-27-56Z \
         --pr \
         --base 446fa8f79d9569799a77e888e8236070e1dc78f7 \
         --job w202663-first-development-job-5 \
         --work 3

2. **Apply, and gate the pin before anything restarts** (the supported
   apply, then the measured equality gate, which exits nonzero and stops
   this block before the stop/start below can ever run):

       set -euo pipefail
       cd /home/sl/src/baton/v12/python
       PYTHONPATH=src:. python3 -m tools.bootstrap \
         --inputs /home/sl/src/baton/work/records/2026/09/finding-v12-initial-claude-worker-pool/pool-bootstrap-inputs.json
       /home/sl/src/baton/work/records/2026/09/finding-v12-initial-claude-worker-pool/check-policy-pin.sh \
         /home/sl/baton-v12/instance-2026-09-21T06-27-56Z pool

3. **Restart to activate the widened pool, then submit job-5 only**
   (activation mints the next pool generation; the reserved job-3 and
   job-4 rows stay bound to their own generations — the reviewed
   scheduler proofs cover exactly this; the submission document the
   composer wrote in step 1 names job-5 alone):

       set -euo pipefail
       just --justfile /home/sl/baton-v12/instance-2026-09-21T06-27-56Z/justfile stop
       just --justfile /home/sl/baton-v12/instance-2026-09-21T06-27-56Z/justfile start
       cd /home/sl/src/baton/v12/python
       PYTHONPATH=src:. python3 -m tools.job_manager \
         --store /home/sl/baton-v12/instance-2026-09-21T06-27-56Z/db/jobs.sqlite3 \
         --incarnation w202663-claude-job5-submit \
         --authority-uuid baf2e7fe4ec04612aa9d28805cafea78 \
         submit --document /home/sl/src/baton/work/records/2026/09/finding-v12-initial-claude-worker-pool/pool-submission.json

4. Signal the implementer. Observation to terminal report-and-hold and all
   evidence extraction run through supported readers only.

Limits, unchanged: one producer + one reviewer episode for job-5;
`provider_turn` 3600 s; `ordinary_verification` 900 s; report-and-hold;
default model; no automatic recovery. The credential authenticated live at
job-4; if job-5's provider nonetheless refuses authentication, that is a
prompt failure report, not a retry.
