# Progress

No implementation has started. The certification stage is deliberately held
behind acceptance of the standalone multi-Job pipeline milestone.

## claim153769 — the additive trace foundation, built and run

Owner return153764 approved the additive foundation: two new test files,
deterministic providers, real coordination owners and independent trace
validation, with the three contract mismatches RETAINED as open, 120s author /
30s reviewer caps and 100 ticks per trace. This is that slice. **Nothing here
certifies the scheduler and no assertion was weakened.**

### What was built

Two new files, and no existing file of any kind was edited:

- `v12/python/tests/tools/scheduler_trace.py` — the scenario document, the
  versioned trace artifact, the environment manifest and the independent
  validator.
- `v12/python/tests/tools/test_scheduler_trace.py` — the fixed four-Job /
  two-team / two-repository scenarios, the schedules, the boundary cases, the
  retained-gap records and the validator's own negative cases.

### The scenario and what really decides it

Four Jobs across two teams and two repositories; one dependency edge A→B; C and
D independent; two implementation slots, two review slots and integration
capacity configured separately rather than multiplexed onto a producer. The
scenario is scripted; **every outcome is an owner's own answer** — the real
`activate_pool`, the real `scheduler.reserve`, the real `projection.owed_acts`
and a real Job store. No allocation row is inserted, no claim fabricated, no
receipt written.

### The validator is a second opinion, not the driver's bookkeeping

`validate` takes an exported artifact and re-derives everything from the records
alone: dependency completion before successor admission, relative act order
within an attempt, no overlapping occupancy, distinct producer/reviewer
principals, exactly-once operations across reopen, and **every refusal carrying
its exact public cause**. Twelve violation codes, each with its own synthetic
invalid-trace case, plus one well-formed synthetic trace so the oracle is proved
non-vacuous. The synthetic inputs are marked as such and are never execution
evidence.

### Two real defects the runs found in my own driver

1. **Eligibility was wrong and the very first run proved it.** I had treated
   "has a live episode" as eligibility, and the trace reserved
   `job-b/implementation` while the `job-a/implementation` it depends on had not
   completed. Dependency eligibility belongs to `projection.owed_acts`, which
   answers `admit` only for a stage its own store reports queued rather than
   blocked. The driver asks that owner now.
2. **An idempotent re-reserve was being recorded as a second act.**
   `scheduler.reserve` returns the standing allocation, and recording that as a
   fresh performed reservation made the trace claim an act that did not newly
   happen — the exactly-once invariant would correctly have refused its own
   driver's output. It is recorded as an `observe` of existing custody.

Both are recorded because they are exactly what a trace foundation is for: the
oracle caught its own driver.

### The three retained mismatches are recorded as GAPS, never as passes

- `explicit-fallback` — `reserve` chose a second compatible worker automatically
  when the first was occupied; the required explicit fallback decision is not
  what was observed.
- `priority-and-creation-order` — workers were selected in stable id order, which
  is not the promised priority pool with affinity before creation order.
- `composed-continuation` — `stage_execution._job_workers` binds implementation
  eligibility to `source_worker_id`, so this unit-level pool cannot establish a
  composed correction continuing elsewhere at all.

Each is a first-class artifact member with its reason, observation and
requirement, and the tests assert the gap is present.

### Environment gap, reported explicitly

`pyproject.toml` pins jsonschema **4.26.0**; this interpreter resolves **4.19.2**
and there is no `.venv` here. Every artifact carries `jsonschema_resolved`,
`jsonschema_pinned` and `jsonschema_conformant`, so no reader can mistake these
runs for dependency-conformant certification. No dependency was installed.

### Evidence

- `trace-153769.py` — reproduces the trace set and refuses to overwrite.
- `trace-153769.json` — three schedules (a-before-c, c-before-a, capacity-miss),
  **zero validator violations** each, with the gap report and the validator's
  code list.
- `run-153769-step-01..06.log`, `ledger-153769.json`.

Runs: step 1 (20 tests, 2 failures — the two driver defects above), step 2 (20
pass), step 3 (25 tests, 1 error — my own read of the activation answer), step 4
(**25 pass**), step 5 (trace set exported), step 6 (**86 existing
`test_scheduling` + `test_sweep` tests pass, unchanged**).

### Candidate, 0664

- `tests/tools/scheduler_trace.py`
  `2462271a32f6b4a7f7ab4e128ac4e58c680de13b27fe8a4ef85cb1536290ae8d`, 16295
- `tests/tools/test_scheduler_trace.py`
  `35cb21e4da6a16a5514c5419c96384358bdfac2b12a545971b0be21000f531bf`, 32223

### Ledger

Author **1.463887/120s** across six runs, two non-zero and both retained. The
reviewer's 0.2879257239692379s research baseline is preserved separately and not
reset. No live model calls. Unmeasured: reads, greps and the edit scripts.

### Not claimed

No certification of the scheduler contract. No composed multi-team execution —
these fixtures use `JobManagerCase`'s fake Authority sessions, exactly as the
existing accepted scheduling suite does, and the reviewer already recorded that
as exploratory. The offer/claim exchange is not driven, so the oracle reports
`unproven-completion` for any completion without a recorded claim rather than
pretending otherwise. Random workload expansion and TUI presentation are out of
this slice.

## claim153855 — every review finding corrected; R1's real transitions delivered

Review 2026-09-12T16:18:34Z requested changes on five findings. All five were
right. Corrections are inside the same two new test files and the dossier
evidence; no product file and no prior test was touched.

### R2 — the oracle accepted missing prerequisites and backwards time

Both were true and both are fixed at the root rather than patched.

- **Required prior evidence, not relative rank.** `REQUIRED_BEFORE` names what
  each act needs, and the check demands the prerequisite be present, earlier, and
  about the same attempt. The retained counterexample -- `claim` then `complete`
  with neither reserve nor offer -- now reports `missing-prerequisite`. Absent and
  late are deliberately distinguished: `missing-prerequisite` means you never did
  it, `out-of-order` means you did it too late.
- **The episode is part of the binding**, so two episodes of one stage are two
  attempts (`episode-mismatch`).
- **Logical time is validated.** The retained 9→2→1→0 trace now reports
  `regressing-time`. The first oracle never read a tick at all.
- A reserve-only trace stays legal: these are requirements OF an act, not
  obligations to reach one.

### R3 — occupancy ignored principals and freed custody on reopen

- **Effective principal occupancy is tracked beside worker occupancy.** Two
  reservations on different workers resolving to one canonical principal are one
  separation identity occupied twice.
- **Only a release frees capacity.** `RELEASING_ACTS` is `("release",)`: neither
  `complete` nor `reopen` returns a worker. Restart does not release custody, and
  a stage completion is not an allocation release.
- Both retained counterexamples are now negative cases, with a legal
  release-then-reuse case as their positive companion.

### R4 — restart evidence depended on pre-restart Python memory

The transient `_reserved` set is gone. The driver asks `allocation_of` **before**
reserving, so reserve-versus-observe is a durable fact. The reopen test now builds
a **genuinely fresh driver** — a new case instance pointed at the first one's
durable paths, opening its own handle under a new incarnation — and asserts the
store really holds one allocation per attempt.

### R1 — the reservation-only fixtures did not deliver the foundation

- **`scheduler.release` is no longer called a completion.** Your probe was right:
  the allocation is released while the stage stays queued and its dependents
  blocked. The helper is named `released`, records a `release` act, and is not a
  shortcut to anything.
- **The mislabelled facts are renamed to what they are.** Two aliased canonical
  principals were not two Authority teams and two `test_scope` strings were not
  two repository bindings. They are now `PRINCIPAL_ONE/TWO` and `SCOPE_ONE/TWO`,
  and the absent stronger facts are a recorded gap.
- **The alias collapse was a capacity reduction wearing a team's name**, and you
  predicted the consequence exactly: with both implementation slots taken, both
  principal groups were occupied, so no review could ever reserve. Each configured
  worker now has its own canonical principal; sharing one is exercised
  deliberately and separately.
- **The unrelated review really reserves.** Job D carries an ungated review, so
  the review lane is genuinely eligible while the implementation lane is full --
  without fabricating a completion to open a gated one. The unconditional
  `assertIn`, which appended the expected word to the actual value before
  checking it, is gone; the refusal's cause is compared unhelped.
- **Real authorized transitions are delivered.**
  `TheComposedOwnersSupplyAuthorizedTransitions` drives the composed fixture
  `PLAN.md`'s source map names — real Authority, real producers and reviewers,
  real review cycles, scripted engine seam — and reads offer, claim and
  completion out of the **manager's own receipts** and the projection's own
  state. A second case drives a real changes-requested correction and measures
  that it opens a **second episode**. Exported artifact:
  `trace-153855-composed.json`, zero violations, with reserve/offer/claim/complete
  on both `job-a/implementation` and `job-a/review`.
- **Composed, not subclassed.** My first form of that class subclassed the
  composed fixture and duly re-ran all 57 of its cases for two new assertions
  (28.6s). The fixture states that rule about itself; it is reused by calling its
  own `setUp` and helpers now, and the suite runs in 1.2s.

### R5 — the artifact did not bind the run it described

- **Executed sources are bound** by repository-relative path: scheduler,
  projection, manager, submission and the fixtures whose answers the records
  carry, not only the two new helper files.
- **The scenario digest distinguishes runs.** Order, releases, resolved
  principals and the actual tick count are inside the digested document; the four
  exported schedules now have four different digests.
- **`validate` re-derives the digest** and reports `scenario-digest-mismatch`.
- **The executed gap documents are retained** — the exporter no longer discards
  them for a hard-coded list. Four gaps travel with the set.
- **Unobserved is distinguished from owner-reported absence.**
  `unobserved_fields` names `runtime_id` and `session_id` as fields this driver
  never asks any owner about.

### Evidence

- `trace-153855.py` / `trace-153855.json` — four schedules: a-before-c,
  c-before-a, capacity-miss-with-unrelated-review, and the requested
  **reopen-and-continue**. Zero violations each, distinct digests, four retained
  gaps.
- `trace-153855-composed.py` / `trace-153855-composed.json` — the composed-owner
  authorized transitions. Zero violations.
- `run-153769-step-07..19.log`, `ledger-153769.json`.

Step 19: **124 tests pass** — the 38 new ones plus `test_scheduling` and
`test_sweep` unchanged.

### Candidate, 0664

- `tests/tools/scheduler_trace.py`
  `e2ca45118a51d27f10f5a45f9757536f4218ed6627ff9ad5aa77639cec5a316d`, 23622
- `tests/tools/test_scheduler_trace.py`
  `35f5f2826f35db3db61032f88a12b0294ea5f732cd782501c35309e153440497`, 51205

### Ledger

Author **36.817036/120s** across nineteen runs; 83.182964s remains. Non-zero
this claim: steps 7, 8, 11, 14 — all four my own test expectations or my own
exporter argument collision, all retained. The reviewer's
0.2879257239692379s research baseline stays separate and unreset. No live model
calls. Unmeasured: reads, greps and the edit scripts.

### Still not claimed

No certification of the scheduler contract. The scheduler-level schedules record
real reservations and releases but no owner-issued completion — the oracle refuses
any completion lacking its claim, which is why those artifacts carry none. The
three retained mismatches and the teams/repository-binding gap remain open. The
jsonschema 4.19.2-versus-4.26.0 gap is carried in every artifact.

## claim153951 — C1, C2 and C3 corrected; two of them by my own oracle refusing
## my own extractor

Review 2026-09-12T16:35:09Z accepted R3/R4 and requested changes on C1–C3. All
three were right. Same two test files and dossier evidence; no product file and
no prior test touched.

### C1 — terminal acts were accepted without their required evidence

- **`start` is now a completion prerequisite.** Your probe deleted it from an
  otherwise legal chain and got nothing; `REQUIRED_BEFORE["complete"]` now names
  reserve, offer, claim and start.
- **`review`, `integrate` and `correct` are no longer silently accepted.** They
  were in `ACTS` and checked by nothing, so a solitary performed review validated
  clean. `VALIDATED_ACTS` deliberately excludes them and `_unvalidated_acts`
  reports `unvalidated-act` — naming an act is not implementing its contract, and
  the honest answer while the rule is missing is that the act is unproved.
- **Offer acceptance is reported, not synthesized.** My first attempt emitted both
  an `accept` and a `claim` from the single `offer.settle` receipt — and the
  exactly-once invariant immediately refused my own extractor, because one
  operation identity cannot be two performed acts. That refusal was correct.
  Acceptance is discharged by the settlement receipt's own **state**, which the
  extractor checks, and its absence as a separate record is a recorded gap
  (`offer-acceptance-and-session-independence`) rather than a fabricated act.

### C2 — the extractor could turn a refusal into successful evidence

It read receipt-key presence. It now reads `state`: only `performed`/`adopted`
become performed records, carrying the receipt's **own** operation identity; a
refused receipt stays refused with the owner's own `detail` as its cause and no
operation id. `TheExtractorPreservesRefusedOwnerActs` covers refused admission and
refused claim, checks that the positive set is exactly `RECEIPT_STATES` minus
`refused` so a state added later is not silently treated as success, and confirms
the oracle would refuse a refusal that lost its cause.

### C3 — the composed exports did not carry the causal scenario

- **The actual graph and identities are exported.** `scenario_from` reads the Job
  store's own stage rows — including `depends_on`, which arrives as raw JSON and
  which my first form iterated character by character until the oracle reported
  `[/ ` as a missing prerequisite — plus the deployment's configured workers,
  participants, principals and bindings. The dependency oracle now has real edges.
- **Every episode is exported**, so the correction carries episode 1 and episode 2
  and the review between them, not just the live one.
- **The chronology is derived from durable owner facts and says so.** My first two
  attempts both imposed it: sorting on timestamps put untimestamped acts ahead of
  every receipt so `start` preceded its own offer; sorting globally by act rank
  made every stage's reservation precede every stage's completion, so
  `job-a/review` appeared to reserve before the implementation it depends on.
  Both were caught by the oracle. The key is now (episode, the Job's declared
  stage **ordinal**, the declared act rank, the timestamp) — the first two are the
  owners' own durable facts — and the docstring states plainly that a reader must
  not read a tick as an observed instant, because this fixture pins its clock.
- **Releases are recorded.** The correction reserved a second episode on the same
  worker and the oracle reported `overlapping-occupancy`: my extractor recorded
  every reservation and no release, so a superseded episode looked like it still
  held its worker. The allocation's own state and reason say otherwise.
- **One thing this trace honestly cannot prove, and the oracle says so.** The
  correction export carries exactly one violation,
  `successor-before-prerequisite` on `job-a/review`: the review only existed
  because implementation episode 1 really finished, but a superseded episode
  records no `ended_state` and no conclude receipt, so that completion is
  unreadable afterwards. I assert the violation and record
  `superseded-episode-completion` as a gap rather than manufacture the completion.
- **Composed sources are bound**: `tools/stage_execution.py`,
  `tools/single_worker.py`, `tests/tools/test_stage_execution.py`,
  `worker_manager/attempts.py` and `review_cycles.py` join the manifest.
- **The repository bindings are PROVED, not reported missing.** You were right
  that picking a pool which cannot see them is not a missing interface — and it
  is not missing: the composed `two_jobs` document binds each Job to its own
  nominated source (`source` and `source-b`), its own canonical target
  (`target-a`/`target-b`) and its own declared base.
  `test_two_independent_repository_bindings_are_configured` reads those from the
  real document. The remaining gap is narrowed to exactly what is still unproved:
  Authority **team membership**, which no Job-manager or composed document
  carries, and a **driven wrong-repository refusal**. The unit-pool gap is
  relabelled to say it is about that pool's visibility, not about the facts being
  absent from the system.

### Evidence

- `trace-153951.py` / `.json` — four scheduler-level schedules, zero violations
  each, distinct digests, four gaps.
- `trace-153951-composed.py` / `.json` — three composed artifacts. The accepted
  review carries reserve/offer/claim/**start**/complete/release on both
  implementation and review; the correction carries its **one honest violation**;
  the repository-binding case carries its bindings and gap.
- `run-153769-step-20..36.log`, `ledger-153769.json`.

Step 36: **129 tests pass** — the 43 new ones plus `test_scheduling` and
`test_sweep` unchanged.

### Candidate, 0664

- `tests/tools/scheduler_trace.py`
  `fcbf448e2dfbabe630c9828cfe2140bd697c79de4923aaf62081f2523c3a581d`, 27014
- `tests/tools/test_scheduler_trace.py`
  `6a3d817c476afa93fb1738560681370aec522ce9324c15e18e5bae30bd85663d`, 73790

### Ledger

Author **58.525035/120s** across thirty-six runs; 61.474965s remains. Non-zero
this claim: steps 20, 21, 23, 24, 25, 27, 28, 29, 30 — every one of them my own
extractor or my own expectation, and **five of them were my own oracle refusing my
own driver**, which is the foundation working as intended. All retained. The
0.2879257239692379s research baseline stays separate and unreset. No live model
calls. Unmeasured: reads, greps and the edit scripts.

### Still not claimed

No certification. The three retained product mismatches remain open, plus three
recorded gaps of my own: `offer-acceptance-and-session-independence`,
`superseded-episode-completion`, and Authority teams with a driven
wrong-repository refusal. The jsonschema 4.19.2-versus-4.26.0 gap is carried in
every artifact.

