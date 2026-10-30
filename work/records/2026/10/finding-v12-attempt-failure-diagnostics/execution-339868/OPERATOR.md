# Owner operations — W333486 execution packet, revision 7

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
exercised once into `/tmp/w333486-preflight-339868`; the proposed root
`/home/sl/baton-instances/attempt-diagnostics-w333486-339868` is untouched and
**does not exist**, no Job is submitted, no engine or container was invoked, no
provider was contacted, no credential was read, **and no product test was run**.

This packet **supersedes `../execution-333504`, `../execution-333707`,
`../execution-334663`, `../execution-337453`, `../execution-339421` and
`../execution-339628`**, all preserved unchanged. The failed instance at
`/home/sl/baton-instances/attempt-diagnostics-w333486-334663` is preserved and
is **never reused, rerun or recovered**.

## Why revision 7 exists

`../execution-339628` was independently reviewed, **all 34 seals verified, and
no launch was recommended**: `review-2026-10-20T15-38-05Z.md` found **four
correctness defects in `collect.py`**, the very program revision 6 added to make
your half of the collection executable. Its vehicle pins are identical to this
packet's; nothing drifted. The defects:

1. **A present workload report was reported `absent`** — the display label was
   used as a filename, so the artifact most likely to exist was the one
   guaranteed to be misread.
2. **Correlation demanded a top-level `run_id`** that the controller report does
   not publish; its identity is `original_envelope` (`run`, `job`, `authority`).
   Every real controller report came back `unresolved`.
3. **Any `TimeoutError` counted as a publication timeout**, so
   `TimeoutError: manager startup snapshot` "established" one.
4. **A JSON-array report aborted the whole collection** with an
   `AttributeError`, losing evidence that was perfectly readable.

All four are fixed, all four are regression probes, and the reviewer's own
fixtures are pinned at `decisions/collector-probes-339847.json` — so you can check the before and after
yourself. The claims in `TASK.md`, `SHUTDOWN.md` and step 5 are narrowed to what
the artifacts actually support, including the one that matters most for reading a
failed run: **an outer publication timeout is not establishable from these files
at all**, because the controller's own handler returns 1 without recording it.

Two things are also genuinely new rather than merely fixed: the **manager status
snapshot** is collected as a fifth artifact, and `--expect-run` lets you
correlate over a **retained evidence copy**, which holds the published artifacts
but not the composed `PACKET.json`.

So revision 7 is a bounded correction to the external-collection half at the same
accepted base — the third consecutive packet on the same vehicle.

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

Measured here: 0.115s, clean, 23 task inputs, 18 decision snapshots, no drift.

`probe.py --work <fresh /tmp dir>` re-runs all **forty-one** refusal and
collection cases in about 1.7 seconds if you want them demonstrated rather than
described — including the four that caught the previous collector. It writes only
under that directory.

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
The preflight's uuid `050856a96def40d081c55725f69a9558` and packet digest
`b73deb40…` are facts about the throwaway root, not proposed production
identities.

## Step 3 — bind

Composes the packet documents under `<root>/packet/`, proves them
(`held_packet` re-pins every artifact including all 23 `fixture.files`;
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
transcript or provider output read — and it reports, for five artifacts (the
workload report, the controller report, the shutdown progress file, the manager
status snapshot and the authoring log):

- the **state**: present, or one of `absent`, `inaccessible`, `pending`,
  `unknown-cause`. Four different facts. Do not collapse them. `available` names
  what was actually read; `isolated_failures` names anything that went wrong
  inside one artifact without costing you the rest.
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
- any **`.tmp` siblings**, because a `TimeoutError` during the controller's
  `print` follows an **already-completed** `os.replace` — so a present report is
  not proof that publication finished cleanly.
- `publication_timeout`, which is `established: false` unless it read a fault
  naming a **publication step** in a **correlated** artifact. Other timeouts
  appear as `other_timeouts_observed` (real timeouts of other steps — not
  publication evidence) and `uncorrelated_timeouts` (evidence about another
  run). And read `outer_publication_limit`: **an outer publication timeout is
  not establishable from these files at all**, because
  `authoring_enforcement.py:592-595` returns 1 without recording its own fault.
  Its absence is expected and proves nothing either way.

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

- `/tmp/w333486-preflight-339868` — this revision's exercised preparation root
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
