# Owner operations — W333486 execution packet, revision 2

**The start is HELD. Read `HOLD.md` before anything else.** Steps 0 to 3 below
are authorized preparation and produce no execution; **step 4 is not
authorized** and `prepare.py` will not let an ordinary-looking sequence of
steps carry you into it.

**Nothing below has been executed against the selected root.** The preparation
steps were exercised once into the throwaway root
`/tmp/w333486-preflight-333707` and the results are in `PREFLIGHT.json`; the
selected root is untouched and does not exist, no Job is submitted, no engine
or container was invoked, no provider was contacted, no credential was read,
and the shared-authoring falsification was **reused** from W333485 rather than
re-run.

This packet **supersedes `../execution-333504`**, which is preserved unchanged
(seal `bca87e931532560d6feebcaff36f59be82592841550d09807ad88f00c811fcf3`).
`PACKET.md` lists the eight changes. One of them is a correction to the
superseded OPERATOR, in the "before step 4" section below.

Selected identities are in `PACKET.md`. In short: base
`bbdacb5d38f6cf2d2461e9da103d28f9ab30cc6c`, run
`attempt-diagnostics-w333486-333707`, selected root
`/home/sl/baton-instances/attempt-diagnostics-w333486-333707`, existing image
`baton-v12-claude-worker:w239528-244216` (not rebuilt), manager runtime
`/home/sl/baton-runs/managed-correction-236087/build/stack/out/distro`.

Let `<packet>` be
`/home/sl/src/baton/work/records/2026/10/finding-v12-attempt-failure-diagnostics/execution-333707`
and `<root>` be `/home/sl/baton-instances/attempt-diagnostics-w333486-333707`.

## Step 0 — read-only input check (anyone, any time)

```
python3 -B <packet>/verify-inputs.py
```

Opens no store and writes nothing. Measured 0.109s. **Run this first.**

It distinguishes two kinds of answer, which is the fix for the superseded
packet's real defect:

- **Refusals** are things that decide what would be built — a pinned
  preparation input, the base's own 112 manager and 3 supervisor files, the
  bootstrap binary, a damaged decision snapshot, an absent task input, a
  checkout document missing from the base, a gate module that already exists,
  or a provenance claiming a start this packet holds.
- **Reports** are things that decide what is next. The turn reads **immutable
  snapshots** under `decisions/`, so an ordinary update to the reviewer-owned
  `FINDING.md` or `PLAN.md` no longer invalidates a sealed packet. Instead the
  check prints a `DECISION-SOURCE DRIFT` section and exits 0, and you and the
  reviewer decide whether the snapshot still reflects accepted scope.

## Step 1 — stage (owner)

```
python3 -B <packet>/prepare.py stage --root <root> --acknowledge-hold
```

`--acknowledge-hold` is required and it is not ceremony: without it this
refuses and prints the hold. Preparation produces no execution.

It proves every base byte **before** creating anything, then creates the root
`0700`, refuses an existing one, writes the base's manager and supervisor
source into it, and emits `bootstrap-inputs.json` and `stage.json` (which
records `start_held: true`). A refused stage leaves the filesystem exactly as
it found it.

## Step 2 — bootstrap this instance's own authority (owner)

```
cd <root>/code/v12/python
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=<root>/code/v12/python/src:<root>/code/v12/python \
python3 -B -m tools.bootstrap \
  --inputs <root>/bootstrap-inputs.json \
  --destination <root>/instance \
  --distro /home/sl/baton-runs/managed-correction-236087/build/stack/out/distro \
  --no-repositories
```

The supported bootstrap. `--no-repositories` is deliberate: this instance binds
no Job and configures no execution capacity until `bind` runs. It generates
**this instance's own** authority uuid. Expect your composed packet digest to
differ from the preflight's: `bind` derives the Work id from that uuid
(`uuid[:8] + "-W1"`) and it travels into the submission. The stable, pinned
half is the input side.

## Step 3 — bind (owner)

```
python3 -B <packet>/prepare.py bind --root <root>
```

