# The shutdown correction this packet binds, and what it means for a report

Recorded by `baton.claude`, claim339421, read-only against the committed diff
at this packet's base. This is the account of the accepted W338305 correction —
why this packet exists at all, what the vehicle now publishes when it ends, and
the one rule that matters when you read those reports.

## Why there is a fifth packet

`../execution-337453` was independently accepted as preparation
(`decisions/review-337566.md`, 25 seals and seven checks) and then **held** by
owner338168 for the finalization assessment. While it was held, the assessment
produced a correction, the correction was accepted, and the correction moved
exactly the bytes that packet pinned:

| input | execution-337453 pinned | this packet pins |
| --- | --- | --- |
| `tools/authoring_enforcement.py` | `bc8c0363…` | **`d12769df…`** |
| `work/records/2026/09/finding-v12-single-implementation-proof/baseline.py` | `c1b0a10e…` | **`8e5987f5…`** |
| `tools/authoring_shutdown.py` | *did not exist* | **`af9e5ea6…`** |

So execution-337453 is not launchable — not because anything is wrong with it,
but because its pins describe a vehicle that is no longer the accepted one. It
is preserved byte-for-byte with its seal intact and its acceptance remains
valid evidence for itself alone, exactly as PLAN says.

`decisions/shutdown-integration.json` is the independent six-path verification
of those bytes at this commit (accepted, committed and checkout digests agreeing
on every one). I re-verified all six myself this claim, the same three ways,
before writing anything.

## The one new file, and why it is load-bearing

`tools/authoring_shutdown.py` is **new at this base and new to every packet in
this campaign**. `tools/authoring_enforcement.py` imports it at line 26:

```python
from tools.authoring_shutdown import Shutdown, bounded
```

A staged manager source that omits it does not refuse — it **fails at import**,
which is a startup failure, and `FAILURE.md` records what a startup failure
cost this Work the last time. That is why the handoff requires the helper to
reach the staged host composition, why `manager_files` holds **114** entries
rather than 113, and why both `prepare.py` and `verify-inputs.py` cross-check it
three ways (the pin, the packet's own manager source, and the declared base) the
way they already check the controller.

## What the correction actually changed

- **One process-local shutdown budget.** `Shutdown` derives its deadline from
  `packet["bounds"]["cleanup_seconds"]` — `min(maximum, now + cleanup -
  min(12, cleanup / 2))`, capped by the controller's transmitted request — and
  subdivides the remainder across named phases: `cleanup` 1, `accounting` .7,
  `workload-publication` .45, `guard-stop` .2, `guard-publication` .05 of the
  reserve. `begin()` is idempotent: **a repeated begin does not renew the
  allowance.**
- **The budget is ephemeral to one incarnation.** The module's own docstring is
  explicit: it is not a persisted token deadline, not a grant, and not evidence
  of container cessation. A shutdown request naming another `run_id` is refused.
- **Blocking main-thread steps became interruptible.** `bounded(deadline, step)`
  arms `ITIMER_REAL` and raises `TimeoutError` with the step name; it refuses to
  run off the main thread and refuses to replace an existing alarm. This is a
  **cooperative** interruption mechanism — not proof that arbitrary kernel I/O
  can always be interrupted.
- **The outer process transmits its deadline instead of only killing.**
  `Process.request_shutdown` writes `<status_path>.shutdown.json` atomically
  with the run id and deadline before `terminate()`, and the watchdog publishes
  `guard.watchdog_deadline` so its own observation sleeps are bounded. Process
  kill and reap remain the backstop.
- **The supervisor accepts the shared deadline.** `baseline.supervise`/`main`
  take `shutdown=None` and, when given one, route the post-stop canonical read,
  cancellation, origins, the cleanup sweep, accounting, workload evidence, the
  outcome publication, `operations.close` and the final reporting through it.
  Cleanup failure is now reported rather than leaving an earlier stale field.
- **The reports became deadline-aware.** The controller report gains
  `shutdown_deadline` and `shutdown_progress`; `RemoteGuard.stop(timeout=…)`
  takes a bounded final snapshot read and, on failure, returns `state='held'`
  with the fault appended. The held wording was corrected to *"manager
  terminated without final enforcement report; retained observations do not
  resolve unknown effects."*

## Where the final results land

Three files, and they are the evidence an operator and a reviewer actually read:

| result | path | written by |
| --- | --- | --- |
| controller final report | `<outcome_path>.enforcement-<pid>-<ns>.json`, named in the report as `enforcement_path` | the outer controller, inside its own `outer outcome publication` bound |
| workload final report | `<outcome_path>` | the supervisor, inside the `workload-publication` reservation |
| shutdown progress | `<status_path>.progress.json` | each `Shutdown.call`, before running the step; the controller copies it into its report as `shutdown_progress` |

`<outcome_path>` and `<status_path>` are the composed packet's own members; the
run root in `COMMANDS.md` is where they resolve.

## The rule

**A missing or partial final report is INCOMPLETE. It is never success, never
acceptance, and never proof of cessation.**

That is not this author's gloss. The accepted review states it three ways: the
candidate's distinction between *execution cessation* and *output acceptance*
aligns with the selected lifecycle; phase evidence identifies the last entered
step and is **not** a sampled stack or an independent cessation receipt; and if
outer publication cannot complete, earlier evidence remains and **the missing
report is incomplete, never acceptance**. The controller's own code agrees — on
a publication `TimeoutError` it returns 1 and writes nothing, deliberately
preserving the earlier manager, workload and phase evidence rather than
manufacturing a result.

PLAN says the same thing from the other side: *no startup success or producer
exit substitutes for final-result acceptance.* So:

- A `state: held` controller report is an honest ending, not a failure to hide.
- An absent `enforcement-*.json` means the outer publication did not fit. Read
  `<outcome_path>` and `<status_path>.progress.json` instead, and say which of
  the three are present.
- `shutdown_progress.step` tells you the last step **entered**, not that it
  finished.
- None of this is a token settlement, and none of it establishes that a
  container stopped.

`TASK.md` carries this into the turn's reporting obligation as item 6, and into
the product axes: a diagnostic reader must not turn an incomplete final report
into an acceptance, nor a deadline-bounded publication failure into cessation
evidence.

## What this packet does NOT do with it

- It does **not** re-run the shutdown regressions. The proof is **reused**:
  `decisions/shutdown-review.md`, 44 tests with no skips in 72.891s unittest
  time under authority338596, plus the six-path integration record. PLAN
  directs exactly that, and the direct exception that authorized those runs
  expired at acceptance.
- It does **not** put `tests.manager.test_authoring_shutdown_deadline` in the
  sealed gate. Measured here: **51.333s for 4 real-process tests**, which
  exceeds the composer-fixed 30-second ceiling on its own. Excluded for the
  ceiling, not for coverage, and this candidate edits none of the three
  corrected files.
- It does **not** claim the correction makes a 3600-second run possible.
  `tokens.LIFETIME_SECONDS` is still 900. The enforcement correction made that
  lease real; this one made the **ending** bounded and its reports honest.
  Neither extends it.
