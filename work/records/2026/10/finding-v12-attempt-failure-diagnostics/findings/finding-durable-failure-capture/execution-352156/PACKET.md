# W341357 — BIND THE SUPERVISOR THE CONTROLLER RUNS, then correct R1 and R2

`baton.claude`, claim352156, role `impl`. **Preparation only.** No Job
submitted, no attempt, no runtime, no engine, no provider, no credential read,
no version-control mutation, no host product or test edit, **and no product
test executed.** **The start is not selected.**

| | |
| --- | --- |
| base | `bc925cf5c62d69426ed5862af4d41f4d2a967b0f` |
| proposed run | `durable-capture-w341357-352156` |
| proposed root | `/home/sl/baton-instances/durable-capture-w341357-352156` — **absent**, created by step 1 |
| continues from | `../execution-350529` — accepted, selected by owner352153, **launched once, and the controller REFUSED AT STARTUP in about two seconds**. Preserved, seal still verifying |
| why | the composition named `<root>/supervisor/baseline.py` as the supervisor program and the accepted controller runs `<root>/code/v12/python/tools/authoring_baseline.py` — **byte-identical files, different paths**, and `verify_imported_sources` compares the paths |
| the correction | **one composition argument**, plus a bind-time refusal, plus the host-side verification now running through the module the controller runs |
| input | **the candidate whose gate passes**: head `e9d292ede76a…`, content `sha256:59d666d9…`, patch `294368c5…`. **RETAINED AND STILL UNACCEPTED** |
| start | `start_authorized: false`, `start_selected: false` |
| exact commands | `COMMANDS.md` (six, no placeholders; step 5a–5e is the operator's post-run collection) |
| host runtime | the **corrected accepted archive** `6b66a5e2…` bound by `HOST-POLICY.json` `8309fd6e…` — **115 members**, controller `248ee9ed…`, helper `af9e5ea6…`, and **the supervisor program now bound as the staged `tools/authoring_baseline.py`** at `8e5987f5…` |
| permission | 3600 / 30 / 4800 / 60, **stop origin + 4740, expiry origin + 4800** — the 900-second lease is retired |

## What happened, and what this packet is for

**The gate passes. Two producer defects remain. And three selected invocations
in a row have now died before reaching either of them — the last two inside the
controller's own startup verification.**

`../execution-350529` consumed the corrected 115-member binding and was
independently accepted. Owner352153 selected it, it was launched once at
03:11:16Z, and the import at controller line 554 that killed run348852
**resolved**. The refusal came two statements later, at line 564:

```
File ".../tools/authoring_enforcement.py", line 564, in main
    baseline.verify_imported_sources(packet)
SupervisorRefusal: this process is running
'<root>/code/v12/python/tools/authoring_baseline.py' and the packet binds
'<root>/supervisor/baseline.py'
```

`verify_imported_sources` proves every package the packet names resolves inside
the bound manager source, and then proves that **the module it is defined in is
the program the packet binds**. Its docstring says it runs *before any store is
opened, which is the only moment at which refusing is free* — and that is
exactly what it did. Nothing was reached: no envelope, no Job, no attempt, no
runtime, no token, no container, no provider call, and nothing to clean.

**Whose defect: this packet's.** The old controller imported a top-level
`baseline` from the staged `supervisor/` directory, so the running module and
the composed supervisor path were the same file. The accepted controller imports
`tools.authoring_baseline` from the **manager source**. `prepare.py`'s `bind`
still passed `supervisor_path=<root>/supervisor/baseline.py`. The two files are
**byte-identical** (`8e5987f5…`, `cmp` reports no difference), so the supervisor
digest pin verified immediately before the refusal and **only the path equality
failed**.

**The correction, and nothing else:**

1. `bind` composes `supervisor_path` as the staged `tools/authoring_baseline.py`
   — the program the controller runs;
2. `bind` **refuses** if the composed supervisor program is not that path, or is
   not the pinned manager source member;
3. the host-side verification now runs through `tools.authoring_baseline` rather
   than the supervisor directory copy — because with (1) in place, verifying
   through the supervisor copy **refuses in mirror image**. That was measured,
   and it is how the full shape of this correction was found.

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

## What changed from `../execution-350529` — minimally, as required

| changed | why |
| --- | --- |
| **`prepare.py` `bind`: one argument** | `supervisor_path` is now the staged `tools/authoring_baseline.py` instead of `<root>/supervisor/baseline.py`. This is the whole defect |
| **`prepare.py` `bind`: two refusals** | it now refuses if the composed supervisor program is not that path, and if that program is not the pinned manager source member. The run that found this cost a selection; a refusal here costs nothing |
| **`prepare.py` `bind`: which module verifies** | `held_packet` and `verify_imported_sources` now run through `tools.authoring_baseline`, the module the controller runs. Verifying through the supervisor directory copy refuses in mirror image once the path is corrected — **measured** |
| **`FAILURE.md`** | the third startup failure recorded: the refusal, what the check is, why it fired, whose defect it is, and that the author's own pre-launch check had said it did not establish that the controller runs |
| **`ENFORCEMENT.md`** | the composer-start section amended: `commands.json`'s forbidden `start` is built from `packet['supervisor']['path']`, and that path moved. Still unenforced, still forbidden |
| `PREPARATION-PINS.json`, `PROVENANCE.json` | the supervisor program block, the blocker account, the startup-verification gap, and the campaign record at ten runs |
| `GATE-CHECK.json`, `LIMITS-CHECK.json`, `PREFLIGHT.json` | re-derived from **this** claim's composed documents |
| `decisions/` | **2 re-taken, 2 added**; 57 → **59**. Task inputs 66 → **68** |
| `COMMANDS.md`, `OPERATOR.md`, this document | the identity, the correction and every regenerated count |
| `PACKET-INPUTS.json`, `SHA256SUMS` | the resultant seal |

**Not changed at all:** the corrected 115-member binding and its archive, the
controller `248ee9ed`, the helper `af9e5ea6`, the three supervisor seals, **the
supervisor digest pin itself** (`8e5987f5…` — the bytes did not move, only the
path this packet names), `probe.py`, `collect.py`, `verify-inputs.py`, the
worker base, the retained candidate, `recovery-345822`, the sealed gate argv,
every limit figure, and **five of the seven worker-visible documents** —
`TASK.md`, `RECOVERY.md`, `COMPLETION.md`, `FIXTURE.md` and `SHUTDOWN.md`
travel byte-identical.

**Unchanged and proved rather than asserted:** the verification member digest
re-derived from this claim's composed `task.json` is
`2f7ed3dca95da498657a0e549e53107679fd7e8cf4503d5022555ba9e642176c`, identical to
the one every accepted packet since claim339421 carried. 3600s provider, 30s
verification, 4800s total, 60s cleanup, one invocation, no retry,
`report-and-hold`, **stop origin + 4740 and expiry origin + 4800**.

### The new snapshots, and why each is here

**Five added, four re-taken.** The four re-taken are `FINDING.md`, `PLAN.md`
and — now pointing at the corrected W348979 artifact — `host-policy.json` and
`host-operator-delta.md`. The five added:

| snapshot | why the turn or the reviewer needs it |
| --- | --- |
| `host-closure-VERIFIED.json` | the supplier's own verdict: 115 members, 114 preserved, the old archive provably missing the deferred dependency, 1261 static edges, `product_executed false`. **Static, not startup evidence** |
| `host-import-closure-review.md` | the independent review of that correction, so the binding's acceptance is readable from the supplier record rather than from this packet's prose |
| `run-348852-BLOCKER.json` | what happened to the run348852 selection, read without reaching into the preserved root |
| `run-350529-BLOCKER.json` | **added this claim** — the same for run350529, including the byte-identity finding and the minimal correction |
| `review-350688.md` | **added this claim** — the review that accepted `../execution-350529`; its acceptance stands for the bytes it verified, and it said plainly that dynamic startup was not among them |
| `review-348968.md` | the review that found the blocker and allocated the packaging repair |
| `review-350495.md` | the review that authorises **this** preparation |

The 236KB `STATIC-CLOSURE.json` edge list is **pinned by path and digest** in
`PREPARATION-PINS.json` rather than copied in: it belongs in the supplier
dossier, and the worker has no use for 1261 edges.

Carried from the previous packet and still the most useful single snapshot:
`decisions/run-345822-W341357-VERIFICATION.json`, **the last completed turn's
own evidence report** at the digest the reviewer published (`a5b69ad3…`), so
this turn can read what was actually measured — roots, mounts, bytes, inodes,
lifetimes, assertion executions — **without reaching into a preserved
instance**.

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
6. **`ENFORCEMENT.md`** — the vehicle, the composer's wrong start command, and
   the envelope-derived permission that replaced the 900-second lease.
7. **`FAILURE.md`** — the **three** startup failures on this vehicle: the
   single-manager refusal that cost the first selected execution, the import
   failure that cost run348852, and the supervisor-path refusal that cost
   run350529.
8. **`COMPLETION.md`** — the supported completion mechanism and **the
   envelope-derived permission**: stop at origin + 4740, expiry at origin +
   4800. It records the old 600/720/180 cutoffs as history, not as policy.
9. **`TASK.md`** — what the authoring turn is asked to do, in a fixed order.

`collect.py` and `probe.py` are the executable documents: the first is the
operator's read-only post-run collection, the second re-runs all **sixty-one**
refusal and collection cases in about 2.5 seconds.

Evidence: `PREPARATION-PINS.json`, `PROVENANCE.json`, `PREFLIGHT.json`,
`GATE-CHECK.json`, `LIMITS-CHECK.json`, `decisions/` (**57** immutable
snapshots indexed by `decisions/INDEX.json`), `SHA256SUMS` and
`PACKET-INPUTS.json`.

## Preparation evidence, measured this claim

**Regenerated from this claim's own composed documents, not carried forward.**
No product test was executed to produce any of it, and the only instance
touched was the one the owner selected — which refused at startup and is
preserved unchanged.

- **THE CORRECTION IS PROVED, NOT ARGUED.** `main`'s first three statements —
  `held_packet`, `verify_imported_sources`, `verify_controller` — were run in
  order against this claim's composed packet, in a child with the controller's
  exact working directory, `PYTHONPATH` and
  `BATON_V12_STAGE_EXECUTION_CONFIG`: **all three accept**, 0.330s. The same
  check against the packet composed at the preserved run350529 root
  **reproduces the exact refusal**, with `verify_controller` *not reached*
  rather than refused, because `main` stops at the first one. **It stops at
  `main`'s next statement, the authoring lock**: no lock taken, no store
  opened, no image inspected, no Job, no container, no provider, no credential.
  **It does not establish that the controller starts.**
- **`bind` now makes the same check itself**, through the module the controller
  runs, and refuses a composed supervisor program that is not the pinned
  manager source member.
- **Input check** 0.06s, exit 0 — **115** manager files, 3
  supervisor, 2 preparation inputs, **68** task inputs,
  **59** decision snapshots, 4 checkout documents, 1 pinned
  controller, 1 pinned shutdown helper, **2** pinned recovery inputs, 1 gate
  module still owed, **no decision-source drift**.
- **Preparation exercised once** into `/tmp/w341357-preflight11`: stage
  0.077s, bootstrap 0.606s, bind 0.367s — **≈1.05s, all status 0**,
  authority `c8ad2beebfce41e08958d57b1d0b100d`, composed packet `4ddf4dd6e40360b2b0d3db352152ac630af96b79aa66206805510da44c4e07d3`, `PREPARED.json`
  `prepared-not-executed` / `start_selected false`.
- **The supervisor program, read back from the composed document**:
  `<root>/code/v12/python/tools/authoring_baseline.py` at `8e5987f56f8d5329c33a8e73f9df56f13213e134f2dade8180afabf80723efe9` — **equal to the pinned
  `tools/authoring_baseline.py` manager source member**, and byte-identical to
  the staged `supervisor/baseline.py`, which stays staged and pinned as
  supervisor provenance because the **host** preparation imports
  `baseline_bindings` and `prepare_instance` from it.
- **The identity, read back from the bound document**: composed
  `run_id durable-capture-w341357-352156`, `work W341357`, `claim 352156`,
  **68 `fixture.files`**.
- **The host runtime is unchanged and still equals the accepted binding**:
  composed `manager_source.files` equal to `HOST-POLICY.json`'s `manager_files`
  as a whole map, all **115** members; `manager_source.packages` exactly
  `["baton_v12", "tools"]`; controller and helper match.
- **The worker did not move**: `candidate.patch` `294368c5…`, base
  `bc925cf5…`, verification member digest `2f7ed3dc…`. No `objects.bundle`
  anywhere in the fixtures.
- **61 of 61 probes behaving as intended, 2.468s —
  carried unchanged**, including across this correction.

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
  **withdrawn**. What remains true: **no candidate has been accepted**,
  **three** selected packets never produced a turn — `execution-334663` at
  0.506s, `execution-341637` at 10.56s and `execution-348852` at about 2s —
  and a passing gate is not acceptance.
- **Two consecutive selections died inside the controller's own startup
  verification**, and nothing in preparation was calling those three functions
  against the composed packet. run348852 at line 554, run350529 at line 564.
  Every preflight passed before both. **This claim closes that specific hole**:
  `bind` now performs `verify_imported_sources` through the module the
  controller runs, and the startup-verification check is run against the
  composed packet with the counterfactual recorded. `probe.py` is still
  unchanged; whether any of this should become a probe is the reviewer's and
  the owner's call.
- **And the preflight gap I reported at claim348929 was real in a way I
  understated.** I wrote that neither preflight establishes that the staged
  source can *import* the controller. The import was only the first of three
  refusals in that window. The author check I added before the last launch
  proved the import resolved and said, in terms, that it *"does not establish
  that the controller RUNS"* — correct, and insufficient.
- **Static closure is not startup evidence.** The supplier's 1261-edge proof
  and this packet's checks are all static. Only a selected invocation
  establishes that the controller starts.
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
  belongs to the selected-run turn. The last provider authentication was
  run345822's, which served 733.29s; **run348852 contacted no provider at
  all**.
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
execution selection; **R1 and R2 reproduced at the production boundary and then
corrected, as one cohesive correction**; the complete five-module gate with no
skips and the extended `W341357-VERIFICATION.json`; independent producer byte
review and acceptance of whatever candidate survives; parent W333486's ordinary
status/report integration, full joined twelve-module gate, installed-bundle
proof and joined acceptance; and the parent's pending human checkpoint.

**Still unproved by anything in this packet:** that the controller starts. The
binding correction is accepted and every check here is static, so only a
selected invocation can establish it.

**Nothing in this packet selects or authorizes a start.**