Composes the packet documents under `<root>/packet/`, then proves them:
`held_packet` re-pins every artifact the packet binds — including all 9
`fixture.files`, so a drifted document refuses here rather than inside a turn
— and `verify_imported_sources` proves the process is running the staged code.
Refuses a root that already holds a composed packet. Ends with
`PREPARED.json: state prepared-not-executed, start_authorized false`. **No Job
is submitted.**

## Step 4 — start: NOT AUTHORIZED

```
# from <root>/packet/commands.json, "start" — recorded, NOT to be run yet
/usr/bin/python3 -B <root>/supervisor/baseline.py \
  --packet <root>/packet/PACKET.json \
  --incarnation attempt-diagnostics-w333486-333707
```

Recorded so you do not have to reconstruct it. **Do not run it.** `HOLD.md`
carries the reason and the reused evidence; in one sentence: the selected
`baseline.py` supervisor calls `serve` with **no reclaim pass**
(`baseline.py:1207`; `manager.py:833 reclaim=None`, `:879` runs a pass only
`if reclaim is not None`), so the 900-second workspace generation is **not
enforced** across the 3600/4800 run these documents request.

`HOLD.md` also records the two routes that could lift the hold — a narrow
temporary exception scoped to the authoring enforcement prerequisite, or
selection of an already independently accepted authoring vehicle. Both are
yours to decide; neither is reviewer-granted and neither is granted here.

If the hold is lifted, `commands.json` also carries the read-only `status`
invocation and records `submission_owner: "start; do not also submit
manually"`; SIGINT/SIGTERM requests the supervisor's bounded cancellation, and
**a held outcome is not proof of cessation**. You would also need to confirm
the credential profile this packet names resolves in your own private registry
(`/home/sl/.baton/credential-sources.json`, slot `claude`, reference
`w202663-development`). This packet reads no credential and carries no bearer.

## Three things to know before step 4 is ever considered

1. **A correction to the superseded packet.**
   `../execution-333504/OPERATOR.md` warned that the native pilot's
   903-second termination might stop the authoring turn at 900 seconds. **That
   claim is withdrawn.** It transferred the native `tools/job_manager.py`
   reclaim's behaviour to a vehicle that does not have it. The truth is the
   reverse, and it is why the start is held: on this vehicle the lease is
   **unenforced**, not strict. The superseded packet is preserved with that
   error in it rather than silently corrected.

2. **The verification ceiling is 30 seconds and is not this packet's to set.**
   Fixed by the composer at `baseline_bindings.py:345` and `:522` with no
   compose parameter. The nine existing gate modules measure 11.830s, leaving
   ≈18.17s for the two the turn must write. `LIMITS-CHECK.json` reports what
   the generated documents say rather than what prose wishes.

3. **Two excluded test modules already fail at this base**, both explicitly
   unverified baseline reports with no cleanup selected:
   `tests.manager.test_boundary_inventory` (328 tests, 28 failures, 1 error,
   49.469s on base bytes) and `tests.tools.test_packaging`'s subcommand case,
   which holds the source command table against the installed bundle — built
   at `1e576ff2`, before `record` and `disposition` joined it. A source-level
   case is **not** proof that a rebuilt bundle carries a new verb, and
   `TASK.md` keeps that deployment obligation explicit.

## Step 5 — after a run, if one is ever selected

The retained proposal is immutable and is **not** an accepted candidate. An
independent reviewer consumes it through v11 after exact runtime cessation;
there is no automatic integration and no self-acceptance. A failed or partial
run is preserved and reported with its evidence rather than retried silently.
Parent W325959 consumes this result jointly with W333485, and the human Git
checkpoint the parent PLAN carries remains pending.

## Retained temporary paths

Left in place for you rather than removed, because a managed turn does not
issue a destructive shell command merely to tidy its own reproduction. None is
the selected root; none holds a credential or a submitted Job.

- `/tmp/w333486-preflight-333707` — this revision's exercised preparation root
- `/tmp/w333486-probe-drift-707` — the staged-but-unbound root the drift probe used
- `/tmp/w333486-base-probe` — a clean `git archive` export of the declared base,
  used for the gate measurements
- `/tmp/w333486-preflight-333504`, `/tmp/w333486-probe-drift` — the superseded
  packet's, preserved with it
