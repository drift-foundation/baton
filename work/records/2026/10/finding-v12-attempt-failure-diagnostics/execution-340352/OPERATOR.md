# Owner operations — W333486 execution packet, revision 9

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
exercised once into `/tmp/w333486-preflight-340352`; the proposed root
`/home/sl/baton-instances/attempt-diagnostics-w333486-340352` is untouched and
**does not exist**, no Job is submitted, no engine or container was invoked, no
provider was contacted, no credential was read, **and no product test was run**.

This packet **supersedes `../execution-333504`, `../execution-333707`,
`../execution-334663`, `../execution-337453`, `../execution-339421`,
`../execution-339628`, `../execution-339868` and `../execution-340016`**, all
preserved unchanged — and the eighth **actually ran**, so its instance and
retained candidate are preserved as evidence too. The failed instance at
`/home/sl/baton-instances/attempt-diagnostics-w333486-334663` is preserved and
is **never reused, rerun or recovered**.

## Why revision 9 exists — and it is not another correction loop

**The previous run worked.** You selected `execution-340016` at reroute340145; it
was prepared, preflighted through the real executor boundary, launched once, and
it **completed** — the first authoring invocation this Work has ever finished.
Docker worked, a worker container ran, and all four final results published.

What it returned is the reason for this packet. The turn produced 1621 insertions
across 8 files — including both owed test modules and a 619-line typed cause
reader — **its gate exited 1**, so it published no proposal and **retained a
candidate** at head `433692c5`. `review-2026-10-20T16-40-37Z.md` then rejected
that candidate with three static blockers:

1. **the production seam is not connected** — no `job_manager` file changed, so
   ordinary status cannot carry the new account and the report can only ever see
   a fixture;
2. **producer and report shapes disagree** — known values would arrive as
   unknown, and several composed facts are absent from the report entirely;
3. **the durable pre-effect intent is best-effort and silent** — four call sites
   discard the recorder's failure, two of them immediately before ordering an
   effect, and a historical *uncertain* outcome outranks a later *positive* one.

So this packet is a **continuation**: it pins the retained candidate patch by
digest as a task input, and `TASK.md`'s first instruction is to apply it and
correct those three things. It does **not** start from an empty tree —
the review is explicit that the candidate's accepted design and both test
modules are to be kept.

**Two things that are now settled facts rather than predictions.** The
900-second lease **did not fire**: the run ended on its own at 869.3s with 30.5
seconds of margin, so do not expect an expiry account this time either.
And the vehicle is now **proven end to end**, which four earlier packets could
only assert.

**One thing is newly a deliverable.** The gate has been run once on real work and
exited 1 with its output withheld by design — it ran with the credential mount
readable. A generated line in `candidate-verification.txt` suggests you rerun it
on the host; the review is explicit that this is **not authority**, and the
author accepts that. `TASK.md` item 7 therefore requires the next turn to run the
gate itself and report which modules failed, the per-module seconds against the
30-second ceiling, and whether that ceiling was material — which finally answers
the fit question this campaign has carried unproved since revision 2.

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

Measured here: 0.117s, clean, 31 task inputs, 24 decision snapshots, 1 pinned
retained candidate patch, no drift.

`probe.py --work <fresh /tmp dir>` re-runs all **fifty-two** refusal and
collection cases in about 2.1 seconds if you want them demonstrated rather than
described — including **both** reviewers' fixture sets, the seven cases that
caught this collector wrong twice. It writes only under that directory.

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
The preflight's uuid `13f568a2178d49048edfab16b070e4a7` and packet digest
`92d48dd3…` are facts about the throwaway root, not proposed production
identities.

## Step 3 — bind

Composes the packet documents under `<root>/packet/`, proves them
(`held_packet` re-pins every artifact including all 31 `fixture.files`;
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
   from inside** — and explicitly forbids it from reporting the host-side final
   results, which it cannot see. Those are step 5, and they are yours.

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

- `/tmp/w333486-preflight-340352` — this revision's exercised preparation root
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
