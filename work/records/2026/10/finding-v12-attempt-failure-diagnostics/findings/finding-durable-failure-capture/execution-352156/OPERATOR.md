# Owner operations — W341357 — BIND THE SUPERVISOR THE CONTROLLER RUNS

**`COMMANDS.md` has the six exact commands with no placeholders.** This
document is what each one does and what to expect. Read both.

**The run you selected refused at startup, and this time the defect was mine.**
You selected `../execution-350529` and it was launched once. The corrected
115-member binding worked — the import that killed run348852 resolved — and the
controller refused two statements later:

```
SupervisorRefusal: this process is running
'<root>/code/v12/python/tools/authoring_baseline.py' and the packet binds
'<root>/supervisor/baseline.py'
```

`verify_imported_sources` asks whether the module it is defined in **is** the
program the packet binds, before any store is opened. The old controller
imported a top-level `baseline` from the staged `supervisor/` directory, so the
two agreed; the accepted controller imports `tools.authoring_baseline` from the
manager source, so they no longer did. **The two files are byte-identical** —
only the path equality failed. `prepare.py`'s `bind` passed the wrong one of two
identical files, and that is a composition argument of this packet, not the
supplier's artifact and not the accepted controller.

**Nothing was reached**: no envelope, no Job, no attempt, no runtime, no token,
no container, no provider call. `instance/db` holds only the `authority.sqlite3`
that step 2 wrote. Nothing was ordered, so there was nothing to clean. The root
is preserved and the selection is consumed.

**So this packet is one argument, two refusals, and the proof.** `bind` composes
the staged `tools/authoring_baseline.py`, refuses anything else, and verifies
through the module the controller runs. Then `main`'s first three statements
were run against the composed packet at the run's own depth: **all three
accept**, and the same check against the failed packet **reproduces the exact
refusal**. `PACKET.md` has the full list of what changed and what did not.

**What that proof is not.** It stops at `main`'s next statement — the authoring
lock — so it does **not** establish that the controller starts, that the
provider session is valid, that a Job is admitted or that a turn completes.
Three selected invocations in a row have now failed at startup; this closes the
one window all three were in, and claims nothing beyond it.

**The producer work is unchanged and still owed.** R1 and R2 — the
fresh-versus-replayed observation and the discarded recording degradation — then
the complete five-module gate with no skips and the extended report.
`FIXTURE.md` carries the diagnosis with file-and-line citations.

**Step 5 is yours.** Post-run collection of the final results belongs to you
and to the reviewer, not to the worker inside the run — it is published after
that worker is gone and cannot be asked for it. `collect.py` is executable.

**The start is NOT SELECTED.** Every input gate this Work had is closed —
W333735 at `a9f4fa4d`, W334910 at `fb487979`, W338305 at
`bc925cf5c62d69426ed5862af4d41f4d2a967b0f`, W333485 and W348979 both closed
satisfying. Owner352153's invocation is **consumed**. What remains is
independent review of this correction and then a new exact selection. Steps 0
to 3 are authorized preparation and produce no execution.

**Three things that will bite you if you skip the rest:**

1. **Do not use `commands.json`'s `start`.** The accepted composer still
   generates the unenforced supervisor invocation — and since this claim it
   generates it with the *new* supervisor path, because it builds that argv
   from `packet['supervisor']['path']`. Still unenforced, still forbidden. Use
   step 4 / `packet/AUTHORING-COMMAND.json`.
2. **The 900-second lease is gone, and a 3600-second provider turn is now
   within permission.** Permission derives from the persisted envelope:
   **execution stop at origin + 4740**, **expiry at origin + 4800**, latest
   full admission origin + 1110. `decisions/host-policy.json` is the authority,
   not this sentence. It is still not a *promise* of a long run, and existing
   tokens keep their old policy.
3. **A missing or partial final report is incomplete, not success — and it
   names no cause.** Absent, inaccessible, pending and unknown-cause are four
   different facts. Run `collect.py` (step 5) rather than eyeballing a
   directory listing. Over run350529 it reported **all six artifacts absent**,
   which is correct and names no cause — the cause is the SupervisorRefusal.

Nothing below has been executed against the proposed root. Preparation was
exercised once into `/tmp/w341357-preflight11`; the proposed root
`/home/sl/baton-instances/durable-capture-w341357-352156` is untouched and
**does not exist**, no Job is submitted, no engine or container was invoked, no
provider was contacted, no credential was read, **and no product test was run**.

