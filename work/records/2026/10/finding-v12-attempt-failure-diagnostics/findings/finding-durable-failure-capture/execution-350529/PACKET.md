# W341357 — CONSUME THE CORRECTED HOST RUNTIME, then correct R1 and R2

`baton.claude`, claim350529, role `impl`. **Preparation only.** No Job
submitted, no attempt, no runtime, no engine, no provider, no credential read,
no version-control mutation, no host product or test edit, **and no product
test executed.** **The start is not selected.**

| | |
| --- | --- |
| base | `bc925cf5c62d69426ed5862af4d41f4d2a967b0f` |
| proposed run | `durable-capture-w341357-350529` |
| proposed root | `/home/sl/baton-instances/durable-capture-w341357-350529` — **absent**, created by step 1 |
| continues from | `../execution-348852` — selected by owner348925, **launched once, and the controller DIED AT IMPORT in about two seconds**. Preserved, seal still verifying |
| why | the 114-member binding it staged did not declare `tools/authoring_baseline.py`, which the accepted controller imports at lines 494, 506 and 554. **W348979 corrected the binding**; owner350489 closed it satisfying |
| input | **the candidate whose gate passes**: head `e9d292ede76a…`, content `sha256:59d666d9…`, patch `294368c5…`. **RETAINED AND STILL UNACCEPTED** |
| start | `start_authorized: false`, `start_selected: false` |
| exact commands | `COMMANDS.md` (six, no placeholders; step 5a–5e is the operator's post-run collection) |
| host runtime | the **corrected accepted archive** `6b66a5e2…` bound by `HOST-POLICY.json` `8309fd6e…` — **115 members**, controller **`248ee9ed…`**, deferred baseline dependency `8e5987f5…`, helper `af9e5ea6…` |
| permission | 3600 / 30 / 4800 / 60, **stop origin + 4740, expiry origin + 4800** — the 900-second lease is retired |

## What happened, and what this packet is for

**The gate passes. Two producer defects remain. And the last selected run never
reached either of them.**

Owner347178 selected `../execution-345822`; it completed on its own at 733.29
seconds and **its sealed gate passed** — `864 tests in 12.631s`, `OK`, exit 0,
no skips, independently confirmed by the reviewer hashing the raw stream in
place.

Owner348925 then selected `../execution-348852`, which is this packet's
predecessor. It was launched once at 19:06:22Z and **the controller exited in
about two seconds**:

```
File ".../code/v12/python/tools/authoring_enforcement.py", line 554, in main
    from tools import authoring_baseline as baseline
ImportError: cannot import name 'authoring_baseline' from 'tools'
```

No envelope, no Job, no attempt, no runtime, no token, no container, no provider
call — and therefore nothing to clean. The accepted controller imports
`tools.authoring_baseline`; the accepted 114-member binding preserved the old
consumer host's runtime path set exactly, and that path set never carried the
module. Two independently accepted artifacts, mutually inconsistent.

**W348979 fixed the binding, not the controller and not this packet's task.** It
added the one member byte-for-byte from the accepted host base
(`8e5987f5…` — the same bytes as the supervisor baseline, which the accepted
host base moved *into* the manager source), preserved the other 114 unchanged,
and published a static closure proof. It was independently reviewed and
owner350489 closed it **satisfying**. `FAILURE.md` carries the account for the
worker; `decisions/host-policy.json`, `decisions/host-operator-delta.md`,
`decisions/host-closure-VERIFIED.json` and
`decisions/host-import-closure-review.md` are the supplier record.

**So this packet consumes the corrected binding and changes nothing else.** The
producer work is exactly what it was: R1, R2, the complete five-module gate and
the extended report, starting from the same retained candidate.

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

## What changed from `../execution-348852` — minimally, as required

| changed | why |
| --- | --- |
| **the host binding** | `host-policy-347952/HOST-POLICY.json` (`eb57aa9c…`, 114 members) → `runtime-348981/HOST-POLICY.json` (`8309fd6e…`, **115 members**), archive `1693bdd0…` → `6b66a5e2…`. `prepare.py` and `verify-inputs.py` read the new constants and **additionally refuse a binding that omits `tools/authoring_baseline.py`** |
| **`SHUTDOWN.md`** | its "this packet pins" column named the **superseded** controller `d12769df…` through four sealed revisions, and said `manager_files` holds 114 entries. Corrected, with the W338305 column kept as history — and the import-failure rule that section states is recorded as having now fired a second time |
| **`FAILURE.md`** | the same superseded controller claim corrected, and the run348852 import failure recorded as the second startup failure on this vehicle, with what it was **not** and the preflight gap stated |
| **`prepare.py`** | three false current statements: "THE VEHICLE IS UNCHANGED. Controller `d12769df…`, 114 pinned manager files"; "`tokens.LIFETIME_SECONDS` IS STILL 900 … no authoring invocation has ever completed"; and the unselected-start warning printed at every stage, which named two never-run selections and claimed the gate had never been measured |
| **the generated command document** | `AUTHORING-COMMAND.json`'s `lease` member asserted *"expect enforced expiry at 900 seconds"* — **generated into every root, including run348852's, four claims after the packet documents retired it**. It is now a `permission` member, with the superseded text preserved beside it |
| `PREPARATION-PINS.json`, `PROVENANCE.json` | the 115-member map, the binding, the re-measured host/worker-base comparison, the blocker account, and the campaign record, which still said five runs and one gate measurement |
| `GATE-CHECK.json`, `LIMITS-CHECK.json`, `PREFLIGHT.json` | re-derived from **this** claim's composed documents. `GATE-CHECK` also carried *"four runs; zero measurements"* in the same file as *"measured three times and it now passes"* |
| `decisions/` | **4 re-taken, 5 added**; 52 → **57**. Task inputs 61 → **66** |
| `COMMANDS.md`, `OPERATOR.md`, this document | the identity, the binding, the record and every regenerated count |
| `PACKET-INPUTS.json`, `SHA256SUMS` | the resultant seal |

**Not changed at all:** `probe.py`, `collect.py`, the host-reading mechanism
itself, the controller and helper identities, the three supervisor seals, the
worker base, the retained candidate, `recovery-345822`, the sealed gate argv,
every limit figure, and **five of the seven worker-visible documents** —
`TASK.md`, `RECOVERY.md`, `COMPLETION.md`, `FIXTURE.md` and `ENFORCEMENT.md`
travel byte-identical.

**Unchanged and proved rather than asserted:** the verification member digest
re-derived from this claim's composed `task.json` is
`2f7ed3dca95da498657a0e549e53107679fd7e8cf4503d5022555ba9e642176c`, identical to
the one every accepted packet since claim339421 carried — **the same gate
across the corrected host binding**. 3600s provider, 30s verification, 4800s
total, 60s cleanup, one invocation, no retry, `report-and-hold`, **stop origin +
4740 and expiry origin + 4800**.

### The new snapshots, and why each is here

**Five added, four re-taken.** The four re-taken are `FINDING.md`, `PLAN.md`
and — now pointing at the corrected W348979 artifact — `host-policy.json` and
`host-operator-delta.md`. The five added:

| snapshot | why the turn or the reviewer needs it |
| --- | --- |
| `host-closure-VERIFIED.json` | the supplier's own verdict: 115 members, 114 preserved, the old archive provably missing the deferred dependency, 1261 static edges, `product_executed false`. **Static, not startup evidence** |
| `host-import-closure-review.md` | the independent review of that correction, so the binding's acceptance is readable from the supplier record rather than from this packet's prose |
| `run-348852-BLOCKER.json` | what actually happened to the last selection, read without reaching into the preserved root |
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
7. **`FAILURE.md`** — the **two** startup failures on this vehicle: the
   single-manager refusal that cost the first selected execution, and the
   import failure that cost run348852.
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
No product test was executed to produce any of it and no instance was touched.

- **The supplier's own verifier, run read-only rather than reimplemented**:
  `verified true`, **115 members**, 114 preserved, the old archive
  provably missing the deferred main dependency, 1261 static import edges,
  `product_executed false` — 6.24s measured here. **Static. It
  does not establish that the controller starts, and nothing in this packet
  claims dynamic startup evidence.**
- **Input check** 0.06s, exit 0 — **115** manager files, 3
  supervisor, 2 preparation inputs, **66** task inputs,
  **57** decision snapshots, 4 checkout documents, 1 pinned
  controller, 1 pinned shutdown helper, **2** pinned recovery inputs, 1 gate
  module still owed, and **no decision-source drift** after re-taking
  `FINDING.md`, `PLAN.md`, `host-policy.json` and `host-operator-delta.md`.
- **Preparation exercised once** into `/tmp/w341357-preflight10`: stage
  0.079s, bootstrap 0.595s, bind 0.361s — **≈1.035s, all status 0**,
  authority `1227b3a0b4f244deb4c724d510cca229`, composed packet
  `8290126781ff5ae4a1b8f6c57799c6fe69be41d2496dcbe9ae93a74ae42295a3`, `PREPARED.json`
  `prepared-not-executed` / `start_selected false`.
- **The identity, read back from the bound document**: composed
  `run_id durable-capture-w341357-350529`, `work W341357`, `claim 350529`,
  **66 `fixture.files`**.
- **The corrected binding equals what was composed**: composed
  `manager_source.files` is **equal to `HOST-POLICY.json`'s `manager_files` as
  a whole map**, all **115** members; `tools/authoring_baseline.py`
  present at `8e5987f5…` in the binding, in the composed packet **and on the
  staged disk**; `manager_source.packages` is exactly `["baton_v12", "tools"]`,
  the package set the supplier requires a consumer to preserve; controller
  `248ee9edd72214efbdc77044a9af6ad2c382e2ca1dbd5b71ff0db720d9a5a5dc`; helper matches.
- **The new refusal is demonstrated, not claimed**: pointed at the exact
  114-member binding run348852 staged — whose bytes and archive digest both
  still verify — `prepare.py` and `verify-inputs.py` now both refuse with *"the
  binding does not declare the deferred controller dependency"*. Read-only, no
  root created, 0.02s. `probe.py` is carried unchanged, so this is recorded as
  a separate check rather than as probe coverage it does not have.
- **The worker did not move**: `candidate.patch` at
  `294368c55fd468a95a4375c250e560def0f4cbc0a0c8a2a3a6f2658732e83856`, base `bc925cf5…`, and the
  verification member digest `2f7ed3dca95da498657a0e549e53107679fd7e8cf4503d5022555ba9e642176c` — **the same gate across the
  corrected binding**. No `objects.bundle` anywhere in the fixtures.
- **Generated limits agree**, re-read from this claim's composed documents:
  provider 3600, verification 30, total 4800, cleanup 60, one invocation, no
  retry, `report-and-hold` — with **stop at origin + 4740 and expiry at origin
  + 4800** from the accepted envelope permission, and the generated command
  document now carrying a `permission` member instead of the retired lease.
- **61 of 61 probes behaving as intended, 2.381s —
  carried unchanged**, including across the corrected binding, which needed no
  probe edit because the host-reading mechanism is unchanged.

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
- **The binding defect was not a consumption defect, and that cuts both ways.**
  run348852's preparation, seals, binding equality and both preflights were all
  correct, which is exactly why nothing caught it. **Neither preflight checks
  that the staged manager source can import the controller it pins**; both
  passed and the controller still could not start. Reported and **not** widened
  into a new preflight — the review requires reusing the existing mechanism —
  and answered instead by the cheap in-scope refusal above. Whether to add a
  staged-import check is the owner's and the reviewer's call.
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
