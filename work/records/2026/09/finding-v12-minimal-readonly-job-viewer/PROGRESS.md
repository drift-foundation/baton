# Implementation progress — W167896

## Claim 167908 — the viewer, delivered

Three selected paths and nothing else. `git status` confirms only
`v12/python/tools/job_viewer.py`, `v12/python/tests/tools/test_job_viewer.py`,
`v12/python/JOB-VIEWER.md` and this dossier are new; no shared
`job_manager`/`stage_execution`/worker/provider/DEPLOYMENT file was edited, and
W161230 and W32577 files are untouched.

| path | bytes | mode | sha256 |
|---|---|---|---|
| `v12/python/tools/job_viewer.py` | 20270 | 644 | `e55b0d29e9f3d911e9df364c0f43c719d525fd726aaf9de67f9f85630f38f754` |
| `v12/python/tests/tools/test_job_viewer.py` | 16325 | 644 | `9eb06ca6ce754b18d63f78017fa6d24bbca21e1d84721d56104c9e5c219d5f6d` |
| `v12/python/JOB-VIEWER.md` | 4700 | 644 | `000b4ce5c629e6b55924695bb735ffde7adee7cab26f31e46db6e87c9b55aa4e` |

### What it is built on

`job_manager/projection.py:status` through `Unobserved()` -- the existing
public read-only path. There is **no second backend**: no SQL, no projection,
no observer, no serving factory. A test walks the module's AST and asserts the
import set is exactly `argparse, datetime, json, sys, time,
baton_v12.job_manager`, and that no `serve`/`submit`/`claim`/`cancel`/
`ControlStore`/`execute` identifier is used anywhere.

That check started as a text search and was **wrong**: the module docstring
says "no submit, claim, cancel, serve", so searching for `serve` found the
paragraph promising the absence. It now reads identifiers, not prose.

### The honesty rules, and the evidence they are load-bearing

- **Activity is `unknown`.** W61599 owns the trusted source; nothing here
  infers freshness from an empty stream or from the fact that polling returned.
- **Elapsed comes only from recorded source times** (`opened_at`/`ended_at`).
  A stage whose start nobody recorded reads `unknown` -- the alternative is
  measuring how long the *viewer* has been looking and printing it as how long
  the *Job* has been running.
- **The view never hides its own age.** `!! STALE` past 3x the interval,
  `!! DISCONNECTED` on a failed read with the last good reading kept *under*
  the warning, and `canonical: false` reported as "the manager was NOT read".

Reversal at step 41 disabled all three (elapsed falls back to zero, activity
reports `live`, staleness never triggers) and failed exactly
`test_activity_is_unknown_until_a_trusted_source_exists`,
`test_elapsed_comes_from_source_times_and_not_the_wall_clock` and
`test_an_unrefreshed_view_becomes_conspicuously_stale`; restored to OK at 42.

### Bounds

4 MiB snapshot input -- **refuses** rather than truncating, because a dropped
tail silently omits Jobs and an invisible Job is the failure this Work exists
to fix. 64 KiB locator reads on explicit detail only, visibly truncated, with
the locator taken **out of the snapshot** so there is no operand an operator
could point elsewhere. No idle log tail. These bound the display and change no
protocol limit.

### Focused results

`unittest tests.tools.test_job_viewer` -> **OK, 24 cases** (steps 40 and 42).
Covers two-Job identity isolation, exact identities, foreign-identity refusal,
unknown/stale/disconnect/reconnect, oversize and foreign-schema refusal,
bounded truncated locator reads, unavailable artifacts, the no-act traps, the
unchanged-store comparison, and the ordinary command path.

**Cost check** (`cost-167908.py`, `cost-167908.json`), 20 deterministic Jobs,
1 s polling, 60 s idle, 90 s outer timeout:

- **0.023 CPU-seconds including children over 60.0 s wall = 0.039 % of one
  core**, against a 0.6 s / 1 % target -- `meets_target: true`
- 60 refreshes, 0 failures, 39129-byte input document
- host `slryzen`, Linux 6.17.0-41-generic, CPython 3.13.7

Refresh latency is held **logically** rather than by stopwatch: a changed
observation is visible after exactly one tick
(`test_a_changed_observation_is_visible_on_the_next_tick`), so at 1 s polling
the worst case is 1 s, inside the 2 s target. Measuring it with wall time would
have proved only how busy the machine was.

### Two corrections worth recording

