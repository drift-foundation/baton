# W341357 — MEASURE FIRST, then correct the fixture storage

`baton.claude`, claim345822, role `impl`. **Preparation only.** No Job
submitted, no attempt, no runtime, no engine, no provider, no credential read,
no version-control mutation, no host product or test edit, **and no product
test executed.** **The start is not selected.**

| | |
| --- | --- |
| base | `bc925cf5c62d69426ed5862af4d41f4d2a967b0f` |
| proposed run | `durable-capture-w341357-348802` |
| proposed root | `/home/sl/baton-instances/durable-capture-w341357-348802` — **absent**, created by step 1 |
| continues from | `../execution-345822` — selected by owner347178, **ran once, completed on its own at 733.29s, and ITS GATE PASSED**. Preserved, seal still verifying |
| input | **the candidate whose gate passes**: head `e9d292ede76a…`, content `sha256:59d666d9…`, patch `294368c5…`. **RETAINED AND STILL UNACCEPTED** |
| start | `start_authorized: false`, `start_selected: false` |
| exact commands | `COMMANDS.md` (six, no placeholders; step 5a–5e is the operator's post-run collection) |
| host runtime | the **accepted archive** `1693bdd0…` bound by `HOST-POLICY.json` `eb57aa9c…` — 114 members, controller **`248ee9ed…`** (was `d12769df…`), baseline `8e5987f5…`, helper `af9e5ea6…` |
| permission | 3600 / 30 / 4800 / 60, **stop origin + 4740, expiry origin + 4800** — the 900-second lease is retired |

## What happened, and what this packet is for

Owner347178 selected `../execution-345822`. It ran once, **completed on its own
at 733.29 seconds** — provider status 0, token returned and not expired, workload
**settled**, stopped **completed** — and **its sealed gate passed**:

```
Ran 864 tests in 12.631s
OK
```

exit 0, **no skips**, independently confirmed by the reviewer hashing the raw
stream in place. The worker's own in-turn run reported 864/0/0/0 in 11.398s; a
separate measurement of the same argv, not an independent repetition.

Three gate measurements now exist on the same argv and the same 864 tests:

| run | result |
| --- | --- |
| `345039` | `failures=9, errors=7`, 12.817s |
| `345388` | `failures=0, errors=16`, 12.515s |
| **`345822`** | **OK, exit 0, no skips**, 12.631s |

**The lease, the 30-second ceiling and the storage pressure are settled.** The
same-environment base comparison ran at last — 801 tests with 2 failures at the
pinned base across the four shared modules, the candidate adding 63 and changing
nothing else — and those two were an umask-dependent **fixture** precondition
with the product read correct in both arms.

**And product acceptance is still withheld**, on two producer defects.
`review-2026-10-21T15-30-10Z.md` confirmed the gate in the same breath:
*"a passing gate lacking these injections does not establish it."*

### The two defects, revalidated in the candidate's own bytes

`FIXTURE.md` is the full account with citations; I read each one rather than
carrying it.

**R1 — a fresh observation is conflated with a replay of an old one.**
`failure_cause.py:524-545` walks the revision chain and returns any revision
whose **facts** match, through `_same_account` (line 461), which excludes only
`revision` and `supersedes` — deliberately. Nothing in the arriving document
distinguishes a new sample from a redelivery. `intake.py:5966-5982` re-samples
the adapter on **every** settlement call with the same component, generation,
runtime and correlation. So `quiescent` → revision 0, `uncertain` → revision 1,
then a **third fresh `quiescent`** matches revision 0, writes nothing, and the
reader keeps answering **revision 1, uncertain**. Reverse the order and a stale
positive wins. The existing replay test at
`test_attempt_failure_cause.py:167-184` supplies identical triples with no
identity separating redelivery from a fresh sample, so it proves value
deduplication and not the thing that matters.

**R2 — recording failures are discarded on the acting paths.** The contract
already exists and is honoured three call sites away —
`intake.py:5710-5711`, `intake.py:6058-6059` and `attempts.py:3647` all do
`if failure_cause.recording_degraded(reported): answer["diagnostic_degradation"]
= reported`. But `intake.py:5771-5775` and `:5788-5792` call the recorder as a
**bare statement**, drop its return, and hand back the ordinary dict; same at
the unresolved-attachment and positive-cessation branches, the settlement
non-absence path and some cancellation **exception** branches. So a post-intent
outcome-write failure leaves the record intent-only and tells an operator
nothing. And `failure_cause.py:733-734` returns a phrase
`recording_degraded()` does not test, so that one failure is invisible to the
classifier.

**Both are static traces, code-derived and never executed.** `TASK.md` step 2
requires a deterministic production-boundary reproduction of each **before** its
fix.

## What changed from `../execution-345822` — minimally, as required

| changed | why |
| --- | --- |
| **the host runtime** | the 114 members now come from the accepted archive instead of the old consumer host base; six of them differ, including the controller. The worker base, candidate and recovery are untouched |
| **`TASK.md`** | **reproduce-then-correct**, eight ordered steps: apply and confirm green, reproduce both defects at the production boundary, correct R1, correct R2, the full gate with no skips, **extend** `W341357-VERIFICATION.json`, land inside 720s, report only what the worker can observe |
| **`FIXTURE.md`** | rewritten as the two-defect account with citations, plus the fixture work that must survive |
| **`RECOVERY.md`** | rewritten for the passing candidate, and explicit that a passing gate is not acceptance |
| `PROVENANCE.json`, `COMMANDS.md`, `OPERATOR.md`, this document | the identity, the task and the record |
| `GATE-CHECK.json`, `LIMITS-CHECK.json`, `PREFLIGHT.json` | re-derived from **this** claim's composed documents |
| `decisions/` | two re-taken, **six** added; 41 → **47**. Task inputs 50 → **56** |
| `PACKET-INPUTS.json`, `SHA256SUMS` | the resultant seal |

**Not changed at all:** `prepare.py`, `verify-inputs.py`, `probe.py`,
`collect.py`, every limit, and the sealed gate argv. The recovery cross-checks
already bind a retained candidate at `baton.w341357-recovery/3`, so swapping
candidates again needed **no program edit and no new probe** — the second
consecutive packet where "reuse unchanged machinery" cost nothing.

**Unchanged and proved rather than asserted:** the verification member digest
re-derived from this claim's composed `task.json` is
`2f7ed3dca95da498657a0e549e53107679fd7e8cf4503d5022555ba9e642176c`, identical to
the one every accepted packet since claim339421 carried — **the same gate across
a host change**. 3600s provider, 30s verification, 4800s total, 60s cleanup, one
invocation, no retry, `report-and-hold`, **stop origin + 4740 and expiry origin +
4800**.

**`COMPLETION.md` no longer travels at `c8c5d4dd…`** and that is deliberate: it
carried the retired lease and the 600/720 cutoffs as policy, so it is the one
carried-verbatim worker byte this successor had to change.

### One new snapshot worth naming

`decisions/run-345822-W341357-VERIFICATION.json` carries **the previous turn's
own evidence report** at the digest the reviewer published
(`a5b69ad3…`), so this turn can read what was actually measured — roots, mounts,
bytes, inodes, lifetimes, assertion executions — **without reaching into a
preserved instance**.

### Two honest notes

**The filename `FIXTURE.md` is now wrong for its subject.** It is pinned by name
in `prepare.py`, `verify-inputs.py` and two probes, and the review required a
minimal continuation reusing unchanged machinery — so renaming it would edit
exactly that machinery. It keeps its name, says so in its first lines, and the
compromise is recorded rather than passed over.

**`TASK.md` step 6 corrects an instruction of mine.** The previous task demanded
correlation keys — `run_id`, `outcome_path`, `status_path` — that nothing in the
worker carries. That turn named them absent-by-structure rather than guessing,
which was right. The task no longer asks for them.

## The candidate transport, and why it is not a task input

The patch is the whole delivery. `candidate-objects.bundle`
(`806ef400…`) is recorded by digest and locator for provenance and is
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
`GATE-CHECK.json`, `LIMITS-CHECK.json`, `decisions/` (**47** immutable snapshots
indexed by `decisions/INDEX.json`), `SHA256SUMS` and `PACKET-INPUTS.json`.

## Preparation evidence, measured this claim

**No product test was executed to produce any of it. No instance was touched.**

- **Input check** 0.10s, exit 0 — 114 manager files, 3 supervisor, 2 preparation
  inputs, **56** task inputs, **47** decision snapshots, 4 checkout documents, 1
  pinned controller, 1 pinned shutdown helper, **2** pinned recovery inputs, 1
  gate module still owed, and **no decision-source drift** after re-taking
  `FINDING.md` and `PLAN.md`.
- **Preparation exercised once** into `/tmp/w341357-preflight6`: stage 0.12s,
  bootstrap 0.59s, bind 0.36s — **≈1.07s, all status 0**, authority
  `072edae375bc4f1081259d6ded8c6aa2`, composed packet
  `3cb30f2ade304af12b793bd16884c3164d46a5b9b420f9bf047638b843b7e9b4`,
  `PREPARED.json` `prepared-not-executed` / `start_selected false`. One input
  check was discarded — it refused because `TASK.md` did not yet name the owed
  gate module by its full path — and is not counted.
- **The identity and the input are correct in the bound document, read back
  rather than asserted**: composed `run_id durable-capture-w341357-348802`,
  `work W341357`, `claim 347396`, **56 `fixture.files`** carrying
  `candidate.patch` at `294368c5…` and the previous turn's report snapshot at
  `a5b69ad3…` — both the reviewer's published digests — and **no
  `objects.bundle` anywhere in the fixtures**. The composed task instructions
  name `W341357-VERIFICATION.json`, `diagnostic_degradation` and
  `recording_degraded`, read back from `task.json`.
- **Sixty-one probes, all behaving as intended, 2.506s — carried unchanged.**
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
- **An invocation has completed and a gate has passed.** The older disclosures
  that no invocation ever completed and that the gate was unmeasured are both
  **withdrawn**. What remains true: **no candidate has been accepted**, two
  selected packets never ran at all, and a passing gate is not acceptance.
- **The composer still emits the unenforced start** at `09fbf3c5…` line 721.
  Reported for classification, not patched; mitigated by
  `AUTHORING-COMMAND.json` and `PREPARED.json`'s
  `composer_start_is_unenforced`.
- **The 900-second lease is retired.** W333485's correction was independently
  accepted and closed satisfying; permission derives from the persisted
  envelope. The three completed runs returned at 461.10s, 789.14s and 733.29s —
  all of them inside the *old* limit, so none of them exercised the new
  permission, and no live run has.
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
