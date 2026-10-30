# W341357 — MAKE THE GATE USABLE, from a real retained candidate

`baton.claude`, claim345388, role `impl`. **Preparation only.** No Job
submitted, no attempt, no runtime, no engine, no provider, no credential read,
no version-control mutation, no host product or test edit, **and no product
test executed.** **The start is not selected.**

| | |
| --- | --- |
| base | `bc925cf5c62d69426ed5862af4d41f4d2a967b0f` |
| proposed run | `durable-capture-w341357-345388` |
| proposed root | `/home/sl/baton-instances/durable-capture-w341357-345388` — **absent**, created by step 1 |
| continues from | `../execution-345039` — selected by owner345206, **ran once and completed on its own at 461.10s**. Preserved, seal still verifying |
| input | **the exact retained candidate**: head `370a0aebd6a4…`, content `sha256:1599471c…`, patch `f9e68939…`. **RETAINED AND UNACCEPTED** |
| start | `start_authorized: false`, `start_selected: false` |
| exact commands | `COMMANDS.md` (six, no placeholders; step 5a–5e is the operator's post-run collection) |
| vehicle pins | **unchanged for the eighth packet running** — controller `d12769df…`, baseline `8e5987f5…`, helper `af9e5ea6…`, 114 manager files |

## What happened, and what this packet is for

Owner345206 selected `../execution-345039`. It ran once and **completed on its
own at 461.10 seconds** — `provider.status 0`, `failure_reason null`, no
interruption, 439s of lease margin, the 600/720/180 cutoffs met without being
tested. It returned the first candidate this slice has produced **and the first
gate measurement in this campaign**:

```
Ran 864 tests in 12.817s
FAILED (failures=9, errors=7)
```

**The 30-second verification ceiling fits with room.** That question was
explicitly unproved in every packet for this Work; this packet retires the
disclosure. Two qualifiers: unittest's self-reported interval is not the
adapter's whole wall clock, and **the gate exited 1**.

**All 16 failing cases are in `tests.manager.test_maintenance`.** `test_intake`,
`test_attempts`, `test_contracts_inventory` and the candidate's own
`test_attempt_failure_cause` — 63 cases — reported none. Every traceback frame
is in `test_maintenance.py` (21) or `workspaces.py` (15), and **no changed path
appears in any traceback**. That is mechanical and real, and it is still not a
general exoneration — `review-2026-10-21T10-42-55Z.md` says so, and **no base
measurement of this argv exists in any run**.

So the reviewer verified the evidence, **withheld acceptance**, and required
**one bounded correction**: make the complete existing five-module gate usable
under the actual verification environment, from this exact candidate, without
weakening anything — and *"do not discard this retained candidate and repeat
open-ended authoring."* That is what this packet prepares.

## The conflict, revalidated in the tree

`FIXTURE.md` is the full account with citations. In short, four places:

1. **`tests/manager/test_maintenance.py:135-137`** — `setUp` stores
   `tempfile.TemporaryDirectory().name`, whatever spelling that is, and every
   derived path is built from it.
2. **`v12/worker/claude_agent.py:3262-3301`** — `_pinned_environment` opens each
   verifier root *before the provider runs* and exports it as
   `/proc/self/fd/<n>`, deliberately, because checking a pathname just before
   launch leaves a check/use interval. `TMPDIR` is one of `EPHEMERA_ROOTS`.
   **This boundary is correct and stays.**
3. **`worker_manager/workspaces.py:6221-6228`** — `_composed_line_roots`
   requires `realpath(place) == place`. A `/proc`-aliased place can never
   satisfy it. **This is a production security check and it stays.**
4. **`tests/manager/test_maintenance.py:249-252`** — `MaintenanceCase.executed`
   discards the child's `returncode` and `stderr`, so a child that cannot
   resolve a parent-descriptor path becomes an empty-output `IndexError` at
   lines 331 and 821. **Not yet confirmed dynamically; confirming it is step 1.**

Both source files are byte-identical to the committed base and neither is among
the candidate's changed paths.

**My argument for the correction, carried as reasoning to confirm rather than as
fact:** the verifier's authority is the descriptors it opened before the
provider ran, re-checked by `_revalidated_directories`. A directory a test
creates *inside* those roots *during* verification is the fixture's own object,
and resolving it to its canonical spelling gives the provider no name to swap —
the provider is already gone. The production refusal is untouched and must still
fire. `TASK.md` tells the turn to confirm or reject that argument, and forbids
relaxing either check to obtain a pass.

## What changed from `../execution-345039`

| changed | why |
| --- | --- |
| **the input** | `recovery-341360` (a producer split from an unfrozen tree, never executed) is replaced **as input** by `recovery-345039`, the exact retained candidate. The old set stays in place as history; its pins are dropped, not edited |
| **`TASK.md`** | restructured around the correction: confirm both diagnoses dynamically, correct the fixture, run the complete gate with no skips. Producer work stays owed and out of scope unless this turn's gate demonstrates a defect |
| **`FIXTURE.md`** | **new**, and a pinned task input — the measurement, the four citations, all 16 case identities, and the five things the correction must leave standing |
| **`RECOVERY.md`** | rewritten for the retained candidate, and explicit that it is retained and **unaccepted** |
| `prepare.py`, `verify-inputs.py` | recovery cross-checks retargeted at `baton.w341357-recovery/3`; the candidate is now held against **four independent records** |
| `probe.py` | **ten new probes**, one per new refusal; three retargeted; the 23 collection cases carried |
| `PROVENANCE.json`, `COMMANDS.md`, `OPERATOR.md`, this document | the identity, the task and the record |
| `GATE-CHECK.json`, `LIMITS-CHECK.json`, `PREFLIGHT.json` | re-derived from **this** claim's composed documents |
| `decisions/` | two re-taken, five added; 31 → 36. Task inputs 41 → 45 |
| `PACKET-INPUTS.json`, `SHA256SUMS` | the resultant seal |

**Unchanged, and proved rather than asserted:** the five gate modules with every
case and assertion — the verification member digest re-derived from this claim's
composed `task.json` is `2f7ed3dca95da498657a0e549e53107679fd7e8cf4503d5022555ba9e642176c`,
**identical** to the one every accepted packet since claim339421 carried.
`COMPLETION.md` travels verbatim at `c8c5d4dd…`. 900s lease, 3600s provider, 30s
verification, 4800s total, 60s cleanup, one invocation, no retry,
`report-and-hold`, and the 600/720/180 planning cutoffs. `ENFORCEMENT.md`,
`SHUTDOWN.md`, `FAILURE.md` and `collect.py` byte-identical.

## The candidate transport, and why it is not a task input

The patch is the whole delivery. `candidate-objects.bundle`
(`9dfce290…`) is recorded by digest and locator for provenance and is
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
`GATE-CHECK.json`, `LIMITS-CHECK.json`, `decisions/` (**36** immutable snapshots
indexed by `decisions/INDEX.json`), `SHA256SUMS` and `PACKET-INPUTS.json`.

## Preparation evidence, measured this claim

**No product test was executed to produce any of it. No instance was touched.**

- **Input check** 0.12s, exit 0 — 114 manager files, 3 supervisor, 2 preparation
  inputs, **45** task inputs, **36** decision snapshots, 4 checkout documents, 1
  pinned controller, 1 pinned shutdown helper, **2** pinned recovery inputs, 1
  gate module still owed, and **no decision-source drift** after re-taking
  `FINDING.md` and `PLAN.md`.
- **Preparation exercised once** into `/tmp/w341357-preflight4`: stage 0.12s,
  bootstrap 0.59s, bind 0.36s — **≈1.07s, all status 0**, authority
  `ef1c08aca5844a0eabdd0ba080650988`, composed packet
  `85e1314bcbe2570e103cc6b8b9b5db729ea5b1eade434198368325daaef22997`,
  `PREPARED.json` `prepared-not-executed` / `start_selected false`.
- **The identity and the input are correct in the bound document, read back
  rather than asserted**: composed `run_id durable-capture-w341357-345388`,
  `work W341357`, `claim 345388`, **45 `fixture.files`** carrying
  `candidate.patch` at `f9e68939…` — the reviewer's published digest — and
  **no `objects.bundle` anywhere in the fixtures**.
- **Sixty-one probes, all behaving as intended, 2.525s.** Ten new, one per new
  refusal.
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
