# Owner operations — W341357 producer slice — FRESH IDENTITY, VERIFICATION FIRST

**`COMMANDS.md` has the six exact commands with no placeholders.** This
document is what each one does and what to expect. Read both.

**This packet is a fresh identity for an already-accepted preparation.**
`../execution-341637` was independently accepted and you selected it once; that
invocation failed provider authentication in 10.56 seconds with no work
attempted. Its root now exists and holds a composed packet, so its commands
cannot be re-run: `stage` refuses an existing root and `bind` refuses a second
composition, both demonstrated by probes that were already in the packet. Only
the run id, the root and the resultant seal differ here. `PACKET.md` has the
exact list of what changed.

**Step 5 is yours.** Post-run collection of the final results belongs to you
and to the reviewer, not to the worker inside the run — it is published after
that worker is gone and cannot be asked for it. `collect.py` is executable.

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

Nothing below has been executed against the proposed root. Preparation was
exercised once into `/tmp/w341357-preflight3`; the proposed root
`/home/sl/baton-instances/durable-capture-w341357-345039` is untouched and
**does not exist**, no Job is submitted, no engine or container was invoked, no
provider was contacted, no credential was read, **and no product test was run**.

This packet **rebinds `../execution-341637`** and supersedes it as an identity
only. Its 48-member seal still verifies, its task and recovery bytes travel
here verbatim, and its failed root is preserved as evidence. Every earlier
packet — the nine parent ones and `../execution-341360` — stays sealed and
unchanged, and **all five instance roots are preserved: never reused, rerun,
recovered or re-bound.**

**The owner reports** that the Claude login and `just providers-check`
completed on 2026-10-21, which clears the prerequisite the review named. That
is owner-reported operational evidence: this packet repeated no check, probed
no provider, read no credential value and substituted no reference, and it does
**not** promise the session will still be valid when you select a start.

## Why this packet exists — and what has gone wrong four times

| run | provider served | ended | result |
| --- | --- | --- | --- |
| parent run340016 | 869.45s | on its own | candidate `433692c5` retained, **`verification-failed`**, independently **rejected** |
| parent run340352 | 904.78s | lease, signal 15 | **nothing frozen** |
| run341360 | 905.18s | lease, signal 15 | **nothing frozen** |
| run341637 | 10.56s | **provider authentication failure** | **no work attempted**; the turn never began |

**One retained candidate, zero accepted. Four runs, zero measurements of this
slice's gate.** Provider served ≈2690s; controller elapsed ≈2777s — separate
figures, since controller elapsed includes its own bounded shutdown, cleanup
sweeps and publication.

The fourth run says nothing about the lease or the scope: it ended before any
work began, on the provider's own supported `authentication_failed` diagnostic.
Nothing was lost, and nothing about the preparation needed changing — which is
why only the identity changed.

`review-2026-10-20T19-50-05Z.md` confirmed the blocker: **repeated provider
turns exhaust the 900-second lease before reaching supported completion.** It is
not scope — the scope was already bounded by decomposition and the failure
recurred. It also corrected two of my own claims, and both corrections matter to
what you are selecting:

1. I wrote "zero frozen candidates". The campaign has **zero ACCEPTED
   candidates, not zero retained** — run340016 retained `433692c5`.
2. I wrote that the slice was "very nearly finished", supported by line counts
   and 62 test-case names. **That was not established.** `_authorizes`, the
   versioned read API and all 62 cases are **unverified**, and the five-module
   gate has **never been measured in any run**.

So this packet is **verification-first**, not more authoring:

- **step 1** apply the pinned recovery from run341360's partial bytes;
- **step 2** **run the focused gate before any design or test expansion** — the
  first real measurement this slice has ever had;
- **step 3** fix only **demonstrated** acceptance failures;
- **step 4** stop optional edits at **600s**, end the provider turn by **720s**,
  preserving **≥180s** of the lease.

**The cutoffs reach the worker.** `COMPLETION.md` is a new pinned task input
that names the actual supported completion mechanism read from the current
protocol — the provider process returning is the only trigger; the adapter then
measures, verifies, revalidates, commits the line whatever the disposition is,
and publishes `/output/output.json` last and atomically as the completion signal
— so **ending the turn IS freezing, there is nothing to submit twice**, and none
of it happens if the lease kills the turn first. `prepare.py` and
`verify-inputs.py` refuse if that document is absent or is not a task input, and
probes cover both refusals.

**These are planning cutoffs inside unchanged limits**: no lease change, no
renewal, no controller modification, no automatic termination, and no
authorization to fabricate success.

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

Measured here: 0.12s, clean, **41** task inputs, **31** decision snapshots,
**4** pinned recovery inputs, **1** gate module still owed, **no drift** —
after re-taking the `FINDING.md` and `PLAN.md` snapshots, which the reviewer
updated after `../execution-341637` was sealed.

`probe.py --work <fresh /tmp dir>` re-runs all **fifty-five** refusal and
collection cases in about 2.2 seconds if you want them demonstrated rather than
described — including **both** reviewers' fixture sets, the seven cases that
caught this collector wrong twice, and the two that prove the old root cannot
be reused (`existing-root`, `rebind-over-a-composed-packet`). It writes only
under that directory. It derives the run id from `prepare.py`, so it followed
this rebinding without being edited.

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
(`held_packet` re-pins every artifact including all 41 `fixture.files`;
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

1. **Two selected starts have failed and neither ran.** `execution-334663`
   died 0.506s into startup — two managers for one workspace, which
   `hold_manager_instance` correctly refused, since corrected — and
   `execution-341637` failed provider authentication at 10.56s. **No authoring
   invocation has ever completed for this Work.** Corrected failures are not
   evidence that a full invocation completes. If this one also fails, the
   honest account of how far it got is the deliverable, and the failed instance
   is preserved rather than retried.

2. **The 900-second lease is enforced, not extended.** Expect expiry at 900
   seconds with cessation ordered, partial output retained and a held outcome.
   `TASK.md` item 6 asks the turn for its retained candidate checkpoint, its
   progress per item and the expiry and cessation facts **it positively observed
   from inside** — and explicitly forbids it from reporting the host-side final
   results, which it cannot see. Those are step 5, and they are yours.

3. **The verification ceiling is 30 seconds and is not this packet's to set.**
   The gate here is **five focused producer modules, and it has never been
   measured in any run.** The 13.642s / 1124-test figure is the parent's
   twelve-module argv, carried as context only, leaving ≈16.36s on paper for
   the one module the turn must create. That fit **remains unproved**, and
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

- `/tmp/w341357-preflight3` — this revision's exercised preparation root
- `/tmp/w341357-probe-345039` — this revision's fifty-five probe copies, roots
  and fixtures
- `/tmp/w341357-preflight2`, `/tmp/w341357-preflight` — the two previous
  revisions' exercised roots
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

The **failed selected runs** are not in this list. They live at
`/home/sl/baton-instances/attempt-diagnostics-w333486-334663` (startup failure)
and `/home/sl/baton-instances/durable-capture-w341357-345039` (authentication
failure), alongside the three cut-off or completed runs, and all of them are
preserved as evidence rather than as temporary paths.