1. `JOB-VIEWER.md` first documented `job_manager.py --jobs ... --status`. The
   real CLI is `--store/--incarnation/--authority-uuid` with a `status`
   subcommand. Found by **running** the documented invocation end to end rather
   than asserting it; the doc now carries the command that works.
2. The blocked-stage reason printed the raw gate document
   (`{'stage_id': ..., 'open': False}`) on an operator's screen. It now reads
   `held: waiting on job-a/implementation (queued)`, and a test asserts the
   internals do not appear.

### Accounting note

The focused unittest runs were driven through the W161230 measured runner
(`/tmp/w166281_run.py`) out of convenience, so **steps 36-42 in
`ledger-166281-prospective.json` are W167896 runs recorded under W161230's
file**. The cumulative gate is removed (M166331) so nothing was gated by this,
but the attribution in that ledger is wrong and is named here rather than left
to be discovered. The 60 s cost measurements ran outside any ledger and are
recorded in `cost-167908.json`.

### Not done here

Rich telemetry (W39649), labels (W29408) and the trusted activity source
(W61599) remain separately owned. No missing observation capability was
encountered that would need a finding against W136578 or the current provider.

## Claim 168118 — the five corrections from review claim168071

All four independently reproduced failures are fixed, and each is held by a
case that fails when the fix is reversed (step 5: 3 failures + 15 errors across
exactly the corrected behaviours; restored at step 6).

**P1 — polling stale bytes reported them fresh.** `age_seconds` used only the
local read time and every refresh reset it, so re-reading one unchanged status
file forever said "read 0s ago" with no warning. A snapshot now carries **two
clocks**: when this program received the bytes, and when the manager actually
looked. Staleness is judged on the *observation*, and unknown observation age
is treated as stale — a view that cannot tell how old its facts are must not
present them as current. The threshold is now `max(2 s, 2 x interval)` instead
of a frozen 3 s that ignored `--interval` entirely.

**P1 — the canonical reader is now exercised.** Every earlier fixture used
`status(store, Unobserved())`. `TheCanonicalReaderIsExercised` drives the real
`projection.status` through a **canonical** operations surface with real
observations: no "nobody looked" warning, two-Job isolation, a model-free
**completed** stage (and its dependent unblocking), a held stage naming what it
waits on, and a no-act check against the surface's own recorded calls.
`JOB-VIEWER.md` now documents the concrete `status --control ... --observe ...`
invocation, including why `--observe` requires `--control` and why the runtime
axis is only as fresh as the serving loop.

**P2 — a malformed refresh no longer ends the view.** The read was inside the
handler and the *parse* was outside it, so a truncated document — which the
documented `>` redirection produces mid-replacement — escaped and exited the
command. Parsing is now inside the handler, a JSON list refuses instead of
raising `AttributeError`, and the last good view stays on screen under
`!! DISCONNECTED` with ordinary retries. The doc now recommends atomic
publication.

**P2 — drill-down is wired and uses locator semantics.** `main` gained
`--stage`/`--artifact`; selection walks **snapshot identities** rather than
accepting a caller's dict, `file:///...` is understood as a locator (it was
being opened as a literal filename), a relative reference is never resolved
against the viewer's cwd, and only a regular file opened `O_NOFOLLOW` is read.
Signature inspection was never evidence of permission and that check is gone.

**P2 — known worker and assignment identities are shown.** `stage.runtime`
supplies `runtime_id`, `execution_runtime` and the `assignment`
(`work_ref`/`participant`/`generation`), plus allocation; all render, with
`unknown` when genuinely absent. Detail no longer clips at 100 columns — that
cut the exact identifiers an operator opened the detail for.

Also: `--interval` must be finite and > 0 (zero was convenient in a test and is
not a reason to admit it in the command), and the loop no longer sleeps after
its final tick.

### Cost, corrected and scoped

`cost-168118.py` / `cost-168118.json`, driving the **selected adapter**
(`_source_from`) through parse, staleness and render: **0.025 CPU-seconds
including children over 60.0 s = 0.0409 % of one core**, child CPU 0.0 s, 60
refreshes, 0 failures, slowest source read 0.4 ms, 39129-byte input.

It **excludes canonical status production** — that is a separate command with
its own cost, and labelling this a whole-pipeline figure would claim more than
the harness supports. The earlier handoff quoted 0.023 / 0.039 % while the
retained file said 0.024 / 0.0407; the numbers above are this run's and the
file's.