This packet supersedes `../execution-350529` **for one composition argument**.
That packet's 78-line seal still verifies, its root is preserved, and its
binding consumption, documents and worker bytes travel here unchanged. Every
earlier packet stays sealed, and **all ten instance roots are preserved: never
reused, rerun, recovered or re-bound.**

**No credential was read, no provider probed and no reference substituted.** The
last provider authentication was run345822's, which served 733.29 seconds;
run348852 and run350529 never reached a provider.

## Why this packet exists — the record

| run | provider served | ended | result |
| --- | --- | --- | --- |
| parent run334663 | — | **startup failure, 0.506s** | single-manager exclusion refusal; nothing ran |
| parent run340016 | 869.45s | on its own | candidate `433692c5` retained, **`verification-failed`**, independently **rejected** |
| parent run340352 | 904.78s | old lease, signal 15 | **nothing frozen** |
| run341360 | 905.18s | old lease, signal 15 | **nothing frozen** |
| run341637 | 10.56s | provider authentication failure | no work attempted; the turn never began |
| run345039 | 461.10s | on its own | candidate `1599471c` retained; **first gate measurement**: 864 tests, 12.817s, exit 1 |
| run345388 | 789.14s | on its own | candidate retained; **second gate measurement**: 864 tests, 12.515s, exit 1, 16 subtest errors, all `database or disk is full` |
| **run345822** | **733.29s** | **on its own, settled and completed** | **candidate `e9d292ed` retained; THE GATE PASSED — 864 tests, 12.631s, OK, exit 0, no skips.** This packet's input |
| run348852 | — | **startup failure, ≈2s** | `ImportError` on `tools.authoring_baseline`; the binding defect W348979 corrected |
| run350529 | — | **startup refusal, ≈2s** | `SupervisorRefusal` on the supervisor path; **the defect this packet corrects** |

**Three retained candidates, zero accepted. Three gate measurements, the last
one passing. Three startup failures, none of which reached a provider.**
Provider served ≈4673s across the campaign; controller elapsed ≈4764s —
separate figures, since controller elapsed includes the bounded shutdown,
cleanup sweeps and publication.

**The lease, the 30-second ceiling and the storage pressure are settled
questions.** `review-2026-10-21T15-30-10Z.md` confirmed the passing gate and
withheld product acceptance in the same breath: *"a passing gate lacking these
injections does not establish it."* The obstacle is no longer the environment —
it is the two producer defects, and they remain **one cohesive correction**.

So this packet's task, mirroring `TASK.md`'s ordered steps:

- **step 1** apply the retained candidate and confirm the gate is green before
  anything else;
- **steps 2–3** **reproduce** each defect at the production boundary — a
  deterministic failing demonstration — **before** correcting it;
- **steps 4–5** correct R1, then R2, without masking the original engine
  refusal, inferring cessation, or changing holds, fencing or cleanup;
- **step 6** run the **complete** five-module gate with **no skips**, and
  report counts and timing;
- **step 7** **extend** `W341357-VERIFICATION.json` — the existing channel in
  the candidate tree, because the provider transcript does not travel;
- **step 8** leave the adapter room before the execution stop, summarise, and
  let the provider return. **The 600/720 cutoffs are history.**

**R1 and R2 are OWED, green gate or not.** The gate passing in run345822 is
exactly why acceptance was withheld on the two producer defects instead: a
passing gate that never injects an outcome-write failure does not establish the
behaviour. Reproduce each one first, then correct it.

**The permission reaches the worker.** `COMPLETION.md` is a pinned task input
that names the actual supported completion mechanism read from the current
protocol — the provider process returning is the only trigger; the adapter then
measures, verifies, revalidates, commits the line whatever the disposition is,
and publishes `/output/output.json` last and atomically as the completion signal
— so **ending the turn IS freezing, there is nothing to submit twice**, and none
of it happens if the turn is still working when permission ends. It carries the
envelope-derived figures and records the old 600/720/180 cutoffs as history.
`prepare.py` and `verify-inputs.py` refuse if that document is absent or is not
a task input, and probes cover both refusals.

**What the permission is not**: not a renewal, not a controller modification,
not automatic termination, not a runtime guarantee, and not authorization to
fabricate success. Existing tokens keep their old policy and are not
converted.

## Step 0 — read-only input check

Opens no store, writes nothing, starts nothing. **Run this first.**

