# The shutdown correction this packet binds, and what it means for a report

Recorded by `baton.claude`, claim339421 and **corrected at claim339628**,
read-only against the committed diff at this packet's base. This is the account
of the accepted W338305 correction — what the vehicle publishes when it ends,
where those reports land, who can read them, and the rules that matter when you
do.

## Statements earlier revisions of this document got wrong

`decisions/review-339623.md` item 2 found both, and they are corrected in place
below rather than softened. Recording them here because a reader of the previous
revision needs to know which claims not to carry forward:

1. **"An absent `enforcement-*.json` means the outer publication did not fit"**
   — a false inference. Many other things leave no final report. Absence means
   *unavailable, cause unknown*; see **The rules** below.
2. **"On a publication `TimeoutError` the controller returns 1 and writes
   nothing"** — false about the filesystem. The bound wraps `write_text`,
   `os.replace` *and* `print` together, so the file may already exist. See
   **What a publication timeout does and does not guarantee**.

Revision 6 then corrected both of those but **overstated what a timeout fault
proves**: it accepted any `TimeoutError` in a controller report as publication
evidence. `decisions/review-339861.md` found that.

Revision 7 narrowed it to publication steps — and still claimed a **child**
publication timeout "reaches the progress file". `decisions/review-340012.md`
found that too, by reading the producer's statement order:
`Shutdown.call` writes its snapshot **before** running its step and appends that
step's fault to memory only, and the controller's final publication is the
**last** such call. **No publication fault is reliably persisted by this vehicle
at all.** Rule 3 below is the corrected account.

None of these errors changes a pinned byte: every revision since
`../execution-339421` pins the same vehicle. What changed is what this document
tells a reader to conclude.

## Why there is an eighth packet

`../execution-339868` fixed the first four collector defects and introduced
three more, all found by `decisions/review-340012.md` with fixtures at
`decisions/collector-probes-339992.json`:

- **a malformed *link* aborted the collection** — `_linked` called `Path()` on
  whatever the report carried and caught only `OSError`, so a controller
  carrying `authoring_log: []` raised `TypeError` and lost a readable workload
  report beside it. In the very revision that fixed the malformed-*report* case;
- **one unrelated temporary marked every artifact `pending`**, because the
  directory-wide `outcome.json*.tmp` set was handed to all of them — and that
  glob never matched the workload temporary at all, which is
  `outcome.json.partial`;
- **the progress file was counted as a manager snapshot**, because
  `outcome.json.manager-*.json` matches `...json.progress.json`.

Plus the false persistence claim corrected in rule 3 below. All are fixed, all
are regression probes, and `../execution-339868` is preserved with its 36-member
seal intact.

## Why there was a seventh packet

`../execution-339628` pins the **same** vehicle as this packet and made the
operator's half executable — and its `collect.py` had four correctness defects,
all found by `decisions/review-339861.md` with fixtures in
`decisions/collector-probes-339847.json`: a present workload report classified
`absent`, correlation demanding a top-level `run_id` the controller does not
publish, any `TimeoutError` accepted as a publication timeout, and a JSON-array
report aborting the entire collection with an `AttributeError`. All four are
fixed and all four are now regression probes. It is preserved byte-for-byte with
its 34-member seal intact.

`../execution-339421` before it pins the same vehicle too, and was superseded for
its documents: the two statements above, a `TASK.md` item 6 that asked the
terminating worker to report results published after its own death, and an
absolute sibling-file ban. `decisions/review-339623.md` is that authority. Its
31-member seal is intact as well.

## Why there was a fifth packet

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

## Who can read them — and it is not the worker

**The worker inside the run cannot observe any of these three files.** All three
are published on the far side of its own termination: the controller writes its
report after `supervise_process` returns and after child cleanup
(`authoring_enforcement.py:552-591`), and the supervisor publishes
`<outcome_path>` post-stop (`baseline.py:1450-1461`). A worker killed at lease
expiry is gone before either exists.

So **post-run collection belongs to the external operator and the independent
reviewer**, with the exact read-only commands, the identity correlation and the
missing-evidence handling in `COMMANDS.md` step 5. The worker's half is
`TASK.md` item 6: what it observed before termination, plus the retained
candidate checkpoint, with the host-side results named as **structurally
unavailable to it** rather than reported as absent. Revision 5 of `TASK.md` got
this wrong and asked the producer to report its own future ending.

