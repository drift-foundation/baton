# W363066 — implementer progress

## claim363069 — per-Job task delivery through the owning composition

Answers the bound `FINDING.md` and `PLAN.md` under born thread363066.

### Base and inherited overlay, revalidated at claim start

Base commit `19f02ce1295b4517a85f0822d48754efc982f388`, confirmed by
`rev-parse HEAD`; the scoped status for `v12/python` is empty. The inherited
working overlay is the parent's `candidate-362931`, manifest
`02090c1c505a055722e15de6c3e06f3e9ed0b940619055a69253549a0169fc9b` — all
thirteen members plus the manifest re-hashed and all fourteen match. It is an
UNACCEPTED working baseline, as the FINDING says, and it is preserved
byte-untouched; this child's candidate is `candidate-363069/` and its manifest
records inherited versus changed bytes member by member.

### Read position

`detail work=W363066`, `work-events work=W363066` complete through seq363069
(`next_after` null, two events) and born thread `T363066` complete — one
message at seq363066, no newer discussion. Bound `FINDING.md` and `PLAN.md`
read in full, and the parent's `review-2026-10-26T19-22-51Z.md` R3 again.

### The authority question, settled rather than re-raised

My E363053 handoff said the per-Job task document needed an owner ruling
before implementation. The FINDING rejects that and names the authority:
SCH-1a already requires ordinary task/source/scope/acceptance creation with
manager-owned admission and no operator-authored manifests, the parent FINDING
already requires requested inputs to reach substantive work, and the AGENTS
September 28 ruling makes necessary file selection an implementation choice
rather than a permission gate. I accept that — moving task composition behind
the owning API implements the accepted outcome, and I found no conflicting
normative clause to identify. No specification change is proposed here.

### Source revalidated, and the seam this follows

`single_worker._task_bytes(given["task_document"], manifest["human_contract"])`
reads the task once at static preflight from the DEPLOYMENT's path;
`single_worker._input` publishes those held bytes into the attempt's input root
through `_published_task`/`_proved_task`, both of which already take a
`content=` override that the `judgment.json` delivery uses;
`stage_execution._Stage.prepare_context` forwards `worker.given["task_bytes"]`
to `provider_context.bind_context_invocation`; and
`contracts.manifest.JOB_INPUT_EXCLUDED` deliberately does not contain
`human_contract`, so the task is inside `job_input_identity` — which
`stage_execution._disagreements` and `single_worker._claimed` both compare.

The seam this delivery follows is the one the product already has for the same
shape of question: `single_worker.job_execution_reader(job_store)` is a narrow
read-only closure over the already-open Job owner, answering exactly one
question per stage because "a value remembered from admission would be a
second account of a fact the Job owner holds". A per-Job task is the same kind
of fact and is read the same way. `stage_execution._served_deployment` is the
existing per-bound-Job manifest substitution, today used for the integration
role, and the rule this delivery must honour is already written in it: "THE
MANIFEST AND THE TASK IT NAMES MOVE TOGETHER."

### What is delivered this round

**The composition and the identity are delivered and verified. The delivery
into the input root for the implementation and review roles is NOT, and the
exact code point is named below.** This is a confirmed defect narrowed, not
closed.

Candidate `candidate-363069/`, manifest
`f319f0cc1b1632d5127e860aa2ca92f4c31854fa5b48f3cd97d77656adce41ba`, sixteen
members over base `19f02ce1295b4517a85f0822d48754efc982f388`. Seven changed in
this child; the other nine are inherited from `candidate-362931` byte for
byte, and the manifest records which is which for every one.

| path | base | candidate-363069 |
| --- | --- | --- |
| `jm/creation.py` | new | `1ac6376876a083ac671445cc3f96e8e20034e9b9fe5077684bbfe02c39ab1420` |
| `jm/schema.py` | base bba74451… | `38ba3ca2e79fe347a3e80c67304af6ccce59cc9100af59b9c0babf579f8747af` |
| `tests/job_manager/test_creation.py` | new | `d6eed8b001f7eb7ba7cf3d55eefb61e40b9c138b5cbfffa025cc98994b692b5d` |
| `tests/tools/test_creation_ports.py` | new | `86797603c0d8f90efb8fc71dc529c33736ac2dd0e87724d4ffbcb2f92169afb1` |
| `tools/creation_ports.py` | new | `a9fc808a63f4d1e78b3ae5bc31937bc450380639cffc6b2057e9249af46a8933` |
| `tools/job_task.py` | new | `a9ce7948bd39e9e8b2981ad26f299f5e2ad388ad18c6a522337a1c7c27d6e919` |
| `tools/single_worker.py` | base 70cc0806… | `af2607f594716fe91b43d444d9ef2a24f700f7ab6a5634684c4aac9816b80934` |
| `tools/stage_execution.py` | base 07ac5119… | `5b0d8d1766f77766e02a48c9e43e9797ff6699779b2dafacc682d4c168825d89` |

`candidate-362931` is preserved byte-untouched; all thirteen of its members
plus its manifest were re-hashed at claim start.

### The composition, and where it lives

