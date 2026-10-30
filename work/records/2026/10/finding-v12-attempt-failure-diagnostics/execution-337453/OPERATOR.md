# Owner operations — W333486 execution packet, revision 4

**Read this first: the previous packet was selected, started, and failed at
startup in 0.506 seconds.** `FAILURE.md` is the account. The defect is
corrected at this packet's base, but no authoring invocation has ever
completed for this Work.

**The start is NOT SELECTED.** Both prerequisites are closed — W333735 at
`a9f4fa4d`, W334910 at `fb48797903160aa764229d58f3a5beaf29648bfc` — so this is
not a blocker. What remains is independent preparation review, then an exact
execution selection. Steps 0 to 3 are authorized preparation and produce no
execution.

**Two things that will bite you if you skip the rest:**

1. **Do not use `commands.json`'s `start`.** The accepted composer still
   generates the unenforced supervisor invocation. Use
   `<root>/packet/AUTHORING-COMMAND.json`.
2. **Do not expect a 3600-second run.** `tokens.LIFETIME_SECONDS` is still 900
   and renewal is not in this base. Both corrections make that lease
   *enforced*, not longer.

Nothing below has been executed against the selected root. Preparation was
exercised once into `/tmp/w333486-preflight-337453`; the selected root is
untouched and does not exist, no Job is submitted, no engine or container was
invoked, no provider was contacted, no credential was read.

This packet **supersedes `../execution-333504`, `../execution-333707` and
`../execution-334663`**, all preserved unchanged. The failed instance at
`/home/sl/baton-instances/attempt-diagnostics-w333486-334663` is preserved and
is **never reused, rerun or recovered** — this packet proposes a fresh run
identity and a fresh destination.

Let `<packet>` be
`/home/sl/src/baton/work/records/2026/10/finding-v12-attempt-failure-diagnostics/execution-337453`
and `<root>` be `/home/sl/baton-instances/attempt-diagnostics-w333486-337453`.

## Step 0 — read-only input check (anyone, any time)

```
python3 -B <packet>/verify-inputs.py
```

Opens no store, writes nothing, starts nothing. **Run this first.**

It separates **refusals** — base bytes, the 113 pinned manager files, the
pinned corrected controller (checked against both the manager source and the
base), the bootstrap binary, a damaged decision snapshot, an absent task
input, a checkout document missing from the base, an already-present gate
module, a provenance claiming an authorized or selected start, an absent
`ENFORCEMENT.md` — from **reports**: a `DECISION-SOURCE DRIFT` section that
exits 0, because the turn reads immutable snapshots and an ordinary update to
the reviewer-owned `FINDING.md` or `PLAN.md` must not invalidate a sealed
packet.

## Step 1 — stage (owner)

```
python3 -B <packet>/prepare.py stage --root <root> --acknowledge-unselected-start
```

The acknowledgement is required and is not ceremony: without it this refuses
and prints why, including the startup failure. It proves every base byte
**before** creating anything, then creates the root `0700`, refuses an
existing one, and writes the base's manager and supervisor source into it. A
refused stage leaves the filesystem exactly as it found it.

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

`--no-repositories` is deliberate. It generates this instance's own authority
uuid, so expect your composed packet digest to differ from the preflight's —
`bind` derives the Work id from that uuid and it travels into the submission.

## Step 3 — bind (owner)

```
python3 -B <packet>/prepare.py bind --root <root>
```

Composes the packet documents under `<root>/packet/`, proves them
(`held_packet` re-pins every artifact including all 15 `fixture.files`;
`verify_imported_sources` proves the process is running the staged code),
refuses a root that already holds a composed packet, and writes
`<root>/packet/AUTHORING-COMMAND.json`. Ends with `PREPARED.json: state
prepared-not-executed, start_selected false, composer_start_is_unenforced
true`. **No Job is submitted.**

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
with the controller's staged path and digest. The invocation is unchanged by
the guard correction; `--status-path` is internal, passed by the watchdog to
the child.

Measured in preparation: the **corrected** controller's own
`verify_controller` **accepts** this packet from the staged source and
**refuses** one imported from the host checkout. A packet pinning the
**superseded** controller digest is refused before any root is created.

`SIGINT`/`SIGTERM` sets the enforcement stop and begins the reserved cleanup
window; the controller reports `state: held`. **A held outcome is not proof of
cessation**, and a missing final status snapshot is also held.

Before starting, confirm the credential profile this packet names resolves in
your own private registry (`/home/sl/.baton/credential-sources.json`, slot
`claude`, reference `w202663-development`). This packet reads no credential and
carries no bearer.

## Four things to know before a start is selected

1. **The previous start failed in 0.506s.** Two managers for one workspace;
   `hold_manager_instance` correctly refused. Corrected at this base — but one
   corrected startup refusal is not evidence that a full invocation completes.
   If this one also fails, the honest account of how far it got is the
   deliverable, and the failed instance is preserved rather than retried.

2. **The 900-second lease is enforced, not extended.** Expect expiry at 900
   seconds with cessation ordered, partial output retained and a held outcome.
   `TASK.md` instructs the turn to report the actual expiry, cleanup,
   retained-output and recovery behaviour — evidence for this Work, not a
   failure to hide.

3. **The verification ceiling is 30 seconds and is not this packet's to set.**
   The ten gate modules measure 14.095s, leaving ≈15.9s for the two the turn
   must write. That fit **remains unproved**, and no coverage may be removed
   to force a pass. `tests.manager.test_authoring_manager_guard` is excluded
   from the gate for a measured reason — 17.643s for 7 real-process tests
   would put the sealed gate at 31.7s — with its coverage carried by the
   reused accepted proof.

4. **Two excluded test modules already fail at base**, both explicitly
   unverified baseline reports with no cleanup selected:
   `tests.manager.test_boundary_inventory` and `tests.tools.test_packaging`'s
   subcommand case, which holds the source command table against the installed
   bundle. A source-level case is **not** proof that a rebuilt bundle carries a
   new verb.

## Step 5 — after a run, if one is selected

The retained proposal is immutable and is **not** an accepted candidate. An
independent reviewer consumes it through v11 after exact runtime cessation;
no automatic integration, no self-acceptance. A failed or partial run is
preserved and reported with its evidence rather than retried silently. Parent
W325959 consumes this jointly with W333485, and the human Git checkpoint the
parent PLAN carries remains pending.

## Retained temporary paths

Left in place for you rather than removed. None is a selected root; none holds
a credential or a submitted Job.

- `/tmp/w333486-preflight-337453` — this revision's exercised preparation root
- `/tmp/w333486-probe-drift-453` — the drift probe's staged-but-unbound root
- `/tmp/w333486-base-fb48` — a clean export of the declared base (including the
  supervisor directory the enforcement tests need), used for the gate
  measurements
- the earlier revisions' roots: `/tmp/w333486-preflight-334663`,
  `/tmp/w333486-probe-drift-663`, `/tmp/w333486-base-a9f4`,
  `/tmp/w333486-preflight-333707`, `/tmp/w333486-probe-drift-707`,
  `/tmp/w333486-base-probe`, `/tmp/w333486-preflight-333504`,
  `/tmp/w333486-probe-drift`

The **failed selected run** is not in this list: it lives at
`/home/sl/baton-instances/attempt-diagnostics-w333486-334663` and is preserved
as evidence, not as a temporary path.
