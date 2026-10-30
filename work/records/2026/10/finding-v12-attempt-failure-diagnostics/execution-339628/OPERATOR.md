# Owner operations — W333486 execution packet, revision 6

**`COMMANDS.md` has the six exact commands with no placeholders.** This
document is what each one does and what to expect. Read both.

**Step 5 is new and it is yours.** Post-run collection of the three final
results belongs to you and to the reviewer, not to the worker inside the run —
it is published after that worker is gone and cannot be asked for it. Revision 5
asked anyway; `collect.py` is the correction, executable.

**The start is NOT SELECTED.** Every input gate this Work had is closed —
W333735 at `a9f4fa4d`, W334910 at `fb487979`, W338305 at
`bc925cf5c62d69426ed5862af4d41f4d2a967b0f`, and the W337955 scheduling edge
removed at339410 as fulfilled. That is not a start. What remains is independent
preparation review and then an exact execution selection. Steps 0 to 3 are
authorized preparation and produce no execution.

**Three things that will bite you if you skip the rest:**

1. **Do not use `commands.json`'s `start`.** The accepted composer still
   generates the unenforced supervisor invocation. Use step 4 /
   `packet/AUTHORING-COMMAND.json`.
2. **Do not expect a 3600-second run.** `tokens.LIFETIME_SECONDS` is still 900
   and renewal is not in this base. The two corrections make that lease
   *enforced* and its *ending* bounded — neither makes it longer.
3. **A missing or partial final report is incomplete, not success — and it
   names no cause.** Absent, inaccessible, pending and unknown-cause are four
   different facts; a publication timeout is named only on a `TimeoutError`
   fault actually read in a correlated report. Run `collect.py` (step 5) rather
   than eyeballing a directory listing: it keeps those states apart for you.

Nothing below has been executed against the selected root. Preparation was
exercised once into `/tmp/w333486-preflight-339628`; the proposed root
`/home/sl/baton-instances/attempt-diagnostics-w333486-339628` is untouched and
**does not exist**, no Job is submitted, no engine or container was invoked, no
provider was contacted, no credential was read, **and no product test was run**.

This packet **supersedes `../execution-333504`, `../execution-333707`,
`../execution-334663`, `../execution-337453` and `../execution-339421`**, all
preserved unchanged. The failed instance at
`/home/sl/baton-instances/attempt-diagnostics-w333486-334663` is preserved and
is **never reused, rerun or recovered**.

## Why revision 6 exists

`../execution-339421` was independently reviewed, **all 31 seals verified, and
no launch was recommended**: `review-2026-10-20T14-56-51Z.md` requested four
bounded corrections first. Its vehicle pins are **identical** to this packet's —
controller `d12769df…`, baseline `8e5987f5…`, helper `af9e5ea6…`, base
`bc925cf5`, 114 manager files. Nothing drifted. Four documents were wrong:

1. **It asked the worker inside the run to report the run's own final results.**
   It cannot. The controller publishes after `supervise_process` returns and
   after child cleanup; the supervisor publishes post-stop. Both land after the
   worker's own termination, and a worker killed at the 900-second expiry cannot
   run a final-report instruction. **Now:** step 5 and `collect.py` are yours and
   the reviewer's; the worker reports what it observed before termination plus
   the retained candidate checkpoint.
2. **It read an absent enforcement report as a publication timeout**, and said
   the controller "writes nothing" on a publication `TimeoutError`. Both false —
   see step 5 and `SHUTDOWN.md`.
3. **The previous claim ran product tests directly on the host**, outside a
   preparation-only boundary, and then reported "re-runs 0" beside the numbers.
   Corrected additively in `PROGRESS.md`; the numbers are carried with that
   attribution and were **not** re-measured. This claim ran none.
4. **It banned two sibling-declared files outright.** Replaced by actual overlap
   declaration and serial reviewed integration.

So revision 6 is a **document correction at the same accepted base**, not a
rebase. `decisions/review-339623.md` is pinned inside the packet as the
authority, and `decisions/FINDING.md` and `decisions/PLAN.md` were re-taken
because the reviewer moved them after revision 5 was sealed.

## Step 0 — read-only input check

Opens no store, writes nothing, starts nothing. **Run this first.**

