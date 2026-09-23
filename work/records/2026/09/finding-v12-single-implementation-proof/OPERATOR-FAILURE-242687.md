# The bounded expired-credential failure-path command

Claim 242906, baton.claude, W239528. Prepared for independent review; **not
approved for execution by its existence**. Supersedes the claim-242687
revision, which review 2026-09-22T23:53:34Z refused on two counts.

**The credentials stay expired. That is the point of this command**, and it is
the owner's recorded decision: a deployment that only works when the token is
valid has not been shown to fail safely.

## What the previous revision got wrong

- **R1, and it would have run the wrong code.** That revision bound
  `/home/sl/baton-runs/managed-correction-236087/manager-source` as its import
  path. That snapshot was taken under W236087 and holds the **pre-correction**
  `review_driver.py` (`b5b22535…ebe10c`) and `stage_execution.py`
  (`33c78091…6e81`). The documented command would have imported the
  unconditional publication and the context-held ending — and reproduced the
  900-second stall it exists to disprove. The composer's digest binding was
  faithful; it bound the old bytes correctly.
- **R2, an operational finding.** It named
  `SELECTIONS-FAILURE-242687.json` and the dossier contained no such file, so
  the lower bounds and the new run and store operands were prose rather than a
  composed input anyone could review. It also said the first run's instance was
  reusable, which weakened the accepted isolation boundary: that boundary
  excluded stores containing **other work**, not only other *live* work, and
  the first run left an unfinished ending and cleanup behind.

Both are corrected below. The old snapshot is **preserved and not written to**
— W236087's own packet is bound to those bytes.

## Step 0 — prepare the successor manager-source snapshot

```sh
DOSSIER=/home/sl/src/baton/work/records/2026/09/finding-v12-single-implementation-proof
/home/sl/.local/state/baton-v12-venv/bin/python -B "$DOSSIER/snapshot_242687.py"
```

It copies `v12/python/src/baton_v12` → `baton_v12/` and `v12/python/tools` →
`tools/` into
`/home/sl/baton-runs/single-implementation-242687/manager-source`, flat, and
then **verifies** that the two corrected modules carry the independently
accepted digests and that the preserved snapshot still carries the superseded
ones. It refuses rather than writing a manifest if either check fails. It
opens no store, starts no container, changes no deployment and rebuilds no
image — both corrections are host-side manager modules, and the worker image
carries neither.

It writes `MANAGER-SOURCE-242687.json`, which manifests all 106 files and names
both snapshots.

    successor   /home/sl/baton-runs/single-implementation-242687/manager-source
                baton_v12/job_manager/review_driver.py
                    9a8a4a8193ff7b1c709c184dee3ba43a1b1e16e60891dcf31277279d2c220ae4
                tools/stage_execution.py
                    ebc9be29d2bd23cf129afe33943f5336832df2ef24256c724708004220032896
    preserved   /home/sl/baton-runs/managed-correction-236087/manager-source
                the pre-correction bytes; W236087's packet is bound to them

`test_successor_snapshot.py` checks all of this against the files on disk, and
runs a child process with the documented `PYTHONPATH` that reports which
`review_driver.py` it actually loaded and whether `PUBLISHABLE` is present — the
whole of R1 in one check. It keeps the reviewer's counterexample too: the same
child bound to the preserved snapshot answers `False`.

## The paths

```sh
PY=/home/sl/.local/state/baton-v12-venv/bin/python
BOUND=/home/sl/baton-runs/single-implementation-242687/manager-source
DOSSIER=/home/sl/src/baton/work/records/2026/09/finding-v12-single-implementation-proof
ROOT=/home/sl/baton-runs/single-implementation-242687
RUN="$ROOT/run"
SEL="$ROOT/selections.json"
```

`$BOUND` is the successor snapshot from step 0, and it is flat, which is why
one `PYTHONPATH` entry is the whole import path.

## Preconditions

1. **A NEW `run_id`, hence a new Job identity.** The
   `single-implementation-239528` grant was CONSUMED by the run that failed —
   consumption commits inside the opening admission, so a failed turn still
   spends it. The selections name `single-implementation-242687`, from which
   the composer derives `job-single-implementation-242687`.

2. **GENUINELY FRESH, DEDICATED stores. The first run's instance is NOT
   reusable.** The accepted isolation boundary excludes stores containing other
   work, and
   `/home/sl/baton-runs/single-implementation-239528/db/` now holds a Job whose
   ending and cleanup are **unfinished** — that is preserved failure evidence,
   not an empty instance. Admission filtering scopes new stages to this Job; it
   does not isolate store-wide recovery and endings. Bootstrap a fresh instance
   rooted at `/home/sl/baton-runs/single-implementation-242687/` with its own
   Authority, Job, control and integration stores. The selections are already
   filled in for exactly those paths.