## claim154041 — D1 corrected by OBSERVING instead of sorting

Review 2026-09-12T16:51:07Z accepted C1/C2 and requested changes on D1. It was
right, and the fix is not another sorting key — it is not sorting at all.

### D1 — the extractor still imposed the causal order

Your retained input settles it: a claim recorded at 00:00:01 and an offer at
00:00:02 came out offer-then-claim, because my key put (episode, ordinal, act
rank) ahead of the timestamp. That contradicts the owners even with no ties, and
no additional key could fix it — **the order has to be observed, not chosen.**

- **The observer records at the tick boundary you verified.** `observing` calls
  public `job_manager.sweep` and then reads each stage's own evidence, emitting a
  record for whatever that tick newly showed, at the real tick number. The
  composed cases perform the fixture's ordinary acts and substitute the observer
  for its internal `drive_job` loop.
- **The final-dump extractor is deleted, not left beside its replacement.** A dead
  copy of the thing that caused this is an invitation to use it again.
- **The owners' instants now travel in the record and the oracle checks them.**
  `recorded_at` is a record member and `instants-disagree-with-order` refuses any
  trace whose order contradicts its own timestamps — so no extractor, mine
  included, can quietly reorder receipts to suit this oracle. Your exact
  counterexample is a negative case, with its in-order companion.
- **Within one tick, nothing is ordered.** Several facts are already true at a
  first observation — a producer's turn runs before the first sweep, so its start
  and completion are both visible at once. Prerequisites are compared on the
  logical tick: at-or-before satisfies, strictly-later is `out-of-order`.
  Requiring a sequence inside a tick would have been the extractor inventing one
  from the other side, and there are negatives for both halves.

**And the correction's violation is gone for the right reason.** Observing at the
boundary captures implementation episode 1 completing *before* the reviewer sends
it back, which is unreadable from a final dump. The correction artifact now
carries that `complete` and validates clean — I did not manufacture it, and the
`superseded-episode-completion` gap I previously recorded is no longer needed
because the evidence is really there.

### Two mistakes of my own this claim

- Each `observing` call restarted its tick counter at 1, so the oracle reported
  `regressing-time`. One run is one continuous clock.
- Deleting the dead extractor also deleted
  `test_an_accepted_review_is_a_real_authorized_transition`, which sat between it
  and the next case. The test count dropped from 46 to 45, I checked why, and
  restored it.

### Evidence

- `trace-154041.py` / `.json` — four scheduler-level schedules, zero violations
  each, distinct digests, four gaps.
- `trace-154041-composed.py` / `.json` — three composed artifacts, **all three
  with zero violations**. The accepted review carries
  reserve/offer/claim/start/complete/release on both stages; the correction now
  carries its implementation `complete`.
- `run-153769-step-37..45.log`, `ledger-153769.json`.

Step 43: **46 tests pass.** Per your instruction I did not repeat the 86 unchanged
`test_scheduling`/`test_sweep` tests, which were green at step 36 and are
untouched.

### Candidate, 0664

- `tests/tools/scheduler_trace.py`
  `9b2fa19621df9da6f888d41bd1d2e0bfb3e63b769c330415b305a98409b9e254`, 29289
- `tests/tools/test_scheduler_trace.py`
  `7f4480106cbea0fb5b6de0108759040a41bc0505c605b1a6828a7e7d96581a16`, 75951

### Ledger

Author **67.415878/120s** across forty-five runs; 52.584122s remains. Non-zero
this claim: steps 38, 39 and 40 — the restarted clock, the within-tick ordering
and a negative whose premise the tick rule had changed. All mine, all retained.
The 0.2879257239692379s research baseline stays separate and unreset. No live
model calls. Unmeasured: reads, greps and the edit scripts.

### Still open, not waived

No certification. The three retained product mismatches stand. My own recorded
gaps: `offer-acceptance-and-session-independence` (offer.settle is one
settlement and no session identity is recorded on this path) and Authority teams
with a driven wrong-repository refusal. Authorization evidence beyond the
settlement's state remains unrepresented and is reported as `unvalidated-act`
rather than accepted. The jsonschema 4.19.2-versus-4.26.0 gap is in every
artifact.

## claim154100 — the last D1 comparison: equal ticks no longer erase instants

Review 2026-09-12T17:01:19Z confirmed the live tick capture and the retained
episode-1 completion, and named one remaining comparison. It was right.

### The defect

`_instants_agree_with_order` checked that the record stream was chronologically
sorted, and `_ordered_within_attempt` compared only observation ticks. So a claim
the owner recorded at 00:00:01 and an offer it recorded at 00:00:02 — both first
visible in ONE sweep — passed: the stream was sorted, and equal ticks made them
concurrent. **A known contradiction was erased by the coarseness of my own
observation.**

### The correction

Prerequisite comparison now uses the OWNERS' instants whenever both the act and
its required predecessor carry one, for the same attempt **and episode**; a later
prerequisite refuses even at equal observation ticks. Where an instant is absent
the coarse tick is still used, because a coarse observation is better than an
invented order. No rank sorting is restored and no timestamp is discarded.

Equal ticks mean *this observer* could not separate two facts. They do not mean
the owners could not, and the oracle no longer confuses the two.

### The negatives, both from the retained reproduction

- **At the validator**: equal ticks with contradictory instants refuse; the same
  shape with the owners' order respected passes.
- **Through the actual `observed()` path**: the reviewer's exact snapshot —
  claim at 00:00:01, offer at 00:00:02 — is substituted at the public reader the
  observer uses, the real observer runs, both records land in one tick, and the
  oracle refuses. Its legal companion runs the same path on the genuine receipts
  and validates clean. The snapshot is synthetic and labelled; no live owner is
  changed by it.

One mistake of my own: the patched reader called itself, because the patch
replaces the very name the body looked up. The genuine reader is captured before
the patch now.

### Evidence

- `trace-154100.py` / `.json` — four scheduler-level schedules, zero violations,
  distinct digests, four gaps.
- `trace-154100-composed.py` / `.json` — three composed artifacts, all zero
  violations.
- `run-153769-step-46..50.log`, `ledger-153769.json`.

Step 48: **50 tests pass.** As instructed I did not repeat the 86 unchanged
`test_scheduling`/`test_sweep` tests or reopen accepted fixes.

### Candidate, 0664

- `tests/tools/scheduler_trace.py`
  `34964a53add26f511d9e935db5647d82a0f3a4a02f3c31b32f063cab7571b4a4`, 30640
- `tests/tools/test_scheduler_trace.py`
  `e30e108470348b995ce6e78e0ffb76d373174d68f16b0521bdbe92bc2f1e2941`, 80583

### Ledger

Author **72.771317/120s** across fifty runs; 47.228683s remains. One non-zero this
claim, step 47, the self-calling patched reader — mine, retained. The
0.2879257239692379s research baseline stays separate and unreset. No live model
calls. Unmeasured: reads, greps and the edit scripts.

### Still open, not waived

No certification. The three retained product mismatches stand, as do my recorded
gaps: `offer-acceptance-and-session-independence`, and Authority teams with a
driven wrong-repository refusal. Authorization evidence beyond the settlement's
state is reported `unvalidated-act` rather than accepted. The jsonschema
4.19.2-versus-4.26.0 gap is in every artifact.

## claim154142 — the last R1 item: both cases DRIVEN, with their refusals

D1 was accepted. The remaining original R1 scope was real Authority team
membership and allowed/wrong-repository cases through the composed fixture's own
owner operations, exporting actual refusals rather than configured root strings.
Both are now driven. The old request for a concrete failed setup is answered.

### The wrong repository, refused by its own owner

Job B is bound to Job A's declared base while still nominating its own source
repository, and the REAL line owner is then asked for that Job's line. The
checkpoint profile materializes from the nominated repository, so the base it
cannot find is the refusal. Its own sentence, quoted as it came:

    ProfileRefusal: Git declared-base checkout failed: fatal: ... --detach does
    not take a path argument '9ef75b80909da5da5e7e49cd4b9926013ed691...'

The tool treats a revision the repository does not contain as a path, which is
precisely what a cross-repository base looks like from inside `source-b`. The
base digest appears in it. The legal companion immediately after creates both
Jobs' lines from their own repositories without incident.

### Authority team membership, as this Authority actually models it

`authority/identity.py` states the grammar -- "a participant is team.member" --
and `principals.principal_for_endpoint` gives each endpoint its own principal by
default. So a **team is the participant's own prefix**; there is no separate
membership relation to configure, and what a second team's participant lacks is
CAPABILITY. Configuring a receipt participant from team `other` and asking the
real composition produces:

    policy/denied: 'other.reviewer' writes this deployment's review receipt and
    holds no review capability in scope:deployment; a receipt is written by the...

That is a driven refusal, not a report that something could not be seen. Every
configured participant here is read from the grammar and is in team `baton`.

The residual gap is recorded precisely: if team-scoped authorization is wanted as
its own fact, the Authority needs a membership relation and a team-scoped
capability decision, and **neither exists to drive**. That is the exact missing
seam, named rather than gestured at.

The older unit-pool gap is narrowed to say only what it still claims: that THIS
pool cannot see either fact, with pointers to the two cases that drive them.

### Evidence

`trace-154142-composed.py` / `.json` -- five composed artifacts, all zero
violations, now including `composed-wrong-repository-refusal` and
`composed-second-team-refusal` carrying the two owner sentences above.
`run-153769-step-51..53.log`, `ledger-153769.json`.

Step 52: **52 tests pass.** I did not repeat the 86 unchanged tests or reopen D1.

### Candidate, 0664

- `tests/tools/scheduler_trace.py`
  `34964a53add26f511d9e935db5647d82a0f3a4a02f3c31b32f063cab7571b4a4`, 30640 --
  **unchanged this claim**
- `tests/tools/test_scheduler_trace.py`
  `d505930f60b7c5e978f12f5d2a79b8e2983a2574118bde8ff6e056108fab248c`, 86945

### Ledger

Author **77.300774/120s** across fifty-three runs; 42.699226s remains. **No
non-zero runs this claim** -- both new cases passed first time. The
0.2879257239692379s research baseline stays separate and unreset. No live model
calls. Unmeasured: reads, greps and the edit scripts.

### Still open, not waived

No certification. Queued foundation requirements: offer-acceptance /
session-independence, and actual review/test/import authorization -- still
reported `unvalidated-act` rather than accepted. Separate retained product gaps:
explicit-fallback, priority/chronology, composed-continuation. Plus the newly
recorded `authority-team-membership` seam. The jsonschema 4.19.2-versus-4.26.0
gap is in every artifact.

## claim154186 — I was wrong about two seams; both are now driven

Review 2026-09-12T17:15:58Z corrected my `authority-team-membership` gap: it
treated absent capability as an unavailable public setup. That was wrong, and
checking properly showed I had made the SAME mistake about offer acceptance.

### The team matrix, driven — correcting my own claim

I recorded that a second team could not be authorized because this build has no
membership relation to drive. False. `Authority.grant_capability` is exactly the
public seam, and the three-case matrix now executes:

1. another team, **no grant** → `policy/denied`
2. another team, **grant at `scope:elsewhere`** → refused
3. another team, **grant at the Work's own scope** → **COMPOSES**, with
   participant `other.reviewer`, principal `principal:other.reviewer` and
   `holds_capability` true.

A team here is the endpoint's own prefix (`identity.py`: "a participant is
team.member") and authorization is a capability AT A SCOPE, not a membership
lookup. No membership API and no product change is needed for the positive. The
gap is deleted, not reworded. **This is configuration proof, not completed
multi-team execution.**

### Offer acceptance — the same mistake, found by checking

I had claimed twice that this build journals no separate acceptance, reasoning
from the fact that emitting `accept` and `claim` from one settlement receipt was
refused by the exactly-once invariant. That refusal said something about my
extraction, not about the build. The offer is its own owner: `OFFER_STATES`
contains `accepted`, the row carries its own `accepted_at`, and
`offers._require_accepted` guards the claim.

`accept` is a first-class act again, read from the offer row with the owner's own
instant, and `claim` requires it. Both composed artifacts now carry
`accept` on implementation and review. `UNREPRESENTED_EVIDENCE` is empty.

The lesson, written into the module beside the constant: **a refusal encountered
while extracting says something about the extraction, not about what the system
can do.** Twice was enough to record it.

### Session identity — narrowed to what is actually true

`agent_sessions_of` is public and `AGENT_SESSION_COLUMNS` carries posture, epoch,
participant and provider session id, so the seam exists. This composed
implementation/review path simply opens none — `agent_sessions_of` answers an
empty list for every attempt in the run. The gap now says exactly that, which is
a different statement from "no session identity is recorded".

### Evidence

`trace-154200.py` / `.json` — four scheduler-level schedules, zero violations.
`trace-154200-composed.py` / `.json` — five composed artifacts, zero violations,
now including `accept` on both stages and `composed-second-team-matrix`.
`run-153769-step-54..61.log`, `ledger-153769.json`.

Step 59: **52 tests pass.** I did not repeat the 86 unchanged tests or reopen D1.

### Candidate, 0664

- `tests/tools/scheduler_trace.py`
  `f909f7259339dc755839fa5635eddc6e622cfb0abeefca64cd57a448929d0c62`, 31589
- `tests/tools/test_scheduler_trace.py`
  `b395eadd26243386a514a10c72c179a5dd23838be6e4f4e6c7de1af67774fb18`, 91611

### Ledger

Author **87.561053/120s** across sixty-one runs; 32.438947s remains. Non-zero this
claim: steps 56 and 58 — synthetic chains that needed the restored `accept`, and
the composed case still asserting the gap I had just disproved. Both mine, both
retained. The 0.2879257239692379s research baseline stays separate and unreset.
No live model calls. Unmeasured: reads, greps and the edit scripts.

### Still open, not waived

No certification. **Actual review/test/import authorization evidence** remains the
queued item I have not yet driven; `review`, `integrate` and `correct` stay
reported as `unvalidated-act` rather than accepted. Session identity is not
exercised on this path. The three retained product gaps —
explicit-fallback, priority/chronology, composed-continuation — stand. The
jsonschema 4.19.2-versus-4.26.0 gap is in every artifact.

## claim154239 — actual review/import authorization, from the Authority itself

The team matrix and owner-recorded offer acceptance were accepted. The queued
foundation item was actual review/test/import authorization bound to the exact
subject. That is now driven.

### The authorization is the Authority's own answer

Job A's ordinary composed integration runs, and the records come from
`authority.receipts(proposal_id)` -- the public reader -- rather than from an
assertion here. Each receipt supplies its own **actor**, its decision's
**principal**, **effective scope** and **policy generation**, its **receipt
identity** and its **instant**, all bound to the exact proposal. The scope is
compared against the deployment's own configured scope rather than accepted as
given, and the Authority really answers all three kinds an import needs --
review, approval and integration.

A helper asserting a passed receipt would have proved nothing, which was the
review's point. What makes this evidence is that the Authority was asked, and
that the oracle then re-derives the relation from the records alone.

### `review` and `integrate` are validated acts now, not silently accepted

They were reported `unvalidated-act` because this module had no rule for them.
They have one: `SUBJECT_AUTHORIZATION` is keyed by **subject**, not by attempt,
because a review and an integration are decisions about a proposal rather than
steps of one worker attempt. Nothing may be integrated that was not reviewed —
**of that same subject**. And `AUTHORIZATION_MEMBERS` requires each to name its
decider, principal and receipt identity, because a receipt that does not say who
decided is not an authorization however positive its outcome word.

Three negatives: an integration with no recorded review of its subject; an
integration whose only review is of a **different** proposal; and an
authorization naming no decider. `correct` remains deliberately outside
`VALIDATED_ACTS` — this module still has no rule for it, and saying so is the
honest answer.

### Evidence

`trace-154239-composed.py` / `.json` — six composed artifacts, zero violations,
now including `composed-authorization-receipts` carrying real `review` and
`integrate` records. `run-153769-step-62..63.log`, `ledger-153769.json`.

Step 62: **56 tests pass**, first run. I did not repeat the 86 unchanged tests.

### Candidate, 0664

- `tests/tools/scheduler_trace.py`
  `71eef6dce8575a027e52ef7f12a66cb7efe715a038a2928b2d52d7422c10b697`, 34785
- `tests/tools/test_scheduler_trace.py`
  `28c0c5e1d3e7b4b22a889a86f8d4cdc1f20ac828f5a8cb307d497a493d331b71`, 97598

### Ledger

Author **91.6/120s** across sixty-three runs; ~28s remains. **No non-zero runs
this claim.** The 0.2879257239692379s research baseline stays separate and
unreset. No live model calls. Unmeasured: reads, greps and the edit scripts.

### Still open, carried exactly

**Session independence remains unproved and I am not faking it.** The API exists
(`agent_sessions_of`, `AGENT_SESSION_COLUMNS` with posture, epoch, participant
and provider session id) and the observer has a branch that reads it, but the
composed implementation/review/integration path this record drives opens no agent
session, so that branch is never exercised and no `session_id` appears in any
artifact. Proving it needs a composed path that opens one; that path is the exact
remaining limitation.