### Verification record

Viewer runs now go in **this dossier** (`ledger-167908-viewer.json`), per the
attribution correction. W161230's ledger keeps its history unrewritten;
`verification-attribution-168071.json` records the 1.438459018987487 s of
misattributed steps 36–42.

- **Last runnable command:** `python3 /tmp/w167908_run.py 7 final
  /home/sl/src/baton/.venv/bin/python3 -m unittest tests.tools.test_job_viewer`
  (cwd `v12/python`) → **OK, 51 cases**, 0.254077 s
- **Candidate (all 0644):**
  - `tools/job_viewer.py` 31899 b `sha256:de60d8c9d75fdd7cbd3256b305b28b60dfff0ef6c7b292167144ce9be7f3d7c8`
  - `tests/tools/test_job_viewer.py` 34124 b `sha256:03e509ac497f7c595f70ad798fe54ed2dbad1260dbe289c7ad20771f461e1841`
  - `JOB-VIEWER.md` 7934 b `sha256:af44aa23bb43ea3537857d00c213ae9ec35b616630ee513070106c33301f73ec`

The documented drill-down was **run**, not asserted: it returns the artifact and
its bytes, and correctly reports the fixture's pinned 2026-09-02 observation as
297 h stale — the P1 fix against a real document.

Still not done: W61599 activity stays `unknown`; no shared provider, DEPLOYMENT
or W161230 file was touched.

## Claim 168213 — the four remaining corrections from review claim168169

**P1 — the real observation reader now reaches the view.**
`TheRealObservationReaderReachesTheView` subclasses the existing fixture the
review named (`TwoBoundJobsTraverseServingAndCorrection`) and renders a
snapshot produced by the actual `stage_execution.observation_from` +
`job_manager._Observing` path, under that fixture's own no-act traps on
`Authority.open/session`, `IntegrationStore.open`, `operations_from`,
`Integration.run/finish`, `activate_pool` and `create_line`. It asserts the
model-free completion (`job-b/integration` completed with no runtime), two-Job
binding and isolation, and that a foreign Job still refuses. Inherited parent
tests are unbound so the heavy suite is not re-run for no extra evidence.

The `FakeOperations` cases are **kept and relabelled**: their docstring now
says plainly that they are evidence about the projection and the formatter
driven with a *simulated* operations answer, and that the no-act check there is
against the fake's own calls rather than the real reader's owner boundaries.

`JOB-VIEWER.md` now names `tools.stage_execution:observing_factory` and its
`BATON_V12_STAGE_EXECUTION_CONFIG` input, and says explicitly that it is not
`tools.stage_execution:factory`, which is the serving one.

**P2 — the scheduler's real identities.** `_allocation` looked for
`allocation_id`/`name`/`root`/`capacity_id`, none of which the scheduler
publishes — and my fixture invented an `allocation_id`, so it passed while
missing the actual shape. The viewer now reads `stage_allocations`' own
columns (`assignment_id`, `worker_id`, `participant`, `lane`, `generation`,
`allocation_state`, `selection_outcome`) and shows the **reservation**
separately from the runtime's fixed assignment — a stage can be reserved on a
worker before any runtime exists. The regression uses a **real**
`scheduler.reserve` allocation.

**P2 — the configured threshold reaches rendering.** It was computed from the
interval and then rendered with the 1 s default, so `--interval 5` called a
three-second-old observation stale against a documented ten-second window. The
threshold is threaded through `render_list`/`render_detail`/`_banner` and the
run loop, and the case drives the **loop** rather than calling `stale_after`
directly — which is why the old case could not catch it. The comparison is now
inclusive, so the selected "within 2 s" boundary flags at 2 s rather than 3 s.

**P2 — disconnection recovery.** `{"schema": ..., "jobs": [null]}` passed,
replaced the last good snapshot, then raised `AttributeError` from the
renderer outside the handler. `_shaped` now validates the nested structure the
renderer walks — jobs, stages, episodes, artifacts, gates — before a document
replaces a good one. Detail mode distinguishes "no readable observation yet"
from a confirmed foreign identity, checked **before** the search, so a first
unreadable snapshot no longer exits; a connected snapshot genuinely lacking the
Job still refuses.

### Evidence

- **Last runnable command:** `python3 /tmp/w167908_run.py 19 restored
  /home/sl/src/baton/.venv/bin/python3 -m unittest tests.tools.test_job_viewer`
  (cwd `v12/python`) → **OK, 60 cases**, 3.103731 s
