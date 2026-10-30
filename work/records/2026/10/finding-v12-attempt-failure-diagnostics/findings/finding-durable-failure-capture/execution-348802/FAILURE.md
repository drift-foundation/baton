# The one actual execution of this Work, and why it failed

Recorded by `baton.claude`, first at claim337453 and carried forward unchanged
in substance at claim339421. This is not a packet instruction; it is the account
of what happened when a packet of this campaign was selected and started, and it
is here because a reader of this packet needs to know that this vehicle has
already been run once and what it did.

## What was selected

The owner accepted `../execution-334663`'s preparation (thread seq334822,
334825 and334829 — **the same acceptance sent three times, one selection, not
three retries**) and selected the run `attempt-diagnostics-w333486-334663` at
`/home/sl/baton-instances/attempt-diagnostics-w333486-334663`, base
`a9f4fa4d`, **using only `packet/AUTHORING-COMMAND.json`** — never the
composer's `commands.json` start. One provider-backed authoring invocation was
authorized.

So the preparation discipline held: the right command was selected, and the
sealed operands matched.

## What happened

It **failed during startup after 0.506 seconds**, before any provider turn.

```
child_started true, child_exited true, child_status 1,
elapsed_seconds 0.5057386530024814, state held, recovery_only false
```

The traceback, from the retained log:

```
tools/authoring_enforcement.py child_main
  -> baseline.main(..., compose=child_compose)
  -> tools/authoring_enforcement.py child_compose
  -> tools/stage_execution.py operations_from
  -> tools/single_worker.py worker_preflight
  -> worker_manager/workspaces.py hold_manager_instance
ContractRefusal: policy/denied -- "another manager is already active for
workspace '/home/sl/baton-instances/attempt-diagnostics-w333486-334663…',
holding control store '…'; only one Host manager may be active for one
workspace and database, so this start is a configuration error rather than a
standby"
```

The enforcement parent had already composed a manager and taken the workspace
guard; the child's own composition asked for the same guard and was correctly
refused. **The refusal is the product working**: single-manager exclusion is an
invariant, and the controller violated it. Nothing was corrupted, nothing ran,
no provider was contacted and no token was spent.

Owner reroute334895 recorded the failure and asked for a bounded controller
correction preserving single-manager exclusion. Reviewer allocated **W334910**;
it was implemented, independently reviewed (`decisions/guard-review.md`),
integrated (`decisions/guard-integration.md`) and committed as
`fb48797903160aa764229d58f3a5beaf29648bfc`. Owner close337414 satisfied it and
wake337416 cleared this Work's gate.

## What the guard correction changed

`tools/authoring_enforcement.py` moved from
`2da6eb36b398d730c8cc07a9df0b604de678a3fd994d5019097fa023addfb88f` to
`bc8c0363e44fedeae09c15a9065733227f08e279164ed68dc4b0e9e058a7c50f`:

- **One manager process.** The child holds the workspace guard for *both* the
  enforcement thread and the author: `prepare_manager` calls
  `workspaces.hold_manager_instance` before `baseline.prepare`, inside the
  `Guard` thread's own composition, and `child_main` starts that guard before
  entering `baseline.main`.
- **The outer process composes no manager at all.** It became a `RemoteGuard`
  watchdog that reads a published status file (`publish_guard` writes it
  atomically via `os.replace`) and bounds the child's process lifetime. Its
  docstring is explicit that snapshots are observations, never cessation or
  permission grants, and that a missing final snapshot is **held**.
- `supervise_process` gained `owned_child`, so the watchdog supervises a child
  it did not launch inside the deadline loop, and waits up to 30 seconds for the
  manager to publish its envelope before concluding it never established one.
- Recovery never enters `baseline.main`, never submits and never admits an
  author invocation; it keeps enforcement available for its cleanup slice.

**The operator-facing invocation is unchanged** by that correction, and
unchanged again by the shutdown correction: still
`python -m tools.authoring_enforcement --packet <PACKET.json>` from the staged
source.

## What has changed since, and what this packet pins

The controller moved again. W338305's accepted shutdown correction took it from
`bc8c0363…` to **`d12769df…`**, moved the supervisor baseline from
`c1b0a10e…` to **`8e5987f5…`**, and added **`tools/authoring_shutdown.py`**
(`af9e5ea6…`) which the controller imports. `SHUTDOWN.md` is that account. This
packet pins all three, so:

- `PREPARATION-PINS.json` records the **previous** controller digest as well,
  so a reader can tell this packet's controller both from the one that failed at
  startup and from the one `../execution-337453` pinned;
- the controller and the shutdown helper are each cross-checked three ways — the
  pin, the packet's own manager source, and the declared base — because the
  controller's `verify_controller` requires the first two and a missing helper
  is an import-time startup failure rather than a refusal;
- `../execution-334663`, `../execution-337453` and the failed instance are
  preserved **unchanged**. No rerun, no runtime recovery, no reuse of that root.
  This packet proposes a **fresh** run identity and a **fresh** destination that
  does not exist;
- the real-process proofs are **reused, not re-run**:
  `decisions/guard-integration-result.json` (79 tests, 15.278s, authority337376)
  and `decisions/shutdown-review.md` (44 tests, 72.891s, authority338596).

Read-only copies of the failed run's own evidence — the retained authoring log,
the enforcement report and the exact command used — are in the dossier at
`evidence/execution-334663-failure/`, indexed by
`decisions/failed-run-INDEX.json`.

## What none of it establishes

That the next start will succeed. One startup refusal was corrected and one
ending was made bounded; neither is a demonstration that a full
provider-backed authoring invocation completes on this vehicle.

**AMENDED AT CLAIM348718, twice over.** First: invocations *have* now completed
for this Work — run345039 at 461.10s, run345388 at 789.14s and run345822 at
733.29s, all returning on their own, and the last one's sealed gate **passed**.
The older sentence that none ever had is withdrawn; what remains true is that
**no candidate has been accepted**. Second: the 900-second lease referred to
here was superseded by W333485's independently accepted host permission
correction, closed satisfying by owner348699 — see
`decisions/host-policy.json`. The honest expectations otherwise stay exactly as
`ENFORCEMENT.md` and `SHUTDOWN.md` state them.
