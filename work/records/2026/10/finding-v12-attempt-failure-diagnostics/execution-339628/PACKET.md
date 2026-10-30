# W333486 execution packet, revision 6 — sealed preparation at `bc925cf5`

`baton.claude`, claim339628, role `impl`. **Preparation only.** No Job
submitted, no attempt, no runtime, no engine, no provider, no credential read,
no Git mutation, no host product or test edit, **and no product test executed**
— which is itself one of the four corrections this revision carries. **The start
is not selected.**

| | |
| --- | --- |
| base | `bc925cf5c62d69426ed5862af4d41f4d2a967b0f` |
| proposed run | `attempt-diagnostics-w333486-339628` |
| proposed root | `/home/sl/baton-instances/attempt-diagnostics-w333486-339628` — **absent** |
| supersedes | `../execution-333504`, `../execution-333707`, `../execution-334663`, `../execution-337453`, `../execution-339421` — all preserved, all seals still verifying |
| start | `start_authorized: false`, `start_selected: false` |
| exact commands | `COMMANDS.md` (six, no placeholders; step 5 is the operator's post-run collection) |
| vehicle pins | **unchanged from revision 5** — controller `d12769df…`, baseline `8e5987f5…`, helper `af9e5ea6…`, 114 manager files |

## Read in this order

1. **`COMMANDS.md`** — the six exact commands, including the post-run
   collection that is **yours and not the worker's**.
2. **`OPERATOR.md`** — what each step does and what to expect.
3. **`SHUTDOWN.md`** — what the vehicle publishes when it ends, who can read
   it, the two statements revision 5 got wrong, and the rules: a missing final
   report is incomplete rather than success, **and an unavailable report names
   no cause**.
4. **`ENFORCEMENT.md`** — the vehicle, the composer's wrong start command, the
   900-second lease, the two measured ceilings.
5. **`FAILURE.md`** — the one actual execution of this Work and why it failed.
6. **`TASK.md`** — what the authoring turn is actually asked to build.

`collect.py` and `probe.py` are the two executable documents: the first is the
operator's read-only post-run collection, the second re-runs all thirty
preparation refusals and collection cases in about 1.5 seconds.

Evidence: `PREPARATION-PINS.json`, `PROVENANCE.json`, `PREFLIGHT.json`,
`GATE-CHECK.json`, `LIMITS-CHECK.json`, `decisions/` (16 immutable snapshots
indexed by `decisions/INDEX.json`), `SHA256SUMS` and `PACKET-INPUTS.json`.

## Why there is a sixth packet, and it is not a rebase

`../execution-339421` pins **exactly the vehicle bytes this packet pins** —
controller `d12769df…`, supervisor baseline `8e5987f5…`, helper `af9e5ea6…`,
base `bc925cf5`, 114 manager files. Nothing drifted under it; all 31 of its
seals verified at review. It is superseded for what its **documents** said, and
`decisions/review-339623.md` is the authority for four corrections:

1. **Post-run collection was the worker's, and could not be.** Its `TASK.md`
   item 6 asked the worker to report the run's own three final results. The
   controller publishes after `supervise_process` returns and after child
   cleanup (`authoring_enforcement.py:552-591`); the supervisor publishes
   post-stop (`baseline.py:1450-1461`). Both land after the worker is gone, and
   a worker killed at the 900-second expiry cannot run a final-report
   instruction at all. **Now:** the external operator and reviewer own it,
   executably, through `collect.py` and `COMMANDS.md` step 5; the worker reports
   what it observed before termination plus the retained candidate checkpoint,
   and names the host-side results as structurally unavailable to it. Overall
   collection acceptance is unchanged.
2. **Absence was reading as a timeout.** Its `SHUTDOWN.md` said an absent
   `enforcement-*.json` means publication did not fit, and that a publication
   `TimeoutError` means the controller "writes nothing". Both false. **Now:**
   absence means *unavailable, cause unknown*, with `absent`, `inaccessible`,
   `pending` and `unknown-cause` kept apart; a timeout is named only on a
   `TimeoutError` fault actually read in a correlated report; and the bound at
   `authoring_enforcement.py:586-594` spans `write_text`, `os.replace` **and**
   `print`, so a timeout during the `print` leaves a **complete** report and one
   during `write_text` can leave a partial `.tmp`. No filesystem non-effect
   follows.
3. **The previous claim's execution boundary.** Claim339421 executed about
   127.7s of product tests directly on the host, outside a preparation-only
   boundary, and then reported "re-runs 0" beside the resulting numbers.
   `PROGRESS.md` carries an additive correction naming the exact commands and
   costs; `GATE-CHECK.json` carries the numbers with that attribution; they were
   **not re-measured**, because re-running them to tidy their own provenance
   would repeat the mistake. **This claim ran no product test.**
4. **Sibling file bans replaced by overlap declaration.** `tools/job_manager.py`
   and `job_manager/manager.py` are no longer an absolute prohibition. The
   sibling allocation and the no-shared-tree rule stand; a necessary
   accepted-outcome edit is permitted with an explicit overlap declaration to
   W333485 and serial reviewed integration.

I re-verified the three vehicle paths and the base myself this claim, read-only,
and they are unchanged from revision 5.

## What changed in the task

`TASK.md` keeps every accepted obligation from revisions 1 to 5 — intent before
effects, typed outcome separate from unknown cessation, both release paths and
crash/replay cuts, the token-bound identity rule, the three-case
absent/quiescent replay table, cancellation as a second terminating component,
the bounded shutdown semantics of the vehicle, the safe locator round trip, the
read-only allowlisted report, and source-versus-rebuilt-bundle proof — and
changes exactly what review339623 required:

- **item 6 is rewritten and its old instruction withdrawn.** The worker reports
  its progress per item, the retained candidate with exact paths, which tests it
  ran and what they measured, the lease and cessation facts it **positively
  observed from inside**, and its correlation keys (`run_id`, `work`, `claim`,
  its pid, `outcome_path`, `status_path`). It must **not** report the three
  host-side final results as present, absent, complete or incomplete — it cannot
  see them, and writing "absent" about a file its own death precedes is a false
  observation rather than a cautious one.
- **revalidation item (e) is corrected twice.** The "returns 1 and writes
  nothing" claim is withdrawn as false with the reason; and the four-state table
  — absent, inaccessible, pending, unknown-cause — enters the task as both a
  reading rule and a product axis, with the timeout rule attached.
- **one preserved axis added**: an unavailable report names no cause. A reader
  that turns a missing report into a timeout, or an inaccessible one into an
  absent one, is wrong in the same way as one that turns an absent record into
  proof that nothing happened.
- **Boundaries now declare overlap instead of banning files**, with the expected
  shape still being that the sibling's surfaces are not needed, and the
  no-shared-tree and serial-integration rules intact.
- **the gate numbers carry their real attribution** so that the turn knows the
  13.642s baseline is an out-of-boundary claim339421 measurement and measures
  its own gate itself.

The vehicle files remain off-limits: the turn edits neither
`tools/authoring_enforcement.py`, `tools/authoring_shutdown.py` nor the
supervisor baseline, which is the condition the two gate exclusions rest on.

## Preparation evidence, measured this claim

**No product test was executed to produce any of it.**

- **Input check**: 0.162s, clean — 114 manager files, 3 supervisor files, 2
  preparation inputs, **21** task inputs, **16** decision snapshots, 4 checkout
  documents, 1 pinned controller, 1 pinned shutdown helper, 2 gate modules still
  owed, **no decision-source drift**.
- **Preparation exercised once** into `/tmp/w333486-preflight-339628`: stage
  0.122s, bootstrap `--no-repositories` 0.627s, bind 0.361s — **1.110s, all
  status 0**, ending `prepared-not-executed` / `start_selected false` /
  `composer_start_is_unenforced true`, after `held_packet` re-pinned all 21
  `fixture.files` and `verify_imported_sources` passed.
- **Thirty probes, all behaving as intended, 1.507s**, and they are now a
  sealed program (`probe.py`) rather than an ad-hoc sequence, so a reviewer
  re-runs the lot in about a second and a half. Every root-creating refusal also
  asserts whether the root was created.
  - **Seven are the executable proof of correction 2**: nothing published;
    inaccessible is not absent; a partial temporary is pending; an unparseable
    report is unknown-cause; an uncorrelated report is unknown-cause; a timeout
    named **only** on a real `TimeoutError` fault; and `collect.py` over the
    **read-only copies of this Work's one actual execution** — which left no
    workload outcome because it died at startup, and reports
    `publication_timeout.established: false` exactly as it should.
  - Four more are new or restored: a provenance declaring a restored buffer, a
    damaged `review-339623.md` snapshot, an absent one, and a drifted
    preparation input.
  - The rest are the revision-5 set: no acknowledgement; the superseded
    controller digest; an unpinned and a drifted shutdown helper; a drifted
    manager source; the superseded supervisor baseline; a provenance claiming a
    selected start; one claiming an authorized start; an absent `SHUTDOWN.md`;
    an absent task input; a checkout input not at the base; a gate module
    already on the host; a root inside the repository; a relative root; an
    existing root (left untouched); a second `bind` over a composed packet; and
    a `bind` against a root staged for another run.
- **The controller binding proved both ways**, read-only, opening no store and
  starting nothing: `verify_controller` **accepted** this packet's composed
  documents from the staged source (0.292s) and **refused** them from the host
  checkout (0.152s) — *"authoring controller is outside the pinned manager
  source"*.
- **The helper pin is load-bearing and re-measured**: importing the controller
  from a staged source with `tools/authoring_shutdown.py` removed fails with
  `ModuleNotFoundError` in 0.326s. A missing helper is a **startup failure**,
  not a refusal, and `FAILURE.md` records what a startup failure cost this Work.
- **Generated limits agree** (`LIMITS-CHECK.json`, re-read from **this** claim's
  composed `policy.json`, `submission.json` and `PACKET.json`, not from prose):
  provider 3600, verification 30, one invocation, no automatic retry,
  `report-and-hold`, 4800 total, 60 cleanup, 1110 residual.
- **The sealed gate was NOT run this claim.** Its argv was re-derived from this
  packet's composed `task.json` and confirmed to name both owed modules
  (`GATE-CHECK.json` `verification_member_identical_at_this_claim`) — a
  composition check, not an execution. The **status 1 / 1126 tests / 14.18s**
  result and the **1124 tests / 13.642s** baseline are claim339421 measurements
  obtained by direct host product execution **outside that claim's preparation
  boundary**, carried forward with that attribution and deliberately not
  re-measured.

Author evidence, **not** independent product acceptance.

## Disclosures, all retained

- **The composer still emits the unenforced start.** `baseline_bindings.py` is
  unchanged at this base (`09fbf3c5…`, re-measured) and line 721 still composes
  `baseline.py` directly. Reported for classification, **not patched** —
  correcting it is host product work this Work does not own — and mitigated by
  `AUTHORING-COMMAND.json`, `PREPARED.json`'s `composer_start_is_unenforced`
  flag and both operator documents. **Every later authoring packet inherits
  this** until the composer is corrected.
- **The 900-second lease is enforced and unextended.**
  `worker_manager/tokens.py:37` still reads `LIFETIME_SECONDS = 900`, measured
  at this base. W333735 made it real; W338305 made the *ending* bounded. The
  3600/4800 ceilings are requested bounds, not a promised run length.
- **No authoring invocation has ever completed for this Work.** One was
  selected and died 0.506s into startup. Two corrected failures are not a
  demonstration that a third attempt completes.
- **The 30-second verification fit remains unproved**, with ≈16.36s left for the
  two modules the turn must create, and no coverage may be removed to force a
  pass.
- **Two excluded real-process modules are reused, never re-run here** —
  `decisions/shutdown-review.md` (44 tests, 72.891s, authority338596) and
  `decisions/guard-integration-result.json` (79 tests, 15.278s,
  authority337376) — on the stated condition that this candidate edits none of
  the three vehicle files.
- **Two excluded modules already fail at base**, both explicitly unverified
  baseline reports with no cleanup selected:
  `tests.manager.test_boundary_inventory` (not re-measured this claim; the
  49.469s figure is from an earlier base's bytes) and
  `tests.tools.test_packaging`'s subcommand case.
- **`AGENTS.md` at this base carries the older W321689 exception section**,
  because the host's replacement of it is an uncommitted working-tree edit. The
  turn reads the base copy. The exception is expired either way; this packet's
  documents are the authority on what is permitted here.
- **Both temporary direct-implementation exceptions have expired** and neither
  ever covered diagnostics.
- **Two gate exclusions rest on out-of-boundary measurements.** The 51.333s and
  19.888s figures that justify excluding `test_authoring_shutdown_deadline` and
  `test_authoring_manager_guard` were obtained by direct host product execution
  at claim339421, outside that claim's preparation boundary. The decisions stand
  on numbers with a known defect in how they were obtained, and that is stated
  in `GATE-CHECK.json`, `PROVENANCE.json`, `TASK.md` and `SHUTDOWN.md` rather
  than laundered.
- **One probe is honest about its method.** `owed-gate-module-already-on-the-host`
  substitutes two existing module paths for the two owed names in the copy's
  `prepare.py`, because probing it literally would mean creating a product test
  file in the host working tree. Labelled `substituted: true`.
- **One probe refuses earlier than I predicted.**
  `bind-a-root-staged-for-another-run` is refused at the pins — *"the pins name
  another base or run"* — rather than at the staged-root comparison, because the
  copy's run constant and its own pins disagree first. Recorded as it behaved.

## Ownership and what is still owed

`baton.impl` owns this packet, `PROGRESS.md` and the isolated candidate;
the reviewer owns `FINDING.md`, `PLAN.md` and the reviews. W333485 owns the
separate serving-renewal preparation at `baton.codx`, with no dependency either
way on its completion. The declared candidate intersection remains
`worker_manager/intake.py` and `worker_manager/attempts.py` at the accepted
bytes, for serial integration. `tools/job_manager.py` and
`job_manager/manager.py` are the sibling's **declared** surfaces: not expected
to be needed and no longer banned outright, but any edit there requires an
explicit overlap declaration to W333485 before the combined candidate and serial
reviewed integration — which is review339623's fourth correction.

Still owed: independent review of **this** preparation; an exact separate
execution selection; a run that actually completes, which has never happened for
this Work; the entire correction in `FINDING.md`; independent review of the
retained candidate; parent W325959's joined acceptance with W333485; and the
parent's pending human Git checkpoint.

**Nothing in this packet selects or authorizes a start.**