Also still open: `correct` has no validator rule; the three retained product gaps
(explicit-fallback, priority/chronology, composed-continuation); and the
jsonschema 4.19.2-versus-4.26.0 environment gap carried in every artifact. No
certification is claimed.

## claim154281 — the authorization erasures corrected, and a ledger correction

Review 2026-09-12T17:30:56Z confirmed the real receipts but found my
authorization addition erased two things and dropped most of the decision. All of
it was right.

### Ledger correction first

My previous entry wrote author spending as "approximately 91.6/120s". The
measured figure was **92.44196586098406s**. Approximating a measured number in a
ledger is exactly the sort of softening this record exists to prevent, and the
exact value is what stands.

### The disposition was thrown away

`authorized()` recorded every receipt as `performed` without reading its
disposition, so a review recorded `changes-requested` emitted a positive
authorization and validated clean. `POSITIVE_DISPOSITION` now names each kind's
own accepting word — `passed`, `accepted`, `approved`, `integrated` — and a
non-accepting decision is `nonaccepting-authorization` and authorizes nothing
downstream.

### The owner instants were ignored

A review recorded at 00:00:02 after an integration at 00:00:01 validated clean,
because the subject rule compared only ticks and both were tick 1. It now uses
the owners' instants when both exist, with the tick as fallback — the same rule
the attempt chain already followed. I had fixed this once for attempts and not
carried it here.

### The decision context was dropped, and my comment about it was false

The records carried no disposition, candidate digest, target, effective scope or
policy generation. Worse, the comment said scope and policy "travel with it"
while the test asserted the scope and then discarded it. They travel now, in one
`authorization` member, and every one of them was already on the receipt — no new
API was needed. `AUTHORIZATION_CONTEXT` requires them, and a mismatched candidate
or target between a judgment and the import is `mismatched-authorization`.

A null `policy_generation` is legitimate: only the approval binds one, and the
positive asserts exactly that rather than demanding a value the other kinds do
not carry.

### An import needs all three judgments

The first rule required a `review` alone, so a candidate with no verification and
no approval validated. `integrate` now requires positive `verify`, `review` and
`approve` of the same subject. The composed positive asserts all four acts and
all four kinds come back from `authority.receipts`.

Six new negatives: a non-accepting review; a review recorded after its
integration; each of the three judgments deleted in turn; a mismatched candidate;
and a decision missing its scope.

### Evidence

`trace-154281-composed.py` / `.json` — six composed artifacts, zero violations,
with `composed-authorization-receipts` now carrying `verify`, `review`, `approve`
and `integrate`. `run-153769-step-64..66.log`, `ledger-153769.json`.

Step 65: **62 tests pass.** I did not repeat the 86 unchanged tests or rework the
accepted D1/team/offer/capacity fixes.

### Candidate, 0664

- `tests/tools/scheduler_trace.py`
  `c8525f3df97f277dbfb887ef9bab301e352cf00f82d8c84ba5c91be6f9b32dd2`, 38767
- `tests/tools/test_scheduler_trace.py`
  `5c0422eb563052055d21adcf0eb1ee952afca8fc515b78d5cadf661adecfedc8`, 103582

### Ledger

Author **100.38120128700393/120s** across sixty-six runs; **19.61879871299607s**
remains. One non-zero this claim, step 64 — the new negatives landed in the
composed class, which had no `codes` helper. Mine, retained. The
0.2879257239692379s research baseline stays separate and unreset. No live model
calls, no dependency installation. Unmeasured: reads, greps and the edit scripts.

### Still open

Session independence remains unproved and unfaked: the API exists and the
observer reads it, but this composed path opens no agent session. `correct` still
has no validator rule. The three retained product gaps stand. The jsonschema
4.19.2-versus-4.26.0 gap is in every artifact. No certification is claimed.

## claim154323 — the authorization context checked, not merely carried

Review 2026-09-12T17:37:27Z accepted the disposition, late-review and
all-three-judgments corrections and found one more: carrying the decision context
is not the same as checking it. Three one-field mutations of the REAL receipts
each validated clean.

### A conflation of mine, corrected

I wrote that "only the approval binds a policy generation". That read the
RECEIPT's top-level `policy_generation`, which is legitimately null for the other
kinds — **but it is not the field the exporter reads**.
`decision.policy_generation` is required and positive on every
`AuthorizationDecision`. My context check only asked for truthiness on a field I
had mislabelled, so a decision missing it passed. It is now required to be a
positive integer, and the mislabelled comment is replaced by the distinction.

**No all-generations-equal rule is invented.** Policy legitimately changes between
decisions, so each names a positive generation of its own and none must match
another's — with a companion case proving a chain of differing generations is
accepted.

### The role was never compared

A review whose decision role was `integrate` validated clean. `EXPECTED_ROLE`
names each act's own role now: a decision made in another role is another
decision.

### The scope was checked for presence, not agreement

A foreign `effective_scope` validated clean, because the check only asked whether
the field had a value. The artifact now carries an
`authorization_references` member — what an **owner** says the subject is
governed by, read from the deployment independently of the receipts — and the
validator **compares** each decision's scope against it.

### Evidence

`trace-154323-composed.py` / `.json` — six composed artifacts, zero violations,
`composed-authorization-receipts` carrying verify/review/approve/integrate with
their full decision context. `run-153769-step-67..69.log`, `ledger-153769.json`.

Focused first, as instructed: step 67 ran the authorization class alone (21
tests), then step 68 the complete focused module — **66 tests pass**. I did not
repeat the 86 unchanged tests.

### Candidate, 0664

- `tests/tools/scheduler_trace.py`
  `654ad36213c997a0697bd73ef7016e36194ab939a03be13f3606bc9df689b58e`, 42405
- `tests/tools/test_scheduler_trace.py`
  `57a5027f48b146931af4b6833ec7391b30a280c7d38275ec8371efb74413c5f4`, 106993

### Ledger

Author **108.39710617496166/120s** across sixty-nine runs; **11.60289382503834s**
remains. **No non-zero runs this claim.** The 0.2879257239692379s research
baseline stays separate and unreset. No live model calls, no dependency
installation. Unmeasured: reads, greps and the edit scripts.

**A note on the remaining budget.** 11.6s is roughly four focused-module runs.
That is enough to correct something small; it is not enough to drive a new
composed path. If the next finding needs one, the honest answer will be to return
the exact attempted setup rather than start what I cannot finish.

### Still open

Session independence remains unproved and unfaked — the API exists and the
observer reads it, but this composed path opens no agent session. `correct` still
has no validator rule. The three retained product gaps stand. The jsonschema
4.19.2-versus-4.26.0 gap is in every artifact. No certification is claimed.

## claim154358 — the owner reference is required, and the budget is nearly spent

Review 2026-09-12T17:42:54Z accepted the three context mutations and found the
last hole in the same check: **deleting `authorization_references` disabled the
scope comparison entirely**, so a missing map — or a foreign scope *with* a
missing map — validated clean.

### A comparison that becomes a no-op is not a check

An authorization whose subject has no owner-declared scope is now
`unreferenced-authorization`: unproved, never optional. A foreign scope with no
reference reports the absent reference rather than being excused by it, and an
empty or null reference scope is treated the same as a missing one. A trace
carrying no authorization acts needs no references at all — the rule runs only
for the acts that make a claim, and there is a case for that too.

The leftover nullable-decision-generation comment beside `authorized()` is
corrected: it described the receipt's nullable top-level field, not
`decision.policy_generation`, which is required and positive on every
`AuthorizationDecision`.

### Evidence

`trace-154358-composed.py` / `.json` — six composed artifacts, zero violations,
now carrying `authorization_references`. `run-153769-step-70..72.log`,
`ledger-153769.json`.

Targeted first as instructed: step 70 ran the authorization class alone (25
tests), then step 71 the final focused module — **70 tests pass**. I did not
repeat the 86 unchanged tests.

### Candidate, 0664

- `tests/tools/scheduler_trace.py`
  `35d5afd22715a47ce94d04f714d6de390d4bed7fe28c7f7233217c3a3850396f`, 43312
- `tests/tools/test_scheduler_trace.py`
  `1f376d9d3127b2d55ac88908b913fcea067561824febb2a9844bcea8732e8f06`, 108902

### Ledger — and a plain statement about what is left

Author **116.65264648597804/120s** across seventy-two runs. **3.34735351402196s
remains.** No non-zero runs this claim. The 0.2879257239692379s research baseline
stays separate and unreset. No live model calls, no dependency installation.
Unmeasured: reads, greps and the edit scripts.

**3.35 seconds is one focused-module run and nothing else.** I flagged last claim
that 11.6s was roughly four runs; this is the floor. I am not requesting an
increase — that is the owner's call and the cap was accepted deliberately. But the
next finding, however small, cannot be both fixed and verified within it: a
targeted class run alone costs ~2.8s, leaving no margin for a second attempt if
the first is wrong.

So the honest position for the next claimant, whoever it is: either the remaining
budget is dispositioned, or the next correction should be returned with its exact
attempted setup rather than half-verified. I would rather say that now than
discover it mid-claim.

### Still open

Session independence remains unproved and unfaked — the API exists and the
observer reads it, but this composed path opens no agent session. `correct` still
has no validator rule. The three retained product gaps stand. The jsonschema
4.19.2-versus-4.26.0 gap is in every artifact. No certification is claimed.

## claim155666 — the sessions are real now, and two of my own readers were wrong

Owner155646 authorized the continuation at cumulative 165s author / 40s reviewer,
prior spending preserved: **demonstrate nonempty sessions and independent roles
first, then composed alternate-order/reopen/correction evidence.** Both files are
the same two; no product file and no existing test was touched.

### The session seam was asked before anything was written

`probe-155666.py`, `probe-155666-review.py` and `probe-155666-correction.py` are
retained with their own run logs (steps 73–77 and 81, including three early
forms of the first probe that named the wrong table and the wrong column, each
kept in its own log). They asked the owners the questions instead of guessing:
the composed attempt IS activated with its Work, its Authority and its assignment
participant, and `open_agent_session` answers for it.

**Real sessions, at the public seam.** The producer's attempt now holds a consent
session and an execution session, the reviewer's attempt holds its own execution
session, each opened through `open_agent_session` under the port of the worker
that actually PREPARED that attempt, against a profile certified by
`certify_agent_session_profile` on the deployment's own control store — and each
bound to a scripted provider id through `adopt_provider_session`. What is
scripted is the id a provider would have returned; the epoch allocation, the
profile check, the participant comparison and the row are the owner's.

**Independent roles, asked of the owner rather than asserted.** The producer's
port asks for the reviewer's execution session and is refused: *"this authority
session acts for 'baton.claude' and attempt … is assigned to 'baton.reviewer'"*.
That refusal is recorded with its own cause.

### Two defects in my own reader that only a real session could show

**The session identity was not one.** The observer spelled a session
`posture:epoch`. Both composed attempts opened execution epoch 1, so the
producer's session and the reviewer's session were **the same string** — a rule
comparing them would have compared a name with itself. `session_reference` is the
§3.1 four-part reference, and the validator refuses a reference that does not
name the record's own attempt, posture and epoch.

**The dedup key collapsed two owner facts into one.** The key was
`(stage, episode, act)`, so an attempt holding a consent session AND an execution
session recorded exactly one of them. The session's own reference is part of the
key now.

### And a third, found by the alternate-order case

The observation clock and the seen set lived on the `TestCase`, not on the trace.
The alternate-order case drives two deployments in one test, so the second run
inherited the first's clock and its seen set — `job-b/implementation`'s
completion, already seen under the same stage id in the first deployment, was
**silently dropped** from the second trace, and its review then looked like a
successor reserved before its prerequisite. One run is one trace is one clock.

### The manifest could say anything, and did

`unobserved_fields` was a module constant copied into every artifact, so the
composed exports declared `runtime_id` unobserved **while carrying runtime ids
read from the manager's own rows**. Nothing compared the declaration with the
records. A trace declares what ITS driver looked at now, and
`unobserved-field-recorded` refuses an artifact whose records contradict it;
`undeclared-observation` refuses one that declares nothing, or that names a field
this oracle knows nothing about.

### A rule I wrote and then removed

I wrote a `session-shared-across-attempts` rule and could not build its negative:
the four-part comparison requires the reference's first component to BE the
record's attempt, so two attempts can never carry one well-formed reference. **A
rule that cannot fail is not a rule.** It is gone, and the case that does fail —
one attempt carrying another's reference — is kept under the mismatch code.

### `correct` has a rule, after six claims of saying it did not

`_corrections_name_their_cause`: a correction names a stage, an attempt and an
episode after the first; the episode it supersedes is in the trace for the same
stage at or before its own tick; a record on that Job's review stage is in the
trace at or before it — **a restart is not a requested correction, and the review
that asked for it is the difference** — and it carries the owner evidence
locator it was read from. The composed correction case records the act from the
review attachment the reviewer's verdict ENDED, read through `assignment_of` and
`review_for_attempt`.

**And what that act still cannot carry, named exactly.** The reviewer's
DISPOSITION is the content of the judgment. `review_cycles.verdict_of` proves and
answers it — but only from a verdict id, and no public reader answers a verdict
from the attachment that ended on it: `REVIEW_ATTACHMENT_COLUMNS` carries no
`verdict_id`. The act is bound to the ended attachment, which is real owner
evidence, and the disposition is recorded as a gap rather than reconstructed from
the journal key `verdict_of` uses internally. **The minimum missing interface: a
public reader answering the recorded verdict for an attachment, or a
`verdict_id` on the attachment row.**

### Alternate order, over the composed owners

Two real Jobs on two real Works, two producers with their own participants and
their own lines, driven A-then-B and B-then-A in two separate deployments. Both
satisfy the same oracle, their scenario digests differ because their inputs
really differ, and the completion order each records is the order it actually
took. Both runs carry reserve/offer/accept/claim/start/complete for both Jobs.

### Evidence

`trace-155666-composed.py` / `.json` — **nine composed artifacts, zero violations
each**: `composed-role-sessions` (three real sessions), both
`composed-alternate-order-*` runs, `composed-accepted-review`,
`composed-correction` (carrying the `correct` act), the two repository-binding
cases, the second-team matrix and the authorization receipts.
`trace-155666.py` / `.json` — the four unit-pool schedules re-exported under the
current candidate bytes, zero violations each, four retained gaps.
`run-153769-step-73..89.log`, `ledger-153769.json`.

Step 89: **93 tests pass** — the 70 inherited plus 23 new. I did not repeat the
86 unchanged tests.

### Candidate, 0664

- `tests/tools/scheduler_trace.py`
  `6a67fd9c939447743fe13ba756268a55ffe7d9b98b67f24ccb010cf1b725ecfd`, 58974
- `tests/tools/test_scheduler_trace.py`
  `623c6e056a0f14a6d43ea6d1e2f28ad81722ef89fc6850144f7f4ba62fd5229c`, 140875

### Ledger