It separates **refusals** — base bytes, the 115 pinned manager files from the
corrected binding, **a binding that omits the controller's deferred
`tools/authoring_baseline.py` dependency**, the pinned corrected controller and
the pinned shutdown helper (each checked against the pin, the packet's manager
source *and* the binding), the bootstrap binary, a
damaged decision snapshot, an absent task input, a checkout document missing
from the base, an already-present gate module, a provenance claiming an
authorized or selected start, an absent `ENFORCEMENT.md` or `SHUTDOWN.md` —
from **reports**: a `DECISION-SOURCE DRIFT` section that exits 0, because the
turn reads immutable snapshots and an ordinary update to the reviewer-owned
`FINDING.md` or `PLAN.md` must not invalidate a sealed packet. **That is exactly
what happened to revision 5** and why reporting rather than refusing was the
right design: the reviewer appended to `FINDING.md` and rewrote `PLAN.md` after
it was sealed, the check reported the drift and exited 0, and this revision
re-took both snapshots.

Measured here: 0.06s, clean, **115** manager files,
**66** task inputs, **57** decision snapshots, **2** pinned
recovery inputs, **1** gate module still owed, **no drift** — after re-taking
`FINDING.md`, `PLAN.md`, `host-policy.json` and `host-operator-delta.md`, the
last two now pointing at the corrected W348979 artifact.

`probe.py --work <fresh /tmp dir>` re-runs all **sixty-one** refusal and
collection cases in about 2.381 seconds if you want them demonstrated
rather than described — including **both** reviewers' collector fixture sets,
the two that prove an existing root cannot be reused (`existing-root`,
`rebind-over-a-composed-packet`), and the ten that guard the retained-candidate
pins. **Not one probe needed editing this revision either**: the host-reading
mechanism is unchanged, so moving to the corrected binding changed no program
beyond its three constants. It writes only under that directory, and it derives
the run id from `prepare.py`.

**The new refusal is demonstrated separately, and deliberately not counted as
probe coverage.** Pointed at the exact 114-member binding run348852 staged,
both programs now refuse with *"the binding does not declare the deferred
controller dependency"*. Read-only, no root created, 0.02s, recorded in
`PREFLIGHT.json` under `the_deferred_dependency_guard`.

## Step 1 — stage

The `--acknowledge-unselected-start` flag is required and is not ceremony:
without it this refuses and prints why, including the startup failure. It proves
every base byte **before** creating anything, then creates the root `0700`,
refuses an existing one, and writes the base's manager and supervisor source
into it. A refused stage leaves the filesystem exactly as it found it — every
probe that could create a root also asserts whether the root was created.

## Step 2 — bootstrap this instance's own authority

`--no-repositories` is deliberate. It generates this instance's own authority
uuid, so **expect your composed packet digest to differ from the preflight's** —
`bind` derives the Work id from that uuid and it travels into the submission.
The preflight's uuid and packet digest are facts about the throwaway root, not
proposed production identities; `PREFLIGHT.json` records them.

## Step 3 — bind

Composes the packet documents under `<root>/packet/`, proves them
(`held_packet` re-pins every artifact including all 68 `fixture.files`;
`verify_imported_sources` proves the process is running the staged code **and
that the composed supervisor program is the module the controller runs** —
through that module, not the supervisor directory copy), refuses a root that
already holds a composed packet, **refuses a composed supervisor program that
is not the pinned `tools/authoring_baseline.py` member**, and writes
`<root>/packet/AUTHORING-COMMAND.json`. Ends with `PREPARED.json: state
prepared-not-executed, start_selected false, composer_start_is_unenforced
true`. **No Job is submitted.**

## Step 4 — start: NOT SELECTED YET

`packet/AUTHORING-COMMAND.json` carries exactly the step 4 command,
machine-readable, with the controller's and the shutdown helper's staged paths
and digests. The invocation is unchanged by either correction; `--status-path`,
`--child-of` and `--lock-fd` are internal, passed by the watchdog to the child.

Measured in preparation, read-only: the corrected controller's own
`verify_controller` **accepts** this packet from the staged source and
**refuses** one imported from the host checkout. A packet pinning the
**superseded** controller digest is refused before any root is created, and so
is one that fails to pin the shutdown helper.

`SIGINT`/`SIGTERM` sets the enforcement stop and begins the reserved cleanup
window; the controller requests the child's bounded shutdown by writing its
deadline, then terminates it, and reports `state: held`. **A held outcome is not
proof of cessation**, and a missing final status snapshot is also held.

Before starting, confirm the credential profile this packet names resolves in
your own private registry (`/home/sl/.baton/credential-sources.json`, slot
`claude`, reference `w202663-development`) and that the image reference is
available. This packet reads no credential, carries no bearer and contacted no
registry.

## Five things to know before a start is selected