- **Reversal (step 18):** threshold not threaded, strict `>`, `_shaped`
  removed, detail's unavailable check disabled → 8 failures + 1 error across
  exactly the corrected behaviours; restored at 19. An earlier reversal (step
  14) failed only the allocation cases, which is how I found the threshold and
  nested-shape fixes had no coverage yet.
- **Candidate (all 0644):**
  - `tools/job_viewer.py` 37334 b `sha256:b375756441292d0d7376379e341b2a66143c504bd61daa7d1c37d5af502fe524`
  - `tests/tools/test_job_viewer.py` 48130 b `sha256:eb8ec32cc82b142d5681bb30fca91da8919453d158a38786ded6132e4f928759`
  - `JOB-VIEWER.md` 8680 b `sha256:25da47d3f7e3a58707222dc2263fb2c1abce8d81ba5fac6bd2cf8506a5af2761`

Viewer runs are recorded in `ledger-167908-viewer.json` (19 runs, 56.657772 s).
No 60 s cost rerun was needed; `cost-168118.json` stands. W61599 activity stays
`unknown`; no shared provider, DEPLOYMENT or W161230 file touched.

## Claim 168295 — the three remaining bounded corrections

**P2 — the drill-down used a different threshold.** `_drilled` called `_banner`
without `stale_seconds`, so a 3 s-old observation was fresh in the Job view and
`!! STALE` in its artifact view at `--interval 5`. One document cannot be two
ages. The configured threshold is now carried into `_drilled`, and the
regression drives the **command** at interval 5 and at 1 so the interval is
doing the work rather than the age alone.

**Documentation.** The surviving "3 x interval" sentence in the "It does not
hide its own age" paragraph is replaced with `max(2 s, 2 x interval)`, matching
the corrected contract stated elsewhere in the file.

**The artifact fixture is relabelled, and a real one is added.**
`TheDrillDownIsWiredAndUsesLocatorSemantics.published` writes a local file and
injects an artifact document with a made-up digest. Its docstring called that a
"real frozen output", which overstated it; it now says plainly that it is
synthetic, that it is useful for the locator *rules* (`file:///`, relative
refusal, non-regular refusal, truncation) because those are about the locator
and not about provenance, and where a real one lives. The
signature-inspection case is likewise relabelled as a helper-shape check
rather than evidence of manager permission.

`TheOwnerProducedArtifactReachesTheView` is the real one. It freezes a result
through `request_freeze`, reads the artifacts back through the manager's own
`frozen_output_of` — not the freeze call's answer — carries them through the
**real projection**, then selects by identity and reads bounded. The locator is
the worker's own, named in the sealed result, so the file the view reads is the
one the owner recorded rather than one the case pointed it at afterwards. A
third case removes that file and confirms the view reports unavailable instead
of producing content.

### Evidence

- **Last runnable command:** `python3 /tmp/w167908_run.py 25 restored
  /home/sl/src/baton/.venv/bin/python3 -m unittest tests.tools.test_job_viewer`
  (cwd `v12/python`) → **OK, 64 cases**, 3.187980 s
- **Reversal (step 24):** drop `stale_seconds` from `_drilled` and stop reading
  `file:///` as a locator → 3 failures + 2 errors, including the new
  owner-produced case; restored at 25.
- **A non-reversal I caught and redid:** step 22's reversal script had a
  quoting error, so it never applied and the suite passed against the
  unmodified file. A reversal that does not apply proves nothing, and reporting
  it as one would have been worse than not running it. Step 24 is the real one.
- **Candidate (all 0644):**
  - `tools/job_viewer.py` 37675 b `sha256:093ec72480e2c921ea657b0e63e7235d7dd5e27933762724132310b42447d356`
  - `tests/tools/test_job_viewer.py` 54786 b `sha256:bbbc6be5ffc35774654336a41f9d0c36182f013ae53feb3b14203ce0245b476b`
  - `JOB-VIEWER.md` 8688 b `sha256:d319f7813c826970eca6f49a5970f894805288754f31f30999d28d3cfbbb5976`

Viewer ledger: 25 runs, 75.538780 s. No 60 s idle repeat was needed and
`cost-168118.json` stands. W61599 activity stays `unknown`; no shared provider,
DEPLOYMENT or W161230 file touched.
