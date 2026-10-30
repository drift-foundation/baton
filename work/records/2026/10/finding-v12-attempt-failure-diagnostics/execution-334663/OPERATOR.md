# Owner operations — W333486 execution packet, revision 3

**The start is NOT SELECTED.** The authoring-enforcement prerequisite that held
the previous packet is **closed** (owner close334628, checkpoint
`a9f4fa4da2323a357ae15aefbc5d7d22d41487b6`), so this is no longer a blocker.
What remains is ordinary sequence: independent preparation review, then an
exact execution selection. Steps 0 to 3 are authorized preparation and produce
no execution.

**Two things will bite you if you skip the rest of this document:**

1. **Do not use `commands.json`'s `start`.** The accepted composer still
   generates the **unenforced** supervisor invocation. Use
   `<root>/packet/AUTHORING-COMMAND.json`. See `ENFORCEMENT.md`.
2. **Do not expect a 3600-second run.** `tokens.LIFETIME_SECONDS` is still 900
   and renewal is not in this base. The new controller makes that lease
   *enforced*, not longer.

**Nothing below has been executed against the selected root.** The preparation
steps were exercised once into `/tmp/w333486-preflight-334663`; the selected
root is untouched and does not exist, no Job is submitted, no engine or
container was invoked, no provider was contacted, no credential was read.

This packet **supersedes `../execution-333504` and `../execution-333707`**,
both preserved unchanged and both unlaunchable — they pin the old unenforced
supervisor. `../execution-333707/HOLD.md` is historical.

Let `<packet>` be
`/home/sl/src/baton/work/records/2026/10/finding-v12-attempt-failure-diagnostics/execution-334663`
and `<root>` be `/home/sl/baton-instances/attempt-diagnostics-w333486-334663`.

## Step 0 — read-only input check (anyone, any time)

```
python3 -B <packet>/verify-inputs.py
```

Opens no store, writes nothing, starts nothing. **Run this first.**

It separates **refusals** — base bytes, the 113 pinned manager files, the
pinned authoring controller (checked against both the manager source and the
base), the bootstrap binary, a damaged decision snapshot, an absent task input,
a checkout document missing from the base, an already-present gate module, a
provenance claiming an authorized or selected start, an absent
`ENFORCEMENT.md` — from **reports**: a `DECISION-SOURCE DRIFT` section that
exits 0, because the turn reads immutable snapshots and an ordinary update to
the reviewer-owned `FINDING.md` or `PLAN.md` must not invalidate a sealed
packet. You and the reviewer decide whether a drifted snapshot still reflects
accepted scope.

## Step 1 — stage (owner)

```
python3 -B <packet>/prepare.py stage --root <root> --acknowledge-unselected-start
```

The acknowledgement is required and is not ceremony: without it this refuses
and prints why. It proves every base byte **before** creating anything, then
creates the root `0700`, refuses an existing one, writes the base's manager and
supervisor source into it, and emits `bootstrap-inputs.json` and `stage.json`.
A refused stage leaves the filesystem exactly as it found it.

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

`--no-repositories` is deliberate: this instance binds no Job and configures no
execution capacity until `bind` runs. It generates **this instance's own**
authority uuid, so expect your composed packet digest to differ from the
preflight's — `bind` derives the Work id from that uuid (`uuid[:8] + "-W1"`)
and it travels into the submission. The stable, pinned half is the input side.

## Step 3 — bind (owner)

```
python3 -B <packet>/prepare.py bind --root <root>
```

Composes the packet documents under `<root>/packet/`, proves them
(`held_packet` re-pins every artifact including all 10 `fixture.files`;
`verify_imported_sources` proves the process is running the staged code),
refuses a root that already holds a composed packet, and **additionally writes
`<root>/packet/AUTHORING-COMMAND.json`** — the enforced invocation. Ends with
`PREPARED.json: state prepared-not-executed, start_selected false,
composer_start_is_unenforced true`. **No Job is submitted.**