1. **Three invocations have completed for this Work** — run345039 at 461.10s,
   run345388 at 789.14s and run345822 at 733.29s, all returning on their own.
   What remains true: **no invocation has ever produced an ACCEPTED
   candidate**, and **four** selected packets never produced a turn —
   `execution-334663` died 0.506s into startup, `execution-341637` failed
   provider authentication at 10.56s, `execution-348852` died at the
   controller's import in about 2s, and `execution-350529` was refused by the
   controller's startup verification in about 2s. **Three of those four were
   startup failures and none reached a provider.** If this one fails, the
   honest account of how far it got is the deliverable, and the instance is
   preserved rather than retried.

2. **Permission comes from the envelope now.** Execution stop at origin +
   4740 and expiry at origin + 4800, with cessation ordered at the end,
   partial output retained and a held outcome if it is reached. Replay does
   not reset origin and restart is cancellation-only.
   `TASK.md` item 6 asks the turn for its retained candidate checkpoint, its
   progress per item and the expiry and cessation facts **it positively observed
   from inside** — and explicitly forbids it from reporting the host-side final
   results, which it cannot see. Those are step 5, and they are yours.

3. **The verification ceiling is 30 seconds, it is not this packet's to set,
   it FITS, and the gate PASSES.** Measured three times on the same argv and
   the same 864 tests: 12.817s exit 1, 12.515s exit 1, then **12.631s, OK, exit
   0, no skips** in run345822. Both questions are closed. Two qualifiers:
   unittest's self-reported interval is not the adapter's whole wall clock, and
   **a passing gate is not acceptance** — which is why R1 and R2 are owed. No
   coverage may be weakened, deleted, relaxed or narrowed to keep it passing. Two real-process modules are
   excluded for measured ceiling reasons — `test_authoring_shutdown_deadline` at
   51.333s for 4 tests, over the whole ceiling by itself, and
   `test_authoring_manager_guard` at 19.888s for 7 — with their coverage carried
   by reused accepted proofs.

   **Where those numbers come from matters.** All of them were measured by
   direct host product test execution at claim339421, **outside** that claim's
   preparation-only boundary; `PROGRESS.md` carries the author's correction and
   `GATE-CHECK.json` the attribution. They were **not** re-measured here,
   because re-running them to tidy their own provenance would repeat the
   mistake. So two exclusion decisions rest on out-of-boundary measurements, and
   this packet says so rather than presenting them as preparation evidence.

4. **Two excluded test modules already fail at base**, both explicitly
   unverified baseline reports with no cleanup selected:
   `tests.manager.test_boundary_inventory` and `tests.tools.test_packaging`'s
   subcommand case, which holds the source command table against the installed
   bundle. A source-level case is **not** proof that a rebuilt bundle carries a
   new verb.

5. **A bounded first milestone is allowed.** PLAN permits delivering a coherent
   slice that fits the available permission with the remaining work stated
   explicitly — but not weakening final acceptance, and not promising full
   completion in one run. **R1 and R2 stay one cohesive correction**: the
   review is explicit that there is no new split after the separately accepted
   packaging child.

## Step 5 — after a run: the collection is yours

Run `collect.py` (`COMMANDS.md` step 5a) before concluding anything. It is
read-only — no store opened, nothing written, nothing started, no credential,
transcript or provider output read — and it reports, for five artifacts (the
workload report, the controller report, the shutdown progress file, the manager
status snapshot and the authoring log):

- the **state**: present, or one of `absent`, `inaccessible`, `pending`,
  `unknown-cause`. Four different facts. Do not collapse them. `available` names
  what was actually read; `isolated_failures` names anything that went wrong
  inside one artifact — **or inside one link** — without costing you the rest.
  **`pending` now means this artifact's own temporary exists**, never a sibling's:
  the workload writes `outcome.json.partial`, the controller
  `outcome.json.enforcement-<pid>-<ns>.tmp`, and they are not interchangeable.
- the **identity correlation**, through the fields each artifact really
  publishes, with `identity_detail.correlated_on` naming which one decided. The
  controller has **no top-level `run_id`** — it carries `original_envelope`
  (`run`, `job`, `authority`). A disagreeing field is a `mismatch` and the
  artifact is downgraded: it is evidence about another run.
- `linked_artifacts`: the paths the controller names **for itself** —
  `enforcement_path`, `authoring_log`, `manager_report_path` and
  `<manager_report_path>.progress.json` — and whether each was found. If the run
  root moved, those absolute paths will not resolve; that is a fact about your
  filesystem, not about the run.
