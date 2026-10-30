# W333486 execution packet, revision 9 — sealed CONTINUATION at `bc925cf5`

`baton.claude`, claim340352, role `impl`. **Preparation only.** No Job
submitted, no attempt, no runtime, no engine, no provider, no credential read,
no Git mutation, no host product or test edit, **and no product test executed**
— which is itself one of the four corrections this revision carries. **The start
is not selected.**

| | |
| --- | --- |
| base | `bc925cf5c62d69426ed5862af4d41f4d2a967b0f` |
| proposed run | `attempt-diagnostics-w333486-340352` |
| proposed root | `/home/sl/baton-instances/attempt-diagnostics-w333486-340352` — **absent** |
| supersedes | `../execution-333504`, `../execution-333707`, `../execution-334663`, `../execution-337453`, `../execution-339421`, `../execution-339628`, `../execution-339868`, `../execution-340016` — all preserved, all seals still verifying |
| start | `start_authorized: false`, `start_selected: false` |
| exact commands | `COMMANDS.md` (six, no placeholders; step 5a–5e is the operator's post-run collection) |
| **continues from** | retained candidate `433692c5003d7f3a91a1acab7efdb471d5597235`, patch `sha256:3af1822d…`, pinned as a task input. `CONTINUATION.md` is the account |
| vehicle pins | **unchanged for the fifth packet running, and now PROVEN end to end by the completed run** — controller `d12769df…`, baseline `8e5987f5…`, helper `af9e5ea6…`, 114 manager files |

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
refusal and collection cases in about 2.1 seconds — including both reviewers'
collector fixture sets and six new refusals that keep the retained-candidate pin
honest.

Evidence: `PREPARATION-PINS.json`, `PROVENANCE.json`, `PREFLIGHT.json`,
`GATE-CHECK.json`, `LIMITS-CHECK.json`, `decisions/` (24 immutable snapshots
indexed by `decisions/INDEX.json`), `SHA256SUMS` and `PACKET-INPUTS.json`.

## Why there is a ninth packet — the previous one RAN

`../execution-340016` was accepted, selected by owner reroute340145, preflighted
through the real executor boundary, and **launched once. It completed** — the
first authoring invocation this Work has ever finished. Launched 16:17:37Z, ended
on its own at **869.3s**, all four final results published, 1621 insertions
returned across 8 files including both owed test modules.

**Its gate exited 1**, so the attempt is `unable`, no proposal was published, and
a candidate was **retained** at head `433692c5003d7f3a91a1acab7efdb471d5597235`.
`decisions/review-340349.md` rejected that candidate with three static blockers,
and this packet is the continuation from it. `CONTINUATION.md` has the full
account with each blocker re-verified against the candidate's own bytes:

1. **the production seam is not connected.** No `job_manager` file changed;
   `_stage_status` emits no `attempt_diagnostics`; `attempt_failure_cause_of`
   has no production caller; the report reads only `stage["attempt_diagnostics"]`.
   **Fixtures on both sides of an unjoined seam prove nothing about the seam** —
   and that is the heart of the requested outcome, so it is `TASK.md` item A.
2. **producer and report shapes disagree.** `_known(value, source)` wrappers
   meet `EXECUTION_MEMBERS`/`_typed`, which want raw scalars and refuse nested
   objects, so a recorded **known** value arrives **unknown**; `CAUSE_MEMBERS`
   wants a scalar `outcome` and a top-level `operation_id` the composition never
   exposes; and the token, completion, start and preparation facts are composed
   but absent from the report's member lists. Item B.
3. **the durable pre-effect intent is best-effort and silent.** All four acting
   call sites discard the recorder's return, two of them immediately before
   ordering an effect, and a fixed outcome identity lets a historical
   *uncertain* observation outrank a later *positive* one. Item C.

### Two predictions settled, one obligation created

- **The 900-second lease did not fire.** `provider.status 0`, 869.45s served
  against 900 — 30.5 seconds of margin. Every earlier packet in this campaign,
  all by this author, predicted enforced expiry cutting the turn short. The
  prediction is **withdrawn**, `TASK.md` says so, and pre-writing an expiry
  narrative is now explicitly forbidden.
- **The vehicle is proven**, not merely asserted: controller, child manager,
  guard, engine, container, candidate retention and all four final reports all
  worked.
- **The gate result must now be classified inside the run.** Its output is
  withheld by design because it ran with the credential mount readable, and a
  generated line suggesting a host rerun is **not authority** —
  `decisions/review-340349.md` is explicit and the author accepts the
  correction. `TASK.md` item 7 makes the classification a deliverable, which is
  how the 30-second fit question finally gets answered.

### How the candidate is delivered, and what stays refused

The patch is pinned by digest and named as a task input, so it travels as
`fixture.files` bytes on the read-only mount. **No version-control object is
created on this host and nothing is restored into the private checkout** — so
`PROVENANCE.checkpoint.paths` stays empty and `prepare.py` still refuses a
declared restored buffer, keeping that refusal meaningful. `prepare.py` and
`verify-inputs.py` cross-check the patch four ways: its bytes against the pin,
the pin against the candidate's own returned disposition record (identity and
all eight `changed_paths`), its presence among the task inputs, and
`CONTINUATION.md`'s presence. Six new probes cover each refusal.