3. **Step 5a Authority preparation on the new instance**, as
   `OPERATOR-239528.md` documents it. `baseline_bindings.preflight` names what
   is missing; re-read its stated limits there — it cannot verify route
   handlers at all.

4. **Do not renew the credentials.** If they are renewed the run answers a
   different question and the answer to this one is lost.

5. **Preserve the earlier evidence.**
   `/home/sl/baton-runs/single-implementation-239528/` and
   `/home/sl/baton-runs/managed-correction-236087/` are records. Do not reuse,
   clean up or recover either.

## Step 1 — the selections

```sh
mkdir -p "$ROOT"
cp "$DOSSIER/SELECTIONS-FAILURE-242687.json" "$SEL"
```

That file exists in the dossier and is the reviewable composed input R2 asked
for. Fill the members marked `<OWNER>`: the fresh Authority uuid from
precondition 2, the participants and principals from step 5a, the fixture
repository and its `harness.py` digest, the credential profile — **the same
expired one** — the bounded egress network, the retention policy digest and the
accepted evidence digest.

Everything else is already bound: the successor snapshot, the code boundary,
the image and adapter digests, the installed runtime, the vectors, the run
identity, and the bounds.

**The bounds are in the file, not in this prose**:

    turn_seconds 180   total_seconds 120   cleanup_seconds 30
    implementer_invocations 1   retry false

120 and 30 are owner reroute 242903's. A failure path has no reason to reserve
fifteen minutes: if the correction holds the run ends in seconds, and if it
does not you know in two minutes rather than fifteen. `held_packet` refuses a
cleanup bound that is not beside the overall one. `turn_seconds` stays 180 and
is never reached — the provider fails in milliseconds — but a packet that
declares a ceiling it does not carry is not a packet.

## Step 2 — the fixture repository

As `OPERATOR-239528.md` step 2: `harness.py` printing `before` and `TASK.md`,
committed, with that commit as the Authority's canonical target. Record the
HEAD and the `harness.py` digest in the selections. No acceptance or
review-feedback document.

## Step 3 — compose

```sh
PYTHONPATH="$BOUND" "$PY" -B "$DOSSIER/baseline_bindings.py" \
    --selections "$SEL" \
    --base "$BASE" \
    --run-root "$RUN"
```

It prints the digest of every document it writes, holds the deployment against
`stage_execution.held_configuration`, opens no store and starts nothing.

Read `PACKET.json` before going on:

- `manager_source.path` must be `$BOUND`, and
  `manager_source.files["baton_v12/job_manager/review_driver.py"]` must be
  `9a8a4a81…20ae4`. **If it is `b5b22535…ebe10c` you are composing against the
  preserved snapshot and the run will reproduce the stall.**
- `bounds.total_seconds` 120, `bounds.cleanup_seconds` 30.
- `submission.job_id` `job-single-implementation-242687`.

## Step 4 — run

```sh
PYTHONPATH="$BOUND" "$PY" -B "$DOSSIER/baseline.py" \
    --packet "$RUN/PACKET.json" \
    --incarnation single-implementation-242687
```

`verify_imported_sources` refuses before any store opens unless the packages
this process really imports resolve inside `$BOUND` — so a mismatched
`PYTHONPATH` is exit 2 rather than a wrong run. `survey` then refuses, also
before any owner act, if the Job identity is already recorded.

## What a corrected run looks like

    stopped              exceptional        (NOT overall-bound-exceeded)
    stage_states         implementation exceptional
    served_seconds       seconds, far inside 120
    outstanding_cleanup  []
    cleanup              retained or complete, state absent
    state                held
    workload.dispositions  [{... "disposition": "unable"}]
    workload.proposals     []
    held_because         names 'unable' and points at the provider log

`state: held` is the CORRECT answer and is not a failure of the packet. The run
established that the deployment fails safely; it established no implementation,
because there was none. Exit status 1.

## What would be a new finding

* `stopped: overall-bound-exceeded`, or `stage_states: answering` — the
  correction did not hold on the real path. **Check `manager_source` in the
  packet first**: binding the preserved snapshot produces exactly this.
* `outstanding_cleanup` non-empty — a container left standing.
* Any proposal, attribution or `completed` disposition — the condition was not
  reproduced, most likely because the token was renewed.
* `held_because` containing `KeyError` — the actionable reporting did not reach
  this path.

Record whichever happened; do not re-run to get a different answer. A second
run needs a new run identity and a new selection.

## What this command does NOT authorize

Credential renewal. Any retry. Reuse of, or recovery on, the first W239528 run's
stores or runtime, or W236087's. Overwriting the preserved manager-source
snapshot. Any reviewer stage or session resume. Any Work closure. Production
enabling of anything.