- that artifact's **own temporaries**, because a `TimeoutError` during the
  controller's `print` follows an **already-completed** `os.replace` — so a
  present report is not proof that publication finished cleanly.
- `publication_timeout`, and read `producer_persistence` before the verdict:
  **this vehicle persists no publication fault reliably**, so
  `established: false` means *nothing on disk could tell you either way* and not
  *no timeout happened*. Step 5d has the per-step table and the reasons.
  `parsed_publication_faults` lists any publication-step fault that is literally
  on disk, each labelled as parsed rather than as producer evidence;
  `other_timeouts_observed` lists real timeouts of **other** steps, which are
  genuine observations and not publication evidence; `uncorrelated_timeouts`
  lists faults in artifacts about another run.
- `linked_artifacts` states, per link: `found`, `named but not present`,
  `inaccessible`, `malformed` (the report carried something that is not a path
  string — reported and **not** followed) or `not named by the report`.

Over a retained evidence copy rather than a live root, use `--packet-dir` plus
`--expect-run`: such a directory has no composed `PACKET.json`, so without it
every identity is `unresolved`. `--expect-run` is your assertion, labelled as
one in the output, and refused if it contradicts a packet that *is* readable.

`SHUTDOWN.md` has the rest: a missing or partial report is incomplete, never
acceptance and never proof of cessation; an unavailable report names no cause;
phase evidence names the last step *entered*, not finished; and an unavailable
final report retracts nothing already recorded.

Join the worker's report to yours on `run_id`. The worker's half covers what it
saw before termination and the retained candidate; yours covers everything
published after it ended. **The acceptance needs both halves**, and neither is a
substitute for the other.

## Retained temporary paths

Left in place for you rather than removed. None is a selected root; none holds a
credential or a submitted Job.

- `/tmp/w341357-preflight11` — this revision's exercised preparation root
- `/tmp/w341357-probe-352156` — this revision's 61 probe copies, roots and
  fixtures
- `/tmp/w341357-352156` — this revision's build scripts, probe report, the
  startup-verification check and its counterfactual against the failed packet
- `/tmp/w341357-preflight10`, `/tmp/w341357-probe-350529` and
  `/tmp/w341357-350529` — the previous revision's
- `/tmp/w341357-preflight9`, `/tmp/w341357-preflight8`,
  `/tmp/w341357-preflight7`, `/tmp/w341357-preflight6` and their probe trees —
  the previous revisions'
- `/tmp/w341357-preflight3`, `/tmp/w341357-probe-345039`,
  `/tmp/w341357-preflight2`, `/tmp/w341357-preflight` — previous revisions'
  exercised roots and probe trees
- `/tmp/w333486-probe-339628` — the thirty probes' copies, roots and fixtures,
  with `/tmp/probe-339628.json` as their report
- `/tmp/w333486-helper-probe-339628` — the staged source with
  `tools/authoring_shutdown.py` removed, which proves the import fails
- `/tmp/w333486-binding-339628.py` — the read-only both-ways controller binding
  check
- the previous revision's roots: `/tmp/w333486-preflight-339421`,
  `/tmp/w333486-base-339421` (the clean base export used for the
  out-of-boundary gate measurements), `/tmp/w333486-probe-339421`,
  `/tmp/w333486-helper-probe-339421`
- the earlier revisions' roots: `/tmp/w333486-preflight-337453`,
  `/tmp/w333486-probe-drift-453`, `/tmp/w333486-base-fb48`,
  `/tmp/w333486-preflight-334663`, `/tmp/w333486-probe-drift-663`,
  `/tmp/w333486-base-a9f4`, `/tmp/w333486-preflight-333707`,
  `/tmp/w333486-probe-drift-707`, `/tmp/w333486-base-probe`,
  `/tmp/w333486-preflight-333504`, `/tmp/w333486-probe-drift`

The **selected runs** are not in this list. All **ten** live under
`/home/sl/baton-instances/` — `attempt-diagnostics-w333486-334663` (startup
failure), `-340016` (completed, candidate rejected), `-340352` (cut off),
`durable-capture-w341357-341360` (cut off), `-341637` (authentication failure),
`-345039` (completed, first gate measurement), `-345388` (completed, second),
**`-345822` (completed; THE GATE PASSED and this packet starts from its
candidate)** `-348852` (startup failure: the import error, corrected by W348979) and
`-350529` (**startup refusal: the supervisor path this packet corrects**). All
are preserved as evidence rather than as temporary paths, and none is reused,
rerun, recovered or re-bound.