It separates **refusals** — base bytes, the 114 pinned manager files, the
pinned corrected controller and the pinned shutdown helper (each checked against
the pin, the packet's manager source *and* the base), the bootstrap binary, a
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

Measured here: 0.162s, clean, 21 task inputs, 16 decision snapshots, no drift.

`probe.py --work <fresh /tmp dir>` re-runs all thirty refusal and collection
cases in about 1.5 seconds if you want the refusals demonstrated rather than
described. It writes only under that directory.

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
The preflight's uuid `bfb4e65b12e5464984b5f56888cd9ca5` and packet digest
`7dc81cc9…` are facts about the throwaway root, not proposed production
identities.

## Step 3 — bind

Composes the packet documents under `<root>/packet/`, proves them
(`held_packet` re-pins every artifact including all 21 `fixture.files`;
`verify_imported_sources` proves the process is running the staged code),
refuses a root that already holds a composed packet, and writes
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

1. **The previous start failed in 0.506s.** Two managers for one workspace;
   `hold_manager_instance` correctly refused. Corrected — but **no authoring
   invocation has ever completed for this Work**, and two corrected failures are
   not evidence that a full invocation completes. If this one also fails, the
   honest account of how far it got is the deliverable, and the failed instance
   is preserved rather than retried.

2. **The 900-second lease is enforced, not extended.** Expect expiry at 900
   seconds with cessation ordered, partial output retained and a held outcome.
   `TASK.md` item 6 asks the turn for its retained candidate checkpoint, its
   progress per item and the expiry and cessation facts **it positively observed
   from inside** — and explicitly forbids it from reporting the three host-side
   final results, which it cannot see. Those are step 5, and they are yours.

3. **The verification ceiling is 30 seconds and is not this packet's to set.**
   The ten gate modules measure 13.642s (1124 tests, zero skips), leaving
   ≈16.36s for the two the turn must write. That fit **remains unproved**, and
   no coverage may be removed to force a pass. Two real-process modules are
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
   slice that fits 900 seconds with the remaining work stated explicitly — but
   not weakening final acceptance, and not promising full completion in one run.

## Step 5 — after a run: the collection is yours

Run `collect.py` (`COMMANDS.md` step 5a) before concluding anything. It is
read-only — no store opened, nothing written, nothing started, no credential,
transcript or provider output read — and it reports, for the workload report,
the controller report, the shutdown progress file and the authoring log:

- the **state**: present, or one of `absent`, `inaccessible`, `pending`,
  `unknown-cause`. These are four different facts. Do not collapse them.
- any **`.tmp` siblings**, because a publication that was entered and did not
  complete leaves one — and because a `TimeoutError` during the controller's
  `print` follows an **already-completed** `os.replace`, so a present report is
  not proof that publication finished cleanly.
- the **identity correlation** against the composed `run_id`: `matched`,
  `mismatch` or `unresolved`. A report naming another run is evidence about
  another run.
- `publication_timeout.established`, which is **false** unless it actually read
  a `TimeoutError` fault in a correlated report. Honour that. This Work's one
  real execution left no workload outcome at all because it died at startup in
  0.506s; a reader that called that a publication timeout would be inventing
  one. `collect.py` was exercised against the read-only copies of exactly that
  evidence and reports `false`.

`SHUTDOWN.md` has the rest: a missing or partial report is incomplete, never
acceptance and never proof of cessation; an unavailable report names no cause;
phase evidence names the last step *entered*, not finished; and an unavailable
final report retracts nothing already recorded.

Join the worker's report to yours on `run_id`. The worker's half covers what it
saw before termination and the retained candidate; yours covers everything
published after it ended. **The acceptance needs both halves**, and neither is a
substitute for the other.

The retained proposal is immutable and is **not** an accepted candidate. An
independent reviewer consumes it through v11 after exact runtime cessation; no
automatic integration, no self-acceptance. A failed or partial run is preserved
and reported with its evidence rather than retried silently. Parent W325959
consumes this jointly with W333485, and the human Git checkpoint the parent PLAN
carries remains pending.

## Retained temporary paths

Left in place for you rather than removed. None is a selected root; none holds a
credential or a submitted Job.

- `/tmp/w333486-preflight-339628` — this revision's exercised preparation root
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

The **failed selected run** is not in this list: it lives at
`/home/sl/baton-instances/attempt-diagnostics-w333486-334663` and is preserved
as evidence, not as a temporary path.
