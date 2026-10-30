# The first actual execution of this Work, and why it failed

Recorded by `baton.claude`, claim337453. This is not a packet instruction; it
is the account of what happened when the previous packet was selected and
started, and it is here because a later reader of this packet needs to know
that this vehicle has already been run once and what it did.

## What was selected

The owner accepted `../execution-334663`'s preparation (thread seq334822,
334825 and334829 — the same acceptance sent three times) and selected the run:
`attempt-diagnostics-w333486-337453`'s predecessor
`attempt-diagnostics-w333486-334663`, at
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
refused. **The refusal is the product working**: single-manager exclusion is
an invariant, and the controller violated it. Nothing was corrupted, nothing
ran, no provider was contacted and no token was spent.

Owner reroute334895 recorded the failure and asked for a bounded controller
correction preserving single-manager exclusion. Reviewer allocated **W334910**;
it was implemented, independently reviewed
(`decisions/guard-review.md`), integrated
(`decisions/guard-integration.md`) and committed as
**`fb48797903160aa764229d58f3a5beaf29648bfc`** — this packet's base. Owner
close337414 satisfied it and wake337416 cleared this Work's gate.

## What the correction changed

`tools/authoring_enforcement.py` moves from
`2da6eb36b398d730c8cc07a9df0b604de678a3fd994d5019097fa023addfb88f` to
`bc8c0363e44fedeae09c15a9065733227f08e279164ed68dc4b0e9e058a7c50f`. Read
read-only this claim against the committed diff:

- **One manager process.** The child now holds the workspace guard for *both*
  the enforcement thread and the author: `prepare_manager` calls
  `workspaces.hold_manager_instance` before `baseline.prepare`, inside the
  `Guard` thread's own composition, and `child_main` starts that guard before
  entering `baseline.main`.
- **The outer process composes no manager at all.** It becomes a `RemoteGuard`
  watchdog that reads a published status file (`publish_guard` writes it
  atomically via `os.replace`) and bounds the child's process lifetime. Its
  docstring is explicit that snapshots are observations, never cessation or
  permission grants, and that a missing final snapshot is **held**.
- `supervise_process` gained `owned_child`, so the watchdog supervises a child
  it did not launch inside the deadline loop, and waits up to 30 seconds for
  the manager to publish its envelope before concluding it never established
  one.
- Recovery never enters `baseline.main`, never submits and never admits an
  author invocation; it keeps enforcement available for its cleanup slice.

**The operator-facing invocation is unchanged**: still
`python -m tools.authoring_enforcement --packet <PACKET.json>` from the staged
source. `--status-path` is internal — the watchdog passes it to the child.

## What this packet does about it

- Pins the corrected controller (`bc8c0363…`) and checks it against **both**
  the pinned manager source and the base, because the controller's own
  `verify_controller` requires exactly that.
- Records the previous digest in `PREPARATION-PINS.json` so a reader can tell
  this packet's controller from the one that failed.
- Preserves `../execution-334663` and the failed instance **unchanged**. No
  rerun, no recovery, no reuse of that root. This packet proposes a **fresh**
  run identity and a **fresh** destination.
- Reuses the accepted real-process proof rather than re-running it:
  `decisions/guard-integration-result.json` records the 79-test selection
  (`test_authoring_manager_guard`, `test_authoring_enforcement`,
  `test_attempts.CancellationFencesBeforeItStops` and two `test_tool` cases)
  passing in 15.278s under authority337376.

## What it does not establish

That the next start will succeed. One startup refusal was corrected; that is
not a demonstration that a full provider-backed authoring invocation completes
on this vehicle. No such run has ever completed for this Work. The honest
expectations stay exactly as `ENFORCEMENT.md` states them — including the
900-second lease, which remains enforced and unextended.
