# The startup failures on this vehicle, and what they cost

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

**CORRECTED AT CLAIM350529.** This section named `d12769df…` as the controller
this packet pins. That has been false since claim348718: W333485's accepted host
permission correction moved the controller to **`248ee9ed…`**, and this packet
stages it from the corrected W348979 binding. The sequence, in full: W334910
took it from `2da6eb36…` to `bc8c0363…` (the guard correction below), W338305
from `bc8c0363…` to `d12769df…` and added **`tools/authoring_shutdown.py`**
(`af9e5ea6…`) which the controller imports, and W333485 from `d12769df…` to
**`248ee9ed…`**, which additionally imports **`tools/authoring_baseline.py`**
(`8e5987f5…` — the same bytes as the supervisor baseline, moved into the
manager source at the accepted host base). `SHUTDOWN.md` is that account. This
packet pins all of them, so:

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

## The second startup failure: run348852, 2026-10-21

**AMENDED AT CLAIM350529.** A second selected invocation died before any
provider turn, and the cause was packaging rather than product behaviour.

Owner348925 selected `../execution-348852` and it was launched once at
19:06:22Z. The controller exited in about two seconds:

```
File ".../code/v12/python/tools/authoring_enforcement.py", line 554, in main
    from tools import authoring_baseline as baseline
ImportError: cannot import name 'authoring_baseline' from 'tools'
```

**No envelope was composed, no Job submitted, no attempt admitted, no runtime
or token created, no container started and no provider contacted.** All six
final-result artifacts are absent, and absence names no cause on its own — the
cause is the line above, read from the controller's own stderr. Nothing was
ordered, so there was nothing to clean. The root is preserved unchanged and the
selection is consumed.

**What it was, exactly.** The accepted controller imports
`tools.authoring_baseline` at lines 494, 506 and 554. The 114-member binding
that run staged preserved the old consumer host's runtime path set exactly, and
that path set never carried the module — at the accepted host base the
supervisor baseline was moved *into* the manager source under that name. So the
binding and the controller were individually accepted and mutually
inconsistent. The preparation, the seals, the binding equality and both
preflights were all correct; the defect was in what the binding declared.

**What it was not:** not authentication, not the permission or the retired
lease, not the worker candidate, not the recovery input and not the gate — none
of them was reached.

**And one honest gap, reported rather than widened:** neither preflight checked
that the staged manager source can *import* the controller it pins. Both passed
and the controller still could not start. Whether to add such a check is the
owner's and the reviewer's call, not this packet's; what this packet does do is
refuse a binding that fails to declare that member by name.

Evidence: `../evidence/run-348852/`, with `BLOCKER-348929.json` at
`f6d48cb7e5f950d02914dd7bf0c0b2908acd34dd519d2dce651739095c09ac61` and the
controller stderr verbatim; snapshot `decisions/run-348852-BLOCKER.json`.
W348979 owns the corrected binding, which this campaign now consumes.

## The third startup failure: run350529, 2026-10-22

**AMENDED AT CLAIM352156.** The corrected binding worked and the run refused
**two statements further on**, for a different reason — and this one was the
packet's, not the supplier's.

Owner352153 selected `../execution-350529` and it was launched once at
03:11:16Z. The import at controller line 554 **resolved** this time. Line 564
refused:

```
File ".../tools/authoring_enforcement.py", line 564, in main
    baseline.verify_imported_sources(packet)
File ".../tools/authoring_baseline.py", line 590, in verify_imported_sources
SupervisorRefusal: this process is running
'<root>/code/v12/python/tools/authoring_baseline.py' and the packet binds
'<root>/supervisor/baseline.py'
```

**What that check is.** `verify_imported_sources` proves every package the
packet names resolves inside the bound manager source, and then proves that
**the module it is itself defined in is the program the packet binds**. Its own
docstring says it runs *before any store is opened, which is the only moment at
which refusing is free* — and that is exactly what it did.

**Why it fired.** The old controller imported a top-level `baseline` from the
staged `supervisor/` directory, so the running module and the composed
supervisor path were the same file. The accepted controller imports
`tools.authoring_baseline` from the **manager source**. The composition still
named the supervisor directory copy. **The two files are byte-identical** —
`8e5987f5…`, `cmp` reports no difference — so the packet's supervisor digest
pin verified immediately before the refusal, and **only the path equality
failed**.

**Whose defect it is: this packet's.** `prepare.py`'s `bind` passed
`supervisor_path=<root>/supervisor/baseline.py`. That is a composition argument
of this packet, not the accepted binding and not the accepted controller. Since
claim352156 `bind` composes the staged `tools/authoring_baseline.py` and
**refuses** if the composed program is not that pinned member.

**Nothing was reached**: no envelope, no Job, no attempt, no runtime, no token,
no container, no provider call. `instance/db` holds only the `authority.sqlite3`
that step 2 bootstrap wrote — no job or control store exists, so the refusal
precedes the authoring lock, the store and the worker-image check, which are
`main`'s next three statements. Nothing was ordered, so there was nothing to
clean.

**And the honest part.** The author check run before that launch proved the
line-554 import resolved and said, in terms, that it *"does not establish that
the controller RUNS; only that these imports resolve"*. That was the right
disclaimer and this run is what it was warning about. **Two consecutive
selected invocations have now died inside the controller's own
startup-verification window, and nothing in preparation was calling those three
functions against the composed packet.** Since claim352156 something does — as
author evidence, not as packet machinery.

Evidence: `../evidence/run-350529/`, with `BLOCKER-352156.json` at
`5d9e626da7f38614bd59be885f4b2074fa686cc89b4339c41c70a72d2c9c8753`, the
controller stderr verbatim, the collection and all three preflight reports;
snapshot `decisions/run-350529-BLOCKER.json`.
