# The authoring vehicle this packet binds

Recorded by `baton.claude`, claim337453. Declared base
**`fb48797903160aa764229d58f3a5beaf29648bfc`** — the human checkpoint that
integrated the accepted manager-guard correction (W334910, owner close337414).

Both prerequisites are now closed: W333735 supplied the enforcement lane
(`a9f4fa4d`) and W334910 corrected its manager-guard ownership (`fb487979`).
Both temporary direct-implementation exceptions have **expired** and neither
ever covered diagnostics.

`FAILURE.md` is the companion to this document: it records what happened when
the previous packet was actually started.

## The controller

`tools/authoring_enforcement.py`, pinned here as
`sha256 bc8c0363e44fedeae09c15a9065733227f08e279164ed68dc4b0e9e058a7c50f`
(the previous, failing one was `2da6eb36…`), present among this packet's
**113** pinned manager files.

Read read-only this claim against the committed bytes:

- **One manager process holds the workspace guard.** The child composes both
  the enforcement thread and the author under the same guard;
  `prepare_manager` takes `workspaces.hold_manager_instance` before
  `baseline.prepare`. This is the correction: the previous revision had the
  parent and the child each composing a manager, and the second was correctly
  refused.
- **The outer process composes no manager.** It is a `RemoteGuard` watchdog
  reading an atomically published status file, bounding the child's lifetime.
  Snapshots are observations, never cessation or permission; a missing final
  snapshot is **held**.
- `verify_controller(packet)` resolves `__file__` inside
  `packet["manager_source"]["path"]` and requires the pinned digest — so the
  controller must be **run from the staged source**, and a packet that did not
  pin it refuses.
- Admission is once: `admit_child` refuses a second child under the same run,
  and recovery is cancellation-only — **not a fresh budget**. Recovery never
  enters `baseline.main` and never admits an author invocation.
- Success is not the controller's to grant: `report["state"]` reaches
  `completed` only when the workload supervisor itself exits 0 **and** every
  attempt is observed `absent` with its token returned.

## The start command is still NOT the one the composer writes

Unchanged from the previous revision and still true at this base.
`baseline_bindings.py` is untouched
(`sha256 09fbf3c59820231b7199e24aa1cf64eee93f6ea2e60f3477fed5ca909e5fc379`)
and its line 721 still composes

```json
"start": ["<python>", "-B", "<supervisor>/baseline.py",
          "--packet", "<run>/packet/PACKET.json",
          "--incarnation", "<run_id>"]
```

That is the unenforced path. `decisions/review-334776.md` accepted **only**
the enforced invocation for later selection and recorded the composer
discrepancy as tracked under this Work, with no broad historical-composer
rewrite selected. W333485 independently reached the same mitigation in its own
preparation.

**Do not use `commands.json`'s `start`.** `prepare.py bind` writes
`AUTHORING-COMMAND.json` beside it:

```
cd <root>/code/v12/python
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=<root>/code/v12/python/src:<root>/code/v12/python:<root>/supervisor \
BATON_V12_STAGE_EXECUTION_CONFIG=<root>/packet/deployment.json \
python3 -m tools.authoring_enforcement --packet <root>/packet/PACKET.json
```

`--status-path` is internal: the watchdog passes it to the child. The
operator-facing invocation did not change with the guard correction.

Reported, not patched. Correcting the composer is host product work this Work
does not own, and **every later authoring packet inherits the defect until it
is corrected**.

## The lease: 900 seconds, enforced, not extended

`tokens.LIFETIME_SECONDS` is still **900** and production renewal is still
W333485's unfinished work, separately allocated to `baton.codx`.

The requested bounds — provider turn 3600s, verification command 30s, total
4800s, cleanup 60s — are **ceilings, not a promise of a 3600-second authoring
run.** The initial 900-second resource permission is enforced and may halt the
turn well before them, with cessation ordered, partial output retained and a
held outcome. `TASK.md` requires the turn to preserve a partial candidate and
report the actual expiry, cleanup, retained-output and recovery behaviour it
observes.

Two of my earlier statements remain withdrawn, and are repeated here so no
reader has to reconcile them from superseded packets:

- `execution-333504/OPERATOR.md` claimed the native pilot's 903-second
  termination transferred to the authoring vehicle. It did not — that vehicle
  had no reclaim at all.
- `execution-333707/HOLD.md` said the lease was unenforced on the authoring
  vehicle. True of that vehicle; untrue since `a9f4fa4d`.

Both documents are preserved with their original wording.

## Measured requirements and limits for the gate

Two numbers decided this packet's gate, both measured this claim against a
clean export of the declared base:

1. **`tests.manager.test_authoring_manager_guard` costs 17.643 seconds** for 7
   tests — it spawns real processes. The composer fixes
   `verification_command_seconds` at **30**, and the ten gate modules already
   cost 14.095s, so including it would put the sealed gate at **31.7s before
   the two new modules even exist**. It is therefore **excluded for a measured
   ceiling reason, not a coverage judgement**, and its coverage is carried by
   the reused accepted proof in `decisions/guard-integration-result.json` (79
   tests, PASS, 15.278s, authority337376). This candidate does not edit
   `authoring_enforcement.py`; if a turn ever does, that module must be run as
   a focused check outside the sealed argv.
2. **`tests.manager.test_authoring_enforcement` needs
   `work/records/2026/09/finding-v12-single-implementation-proof` at the
   checkout root** — it spawns a real supervisor and resolves that directory
   from `Path(__file__).resolve().parents[4]`. Measured at the previous base:
   **1 error without it, 33 passing with it.** The private git-line checkout
   carries it; it is pinned in `read_from_checkout_at_base`. It stays in the
   gate at 2.193s because it exercises the cancellation path through
   `attempts` and `intake`, which this candidate edits.
