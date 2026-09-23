# The successor baseline packet — and the blocker it does NOT clear

Claim 243284, baton.claude, W239528. Prepared for independent review; **not
approved for execution by its existence**.

## Read this first: this packet is NOT successful-baseline ready

Owner reroute 243281: *"Do not present a packet as successful-baseline ready
while that blocker remains."*

**The custody-mode failure is unresolved.** The successful run of
2026-09-22 produced everything it was asked for — a real provider that edited
without committing, an adapter-attributed proposal on the declared base, a
destroyed runtime and positive cleanup — and its stage still could not settle,
because `context_delivery._private` refuses any custody directory carrying
group or other bits and the real CLI creates seven of them at `0o755` under the
ordinary process umask. See the claim-243174 FINDING entry and
`live-success-243174/`.

Running this packet today will reproduce that. What it will do **differently**
is say so in about six seconds instead of spending its bound, and tell you where
the outcome is. That is a real improvement and it is not an end-to-end
implementation proof.

**So this command is for observing the blocker under the corrections, not for
demonstrating a successful baseline.** A successful baseline needs the custody
decision first, and that decision is the next selection:

> whether the manager should tolerate a umask-created directory inside the
> private context home, or the delivery should impose the mode on the tree it
> hands the container.

That is a product decision with its own security reasoning and its own review.
This claim diagnosed it and deliberately did not decide it.

## What changed, and against what

**`OPERATOR-FAILURE-242687.md` was ACCEPTED and already carries the corrected
inputs.** It binds the successor snapshot and 120/30 bounds. The
pre-correction snapshot and the 900-second bound belong to the revision BEFORE
it, which review 2026-09-22T23:53:34Z refused. An earlier draft of this table
attributed those rejected inputs to the accepted packet; that was wrong and is
corrected here.

Against the ACCEPTED failure packet, this successor differs in two things:

| | accepted failure packet | this successor |
| --- | --- | --- |
| `total_seconds` / `cleanup_seconds` | 120 / 30, sized for a path that fails in milliseconds | **300 / 60**, sized for a full-length provider turn |
| what it expects to reach | the `unable` ending | the custody blocker, reported promptly |

Both bind the same verified successor snapshot and the same fresh-store rule.

Against the revision that was REFUSED:

| | refused draft | since |
| --- | --- | --- |
| bound source | the W236087 snapshot, holding **pre-correction** bytes | the successor snapshot, verified |
| `total_seconds` | 900 | 120 accepted for failure; **300** here |
| a run that stops moving | spends the bound | stops in `STALLED_TICKS` = 6 ticks |
| Ctrl-C | uncaught traceback | the outcome's path, printed; exit 130 |
| snapshot builder | deleted its destination | refuses a tree **and** a manifest, and demands `--claim` for a successor |

### Why 300 seconds

It has to cover one provider turn at its own declared ceiling
(`turn_seconds` = 180) plus the launch, the exchange, the ending's nine
journalled steps and the publication. It no longer has to cover a run that has
stopped moving, because that is detected in six seconds. Measured against the
two real runs: the expired-credential provider answered in 31 ms, and the
successful provider took 18.3 s and reached its terminal state well inside a
minute. 300 leaves two minutes of headroom over a full-length provider turn
neither real run came close to using. `held_packet` still refuses a cleanup
bound that is not beside the overall one.

## Step 0 — the bound source

The snapshot already exists and is verified; **do not rebuild it**.

```sh
DOSSIER=/home/sl/src/baton/work/records/2026/09/finding-v12-single-implementation-proof
/home/sl/.local/state/baton-v12-venv/bin/python -B "$DOSSIER/snapshot_242687.py" --verify
```

That re-checks the bound tree against **its own** manifest and confirms the
preserved predecessor is unmoved. `snapshot_242687.py` with no arguments now
refuses, because the destination exists; `--rebuild-into <path>` builds a
successor with **its own** manifest and refuses to replace an existing one.

## The paths

```sh
PY=/home/sl/.local/state/baton-v12-venv/bin/python
BOUND=/home/sl/baton-runs/single-implementation-242687/manager-source
DOSSIER=/home/sl/src/baton/work/records/2026/09/finding-v12-single-implementation-proof
ROOT=/home/sl/baton-runs/single-implementation-243284
RUN="$ROOT/run"
SEL="$ROOT/selections.json"

# THE FIXTURE AND ITS BASE, BOUND. Step 2 creates the repository; this reads
# its HEAD back rather than guessing one. An earlier draft of this page invoked
# the composer with `--base "$BASE"` and never assigned BASE at all, so in a
# fresh shell it expanded empty.
SOURCE="$ROOT/fixture-source"
BASE="$(git -C "$SOURCE" rev-parse HEAD)"
```

`$BASE` must also be the Authority's canonical target, which step 5a sets from
this same value. Record it and `harness.py`'s digest in `$SEL`.

## Preconditions

1. **A new run identity**, hence a new Job identity.
   `SELECTIONS-SUCCESSOR-243284.json` names `single-implementation-243284` and
   the composer derives `job-single-implementation-243284`. Every earlier
   grant is spent by its own run.
