# Recovery package — Job2's faulted episode, prepared deterministically (claim227097)

Per owner 227095, from review-2026-09-21T04-50-00Z.md. NOTHING LIVE RAN this
claim: no provider episode, no restart, no resubmission, no cleanup, no
credential act, no instance mutation, no Git mutation, no broad sweep. The
decision is pinned in FINDING/PLAN (entries dated 2026-09-21T05:06Z) BEFORE
any of the work below. Job1, Job2, the two retained unreviewed source files,
every log/sidecar byte and the accepted A/B evidence are preserved exactly
as found.

## The four questions, answered

### 1. Process reaping — corrected in the image's own entry, proven at PID 1

Job2's mechanism: PID 1 is `python3 /opt/baton/dogfood_entry.py` and never
called `wait`; the producer's killed background full-suite run reparented
its orphans there (~498 producer-reported zombies against the composed
`--pids-limit 512`, Docker-confirmed `Init=null`), and later forks failed.

`dogfood_entry.py` is now a minimal PID-1 supervisor: it forks the
UNCHANGED `baton_worker.main(agent=ClaudeAgent())` one process down,
forwards SIGTERM/SIGINT (the manager's stop contract — signal PID 1 — is
unchanged, and PID 1 is still Python), reaps every child the kernel hands
it, drains already-reparented zombies at the end, and exits with the
worker's own ending (128+N for a signal death). Raising the PID cap was NOT
selected: the review says that postpones exhaustion and is not reaping.
Image-side, so NO host runtime change and NO reinstall is required.

Proof, deterministic: `tests/manager/test_dogfood_entry.py` (6 tests — the
orphan-reap topology under a PR_SET_CHILD_SUBREAPER helper, status carry,
signal forwarding), and IN THE BUILT IMAGE as real PID 1 under
`--pids-limit 512 --read-only --network none --user 65532:65532`: an orphan
reparents to PID 1 while the worker still runs, and after `supervised()`
returns no child remains at all (RECOVERY-IMAGE-227097.json).

### 2. Nested capture isolation — the room is an explicit delivery now

`claude_agent._log_room()` used to open the fixed `/run/baton/logs` for ANY
importer; nested adapter code run by the provider's own shell reached the
real attempt room and its killed writers declared `failed` into the real
sidecars. The room is now opened ONLY when `BATON_ATTEMPT_LOG_ROOM` names
it. `dogfood_entry` sets that in the worker's own process; the adapter's
`_closed_environment` composes both children's environments member by
member and never forwards it, so nothing the provider starts — and nothing
a nested test constructs — holds a room. No sidecar byte was reset; the
retained Job2 sidecars stand as found.

Proof: no-marker → `(None, None)` even with a real room present (unit test
AND in-image probe with a room mounted at `/run/baton/logs`); marker → that
exact room; the composed child environments are exactly
{HOME, PATH, PYTHONPYCACHEPREFIX, TMPDIR, XDG_CACHE_HOME} with the marker
provably absent while the parent's environment carries it.

**Stated residual, exactly:** nested runs import the CANDIDATE's own
modules, and the candidate at the accepted base still carries the ungated
`_log_room` (and `baton_worker._WorkerCapture` opens `TARGET` by default in
the reference worker, which this Work does not own). A same-uid writer
inside the container can still reach the writable room mount by absolute
path — no image-side change can revoke a bind mount under `--cap-drop ALL`.
What this claim removes is the measured accidental path (image-sourced
adapters and the fork-exhaustion cascade that turned contamination into a
fault); the task instruction now also forbids background/full-suite runs
(a pilot constraint, per the review NOT counted as isolation). The COMPLETE
fix — an unpredictable or per-attempt container-side room target — is
manager product surface for separate owner selection.

### 3. Exact frozen verifier environment — measured, corrected, demonstrated

Measured at the accepted base 446fa8f7 (VERIFIER-ENV-DEMO-227097.json):
`test_bootstrap` is 125 tests and divides in two. Three stack classes take
any WRITABLE root through `BATON_V12_STACK_TEST_ROOT` (default `/var/tmp`,
read-only in the container; peak use ~1 MiB). Eleven `ValidFixture`-derived
classes (75 tests) demand — through `_disk_root_outside_the_checkout`,
which REFUSES rather than skips — a root at once disk-backed, writable and
OUTSIDE the checkout. The container has no such place BY CONTRACT: the
rootfs is read-only, `/tmp` and `/dev/shm` are memory, and the one writable
disk mount, `/output`, IS the git-line checkout. The only in-container
paths that could satisfy them are manager-owned delivery mounts (the
log/exchange rooms) — using one is exactly the contamination class this
recovery removes, and is the plausible explanation of the producer's manual
"160 OK" that review226905 already declined to credit.

The corrected frozen argv (compose-pool-207219.py, the task's own bytes):
establishes the fixture root itself before any test runs — an explicitly
exported operator selection is never overridden; otherwise
`realpath(mkdtemp)` under the invocation's own TMPDIR (in-container: the
held verification ephemera object, writable, outside the candidate;
realpath because `/proc/self/fd` spellings are process-local and the stack
cases hand the root to children) — runs `tests.tools.test_pool` plus
`test_bootstrap` with the eleven impossible classes EXCLUDED BY NAME and
the reason frozen in the argv, and floors the count at 51 so the exclusion
can never silently widen. The full family still gates every host rerun,
which `_verify`'s acceptance already names as the only run an operator
trusts. The complete in-container fix — a dedicated writable disk-backed
fixture delivery mount — is manager product surface for separate owner
selection.

