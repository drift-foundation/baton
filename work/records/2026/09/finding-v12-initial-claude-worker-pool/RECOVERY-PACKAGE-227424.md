# Recovery package, round 2 — the three owner-selected corrections, complete (claim227424)

Per owner 2026-09-21T05:53:07Z / 05:54:40Z / 05:56:02Z, answering
review-2026-09-21T05-43-00Z.md's R1–R3. NOTHING LIVE RAN this claim: no
provider episode, no install, no apply, no start, no submission, no cleanup,
no credential read, no Git mutation. Both failed Jobs, the retained
unreviewed bytes, all sidecars and the accepted A/B evidence are preserved
exactly as found. Scope was pinned in PLAN (2026-09-21T06:05Z) before any
edit. Evidence: RECOVERY-EVIDENCE-227424.json.

## R2 — the scratch mount, and the FULL real tests pass in-container

The owner-approved per-attempt disk-backed scratch is a real delivery now:
`workspaces.HOME_ENTRIES` provisions a `scratch` directory with every
assignment home (the home closes right after provisioning, which is why a
post-hoc mkdir was measured refusing), `single_worker` adopts it on the
START path and hands it to the adapter, and `oci` composes exactly one
writable bind at the constant `/scratch` (`_scratch_mount`, execution-only
at both the adapter and the vector, absent by default, collision-checked
both directions). The frozen argv selects `/scratch` when present — an
explicitly exported `BATON_V12_STACK_TEST_ROOT` still wins, and a host
rerun without `/scratch` falls back to a real temporary directory — and
runs the FULL `tests.tools.test_pool` + `tests.tools.test_bootstrap`.
Claim227097's exclusion remedy is superseded and gone; no stub, no
excluded class, no count games.

**The proof review227324 asked for:** in a container from the rebuilt
image, mirroring the composed restrictions, over the accepted base PLUS
the ACTUAL RETAINED `pool.py`/`test_pool.py` (hash-verified against
REVIEW-EVIDENCE-226905.json; `AdmissionCase → ValidFixture` and all), with
`/scratch` bound to real disk and the variable unset: the EXACT frozen
argv ran **160 tests, OK, exit 0** — the same family that measured 75
failures without a compliant root. This demonstrates the retained bytes
VERIFY under the corrected topology; it is not an acceptance and no
retained byte moved.

## R3 — disposable nested-test logs, covering old bytes too