2. **Genuinely fresh, dedicated stores** under `$ROOT/db/`. The accepted
   isolation boundary excludes stores containing other work, and **every**
   earlier instance now holds some: `single-implementation-239528` holds a Job
   whose ending never settled, the success instance holds another, and
   `managed-correction-236087` holds W236087's outstanding runtime. None of
   them is reusable and all of them are preserved evidence.
3. **Step 5a Authority preparation on the NEW instance.** The block is
   below and every operand is read from `$SEL`. Do NOT follow
   `OPERATOR-239528.md`'s copy: it literally opens
   `/home/sl/baton-runs/single-implementation-239528/db/authority.sqlite3` and
   performs `create_work`, `add_route_handler` and `grant_capability` against
   it. That is a write-capable example pointed at a preserved instance holding
   an unfinished Job, and it must not be the preparation instruction here.
4. **Whatever credential state you want to observe.** This packet is
   indifferent: with a valid token you will reach the custody blocker, with an
   expired one you will reach the `unable` path. Both are now reported
   promptly.

## Step 5a — prepare the successor Authority, from the successor selections

Every operand comes from `$SEL`; nothing below names an earlier instance, and
the assertion refuses if one creeps in.

```python
import json
from baton_v12.authority import Authority

SEL = "/home/sl/baton-runs/single-implementation-243284/selections.json"
BASE = "<the HEAD the command bound -- the same value>"

chosen = json.load(open(SEL))["compose"]
store = chosen["instance"]["authority_store"]
uuid = chosen["instance"]["authority_uuid"]
work = chosen["participants"]["work_id"]
integrator = chosen["instance"]["integration_profile"]["integrator_participant"]
receipts = chosen["participants"]["receipts"]

assert "single-implementation-243284" in store, store   # never an older one

authority = Authority.open(store, expected_authority_uuid=uuid)
try:
    authority.create_work(work, "impl", contract="v12-assignment-1",
                          operation_id="w239528-successor-243284")
    scope = authority.project_work(work)["scope"]
    authority.add_route_handler("impl", chosen["participants"]["implementation"])
    # The review worker is CONFIGURED and never admitted; `stage_execution`
    # resolves its principal, so it must exist. `rview` handler registration is
    # not a prerequisite of this run, which submits no review stage.
    authority.add_route_handler("integration", integrator)
    for who, capability in ((receipts["verification"], "verify"),
                            (receipts["review"], "review"),
                            (receipts["approval"], "approve"),
                            (integrator, "integrate")):
        authority.grant_capability(who, capability, scope=scope)
    authority.set_policy("canonical_target", BASE)
finally:
    authority.dispose()
```

Then check what is left with `baseline_bindings.preflight`, reading its stated
limits in `OPERATOR-239528.md`: it is a helper neither CLI `main` calls, a
missing capability NAME is conclusive while a present one is not, and it cannot
verify route handlers at all.

## Steps 1–4

Step 2 (the fixture repository) is `OPERATOR-239528.md` step 2 unchanged:
`harness.py` printing `before` and `TASK.md`, committed, at `$SOURCE`. No
acceptance or review-feedback document.

```sh
mkdir -p "$ROOT"
cp "$DOSSIER/SELECTIONS-SUCCESSOR-243284.json" "$SEL"
# fill the <OWNER> members, then:

PYTHONPATH="$BOUND" "$PY" -B "$DOSSIER/baseline_bindings.py" \
    --selections "$SEL" --base "$BASE" --run-root "$RUN"

PYTHONPATH="$BOUND" "$PY" -B "$DOSSIER/baseline.py" \
    --packet "$RUN/PACKET.json" \
    --incarnation single-implementation-243284
```

Before running step 4, read `PACKET.json`:

- `manager_source.files["baton_v12/job_manager/review_driver.py"]` must be
  `9a8a4a81…20ae4`. If it reads `b5b22535…ebe10c` you are bound to the
  preserved pre-correction snapshot.
- `bounds.total_seconds` 300, `bounds.cleanup_seconds` 60.
- `submission.job_id` `job-single-implementation-243284`.

## What to expect, and what each outcome means

**The likely outcome, while the blocker stands:**

    stopped              no-progress
    stage_states         implementation answering
    stalled_ticks        6
    served_seconds       seconds, not 300
    outstanding_cleanup  []
    workload.dispositions  [{... "disposition": "completed"}]
    workload.attribution   author and committer "Baton worker <worker@baton.invalid>"
    state                held

That is the custody blocker, observed under the corrections. The proposal the
run really produced is still reported; nothing reads as success.

**If you interrupt it**, you get the outcome's path printed and exit 130 — not
a traceback. The outcome is retained before the interrupt is re-raised.

**A new finding would be**: `overall-bound-exceeded` (the no-progress rule did
not fire), `outstanding_cleanup` non-empty, a `completed` stage state with
`state: settled` (which would mean the custody blocker had resolved itself and
deserves its own inspection), or any traceback out of the command.

Record whichever happened. Do not re-run for a different answer: a second run
needs a new run identity and a new selection.

## What this command does NOT authorize

Deciding the custody question. Any retry. Reuse of, recovery on, or cleanup of
any earlier run's stores, runtimes or evidence. Overwriting any bound snapshot
or manifest. Any reviewer stage or session resume. Any Work closure.
