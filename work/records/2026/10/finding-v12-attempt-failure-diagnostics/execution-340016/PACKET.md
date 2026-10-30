# W333486 execution packet, revision 8 — sealed preparation at `bc925cf5`

`baton.claude`, claim340016, role `impl`. **Preparation only.** No Job
submitted, no attempt, no runtime, no engine, no provider, no credential read,
no Git mutation, no host product or test edit, **and no product test executed**
— which is itself one of the four corrections this revision carries. **The start
is not selected.**

| | |
| --- | --- |
| base | `bc925cf5c62d69426ed5862af4d41f4d2a967b0f` |
| proposed run | `attempt-diagnostics-w333486-340016` |
| proposed root | `/home/sl/baton-instances/attempt-diagnostics-w333486-340016` — **absent** |
| supersedes | `../execution-333504`, `../execution-333707`, `../execution-334663`, `../execution-337453`, `../execution-339421`, `../execution-339628`, `../execution-339868` — all preserved, all seals still verifying |
| start | `start_authorized: false`, `start_selected: false` |
| exact commands | `COMMANDS.md` (six, no placeholders; step 5a–5e is the operator's post-run collection) |
| vehicle pins | **unchanged for the fourth packet running** — controller `d12769df…`, baseline `8e5987f5…`, helper `af9e5ea6…`, 114 manager files |

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
refusal and collection cases in about 1.8 seconds — including **both** reviewers'
fixture sets, the seven cases that found this collector wrong twice.

Evidence: `PREPARATION-PINS.json`, `PROVENANCE.json`, `PREFLIGHT.json`,
`GATE-CHECK.json`, `LIMITS-CHECK.json`, `decisions/` (20 immutable snapshots
indexed by `decisions/INDEX.json`), `SHA256SUMS` and `PACKET-INPUTS.json`.

## Why there is an eighth packet

`../execution-339868` pins **exactly the vehicle this packet pins** — fourth
consecutive packet on the same bytes — and it fixed the first four collector
defects. **It introduced three more**, all found by
`decisions/review-340012.md`, all reproduced in that reviewer's fixtures at
`decisions/collector-probes-339992.json`:

5. **A malformed *link* aborted the whole collection.** `_linked` called
   `Path(value)` on whatever the report carried and caught only `OSError`, so a
   correlated controller with `authoring_log: []` raised `TypeError` out of
   `collect()` and destroyed a perfectly readable workload result beside it.
   **In the very revision that fixed the malformed-*report* case.** That is the
   uncomfortable part and it is recorded, not smoothed: I isolated one shape of
   bad input and left the adjacent one unguarded.
6. **One unrelated temporary marked every artifact `pending`.** The
   directory-wide `outcome.json*.tmp` set was handed to all of them, so a single
   controller temporary made the workload, the progress file and the manager
   snapshot each report that **its** publication had been entered. The same glob
   never matched the workload temporary at all — which is `outcome.json.partial`
   (`baseline.py:1006`), not a `.tmp`. I had guessed both names instead of
   reading the producers; `with_suffix('.tmp')` *replaces* `.json`, so the
   controller's is `outcome.json.enforcement-<pid>-<ns>.tmp`.
7. **The progress file was counted as a manager snapshot**, because
   `outcome.json.manager-*.json` matches `...json.progress.json`.

**And a false claim about the producer.** The previous packet said a child
publication timeout "reaches the progress file". It does not, and the reviewer
showed it from statement order alone: `Shutdown.call`
(`authoring_shutdown.py:72-86`) enters `bounded(deadline, step)` **first** — an
exhausted deadline raises before any write — then writes its snapshot carrying
the faults of **earlier** calls, then runs the step, then on failure appends that
step's fault to **memory only**. `final enforcement publication`
(`authoring_enforcement.py:493`) is the **last** such call in the controller's
`finally`, so nothing flushes it. So **this vehicle persists no publication fault
reliably**: absence is the expected state even when a publication really did time
out, and a fault found on disk is *parsed*, not proof the producer records them.

**The fix, each time, is the same move**: read the producer, narrow the claim,
and make the probes assert named claims instead of states. Seven defects across
two revisions, every one a claim stronger than its evidence — which is precisely
what the diagnostics outcome this packet prepares exists to stop a reader doing.
Both reviewers' fixture sets now travel in `decisions/`, so the whole sequence is
re-checkable without reconstruction.

### The earlier supersessions, in one line each

`../execution-339628` fixed defects 1–4 (`decisions/review-339861.md`).
`../execution-339421` was superseded for its documents: the terminating worker
asked to report results published after its own death, absence read as a
publication timeout, an overstated filesystem non-effect, and absolute
sibling-file bans (`decisions/review-339623.md`). All preserved byte-for-byte —
31, 34 and 36 members, seals intact.

## What changed in the task

`TASK.md` keeps every accepted obligation from revisions 1 to 7 and narrows two
more reading rules to what the artifacts support:

- **item (e)'s publication table is corrected.** It previously said a child
  publication timeout is recorded in the progress file. It is not: no
  publication fault is reliably persisted by this vehicle, so **absence is
  expected and informative in neither direction**, and the table now gives the
  reason per step from the producer's statement order.
- **item (e) gains the filename rules**, because they are not guessable and were
  twice got wrong here: the workload's temporary is `outcome.json.partial`, not a
  `.tmp`; `with_suffix('.tmp')` replaces `.json`; and
  `outcome.json.manager-*.json` matches `...json.progress.json`.
- **two preserved axes added**: where the producer does not persist a fault its
  absence is expected and proves nothing either way; and evidence belongs to the
  artifact whose name it carries — one artifact's temporary says nothing about
  another's publication.
- **both reviews and both fixture sets are pinned inputs**, recommended reading
  for any turn that builds a reader over these artifacts.

Unchanged: item 6's worker/operator split, Boundaries declaring overlap rather
than banning files, the out-of-boundary attribution on the gate numbers, and the
vehicle files remaining off-limits — the condition the two gate exclusions rest
on.

## Preparation evidence, measured this claim

**No product test was executed to produce any of it.**

- **Input check** 0.118s, clean — 114 manager files, 3 supervisor files, 2
  preparation inputs, **25** task inputs, **20** decision snapshots, 4 checkout
  documents, 1 pinned controller, 1 pinned shutdown helper, 2 gate modules still
  owed, **no decision-source drift**.
- **Preparation exercised once** into `/tmp/w333486-preflight-340016`: stage
  0.115s, bootstrap `--no-repositories` 0.610s, bind 0.360s — **1.085s, all
  status 0**, ending `prepared-not-executed` / `start_selected false`, after
  `held_packet` re-pinned all 25 `fixture.files` and `verify_imported_sources`
  passed.
- **Forty-six probes, all behaving as intended, 1.763s** — 23 preparation
  refusals and 23 collection cases, re-runnable in under two seconds via
  `probe.py --work <fresh /tmp dir>`.
  - **Both reviewers' fixture sets are regressions now.** From
    `review-339861`: `present-workload-is-read`,
    `actual-controller-shape-correlates`,
    `unrelated-timeout-is-not-publication`,
    `nonobject-report-does-not-abort-collection`. From `review-340012`:
    `malformed-link-does-not-lose-other-results`,
    `unrelated-temporary-cannot-fabricate-pending`,
    `progress-is-not-a-manager-snapshot`. Both fixture files are pinned in
    `decisions/`.
  - **Two of my own probes were worthless and are rebuilt.** The
    temporary-pending case used `outcome.json.enforcement-1-2.json.tmp` — a name
    no producer writes — so it proved nothing; it is now two cases on the real
    names. And the former "producer-shaped positive" for a child publication
    timeout is relabelled
    `publication-fault-on-disk-is-parsed-not-producer-proof`, because the
    producer does not persist that fault at all. A new
    `absent-publication-fault-stays-unknown` asserts the verdict says **not
    establishable**, not merely not established.
  - One probe *expectation* was also wrong and was corrected toward the code: I
    expected `unclassified_entries` to be empty in fixtures containing
    `PACKET.json`, but that is a legitimate composed member and the collector was
    right to surface it. `COMPOSED_MEMBERS` now recognises the packet documents.
- **The controller binding proved both ways**, read-only: accepted from the
  staged source 0.296s, refused from the host checkout 0.141s.
- **The helper pin re-measured as load-bearing**: `ModuleNotFoundError` in
  0.330s.
- **Generated limits agree**, re-read from this claim's composed documents:
  provider 3600, verification 30, one invocation, no retry, `report-and-hold`,
  4800 total, 60 cleanup, 1110 residual.
- **The sealed gate was NOT run.** Its argv was re-derived from this claim's
  composed `task.json`; the digest `9841127b…` is **identical** across claims
  339421, 339628, 339868 and 340016, so the gate has not changed. A composition
  check, not an execution. The out-of-boundary claim339421 figures are carried
  with that attribution and were not re-measured.

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
- **This packet's collector has now been found wrong twice: seven defects
  across two reviews.** Four by `decisions/review-339861.md`, three more by
  `decisions/review-340012.md`, plus one false claim about what the producer
  persists. Every one was a claim stronger than its evidence, and most came from
  not reading the producer — the controller publishes `original_envelope` not
  `run_id`, the workload temporary is `.partial` not `.tmp`, `with_suffix`
  replaces a suffix, a manager glob swallows the progress file, and no
  publication fault is persisted at all. **Twice the fix for one class of defect
  shipped beside a fresh instance of the same class**: a malformed report was
  isolated while a malformed link was not. All seven are regression probes and
  both fixture sets are pinned. Counting the reclaim-path wording in revision 2,
  this is the third kind of over-claim in this campaign to be caught by review
  rather than by me.
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