Full final-result collection acceptance is unchanged. The obligation moved to a
party that can discharge it.

## The rules

**1. A missing or partial final report is INCOMPLETE. It is never success, never
acceptance, and never proof of cessation.**

That is not this author's gloss. The accepted review states it three ways: the
candidate's distinction between *execution cessation* and *output acceptance*
aligns with the selected lifecycle; phase evidence identifies the last entered
step and is **not** a sampled stack or an independent cessation receipt; and if
outer publication cannot complete, earlier evidence remains and **the missing
report is incomplete, never acceptance**.

PLAN says the same thing from the other side: *no startup success or producer
exit substitutes for final-result acceptance.*

**2. An unavailable report names no cause.** Keep four states apart and never
collapse them into "absent" — and correlate each artifact through the shape **it**
publishes: the controller report through `original_envelope` (`run`, `job`,
`authority`; it has **no top-level `run_id`**), the workload outcome through
`run_id`/`work`/`claim`/`job_id`, the progress file through `run_id`/`job_id`.
Demanding one shape of all three reports a false `unresolved` for every real
controller report.

| state | what you observed | what it licenses |
| --- | --- | --- |
| **absent** | the path does not exist and you could read its directory | unavailable, cause unknown |
| **inaccessible** | the read itself failed — permission, mount, I/O | unavailable, cause unknown, and **not** absent |
| **pending** | the run has not reached publication, or an `.enforcement-*.tmp` sibling exists | unavailable **so far**; not absent, not failed |
| **unknown cause** | present but unparseable, **not a JSON object**, truncated, or its identity does not correlate | unavailable as evidence; say which |

A report can be missing because the run never started, because an import or
startup failure killed it — `FAILURE.md` is precisely that case, and it produced
no enforcement report at all — because the process died, because a read failed,
or because publication failed for a reason that is not a timeout.

**3. This vehicle persists NO publication fault reliably, so absence of one
proves nothing.** Revision 6 of this document said a child publication timeout
"reaches the progress file"; revision 7 kept that. **It is false**, and
`decisions/review-340012.md` item 3 is the finding. The source order, in
`Shutdown.call` (`authoring_shutdown.py:72-86`):

1. `:74` enters `bounded(deadline, step)` — **an exhausted deadline raises here**,
   before anything is written, so even the step name can be missing;
2. `:76-81` writes the snapshot carrying `list(self.faults)` — the faults of
   **earlier** calls, never this one's;
3. `:83` runs the step;
4. `:85` on exception appends the fault to `self.faults` **in memory** and
   re-raises.

So a step's own fault reaches disk **only if a later `Shutdown.call` writes a
snapshot successfully**. Therefore:

| step | can its timeout be recorded? | why |
| --- | --- | --- |
| `outer outcome publication` (`authoring_enforcement.py:588`) | **no** | not a `Shutdown.call` at all; the handler at `:592-595` returns 1 without recording anything |
| `final enforcement publication` (`:493`) | **no** | it is the **last** `Shutdown.call` in the controller's `finally`. Nothing follows it to flush its fault |
| `workload publication` (`baseline.py:1461`) | **not reliably** | later calls exist in `main` (`:2796`, `:2884`) but are reached only if control gets there, and each re-enters `bounded()` against the **same exhausted deadline**, so it will likely raise before writing |

**So an absent publication fault is the EXPECTED state even when a publication
really did time out.** It is not evidence either way. Where a fault *is* on disk,
`collect.py` parses it and labels it `PARSED FROM A FAULT ALREADY ON DISK` — that
is parsing, never proof that the producer records such faults.

A `TimeoutError: manager startup snapshot` or `manager shutdown observation` is
a **real timeout of something else**. Report it as that. It is not publication
evidence, and a reader that treats it as such invents a cause — the defect
`decisions/review-339861.md` found in revision 6. A fault in an artifact that
correlates to **another run** is not evidence about this one either.

What *is* available: a temporary belonging to **that** artifact, with no final
path, shows **its** publication was entered and did not complete. That is a fact
about progress, not about cause — and it must be that artifact's **own**
temporary. `outcome.json.partial` is the workload's (`baseline.py:1006`);
`outcome.json.enforcement-<pid>-<ns>.tmp` is the controller's. Revision 7 pooled
every `.tmp` in the directory and so reported four artifacts `pending` on the
evidence of one unrelated file, while never matching the workload's `.partial` at
all. Each artifact now sees only its own filenames.