## What changed in the task

`TASK.md` is restructured around the review rather than edited at the margins:

- **it opens by telling the turn to apply the pinned candidate patch** and
  confirm the eight `changed_paths`, with `CONTINUATION.md` as required reading;
- **the milestone is now seven things**: A connect the seam into ordinary
  versioned status and have the report consume those actual bytes; B one owned
  versioned shape across producer, status and report; C make the durable intent
  actually durable and replay truthful on both release paths; 6 report only what
  the worker can observe; 7 **new** — classify the gate result inside the run;
- **items 1 to 5 are reproduced verbatim** as the standing specification, so the
  turn checks the candidate against what was actually asked rather than against
  a summary of it. Most of them are already satisfied in the patch;
- **the expiry framing is corrected** with the measured fact, and pre-writing an
  expiry narrative is forbidden;
- **the gate section records that the gate has now been run once on real work**
  and exited 1 with its cause unclassified, so the baseline figures are labelled
  pre-run;
- **Boundaries** add the completed run and its retained candidate to what is
  preserved, and name the host-side rerun as explicitly not authorized.

Unchanged: the worker/operator collection split, overlap declaration instead of
sibling file bans, the out-of-boundary attribution on the old gate numbers, and
the vehicle files staying off-limits.

## Preparation evidence, measured this claim

**No product test was executed to produce any of it, and the completed run was
not re-run, recovered or mutated.**

- **Input check** 0.117s, clean — 114 manager files, 3 supervisor files, 2
  preparation inputs, **31** task inputs, **24** decision snapshots, 4 checkout
  documents, 1 pinned controller, 1 pinned shutdown helper, **1 pinned retained
  candidate patch**, 2 gate modules still owed, **no decision-source drift**.
- **Preparation exercised once** into `/tmp/w333486-preflight-340352`: stage
  0.122s, bootstrap `--no-repositories` 0.591s, bind 0.366s — **1.079s, all
  status 0**, ending `prepared-not-executed` / `start_selected false`, after
  `held_packet` re-pinned all **31** `fixture.files`.
- **The candidate patch demonstrably travels**: the composed
  `PACKET.json` `fixture.files` carries
  `…/evidence/run-340016/candidate-change.patch` at
  `3af1822dc0d08851466105f17cbf5e9e26248ff75dc3d9352a9a43b979058e3e` — read from
  the composed document, not asserted.
- **Fifty-two probes, all behaving as intended, 2.108s** — 29 preparation
  refusals and 23 collection cases. **Six are new** and each matches one
  cross-check on the retained candidate: a drifted patch, a patch that is not a
  task input, an identity disagreeing with what the run returned, paths
  disagreeing with what the run returned, an absent `CONTINUATION.md`, and a
  damaged candidate disposition snapshot. Both reviewers' collector fixture sets
  remain regressions.
- **The controller binding proved both ways**, read-only: accepted from the
  staged source, refused from the host checkout.
- **Generated limits agree**, re-read from this claim's composed documents:
  provider 3600, verification 30, one invocation, no retry, `report-and-hold`,
  4800 total, 60 cleanup, 1110 residual.
- **The sealed gate was NOT run here.** Its argv was re-derived from this claim's
  composed `task.json`; the digest is unchanged across every claim since 339421,
  so the gate itself has not moved. The real information about it now comes from
  the completed run: **it exited 1 on actual candidate work**, cause
  unclassified, which is why item 7 exists.

One probe failure of mine, corrected toward the code rather than worked around:
the `decisions/` snapshots copied out of `evidence/run-340016/` arrived mode
`0444`, so the damaged-snapshot probe could not write to one and raised
`PermissionError`. The packet's own documents should not be read-only inside the
packet; I normalised the modes rather than teaching the probe to chmod.

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
- **The retained candidate is rejected, not accepted.** A run completing and a
  candidate existing are not acceptance: its gate failed, three static blockers
  stand, and `review-340349.md` is explicit that it is not a complete
  certification of all 619 new cause-reader lines either. The installed/rebuilt
  bundle obligation also remains open.
- **The gate's failure cause is unknown and must stay unknown until classified
  inside a run.** Both a real test failure and a 30-second ceiling kill remain
  live; nothing in the retained evidence distinguishes them, and the host rerun
  a generated line suggests is not authorized.
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
