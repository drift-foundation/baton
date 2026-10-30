# W333486 execution packet, revision 7 — sealed preparation at `bc925cf5`

`baton.claude`, claim339868, role `impl`. **Preparation only.** No Job
submitted, no attempt, no runtime, no engine, no provider, no credential read,
no Git mutation, no host product or test edit, **and no product test executed**
— which is itself one of the four corrections this revision carries. **The start
is not selected.**

| | |
| --- | --- |
| base | `bc925cf5c62d69426ed5862af4d41f4d2a967b0f` |
| proposed run | `attempt-diagnostics-w333486-339868` |
| proposed root | `/home/sl/baton-instances/attempt-diagnostics-w333486-339868` — **absent** |
| supersedes | `../execution-333504`, `../execution-333707`, `../execution-334663`, `../execution-337453`, `../execution-339421`, `../execution-339628` — all preserved, all seals still verifying |
| start | `start_authorized: false`, `start_selected: false` |
| exact commands | `COMMANDS.md` (six, no placeholders; step 5a–5e is the operator's post-run collection) |
| vehicle pins | **unchanged for the third packet running** — controller `d12769df…`, baseline `8e5987f5…`, helper `af9e5ea6…`, 114 manager files |

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
operator's read-only post-run collection, the second re-runs all **forty-one**
refusal and collection cases in about 1.7 seconds — including all four fixtures
the last review used to find this packet's predecessor wrong.

Evidence: `PREPARATION-PINS.json`, `PROVENANCE.json`, `PREFLIGHT.json`,
`GATE-CHECK.json`, `LIMITS-CHECK.json`, `decisions/` (18 immutable snapshots
indexed by `decisions/INDEX.json`), `SHA256SUMS` and `PACKET-INPUTS.json`.

## Why there is a seventh packet

`../execution-339628` pins **exactly the vehicle this packet pins** — controller
`d12769df…`, baseline `8e5987f5…`, helper `af9e5ea6…`, base `bc925cf5`, 114
manager files — and introduced `collect.py`, the executable operator half the
review before it asked for. **That collector had four correctness defects**, all
found by `decisions/review-339861.md`, all reproduced in the reviewer's own
fixtures at `decisions/collector-probes-339847.json`, and all fixed here:

1. **A present workload report was reported `absent`.** The old `_workload`
   handed the display label *"workload final report"* to the path resolver,
   discovered `outcome.json` afterwards, replaced `paths` — and never corrected
   the state or parsed the file. So the one artifact most likely to exist was the
   one guaranteed to be misread. **Now:** every artifact resolves from an explicit
   name or glob, never from a label, and the positive case is a probe.
2. **Correlation demanded a field the vehicle does not publish.** The controller
   report has **no top-level `run_id`**; its identity is `original_envelope`
   (`authoring_enforcement.py:40-52`, stored at `:580`) carrying `run`, `job`,
   `authority`. The old code insisted on `run_id`, so **every real controller
   report came back `unresolved`** — and my own probes hid that by inventing the
   field. **Now:** each artifact is correlated through the shape *it* publishes,
   the field used is named in the output, a disagreeing field is a `mismatch`,
   and the exact links the controller names for itself are resolved.
3. **An unrelated timeout became a publication timeout.** Any fault containing
   `TimeoutError` counted, so `TimeoutError: manager startup snapshot`
   "established" a publication timeout. **Now:** only a fault naming a
   **publication step** in a **correlated** artifact can; other timeouts are
   reported as timeouts of other steps and uncorrelated ones as evidence about
   another run. And the sharper fact is stated rather than papered over: the
   **outer** publication timeout is **not establishable at all**, because the
   handler at `:592-595` catches its own `TimeoutError` and returns 1 *without*
   adding that fault to the report it was writing.
4. **A malformed report aborted everything.** A JSON array raised
   `AttributeError` and no other evidence was collected. **Now:** a bad shape or
   a failed read is an `unknown-cause` observation, `isolated_failures` records
   it, and the other artifacts are still collected.

The honest summary: the collector asserted conclusions its inputs did not
support — the exact failure mode this whole diagnostics outcome exists to
prevent. The fix was to read the producers and **narrow** the claims.
`TASK.md` item (e), the preserved axes, `SHUTDOWN.md`'s rules and `COMMANDS.md`
step 5 are all narrowed to match.

Also new, because the real case demanded it: a fifth collected artifact (the
manager status snapshot) and an `--expect-run` operand, since a retained
evidence directory holds the published artifacts but not the composed
`PACKET.json`. It is labelled an operator assertion and refused if it
contradicts a packet that *is* readable.

### And why the sixth existed

`../execution-339421` pins the same vehicle too and was superseded for its
documents: a `TASK.md` item 6 that asked the terminating worker to report
results published after its own death, an absent report read as a publication
timeout, an overstated filesystem non-effect, and absolute sibling-file bans.
`decisions/review-339623.md` is that authority. Both packets are preserved
byte-for-byte, 31 and 34 members, seals intact.

## What changed in the task

`TASK.md` keeps every accepted obligation from revisions 1 to 6 and narrows the
reading rules to what the artifacts support:

- **item (e)** gains the publication-step table — which timeouts are
  publications, where each is recorded, and that the **outer** one is
  structurally unrecordable — plus the rule that each artifact is correlated
  through the shape it publishes, with the controller's `original_envelope`
  named explicitly, and that one malformed artifact must not cost the others.
- **two preserved axes added**: a cause is named only from evidence that is both
  **specific** and **correlated**; and an artifact is correlated through its own
  shape, where demanding a field the producer does not publish yields a false
  `unresolved`.
- **item 6 is unchanged in substance** — the worker still reports only what it
  observed before termination plus the retained candidate — with its pointer to
  the operator's half updated to describe what `collect.py` actually does.
- **`decisions/review-339861.md` and the reviewer's fixtures are pinned inputs**,
  recommended reading for the turn precisely because they are a short lesson in
  claims an artifact does not support.

Unchanged from revision 6: Boundaries declare overlap rather than banning files,
the gate numbers carry their out-of-boundary attribution, and the vehicle files
remain off-limits — which is the condition the two gate exclusions rest on.

## Preparation evidence, measured this claim

**No product test was executed to produce any of it.**

- **Input check** 0.115s, clean — 114 manager files, 3 supervisor files, 2
  preparation inputs, **23** task inputs, **18** decision snapshots, 4 checkout
  documents, 1 pinned controller, 1 pinned shutdown helper, 2 gate modules still
  owed, **no decision-source drift**.
- **Preparation exercised once** into `/tmp/w333486-preflight-339868`: stage
  0.121s, bootstrap `--no-repositories` 0.598s, bind 0.372s — **1.091s, all
  status 0**, ending `prepared-not-executed` / `start_selected false` /
  `composer_start_is_unenforced true`, after `held_packet` re-pinned all 23
  `fixture.files` and `verify_imported_sources` passed.
- **Forty-one probes, all behaving as intended, 1.678s** — 23 preparation
  refusals and 18 collection cases, re-runnable by any reviewer in under two
  seconds via `probe.py --work <fresh /tmp dir>`.
  - **The four fixtures from `review-339861` are regressions now**:
    `present-workload-is-read`, `actual-controller-shape-correlates`,
    `unrelated-timeout-is-not-publication` and
    `nonobject-report-does-not-abort-collection`. The reviewer's own fixture
    file is pinned at `decisions/collector-probes-339847.json` so the before and
    after are checkable side by side.
  - Fourteen further collection cases: specific publication evidence through the
    progress file (where `Shutdown.call` actually records it); a conflicting
    identity; a controller incarnation with no envelope; an uncorrelated
    timeout; exact progress linkage resolved from the report's own
    `manager_report_path`; an isolated read failure with the workload still
    read; an unreadable composed packet; both `--expect-run` cases including the
    contradiction refusal; and this Work's **real retained evidence** collected
    both uncorrelated and correlated.
  - `probe.py` now checks **named claims** — which identity field correlated,
    which publication step was named, how many non-publication timeouts were
    seen — and not merely states. States alone are what let the previous defects
    pass review once.
- **The controller binding proved both ways**, read-only: `verify_controller`
  **accepted** this packet's composed documents from the staged source (0.292s)
  and **refused** them from the host checkout (0.140s).
- **The helper pin re-measured as load-bearing**: `ModuleNotFoundError` in
  0.327s with `tools/authoring_shutdown.py` removed from a staged source.
- **Generated limits agree**, re-read from **this** claim's composed
  `policy.json`, `submission.json` and `PACKET.json`: provider 3600,
  verification 30, one invocation, no automatic retry, `report-and-hold`, 4800
  total, 60 cleanup, 1110 residual.
- **The sealed gate was NOT run.** Its argv was re-derived from this claim's
  composed `task.json`, confirmed to name both owed modules, and its digest
  `9841127b…` is **identical** to the previous claim's — the gate did not change.
  A composition check, not an execution. The **status 1 / 1126 tests / 14.18s**
  result, the **1124 tests / 13.642s** baseline and the 51.333s / 19.888s
  exclusion figures remain claim339421 measurements obtained by direct host
  product execution **outside that claim's preparation boundary**, carried with
  that attribution and deliberately not re-measured.

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
- **The collector in the previous packet was wrong in four ways and shipped
  through one review before it was caught.** `decisions/review-339861.md` found
  them with four fixtures. Every one was a claim stronger than its evidence, and
  three of the four came from not having read the producer: the controller does
  not publish `run_id`, and the outer publication timeout is recorded nowhere.
  All four are now regression probes. This is the second time in this campaign
  that a confident summary of mine outran what the code said — the first was the
  reclaim path in revision 2 — and both are recorded rather than quietly fixed.
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
