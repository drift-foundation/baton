# Fresh attempt after the `quickstart-c` credential failure — owner commands

Prepared at claim358697 for `review-2026-10-23T05-27-08Z.md` under owner
reroute358671. **Nothing here was executed against the live instance except the
read-only check**, which is proved to leave every accountable byte identical.

The owner helper is `/tmp/w325959-fresh-attempt.py`; the durable canonical copy
is `fresh_attempt.py` beside this file and both are
sha256 `64d4442c445d85a8002f2d98e5069abf229e2f0204c27eb46e1638ba47aff621`.

```sh
BUILD=/home/sl/baton-builds/w325959-30245386-356981
SRC="$BUILD/src/v12/python"
PY="$BUILD/venv/bin/python"
H=/tmp/w325959-fresh-attempt.py
D=/home/sl/baton-instances/native-coordination-pilot-w321608-3
```

## What failed, and what this is not

`quickstart-c`'s implementation stage went `exceptional` on an **expired OAuth
credential** — `duration_api_ms 0`, `cost 0`, runtime destroyed, allocation
released, review `blocked`. That is a credential fault, not a product defect.

There is **no supported same-Job retry**, and this does not invent one.
`submission.submit` journals by submission identity, so an identical
resubmission is a **replay**; `submission._unclaimed` refuses an existing Job
claimed by another submission; and `episodes.restart_abandoned_correction`
requires abandonment, fence, restored-line and excluded-writer receipts that an
expired credential does not produce. So this prepares a **new Job on a new Work
in the same instance**, and `quickstart-c` is preserved as the record of the
failure.

## Selection 1 — check (read-only, writes nothing)

```sh
cd "$SRC" && PYTHONPATH=src:. "$PY" "$H"
```

This is a **rehearsal, not an opinion**: it copies the instance's metadata and
stores into a disposable directory and runs the **real** supported operation
there, then drives the product's own runtime selector over the result. The live
stores are never opened — opening sqlite writes `-wal` and `-shm` beside it, so
a check that promised unchanged bytes and then opened the authority would break
its own promise. It digests all 23 accountable entries before and after and
refuses if they differ.

Expected: `destination_unchanged: true`, `rehearsal.exit: 0`, and the selector
answering all four pairs.

## Selection 2 — apply the additive preparation in place

```sh
cd "$SRC" && PYTHONPATH=src:. "$PY" "$H" --owner-selected
```

Re-runs the whole check, then makes **one** supported call —
`bootstrap --inputs <composed>` with **no `--destination`** — which adds:

| | |
|---|---|
| Job | `quickstart-d` |
| Work | `5a8fa4b4-W2` |
| Task | `w321608-native-operator-quickstart-4` |
| Workers | `implementation-pilot-d`, `review-pilot-d` |

**Nothing existing changes.** `quickstart-c`'s binding and both its workers are
asserted byte-identical afterwards, which is what keeps the failed Job servable
and accountable rather than orphaned.

**Why new workers rather than re-pointing the existing two:** both shapes
configure, but the product's selector `_job_workers` compares *the Work* between
a worker's manifest and the Job's binding. Re-pointing would make
`quickstart-c`'s stages unservable. With new workers all four stage/Job pairs
select a worker.

**No new repository is needed** — the new workers reuse the existing
`source-implementation-pilot` and `source-review-pilot`, and the in-place
operation prepares no repositories, so nothing clones and no Git runs.

**Expected readbacks — stop on any mismatch:**
- `job_bindings`: two entries, `quickstart-c` on `5a8fa4b4-W1` **unchanged**, and `quickstart-d` on `5a8fa4b4-W2`
- `workers`: four, the two existing ones unchanged plus the two `-d` ones
- `selector`: all four pairs non-empty
- `preserved`: `binding_identical` and `existing_workers_identical` both true

A second apply **refuses** on the already-bound Job and leaves the instance
byte-unchanged. Do not re-run it to "fix" a mismatch — report the mismatch.

## Selection 3 — emit the submission (separate decision)

```sh
cd "$SRC" && PYTHONPATH=src:. "$PY" "$H" --emit-submission
```

Writes `$D/generated/submission-quickstart-d.json` only. It refuses if run
before selection 2, refuses to overwrite an existing one, and refuses if the
document still names the failed Job or its Work anywhere — including a stage
dependency. It passes the manager's own `documents.owned_submission` validator,
and the per-invocation **3600s provider / 900s verification** limits are
unchanged.

## Selection 4 — submit (separate decision)

```sh
C="$D/distro/baton-v12-stack"
A="5a8fa4b4275b4f7fa32efafc2c48f546"

"$C" manager \
    --store "$D/db/jobs.sqlite3" \
    --incarnation w325959-owner-submit-4 \
    --authority-uuid "$A" \
    submit --document "$D/generated/submission-quickstart-d.json"
```

## Selection 5 — serving (separate decision)

```sh
I="$D/instance.json"
"$C" status --instance "$I"
"$C" start  --instance "$I"      # live serving
```

After submit, `quickstart-d` should appear alongside the retained
`quickstart-c`, whose implementation stays `exceptional` and whose review stays
`blocked`.

## The credential prerequisite, stated plainly

The original failure was an expired OAuth credential. The owner reports the
selected source refreshed at `2026-10-23T05:22:04Z`, expiring `13:22:04Z`
(**metadata only** — no secret was read and refreshed authentication was not
independently proved here). **Nothing in this packet tests authentication**, and
a fresh attempt launched after that expiry would fail the same way. Confirm the
credential is valid at selection 4, not at authoring time.

## What is proved, and what is not

`evidence/PROVE.json` — **39 checks, zero failures**, in two scenarios: a
read-only rehearsal against the **real** failed instance using the helper's
shipped identities, and a disposable instance where apply, repeat-apply,
submission emission and every refusal are exercised.

**Not proved:** that the new Job will *succeed*. Only that it is configured,
bound, collision-free and selectable. The disposable scenario's retained Job was
configured but never ran, so the claim that the real failed Job's recorded
history is untouched rests on the live accountable digest over `db/` — which is
measurement of the actual instance, and it was identical before and after. No
submit, serve, start, provider, engine, model or credential read, and no Git.
