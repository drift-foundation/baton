# Progress

Created for bounded decomposition; implementation handler records work here.

## 2026-10-19 — claim 329622: Stage A and the shared vocabulary delivered; the two materializers are NOT

**Source bound freshly, after both gates closed.** W321780 closed satisfying
(packet checkpoint `6348161e608187393e45454db63c192a93f6deb3`) and W321528
closed satisfying with candidate `602d7c14` accepted on `03b94fc8`. The
human integration of that delivery is this tree's `HEAD`, read this claim:

```
<BASE> = bbdacb5d38f6cf2d2461e9da103d28f9ab30cc6c
         "fix(v12): report retained failed-run candidates and effective timeouts"
```

`2c89d3aa` is **not** bound anywhere; the retained unaccepted candidate stays
unaccepted. The v12 source was clean at `HEAD` when this claim began (the only
working-tree modifications were another dossier's reviewer files).

### What is delivered, and it is one slice rather than the Work

`PACKET.md`'s lifecycle trace splits this Work's behaviour into what is
decidable **before** any view exists and what is decidable **only inside one**.
This claim delivers the first half, as the module both holders consume:

| artifact | what it is |
| --- | --- |
| `v12/python/src/baton_v12/verification_context.py` | STAGE A, the closed durable vocabulary, and the derived import path. Imports `re` and nothing else |
| `v12/python/tests/manager/test_verification_context.py` | 96 focused cases — every Stage-A row, the five legal combinations and each illegal one, the refusal direction in both generations, legacy non-reinterpretation, and the detail-carries-no-value rule |
| `v12/worker/Dockerfile.claude` | the module travels to the worker image under its own name, on the rule that admitted `source_profiles` and `attempt_log_format` |
| `v12/.dockerignore` | the one-file re-include that COPY needs; W202663 records that omitting it fails every build in this tree |
| `v12/python/tests/manager/test_claude_agent.py` | the travel allowlist and the import-graph case extended to the third admitted name |

Why this slice and not a thinner or wider one: Stage A is the only part of the
pair that **can** be decided identically by two holders without either one
building anything, and writing it once is the point — a contract each holder
spelled separately is two rules that can disagree while each half believes it
agreed. It is also the part that needed no new materializer to be honest.

`held()` cannot materialize anything: the module imports no filesystem verb at
all, and a case asserts that over its AST with a planted-call vacuity check
beside it. That is the structural form of "a Stage-A refusal leaves the view
unbuilt", rather than an observation of one directory.

### Three interpretations a reviewer should judge as interpretations

1. **The Stage-A cause mapping.** The packet's Stage-A table names its refusals
   without naming their causes, and the context document admits exactly four.
   `materialization` and `start-failure` cannot be reached before anything is
   materialized or started, so Stage A produces two: `missing-input` for a
   declared input or pinned path the **seal** does not hold or holds at other
   bytes, and `invalid-layout` for every declaration fault. Stated in the
   module docstring as a choice.
2. **Two sealed maps rather than one.** The packet asks the input question by
   `name` and the pin question by candidate-relative `path`, so `held()` takes
   `sealed` (by name) and `pinned` (by path). One map would have had to invent
   a single key for two differently-keyed facts.
3. **The task names the profile and base twice, so the two must agree.** `/3`
   is `/2` plus one member, so `source_profile`/`declared_base` keep their
   `/2` meaning *and* `verification_context.candidate` names them again. A
   holder reading the task would otherwise check out one revision while a
   holder reading the context verified another, each believing they agreed.
   Refused as `invalid-layout`. This is the derived-import-path argument one
   member over, and it is not quoted from the packet.

The profile vocabulary is **asked, not restated**: `pairing` is injected and the
tests compose it from the real `checkout_plan`, so `generic`-with-a-base and
`git`/`git-line`-without-one are refused by the package that owns them. The
refusal names the member pair and never the package's prose.

### Evidence, measured this claim

| run | result |
| --- | --- |
| `tests.manager.test_verification_context` | **96 tests OK, 0.023s** |
| the named 102 gate, literal argv from `PACKET.md` | **102 tests OK, 0.222s** (unchanged from the packet's measurement) |
| `tests.manager.test_claude_agent` + `test_claude_context` | **323 tests OK, 57.7s** |
| `tests.tools.test_dogfood_operator` | **359 tests OK, 5.7s** |
| `tests.manager.test_dogfood_image` (real build + container probes) | **16 tests OK** |
| `tests.manager.test_contracts_inventory` | 15 tests OK |

**Two failures that are NOT this candidate's, characterized rather than
asserted away.** `tests.manager.test_dependencies` fails 70 subtests at a
pristine `HEAD` export (`attempts.py`, `authority_port.py`,
`context_delivery.py` operand declarations and manager import rules) — the
failure set is byte-identical before and after this candidate, diffed. The
working tree shows one further failure,
`test_the_repository_carries_no_dependency_distributions`, because
`DISTRIBUTION.rglob("*.zip")` finds PyInstaller `base_library.zip` under the
git-ignored `v12/python/build/` left by a distro build dated 2026-10-18 10:28,
before this claim. Neither is touched here and neither is mine to fix; the
second is arguably a sweep that should exclude ignored build output, which is a
separate question and not this Work's.

### EXACT REMAINING SCOPE — the two materializers and everything that needs a view

Nothing below is started. No holder reads a `/3` task yet: `claude_agent.py`
and `dogfood_operator.py` are **unmodified**, so `/2` behaviour is exactly as
accepted and the new module is not yet reachable from either.

1. **Stage 6 — the worker's fresh disposable view** (`claude_agent._verify`
   today runs "the task's OWN command, in the candidate copy", and for a line
   the candidate *is* the retained worktree, which VER-3 forbids). It must take
   the candidate's own bytes with the measured `changed_paths` applied and
   every `removed` path absent, materialize each sealed input by `name` at its
   view-relative destination, own and delete only the view, and preserve the
   retained candidate and seal on success, test failure, timeout, failed start
   and partial materialization.
2. **Stage 8 — the operator's fresh disposable view**, from the retained output
   only: the accepted-base object source (the deployment's own retained
   repository, advanced solely by `tools/accepted_base.py`), the
   `objects.bundle` for `base..HEAD` resolving the published `head`, and the
   same seal. No fallback to an ambient host checkout.
3. **Stage B — view preflight in BOTH views**, with the causes the packet
   assigns: absent `working_directory`/`import_root` → `invalid-layout`; absent
   `required_path` → `missing-input`; input bytes, pins, reported changed and
   reported removed → `materialization`; `git-line` ancestry → `invalid-layout`;
   missing `base` in the object source → `missing-input`; unsatisfied bundle
   prerequisites or a transport resolving another head → `materialization`.
   The base is never checked out into a view.
4. **`/3` acceptance wired at both holders**, including the refusal direction
   against the live `TASK_SCHEMA` equality checks (`claude_agent.py:117`,
   `dogfood_operator.py:768`), and `baton.dogfood-proposal/3` /
   `baton.dogfood-operator-evidence/1` emitted with the members
   `CONTEXT-CONTRACTS.md` closes — including `result_digest`, `result_head` and
   `transport` bound to the retained output, and the generic-candidate case
   where head and transport are null.
5. **The acceptance obligation itself: the 102 gate passing in each of the two
   independently materialized views, zero skips and zero import or fixture
   errors**, plus the negative cases `VERIFICATION.md` lists for candidate
   exactness, deletion, substituted base, write/delete attempts reaching
   nothing retained, cleanup on timeout/start-failure/partial, ambient
   `PYTHONPATH` independence, and nothing unsafe in the durable record.

A separately selected concrete packet is still required for any live execution;
this claim selected none.

### Boundaries of this claim

No live provider run, no engine container beyond the image-recipe gate's own
throwaway probes, no credential read, no submission, no `start`, no deployment,
no raw SQL, and **no mutating Git operation** — the delivered files are
uncommitted working-tree changes, and the campaign's integration/checkpoint is
the human's act. `tests.manager.test_dogfood_image` builds from the live `v12`
context, so it exercised the new COPY without any index change.

## 2026-10-19 — claim 329810: the continuation packet, prepared and not executed

Review 2026-10-19T04-39-20Z (seq 329803) preserved the Stage-A slice and ruled
the **vehicle** wrong: host working-tree edits carry no selected v12 Job or
attempt provenance, and uncommitted bytes may not be treated as accepted
source. The authorized milestone was packet preparation only. That packet now
exists at `continuation-329810/` and **nothing in it has been executed against
its selected root**.

### What was delivered this claim

| member | what it is |
| --- | --- |
| `PACKET.md` | the reviewable document: vehicle, identities, the `/2`-vs-`/3` split, the one interpretation to judge, and what the packet does not claim |
| `PROVENANCE.json` | the freshly compared base, the checkpoint's triple-agreement, and the return that required this |
| `PREPARATION-PINS.json` | 112 manager files and 3 supervisor files **at the declared base**, the 13 task inputs, the bootstrap binary |
| `TASK.md` | the `/2` instructions: the load command, the five-part milestone, the sealed test-module convention, and the boundaries |
| `candidate-input/` + `restore.py` + `LOAD-COMMAND.txt` | the checkpoint as digest-bound input, placed by a digest-verified script that validates every buffer and every base file before its first write |
| `prepare.py` / `verify-inputs.py` | stage/bind, and the read-only check anybody can re-run |
| `CONTEXT-CHECK.json` / `LIMITS-CHECK.json` / `PREFLIGHT.json` | the three contract questions asked of the owning code, the resolved bounds, and the one throwaway-root preparation run |
| `OPERATOR.md` / `PACKET-INPUTS.json` | owner commands, labelled and unexecuted, and the sealed 17-member manifest |

### The base, compared rather than assumed

`HEAD` read at the start of this claim and again before sealing:
`bbdacb5d38f6cf2d2461e9da103d28f9ab30cc6c`. The five preserved files were
compared against **three** holders — the reviewer's `CHECKPOINT.json`
declaration, the reviewer's byte-for-byte copies under
`evidence/review-329794/checkpoint/`, and the live tree — and all three agree.
The base genuinely carries **neither** `verification_context.py` nor
`test_verification_context.py`, so their declared base digest is `null` and
`restore.py` refuses a checkout that already holds a file there. **The
preserved host files were not edited by this claim.**

### Evidence, measured this claim

| check | result |
| --- | --- |
| `verify-inputs.py` (read-only pins, base bytes, load-command agreement) | `prelaunch-input-pins-match`, 112 manager files, 13 task inputs, 10 gate names |
| `prepare.py stage` → `tools.bootstrap --no-repositories` → `prepare.py bind`, into `/tmp/w321776-preflight-329810` | all three steps status 0; `PREPARED.json` `state: prepared-not-executed`, packet `f5302a8d…` |
| `held_packet` + `verify_imported_sources` on the composed packet | pass — every artifact re-pinned, including all 13 `fixture.files`, before any store opened |
| `tools.dogfood_operator.held_task` on the composed launch | staged: `/2`, `source_root` `source`, `git-line`, base `bbdacb5d…` |
| the checkpoint buffer's own `held()` on the declared `/3` context | `ready`; derived import path `candidate/v12/python/src` |
| the generation boundary, both directions | `/2` asked for Stage A → `invalid-layout/schema`; `/2` carrying the member and `/3` lacking it → `invalid-layout/verification_context` |
| `execution_limits.resolved` | provider turn 900s, verification 30s (origin `job` on every boundary) |

No broad suite was re-run and **no image was rebuilt** — the reviewer forbade
both for preparation. No Job submitted, no engine or container, no provider, no
credential read, no deployment, no raw SQL, and no mutating version-control
operation. Cumulative verification spending for this claim is the three
preparation steps (~1.1s total wall) plus the read-only checks; the 96 focused
contract cases and the 102 gate were **not** re-measured, because their last
measurement is the reviewer's own at claim 329794 and re-running them proves
nothing new about a document.

### The interpretation a reviewer must judge

**The sealed verification argv is a `-c` program rather than `PACKET.md`'s
literal argv.** The literal argv needs a working directory and a derived
`PYTHONPATH`, and both come from `verification_context` — a `/3` member the `/2`
launch envelope does not have, with no environment assignment permitted in the
argv. So the sealed gate runs the same six credential-gate names plus the
restored contract, the image-recipe cases and the two new modules, under a
program that establishes `v12/python` and `src` itself; the literal argv stays
the `/3` obligation to be met inside the two produced views. The gate also
refuses a skip. If a reviewer reads VER-5 as requiring the literal argv at
launch, this is the member to correct and the packet is the place to correct it.

### EXACT REMAINING SCOPE — unchanged, and still unstarted

Stages 6 and 8, Stage B in both views, `/3` accepted at both holders with `/2`
still stageable, and `proposal/3` + `operator-evidence/1` bound to the retained
output, then the paired 102 gate in two independently materialized views plus
the VER-1..5 negatives. `claude_agent.py` and `dogfood_operator.py` remain
untouched at the base. The packet's bounds (900s turn, 1500s total) are carried
from the accepted table and **flagged as possibly too small** — W321528 selected
3600/4200 and still spent its turn; raising an accepted bound is the owner's
act.

### Coordination

W325695's actual overlap was posted to its own thread as T325695 seq 329931 —
the exact restored paths and the exact paths the turn will edit, so disjointness
is judged by path. No blanket gate, no reverse dependency, no launch
authorization claimed.

## 2026-10-19 — claim 329953: revision 2, concrete bounds and one real gate defect

Review 2026-10-19T05-00-43Z (seq 329950) accepted 329810's composition and
required one preparation revision: turn the acknowledged-inadequate historical
bounds into a **concrete proposal resolved from the generated submission**, with
the policy digest, packet bounds, submission and `LIMITS-CHECK` in agreement,
re-pinned and proved; preserve 329810 unchanged and supersede it.

`continuation-329810` is **preserved and re-verified member-by-member** — its
sealed manifest is still `1afddeeb3db646f5f574a41898a7084e3cbe192fd724202afca33f656507efdc`,
0 members drifted. The superseding packet is `continuation-329953/`, 18 sealed
members, manifest `356e8ef42295dcd5d7a966fb2a050bcba1d2991c9b074b945fa4572dd6d40fb0`,
run `paired-context-w321776-329953`, state `prepared-not-executed`.

### The bounds, proposed and resolved rather than asserted

`LIMITS-CHECK.json` is now **composed from the documents the preparation
generated** — `PACKET.json`, `policy.json`, `submission.json` — and it asserts
seven agreements, all true, including the policy digest recomputed from
`policy.json` and matched against the submission's own `policy_digest`:

| bound | proposed | resolved in the generated documents |
| --- | --- | --- |
| provider turn | 3600s | `bounds.turn_seconds` = `policy.provider_turn_seconds` = `submission.execution_limits.provider_turn_seconds` |
| verification command | **30s, not the requested 900s** | see below |
| total | 4800s | serving 4740s after 60s reserved cleanup |
| invocations / retry / terminal | 1 / none / `report-and-hold` | unchanged |

Residual margin 4740 − 3600 − 30 = 1110s. An estimate for one invocation, not a
correctness guarantee and not an authorization.

**The 900s verification ceiling is not expressible on this vehicle, and that is
reported rather than faked.** In fresh mode the composer fixes
`verification_command_seconds` at 30 in both places it appears —
`baseline_bindings.py:345`, the execution policy whose digest the submission
carries, and `:522`, the submission's own `execution_limits` — with no compose
parameter and no bounds member. The three ways to 900 were considered and
refused in writing: editing accepted supervisor product this claim does not own;
switching to contextual mode, which changes the packet schema to `/1`, the
runtime profile and drops the member from the submission; and writing 900 into
the check anyway, which is the prose-only edit the review refused. The unused
`VERIFICATION_SECONDS` constant the review flagged is **deleted**.

### A real defect found while proving the revision

329810's sealed gate program set `sys.path` only. `sys.path` does not cross a
process boundary, and named cases in the credential gate **spawn** the operator
as a subprocess — so the gate failed
`test_help_names_the_credential_source_the_launcher_requires` with returncode 1
because the child could not import `baton_v12`. A failure about the command's
own environment, wearing the shape of a candidate failure. The program now also
assigns `PYTHONPATH` from the same two derived facts (its own working directory
joined to its own import root) and **overwrites** rather than extends, so no
ambient value leaks in; the argv still carries no environment assignment.

| measurement | result |
| --- | --- |
| the eight gate names that exist at the base, without the assignment | 209 tests, **1 failure** (the subprocess case) |
| the same eight with it | 209 tests, **0 failures, 0 errors, 0 skips, 0.248s** |
| the **sealed argv verbatim** from the generated task, run with a deliberately useless ambient `PYTHONPATH` | status 1, 211 tests, 0.246s, **exactly two errors** — `tests.manager.test_verification_views` and `tests.tools.test_operator_verification_view`, the two modules the turn must write, and no credential case among them |

That last row is `GATE-CHECK.json`, and it is the point: the gate fails for the
right reason and only the right reason.

### Evidence re-run this claim, and only what the revision affected

`verify-inputs.py` → `prelaunch-input-pins-match`, 112 manager files, 13 task
inputs; `stage` → supported `bootstrap --no-repositories` → `bind` into a fresh
throwaway root, all three status 0, `PREPARED.json` `prepared-not-executed`,
packet `acd54228…`; `held_packet` and `verify_imported_sources` pass;
`held_task` stages the `/2` launch; the packet buffer's own `held()` returns
`ready` with derived import path `candidate/v12/python/src`; the generation
boundary refuses in both directions. No broad suite, no image rebuild, no Job
submitted, no engine or container, no provider, no credential read, no
deployment, no mutating version-control operation. Cumulative verification
spending this claim: the three preparation steps plus four read-only checks,
each sub-second; nothing re-measured that the revision did not affect.

### Unchanged

The declared base, the five preserved buffers and their digests, `restore.py`
byte-for-byte (`4db9bfc9…`), the vehicle, the image `c862c055`, the manager and
supervisor source selection, the task milestone, the module convention and every
boundary. Remaining scope is unchanged and still unstarted: stages 6 and 8,
Stage B in both views, `/3` at both holders with `/2` still stageable,
`proposal/3` + `operator-evidence/1`, then the paired 102 gate in two
independently materialized views plus the VER-1..5 negatives. The W325695
overlap notice stands at T325695 seq 329931, with the superseding run named in a
follow-up.

## 2026-10-29 — claim 383132: the paired delivery, under direct development

Handler `baton.claude`, role `impl`, claim seq **383132** on W321776 after the
ledger woke it at 383122. Read this turn: canonical `detail`, the complete
`work-events` history (31 events, 321776→383132), the whole `T321776` thread
(4 messages, last seq 371003), `AGENTS.md`, `docs/EFFECTIVE-BATON.md`, this
dossier's `FINDING.md`/`PLAN.md`/`PROGRESS.md`/`REVALIDATION-370930.md`/
`review-2026-10-28T22-02-18Z.md`, the sibling packet's `VERIFICATION.md`,
`CONTEXT-CONTRACTS.md` and `PACKET.md`, and `v12/DESIGN.md` VER-1..5.

### Source bound freshly, against the accepted W376586 candidate

`HEAD` = **8876bf950ff1f8ab8767ce9786df268cc9d767c6**. W376586 closed
satisfying; its accepted source is the independent review
`work/records/2026/10/finding-v12-typed-adapter-exchange/review-2026-10-28T23-32-40Z.md`
with manifest `evidence/review-378517/ACCEPTED-SOURCE.json`. **All 19 pinned
paths re-hashed at claim start: 0 drifted.** So the bytes this delivery builds
on are the reviewed ones, and the typed exchange/launch-/5/terminal work is
preserved rather than rebased away. The accepted candidate is still uncommitted
working tree; the human Git checkpoint for it is not mine to make.

Stage A (`baton_v12/verification_context.py`, 555 lines) and its 96 focused
cases are the committed Stage-A slice and are preserved; no byte of either is
restored from `continuation-329810`/`continuation-329953`, and no packet is
staged, bound or launched this claim.

### The vehicle

Direct development under the October 22 AGENTS ruling, as owner E370982
selected and `REVALIDATION-370930.md` recommended. No v12 Job, no launch
packet, no engine, no image build, no live provider, no credential read, no
deployment, no raw SQL, **no mutating Git operation of any kind** — including
inside a throwaway fixture, which this campaign has already recorded as a
policy finding once.

Baseline measured before the first source edit, for provenance only: the named
102-test credential gate on the current tree, **102 tests OK, 0.220s**
(`PYTHONPATH=src`, bytecode disabled, cwd `v12/python`). That is a host run and
establishes nothing about either view.

### WHAT IS DELIVERED — both holders, and the gate in each of their views

Exact candidate bytes: `evidence/claim-383132/CANDIDATE.json`. Measured runs
and every attributed failure: `evidence/claim-383132/RUNS.json` and
`focused.log`.

| path | what changed |
| --- | --- |
| `v12/python/src/baton_v12/verification_context.py` | Stage A preserved byte-for-byte in behaviour; **added** `held_seal`, `held_observation`, `view_plan`, `answered`, `held_evidence`, the seal/evidence/proposal member sets and the four view-question kinds. Still imports `re` and nothing else |
| `v12/worker/claude_agent.py` | `/3` accepted beside the frozen `/2`; the seal read from the input mount; **Stage A before the provider**; a fresh private view materialized, preflighted, run in and destroyed; `baton.dogfood-proposal/3` |
| `v12/python/tools/dogfood_operator.py` | `/3` accepted beside `/2`; `compose_seal`/`read_seal`; the operator's **own** view from the retained output — a retained candidate tree, or the accepted-base object source plus the incremental bundle through an injected repository capability; `baton.dogfood-operator-evidence/1` |
| `v12/worker/Dockerfile.integration` | the shared contract travels to the overlay image too, which `test_worker_packaging` caught as a stated-dependency gap |
| `v12/python/tests/manager/test_verification_views.py` | **new, 44 cases** — the worker's view |
| `v12/python/tests/tools/test_operator_verification_view.py` | **new, 38 cases** — the operator's view |
| `v12/python/tests/manager/verification_fixtures.py` | **new** — one declaration, one seal and one gate candidate, shared by both suites so neither holder can pass against its own arrangement |
| `v12/python/tests/tools/test_dogfood_operator.py` | the both-ends loader now reproduces the image's own directory, and two `/3` constants join the agreement cases |

**THE ACCEPTANCE OBLIGATION IS MET IN BOTH VIEWS.** The named 102-test
credential gate, as the LITERAL argv with the import path derived from the
declaration, passes:

- in the **worker's** own materialized view —
  `context: ready`, `command: passed`, `exit_status: 0`, zero skips and zero
  context errors;
- in the **independent operator's** own materialized view, built from the
  retained output and the same seal — `verification_status: 0` with a held
  `operator-evidence/1` bound to the retained result's digest.

Three verification suites together: **178 tests OK, 13.534s unittest /
13.72s wall.** The adapter and operator consumers:
`test_claude_agent + test_claude_context + test_worker_packaging +
test_worker_entry + test_exchange + test_dogfood_operator` = **973 tests OK**
(one pre-existing skip), 70.451s.

### Six interpretations a reviewer should judge AS interpretations

1. **Stage B's rules live in the shared module; the materializing and the
   reading do not.** `view_plan` answers an ordered collection of questions
   over view-relative paths and `answered` takes three readers the holder
   injects, so the module still creates nothing, opens nothing and imports
   `re` alone — the structural case over its imports is unchanged and still
   passes. The alternative was a Stage B spelled separately at each holder,
   which is two rules that can disagree while each half believes it agreed.
   The module's "NOT A MATERIALIZER" paragraph is KEPT and a dated amendment
   explains the narrowing.
2. **The seal is `baton.dogfood-seal/1`: one document plus one byte root.**
   The packet names "the sealed set" on every Stage-A row and never says what
   it is on disk. This defines it, and the pins live in it rather than being
   re-measured from a tree — because Stage A answers before the provider, and
   a holder that re-measured the candidate after the provider would be
   deciding a pin against bytes the provider could have changed. The packet
   says a pin is "decided against the seal, at sealing time".
3. **`proposal/3` adds five members, not three, and spans both profile
   branches.** `CONTEXT-CONTRACTS.md` writes `/3` as "every `/2` member" plus
   `context`/`command`/`exit_status`, and that is incomplete rather than
   wrong: `/2` has **no `removed` member at all**, and its `changed_paths` is a
   path inventory while Stage B's own row is "a path the retained result
   reports changed is absent OR PRESENT AT OTHER BYTES" — which no collection
   of paths can decide. So `candidate_changed` (digested) and
   `candidate_removed` join them, named identically to the operator's own
   members so a consumer compares the two holders directly. `/1` and `/2` stay
   frozen: a `/2` task produces exactly the record it always did, and a case
   asserts the new members are absent from it.
4. **The copy profiles now collect their deletions.** Their existing
   measurement walks the candidate, so a deleted path was invisible to the
   published result. A view bound only to changes would have accepted a
   substituted base, so `_removed_from` collects them from the baseline for
   the fresh generation. The line profile already collected its own.
5. **A `/3` view refuses a non-regular entry anywhere in the candidate.** The
   adapter already refuses a link among the turn's changes; the view copier
   widens that to the whole copied tree, because a copied link is how a view
   reaches outside itself. **This is a real limitation**: a candidate carrying
   a committed link cannot be verified under `/3` until a declared handling is
   selected. Silently skipping it was rejected — a view that quietly lacks a
   path the command may read is a view nobody can reason about.
6. **A context refusal answers a non-zero `verification_status` at the
   operator.** The ending decides its authority pass on that number, so `None`
   would read as absent and `0` as verified. A refusal answers the one value
   that is neither, with the evidence beside it saying no verdict about the
   candidate exists.

### Boundaries actually held this claim

No v12 Job, launch packet, engine, image build, live provider, credential
read, deployment or raw SQL, and **no mutating version-control operation in
any repository** — including a throwaway one, which this campaign has already
recorded as a policy finding once. The operator's version-control view is
driven by an **injected repository capability answered by a recorded simulated
repository**, and every report of it is labelled a **simulated boundary**. The
adapter's process capability is likewise injected: the "provider" is a
recorded fake and only the verification command is a real child.

One disclosure: the sweep included `tests.manager.test_worker_entry_engine`, a
daemon-backed module name, which was outside that posture. It failed in well
under a second on its own fixture's uid assertion — no image was built and no
container was created — and it fails identically at pristine `HEAD`.

### Found and NOT mine — seven failures, each attributed by swapping bytes

Full detail in `evidence/claim-383132/RUNS.json`. Nothing here is waived or
re-attributed by name alone; where a tree could be swapped, it was.

- **`test_credentials.OneOrderedTeardownOnEveryEnding`, 4 errors.** The
  fixture's `observe` lambda does not accept the `seconds=` keyword that
  `oci._removed` passes. **Reproduced at pristine `HEAD 8876bf95`** in an
  exported tree at `/tmp/w321776-attrib-1`; `test_credentials.py` imports
  nothing this candidate changes. Reported as a found defect rather than fixed
  here: it is outside this Work's accepted scope.
- **`test_execution_limits`, 3 failures** and
  **`test_source_boundary`, 1** — all reproduced at pristine `HEAD`.
- **`test_execution_limits.AFreshProcessAdoptsBothJobsConfiguredLaunches`** and
  **`test_stage_execution.OrdinaryTerminalLifecycle
  .test_fresh_process_observes_owned_completion_after_serving_closes`** — both
  are the `baton_v12.integration.admission` circular import, raised through
  `job_manager/role_contract.py:510`. These are the **two fresh-process
  circular-import failures W376586's accepted review already discloses**; the
  second does not reproduce at `HEAD` because `role_contract.py` is a new
  untracked W376586 file. This candidate touches no module in that cycle.
- **`test_single_worker` WAL/SHM observational-file failure** — the one
  W376586's accepted review discloses by that name.

### Not measured, and therefore not claimed

`test_integration_image` and `test_dogfood_image` BUILD the reference worker
image, which this claim's no-build posture excludes. The new
`Dockerfile.integration` layer is established by `test_worker_packaging`,
which stages exactly what each recipe names into a directory outside the
checkout and imports the programs there — that proves the recipe STATES the
dependency and not that an image was built. No real repository behaviour is
measured anywhere.

### The human Git checkpoint that is due

This delivery and the accepted W376586 candidate are both uncommitted working
tree. The milestone checkpoint is Slawomir's act, not an agent's; suggested
message **`Complete paired verification contexts`**. Carried explicitly until
it is fulfilled.