Proof, through the adapter's OWN code path (`_closed_environment` →
`_pinned_environment` → the real `_verify`, real subprocess, real bound)
over a `git archive` candidate at the accepted base plus the
claim225590-precedent labeled discovery fixture: variable UNSET → the argv
makes exactly one root under the held TMPDIR and exits 0 (51 tests);
variable EXPORTED → respected, no argv-made root, exit 0. Partition
measured 125/75/11 (`acceptable: true` in the evidence file).

### 4. Job2 disposition and pool revalidation — from the product's closed sets

Job2's exact state (unchanged, canonical per review226905): implementation
exceptional, exchange faulted `agent`, episode LIVE (ended_state null),
allocation RESERVED on `baton.claude-coder-2`, review blocked, runtime
exited, the two unreviewed files durable in the retained line.

Established from source and proven by 4 new composed tests
(`tests/job_manager/test_scheduling.AFreshJobComposesBesideAReservedAllocation`):

- `activate_pool` with the widened document is a NEW generation and the
  reserved row stays bound to its old one — untouched, unrepaired.
- `scheduler._required_workers` still names the reserved worker FROM ITS
  OWN immutable generation — so the deployment must keep Job2's workers,
  which the composer's add-beside cadence does.
- A fresh stage under fresh identities reserves on the fresh worker:
  `reserve` excludes exactly the occupied worker ids AND canonical
  principals. The refusal half is proven too: a successor sharing the
  reserved principal refuses by name.

Disposition options for the reserved row, for the OWNER's decision:

- **(a) Preserve as live evidence (recommended).** Costs one worker/one
  principal of logical capacity and nothing else; ordinary ticks neither
  retry nor touch a faulted, unended episode. This is the accepted
  fresh-Job cadence, now deterministically revalidated against RESERVED
  (Job1's precedent only covered RELEASED).
- **(b) W128698 exclusion recovery of Job2 itself** (`episodes.
  restart_abandoned_correction`) EXISTS and now matches Job2's shape (its
  container ran) — but its preconditions are an operator abandonment
  declaration, a fence, a POSITIVELY DESTROYED runtime and a RESTORED
  checkout, i.e. cleanup acts the owner has excluded AND a checkout
  restore that would destroy the retained unreviewed source bytes the
  owner ordered preserved; and no packaged operator command exists for
  this pooled composition. Not recommended while the evidence must stand.

## The candidate image

`sha256:b44f55220e9f04ccde2485871aeb40f715db695b88567ead5fb63831374a2e3b`
(tag `w202663-recovery-227097`) — the unchanged `Dockerfile.claude` recipe
over the corrected `dogfood_entry.py`/`claude_agent.py`; in-image byte
identity, both in-image demonstrations and every gate in
RECOVERY-IMAGE-227097.json. The composer's `PROVIDER_IMAGE` now names it,
with the superseded 448c98c9 kept as history. A CANDIDATE until the owner's
launch authorization selects it. The host runtime, the installed instance
and its stores are untouched this claim.

## The owner's commands — AFTER independent review and your execution decision

All on the preserved instance `/home/sl/baton-v12/instance-2026-09-21T01-28-41Z`
(identity unchanged; no reinstall). Job1 and Job2 stay preserved; job-3 is a
FRESH Job (coder-3/reviewer-3, fresh Work, corrected task bytes, corrected
image). Each block is fail-closed.

1. **Compose and apply job-3 beside the preserved Jobs** (the composer's own
   gates check the pin arithmetic and predict the next pool generation; a
   wrong prediction refuses):

       set -euo pipefail
       cd /home/sl/src/baton
       python3 work/records/2026/09/finding-v12-initial-claude-worker-pool/compose-pool-207219.py \
         --instance /home/sl/baton-v12/instance-2026-09-21T01-28-41Z \
         --pr --base 446fa8f79d9569799a77e888e8236070e1dc78f7 \
         --job w202663-first-development-job-3

2. **Restart to activate the widened pool** (activation mints the next
   generation; the reserved allocation stays bound to its own row — proven
   above):

       set -euo pipefail
       DEST=/home/sl/baton-v12/instance-2026-09-21T01-28-41Z
       just --justfile "$DEST/justfile" stop
       just --justfile "$DEST/justfile" start

3. **Submit job-3 only** (the submission document the composer writes names
   the fresh Job only; nothing resubmits Job1 or Job2):

       set -euo pipefail
       cd /home/sl/src/baton/v12/python
       PYTHONPATH=src:. python3 -m tools.job_manager \
         --store /home/sl/baton-v12/instance-2026-09-21T01-28-41Z/db/jobs.sqlite3 \
         --incarnation w202663-claude-job3-submit \
         --authority-uuid 13c91b695bfe4625b4f22dabd35a54a4 \
         submit --document /home/sl/src/baton/work/records/2026/09/finding-v12-initial-claude-worker-pool/pool-submission.json

4. Signal the implementer; observation to terminal report-and-hold and
   evidence extraction run through supported readers only.

## Limits (unchanged)

One producer episode + one reviewer episode for job-3; `provider_turn`
3600 s; `ordinary_verification` 900 s; report-and-hold; default model; no
automatic recovery; deadline 2026-09-21T09:32:05Z. The preserved Jobs
consume nothing.