**4. Prior observations survive, and one bad artifact costs you only itself.** An
unavailable final report retracts nothing already recorded — the authoring log,
the manager snapshots and the progress file remain exactly as good as they were.
And a malformed report is an observation about that report: a reader that aborts
on it throws away evidence that was perfectly readable.

And the rest, unchanged:

- A `state: held` controller report is an honest ending, not a failure to hide.
- When `enforcement-*.json` is unavailable, read `<outcome_path>` and
  `<status_path>.progress.json`, and report which of the three you reached,
  which you could not, and in which of the four states each one was.
- `shutdown_progress.step` tells you the last step **entered**, not that it
  finished.
- None of this is a token settlement, and none of it establishes that a
  container stopped.

## What a publication timeout does and does not guarantee

Revision 5 said the controller "returns 1 and writes nothing" on a publication
`TimeoutError`. **The first half is right and the second is false.** The code,
at `authoring_enforcement.py:586-594`:

```python
temporary = result.with_suffix('.tmp')
try:
    with bounded(report.get('shutdown_deadline', time.monotonic()), 'outer outcome publication'):
        temporary.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
        os.replace(temporary, result)
        print(json.dumps(report, sort_keys=True))
except TimeoutError:
    return 1
```

One `bounded(...)` block spans **all three** statements. So:

- a `TimeoutError` raised during `print` follows an **already-completed
  `os.replace`** — the final report **exists and is valid**, and only the stdout
  echo was cut;
- one raised during `write_text` can leave a **partial
  `.enforcement-*.tmp`** — which is a `pending`-looking artifact, not a result;
- one raised during `os.replace` leaves the complete temporary and no final
  path.

What the handler does guarantee is narrow and still worth having: **it does not
renew the publication budget and it does not manufacture a result.** It returns
1. No filesystem non-effect follows from that exception, so "the controller
timed out" never licenses "nothing was written", and the presence of a report is
not by itself proof that publication completed cleanly. Check for a `.tmp`
sibling before concluding anything.

**And note what the `except` clause does NOT do: it does not record the fault.**
`report` was the thing being written; the exception discards the attempt and
returns. So **no artifact anywhere carries "the outer publication timed out"**,
and nobody downstream can establish that cause from these files. That is a
property of the vehicle, not a gap in the collector, and the honest reading is
*unavailable, cause unknown* — with a partial `.tmp` as the only positive sign
that publication was entered at all.

`TASK.md` carries all of this into the turn's reporting obligation as item 6,
into revalidation item (e), and into the product axes: a diagnostic reader must
not turn an incomplete final report into an acceptance, nor a deadline-bounded
publication failure into cessation evidence, nor an unavailable report into a
named cause.

## What this packet does NOT do with it

- It does **not** run any product test at all this claim. The proof is
  **reused**:
  `decisions/shutdown-review.md`, 44 tests with no skips in 72.891s unittest
  time under authority338596, plus the six-path integration record. PLAN
  directs exactly that, and the direct exception that authorized those runs
  expired at acceptance.
- It does **not** put `tests.manager.test_authoring_shutdown_deadline` in the
  sealed gate. **51.333s for 4 real-process tests**, which exceeds the
  composer-fixed 30-second ceiling on its own. Excluded for the ceiling, not for
  coverage, and this candidate edits none of the three corrected files. That
  figure was measured by direct host product execution at **claim339421,
  outside that claim's preparation-only boundary** — `PROVENANCE.json`'s
  `execution_boundary_correction` and `PROGRESS.md` record the error — and it
  was **not** re-measured at claim339628, because re-running it to tidy its
  provenance would repeat the same mistake.
- It does **not** claim the correction makes a 3600-second run possible. The
  enforcement correction made the initial lease real; this one made the
  **ending** bounded and its reports honest. Neither extends it.
  **AMENDED AT CLAIM348718:** the 900-second limit itself was superseded by
  W333485's independently accepted host permission correction, which
  owner348699 closed satisfying — permission now derives from the persisted
  envelope, with execution stop at origin + 4740 and expiry at origin + 4800.
  See `decisions/host-policy.json`. That changes the allowance, not one word of
  this document's rules about what a bounded ending publishes.