## Step 4 — start: NOT SELECTED YET

When a start is selected, this is the invocation — **not** the one in
`commands.json`:

```
cd <root>/code/v12/python
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=<root>/code/v12/python/src:<root>/code/v12/python:<root>/supervisor \
BATON_V12_STAGE_EXECUTION_CONFIG=<root>/packet/deployment.json \
python3 -m tools.authoring_enforcement --packet <root>/packet/PACKET.json
```

`<root>/packet/AUTHORING-COMMAND.json` carries exactly this, machine-readable,
with the controller's staged path and digest.

Why it must be this: `baseline_bindings.py:721` still composes `start` as
`[python, -B, <supervisor>/baseline.py, …]`, and `baseline.py:1207` calls
`serve` with no reclaim argument — the unenforced path. The accepted controller
runs from the **staged** source so its own `verify_controller` can resolve
itself inside `manager_source` and match its pinned digest. Measured in
preparation: that check **accepts** the staged controller and **refuses** one
imported from the host checkout.

`SIGINT`/`SIGTERM` sets the enforcement stop and begins the reserved cleanup
window; the controller reports `state: held`. **A held outcome is not proof of
cessation.**

Before starting, confirm the credential profile this packet names resolves in
your own private registry (`/home/sl/.baton/credential-sources.json`, slot
`claude`, reference `w202663-development`). This packet reads no credential and
carries no bearer.

## Three things to know before a start is selected

1. **The 900-second lease is enforced, not extended.** Production renewal is
   W333485's unfinished work. Expect expiry at 900 seconds with cessation
   ordered, partial output retained and a held outcome. `TASK.md` instructs the
   turn to preserve a partial candidate and report the actual expiry, cleanup,
   retained-output and recovery behaviour — that is evidence for this Work, not
   a failure to hide. Two of my earlier statements about this are withdrawn and
   recorded in `ENFORCEMENT.md`.

2. **The verification ceiling is 30 seconds and is not this packet's to set.**
   Fixed by the composer at `baseline_bindings.py:345` and `:522`. The ten
   existing gate modules measure 14.230s, leaving ≈15.8s for the two the turn
   must write — deliberately tighter than the previous revision, because
   `tests.manager.test_authoring_enforcement` was added to protect the accepted
   correction this candidate builds on.

3. **Two excluded test modules already fail at base**, both explicitly
   unverified baseline reports with no cleanup selected:
   `tests.manager.test_boundary_inventory` and
   `tests.tools.test_packaging`'s subcommand case, which holds the source
   command table against the installed bundle. A source-level case is **not**
   proof that a rebuilt bundle carries a new verb; `TASK.md` keeps that
   obligation explicit.

## Step 5 — after a run, if one is selected

The retained proposal is immutable and is **not** an accepted candidate. An
independent reviewer consumes it through v11 after exact runtime cessation;
there is no automatic integration and no self-acceptance. A failed or partial
run is preserved and reported with its evidence rather than retried silently.
Parent W325959 consumes this jointly with W333485, and the human Git checkpoint
the parent PLAN carries remains pending.

## Retained temporary paths

Left in place for you rather than removed, because a managed turn does not
issue a destructive shell command merely to tidy its own reproduction. None is
a selected root; none holds a credential or a submitted Job.

- `/tmp/w333486-preflight-334663` — this revision's exercised preparation root
- `/tmp/w333486-probe-drift-663` — the drift probe's staged-but-unbound root
- `/tmp/w333486-base-a9f4` — a clean `git archive` export of the declared base
  (including the supervisor directory the enforcement tests need), used for the
  gate measurements
- `/tmp/w333486-preflight-333707`, `/tmp/w333486-probe-drift-707`,
  `/tmp/w333486-base-probe`, `/tmp/w333486-preflight-333504`,
  `/tmp/w333486-probe-drift` — the two superseded packets', preserved with them