**`tools/job_task.py` — new.** The worker's task vocabulary is
`v12/worker/claude_agent.py`'s (`baton.dogfood-task/2`, exactly `schema,
task_id, instructions, verification, source_root, source_profile,
declared_base`) and nothing from `baton_v12` travels into that image — so the
composer is on the deployment side, where `single_worker` already holds the
`human_contract` rule. It is a **substitution of two named members, not a
second reader of that contract**: `task_id` and `instructions` are the two the
caller's request owns, every other member travels as the deployment wrote it,
and the receiving adapter remains the only party that validates the
vocabulary. A case asserts that directly — a task id the worker's own regex
rejects is composed without complaint, and the worker's rule is what says no.

**No digest check is weakened.** The composed bytes get their own
`content_digest` and `bytes`; the manifest's `human_contract` is replaced with
that artifact and its `manifest_digest` is recomputed by §12's rule; and the
result is proved by `check_manifest_structure` before anybody is handed it.
`delivered_bytes` is the single encoding, so the bytes the artifact names and
the bytes a worker would read are one computation.

**`creation_ports.DeploymentDerivation.derived(selection=...)`** composes it.
Without a selection the port answers the installed facts; with one it answers
this Job's task document, the manifest naming it, and an `input_digest` that
IS that manifest's Job-scoped identity. The Work is the port's own answer and
is added there rather than asked of the caller, which is what keeps this ONE
reading of the configuration rather than two.

**`creation.py`** builds the selection from members it owns, stores the task
document in the `template_jobs` row (new nullable `task_document` column), and
`_task_agrees` refuses inside the operation — before anything is reserved — if
the submitted input identity and the manifest naming the delivered task ever
disagree. That check is the finding stated as a precondition.

**`single_worker.job_task_reader(job_store)`** is the narrow read-only closure
the serving composition asks, modelled on `job_execution_reader` and for its
stated reason: "a value remembered from admission would be a second account of
a fact the Job owner holds."

**`stage_execution._with_job_task`** performs the substitution inside
`_served_deployment`, which is the one place a worker's held deployment becomes
the document it serves a particular Job under — and whose own comment already
required it: "THE MANIFEST AND THE TASK IT NAMES MOVE TOGETHER." It is now
threaded through `servable_workers`, `_job_workers`,
`integration_deployment_for` and `_integration_operations`.

**A Job with no own task is unchanged.** `job_task_of` answers `None` for a
Job submitted by hand, created before the column existed, or created against
a deployment that composes none, and its delivery is the installed task
exactly as before. A case asserts it stays servable.

### Two defects of my own, caught by my own cases

- **A selection dereferenced before it was owned.** `per_job_delivery` read
  `selection["job_id"]` before `instructions_for` validated the selection, so
  a missing member left a `KeyError` — the same shape as the parent's R4. The
  instructions are composed first now, and `instructions_for` owns every
  member of its operand: it is a public function in a module a deployment
  composes, so its operand is receiver input whatever `creation` did before.
- **`creation` reached into unvalidated request members.** Composing the
  selection needs the acceptance list and both scopes BEFORE
  `templates.resolve` runs, and reading them raw left a `TypeError` for
  `acceptance: null`. `_asked` now owns their SHAPES — stated as exactly
  that, with the path rule, the dedupe and the bounds still
  `templates._scope`/`_acceptance`'s.

### Evidence

`evidence/claim-363069/`, and `COMPOSED-TASK.txt` is the one to read first:
two distinct selections over one pool, each composed document printed with its
rendered instructions, its input identity and its `human_contract` artifact,
and the installed identity beneath which is neither of them.

- **`tests.tools.test_creation_ports`**: **28 cases, OK** (19 inherited). The
  nine added are `TwoDistinctTasksOnOnePool`: own content per Job, the
  deployment's members unchanged, the identity naming the delivered task, two
  identities neither of which is the installed one, **both stages of each Job
  servable through `stage_execution.servable_workers`**, the installed-task
  Job still servable, determinism, malformed-selection refusal, and the
  adapter remaining the only validator.
- **`tests.job_manager.test_creation`**: **76 cases, OK** — the inherited
  count, so the parent's R1 and R2 corrections still hold.
- **Whole `tests/job_manager`**: **1375 OK**, the inherited count.
- **`test_stage_execution` + `test_bootstrap` + `test_single_worker` +
  `test_creation_ports`**: 883 cases, 1 failure and 17 errors — **all 18
  pre-existing and byte-identical to the base**. `test_stage_execution` and
  `test_creation_ports` contribute none.

### Remaining scope, with the exact code point

**The implementation and review roles do not yet receive the per-Job task at
delivery.** `stage_execution` composes
`single_worker.worker_operations(one["deployment"], ...)` ONCE PER WORKER for
those two roles (line ~6656), not per bound Job — so the `_SingleWorker` that
runs an implementation stage still holds the installed `task_bytes` and
`input_manifest`, and `_input` publishes the installed task into the attempt's
input root. The selector now agrees about the per-Job document, and the
integration role is composed per bound Job and gets it; these two do not.

The seam for it is identified and is small, and I am naming it rather than
leaving the next claim to find it again:

- `_published_task` and `_proved_task` already take a `content=` override —
  the `judgment.json` delivery uses it — so `_input` can publish this stage's
  Job's bytes without a new writer;
- `stage` is in scope at `_input`'s caller, so the Job id is available;
- `job_task_reader` is composed and available, and `_SingleWorker` already
  holds exactly this shape of reader as `execution_context`;
- `_claimed` compares `job_input_identity(self.given["input_manifest"])`
  against the offer, so that comparison needs the per-Job manifest in the same
  change or the stage refuses its own claim.

Also still open, inherited from the parent and unchanged by this claim: the
connected implementation/review/correction/held rehearsal, the OBS-0 interval,
`NewJobBinding.create_binding` against an installed instance, and interruption
inside `bootstrap.prepare`. No figure for OBS-0 is offered and none should be
inferred from the suite timings in the evidence, which are harness wall time.

### Cost

Read-only investigation of `single_worker._task_bytes`, `_input`,
`_published_task`/`_proved_task`, `_claimed`, `job_execution_reader`,
`stage_execution._served_deployment`/`_disagreements`/`servable_workers`/
`_integration_operations`, `contracts.manifest.JOB_INPUT_EXCLUDED` and
`validate.verify_manifest_digest`, and `v12/worker/claude_agent.py`'s task
contract — which is what established that the composition is a two-member
substitution rather than a new document. Test runs: the ports suite about
eight times, the creation suite four, whole `tests/job_manager` three, and the
four-suite tools run once at ~270s plus one base comparison run. No live
provider, no engine, no total manufactured.

### Boundaries

No Git operation of any kind, in the repository or in the scratch roots. The
canonical `v12/python` tree is byte-unchanged and the scoped status for it is
empty. `candidate-362931` and every parent record and evidence directory are
preserved exactly; per the FINDING's split I wrote only `candidate-363069/`,
`evidence/claim-363069/` and this file, and the bound `FINDING.md`/`PLAN.md`
are the reviewer's and are unmodified. No live provider, engine, credential
read, deployment, install, instance operation, migration or cutover.

## claim363241 — the delivery completed: the requested task reaches the root

Answers `review-2026-10-26T20-10-02Z.md` under handoff363238. Base
`19f02ce1295b4517a85f0822d48754efc982f388`, unchanged; scoped status for
`v12/python` empty. At claim start all sixteen members of `candidate-363069`
and its manifest were re-hashed and all seventeen match.

**The reviewer's blocker is closed.** `stage_execution:6656` now hands the two
ordinary roles the per-Job task reader, `:1315` sends this stage's own bytes to
the provider context, and `single_worker._input` publishes and proves them —
with the claim comparison moved to the same per-Job manifest in the same
change, which the review required and which the stage would otherwise refuse
itself for.

### The member count, corrected

The review was right: my E363225 handoff said seven changed members while its
table listed eight. `candidate-363069` is **8 changed in that child and 8
inherited**, sixteen members. This claim's `candidate-363241` has
**17 members, 4 changed since
`candidate-363069` and 13 carried forward byte for
byte**; the manifest records base, inherited-362931, candidate-363069 and
candidate digests plus a changed flag for every one, and a `COUNTS` block so
the narrative cannot drift from it again.

| path | candidate-363241 |
| --- | --- |
| `tests/tools/test_creation_ports.py` | `640293c7fc826bde3a4e5648e0a0a1cd680fdaecaa868b4c05c45d72ef9172a7` |
| `tests/tools/test_job_task_delivery.py` | `71835383eef070115666eea62722c10c6559949c086b6c3766a32f54e1d2da48` |
| `tools/single_worker.py` | `9e5c1378e9fe196e882d45b7cabe9e5322eaa12a3d3c94f38f1f6ac78c2bb484` |
| `tools/stage_execution.py` | `ed2cf4423ff0f9d37b69532310696b211cb2d52b8da1cb5ffcddcf4c2add6fdd` |

`candidate-363069` and `candidate-362931` are both preserved byte-untouched.

### How the delivery works

**`_SingleWorker.job_task`** is the reader, held exactly as
`execution_context` is and consulted **per stage**. `_for_job(stage)` answers
the `(input_manifest, task_bytes)` pair this stage's Job is served under,
composed from a FRESH copy — `given` is the worker's installed configuration,
shared by every Job that worker serves, and is never written to. A worker that
cached one Job's task on itself would hand it to the next Job that asked, so
nothing is cached.

**The two travel together or neither does.** `_task_bytes` proved the
installed bytes against the installed manifest's own human contract, so a
per-Job task beside the installed manifest is a pair that validator would
never have accepted. `_for_job` returns both.

**`_claimed` compares the per-stage manifest.** The offer was issued for the
Job's own submitted input identity, so comparing against the installed
manifest would make the stage refuse its own claim — which is exactly what the
review said had to change in the same edit.

**`_input` publishes and proves the per-stage bytes** through
`_published_task`/`_proved_task`'s existing `content=` override, the one the
`judgment.json` delivery already uses. No new writer, and no digest check
removed: the read-back comparison, the 0444 mode and the restart proof are
unchanged and now run over the per-Job bytes.

**`prepare_context` asks the worker** rather than reading the shared
configuration, so the provider context binds the same bytes the input root
carries.

**The installed path is preserved three ways**, each asserted: a Job the
reader answers `None` for, a worker composed with no reader at all, and a
stage with no Job — the bootstrap composition — all receive the installed
task.

### Evidence

`evidence/claim-363241/`. **`PUBLISHED-BYTES.txt` is the one to read first**:
the installed task this pool was configured with, then the actual file at
`task.json` for two distinct Jobs served by ONE worker object — mode, byte
count, `human_contract` artifact and published instructions for each — and
then a Job with no own task receiving the installed bytes.

- **`tests.tools.test_job_task_delivery`**: **43 cases, OK**, new this claim.
  It drives `_published_task` and `_proved_task` over real directories, not
  assertions around them: two Jobs on one worker each publishing their own
  file, no bytes crossing and the shared configuration unchanged, two
  distinct consistent identities, the implementation and review roles
  delivered the SAME task for one Job, restart proving what was published at
  0444, and refused before launch for another Job's task, a tampered file, a
  missing file and publishing over an existing one — plus `job_task_reader`
  over a real `JobStore`.
- **`tests.tools.test_creation_ports`**: **28 cases, OK**. One case changed:
  the R3 diagnostic that asserted `task_bytes=worker.given["task_bytes"]`
  recorded the defect and is now the assertion that it is gone.
- **`tests.job_manager.test_creation`**: **76 OK**, unchanged.
- **Whole `tests/job_manager`**: **1375 OK**, unchanged.
- **Five tools suites** (`test_stage_execution`, `test_single_worker`,
  `test_bootstrap`, `test_creation_ports`, `test_job_task_delivery`): 926
  cases, 1 failure and 17 errors — **all 18 pre-existing and byte-identical
  to the base**. The three suites this Work touches contribute none.

### What this child does not claim

No container is run over the published root. The worker is composed the way
`test_single_worker.ThreeWorkersOneJobThreeImages` composes one, because
`_for_job`, `_published_task` and `_proved_task` read the held configuration
and their operands and nothing else. So this proves the bytes that reach the
input root, the identity that accompanies them, the isolation between two Jobs
on one worker and the restart and refusal behaviour — and it does not run a
provider over them.

The connected implementation/review/correction/held rehearsal, the OBS-0
interval, `NewJobBinding.create_binding` against an installed instance and
interruption inside `bootstrap.prepare` remain the PARENT W361912's, which the
review states explicitly. No figure for OBS-0 is offered and none should be
inferred from the suite timings in the evidence, which are harness wall time.

### Cost

Read-only re-reading of `single_worker._input`/`_claimed`/`_published_task`/
`_proved_task`/`worker_operations`, `stage_execution.prepare_context` and the
per-worker composition at 6656, and `test_single_worker`'s own worker harness.
Test runs: the delivery suite six times (three failing — a `Column("json")`
row member I seeded with non-JSON text, a refusal code I guessed as `digest`
where `_proved_task` answers `precondition`, and its message naming "another
task document" rather than the file name), the ports suite three, the creation
suite twice, whole `tests/job_manager` twice, the five-suite tools run once at
~272s against the retained base list. No live provider, no engine, no total
manufactured.

### Boundaries

No Git operation of any kind, in the repository or in the scratch roots. The
canonical `v12/python` tree is byte-unchanged. `candidate-363069`,
`candidate-362931`, every parent candidate and every evidence directory are
preserved exactly; per the FINDING's split I wrote only `candidate-363241/`,
`evidence/claim-363241/` and this file, and the bound `FINDING.md`/`PLAN.md`
and the reviews are the reviewer's and are unmodified. No live provider,
engine, credential read, deployment, install, instance operation, migration or
cutover.

## claim363375 — one per-stage document, for every consumer

Answers `review-2026-10-26T20-28-59Z.md` under handoff363366. Base
`19f02ce1295b4517a85f0822d48754efc982f388`, unchanged; scoped status for
`v12/python` empty. All seventeen members of `candidate-363241` and its
manifest re-hashed at claim start and all eighteen match.

**My E363350 "blocker closed" claim was wrong and the review disproved it
properly.** I substituted the per-Job pair at `_claimed` and `_input` and
tested `_for_job` and the file helpers DIRECTLY — so the two production
boundaries in between were never exercised: `_matches` still compared the
installed manifest and refused the composed Job as "another bootstrap input",
and `_assignment_manifest` still minted against the installed digest while
`_input` published the per-Job one, which `compose_input_root` refuses as "two
halves of two deliveries" after `task.json` is already on disk. Both were
reproduced by the reviewer's own probe against those functions.

### The correction: one document, not two members

Candidate `candidate-363375/`, manifest
`09cb927ef787a7d59a62ff44fc56d35819d2db65d6a4ad4b02baa14ed91b71b0`,
17 members — 4 changed since
`candidate-363241` and 13 carried forward byte for
byte, with a `COUNTS` block in the manifest.

| path | candidate-363375 |
| --- | --- |
| `tests/tools/test_creation_ports.py` | `83c507131df51f8da158def10795c6d5712621a149a170d20e788dfd851d74da` |
| `tests/tools/test_job_task_delivery.py` | `69102aa32c7e000bc79d47e71e0afdbfbc0e2104d88e202242daa5fa1fbb6ff2` |
| `tools/single_worker.py` | `71586b8a5b26423d7742d5071d84d8f1aef7abb36ff63b50c0b587d8d1c65ffc` |
| `tools/stage_execution.py` | `835b0297e7ddc5aee5da84515735cce928b21f1ed8b085d2419cf747f6d421ef` |

`_for_job` answered a manifest and a task and left every caller to remember to
use both. **`_given_for(stage)` answers the whole held configuration** — the
installed `given` itself when the stage has no own task, a fresh copy
otherwise — and every stage-scoped operation in the class now begins
`given = self._given_for(stage)`:

- `_matches` — closes R1;
- `_prepared` — closes R2, because the assignment and the input root are now
  composed from one document;
- `start` — the recorded attempt names the runtime input actually delivered;
- `_job_execution` — the execution context carries the same digest;
- `_claimed` and `_input` — unchanged in effect, now reading the one document;
- `_adapter` gained a `stage=None` operand and the preparation caller passes
  it, so the OCI identity matches too.

There is nothing left to remember to substitute, which is the point: the
previous shape was correct at two call sites and wrong at five.

**The shared configuration is still never written to.** `_given_for` returns
`self.given` itself for a Job with no own task and a fresh `dict(...)`
otherwise, and a case asserts the installed `task_bytes` are unchanged after
two Jobs prepare.

**One product robustness fix.** `_given_for` reads the reader with `getattr`
rather than the attribute, because `test_single_worker`'s own harness composes
a worker through `__new__` to ask a preflight question without a store, port,
engine or credential provider — and a composition with no reader is the
installed delivery, which is what that harness is asking about.

### A real defect in my previous test file

The previous `test_job_task_delivery` subclassed
`ThreeWorkersOneJobThreeImages` for its helpers and therefore **re-ran that
class's own cases under four of my classes** — which is why its count was 43.
Worse, one of those borrowed cases composes a worker through `__new__` for a
preflight question, so it was asking a different question under this suite's
name. The helpers are now bound explicitly (`configured_as`, `held`,
`stage_for`, `job_for`, `worker_for`) and no borrowed assertion runs here. The
honest count is **26**, nine of them the new connected class.

### Evidence

`evidence/claim-363375/`, with both probe outputs kept side by side because
the difference between them is the whole correction.

- **Your `input_pair_probe.py`, run UNCHANGED**: `worker_matches` is now
  **true** — R1 closed with no change to the probe.
- **`PRODUCTION-SEQUENCE.stdout`**: the same two constructions with ONE line
  different, named in its header — the assignment minted from
  `_given_for(stage)` instead of `w.given`. `assignment_input_digest ==
  per_job_input_digest`, both different from `installed_input_digest`,
  `worker_matches` true, `input_succeeded` true,
  `root_manifest_is_the_per_job_one` true, `published_task_id` `job-first`.
  Your probe's remaining `input_succeeded: false` is the pair validator
  working — an installed assignment beside a per-Job root IS two halves of two
  deliveries, and a case asserts it must stay refused.
- **`tests.tools.test_job_task_delivery`**: **26 cases, OK**.
  `TheConnectedPreparationPath` drives what `_prepared` drives, in its order:
  one document, then the real `_matches`, the real `_assignment_manifest` and
  the real `_input` — which calls the real `compose_input_root`. Both ordinary
  roles; two Jobs on one worker with nothing crossing; a reopened preparation
  running the comparison branch and `_proved_task` over real material; the
  installed-assignment mismatch refused; tampered and missing refused with no
  launch; and a Job with no own task preparing the installed one through the
  same sequence.
- **Whole `tests/job_manager`**: **1375 OK**, unchanged.
- **Five tools suites including `test_single_worker`** — the suite that owns
  these functions: 909 cases, 1 failure and 17 errors, **all 18 pre-existing
  and byte-identical to the base**.

### What is still not delivered

- **The `_adapter` RECOVERY callers read the installed configuration.** Seven
  of its nine call sites hold roots and an attempt and no stage — 1850, 1978,
  2482, 2633, 2720, 2729, 2920 — and pass no stage, so they answer the
  installed document. That is correct for every Job with no own task and a
  real limitation for one that has. The fix I would reach for is to derive the
  delivered manifest from the root itself: `workspaces.read_input_root`
  already returns the pair the attempt was composed with, which is the
  authoritative record of what was delivered and needs no stage. I did not do
  it in this claim and I am not claiming it.
- **No container is started over the prepared root.** The sequence under test
  ends at the composed input root.
- The parent's obligations are unchanged: the connected
  implementation/review/correction/held rehearsal, the OBS-0 interval,
  `NewJobBinding.create_binding` against an installed instance and
  interruption inside `bootstrap.prepare`.

### Cost

Read-only mapping of every consumer the review named — `_matches`,
`_assignment_manifest`, `record_attempt`'s site in `start`, `_adapter`'s nine
call sites and `_job_execution` — plus `compose_input_root`'s pair rule. Test
runs: the delivery suite seven times (four failing: inherited test methods
from the borrowed base class, an `AttributeError` for a worker composed
without `__init__`, a `PermissionError` from `compose_input_root` freezing a
root my fixture then wrote beside, and a keyword-before-positional syntax
error from my own `_adapter` call edit), whole `tests/job_manager` twice, the
five-suite tools run once at ~270s against the retained base list, and both
probes twice. No live provider, no engine, no total manufactured.

### Boundaries

No Git operation of any kind. The canonical `v12/python` tree is
byte-unchanged. `candidate-363241`, `candidate-363069`, `candidate-362931` and
every evidence directory are preserved exactly; I wrote only
`candidate-363375/`, `evidence/claim-363375/` and this file. The bound
`FINDING.md`/`PLAN.md` and both reviews are the reviewer's and are unmodified
— your `input_pair_probe.py` was executed from where it sits, not copied or
edited. No live provider, engine, credential read, deployment, install,
instance operation, migration or cutover.

## claim363492 — the stage-less adapter carries the delivered identity

Answers the review at handoff E363482: "carry the same delivered attempt
identity through adapter identification/adoption/cleanup/recovery without
stage. If deriving from persisted root, validate pair against durable
attempt/assignment provenance; self-consistency alone is insufficient. Handle
partial/missing pre-publication roots truthfully, preserve legacy tasks and
shared-worker isolation."

### Base and inherited overlay, revalidated at claim start

Base commit `19f02ce1295b4517a85f0822d48754efc982f388`. `candidate-363492/` is
seeded from the reviewed `candidate-363375/` (manifest
`09cb927ef787a7d59a62ff44fc56d35819d2db65d6a4ad4b02baa14ed91b71b0`) and every
earlier candidate is preserved byte-untouched. A fresh base scratch root was
rebuilt from canonical bytes for this claim because the retained
`/tmp/w361912-base` had drifted — it discovered 34 fewer `tests/manager` cases
than canonical does and failed to load two modules — so no comparison below
uses it.

### What the correction is

`_adapter` took a `stage` and nothing else, so the seven callers that hold an
attempt and roots and no stage got the INSTALLED input manifest. That is not a
cosmetic default: `OciAdapter` carries `input_manifest_digest` into
`sealing.sealed_result` and the declared `outputs` into the collection, so a
per-Job attempt identified, adopted, cleaned up or recovered through any of
those callers would have been described — and sealed — with provenance naming
an input it was never given.

Three changes, and the third is what makes the second provable.

1. **`attempts.recorded_input_of(store, attempt_id)`** — a read and nothing
   else, over the column `record_attempt` already writes and
   `authorize_input_root` already proves a root against. It exists so a caller
   can tell "this attempt was recorded against the installed input" from "this
   attempt owns another one" BEFORE deciding whether a root must be read.
   Absence and a recorded `None` are both answers, for the reasons its
   docstring gives.
2. **`_adapter_manifest` and `_delivered_manifest` on `_SingleWorker`.** With
   a stage, the stage's document is used AND CHECKED against the recorded
   digest — because `refresh_runtime` is handed `{"attempt_id": ...}` with no
   `job_id`, and a stage-shaped operand with no Job would otherwise resolve the
   installed document silently, which is the same wrong answer by another
   route. Without a stage: an attempt recorded against the installed identity,
   or recording none, is answered the installed manifest with no root read at
   all; an attempt recorded against another identity is answered the manifest
   read back OFF DISK by `attempts.authorize_input_root`, which holds the pair
   to all four parts of the activated assignment, the runtime attempt id and
   the recorded input digest. A root that cannot be proved is a refusal, not a
   substitution — for that attempt there is no second source for what it was
   delivered.
3. **`operations_from` now wires `job_task=job_task_reader(job_store)`.** The
   production bootstrap composition reads the Job store for its execution
   context already; the per-Job task is the same store, read the same way.
   This is what makes the serving loop a real test bed for the delivery, and a
   Job carrying no task document is answered the installed one exactly as
   before.

The shared configuration is still never written to, and the worker's own
identity digests — image, profile, policy, adapter — still come from the
installed document in every path. The only per-attempt member is the input
manifest, which is the one thing that differs.

### Why the root rather than the Job

The reviewer offered the root as an option, not a design. I took it because an
attempt's roots are what the RUNTIME mounted, and asking the Job store again
would answer what the manager meant to deliver rather than what it did. The
reviewer's constraint is met by construction: the root is never read on its own
authority, only through `authorize_input_root`, so a complete and internally
consistent root composed for another attempt is refused rather than believed.
There is a case that builds exactly that root.

### Verification

Scratch roots `/tmp/w363066-492` (candidate) and `/tmp/w363066-base492`
(canonical base), each `v12/python` + `v12/worker` + `v12/DESIGN.md` + the v12
JSON files + `AGENTS.md` + the published vectors subtree, with the `v12`
directory level kept. `PYTHONPATH=src:.`

- **`tests.tools.test_job_task_delivery`: 33 cases, OK** — the inherited 26
  plus seven in `TheRuntimePathDeliversAndRecoversOneIdentity`, which drives
  the PRODUCTION bootstrap composition (`single_worker.operations_from`) over a
  real Job store, a real control store, the suite's deterministic `Engine` and
  the serving loop's own `reconcile`/`status`: offer, claim, `_prepared`,
  `_matches`, `_assignment_manifest`, `_input`, `record_attempt`, the launch
  adapter and a started container. The only substitution is the per-Job task
  READER on the composed worker, because a Job row carrying a `task_document`
  is written by `creation.create_template_job`, which needs an installed
  deployment and a Work binding this suite has neither of —
  `TheReaderOverARealStore` drives that reader against a real store. What the
  seven assert: the recorded attempt digest IS the delivered identity and the
  bytes at `/input/task.json` are the delivered task, with one engine launch;
  the stage-less `_adapter` describes the delivered manifest digest and the
  delivered outputs and NOT the installed digest; `refresh_runtime` — the
  caller with no `job_id` — identifies the running attempt and really asks the
  engine; a complete, internally valid installed pair substituted into the root
  is refused `integrity/digest` with no second launch, and `_naming` contains
  that refusal as `None` rather than raising into the retry loop; a root whose
  protocol document has been removed is refused rather than answered from the
  installed configuration; an attempt recorded against the installed input
  composes its adapter with the root already deleted; and a stage-shaped
  operand with no Job refuses, naming both digests.
- **Whole `tests/job_manager`: 1375 OK** — unchanged.
- **`test_single_worker` alone: 243 cases, 1 failure**, and the failing-name
  list is byte-identical to the same run on a base root
  (`test_a_real_observing_status_run_mutates_no_durable_state`).
- **Five tools suites** (`test_single_worker`, `test_stage_execution`,
  `test_bootstrap`, `test_creation_ports`, `test_job_task_delivery`): 916
  cases, 1 failure and 17 errors — the same 18 pre-existing names carried in
  every claim of this child, 17 of them in `test_bootstrap`, which installs
  instances and serves them.
- **Whole `tests/manager`** was run on both roots. The name-level diff is
  confined to engine- and daemon-dependent suites and repository-shape cases
  (`*_engine`, `test_worker_container`, `test_dependencies`, `test_frozen`);
  nothing in it names `attempts`, `single_worker`, an input manifest or an
  adapter. The base root available when that pair ran was the drifted one, so I
  state it as what it is: a check that found no regression in the modules I
  touched, not a byte-identical comparison.

### What is still not delivered

- **Two Jobs through ONE serving loop.** Two Jobs on one worker are proved at
  the preparation sequence and at `servable_workers`; the engine-driven cases
  run one Job, because this deployment's submission carries one.
- **A REVIEW-role serving loop.** `SingleWorkerCase`'s deployment is
  `launch_role: implementation`. Both ordinary roles are driven through the
  real `_given_for`/`_matches`/`_assignment_manifest`/`_input` sequence, and
  the adapter composition reads the same two operands for either role, but no
  review stage reaches a container here: a review attempt mounts an upstream
  frozen checkpoint, which needs a completed implementation attempt first.
- **Restart and adoption through the real restart entrypoint.** The published
  root is re-proved by `_proved_task` and by a reopened preparation; a crash
  between the start and the adoption, driven by the suite's own checkpoint
  machinery, is not run.
- The parent's obligations are unchanged: the connected implementation/review/
  correction/held rehearsal, the OBS-0 interval,
  `NewJobBinding.create_binding` against an installed instance, and
  interruption inside `bootstrap.prepare`.

### An observation, not part of this Work

The canonical `v12/python` working tree carries around forty untracked
`v12-w71917-*/` directories left behind by earlier test runs, several with a
repository directory inside. They are not mine and I have not touched them; a
permission-preserving copy of the tree fails on them, which is worth knowing
for anyone building a scratch root.

### Cost

One read-only mapping pass over `_adapter`'s nine call sites and their
enclosing methods — every stage-less one has an attempt id in scope — plus
`authorize_input_root`, `read_input_root`, `record_attempt`, `operations_from`
and `SingleWorkerCase`. Test runs: the delivery suite five times, four of them
failing (a dict-shaped `declared_outputs` compared as entries;
`refresh_runtime` reached through the delegation wrapper, which needs a whole
stage; a frozen root `shutil.rmtree` could not remove; and one assertion about
a refresh answer that carries only `execution_runtime`); `tests/job_manager`
once; the five-suite tools run once on the candidate and `test_single_worker`
twice for the base comparison; `tests/manager` once per root. No live provider,
no container engine, no deployment, no installed instance, no migration, no
cutover.

### Boundaries

No Git operation of any kind. The canonical `v12/python` tree is
byte-unchanged. Every earlier candidate and evidence directory is preserved
exactly; I wrote `candidate-363492/`, `evidence/claim-363492/` and this
section. The bound `FINDING.md`/`PLAN.md` and every review are the reviewer's
and are unmodified.

## claim363763 — the acceptance scenarios, and two corrections to my own claims

Answers `review-2026-10-26T21-26-14Z.md` (handoff E363761): finish the three
original acceptance scenarios, replace the overstated substitution case with a
genuinely self-consistent pair, remove the coverage claim for a class that does
not exist, and record the correction without rewriting old history.
`candidate-363763/` is seeded from `candidate-363492` (manifest
`ae177cee4772d8b31dbe28be0930614f8770bade7ce4f80299a3c928819241b1`, all 18
members re-hashed at claim start); earlier candidates are untouched.

### Correction 1 — the substituted root was HALF a substitution

The reviewer is right, and the overstatement was mine in three places: the case
docstring, the claim363492 PROGRESS section and that claim's
HOW-THESE-WERE-RUN. The case wrote `self.manifest` into `input.json` only, so
`assignment.json` still named the delivered manifest; `read_input_root`'s own
pair rule refuses that before any provenance question is reached. It was never
the complete internally valid pair I said it was. I have NOT edited the
claim363492 section or its evidence file — they stand as written, and this is
the correction.

What the candidate carries now is two cases instead of one:

- `test_an_attempt_whose_root_HALF_was_substituted_refuses` — the original
  mutation, kept and described as what it is, with the refusal now attributed
  to the pair rule by asking `read_input_root` directly and asserting its
  "two halves of two deliveries" sentence.
- `test_an_attempt_whose_WHOLE_root_was_substituted_refuses` — the case that
  needed writing. BOTH documents are replaced by one consistent installed
  delivery minted for THIS attempt and THIS assignment: the assignment
  manifest is rebuilt against the installed input digest the way
  `_assignment_manifest` builds one, and `check_input_pair` is called on the
  result inside the test, so if the fixture were malformed the case would fail
  rather than pass for the wrong reason. `read_input_root` then accepts the
  root, the activated assignment still agrees in all four parts and the
  runtime attempt id still agrees. The ONLY disagreement left is the durable
  record, and it is enough: `integrity/digest`, "not claimed against", no
  second launch, and `_naming` contains it as `None`.

### Correction 2 — a docstring claimed a class that was not there

The runtime class's docstring pointed at `TheStagelessAdapterOverBothRoles`
"below" for the review role. I wrote that class, found it needed a fake control
store to reach `authorize_input_root`, deleted it as a fixture measuring
itself, and left the reference. It is removed, and the docstring now points at
the open scenario instead of claiming coverage.

### Scenario 3 — crash/restart adoption: DELIVERED

`ARestartAdoptsTheDeliveredAttempt`, seven cases, reusing
`TheProductionCompositionIsRestartSafe`'s machinery: the production
composition dies inside the operation at a named checkpoint with no unwinding,
and a fresh `operations_from` over fresh store handles with a new incarnation
resumes it. Six crash points — `claimed`, `attempt`, `boundary`, `input`,
`manifest`, `credential` — and each asserts the restart machinery's own two
questions (ONE launch, ONE claimed offer) plus this Work's four: the attempt is
recorded against the delivered identity, the root on disk still carries the
delivered task, the stage-less adapter over the adopted roots describes the
delivered manifest, and `refresh_runtime` identifies the adopted runtime.

TWO THINGS I GOT WRONG HERE AND FIXED INSIDE THE CLAIM, both recorded because
they are the kind of fixture error that passes quietly:

- The first draft looped over crash points inside ONE test. `self.stores`
  re-opens one pair of store files under a new incarnation and the attempt id
  is derived from the stage, so after the first point the later points' work
  was already durably done and their crashes never fired: three subtests
  passed by not running. It is one point per case now, and the reason is in
  the code.
- The first draft also listed `prepared`, `launch` and `runtime` as crash
  points. A one-worker bootstrap serving loop does not take those branches, so
  those subtests asserted a crash that never happens. They are gone.

And the seventh case is a defect hunt that came back negative in a useful way.
`test_a_restart_that_would_deliver_another_task_publishes_nothing` crashes
after the root is published and restarts with a DIFFERENT rendering for the
same Job. I expected `_proved_task` to refuse out of `reconcile`; it does not
get that far. The Job declares the first rendering's input identity, so the
re-preparation is refused by `_matches` BEFORE any publication is attempted,
and the serving loop treats a worker that does not match as one that cannot
serve this stage: no exception, no durable preparation failure, nothing on
disk touched, nothing launched, the record unchanged. The case asserts that
state from the durable side and then asks `_matches` directly so it names the
mechanism. No product change: the outcome is safe, and the silence is the
pre-existing shape of "no servable worker".

### Scenario 1 — two Jobs through one loop: HALF DELIVERED, and why

`TwoRequestedJobsThroughOneServingLoop` serves one requested Job through the
real loop, drives the real in-image program (`baton_worker.serve_exchange`
with the scripted agent) to an answered terminal, ends it through the Worker
Manager's own ending via `sweep`, and asserts the delivered identity, the
published bytes, the stage-less adapter and that the second Job is never
delivered the first one's bytes.

It does NOT serve the second Job, and the two reasons are measured rather than
assumed:

1. `_matches` holds a stage's `work_id` to the one THIS worker's manifest
   declares. A second Job on another Work is never servable by this
   deployment at all — the first draft used `WORK_B` and the second stage sat
   `queued` for ever, which would have been a case asserting a fixture.
2. Two Jobs over ONE Work do not finish it either. The first ending passes the
   Work on to its `review_route` — the ending's own reported act — so the
   second stage reaches `offered` and its claim never completes. Measured over
   eight ticks in the case and thirty in a probe: `offered`, no recorded
   attempt, no roots, no second launch.

So the bootstrap single-worker deployment cannot express "two Jobs through one
loop": it is bound to one Work by its own manifest and single-capacity by
construction. That scenario lives in the POOL, and I located the harness for
it rather than leaving it as a direction: `tests.tools.test_stage_execution`'s
`ServingCase.serving()` composes `stage_execution.operations_from` with three
role workers, an `Engine` and `checkout=self.checkout` — the product's own
injected checkout seam, NO version control — and I confirmed it composes and
ticks. The next obstacle is exactly one thing: the pool's Jobs must declare
`job_input_identity` derived from each pool worker's own manifest (the default
`fixtures.submission()` digests do not match, so its stages stay `queued`).
A second implementation worker in the composed document is what makes two
Jobs concurrent rather than serial.

### Scenario 2 — the review-role runtime delivery: NOT DELIVERED

`single_worker.operations_from` calls `_held(document)` with
`roles=("implementation",)`, so the bootstrap composition REFUSES a
`launch_role: review` configuration outright (`policy/denied`). A review-role
runtime is therefore a pool composition, and a review attempt mounts an
upstream FROZEN CHECKPOINT behind `review_driver.prepare_review`.

The route exists without version control and I have it located:
`test_stage_execution`'s `sealed_review` fixture (around
`tests/tools/test_stage_execution.py:984`) reaches a real review attachment
through the accepted operations — `review_driver.prepare_implementation`, a
real publication, `freeze_checkpoint`, then `prepare_review` — with the port
and profile as injected seams. The harness that drives a review stage to a
started runtime end to end is `ComposedOneJobCase`, whose `setUp` runs
version-control `init`/`add`/`commit` in its fixture; my role contract forbids
mutating version-control operations anywhere, including a temporary fixture
repository, so I did not run it and did not build a case on it. That is the
exact external blocker and the exact checkpoint: either the pool-plus-
`sealed_review` route above is built up to a started review attempt, or an
owner allowance is needed for the version-controlled line fixture.

### Verification

Scratch root `/tmp/w363066-763` (candidate) built from canonical bytes at base
`19f02ce1` with `candidate-363763` overlaid, keeping the `v12` level;
`PYTHONPATH=src:.`

- **`tests.tools.test_job_task_delivery`: 46 cases, OK** — the inherited 33
  plus the whole-pair substitution, plus seven restart/adoption cases, plus
  the serving-loop case, plus the split half-pair case.
- The broader runs and the base comparison are in
  `evidence/claim-363763/`, produced by the commands in that directory's
  HOW-THESE-WERE-RUN.txt.

### Cost

Reading: `authorize_input_root`, `check_input_pair`/`_relate_input_pair`,
`_assignment_manifest`, `_held`'s role gate, `TheProductionCompositionIsRestart
Safe`, `TheAnsweredEndingRunsThroughTheRealOwners`, `ComposedOneJobCase`,
`ServingCase`, `StageComposition.mount` and the `sealed_review` fixture. Probes:
five, all read-only or over disposable stores — which checkpoints a bootstrap
loop reaches, why a second Job stays queued (twice), whether thirty ticks
change it, and whether the pool composes without version control. Test runs:
the delivery suite seven times (three failing: the inherited-subtest inertia,
the `WORK_B` stage that was never servable, and the drifted-restart refusal I
expected from the wrong owner), plus the broad runs recorded in the evidence
directory. No live provider, no container engine, no deployed instance, no
version-control operation of any kind.

### Boundaries

No Git operation of any kind, and no test fixture that performs one was run.
The canonical `v12/python` tree is byte-unchanged. Every earlier candidate and
evidence directory is preserved exactly, including the claim363492 section
above and its evidence, which this section corrects rather than edits. I wrote
`candidate-363763/`, `evidence/claim-363763/` and this section. The bound
`FINDING.md`/`PLAN.md` and every review are the reviewer's and are unmodified.

## claim363909 — both pool scenarios, over the non-version-controlled route

Answers `review-2026-10-26T21-5?Z` (handoff E363761 → E363900): finish the two
finite pool scenarios with correct per-Job identities and Work/role routing,
continue the identified non-VCS route, and report the restart limits exactly.
`candidate-363909/` is seeded from `candidate-363763`; earlier candidates are
untouched. No product byte changed in this claim either — the whole of it is
`tests/tools/test_job_task_delivery.py`.

### The route, measured before it was used

The pool's own serving loop cannot be driven by this implementer, and that is
now a measurement rather than a worry: with the process runners replaced by
ones that refuse any version-control invocation, the FIRST preparation tick of
`ServingCase.serving()` raises `git clone --no-hardlinks --no-local ...` —
the line materialization through the configured `git` checkpoint profile.

What the product supports instead is the PROFILE SEAM, which the review
pointed at: `create_line`, `prepare_implementation`, `freeze_checkpoint` and
`prepare_review` all take the checkpoint profile as an operand, and
`tests.job_manager.test_review_driver.Profile` is the deployment-configured
profile "with no VCS behind it" — its own docstring. Over that seam, the line,
the writer grant, the frozen checkpoint, the review attachment and both mounts
are the accepted operations against a real control store, composed by the real
`stage_execution.StageComposition` the serving loop composes.

`PoolDeliveryCase.setUp` installs the refusing runners for the life of every
case, so each case PROVES its own absence of version control. The guard is not
vacuous: a probe case calling `subprocess.run(["git", "--version"])` under it
fails with `this case spawned version control: git --version`. That negative
control was run once from the candidate root and is recorded in the evidence
directory; it is not part of the suite.

### Scenario 2 — the review-role runtime delivery: DELIVERED

`TheReviewRoleRuntimeIsDeliveredTheSameTask`, five cases. One real
implementation round grants a writer on a real line, publishes its input root
through the real `_input`, completes, and freezes a real checkpoint; the review
attempt is then prepared by the real `StageComposition`, which calls
`review_driver.prepare_review` against the line's current checkpoint and
composes the accepted `review_boundary` behind the attachment. What the cases
assert:

- the review attempt's own `/input/task.json` carries the JOB'S REQUESTED task
  bytes — not the review deployment's installed ones — and the manifest beside
  them is the REVIEW worker's own, with its own image digest and a human
  contract naming the delivered bytes;
- ONE JOB GIVES BOTH ROLES ONE JOB-SCOPED IDENTITY over two different runtime
  manifests, with an identical human contract, which is what lets a Job
  declare one `input_digest` for its stages;
- the mount is the attachment's: `review_cycles.review_for_attempt` reads back
  `active`, naming the checkpoint the upstream round really froze and this
  reviewer's participant, and the boundary's SOURCE PATH is the line's frozen
  checkout rather than the writable line the writer was granted — the
  different source path the review said a configuration-level both-role proof
  cannot reach;
- the stage-less adapter over the review attempt describes the DELIVERED
  manifest digest, so this Work's correction is now proved for the role it had
  never been asked for;
- and a Job with no own task is delivered the installed one through the same
  mount.

### Scenario 1 — two requested Jobs through one pool: DELIVERED

`TwoRequestedJobsThroughOnePool`, three cases. Two Jobs, two Works, two lines,
ONE control store, one storage, one workspace group, and ONE shared reader
table holding BOTH Jobs' tasks — which is what makes a crossed delivery
observable at all. Each attempt's root carries its own requested bytes, its own
input identity and its own stage-less adapter identity; the identities differ;
neither root contains the other Job's id anywhere; each Job is granted its own
line, read back through `review_cycles.writer_for_attempt` as `active` with the
composition's own writer id; and neither delivery mutates the shared held
configuration — the mapping, the serialized installed manifest and the
installed task bytes are unchanged after both, and each stage's served
document is a fresh object.

TWO WORKS IS THE PRODUCT'S RULE, not my convenience, and I found it by being
refused: `create_line` answers "this Authority and Work already own a line
under different immutable operands" for a second line on one Work, and a pool
worker's manifest declares the Work its stages belong to. So a pool serving two
Jobs is two deployments over one control store, which is what
`EachJobBindsItsOwnDeploymentAndLine` already says it is. The real `_matches`
is asked to admit each worker for its Job before the pair under test is
prepared, so neither pairing is one the serving loop would have rejected.

### The limits, stated exactly as asked

- **No runtime is STARTED in the pool cases.** The sequence driven is
  `_prepared`'s own — `_mounted` through the stage composition, the real
  `_assignment_manifest`, the real `_input` — and it stops where the launch
  document, the credential delivery and the runtime start would begin, because
  those need a minted Authority session this harness does not compose. The
  engine-driven start, the adopted launch context and the recovery entrypoints
  are covered for the implementation role by the two runtime classes in the
  same suite.
- **The six restart cases crash BEFORE any engine-start effect.** The points
  are `claimed`, `attempt`, `boundary`, `input`, `manifest` and `credential`;
  the one launch happens after all of them. No case claims recovery from a
  crash between the start vector and its record, and the class docstring now
  says so.
- **The upstream implementation attempt in the review scenario** has its
  four-part assignment identity and its completion axes written by the
  fixture, which is the owning suite's own device
  (`tests.job_manager.test_review_driver.DriverCase.attempt`). The input
  identity every assertion is held against is written by the product's own
  `attempts.record_attempt`, called the way `start` calls it.

### Verification

Scratch root `/tmp/w363066-909`, built from canonical bytes at base `19f02ce1`
with `candidate-363909` overlaid, `v12` level kept, `PYTHONPATH=src:.`

- **`tests.tools.test_job_task_delivery`: 54 cases, OK** — the inherited 46
  plus five review-role and three two-Job-pool cases.
- **Whole `tests/job_manager`: 1375 OK** — unchanged.
- **Five tools suites: 937 cases**, 1 failure and 17 errors, failing names
  byte-identical to the base root's list (that root re-verified byte-identical
  to canonical `src/` and `tools/` again before reuse).

### Cost

Reading: `StageComposition._prepare`/`mount`, `review_cycles.create_line`/
`line_of`/`writer_for_attempt`/`review_for_attempt`, `freeze_checkpoint`,
`record_attempt`, `activate_assignment`, `_held`'s role gate, `ServingCase`,
`ComposedLifecycleCase`, `DriverCase` and the `Profile`/`Port` seams. Probes:
four — whether the pool spawns version control (it does, at the first
preparation tick), whether the review-driver harness does (it does not: 14
cases pass under the guard), the shape of the real review preparation record,
and the negative control for the guard itself. Test runs: the delivery suite
nine times; six failing, each for a fixture reason I then named in the code —
a package import that is not re-exported, a deep copy the product's immutable
objects refuse, a `state` member only the RECOVERED record carries, the
adapter's engine and credential-home operands, and the second line on one Work
the product refuses. Plus the broad runs recorded in the evidence directory.
No live provider, no container engine, no deployed instance, no version-control
process.

### Boundaries

No Git operation of any kind. Every case added in this claim refuses to spawn
one and that refusal is itself verified. The canonical `v12/python` tree is
byte-unchanged; no product file changed in this claim. Every earlier candidate
and evidence directory is preserved exactly. I wrote `candidate-363909/`,
`evidence/claim-363909/` and this section. The bound `FINDING.md`/`PLAN.md` and
every review are the reviewer's and are unmodified.

## claim364051 — the pool serving loop, and the defect it found

Answers the review at handoff E364048: continue the runtime scenarios from the
pool seam the reviewer proved, do not seed activation/preparation/launch state,
and correct the completion language. `candidate-364051/` is seeded from
`candidate-363909`; earlier candidates are untouched.

### Correction first: my last headline was wrong

The claim363909 handoff said "BOTH remaining pool scenarios delivered". The
reviewer is right that this exceeded the boundary that claim's own PROGRESS
stated three paragraphs later: no runtime was STARTED in either pool scenario,
and the two Jobs were prepared through `_prepared`'s sequence rather than
driven by the loop. What was delivered there was mount and delivery evidence
over real driver operations — valuable, and preserved — not the runtime
scenarios. I have not edited that section; this is the correction, and the
language in this one is written to be checked against what the cases do.

### The reviewer's seam works, and it found a product defect

`stage_execution.operations_from` takes `checkpoint_profile`, the document
names the profile by name, and the fixture `Profile` has no version control
behind it — so the real pool can be composed and driven. Driving it over a Job
created by the real `creation.create_template_job` printed `queued` for
fourteen ticks, with the scheduler's own refusal every tick:

    no worker this deployment configures for the 'implementation' stage can
    serve Job 'job-pool-a': {'implementation-worker': ['the submitted
    input']}

**The cause.** `_with_job_task` returned the installed document whenever
`binding.get("job_id") is None` — and in a `/1` deployment document, the
ordinary one-Job pool and the shape the dogfood instance runs, the binding's
`job_id` IS `None` by construction. `binding_for`'s own docstring says so:
"THE ONE-JOB DOCUMENT BINDS EVERY JOB IT IS ASKED ABOUT." So a created Job's
own task never reached the pool's compatibility derivation, every configured
worker was excluded as disagreeing about the submitted input, and **the pool
path for a created Job was dead end to end** — while the bootstrap
single-worker path, which has no binding, worked. That is why five claims of
preparation-level evidence never caught it.

**The fix** is to drop the binding condition: which Job's task this is was
never the binding's fact. The caller reads it with
`job_task_reader(...)(job_id=stage["job_id"])` — the stage's own Job — and
`_job_workers` has already refused a stage whose Job this deployment does not
bind. The binding answers where a Job's line, base and target come from; it
does not answer whether the Job exists. One product file changed in this
claim: `tools/stage_execution.py`.

### What the loop now proves

`TheCreatedJobRunsThroughThePoolServingLoop`, three cases. The Job is created
by the real operation — template resolved, per-Job task derived, submission
admitted, `template_jobs` row written — and then `reconcile` and `sweep` do
everything: offer, claim, allocation, line grant, publication, start. Nothing
in the class writes an offer, a claim, an attempt, an activation, a
preparation or a launch.

- the created Job's OWN requested task reaches a STARTED runtime: the bytes at
  `/input/task.json` are that Job's composed document, one container is
  created and activated, the attempt is recorded against the delivered
  manifest digest and not the installed one, and the Job-scoped identity is
  the one the Job declared;
- the stage-less adapter over that pool attempt describes the delivered
  input, so this Work's recovery correction holds on the pool path too;
- a Job with no own task is served the installed one through the same loop and
  the same fixed function.

`TwoCreatedJobsRunThroughOnePoolServingLoop`, four cases. Two created Jobs,
each with its own requested task, Work, line and producer, bound by a `/2`
document, driven by ONE loop over one Job store and one control store. Each
input root carries its own task document and its own instructions; neither
carries a word of the other's; both attempts are recorded against their own
distinct identities; each Job's writer grant names its own line, read back
through `review_cycles.writer_for_attempt`; and the scheduler's allocation
names each Job's own producer.

### What is still not proved, exactly

- **The second Job's runtime does not start, and the reason is the fixture.**
  Every engine double in this repository models ONE container: `Engine` mints
  `runtime-single-1` for every launch, and `ComposedOneJobCase.quiescing` --
  borrowed here, and the repository's own correction for one lifecycle's
  successive containers -- mints a fresh identity per launch but still answers
  one listing row. So the second CONCURRENT attempt is shown the first
  attempt's container and the manager refuses to adopt it: "one delivery
  carries one identity". That refusal is correct product behaviour. The case
  asserts what the loop durably recorded instead — a start failure, no runtime
  attached, an uncertain runtime axis for the second attempt, and the first
  attempt still running. The missing capability is a deterministic double that
  models two live containers.
- **The review-role runtime is still not driven through the loop.** A review
  stage opens only when its implementation stage completes, which needs the
  in-image worker turn, the freeze, the publication and the intake. The review
  MOUNT, its upstream frozen checkpoint, its attachment, its delivered task
  and its stage-less adapter are proved over the accepted driver operations by
  `TheReviewRoleRuntimeIsDeliveredTheSameTask` from the previous claim; what is
  missing is that same delivery reached through `sweep`. The harness for it is
  `TheComposedJobTraversesReviewAndAcceptance`'s, and with the profile seam the
  line half of it needs no version control; the worker turn is
  `baton_worker.serve_exchange` with a scripted agent, as in
  `TwoRequestedJobsThroughOneServingLoop.answered`.

### Verification

Scratch root `/tmp/w363066-051`, base `19f02ce1`, `v12` level kept,
`PYTHONPATH=src:.`

- **`tests.tools.test_job_task_delivery`: 61 cases, OK** (54 inherited + 7).
- **Whole `tests/job_manager`: 1375 OK** — unchanged.
- **Five tools suites: 944 cases**, 1 failure and 17 errors, failing names
  byte-identical to the base root's list; `test_stage_execution` is in that
  run, so the product change is covered by its owning suite.

### Cost

Reading: `_with_job_task`, `_served_deployment`, `_disagreements`,
`_job_workers`, `servable_workers`, `line_for`/`binding_for`/`works_for`,
`unconfigured_work`, `creation`'s derivation interface, `FakeDerivation`/
`FakeBinding`/`FakeOwnership`/`FakeOperations`, `ServingCase`,
`EachJobBindsItsOwnDeploymentAndLine`'s two-Job document, and both engine
doubles. Probes: six — the pool loop with a hand-submitted Job, the same with
a created Job (which found the defect), the scheduler's own refusal text, the
pool generation and `unconfigured_work`, the second attempt's launch refusal,
and whether the second Job's root is published before it. Test runs: the
delivery suite eleven times; seven failing, each for a reason now recorded in
the code — the ports' instance identity, the missing `work_id` in the derived
selection, `_task_agrees` on a derivation that answered the installed digest,
an inherited test class, the `/2` document's member set, an unauthorized route
for the second producer, and two assertions about state the projection does not
carry. No live provider, no container engine, no deployed instance, no
version-control process.

### Boundaries

No Git operation of any kind; every pool case refuses to spawn one. The
canonical `v12/python` tree is byte-unchanged. Every earlier candidate and
evidence directory is preserved exactly, including the claim363909 section this
one corrects rather than edits. I wrote `candidate-364051/`,
`evidence/claim-364051/` and this section. The bound `FINDING.md`/`PLAN.md` and
every review are the reviewer's and are unmodified.

## claim364233 — the concurrent regression, and where the review stage stops

Answers the review at handoff E364228: incorporate the concurrent success
regression, append the correction of my fixture claim, preserve the
wrong-runtime refusal separately, and finish the review-runtime milestone.
`candidate-364233/` is seeded from `candidate-364051`; earlier candidates are
untouched. No product byte changed in this claim.

### Correction — my "no multi-container fixture" claim was false

claim364051 said "every engine double in this repository models ONE
container" and reported the second Job's start as blocked by that. The
reviewer disproved it in one line:
`tests/tools/test_stage_execution._ConcurrentEngine` is "one observable OCI
process boundary holding SEVERAL containers", written for exactly this fact,
and calling my own `both()` with it starts both Jobs. I had read two doubles —
`test_single_worker.Engine` and `ComposedOneJobCase.quiescing` — found that
neither modelled simultaneous containers, and generalized from them to the
whole repository without searching for a third. That is the error, and it is
the second time in this child I have reported a fixture limit that was really
an unsearched one.

### Scenario 1 — the concurrent success is now the regression

`TwoCreatedJobsRunThroughOnePoolServingLoop` takes the engine as an operand:

- `test_both_jobs_reach_their_own_started_runtime` uses `_ConcurrentEngine`.
  Both created Jobs reach `waiting` through ONE loop over one Job store; the
  engine composes TWO containers with distinct identities; each attempt is
  attached to its own; each started runtime's input root equals
  `creation.job_task_of(jobs, job_id)` — the Job store's own answer, so the
  bytes on disk are held against the created Job rather than a value the case
  recomposed.
- `test_the_single_container_engine_refuses_the_second_delivery` keeps the
  earlier behaviour under the single-container double, because what it
  measures is the manager declining to adopt a runtime labelled for another
  attempt, and both roots are still published with their own task — which is
  what makes it a launch-identity case and not a delivery one.

### Scenario 2 — the review runtime: where it stops, and why

Driven as far as it goes and recorded verbatim in
`evidence/claim-364233/REVIEW-STAGE-PROBE.txt`:

1. the created Job's implementation stage reaches `waiting` with its own
   requested task published and a container started;
2. the real `baton_worker.serve_exchange` turn over the MOUNTED roots returns
   0. Those roots are the composition's own, and getting them from the
   composition mattered: in the pool an implementation attempt's workspace is
   the LINE CHECKOUT, not `<storage>/<attempt>/workspace`. My first probe
   derived the paths and the ending deferred with "this assignment is
   completed and published no 'output.json'" — the agent had written the
   envelope into a directory nothing mounts;
3. the stage reaches `answering`, and the ending then DEFERS every tick with
   the publication's own refusal:

       the frozen result carries 0 git-change-proposal outputs; publication
       needs exactly one

   so the review stage stays `blocked`, because a review stage opens only
   after its implementation result is PUBLISHED.

**The exact missing capability.** `ServingCase`'s manifest — the one this pool
composes — declares exactly one output: `proposal`, of type
`directory-result`, at `workspace/output`. Nothing written under that
declaration can be a `git-change-proposal`. The harness that publishes one is
`ComposedOneJobCase`, whose manifest declares the proposal and whose line is a
real version-controlled checkout: the proposal IS a patch and a bundle
produced by version control inside the line, and its `setUp` runs
version-control `init`/`add`/`commit`. I may not perform version-control
mutations, so I did not run it and did not build on it.

Two supported ways out, neither mine to choose: an owner allowance to run the
version-controlled line fixture, or a publication seam for the pool like
`ComposedLifecycleCase`'s injected `Publisher` — which exists at
`stage_execution.Publication` but is not reachable through
`stage_execution.operations_from`, so the pool composes its publisher
internally today. A third possibility I did not pursue, because it would be
asserting fabricated artifacts as a published proposal: compose a second
manifest declaring a `git-change-proposal` output, write patch and bundle
bytes into the line, and let the freeze carry them.

What this milestone HAS, short of the loop: the review mount, its upstream
frozen checkpoint, its attachment, its delivered requested task, its distinct
source path and its stage-less adapter identity are all proved over the
accepted driver operations by `TheReviewRoleRuntimeIsDeliveredTheSameTask`
(claim363909), and that evidence stands.

### Verification

Scratch root `/tmp/w363066-233`, base `19f02ce1`, `PYTHONPATH=src:.`

- **`tests.tools.test_job_task_delivery`: 62 cases, OK.**
- **Whole `tests/job_manager`: 1375 OK.**
- **Five tools suites: 945 cases**, 1 failure and 17 errors, failing names
  byte-identical to the base root's list.

### Cost

Reading: `_ConcurrentEngine`, `ComposedOneJobCase.turn`/`mounted_view`/
`job_execution_for`/`implemented`, `launch.adopt`'s canonical comparison, the
pool manifest's declared outputs, and `ComposedLifecycleCase`'s publication
seam. Probes: five on the review stage — the adoption refusal from an
installed-digest context, the deferral naming the missing `output.json`, the
same with the mounted roots, the publication's change-proposal refusal, and
the manifest's output declaration. Test runs: the delivery suite three times,
all passing after the engine operand was threaded. No live provider, no
container engine, no deployed instance, no version-control process.

### Boundaries

No Git operation of any kind; every pool case refuses to spawn one and the
guard is verified. The canonical `v12/python` tree is byte-unchanged and no
product file changed in this claim. Every earlier candidate and evidence
directory is preserved exactly, including the claim364051 section whose
fixture claim this one corrects rather than edits. I wrote
`candidate-364233/`, `evidence/claim-364233/` and this section. The bound
`FINDING.md`/`PLAN.md` and every review are the reviewer's and are unmodified.

## claim364329 — the review runtime, through the loop

Answers the review at handoff E364325: choose and implement a bounded
deterministic output/publication fixture composition, label synthetic inputs
honestly, and finish the actual review runtime through the loop.
`candidate-364329/` is seeded from `candidate-364233`; earlier candidates are
untouched. No product byte changed in this claim.

You were right that this was not an owner gate. The publication's operands are
a fixture composition, the repository already shows the technique
(`ComposedLifecycleCase.frozen`), and nothing about it needs version control.

### The milestone, delivered

`TheReviewStageRunsThroughThePoolServingLoop`, three cases, one chain driven by
`reconcile` and `sweep` with one real in-image worker turn in the middle. No
offer, claim, activation, preparation or launch is written by the fixture; the
states it waits for are the projection's own.

1. a Job created by the real `creation.create_template_job`;
2. the pool's loop offers, claims, prepares, publishes its requested task and
   starts its implementation runtime;
3. one real `baton_worker.serve_exchange` turn over the MOUNTED roots;
4. the real ending — seal, intake, retention, `retain_proposal`,
   `publish_candidate`, `freeze_checkpoint` — and the implementation stage
   reaches `completed`;
5. the loop reaches the REVIEW stage, grants its attachment over that frozen
   checkpoint, publishes the Job's requested task into the review attempt's
   own input root, and STARTS its runtime: `review: waiting`.

What the cases assert: the projection is exactly
`{implementation: completed, review: waiting}`; the review attempt's
`/input/task.json` equals `creation.job_task_of(jobs, job_id)` and is not the
installed task; a second container was started with its own identity; the
review attempt is recorded against the REVIEW worker's own per-Job manifest
digest, which differs from that worker's installed one; its Job-scoped identity
is the one the Job declared and the same one the implementation stage was
served under; the manager's own launch CONTEXT carries that identity, proved by
`launch.adopt` accepting it (adoption compares canonical bytes, so anything
else refuses); the stage-less ADAPTER over the review roots describes it; and
the attachment read back through `review_cycles.review_for_attempt` is
`active`, names this reviewer's participant and the line's CURRENT checkpoint —
the one the round froze — with the mount's source being that checkpoint's
checkout rather than the writable line the producer was granted.

### What is synthetic, and why the rule is not bypassed

A real producer's proposal is a patch and an object bundle that version control
wrote in the line, and its claim names the base it was taken from. This
fixture's agent writes `objects.bundle` with fixed bytes and answers a claim
naming the configured canonical target as its base and a fixed head. Those
bytes are NOT a change proposal anybody could apply, and nothing here claims a
live proposal or an owner receipt. The manifest declares the three outputs
`ComposedOneJobCase` declares — proposal/findings/logs, each at its own name,
none required, the proposal typed `git-change-proposal` — with the human
contract untouched, so `single_worker._held` still proves the installed task
document against it.

The product validated both drafts before this one: without a
`git-change-proposal` output, "the frozen result carries 0 git-change-proposal
outputs; publication needs exactly one"; with one but no bundle, "the worker
names its object transport at 'objects.bundle' and the frozen content manifest
measured nothing there". Both had to be satisfied rather than skipped, which is
how this fixture knows it is not bypassing validation.

### Two fixture errors of mine, recorded

- The roots for the worker turn must come from the COMPOSITION. In the pool an
  implementation attempt's workspace is the LINE CHECKOUT, not
  `<storage>/<attempt>/workspace`; my first turn wrote the completion envelope
  into a directory nothing mounts and the ending deferred with "published no
  'output.json'".
- `ScriptedAgent.work` answers a DOCUMENT (`disposition`, `outputs`, `recap`),
  not a list. Iterating it as a list made the agent raise and the attempt
  ended `faulted` with `fault_code: agent`.

### Verification

Scratch root `/tmp/w363066-329`, base `19f02ce1`, `PYTHONPATH=src:.`

- **`tests.tools.test_job_task_delivery`: 65 cases, OK** (62 inherited + 3).
- **Whole `tests/job_manager`: 1375 OK.**
- **Five tools suites: 948 cases**, 1 failure and 17 errors, failing names
  byte-identical to the base root's list.

### Cost

Reading: `baton_worker`'s output-answer validation and its frozen-rule
checker, `scripted_agent`, `claude_agent`'s claim namespace,
`ComposedOneJobCase`'s manifest composition and `turn`, `Publication`,
`publication_for`, and `ComposedLifecycleCase.frozen`. Probes: six on the
ending — the missing `output.json`, the missing proposal type, the agent fault
from the answer shape, the validator-digest noise from the `oneOf` branch, the
missing object transport, and the final pass. Test runs: the review class four
times, the delivery suite twice, plus the broad runs in the evidence
directory. No live provider, no container engine, no deployed instance, no
version-control process.

### Boundaries

No Git operation of any kind; every pool case refuses to spawn one. The
canonical `v12/python` tree is byte-unchanged and no product file changed in
this claim. Every earlier candidate and evidence directory is preserved
exactly. I wrote `candidate-364329/`, `evidence/claim-364329/` and this
section. The bound `FINDING.md`/`PLAN.md` and every review are the reviewer's
and are unmodified.