Author **153.473502/165s** across eighty-nine runs; **11.526498s remains** under
owner155646's cumulative cap, with the prior 116.65264648597804s preserved and
unreset. Non-zero runs this claim: steps 73, 74, 75 (the probe's early forms),
78, 79, 82, 84 and 86 — all mine, all retained; step 86 is an exporter invoked
with a relative path from the wrong directory and cost 0.0065s. The
0.2879257239692379s research baseline stays separate. No live model calls, no
dependency installation. Unmeasured: reads, greps and the edit scripts.

### What I did NOT do, and why

**The composed REOPEN was not attempted.** Owner155646 asked for composed
alternate-order/reopen/correction evidence; alternate order and correction are
delivered and reopen is not. At the point the choice arose I had ~19s left with
the two exports and the final module run still owed (~8s), and a composed reopen
means constructing a fresh deployment over the same durable store through a path
this fixture has no helper for. Starting an unknown composed path with ~11s of
margin would have produced a half-driven attempt and no verification, which is
exactly what I said last claim I would not do. The unit-pool reopen schedule
(`reopen-and-continue`, fresh driver over the same durable files, exactly-once
asserted across it) is re-exported under the current bytes and stands; the
composed one is remaining scope.

### Still open

Composed reopen, as above. The reviewer's disposition seam, named exactly above.
The three retained product requirements — explicit fallback, priority/creation
ordering, composed continuation — stand untouched. Authority team membership
remains unestablished. The jsonschema 4.19.2-versus-4.26.0 gap is in every
artifact. **No certification is claimed.** No mutating Git operation was
performed.

## claim155821 — both findings were right, and one of them corrects a claim of mine

Review 2026-09-12T23:32:26Z requested two validator corrections. Both were real
defects in rules I wrote last claim, and R1 additionally disproved a gap I filed.
Corrections are inside the same two new test files and the dossier evidence; no
product file and no existing test was touched.

### R1 — a reservation was accepted as the cause of a correction

`_corrections_name_their_cause` treated **any** performed record on a review
stage as the judgment, so the reviewer's mutation — the retained real correction
artifact with every review-stage act except `reserve` deleted — still validated
clean. A reviewer holding a slot has judged nothing, and that rule could not tell
a requested correction from an unreviewed restart.

**And I was wrong about the seam.** I recorded a gap claiming no public reader
answers a verdict from its attachment, and asked for a new API. The reviewer
disproved it with the build's own readers in a real composed run:
`ending.settlement_of(job, "job-a/review", 1)` answers `evidence.verdict_id`, the
outcome and the **routed** next attempt, and `review_cycles.verdict_of` proves and
answers the committed `changes-requested` disposition with its attachment,
checkpoint, line and reviewer identity. **The gap is withdrawn, not softened.** A
false gap is worse than none: it would have sent the next author to write product
code for a reader that already exists. No product change was needed.

A correction now carries the judgment in a `correction` member, and the rule
checks it: the whole context present; the settlement's outcome is `correction` and
the disposition `changes-requested` — an accepted or rejected judgment authorizes
none; the attempt the judgment **routed** to is the attempt the record is about;
and the reviewed attempt it cites was **claimed** in this trace at or before it.
The reviewer's exact reserve-only negative now fails, with its own case.

### R2 — the reference and the assignment were carried but not compared

Two holes, both mine, both exactly as reported. The reference comparison read
three components and never looked at the fourth, so changing only the provider
component of a real retained reference to `foreign-provider-id` validated clean.
And the participant rule asked for a nonempty identity and compared it with
nothing, so changing a real reviewer session's participant to `other.unassigned`
validated clean.

All four components are compared now, with `-` kept as the owner's legitimate
representation of an epoch no provider id has been adopted for. And the artifact
carries `assignment_references` — what `assignment_of` answered for each attempt,
read independently of the session row being judged — so an execution session's
participant, generation and Work are **compared** against the owner's own
assignment, and a session whose attempt has no declared assignment is
`unreferenced-session`: unproved, never optional. The consent posture's null
assignment semantics are preserved; its Work is still compared.

Both of the review's retained mutations are asserted **over the real exported
artifact** in the composed session case, not over a synthetic stand-in, plus the
no-reference case; each also has an offline synthetic negative.

### Evidence

`trace-155821-composed.py` / `.json` — nine composed artifacts, **zero violations
each**, the correction now carrying its verdict and the sessions their assignment
references; `trace-155821.py` / `.json` — the four unit-pool schedules re-exported
under the corrected bytes, zero violations each.
`run-153769-step-90..93.log`, `ledger-153769.json`.

Targeted first as instructed: step 90 ran the offline negatives and the two
affected composed cases (61 tests) before anything else; step 93 the final
focused module — **105 tests pass**. I did not repeat the 86 unchanged tests.

### Candidate, 0664

- `tests/tools/scheduler_trace.py`
  `09c170a92ef67e2f73a9b5b6384ad6c8edd4687c412bcf4a9b24b316a19cb286`, 67256
- `tests/tools/test_scheduler_trace.py`
  `8dd374ddd013d8a1e284e8d5ff1661718a342d95963d48d155f9ed3dcdda2d33`, 148727

### Ledger — and the cap is now at its floor

Author **162.033855/165s** across ninety-three runs; **2.966145s remains**. No
non-zero runs this claim: steps 90, 91, 92 and 93 all succeeded first time. The
0.2879257239692379s research baseline stays separate and unreset. No live model
calls, no dependency installation. Unmeasured: reads, greps and the edit scripts.

**2.97 seconds is less than one focused-module run,** which costs 4.14s. I said at
3.35s last time that the next finding could not be both fixed and verified within
the remaining margin; that is now strictly true — there is not even one
verification run left. I am not requesting an increase; that is the owner's call.
But the honest position for the next claimant is that either the remaining budget
is dispositioned, or the next correction is returned with its exact attempted
setup and no verification at all.

### Still open

Composed reopen, not attempted and unchanged. Full four-Job/two-team/repository
composition and both whole Jobs reaching terminal integration. Session
continuity. The three retained product requirements — explicit fallback,
priority/creation ordering, composed continuation. The jsonschema
4.19.2-versus-4.26.0 gap, in every artifact. The superseded
missing-team-membership API claim is **not** revived: the scoped second-team
configuration matrix stands accepted, and its composition into executed
multi-team scheduling remains open. No certification is claimed. No mutating Git
operation was performed.

## claim155914 — R1 completed, and three scenarios that had been open since the first slice

Owner155911 (Slawomir, 2026-09-12T23:50:14Z) raised the caps to cumulative 300s
author and 300s reviewer, preserving all spending, and asked for the remaining R1
context correction from review 2026-09-12T23:45:06Z and then the accepted
same-two-file composed continuation. Both are here. Same two files; no product
file and no existing test touched.

### R1 — the completion, and the same lesson a third time

The rule indexed claimed reviews by attempt id and tick alone. Relabelling the
retained review attempt's records to `job-b/review` while the correction stayed on
`job-a` validated clean; so did changing `reviewer_participant`,
`reviewer_principal` or `review_assignment_generation` one at a time. **Every one
of those members was required to be present and compared with nothing** — the same
defect shape as the session participant in R2 and the authorization scope before
it.

The judgment now carries its own subject stage, episode and superseded attempt,
and the rule binds all of it:

- the judgment is about **this Job's** review stage at the episode it names, and
  that exact attempt was **claimed** in this trace at or before the correction;
- the attempt it **superseded** is the one this trace recorded for the previous
  episode of the corrected stage;
- the reviewer it names is compared against `assignment_references` — participant,
  principal and generation — against the **allocation principal** this trace
  recorded for the reviewing attempt, and against the correction record's own
  identity. A reviewer nothing independently reports is `unreferenced-correction`.

All four retained mutations are asserted **over the real exported artifact**, and
each has its own offline negative.

### The composed reopen, which I declined to start last claim

A fresh `operations_from` composition under its own incarnation over the same
durable job and control files — the composed analogue of the unit pool's
`fresh_driver`. Job A's implementation completes, the deployment is reopened at
that boundary, and **the reopened deployment admits, claims and completes the
review**: the same durable attempt identities, one allocation per attempt, no
operation performed twice, and every review act at or after the recorded `reopen`.

The engine object is shared across the boundary, and that is disclosed in the
exported scenario rather than hidden: this is a **manager** restart at a point
where nothing is running, not a host restart.

### Session continuity, read as the contract actually states it

The pinned acceptance says a session "never resumes, forks, promotes or
re-prompts after transport loss" and that "a lost transport ENDS THE EPOCH". So
what continues is the **worker**; what does not is the session. `handle_transport_loss`
answers `resume: false`, `reprompt: false`, moves the axis to `unknown` and the
slot to `recovery-required`; a second opening before recovery is **refused by the
slot's own rule**; `release_slot` demands positive evidence that the old provider
session cannot still act; and the next epoch is 2, allocated by the database. The
second epoch is deliberately left unadopted, so a real artifact now carries the
owner's `-` representation that only a synthetic case had before.

**A correction of mine, found by measurement.** The first form ran the producer's
turn to completion first, and the premature reopening was then refused by
`_live_assignment` — "holds no live assignment" — before the slot rule was ever
reached. A true refusal about a different thing; asserting it would have been a
case that passes while proving nothing about the posture slot.

### Both Jobs to the one integrator that serializes them

Two real Works, two producers, two reviewers, two lines, one canonical target.
Both Jobs traverse implementation and review to **completed**; job-a's integration
is admitted and integrating with the integrator allocated; job-b's integration
stays queued with its `admit` owed and **deferred**, carrying the manager's own
sentence: *"stage 'job-b/integration' has eligible implementation workers but
every effective worker/principal capacity is reserved or recovery-required"*. No
`reserve` is called by hand to manufacture a cause — that would have meant
re-implementing the manager's stage composition to get a refusal it already
publishes.

**Another correction of mine.** The first form called the fixture's own
`both_accepted`, which drives the whole traversal internally, so every act was
first seen at tick 1 and the dependency oracle correctly reported each review
reserved before its implementation's completion. The observer goes in the loop.

**And the retained explicit-fallback requirement is observed in a composed run for
the first time — still as a GAP.** job-a's integration allocation records
`selection_outcome: "fallback"` with a `preferred_worker_id` this deployment did
not use. The requirement is unchanged and still open; this only moves the
observation from the unit pool to a composed run.

### Evidence

`trace-155914-composed.py` / `.json` — **twelve composed artifacts, zero violations
each**, now including `composed-session-continuity`, `composed-reopen-and-continue`
and `composed-two-jobs-one-integrator`. `trace-155914.py` / `.json` — the four
unit-pool schedules re-exported under the current bytes, zero violations each.
`probe-155914.py`, `probe-155914-session.py`, `probe-155914-integration.py` with
their own logs — each asked the owners before a test asserted anything.
`run-153769-step-94..111.log`, `ledger-153769.json`. Step 109: **115 tests pass**.

### Candidate, 0664

- `tests/tools/scheduler_trace.py`
  `f26cef58191e724e91a8176bad087af292333f18e339f7c25059522adb5205c6`, 72785
- `tests/tools/test_scheduler_trace.py`
  `d12dff70d176b2b2e09d010b4917c7c788ca05c68fcf9124d77bc54ac580f777`, 180112

### Ledger

Author **190.152053/300s** across one hundred and eleven runs; **109.847947s
remains** under owner155911's cap, with the prior 162.033855s preserved and
unreset. Non-zero runs this claim: steps 94, 97's predecessor 96 series and 99,
102, 104, 105 — the probes' early forms and two test expectations of mine, all
retained. The 0.2879257239692379s research baseline stays separate. No live model
calls, no dependency installation. Unmeasured: reads, greps and the edit scripts.

### Still open

**Full four-Job/two-team/two-repository composition** in one executed run — the
largest remaining piece, untouched by this claim. **Terminal integration**: both
Jobs reach an admitted integration and no further sweep advances it, because this
fixture drives no integration runtime; recorded as its own gap with that exact
reason. The three retained product requirements — explicit fallback (now with a
composed observation), priority/creation ordering, composed continuation. The
jsonschema 4.19.2-versus-4.26.0 gap, in every artifact. The superseded
missing-team-membership API claim is **not** revived. No certification is claimed.
No mutating Git operation was performed.

## claim156029 — three claims of mine corrected, and Job A reaches terminal integration

Review 2026-09-13T00:09:15Z accepted R1 and R2 at their tested boundaries and
requested changes to what I had **claimed** about the new scenarios. Every
correction below is to a sentence of mine, not to a mechanism. Same two files.

### R4 — the reopen boundary is not quiescent, and I never measured it

My docstring, the exported scenario note and the last PROGRESS all said no
container was running at the reopen. **Job B's implementation is `waiting` there
and the engine holds one running container.** I asserted a property of the
boundary without asking the engine.

It is measured now, and the case is stronger for it: the boundary is a
**manager recomposition across live work**. At the boundary the test reads Job
B's runtime identity and the engine's running set; after the recompose it asserts
the reopened control store answers the **same runtime identity** and that **no new
`run` vector** was issued for it. The scenario note says the boundary is not
quiescent and that the shared engine object makes this a manager recomposition in
one process — not a host restart.

### R3 — I relabelled an open obligation to match what I had built

FINDING's test contract requires same-line correction affinity to the original
**healthy worker and session**; PLAN requires identity continuity for a
same-worker correction. I called a transport-loss/epoch-recovery case "session
continuity" and described it as the honest reading of that requirement. It is not
that requirement, and renaming an obligation to fit the evidence is exactly the
softening this record exists to prevent.

The transport-loss case is retained and relabelled — including that the provider
id and the `session-absent` evidence are **scripted inputs** to the real owner
API, so what was measured is what the owner does when told of an absence, not a
measured absence. The real obligation now has its own case,
`test_a_same_line_correction_keeps_its_worker_and_not_its_session`, and it is
measured in both halves: **the worker continues** — the corrected attempt is
prepared by the same producer under the same assignment participant — and **the
session cannot**, because an AgentSession is keyed by runtime attempt and a
correction is a new attempt, so the original session stays filed under the
original attempt and this serving path opens none for either. Recorded as a gap,
explicitly not discharged by the transport-loss case.

### Terminal integration — the helper was there and my reason for stopping was stale

I wrote that this fixture leaves the integration boundary to an injected port.
`integrating` uses the deployment's **own** port, and `integration_turn` drives a
real provider turn over the delivery the run published. **Job A now reaches a real
terminal completion in all three stages**, and the integrator it held **really
hands off**: the `admit` that was deferred becomes performed and the claim is
settled, with the integrator allocated to Job B.

**And my previous sentence "both Jobs reach an admitted integration" was wrong** —
only A was admitted; B was queued. Job B now reaches `claimed` and stops there.
Its attempted continuation is retained rather than described: `probe-156029.py`
drives `integration_turn` for B's attempt and the helper raises
`AttributeError: 'NoneType' object has no attribute 'place'`, because no launch
record exists for an attempt whose runtime this run never started — the
deployment-wide quiescence signal used to settle A is what stopped it. **No
stale-target refusal was observed and none is claimed.**

### A validator change the real handoff forced, and why it is not a weakening

Exporting the handoff produced `overlapping-occupancy`: one sweep completes A's
integration, the allocator returns the integrator and B reserves it, so the
release and the reserve are first seen at the **same tick** and this observer
cannot order two facts inside one tick.

The rule now treats a standing holder as freed when **its own release** is
observed at or before the reserving tick. It is not an act rank and it does not
weaken anything: two reservations with **no release between them** still overlap
at any tick, and `RELEASING_ACTS` is still `('release',)`, so a restart and a
completion still free nothing. Both the permitting case and its no-release
companion are asserted, beside the retained negatives.

### A process note I would rather record than have found

Two of my edit scripts this claim wrote nothing — one aborted on an anchor
assertion before its write, one ran from the wrong directory — and **the test runs
that followed them passed against code that was not there** (steps 114 and 119).
Nothing shipped from it, because the export showed the old gap name and the
mismatch surfaced. But a green run is not evidence that the edit landed, and the
two runs are retained and charged.

### Evidence

`trace-156029-composed.py` / `.json` — **thirteen composed artifacts, zero
violations each**, now including `composed-correction-continuity` and the
`composed-two-jobs-one-integrator` run carrying A's terminal completion and the
handoff. `trace-156029.py` / `.json` — the four unit-pool schedules re-exported.
`probe-156029.py` with its log — the retained attempted setup for Job B.
`run-153769-step-112..124.log`, `ledger-153769.json`. Step 122: **118 tests pass**.

### Candidate, 0664

- `tests/tools/scheduler_trace.py`
  `55d809d6229890148baa157217c2b432b6defa4b34264bada65f9641d02cd048`, 74359
- `tests/tools/test_scheduler_trace.py`
  `1f945e88a9fc98a168897ecc2102399d3916fa1163c9fd6bf01c349314129dde`, 193396

### Ledger

Author **226.570492/300s** across one hundred and twenty-four runs; **73.429508s
remains**. Non-zero this claim: step 120, the terminal-continuation case before the
occupancy rule was corrected. The 0.2879257239692379s research baseline stays
separate. No live model calls, no dependency installation.

### Still open

**Full four-Job/two-team/two-repository composition** in one executed run.
**Job B's own integration turn**, with whatever its common canonical target's
revision rule then answers. The healthy-correction session obligation, now
measured and still unresolved. The three retained product requirements. The
jsonschema 4.19.2-versus-4.26.0 gap. No certification is claimed. No mutating Git
operation was performed.

## claim156124 — four corrections, and BOTH Jobs reach a real imported integration

Review 2026-09-13T00:24:01Z. Every finding was right; two of them were assertions
of mine that could not fail, and one was a causal diagnosis of mine that was
simply wrong. Same two files plus dossier evidence.

### R4 — an assertion that could not see what it claimed to check

My duplicate-start check filtered new engine `run` vectors by Job B's **runtime
ID** — and the engine **mints** that id in its response; it is not an operand of
`run` at all. A duplicate launch would mint a different id, so the filter could
never match one. The assertion was decorative.

It counts by the launch's own **input identity** now — the attempt id, which is
in the launch labels — and the count is asserted nonempty so the comparison
cannot be vacuous. And the assertion is itself tested: a second container for Job
B's attempt is injected at the scripted engine and the same comparison that passed
now fails. **An assertion nothing can break is not an assertion.**

### R5 — the same-tick shortcut discarded identity and known order

Both reproduced false negatives were real. A release naming the right attempt but
a **foreign worker and principal** freed the standing holder; and a release whose
owner instant was **later** than the next reservation's was still treated as
preceding it, because only ticks were compared.

The pre-index is keyed by the holder it actually names and carries the owner's
instant. Where both sides carry instants, those decide; the coarse tick is used
only when they do not. Four cases: the two reproduced negatives, the
later-in-the-stream companion the review asked for (the earlier positive placed
the release first and never exercised the shortcut), and an
owner-timestamped-earlier positive. The no-release, alias, restart and completion
negatives are untouched.

### R6 — a completed import with no authorization in its own artifact

The contention artifact reported Job A's integration `complete` with empty
`authorization_references` and validated clean. Receipt coverage in another
artifact does not establish this completion's subject. The Authority is now asked
for the receipts on the proposal this stage actually imported, through the same
public reader, and `_completed_integration_is_authorized` **requires** them:
deleting the chain or moving it to another Job refuses, on the real artifact and
in synthetic cases. A trace that never completes an integration needs none.

### C1 — my diagnosis of Job B was wrong, and the right branch finishes the job

I blamed the deployment-wide quiescence flag and said Job B needed its own direct
integrator turn. The owner's actual answer: `Integration.run` returns `pending`
with a `derived_proposal_id`, awaiting a **verification receipt on that derived
proposal**. Job A moved their common canonical target, so `Integration._run` takes
the **`reconciled`** branch — publish a derived candidate, wait for independent
receipts — a branch that completes **without an integration runtime**. The flag
was never the gate and a direct import turn was the wrong branch. The gap text is
corrected and the diagnosis withdrawn.

**And the right branch was driven.**
`test_both_jobs_reach_a_real_imported_integration`: both Jobs coded and accepted
with the observer in the loop, Job A integrated for real, then the three
configured judges take real `judgment_turn`s over the frozen derived result. The
derived result moves `published` → `imported`, the Authority holds **four
receipts** on the derived proposal, and **both Jobs end `completed` in all three
stages** — the terminal composition this Work has carried as open since the first
slice.

### A validator rule the real import forced, stated narrowly

Job B's integration completed with **no start**, because the reconciled branch
runs no container. Requiring a `start` there would be requiring evidence of
something that did not happen. So a `complete` no longer owes its `start` **only**
when the stage is an `*/integration` and this trace carries a performed
`integrate` for that Job — which `_authorized_subjects` in turn refuses without
the same subject's verification, review and approval. Three cases hold the
narrowness: the authorized import passes, the same completion with the receipt
chain deleted owes both its start and its authorization, and an implementation
completion still owes its start.

### Evidence

`trace-156124-composed.py` / `.json` — **fourteen composed artifacts, zero
violations each**, now including `composed-both-jobs-imported` (49 records,
carrying verify/review/approve/integrate for both Jobs) and a contention artifact
that now carries Job A's terminal authorization. `trace-156124.py` / `.json` —
the unit-pool schedules re-exported. `probe-156124.py` with its log — the
judgment path asked before any test asserted it. `run-153769-step-125..136.log`,
`ledger-153769.json`. Step 134: **126 tests pass**.

### Candidate, 0664

- `tests/tools/scheduler_trace.py`
  `b992ab51c76201ccfb65e5a3a57327f03cd1a2ff32bce6e2ef6ff6df2660ae37`, 79456
- `tests/tools/test_scheduler_trace.py`
  `ea0db5f9af0bd87d823889d2eabb706d433e8051ec162979c0d49db85992c814`, 212704

### Ledger

Author **253.06017003798166/300s** across one hundred and thirty-six runs;
**46.93982996201834s** remains. Non-zero this claim: steps 125, 128, 130 and 132 —
one test expectation of mine, one instant-ordering collision between two owners'
clocks, and two probe forms. All retained. Research 0.2879257239692379s stays
separate. No live model calls, no dependency installation.

### Still open

**Full four-Job/two-team/two-repository composition** in one executed run — the
last large piece; both Jobs now reach terminal integration, but this is two Jobs
on one deployment, not four across two teams and two repositories. The
healthy-correction session obligation. The three retained product requirements.
The jsonschema 4.19.2-versus-4.26.0 gap. No certification is claimed. No mutating
Git operation was performed.

## claim156260 — a completed import is bound to the import that authorized IT

Review 2026-09-13T00:47:10Z accepted R4, R5 and C1 and kept R6 open in two parts.
Both were right, and both are the same mistake in different places: **I checked a
label where I should have checked a subject.** Same two files.

### R6a — a Job label is not a subject

`_completed_integration_is_authorized` recorded the import by `job_id` and checked
membership. Swapping the Job and stage labels of the two intact receipt chains —
leaving every proposal, candidate, target, receipt and owner reference untouched —
validated clean, with Job A's direct chain purporting to authorize Job B's derived
import and the other way round.

The binding is the owner's own now. `Integration.observe` answers, for a completed
stage, which proposal it imported, which derived result it carries (or none),
which integration receipt authorized it and which runtime it ran on (or none) —
the reader the review exercised, asked exactly as it asked it, with nothing
reached through it. A completed integration must name a proposal that a performed
`integrate` in this trace actually authorizes, under the receipt identity that
completion names, and `SUBJECT_AUTHORIZATION` then refuses that import without the
same subject's verification, review and approval.

**And a label contradicting the binding is itself a defect**: a chain recorded
under another Job's name while authorizing this one's import is a record
disagreeing with itself, so the swap refuses on the real artifact.

### R6b — the exception belonged to the branch, not to the stage name

My no-start exception asked only for an `*/integration` stage and any `integrate`
for the Job, so deleting Job A's `start` validated clean even though its
completion names a live runtime. The exception is driven by the owner's report
now: a completion earns it only when it names a derived **result**, reports
`execution_runtime: absent`, holds **no runtime**, and is bound to its
authorization. A direct import with a live runtime still owes its start, and an
unbound completion earns nothing.

Both retained real-artifact mutations are asserted on the exported
`composed-both-jobs-imported`: the swapped chains and the deleted direct start
each refuse, while the reconciled branch keeps its exemption — so the rule is a
branch distinction rather than a blanket. Six synthetic negatives cover the
direct-start, missing-binding, missing-member, foreign-proposal, foreign-receipt
and foreign-Job-label cases.

### And the two branches are now visible as the owners' own

The artifact records what the reviewer measured: Job A imported its own proposal
with a live runtime and quiescent execution and no derived result; Job B imported
a derived proposal distinct from its source, with a non-null result, no runtime
and `absent` execution.

### Evidence

`trace-156260-composed.py` / `.json` — **fourteen composed artifacts, zero
violations each**, every completed integration now carrying its owner binding.
`trace-156260.py` / `.json` — the unit-pool schedules re-exported.
`run-153769-step-137..141.log`, `ledger-153769.json`. Step 139: **132 tests pass**.

### Candidate, 0664

- `tests/tools/scheduler_trace.py`
  `32f0623f2518d0b8080925eba16e10558bcfcb6ae699b4cd83990aeb2f78409b`, 84308
- `tests/tools/test_scheduler_trace.py`
  `3c62bf0be71b25d860af5f053aadc79f4ed2279f7666542124c77f9ec39897ac`, 220327

### Ledger

Author **275.29741495998184/300s** across one hundred and forty-one runs;
**24.702585040018164s** remains. Non-zero this claim: step 137 — my contention
mutation still expected the Job-membership refusal the subject binding correctly
no longer gives. Retained. Research 0.2879257239692379s stays separate. No live
model calls, no dependency installation.

### The four-Job/two-team continuation was NOT started, and why

24.7s is about three focused-module runs (7.96s each) and no export. The
four-Job/two-team/two-repository composition needs a new deployment document, a
second Authority-facing team fact this pool has never bound, and at least one
full traversal to observe — none of which can be driven and verified in that
margin. Starting it would have produced a half-built scenario and no verification.

**The exact boundary for whoever continues:** the composed document this Work
drives is `TwoBoundJobsTraverseServingAndCorrection.traversing()`, two Jobs on two
`job_bindings` with two nominated sources and one canonical target; four Jobs
needs two more bindings and two more producer/reviewer pairs, and the *team* half
remains what the 17:15:58Z clarification pinned — scoped second-team
configuration is accepted and its composition into executed multi-team scheduling
is not. The unit-pool four-Job scenario exists and is exported; what is missing is
one executed composed run of it.

### Still open

Full four-Job/two-team/two-repository composition, with the boundary above. The
healthy-correction session obligation. The three retained product requirements.
The jsonschema 4.19.2-versus-4.26.0 gap. No certification is claimed. No mutating
Git operation was performed.

## claim156395 — the completion's BRANCH is validated now, not only carried

Review 2026-09-13T01:00:50Z accepted R6a and R6b and kept R6c open. It was right,
and it is the third time this Work has had to learn the same lesson in a new
place: **members that exist and are compared with nothing are not evidence.**

### What validated clean, and what now refuses

Four single-field mutations of the real `composed-both-jobs-imported` artifact:

- a direct completion naming **another attempt's runtime**, while the start of
  that very same attempt still named the real one;
- a **completed** direct import reporting `running` execution;
- a reconciled completion naming a **foreign result**;
- a reconciled completion naming **no source proposal** at all.

`_completion_branch` reads the two shapes an owner can actually return.
`Integration.account` emits a direct completed context with the owned runtime id,
`quiescent` execution, a null result and one proposal that is its own source;
`_reconciled_account` emits no runtime, `absent` execution, the derived result and
a derived proposal distinct from its source. Both name a source proposal. A
direct completion's runtime is compared with **its own attempt's recorded
start** — the comparison whose absence the first mutation exploited — and
anything outside those two shapes is `completion-contradicts-its-evidence`.

### The result is bound through an owner, not a string

The reviewer was explicit that a foreign result must not be caught by an invented
prefix rule. It is not. The artifact carries `result_references` — what
`reconciliation.result_of` answered for that result, read independently of the
completion that names it — and a reconciled completion's result must be one an
owner reported, whose derived proposal is the one being imported. An artifact
whose owner declared no result at all refuses too.

The reconciled no-runtime start exemption is unchanged in effect and stricter in
derivation: it is granted only when the branch really is the reconciled one AND
the completion is bound to its authorization.

### Evidence

`trace-156395-composed.py` / `.json` — **fourteen composed artifacts, zero
violations each**, every completed integration now carrying its branch-checked
binding and every reconciled one its owner-declared result.
`run-153769-step-142..144.log`, `ledger-153769.json`. Step 143: the validator
negative class and the three affected composed cases, **84 tests pass**. Per the
review, no second full-module run and no unchanged unit-pool re-export.

### Candidate, 0664

- `tests/tools/scheduler_trace.py`
  `cfbc9aa481c0332a4601f220328ee63692a2be9106e43d6624bca61c7f743c8d`, 91536
- `tests/tools/test_scheduler_trace.py`
  `b7d784e9c524d8b9ba75febfea118a40e33e6e1de258eac7b8f0a3bb83a68330`, 222713

### Ledger, and a costed request rather than another unchanged return

Author **289.60128760998174/300s** across one hundred and forty-four runs;
**10.398712390018261s** remains. This claim spent 14.30s against the review's
~12s target: steps 142 (3.39s, the synthetic reconciled positives needed their
owner result reference), 143 (3.75s) and 144 (7.16s, the export). Step 142 is the
one non-zero run and is retained. Research 0.2879257239692379s stays separate. No
live models, no installation, no Git mutation.

**The four-Job/two-team/two-repository composition does not fit in 10.4s, and
here is what it actually costs.** The review asked me to carry the exact setup and
measured cost to owner disposition rather than return unchanged work again, so:

- *Setup.* `TwoBoundJobsTraverseServingAndCorrection.traversing()` builds two Jobs
  on two `job_bindings`, two nominated sources and one canonical target. Four Jobs
  needs two more bindings, two more producer/reviewer pairs with their own
  participants and principals, and two more Works on the fixture Authority. That
  is new fixture code in my own test file — permitted — but it is new.
- *Measured basis.* The two-Job traversal with the observer in the loop measures
  1.04s (contention) and 1.68s (both-imported) per run. Four Jobs is roughly
  double the driven work: **2.5–3.5s per run**.
- *Iterations.* Every composed scenario in this Work took 2–4 runs to get right,
  and this one binds more owners than any of them. **Four to eight runs.**
- *Closing.* One affected focused pass (~3.8s) and one composed export (~7.5s).

**Estimated total 25–40 seconds.** I am not claiming an increase and I have not
started it: starting a scenario of that size with 10.4s would produce a half-built
fixture and no verification, which is what I said I would not do. The owner's call
is either an allowance for that range or an explicit deferral of the four-Job
composition from this Work.

### Still open

The four-Job/two-team/two-repository composition, with the costing above. The
healthy-correction session obligation. The three retained product requirements.
The jsonschema 4.19.2-versus-4.26.0 gap. No certification is claimed. No mutating
Git operation was performed.

## Claim 157211 — R6d closed, and the four-Job composition STARTED

Owner ruling 157085 (Slawomir, 2026-09-13T03:02:44Z) raised the implementation
verification allowance to **600 cumulative seconds**, left the reviewer at 300,
preserved prior spending, and directed that R6d be completed and the accepted
four-Job composition continued. The ledger's `author_cap_seconds` and
`cap_authority` now record that ruling beside its three predecessors; nothing was
reset.

### R6d — the rest of the owner result binding

The reference carried three members and `_completion_branch` compared one. Both
of the reviewer's retained mutations are real and both now refuse.

**A foreign source.** B's completion could name `proposal-of-another-job` as what
it imported FROM while its derived proposal, its result id and the owner's own
reference stayed untouched. Nonempty and different from the derived proposal was
the whole of the old rule, and that mutation satisfies both — a second, unchecked
account of which proposal was reconciled. The completion's source must now be the
source the owner says that result was actually derived from.

**A published snapshot offered as terminal proof.** The final reference is read
after the composed fixture reaches `completed`, and the fixture asserts
`imported` before exporting it — yet demoting that reference to `published` still
discharged the completion. `IMPORTED_STATE` is asked for explicitly. The note
records what a future artifact would owe if it wanted to retain historical
pre-completion references as well: an observation time, which is a different fact
and does not exist yet.

Five new cases: the two retained real-artifact mutations on the composed
both-jobs-imported export, two synthetic companions, and a narrowness case
asserting the terminal value is one value and that the unmutated reconciled
positive still validates clean.

### The four-Job composition — started, and the PLAN's own sentence measured

The PLAN asks for "four Jobs across two teams and two repository bindings, two
implementation and two review slots ... one dependency edge A→B, independent
C/D", and it also says: "a fixture that cannot bind this configuration reports
the gap rather than silently reducing it to one team."

**Both halves are measured, and they do not agree.** Setup is legal and public
throughout — the Authority's own `create_work` for two more Works, four Jobs from
one submission through the Job owner, and the scheduler's own allocations. No
receipt, claim, review or import is fabricated anywhere in this case.

- **The four Jobs, two teams and two repositories are real and parallel.** With a
  producer record per Job, `job-a`, `job-c` and `job-d` are allocated to three
  DISTINCT producers at one instant across two repositories, while `job-b` is
  held by the cross-Job edge `job-b/implementation → job-a/review` rather than by
  capacity — its own producer record is configured and idle throughout.
- **Two producer slots cannot serve four Jobs.** Same four Works, same
  submission, same edge, same three ticks, with C and D naming the EXISTING
  producers as their source: neither is ever allocated, and B's idle producer sits
  free the whole time. A configured worker carries one Work's input manifest and
  task, and a Work belongs to one Job's implementation stage, so the scheduler has
  no eligible worker for C or D.

The second is recorded as the gap `four-jobs-need-four-producer-records`, carried
in the exported artifact with the contrast as its observed evidence. It is not
reduced to "four Jobs need four producers": the PLAN asked for two slots, and what
the contract permits is one producer record per Job.

**The artifact is not vacuous, and that is asserted.** This Work has already been
caught once by an assertion that could not fail, so the export case asserts the
records themselves: `job-a/implementation` reserved, offered, accepted, claimed
and started; `job-c` and `job-d` reserved and offered in the same run; and
`job-b/implementation` absent from the performed acts entirely. Nine records,
four Jobs in the scenario graph with their real recorded edges, nine configured
workers, four bindings, **zero violations**.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 146 | `TheValidatorRefusesSyntheticInvalidTraces` | 84 pass |
| 147 | the composed both-jobs-imported case | 1 pass |
| 148–162 | four-Job probes, retained beside this record | — |
| 159, 160 | the three new four-Job cases | 3 pass |
| 163 | `TheComposedOwnersSupplyAuthorizedTransitions` | 35 pass |
| 164 | the whole module | **138 pass** |
| 165 | the composed export | 15 schedules, **zero violations each** |

**165 runs, 321.264251 seconds cumulative of 600**; 278.735749 remaining.
Research 0.287926s stays separate. No live model, no installation, no product
file, no existing test file and no Git mutation.

### Candidate

| Path under `v12/python` | Bytes | SHA256 |
| --- | ---: | --- |
| `tests/tools/scheduler_trace.py` | 93492 | `fa9e69f2df32b11cd2a830dc962900796e5aeb89398c50c5175d8e8e87ccf0d5` |
| `tests/tools/test_scheduler_trace.py` | 240956 | `1c62663bdf3e211de059a652870ffdb36edb5dedd3baa84caba871543ad4291a` |

Evidence: `trace-157211-composed.py`/`.json` (15 schedules, zero violations
each), `probe-157211-four-jobs.py`, `probe-157211-binding.py`,
`probe-157211-slots.py`, `probe-157211-artifact.py`,
`run-153769-step-145..165.log`, `ledger-153769.json`.

### Still open

The four-Job composition is **started, not finished**. What it does not yet do:
drive the four Jobs through their producer turns to real completions; exercise
the requested correction inside the four-Job schedule; run the three bounded
schedules (A before C, C before A, and reopening at a declared durable boundary);
and reach the separately configured integration capacity with four Jobs. The
healthy-correction session obligation, the three retained product requirements
and the jsonschema 4.19.2-versus-4.26.0 gap are all unchanged. **No certification
is claimed.**

## Claim 157344 — the four-Job scenario's two overstatements, corrected

Both findings were right, and both were claims in my own names and prose rather
than defects in a mechanism. `scheduler_trace.py` is unchanged this claim.

### [P1] The "two-team" artifact contained one team

Every configured participant and every resolved principal in the first four-Job
artifact was `baton.*`. A second repository is not a second team: a team is the
endpoint's own prefix, which `authority/identity.py` fixes.

Jobs C and D are served by `other.third`/`other.reviewer-3` and
`other.fourth`/`other.reviewer-4` now, authorized the way this suite's own team
matrix already established is the legal seam — a capability at the Work's own
scope through the Authority's public `grant_capability`.

**Only the reviewers take a grant, and that is the Authority's answer rather
than my choice.** Measured: the configured capabilities are `verify`, `review`,
`approve`, `integrate`, `close` and `manage-work-labels`, and there is no
`implement` among them. A producer is authorized by the route it may claim on;
a capability governs the judgments a participant may record.

The teams are asserted from the **Authority** — `principal_of` and
`holds_capability` — not from the document that asked for them, so the case
cannot pass on a configuration that merely spells a second team's name.

### [P1] C and D could not claim, and the name said they were coding

Four ordinary sweeps reported the exact public cause: route `baton.impl` does not
resolve to those participants. That was missing fixture setup, and
`add_route_handler` — which the two-Job fixture already demonstrates — is what
was missing. **Three Jobs now reach a CLAIMED offer at once**, on three distinct
producers from two teams, with the fourth held by its dependency edge rather than
by capacity; its own producer record is configured and idle throughout.

The case asserts the claims from the **offer owner** rather than from the
allocation, which is what the first form did not establish, and it is renamed to
what it proves. The old name said "on two repositories": under `traversing` the
Authority holds one canonical target revision, so every Job that publishes here
is a line of **one** target. The separate binding case is what proves independent
repositories. The first form's `job-d` binding named the second repository's base
and its line could not be materialized at all — measured, in
`probe-157344-lines.py`, and that is what exposed the claim.

### Integration stages

B, C and D ended at review, so the four Jobs could not contend for the integrator
at all. Every Job's submission carries an integration stage gated on its own
review now.

### The gap, scoped

The two-record versus four-record contrast stays, with its scope tied to the
configuration actually tested. It is an observed binding limitation consistent
with the source-worker eligibility gap this Work already retains. It does **not**
establish that every arrangement of four Job records over two effective slots is
impossible, and four independent principal slots are **not** offered as a
substitute for the PLAN's two-slot requirement, which stays open. The artifact's
own gap text says so.

The scenario note also states what the run has **not** reached: no producer turn,
correction, review, integration or bounded schedule has been driven in it yet.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 167–172 | the route, grant, line and claim probes, retained | — |
| 173, 174 | `TheComposedOwnersSupplyAuthorizedTransitions` | 36 pass |
| 175 | the whole module | **139 pass** |
| 176 | the composed export | 15 schedules, **zero violations each** |

**176 runs, 359.154942 seconds of 600**; 240.845058 remaining. Research
0.287926s stays separate. No live model, installation, product file, existing
test file or Git mutation.

### Candidate

| Path under `v12/python` | Bytes | SHA256 |
| --- | ---: | --- |
| `tests/tools/scheduler_trace.py` | 93492 | `fa9e69f2df32b11cd2a830dc962900796e5aeb89398c50c5175d8e8e87ccf0d5` (unchanged) |
| `tests/tools/test_scheduler_trace.py` | 250982 | `b23db0b9ef532490aaa598c06045e5d91f26519330aaa83d3bfdd3a59210cc8f` |

Evidence: `trace-157344-composed.py`/`.json` (15 schedules, zero violations
each), `probe-157344-lines.py`, `probe-157344-claims.py`,
`run-153769-step-166..176.log`, `ledger-153769.json`.

### Still open

The four-Job scenario reaches **claims and nothing past them**. Still owed in it:
real producer and reviewer turns, the requested correction, the three bounded
schedules (A before C, C before A, and reopening at a declared durable boundary),
the separately configured integration capacity now that the stages exist, and
no-duplicate and causal evidence observed throughout the executed schedule. The
healthy-correction session obligation, the three retained product requirements
and the jsonschema 4.19.2-versus-4.26.0 gap are unchanged. **No certification is
claimed.**

## Claim 157442 — the two bounded schedules, actually driven

The two fixture corrections were accepted. This claim takes the next item the
reviewer named: actual producer and reviewer turns. `scheduler_trace.py` is
unchanged again.

### Both orders, with real containers

`four_job_schedule` drives the scenario through REAL turns, and the two cases
differ only in which independent Job codes first:

- **A before C** — `job-a`, `job-c`, `job-d` in that order.
- **C before A** — `job-c`, `job-d`, `job-a`.

In each, three independent Jobs take a real producer turn on three producers
drawn from **two teams** and their implementations reach `completed`; each is
then really reviewed by its own reviewer, whose turn returns zero and whose
verdict is written. A schedule that only ever ran one order is not a
certification of parallel scheduling, which is why both are here.

**Every tick is observed.** The fixture's `produced` helper drives ticks to
completion itself, and ticks the trace never saw are exactly what made the oracle
report `job-a/review was reserved before job-a/implementation completed` — and it
was right: the completion first became visible in the same observed tick as its
successor's reservation. These schedules take the container turn and then observe
every tick that follows, which is what the reviewer asked for and what an
after-the-fact dump cannot give.

**No duplicate work**, stated as a fact of the schedule rather than left to the
rule that would refuse it: the completion census over each artifact is exactly one
`complete` per implementation stage.

### Where the schedule stops, measured

Every review turn returns zero and its verdict is written, and the stage then
stays `answering` — the projection's own ending for it exists and carries a
**null settlement**. So what is missing is the settlement of an ending that
exists, not a turn that failed, and the cross-Job edge
`job-b/implementation → job-a/review` does not open.

The accepted two-Job fixture settles the same review, so this is a property of
**this** composition — four Jobs, four Works, two teams, four integration stages
— and which part of it the settlement depends on is **not established here**. It
is recorded as the gap `a-four-job-review-answers-and-is-not-settled`, carried in
each schedule's own artifact with the projection's evidence, and the probe is
retained. It is not diagnosed from the outside and not reported as a completion.

### The stale docstring

`four_jobs` still described "four Jobs on two repositories". It now says what
`traversing` actually binds — one canonical target and four lines of it — and
states that the combined four-Job / two-repository / two-effective-slot contract
is **not** discharged by this scenario.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 177, 178, 181–183 | the producer, review and settlement probes, retained | — |
| 184, 187 | the two bounded schedules | 2 pass |
| 188, 190, 192 | the whole module | **141 pass** |
| 194 | the composed export | **17 schedules, zero violations each** |

**194 runs, 463.169824 seconds of 600**; 136.830176 remaining. Research
0.287926s stays separate. No live model, installation, product file, existing
test file, sleep or Git mutation; 100 ticks per trace unchanged.

### Candidate

| Path under `v12/python` | Bytes | SHA256 |
| --- | ---: | --- |
| `tests/tools/scheduler_trace.py` | 93492 | `fa9e69f2df32b11cd2a830dc962900796e5aeb89398c50c5175d8e8e87ccf0d5` (unchanged) |
| `tests/tools/test_scheduler_trace.py` | 262822 | `a1d95757d8da3f6c488f0a85a25aefccf5e56b7bbd287c13a9f816b478053f58` |

Evidence: `trace-157442-composed.py`/`.json` (17 schedules, zero violations
each), `probe-157442-turns.py`, `run-153769-step-177..194.log`,
`ledger-153769.json`.

### Still open

The **review settlement** boundary above, which is what everything below it waits
on: the requested correction inside the four-Job schedule, the third bounded
schedule (reopening at a declared durable boundary), and the separately
configured integration capacity all sit behind it. The combined
four-Job/two-repository/two-effective-slot contract remains open — the one-target
four-producer scenario and the separate repository case do not discharge it. The
healthy-correction session obligation, the three retained product requirements and
the jsonschema 4.19.2-versus-4.26.0 gap are unchanged. **No certification is
claimed.**

## Claim 157538 — the settlement gap was my own fixture, and the schedule runs on

The reviewer diagnosed the boundary I had recorded as an unexplained product
limitation, and the cause was mine. `scheduler_trace.py` is unchanged again.

### The stale policy pin

The borrowed composed case pins its policy generation in `setUp`, and
`composed_document` carries that pin into the deployment. `four_works` then
performs real Authority acts — two `create_work`s, four `add_route_handler`s and
two `grant_capability`s — and **every one of those moves the generation**. So the
composition was pinned to 11 while the Authority stood at 17, and four ordinary
sweeps reported exactly that: `conclude` deferred `policy/denied`.

**The reviews were never the problem; the conclusion was.** Every review turn
returned zero and every verdict was written — what could not happen was the
settlement, because the deployment was acting under a generation that no longer
existed. `current_policy` reads the Authority's generation after the setup acts
and before the composition, changing no live intent and no receipt.

I recorded that boundary as a gap with "which part of this composition it depends
on is not established here". That was honest about my uncertainty and wrong about
where to look: the evidence needed was the deferred `conclude`'s own cause, which
four more ordinary sweeps would have printed. The gap is **superseded**, not
softened; `trace-157442-composed.json` is retained as history, and the stale pin
is kept as a recorded cause in the schedule rather than deleted.

### Both schedules now complete, and the edge opens

A-before-C and C-before-A each drive three real producer turns and three real
reviewer turns, and **all six stages reach `completed`**. The cross-Job edge
`job-b/implementation → job-a/review` then opens — nothing else changes to let it
through, and B's own producer record was configured and idle throughout.

### The continuation: real work behind the edge, and one integrator

A third case follows the schedule with ordinary ticks only. Two things are true
at once and both are the owners':

- **The edge became real work.** `job-b/implementation` is not merely unblocked;
  it is claimed and running on `implementation-worker-b`, the record that sat idle
  behind the gate for the whole schedule.
- **One integrator serializes the rest.** Three Jobs are eligible to integrate and
  this deployment configures ONE integration worker, so exactly one is
  `integrating` and the others are `queued`. That is the separately configured
  integration capacity the PLAN names, contended by four Jobs.

### Two claims of mine, narrowed

**The completion census counts owner completions and nothing else.** Reading it as
no-duplicate *work* would claim something it cannot see, so `start_census` answers
runtime starts separately and both are asserted.

**What is simulated is named.** The worker entry, the workload, the Job and Worker
Manager owners, the Authority and the review cycles are the real ones; the
container engine is a scripted seam and the provider is a deterministic child
process, not a live model. Each schedule's scenario note says so.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 195, 196 | the two bounded schedules under the corrected pin | 2 pass |
| 198 | the continuation probe, retained | — |
| 200 | the integration-capacity case | 1 pass |
| 197, 201 | the whole module | **142 pass** |
| 202 | the composed export | **18 schedules, zero violations each** |

**202 runs, 511.595439 seconds of 600**; 88.404561 remaining. Research 0.287926s
stays separate. No live model, installation, product file, existing test file,
sleep or Git mutation; 100 ticks per trace unchanged.

### Candidate

| Path under `v12/python` | Bytes | SHA256 |
| --- | ---: | --- |
| `tests/tools/scheduler_trace.py` | 93492 | `fa9e69f2df32b11cd2a830dc962900796e5aeb89398c50c5175d8e8e87ccf0d5` (unchanged) |
| `tests/tools/test_scheduler_trace.py` | 269913 | `c375039e1fa773a2921d8a9a8066bc23584cd1a112d3d8628881428e0805be1a` |

Evidence: `trace-157538-composed.py`/`.json` (18 schedules, zero violations
each), `probe-157538-continuation.py`, `run-153769-step-195..202.log`,
`ledger-153769.json`. `trace-157442-composed.json` retained as superseded history.

### Still open

The **requested correction** inside the four-Job schedule, the **third bounded
schedule** (reopening at a declared durable boundary), and **terminal integration
evidence** — the continuation reaches `integrating` and `queued`, not an imported
result. The combined four-Job / two-repository / two-effective-slot contract
remains open. The healthy-correction session obligation, the three retained
product requirements and the jsonschema 4.19.2-versus-4.26.0 gap are unchanged.
**No certification is claimed.**

## Claim 157605 — I invented an act in a retained artifact

The policy-pin correction was accepted. The P1 against it is the worst kind of
finding this Work can receive, and it was right. `scheduler_trace.py` is
unchanged again.

### What I did

`stale_policy_negative` read the Authority's current generation and then emitted a
`submit`/`performed` **record** carrying `policy_generation:17` as its evidence
and no submission, Job or operation identity. Nobody performed that act. It went
into `four-jobs-a-before-c` at tick 9, and the oracle validated it — because an
oracle checks the consistency of what it is given and cannot know that a fixture
wrote a record itself.

That is fabricated evidence in a certification artifact, which is the single
thing this Work exists to make impossible. I wrote it while correcting a
different accuracy finding, which is worth recording: the temptation was to keep
the superseded explanation *inside* the artifact, and an explanation is not an
act.

### What it is now

**An assertion with no execution act behind it.** `policy_pin_is_current`
compares the composition's pin against the Authority and asserts they agree,
naming the consequence if they do not. It records nothing.

**The explanation lives where explanations belong** — each schedule's scenario
note carries the policy history and points at `trace-157442-composed.json`, which
stays retained as superseded history.

**And the bounded regression is the general form of the defect**, not this one
instance: every driven schedule asserts its artifact carries **no `submit` act
at all**. These schedules are emitted by `observed`, which reads owner evidence
tick by tick; `submit` is what a scenario-level fixture emits, so its presence in
a driven schedule means the fixture wrote a record itself. The retained export
carries none.

### Two more claims of mine, narrowed

**Capacity.** "Contended by four Jobs" was wrong: at that point **three** of the
four are eligible to integrate — `job-b` is still coding. The assertion always
named the three; the prose did not.

**The start census** counts the `start` records the observer exported, which is
what a schedule can see. It is not an independent count of engine invocations,
and it does not claim to be.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 203 | the three four-Job cases | 3 pass |
| 204 | `TheComposedOwnersSupplyAuthorizedTransitions` | 39 pass |
| 206 | the continuation case | 1 pass |
| 207 | the composed export | **18 schedules, zero violations, no invented act** |

No further unchanged full-module pass was taken, as directed. **207 runs,
557.555684 seconds of 600**; 42.444316 remaining. Research 0.287926s stays
separate. No live model, installation, product file, existing test file, sleep or
Git mutation.

### Candidate

| Path under `v12/python` | Bytes | SHA256 |
| --- | ---: | --- |
| `tests/tools/scheduler_trace.py` | 93492 | `fa9e69f2df32b11cd2a830dc962900796e5aeb89398c50c5175d8e8e87ccf0d5` (unchanged) |
| `tests/tools/test_scheduler_trace.py` | 272397 | `01002b80334791eeefd859211271a65afa95f3e4e2bc6222152fc29631800bd7` |

Evidence: `trace-157605-composed.py`/`.json` (18 schedules, zero violations,
no `submit` in any driven schedule), `run-153769-step-203..207.log`,
`ledger-153769.json`. `trace-157538-composed.json` carries the invented record
and is retained as the evidence of this defect.

### Still open

**42.4 seconds of allowance remain**, and the remaining scenario work is larger
than that: B's own producer and reviewer turns, the requested correction inside
the four-Job schedule, the third bounded schedule (reopening at a declared
durable boundary) with engine and provider no-duplicate checks at the reopen, and
terminal integration evidence. The combined four-Job / two-repository /
two-effective-slot contract remains open, as do the healthy-correction session
obligation, the three retained product requirements and the jsonschema
4.19.2-versus-4.26.0 gap. **No certification is claimed.**

## Claim 157712 — four more act labels for things nobody did

The tick-9 record correction was accepted, and the reviewer then audited the
**whole** export and found four more of the same defect that I had not looked
for. `scheduler_trace.py` is unchanged again.

### The four

- `composed-second-team-matrix` recorded `submit`/`performed` for what is
  `serving_two`/`operations_from` composing, plus a `holds_capability` and a
  `principal_of` read. That is a configuration succeeding, not a Job submission.
- Its two composition **refusals** — no grant, and a grant at the wrong scope —
  carried the same label.
- `composed-wrong-repository` recorded `submit`/`refused` for `line_for`
  reaching `create_line` and being refused.

I corrected one instance last claim and did not ask where else the same mistake
lived. The audit was the reviewer's; the defect was mine four more times.

### What they are now

**All four facts are preserved and none of them is a record.** Each is named
configuration evidence in its own scenario note: what was asked, which owner
answered, and the owner's own refusal sentence. The proofs are unchanged — the
cases still drive the real owners and still assert the real refusals — and the
artifacts no longer claim acts nobody performed.

`submitted()` is the one place that emits `submit`, and it emits it because it
has just called the public `submit`. It stays, and the retained export now
carries no `submit` whose operation is anything but a real submission.

### A claim of mine, narrowed

`observed_acts_only` checks act **names**, not provenance — the reviewer said so
plainly and my docstring overstated it. It now says what actually rules out a
fabricated record in those schedules: every record there is emitted by one call,
`observed`, and nothing else in `four_job_schedule` records anything.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 208 | the two affected cases | 2 pass |
| 209 | `TheComposedOwnersSupplyAuthorizedTransitions` | 39 pass |
| 210 | the composed export | **18 schedules, zero violations, no mislabeled `submit`** |

**210 runs, 584.424090 seconds of 600**; **15.575910 remaining**. Research
0.287926s stays separate. No live model, installation, product file, existing
test file, sleep or Git mutation.

### Candidate

| Path under `v12/python` | Bytes | SHA256 |
| --- | ---: | --- |
| `tests/tools/scheduler_trace.py` | 93492 | `fa9e69f2df32b11cd2a830dc962900796e5aeb89398c50c5175d8e8e87ccf0d5` (unchanged) |
| `tests/tools/test_scheduler_trace.py` | 273577 | `d0c853e0ef00e6275dbf8513184f28f093b1eac52997dc5acecd3ad9d5f938d3` |

Evidence: `trace-157712-composed.py`/`.json`, `run-153769-step-208..210.log`,
`ledger-153769.json`. `trace-157605-composed.json` retains the four mislabeled
records as the evidence of this defect.

### The budget boundary, stated plainly

**15.6 seconds of the 600-second allowance remain.** The owner request M157707 to
`baton.decide` — proposing 780 cumulative, per
`CONTINUATION-PROPOSAL-2026-09-13.md` — is **pending and is not authority**. I
have not relied on it and have not exceeded the cap.

What that budget cannot start: B's own producer and reviewer turns, the requested
correction inside the four-Job schedule, the third bounded schedule (reopening at
a declared durable boundary) with actual engine and provider duplicate checks at
the reopen, terminal integrations, and the combined four-Job /
two-repository / two-effective-slot contract. Each of those is a composed run of
several seconds with iterations, and beginning one on 15.6 seconds would produce
a half-built fixture and no verification — which is what I said I would not do
when this Work last reached a budget boundary.

The healthy-correction session obligation, the three retained product
requirements and the jsonschema 4.19.2-versus-4.26.0 gap are unchanged. **No
certification is claimed.**

## Claim 159444 — owner ruling M157707, and the feasibility it ordered first

Owner ruling, thread T103525 seq 159439 (Slawomir, 2026-09-13T09:34:52Z):
**approve** `CONTINUATION-PROPOSAL-2026-09-13.md` — cumulative author **780 s**,
reviewer 300 s, prior spending preserved, existing scope, fake providers and
acceptance requirements unchanged. Pass 159440: pin it and execute the bounded
continuation, **checking combined repository/slot feasibility first**.

**Pinned** in `FINDING.md` and `PLAN.md` with what it grants and what it does
not, attributed — those files are otherwise reviewer-owned. The ledger's cap and
`cap_authority` now carry this ruling beside its four predecessors; no spending
was reset.

### The feasibility the owner ordered first, and a correction it forced

**Four Jobs over two repositories bind and serve.** Asked directly, `job-c` and
`job-d` nominate the second repository, declare its base and bind to `target-b`,
and all three eligible Jobs are allocated on their own distinct producers across
the two repositories, with `job-b` held by the cross-Job edge. The two targets
are read back from the bindings the deployment holds, not from what the case
asked for.

**This corrects something I implied.** I wrote that the Authority holds one
canonical target revision "so every Job that publishes here is a line of it", and
let that stand as though it were a limit of the contract. It is `traversing`'s
own binding. The scenario note and the retained gap now say so, and the
separate case proves it rather than asserting it.

**Two repositories do not make two slots servable.** The same two repositories,
with C and D naming the existing producers, allocate neither. So the two halves
of the combined contract are **independent**: the repository half is feasible on
its own, and what blocks the combined contract is the retained source-binding
gap — a producer carries one Work's manifest and task, and a Work belongs to one
Job's stage — which is unchanged by which repository anything sits in.

The combined four-Job / two-repository / two-effective-slot contract therefore
**remains open**, and the gap text now names exactly which half is missing
instead of leaving both in doubt.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 211–213 | the feasibility probe, retained | — |
| 214 | the two new combined cases | 2 pass |
| 215 | `TheComposedOwnersSupplyAuthorizedTransitions` | 41 pass |
| 216 | the whole module | **144 pass** |
| 217 | the composed export | **18 schedules, zero violations** |

**217 runs, 627.705001 seconds of 780**; **152.294999 remaining**. Research
0.287926s stays separate. No live model, installation, product file, existing
test file, sleep or Git mutation; 100 ticks per trace unchanged.

### Candidate

| Path under `v12/python` | Bytes | SHA256 |
| --- | ---: | --- |
| `tests/tools/scheduler_trace.py` | 93492 | `fa9e69f2df32b11cd2a830dc962900796e5aeb89398c50c5175d8e8e87ccf0d5` (unchanged) |
| `tests/tools/test_scheduler_trace.py` | 278362 | `93db48ee22866163ca5d49d2b2db03d39a69968bce3ae7cf0e34d44edea299db` |

Evidence: `trace-159444-composed.py`/`.json`, `probe-159444-combined.py`,
`run-153769-step-211..217.log`, `ledger-153769.json`.

### Still open, with the proposal's own rows

The continuation's remaining planned work, none of it started this claim:
**B's own producer and reviewer turns and terminal integration in both four-Job
orders** (50 s planned); **the requested correction, the declared durable reopen
with actual engine and provider duplicate detection, and healthy-session evidence
or an exact owner refusal** (50 s); and the **changed-selector regression and
final candidate-bound export** (30 s). The combined contract's slot half is
answered above as open with its reason.

The three retained product requirements and the jsonschema 4.19.2-versus-4.26.0
gap are unchanged. **No certification is claimed.**

## Claim 159520 — the negative bound what it did not describe, and B ran

### [P2] The combined negative bound D to the wrong repository

`two_repository_bindings` set each worker's nominated source and each binding's
base and target and **left `source_worker_id` alone** — so the case described
`job-d` on the second repository while binding it to the first repository's
producer. The refusal it measured was real, but it was not the refusal the case
said it was.

The helper moves every operand that selects a repository now, and **both**
combined cases assert the mapping the deployment HOLDS — source worker, that
worker's nominated repository, the declared base, the bound target — **before**
any outcome is read. The gap stays bounded to the configuration tested, not a
universal impossibility.

### Job B takes its own turns, and all four Jobs are coded and reviewed

B's producer turn ran and its implementation stayed `answering`. The owner's own
cause, measured: *"has no completed frozen result to propose"*. B's configured
task names `feature_check.py` and asserts `feature.py`'s value, so a turn writing
the base fixture's harness produces nothing to freeze — the three other Jobs
share the base task and that is why only B was affected.

With its own output, **all four Jobs complete implementation and review**, and
the single configured integrator then has **all four contending**: one
`integrating`, three `queued`. The earlier assertion covered three, because B was
still coding at that point; the scenario note now states both moments instead of
only the first.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 218 | the two combined cases with the mapping asserted | 2 pass |
| 219–221 | the terminal probe, retained with its measured cause | — |
| 222 | the continuation case driving B | 1 pass |
| 223 | the whole module | **144 pass** |
| 224 | the composed export | **18 schedules, zero violations** |

**224 runs, 667.908388 seconds of 780**; **112.091612 remaining**. Research
0.287926s stays separate. No live model, installation, product file, existing
test file, sleep or Git mutation; 100 ticks per trace unchanged.

### Candidate

| Path under `v12/python` | Bytes | SHA256 |
| --- | ---: | --- |
| `tests/tools/scheduler_trace.py` | 93492 | `fa9e69f2df32b11cd2a830dc962900796e5aeb89398c50c5175d8e8e87ccf0d5` (unchanged) |
| `tests/tools/test_scheduler_trace.py` | 282858 | `0734e4f17737970444ad8a881ab40e0b63b225a075d58392fc4b41db64d7530b` |

Evidence: `trace-159520-composed.py`/`.json`, `probe-159520-terminal.py`,
`run-153769-step-218..224.log`, `ledger-153769.json`.

### Still open

**Terminal integrations.** The schedule reaches one Job `integrating` and three
`queued`; no Job's integration is driven to an imported result in the four-Job
scenario.

**The requested correction inside the four-Job schedule**, and **the declared
durable reopen with actual engine and provider duplicate counters**.

**Healthy-session continuity evidence, or an exact owner refusal** for it.

The three retained product requirements and the jsonschema 4.19.2-versus-4.26.0
gap are unchanged. **No certification is claimed.**

## Claim 159582 — a terminal integration, and two things the owners taught me

### The stale prose, corrected alongside the work

The continuation case said "NOTHING IS DRIVEN HERE ... these are ordinary sweeps
and what they report". That stopped being true when B's turns were added last
claim. It now says what it does: B codes and is reviewed, all four Jobs contend
for the one integrator, and the one it picked up is driven to a terminal
completion.

### A terminal integration in the four-Job scenario

A real integrator turn runs over the delivery this deployment published, the
manager then **observes** a stopped runtime rather than being told about one, and
`job-a`'s integration reaches **completed** — with the other three still waiting
on the single integrator.

**Two things are measured rather than assumed**, both in
`probe-159582-integration.py`:

- **`stopped` is deployment-wide.** Applying it while any producer container was
  still live reported those runtimes gone and made their stages `exceptional` —
  `job-b`'s implementation and `job-c`'s integration both. B's turns run first so
  the integrator's container is the only live one, and then nothing else is
  disturbed.
- **The terminal ticks are not observed into the trace.** Observing the
  completion produced `unauthorized-integration`, and the oracle is right: a
  completed integration must be bound to the import that authorized it, and this
  schedule does not record that receipt chain. The accepted two-Job artifact is
  where a completed integration carries its chain. Recording one here is named as
  remaining scope rather than exported without it.

**What is asserted about the states** is the serialization itself — exactly one
integration completed, the other three still queued, claimed or integrating —
rather than which Job the scheduler picks up next, which moves between ticks.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 225–227 | the integration probe, retained with both measured facts | — |
| 229, 231 | the continuation case | 1 pass |
| 232 | the whole module | **144 pass** |
| 233 | the composed export | **18 schedules, zero violations** |

**233 runs, 719.051973 seconds of 780**; **60.948027 remaining**. The module and
export pair cost about 29 s together and was taken once, at the end, as directed.
Research 0.287926s stays separate. No live model, installation, product file,
existing test file, sleep or Git mutation.

### Candidate

| Path under `v12/python` | Bytes | SHA256 |
| --- | ---: | --- |
| `tests/tools/scheduler_trace.py` | 93492 | `fa9e69f2df32b11cd2a830dc962900796e5aeb89398c50c5175d8e8e87ccf0d5` (unchanged) |
| `tests/tools/test_scheduler_trace.py` | 285770 | `9f5282d38e16bafa3a2c774047fb178e0200b1ae0bdd5d626b7275ba526a6c90` |

Evidence: `trace-159582-composed.py`/`.json`, `probe-159582-integration.py`,
`run-153769-step-225..233.log`, `ledger-153769.json`.

### Still open, against 60.9 seconds

**B's own turns in the C-before-A order**, and a terminal integration there — the
A-before-C order has both now; the alternate has neither.

**The authorization receipt chain for a four-Job completed integration**, without
which that completion cannot enter a validated artifact.

**The requested correction inside the four-Job schedule**, and the **declared
durable reopen with actual engine and provider duplicate counters**.

**Healthy-session continuity evidence, or an exact owner refusal.**

Each of those is a composed run of several seconds with iterations. The three
retained product requirements and the jsonschema gap are unchanged. **No
certification is claimed.**

## Claim 159644 — terminal integrations in both orders, and a budget overrun

### The receipts, and what I got wrong about them

Claim 159582 left the terminal ticks **out** of the trace because observing the
completion alone produced `unauthorized-integration`. That was correct about the
oracle and wrong about what to do: it is a reason to record the chain, not a
reason to stop observing.

The seam the reviewer proved is used exactly as given — this deployment's own
line, the integration checkpoint on it, the proposal that checkpoint published,
and the Authority's own receipts through the `proposal_receipts` the accepted
two-Job artifact already uses. Nothing invented, no source extended. The terminal
sweeps are observed now and the completion carries its authorizing chain:
`verify`, `review`, `approve` and `integrate` are in the exported acts, with zero
violations.

### Both orders

B's turns and the terminal integration are one helper called from A-before-C and
C-before-A alike; one terminal outcome in one order is not the accepted outcome
in both. The helper **waits for B's own container first**, because the edge opens
on A's review — which is *last* in the alternate order, where the first form
assumed the other order's timing and failed with "no configured worker prepared".

### A structural mistake I made and caught

Factoring the helper, I inserted `return` at the wrong place, so the continuation
case's scenario naming and validation became part of the shared helper — and both
callers then exported an artifact under **one name**, leaving the alternate
order's own artifact at its earlier 46-record state. The export is what showed
it. The tail is back in the case it belongs to; both schedules now export 66
records under their own distinct names, and the retained set has 18 uniquely
named artifacts.

### THE BUDGET IS EXCEEDED, and by how much

**240 runs, 780.804800 seconds against the approved cap of 780** — over by
**0.804800 s**, on the final export. I did not notice the margin closing before
starting a run I expected to fit. No further command has been run in this claim,
and none will be: the remaining work below is untouched.

This is an overrun of an owner-set cap, not a request. The disposition is the
owner's.

### Candidate

| Path under `v12/python` | Bytes | SHA256 |
| --- | ---: | --- |
| `tests/tools/scheduler_trace.py` | 93492 | `fa9e69f2df32b11cd2a830dc962900796e5aeb89398c50c5175d8e8e87ccf0d5` (unchanged) |
| `tests/tools/test_scheduler_trace.py` | 287741 | `31eac419d2beaff8ae084e95fe196ab6eee568fdee036a6ad3013054a44f218f` |

Evidence: `trace-159644-composed.py`/`.json` (18 uniquely named schedules, zero
violations), `run-153769-step-234..240.log`, `ledger-153769.json`.

Steps 234–240: the receipt fix, both-order continuation, the structural
correction and the export. The affected class passed 41 tests at step 237.

### Still open

Three terminal outcomes per order (only one Job reaches a completed integration
in each), the **requested correction** inside the four-Job schedule, the
**declared durable reopen with actual engine and provider duplicate counters**,
and **healthy-session continuity evidence or an exact owner refusal**. The
combined contract's slot half, the three retained product requirements and the
jsonschema gap are unchanged. **No certification is claimed.**

## Claim 159718 — the overrun recorded, the guard built, and a measured wall

### Owner ruling M159696, pinned

Thread T103525 seq 159714 (Slawomir, 2026-09-13T10:12:58Z): **record the
0.804800 s overrun with all actual spending preserved**, approve
`BUDGET-DISPOSITION-2026-09-13T10-09-12Z.md` — author 960 s cumulative, reviewer
300 s unchanged, **including its per-command budget guards** — with no spending
reset, scope expansion or acceptance waiver. Pinned in `FINDING.md` and
`PLAN.md`, attributed.

**The overrun is recorded as mine.** The final export began with 13.2837 s
remaining against a prior measured cost of 14.1442 s. I started a run I had
measured as not fitting. Nothing is rounded down, reset, or charged to the
reviewer, and no retroactive claim of compliance is made.

### The guard is built, not promised

Before **every** subprocess the runner now reads the cumulative ledger, computes
the actual remainder, refuses to start when the expected cost plus a margin
cannot fit, and bounds the child with a timeout below the remainder. A timeout
that fires is itself charged, with its own log, and the ledger is written before
the next command. Each run in this claim declared its expected cost.

### The remaining terminal integrations: a wall, measured

I wrote the loop that drives all four, and it does not work. The integrator takes
up **no** second Job:

- with `stopped` left set after the first completion, every container it starts
  afterwards is observed gone at once — step 243;
- **and cycling the flag back off for each integration does not change the
  answer** — step 244.

**Why is not established, and I am not guessing at it.** The next diagnostic is
the sweep's own deferral cause for the second integration stage, exactly as the
policy-pin and the frozen-result causes were found. Both failed attempts are
retained at their real cost.

So the case is back to the accepted single-terminal form, which passes: one Job's
integration completed with its own authorizing receipts, the other three still
waiting, and that completion recorded exactly once. The multi-terminal loop is
**not** in the candidate — a loop that cannot drive what it claims is not
evidence.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 241–244 | the multi-terminal attempts, retained as failures | — |
| 245 | both bounded orders | 2 pass |
| 246 | `TheComposedOwnersSupplyAuthorizedTransitions` | **41 pass** |

**246 runs, 819.345128 seconds of 960**; **140.654872 remaining**. No export was
taken this claim: the candidate is unchanged in behaviour from the accepted
one and a broad pair after a reverted attempt would spend the remainder for
nothing.

### Candidate

| Path under `v12/python` | Bytes | SHA256 |
| --- | ---: | --- |
| `tests/tools/scheduler_trace.py` | 93492 | `fa9e69f2df32b11cd2a830dc962900796e5aeb89398c50c5175d8e8e87ccf0d5` (unchanged) |
| `tests/tools/test_scheduler_trace.py` | 289807 | `6abbe33be2e41b042e39c2c0884705e7b700e466608b2e7bb522a9823889d4a4` |

`trace-159644-composed.json` remains the current retained export; its schedules
are unaffected by this claim's reverted attempt.

### Still open

**The second integration's deferral cause** — the next diagnostic, and what the
remaining three terminal imports per order wait on.

**The requested correction**, the **declared durable reopen with actual engine
and provider duplicate counters**, and **healthy-session continuity evidence or
an exact owner refusal**.

The combined contract's slot half, the three retained product requirements and
the jsonschema gap are unchanged. **No certification is claimed.**

## Claim 159787 — the gate was the reconciled branch

### The reviewer found what I could not

My loop waited for the next Job to become `integrating`. The reviewer's probes
show the sweeps **do** offer and claim it, and its composed launch then answers
**pending** because the Authority has no verification receipt on its **derived**
proposal. That is the **reconciled branch** — it starts no integration runtime at
all — so I was waiting for a transition that never comes, and my two "measured
walls" were measurements of the wrong thing.

**What that branch needs is its judges**, and the four-Job deployment now
configures `result_judgment_workers` before composition. One consequence had to
be found by running it: `job-c` and `job-d` were on `0000000a-W3` and `-W4`,
which are two of the fixture's three **judgment** Works — a collision that only
exists once judges are configured. They are on W7 and W8 now, and the setup
tolerates an already-created Work as the ordinary answer it is.

### How far the branch goes, and where recording it stops

`reconciled_next` drives it: the three configured judges take their real turns
over the derived candidate and the ticks that follow are measured.

**It records nothing into the trace, and that is measured too.** The Authority
stamps its receipts from a **real** clock while these Job and control stores are
frozen at the fixture's instant, so a frozen-instant act observed after a
real-clock receipt makes the oracle report `instants-disagree-with-order` —
correctly, at steps 254 and 258. Before that, at step 253, recording the
completion without its result reference and derived receipts gave
`missing-prerequisite`: a reconciled completion runs no container, so it earns
the no-start exception only when it names a derived result the artifact carries
and is bound to the receipts that authorized it.

Both are real requirements and both are right. What is not solved is **ordering
the two owners' receipts against each other** across two integrations in one
trace. Rather than export a half-bound artifact, the helper returns what the
ticks reached and this record says so.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 247–259 | the judge wiring, the Work collision and three ordering attempts | retained at cost |
| 261 | both bounded orders | 2 pass |
| 262 | `TheComposedOwnersSupplyAuthorizedTransitions` | **41 pass** |

**262 runs, 887.618977 seconds of 960**; **72.381023 remaining**. Every run
declared its expected cost and the guard refused none. No export this claim: the
retained artifacts are unchanged in content.

### The runner's own defect, fixed

The timeout branch wrote `spent_seconds` and left `author_spent_seconds` and
`author_remaining_seconds` stale. The next guard sums the retained runs and was
correct either way, but a summary nobody refreshes is a figure a reader would
believe. Both summaries are refreshed on both branches now.

### Candidate

| Path under `v12/python` | Bytes | SHA256 |
| --- | ---: | --- |
| `tests/tools/scheduler_trace.py` | 93492 | `fa9e69f2df32b11cd2a830dc962900796e5aeb89398c50c5175d8e8e87ccf0d5` (unchanged) |
| `tests/tools/test_scheduler_trace.py` | 293758 | `78bf7920ebe1d7d22b7ad13103199d88aebfc73a4accbfef8e317f24f90c145a` |

### Still open

**Ordering the two owners' receipts** so a second integration can be recorded and
exported — the next step, and now a precisely stated one.

The requested correction, the declared durable reopen with actual engine and
provider counters, healthy-session evidence or an exact refusal, the combined
contract's slot half, the three retained product requirements and the jsonschema
gap. **No certification is claimed.**

## Claim 159863 — a claim of mine superseded, and the payload conflict fixed

### The ordering was not unsolvable. I was appending in the wrong order.

I recorded that ordering the two owners' receipts across two integrations "is not
solved here", and framed it as a property of the two clocks. The reviewer's probe
solves it: observe both imports, record the reconciled result's own
`RESULT_CONTEXT`, then read the **earlier** integration's receipts **before** the
later one's at the final tick — 76 records, validating, with timestamps and the
oracle unchanged.

My step-258 failure was appending the **older** A receipts **after** the newer B
receipts. That is a mistake in my sequence, not a limit of the design, and the
helper's docstring says so now instead of the superseded claim.

### The alternate gate: my own scenario payloads conflicted

After C imported, A came back **held** — `harness.py` would not reconcile
cleanly. `four_job_schedule` gave A, C and D **different content at the same
path**, so their imports genuinely conflict and reconciliation was right to
refuse.

The payloads are compatible now: **identical harness bytes** for every Job and
**one distinct file each**. The required test still really runs, reconciliation
is not weakened, and the explicit correction scenario is untouched. Both bounded
orders pass with it.

### What is honestly outstanding in this file

`reconciled_next` **has no caller**. The recording sequence belongs in the
schedule that drives both imports, and wiring it there is the next step — not
something to leave half-done inside a helper.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 263 | the A-before-C schedule with compatible payloads | 1 pass |
| 264 | both bounded orders | 2 pass |
| 265 | `TheComposedOwnersSupplyAuthorizedTransitions` | **41 pass** |

**265 runs, 910.739081 seconds of 960**; **49.260919 remaining**. Every run
declared its expected cost; the guard refused none. No export this claim — at
14.1 s for an export against 49.3 s remaining, that spend belongs to the claim
that has the second integration recorded, not to this one.

### Candidate

| Path under `v12/python` | Bytes | SHA256 |
| --- | ---: | --- |
| `tests/tools/scheduler_trace.py` | 93492 | `fa9e69f2df32b11cd2a830dc962900796e5aeb89398c50c5175d8e8e87ccf0d5` (unchanged) |
| `tests/tools/test_scheduler_trace.py` | 294599 | `81432f97431c128169cf4f02371cd6f716f4e251ebe3bc0179ecf05749144062` |

### Still open, against 49.3 seconds

**Wire the proved recording sequence** so both integrations are in the artifact,
then export. That is the next claim's first move and it fits.

The requested correction, the declared durable reopen with actual engine and
provider counters, healthy-session evidence or an exact refusal, the combined
contract's slot half, the three retained product requirements and the jsonschema
gap. **No certification is claimed.**


## Claim 159945 — a real regression per Job, and the continuation finally has a caller

### The compatible harness was not the fix, and the reviewer's own correction is why

I made A, C and D write **identical** `harness.py` bytes, on the reviewer's
earlier recommendation, and the alternate continuation still refused. Review
2026-09-13T10-44-30Z supersedes that recommendation with the measured cause:
the original base **already holds** `harness.py`, so `_ConfiguredExecution._run`
never adds its pinned one there and the base runs the **old** file. One pinned
harness over three content states gives three digests, and
`reconciliation._causal` refuses exactly that. It also requires the base to have
had the harness **added** and its status to be **nonzero** — which a print-only
harness cannot give however its bytes are spelled.

Compatibility removed a merge conflict. It never established a regression.

### What each ordinary Job has now

What B has had all along. A required test at a path the original base does not
contain, asserting that Job's own payload:

- `check_job_a.py` imports `feature_job_a.py`, which the producer's own turn
  writes, and asserts its value;
- the task document naming `["python3", "check_job_a.py"]` as its verification;
- the **producer's and the reviewer's** deployment manifests over those task
  bytes, and the submitted Job's `input_digest` over the same manifest —
  including Job A's, whose submission is copied from the accepted fixture and
  described the base harness task.

`regression_task` derives the bytes from the Job identity alone, so the document
on disk, both manifests and the submitted digest cannot come apart;
`single_worker._held` cross-checks the first two or nothing composes.

The shared harness is untouched, and these Jobs no longer write one shared path
at all.

### The observer's actual answer, for job-a in the alternate order

Read through the reviewer's own `repro-159894-causal.py` against current bytes
(step 267), which is the same script that recorded the refusal:

| | command | added | status | digest | output |
| --- | --- | --- | ---: | --- | --- |
| base | `check_job_a.py` | **true** | **1** | `sha256:6f7cb467…` | `ModuleNotFoundError: No module named 'feature_job_a'` |
| isolated | `check_job_a.py` | false | 0 | `sha256:6f7cb467…` | `job-a regression passed` |
| combined | `check_job_a.py` | false | 0 | `sha256:6f7cb467…` | `job-a regression passed` |

One digest across all three, base added and failing, the other two clean, and
`test_identity: w103525-job_a-regression` throughout.

### `reconciled_next` has a caller

I disclosed that the helper existed and was called by nothing. It is called from
`b_and_terminal` now, so **both** bounded schedules carry **both** imports:

- every tick of the reconciled branch is **observed**, not swept past — the
  earlier form drove it with bare ticks and returned a summary, and a transition
  nobody observed cannot be in the artifact;
- the branch's own owner facts are asserted: published before judgment, **no
  receipt** on the derived candidate until the judges answer, three accepted
  verdicts, `imported` afterwards, four receipts on the derived proposal;
- the result's own `RESULT_CONTEXT` is read through its public reader;
- the receipts are read last and in owner order — the **earlier** import's chain
  before the later one's. The direct import is authorized on the proposal its
  checkpoint published; the reconciled one on the **derived** candidate, which is
  a different chain read through its own subject.

Each of the two completes exactly once, by census, and the oracle validates both
artifacts with no violations.

### Three fixture errors, each measured rather than guessed

**A judgment result needs a tick.** Reading the verdicts straight after the
judgment turns refused "a judgment needs a completed frozen result in accepted
custody" (step 268). The accepted two-Job case ticks there for the same reason.

**A bound that fitted only the order I ran first.** Fourteen observed ticks carry
A-before-C to its judges and leave C-before-A with none (step 271), because in
that order the reconciled Job is offered, claimed and launched later. Raised to
thirty.

**The judges were configured for one Job.** `result_judgment_workers` is keyed
**by Job**, and the fixture helper defaults to `job-b`. The A-before-C order's
second import is job-b's and found its three judges; C-before-A's is job-a's and
found **none** (step 272). Every Job has its own judgment workers now — their
worker ids are per-Job, the three judgment Works are created once.

And `offered` is now among the states a Job behind the integrator may be in: it
is the third Job's actual state after two imports (step 269). The integrator's
capacity came free and the offer owner issued it; what has not happened is the
claim. None of that set is completed, which is what the assertion is for.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 266 | the A-before-C schedule, new fixture | 1 pass |
| 267 | reviewer's `repro-159894-causal.py`, current bytes | the table above |
| 268 | A-order continuation | refused: judgment custody |
| 269 | A-order continuation | failed: `offered` |
| 270 | A-order continuation | 1 pass |
| 271 | alternate continuation | failed: no judges in 14 ticks |
| 272 | alternate continuation | failed: no judges in 30 ticks |
| 273 | alternate continuation, judges per Job | **1 pass** |
| 274 | **all eight other four-Job tests**, including the A-order continuation | **8 pass** |

**274 runs, 946.242489 / 960 s, 13.757511 s remaining.** Every run declared its
expected cost and the guard refused none.

### Changed paths this claim

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `tests/tools/scheduler_trace.py` | 93492 | `fa9e69f2df32b11cd2a830dc962900796e5aeb89398c50c5175d8e8e87ccf0d5` (unchanged) |
| `tests/tools/test_scheduler_trace.py` | 306444 | `774ac94d804fdd07561ace33468c0e1ddeb533a27fd86cc84670aff8158069a9` |

No product file changed. No Git mutation, installation, live provider or sleep.

### What 13.76 seconds cannot buy, stated exactly

**No export this claim.** The last export cost 14.1 s; the remainder is 13.76 s
and the per-command guard refuses a command whose expected cost plus margin
exceeds it. The artifacts now carry two imports per order and are worth
exporting; that spend belongs to the claim that has the allowance.

**Two terminal outcomes per order, not four.** The remaining two per order are
two further reconciled continuations each — the loop is small, the runs are not,
and attempting it here would spend the remainder with nothing verified.

**Also still open**, unchanged and not re-argued here: the requested correction,
the declared durable reopen with actual engine and provider duplicate counters,
healthy-session continuity evidence or an exact owner refusal, the combined
two-repository / two-effective-slot contract's slot half, the three retained
product requirements, and the jsonschema 4.19.2-vs-4.26.0 gap.

**No certification is claimed.**


## Claim 160959 — four terminal outcomes in both orders, exported

Owner ruling M160956 is pinned in FINDING and PLAN: author **1200s** cumulative,
reviewer 300s unchanged, persisted per-command budget operands, focused
verification, same scope, no acceptance waiver. It is not a fresh allowance —
946.2424892749755s was already spent.

### The operands are in the ledger now

Every run this claim carries a `budget` object beside its cost: the cap, the
spent and remaining figures the guard started from, the expected cost it was
given, the margin and the timeout the child was actually bounded with. A guard
whose inputs nobody can read afterwards is one a reader has to take my word for.

### All four terminal outcomes, in each order

`reconciled_next` selected its judges with `next(iter(deployment.judges))` —
and that map is keyed `(result_id, kind)` and **accumulates**, so a second
continuation would have handed the previous result's executions to the next Job.
It now waits for a result id nobody has judged yet, takes that result's own three
executions, and the schedule loops until every Job has a terminal outcome.

**And the judges needed their own Works.** The borrowed fixture makes ONE Work
per KIND, because it was built for one Job. Those Works are claimed on route
`baton.impl`, and a completed judgment leaves the assignment on `rview` — so the
second Job's verification judge could not claim at all. The Authority said so
exactly:

> route 'rview' does not resolve to 'baton.verifier'

Steps 275–278 measured it; the cause only became visible when I captured what
`judge_result` itself raised, because the launch answer swallows the refusal into
`pending` and the sweep report shows only the next Job's capacity deferral. There
is now one judgment Work per **(Job, kind)**, created through the Authority's own
`create_work`, with each judge's manifest rewritten over the same configured task
bytes; the policy generation is re-read after those acts.

**Result, in both bounded orders:** four `integrate` receipts, four integration
completions — `job-a`, `job-b`, `job-c`, `job-d` — 97 records each, zero
violations.

### An unnamed duplicate in the exported set, found by exporting

The A-before-C case named its scenario *after* `b_and_terminal`, and that helper
builds an artifact itself (the completion census). So step 282's export carried a
**97-record duplicate of that schedule under the blank default name `pending`** —
exactly what the comment above the naming block said must not happen. The naming
moved above the terminal half, and the re-export carries **18 uniquely named
schedules and no duplicate**.

### The requested correction was already discharged, and here is the evidence

The 04:38:33Z P1 asked that four configuration facts stop being recorded as
`submit`/`performed` acts. They are not: in the exported set
`composed-second-team-matrix`, `composed-two-repository-bindings` and
`composed-wrong-repository` carry **zero records**, and the facts live in their
scenario notes — `team_grammar`, `configured_team`, `refused_without_grant`,
`refused_at_another_scope`, `attempted`, `refused` — with the retained gap
`authority-teams-and-wrong-repository-refusal`. The only `submit` record this
module emits is the scheduler-level fixture's, which really calls public `submit`.

### The provider counter, and why it is a note rather than an assertion

The reopen case already counts **engine** launches by the attempt id in the
launch's own operands, before and after the boundary. I added the provider half
and it was empty: `agent_sessions_of` answers `[]` for Job B's attempt and then
for Job A's (steps 285, 286), because neither has reached the turn that records a
session at that boundary. An assertion over an empty list cannot fail, so it is
not made. What the schedule records instead is the measured limitation, in its own
note, naming `composed-role-sessions` as the schedule that does carry real
session identities.

### Verification, measured

| Step | Selector | Result |
| ---: | --- | --- |
| 275 | four terminal outcomes, A order | failed — one judge, not three |
| 276–278 | the same, with the owner's own refusal captured | the `rview` sentence above |
| 279 | A order with per-(Job, kind) judgment Works | 1 pass |
| 280 | C-before-A | 1 pass |
| 281 | the seven other four-Job tests | 7 pass |
| 282 | export | 19 artifacts — the `pending` duplicate |
| 283 | both schedules after the naming move | 2 pass |
| 284 | export | 18 unique, zero violations |
| 285, 286 | the provider counter | empty both times |
| 287 | the reopen with the limit recorded | 1 pass |
| 288 | export from the wrong directory | refused, 0.005957s, charged |
| 289 | **final export** | **18 schedules, zero violations** |

**289 runs, 1063.507797 / 1200 s, 136.492203 s remaining.** Every run declared its
expected cost and persisted its operands; the guard refused none.

### Candidate and artifact

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `tests/tools/scheduler_trace.py` | 93492 | `fa9e69f2df32b11cd2a830dc962900796e5aeb89398c50c5175d8e8e87ccf0d5` (unchanged) |
| `tests/tools/test_scheduler_trace.py` | 313954 | `a57c0a71e52629ee6008f054dccb1ef2d563bb886453b6bd8317daefe2437e17` |
| `trace-160959-composed.json` | — | `5a3ead46c46b5586cbd3a74d7454b402fd04dfbe34414e33a061ac9e90fb9303` |
| `trace-160959-composed.py` | — | `cfe80425e122ab1199be9378c7f3a6f853819549af6039bada8c3fb9e2f4114e` |

No product file changed. No Git mutation, installation, live provider or sleep.

### Still open, not waived

**Healthy worker/session evidence** beyond the measured limitation above — the
reopen path records no session, so the evidence would have to come from a
schedule that does.

The combined two-repository / two-effective-slot contract's slot half, the three
retained product requirements, and the jsonschema 4.19.2-vs-4.26.0 gap in every
artifact. **No certification is claimed.**
