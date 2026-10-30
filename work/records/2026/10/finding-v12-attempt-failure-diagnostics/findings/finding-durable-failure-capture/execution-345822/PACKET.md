# W341357 — MEASURE FIRST, then correct the fixture storage

`baton.claude`, claim345822, role `impl`. **Preparation only.** No Job
submitted, no attempt, no runtime, no engine, no provider, no credential read,
no version-control mutation, no host product or test edit, **and no product
test executed.** **The start is not selected.**

| | |
| --- | --- |
| base | `bc925cf5c62d69426ed5862af4d41f4d2a967b0f` |
| proposed run | `durable-capture-w341357-345822` |
| proposed root | `/home/sl/baton-instances/durable-capture-w341357-345822` — **absent**, created by step 1 |
| continues from | `../execution-345388` — selected by owner345560, **ran once and completed on its own at 789.14s**. Preserved, seal still verifying |
| input | **the second retained candidate**: head `5a7d5976ab48…`, content `sha256:5c0fca78…`, patch `5030be08…`. **RETAINED AND UNACCEPTED** |
| start | `start_authorized: false`, `start_selected: false` |
| exact commands | `COMMANDS.md` (six, no placeholders; step 5a–5e is the operator's post-run collection) |
| vehicle pins | **unchanged for the ninth packet running** — controller `d12769df…`, baseline `8e5987f5…`, helper `af9e5ea6…`, 114 manager files |

## What happened, and what this packet is for

Owner345560 selected `../execution-345388`. It ran once and **completed on its
own at 789.14 seconds** — `provider.status 0`, token returned and not expired,
110.86s of lease margin. **Not a lease truncation.** It did **overrun the
720-second planning target by 69s**, which is recorded rather than rounded away.

**The gate has now been measured twice:**

| run | result |
| --- | --- |
| `345039` | `864 tests in 12.817s` — `failures=9, errors=7`, all in `test_maintenance`, path-shaped |
| `345388` | `864 tests in 12.515s` — **`errors=16`, zero failures**, one cause |

**The 30-second ceiling fits, twice over** — that question is closed. Every
path-comparison assertion and line-layout refusal that failed in `345039` now
passes. What remains is **16 failing SUBTEST outcomes in FOUR methods**, every
chain ending in `sqlite3.OperationalError: database or disk is full`.

**And nothing about why has been observed.** Not the filesystem that filled, not
its available bytes or inodes, not the peak usage, not the per-subcase lifetime,
not the same-environment base/candidate counts. `review-2026-10-21T11-37-58Z.md`
verified the evidence, **withheld acceptance**, and required one **minimal**
continuation that **measures before it fixes** — reusing unchanged machinery.
That is what this packet prepares.

### Three claims of mine the review corrected, and all three are accepted

I checked each against the base rather than taking it on the handoff.

1. **`disk_roots.py` was not new.** It exists at the base with sha256
   `53dc1fa9b99697c8b6ea0597579ba05135a6a7707f798d15d9a8da2b5dd85c08`, 121
   lines. The candidate only canonicalises its temporary directory. I read the
   path in `changed_paths` and never checked whether the section was a creation.
2. **The 16 errors are SUBTEST outcomes in FOUR methods** — not 16 independent
   methods, and not 864 concurrent durable stores. That makes this a small
   fixture-lifetime problem, not a suite-too-big-for-the-filesystem problem.
3. **An equal test count proves nothing about assertion coverage.** A test that
   fails during setup never proved its later assertions. So `failures 9 → 0` is
   progress, not proof every earlier affected assertion reached and passed.

The original evidence in `../evidence/run-345388/GATE-CLASSIFICATION.json` stays
untouched; `FIXTURE.md` and `PROVENANCE.json` carry the corrections.

## Where the pressure is — the static lead, revalidated in the tree

`FIXTURE.md` is the full account. In short, three places, each read at the base:

1. **`tests/manager/test_intake.py:2531-2535`** — `self.setUp()` runs **inside**
   a `subTest` loop, so each of six iterations registers another `addCleanup`
   that only fires when the **outer** test ends. Every iteration's store stays
   live until then. `test_a_receipt_about_something_else_is_refused_by_both_exits`
   has the same shape.
2. **`tests/manager/test_maintenance.py:2763`, `:2786`, `:2915`** — the same
   shape with `self.addCleanup(case.doCleanups)`, deferring each sub-case's
   cleanup to the outer test.
3. **`tests/manager/test_output.py:101-104`** — `OutputCase.setUp` creates
   `control.sqlite3` under `tempfile.TemporaryDirectory`, **not**
   `disk_backed_root`. **So `BATON_V12_DISK_ROOT` does not relocate it**; it
   selects workspace fixture roots only.

**This is a static lead, not measured proof of which filesystem filled.**
`TASK.md` step 2 asks for the observation first — roots, mounts, available bytes
*and inodes* before/during/after, per-subcase lifetime, high-water mark, and the
same-environment base/candidate counts — and says plainly that if the
measurement contradicts the lead, follow the measurement.

The composed `tmp_bytes 67108864` / `shm_bytes 16777216` /
`workspace_min_bytes 83886081` are **configured capacities, not observed free
space.** The previous classification treated them as evidence for the
exhaustion and that was wrong.

## What changed from `../execution-345388` — minimally, as required

| changed | why |
| --- | --- |
| **the input** | `recovery-345039` (the first retained candidate) is replaced **as input** by `recovery-345388`, the second. The old set stays in place as history; its pins are dropped, not edited |
| **`TASK.md`** | **measurement-first**: reproduce the four methods, measure roots/mounts/bytes/inodes/lifetime and the base-versus-candidate counts, **then** correct, **then** the complete gate with no skips — and write `W341357-VERIFICATION.json` into the candidate tree |
| **`FIXTURE.md`** | the two measurements, the three corrections, the citations for the four-method lead, and the two things not selected |
| **`RECOVERY.md`** | rewritten for the second retained candidate and explicit that it is retained and **unaccepted** |
| `PROVENANCE.json`, `COMMANDS.md`, `OPERATOR.md`, this document | the identity, the task and the record |
| `GATE-CHECK.json`, `LIMITS-CHECK.json`, `PREFLIGHT.json` | re-derived from **this** claim's composed documents |
| `decisions/` | two re-taken, five added; 36 → 41. Task inputs 45 → 50 |
| `PACKET-INPUTS.json`, `SHA256SUMS` | the resultant seal |

**Not changed at all, which is the point of "minimal":** `prepare.py`,
`verify-inputs.py`, `probe.py`, `collect.py`, every limit, and the sealed gate
argv. The recovery cross-checks already bind a retained candidate at
`baton.w341357-recovery/3`, so swapping the first retained candidate for the
second needed **no program edit and no new probe**.

**Unchanged and proved rather than asserted:** the verification member digest
re-derived from this claim's composed `task.json` is
`2f7ed3dca95da498657a0e549e53107679fd7e8cf4503d5022555ba9e642176c`, **identical**
to the one every accepted packet since claim339421 carried. `COMPLETION.md`
travels verbatim at `c8c5d4dd…`. 900s lease, 3600s provider, 30s verification,
4800s total, 60s cleanup, one invocation, no retry, `report-and-hold`, and the
600/720/180 planning cutoffs. `ENFORCEMENT.md`, `SHUTDOWN.md`, `FAILURE.md`,
`collect.py` and `probe.py` byte-identical.

## The report, because the last turn's numbers were lost

`TASK.md` step 5 names **`W341357-VERIFICATION.json`**, written into the
candidate tree so it travels as a changed path in the existing `change.patch`.
No new output protocol and no transcript-only proof. The previous task asked for
the base/candidate counts and gave the turn no channel but the provider
transcript, which the proposal does not carry — **my defect**, and this is the
fix the review prescribed.

## The candidate transport, and why it is not a task input

The patch is the whole delivery. `candidate-objects.bundle`
(`c6d1706d…`) is recorded by digest and locator for provenance and is
**deliberately not pinned as a task input**: this campaign creates no
version-control object on this host and restores nothing into the private
checkout, `PROVENANCE.checkpoint.paths` stays empty, and `prepare.py` still
refuses a declared restored buffer — so that refusal keeps its meaning. Both
programs **refuse** if the bundle ever appears among the task inputs, and probe
`candidate-transport-pinned-as-a-task-input` demonstrates the refusal.

## Read in this order

1. **`COMMANDS.md`** — the six exact commands, including the post-run collection
   that is **yours and not the worker's**.
2. **`FIXTURE.md`** — what the gate measured and exactly where it fails.
3. **`RECOVERY.md`** — the retained candidate, and what it is not.
4. **`OPERATOR.md`** — what each step does and what to expect.
5. **`SHUTDOWN.md`** — what the vehicle publishes when it ends, and the rules: a
   missing final report is incomplete rather than success, and an unavailable
   report names no cause.
6. **`ENFORCEMENT.md`** — the vehicle, the composer's wrong start command, the
   900-second lease.
7. **`FAILURE.md`** — the first selected execution of this Work and why it failed
   at startup.
8. **`COMPLETION.md`** — the supported completion mechanism and the 600/720/180
   cutoffs.
9. **`TASK.md`** — what the authoring turn is asked to do, in a fixed order.

`collect.py` and `probe.py` are the executable documents: the first is the
operator's read-only post-run collection, the second re-runs all **sixty-one**
refusal and collection cases in about 2.5 seconds.

Evidence: `PREPARATION-PINS.json`, `PROVENANCE.json`, `PREFLIGHT.json`,
`GATE-CHECK.json`, `LIMITS-CHECK.json`, `decisions/` (**41** immutable snapshots
indexed by `decisions/INDEX.json`), `SHA256SUMS` and `PACKET-INPUTS.json`.

## Preparation evidence, measured this claim

**No product test was executed to produce any of it. No instance was touched.**

- **Input check** 0.12s, exit 0 — 114 manager files, 3 supervisor, 2 preparation
  inputs, **50** task inputs, **41** decision snapshots, 4 checkout documents, 1
  pinned controller, 1 pinned shutdown helper, **2** pinned recovery inputs, 1
  gate module still owed, and **no decision-source drift** after re-taking
  `FINDING.md` and `PLAN.md`.
- **Preparation exercised once** into `/tmp/w341357-preflight5`: stage 0.11s,
  bootstrap 0.61s, bind 0.37s — **≈1.09s, all status 0**, authority
  `2ae413ff9d05429593b96b15ee557f7c`, composed packet
  `b2616bdf5f566807c8fb1563dceea77478c5a21e52851937c52f3b19f43fb18e`,
  `PREPARED.json` `prepared-not-executed` / `start_selected false`. **No pass
  was discarded.**
- **The identity and the input are correct in the bound document, read back
  rather than asserted**: composed `run_id durable-capture-w341357-345822`,
  `work W341357`, `claim 345822`, **50 `fixture.files`** carrying
  `candidate.patch` at `5030be08…` — the reviewer's published digest — and
  **no `objects.bundle` anywhere in the fixtures**. The composed task
  instructions name the four methods and `W341357-VERIFICATION.json`, read back
  from `task.json`.
- **Sixty-one probes, all behaving as intended, 2.555s — carried unchanged.**
- **Generated limits agree**, re-read from this claim's composed documents:
  provider 3600, verification 30, one invocation, no retry, `report-and-hold`,
  4800 total, 60 cleanup, 1110 residual.

Author evidence, **not** independent product acceptance.

## Disclosures

- **The candidate is retained and UNACCEPTED.** Adapter disposition
  `verification-failed`, worker disposition `unable`, no published proposal,
  `acceptance: unobserved`. Its 63 producer cases reporting no failure is
  **useful evidence, not independent signoff** — the reviewer's words. Full
  producer byte review comes after the gate is usable.
- **"Pre-existing" is a hypothesis.** No base measurement of this argv exists in
  any run. `TASK.md` step 1 asks the turn to produce that comparison rather than
  assume its answer.
- **Absence from a traceback is not exoneration.** 21 frames in
  `test_maintenance.py`, 15 in `workspaces.py`, zero in any changed path — real,
  mechanical, and not a general proof of innocence.
- **The subprocess diagnosis is an inference, not a measurement.** Confirming it
  is step 1.
- **An invocation has now completed for this Work** — run345039. The older
  disclosure that none ever had is **withdrawn**. What remains true: **no
  invocation has produced an accepted candidate**, and two selected packets never
  ran at all.
- **The composer still emits the unenforced start** at `09fbf3c5…` line 721.
  Reported for classification, not patched; mitigated by
  `AUTHORING-COMMAND.json` and `PREPARED.json`'s
  `composer_start_is_unenforced`.
- **The 900-second lease is enforced and unextended.** The last run returned at
  461.10s with 439s of margin; that is comfort, not licence.
- **The structural credential preflight cannot detect an expired session.**
  Reported, not widened. This claim ran no boundary preflight at all — that
  belongs to the selected-run turn.
- **Two gate exclusions still rest on out-of-boundary measurements** — the
  51.333s and 19.888s figures for `test_authoring_shutdown_deadline` and
  `test_authoring_manager_guard`, measured by direct host execution at
  claim339421 outside that claim's preparation boundary. Stated rather than
  laundered, and not re-measured.
- **Two probes refuse earlier than I predicted.**
  `drifted-candidate-transport-bundle` and `run-evidence-names-another-candidate`
  both trip the index-versus-pins comparison first, so neither exercises the
  check it is named for. Recorded as they behaved in
  `PREFLIGHT.json`, because claiming coverage a probe did not provide is the
  habit this campaign keeps catching.
- **`AGENTS.md` at this base carries the older W321689 exception section**,
  because the host's replacement is an uncommitted working-tree edit. The
  exception is expired either way.

## Ownership and what is still owed

`baton.impl` owns this packet, `PROGRESS.md` and the isolated candidate; the
reviewer owns `FINDING.md`, `PLAN.md` and the reviews. W333485 owns the separate
serving-renewal preparation at `baton.codx`, with no dependency either way; the
candidate touches no `job_manager` file, so that intersection is empirically
empty, and `intake.py` and `attempts.py` remain the declared overlap for serial
integration.

Still owed: independent review of **this** preparation; an exact separate
execution selection; the fixture correction and a complete gate; the
base-versus-candidate comparison; independent producer byte review and
acceptance of whatever candidate survives; parent W333486's ordinary
status/report integration, full joined twelve-module gate, installed-bundle
proof and joined acceptance; and the parent's pending human checkpoint.

**Nothing in this packet selects or authorizes a start.**