The authoritative room MOVED: `attempt_log_format.TARGET` is
`/run/baton/attempt-logs` now, and `attempt_logs.LOG_TARGET` (the
manager's mount target) and the image entry's marker both derive from it,
so mount and writer cannot disagree. The LEGACY `/run/baton/logs` — the
spelling every accepted image and the retained candidate still carry — is
composed as a small disposable tmpfs in the UNCONDITIONAL restrictions:
any old-byte writer gets its own memory-backed log location that dies with
the container. That covers the candidate-source adapter AND the
reference-worker `_WorkerCapture` without editing the reference worker,
because `_WorkerCapture` reads its target from the shared module it
travels with.

**Demonstrated with the measured nested path itself:** the accepted
base's own `attempt_log_format`/`claude_agent`/`baton_worker` bytes,
imported first exactly as nested checkout tests import them, wrote a
declared-failed verification capture and a teed worker stream — all four
files landed in the decoy; the real room's pre-seeded
`verification.stdout.log` and its `finished` sidecar were byte-identical
after (sha256-checked). No retained Job2 evidence was touched or reset.

## R1 — the complete fail-closed command sequence

The manager changed, so the frozen installed runtime cannot compose the
new mounts: the sequence starts from the owner's own established
fenced-install cadence. Built and recorded THIS claim (nothing installed):
runtime executable `sha256:c45ff6d9…`, bundle `sha256:8616ab85…`/81 files
(PROSPECTIVE-INPUTS-227424.json taken before the build;
RUNTIME-BUILD-227424.json; BUNDLE-MANIFEST-227424.json;
`install-next-instance.sh` now fenced on exactly these records — its
BEFORE gate was re-run against them and passes). Candidate provider image
`sha256:d1e2869e…` (RECOVERY-EVIDENCE-227424.json), pinned in the
composer. The current instance and both failed Jobs stay preserved; job-3
runs on a FRESH instance under fresh identities.

Each block is `set -e` fail-closed; a refusal anywhere stops everything
after it. `DOSSIER=/home/sl/src/baton/work/records/2026/09/finding-v12-initial-claude-worker-pool`.

1. **Install the fresh instance** (fenced on the recorded artefact; never
   rebuilds, never replaces; retains the destination in
   `selected-instance.txt`):

       set -euo pipefail
       cd /home/sl/src/baton/work/records/2026/09/finding-v12-initial-claude-worker-pool
       ./install-next-instance.sh

2. **Compose job-3, APPLY it, and gate the pin** — the supported apply is
   `tools.bootstrap`, exactly as review227324 R1 required, and
   `check-policy-pin.sh <dest> pool` exits nonzero and stops the sequence
   BEFORE any start if the installed policy generation does not equal the
   composer's prediction. The credential preflight refuses before apply if
   the registry no longer carries exactly one `w202663-development` entry
   (it reads no secret):

       set -euo pipefail
       DOSSIER=/home/sl/src/baton/work/records/2026/09/finding-v12-initial-claude-worker-pool
       DEST="$(cat "$DOSSIER/selected-instance.txt")"
       python3 - <<'PY'
       import json, sys
       held = json.load(open("/home/sl/.baton/credential-sources.json"))
       found = [one for one in held["sources"]
                if one.get("reference") == "w202663-development"]
       sys.exit(0 if len(found) == 1 else
                "refused: the registry does not carry exactly one "
                "w202663-development entry; re-run the accepted mapping "
                "command from RECOVERY-PATH-226458.md step 1")
       PY
       cd /home/sl/src/baton/v12/python
       PYTHONPATH=src:. python3 "$DOSSIER/compose-pool-207219.py" \
         --instance "$DEST" --pr \
         --base 446fa8f79d9569799a77e888e8236070e1dc78f7 \
         --job w202663-first-development-job-3 --work 1
       PYTHONPATH=src:. python3 -m tools.bootstrap \
         --inputs "$DOSSIER/pool-bootstrap-inputs.json"
       "$DOSSIER/check-policy-pin.sh" "$DEST" pool

   (`--job …-job-3` names the fresh participants `baton.claude-coder-3` /
   `baton.claude-reviewer-3`; `--work 1` selects the fresh Authority's
   first Work, since Job1/Job2's Works live on the preserved old
   instance.)

3. **Start and submit job-3 only** (reached only if every gate above
   passed):

       set -euo pipefail
       DOSSIER=/home/sl/src/baton/work/records/2026/09/finding-v12-initial-claude-worker-pool
       DEST="$(cat "$DOSSIER/selected-instance.txt")"
       just --justfile "$DEST/justfile" start
       UUID="$(python3 -c "import json;print(json.load(open('$DEST/authority-identity.json'))['authority_uuid'])")"
       cd /home/sl/src/baton/v12/python
       PYTHONPATH=src:. python3 -m tools.job_manager \
         --store "$DEST/db/jobs.sqlite3" \
         --incarnation w202663-claude-job3-submit \
         --authority-uuid "$UUID" \
         submit --document "$DOSSIER/pool-submission.json"

4. Signal the implementer; observation to terminal report-and-hold and
   evidence extraction run through supported readers only.

## What round 1 contributes unchanged

The PID-1 reaping supervisor and the image adapter's explicit-room marker
(review227324 independently verified 10/10), and the four composed
scheduler proofs that a fresh Job reserves beside Job2's untouched
RESERVED allocation. Job2's disposition recommendation stands: preserve as
live evidence; the W128698 exclusion path would destroy the retained
unreviewed bytes and is recorded, not recommended.

## Limits

One producer + one reviewer episode for job-3; provider_turn 3600 s;
ordinary_verification 900 s; report-and-hold; default model; no automatic
recovery. Owner 05:56:02 authorizes exactly this round; no deadline is
invented and none extended.
