# Progress — W202663 (writer: `baton.claude`, role `impl`)

Append-only. Each entry is the state at the end of one claim episode.

## claim202665 — dossier pinned, images built, pool composed

**Step 1 — the decision is pinned.** `FINDING.md` quotes the owner's canonical
message verbatim and resolves each clause into a boundary. The dossier is bound
to `W202663` at `work/records/2026/09/finding-v12-initial-claude-worker-pool`.

Everything below is recorded as it happens; unfinished steps are named as
unfinished rather than summarized as progress.

**Steps 2 and 3 — both images built, verified and provenanced.**
`PROVENANCE-202663.json` carries the whole account. Provider
`sha256:9ff3322f…` through the supported normalizing path; integration
`sha256:b9b75acc…` on that exact digest through the engine directly, because
`tools.worker_image` cannot drive a recipe whose `FROM` is `${PROVIDER_BASE}`
and passes no `--build-arg` — recorded as a limitation rather than worked
around. Every COPYed module is byte-identical to this tree, measured inside a
container rather than asserted from the recipe. The provider image answers
Python 3.13.5, Node v22.23.2, Claude Code 2.1.247, uid 65532, and carries no
`scripted_agent.py`.

**D1 — the accepted W198667 recipe change could not build, and I corrected it.**
`v12/.dockerignore` is an allowlist and was never widened for
`attempt_log_format.py`, so every build of either supported image failed at that
`COPY`. Measured with a two-line probe recipe over the real context before any
production build was attempted. The correction re-includes the ONE file. This
is a file W198667 owned and the change is flagged for the reviewer rather than
presented as uncontested.

**Step 4 — BLOCKED, and the block is measured, not suspected.** D2 in
`FINDING.md`: a Job names one `input_digest`, a worker's `image_digest` must
equal its own manifest's `worker_image_digest`, and `run_vector` ends at the
image with no program operand — so one Job's pool is one image with one
entrypoint, and the two supported recipes are two images with two entrypoints.
`probe-one-image-per-job-202663.py` asks the real validators on a real composed
document: the control is accepted and both pairings refuse with "the bootstrap
input manifest names another worker image".

I did not route around it. Configuring all three roles on the provider image
would put `dogfood_entry.py` on the integration stage — a pool that starts and
does the wrong work, which is worse than one that refuses. A dispatching
production entrypoint is a new recipe and a new entry: product design, adjacent
to the worker-add interface the owner excluded, and an owner selection.

**Step 5 — not started.** It is gated on step 4. No deterministic Job was run,
no lifecycle was proven, and no logs from one exist. Said plainly rather than
softened.

**What was NOT done, by rule.** No live-model execution and no credential was
read, staged or exercised. No Git mutation of any kind. No worker-add interface.
No prior instance was started, changed or reused — `2026-09-17T20-29-21Z` was
read only, which is how its own latent two-image configuration was observed.

**Verification spending, this claim.** Two image builds (provider via the
normalizing path, integration direct) plus one two-line context probe build;
four short container runs to measure contents; one read-only validator probe.
No test suite was run — nothing in this claim changed product Python. The
`.dockerignore` correction is covered by the probe build that failed before it
and succeeded after it. Measured wall-clock was not recorded per command and is
marked unknown rather than reconstructed.

## claim206704 — the ruling pinned, the coupling corrected, the migration unfinished

**Step 4 done.** The owner's ruling of 2026-09-18T22:01:51Z is pinned in
`FINDING.md` verbatim, with my own D2 conclusion explicitly marked superseded,
and `PLAN.md` is rewritten around it. Both before any implementation, as the
ruling required.

**The revalidation found the ruling is right on the code's own evidence.**
`worker_manager/launch.py:137` has always carried `job_input_digest` and
`runtime_input_digest` as two members, and its comment rules that requiring
them equal "would refuse the ordinary case". The architecture is
provider-diverse; three comparisons had simply not been told. D2 reported one
image per Job as a property of the design and that was wrong.

**Step 5, the correction, is written and coherent.** A Job's `input_digest`
names the Job-scoped PROJECTION of a worker's input manifest; each worker keeps
its own full `manifest_digest` as its runtime identity. Nothing is added to the
manifest document and no frozen schema asset moves, so no built image is
invalidated and no worker changes.

| site | what it now compares |
| --- | --- |
| `contracts/manifest.py` | new `JOB_INPUT_EXCLUDED` + `job_input_identity()`; the excluded tuple is the contract and exists once |
| `single_worker._matches` | the Job's `input_digest` against the projection |
| `single_worker._claim` | the OFFER's `input_digest` — minted by `delegation.admit` from "the Job's immutable input identities" — against the projection |
| `stage_execution._correspondent` | the producer's Job input identity, not its whole manifest digest |
| `stage_execution` worker compatibility | the projection; this is the rule that silently excluded every heterogeneous worker before anything could refuse out loud |
| `integration/admission` | re-reads the producing worker's retained manifest and compares its projection; an unretained one refuses |
| `integration/driver.REQUIRED_TESTS_MEMBERS` | widened by `job_input_identity`, so the selection can state both identities |

`single_worker.py:267` — a worker's image against its OWN manifest — is
deliberately untouched, and it is what keeps "each worker selects its own
image" from becoming "any worker may run any image". So are `record_attempt`,
`output.py`, `provider_context.py` and `review_cycles.py`, which are the
per-attempt input, image and provenance validation and the recovery
attribution the ruling requires preserved.

**Verification, measured, with the regressions stated rather than softened.**

| suite | before | after |
| --- | --- | --- |
| `tests.tools.test_single_worker` | 153 OK | **153 OK** |
| `test_stage_execution` + `test_managed_integration` + `test_integration_worker` + `test_lifecycle_composition` | 348 tests, 13 errors, 0 failures | 348 tests, **20 errors, 2 failures** |
| `tests.integration.test_driver` + `tests.integration.test_execution` | **not measured** | 175 tests, 11 errors |

The middle row is a REGRESSION of +7 errors and +2 failures and I am not
calling it anything else. The bottom row's baseline is unknown: I did not
measure it before changing those files, and I am not reconstructing a number I
did not take. One of the 13 baseline errors is
`test_managed_integration`'s `ModuleNotFoundError: integration_placement`, an
import-path fault that predates this claim and is unrelated to it.

**Why they fail, exactly.** Every remaining failure is a TEST DOUBLE that
composes a Job's `input_digest` as the producing worker's whole
`manifest_digest`, or hands `admission` a fake manager that cannot answer
`load_manifest`. That is the compatibility consequence this correction has by
construction, documented in `FINDING.md`. It is fixture migration, not an
unresolved product question — but it is unfinished, and an unfinished migration
is a failing tree.

**Migrated so far:** `test_single_worker` (2 job compositions),
`test_stage_execution` (7 compositions plus the required-tests expectation),
`test_driver` (`requirements()` helper, `ProducerCase` submission),
`test_execution` (a real retained manifest behind the proposal digest).

**Still to migrate, by name:** the `tests.integration.test_reconciliation`
doubles that pass a `SimpleNamespace` manager into `admit_candidate`; the
remaining `test_stage_execution` doubles that construct a `required_tests`
selection without `job_input_identity`; and `tools/dogfood_operator.py:1210`
and `:1221`, which are PRODUCT composers still naming `manifest_digest` as a
Job's input digest and must be corrected before any real deployment is composed.

**Reversal probe.** With the three comparisons textually reversed
(`/tmp/w202663-toggle.py off`) and the fixtures at their old values,
`test_single_worker` is 153 OK and the D2 refusal reproduces — so the corrected
comparisons are load-bearing rather than inert.

**Steps 6, 7, 8, 9 not started.** No heterogeneous-image execution proof, no
mismatch-refusal case, no pool composition, no deterministic Job, no logs, and
`COMMANDS-202663.md` part 2 is still the template review206578 correctly
refused to accept as a deliverable. Step 3a — the complete copied-input
provenance including `source_profiles` — is also still open.

**Boundaries kept.** No live model, no credential read, no Git operation of any
kind, no worker-add interface, no prior instance touched, no frozen schema
asset or image changed.

**Spending this claim.** Roughly twelve focused suite runs across seven suites
(the largest ~105s for 676 tests), one baseline run with the correction
reversed, and no container, image build or engine execution. Per-command
wall-clock was not recorded and is marked unknown rather than reconstructed.

## claim206923 — review206898 answered; the contract is now a classification

**R1 — my handoff was wrong and the reviewer was right.** I called
`dogfood_operator.py:1210` and `:1221` product Job composers because of a field
name. Verified against the tree: line 1221 is `record_attempt` with the
delivered manifest's own digest, and `attempts.authorize_input_root` compares
that recorded digest to the manifest found in the input root — converting it
would refuse every runtime start and destroy the per-attempt runtime
attribution the owner ruling requires preserved. Line 1210 is a standalone
offer inside `run_dogfood_task`, which imports neither `single_worker` nor
`claimed_offers_for`, so it can never reach the Job-scoped comparison; its
digest is folded into a claim intent digest compared only against itself.
**Both are correctly left unchanged, and that remaining-scope item is
withdrawn.** The full six-identity trace is
`INVENTORY-input-digest-206923.md`.

**R2 — the projection was under-specified, and the reviewer's measurement is
reproduced.** Changing only `manifest_id`, `created_at` or
`role_instructions_digest` moved the shared identity too, so three
independently composed manifests could never have agreed and only three clones
would have. `JOB_INPUT_EXCLUDED` is now an explicit classification of EVERY
member, with the reason each one is on its side written at the tuple:

- projected out — `worker_image_digest`, `toolchain_digest`,
  `runtime_profile_digest`, `credential_policy_digest`,
  `role_instructions_digest`, `manifest_id`, `created_at`, `manifest_digest`;
- still compared, whole — `work_ref`, `human_contract`, `sources`, `outputs`,
  `record_binding`, `policy_digest`, the resource/network/mount/tool/retention
  bounds, `extensions`, `schema`, `version`, `assignment_contract`.

The shared policy digests are deliberately NOT dropped; only the credential
profile leaves, because the ruling names it separate. Role instructions leave
because an implementer and a reviewer are told different things and the ruling
makes role separate.

**R3 — compatibility is now an explicit, diagnosable rule.** `_matches`
distinguishes a Job naming the whole runtime manifest digest — the pre-W202663
identity — from a Job about someone else's input, and says which digest it
named, what a Job names now, and that the retained submission is evidence and
is not rewritten for it. Fail-closed, never silent, no provenance rewritten.

**A seventh consumer surfaced and its PREMISE was corrected, not its rule.**
`reconciliation._accepted_digests` justified reading the producer's proposal by
"admission refuses unless the producer's proposal and the owning Job agree" —
an equality this correction removes. The rule is right and untouched (a derived
publication carries the producer's runtime identity, and `_custody_basis` binds
the same value); its docstring now records that correspondence replaced
equality, so no later reader acts on the old sentence.

**New tests.**
`tests/manager/test_manifest_rules.TheJobInputIdentityIsAClassification` — 8
cases fixing the classification, including a positive built from three
INDEPENDENTLY composed manifests with their own ids, timestamps, images,
toolchains, profiles, credential policies and role instructions (not clones),
and the operand-ownership and hostile-`__getitem__` cases this surface has
already paid for once.
`tests/tools/test_single_worker.ThreeWorkersOneJobThreeImages` — 5 cases at the
LAUNCH boundary: three roles on three images all matched for one Job; a worker
whose image is not its own manifest's still refused; a worker that moved a
shared member still refused; the legacy Job told what it named; and the two
refusals proven to read differently.

**Verification, measured.**

| suite | before this claim | now |
| --- | --- | --- |
| `test_single_worker` | 153 OK | **158 OK** (5 new) |
| `test_manifest_rules` | 46 OK | **54 OK** (8 new) |
| `test_claude_context` | failing | **34 OK** |
| `test_driver` + `test_execution` + `test_reconciliation` | 11 errors + 57 errors | **266 OK** |
| `job_manager` (879) | — | **OK** |
| `test_stage_execution` + `test_managed_integration` + `test_integration_worker` + `test_lifecycle_composition` | 13 errors (pre-change baseline), 20 errors + 2 failures (claim206704) | **20 errors, 0 failures** |

**The 20 remaining errors, classified.** 8 `'object' has no attribute
'proposal'`, 4 `'types.SimpleNamespace' has no attribute 'reconciles'`, 1
`ModuleNotFoundError: integration_placement`, and the rest sharing those
tracebacks. All are test doubles missing an attribute; none is a digest
refusal. `AFreshPortReentersANeverStartedDelivery` was measured with my
`_correspondent` change reversed and errors identically (4 either way), so that
group is not mine. **I could not cleanly attribute the 13→20 delta without a
simultaneous revert of product and fixtures, which I did not perform, so I am
not claiming all 20 are pre-existing.** The two FAILURES from claim206704 are
resolved.

`test_dependencies` (57 failures) and `test_worker_image` (5) were checked and
are pre-existing: neither imports any module this claim changed.

**Still open.** Step 6's integration half — the review asks for actual
integration as well as launch/claim, and what exists is the contract level plus
the launch/claim level. Steps 7, 8, 9 and 3a are untouched: no pool on the
selected instance, no deterministic report-and-hold Job, no logs, and
`COMMANDS-202663.md` part 2 is still a template.

**Boundaries kept.** No live model, no credential read, no Git operation, no
worker-add interface, no prior instance touched, no frozen schema asset or
image changed.

**Spending this claim.** About twenty focused suite runs across eleven suites
(largest 348 tests in 92s), two isolation probes with a change reversed, and no
container, image build or engine execution. Per-command wall-clock unrecorded
and marked unknown.

## claim207111 — the +7 delta found and fixed; the lifecycle proof is real

**The unexplained delta was a product site I had missed, and my own refusal
message is what found it.** Enumerating all 20 errors with their terminal
exception showed the +7 is exactly one class —
`TwoBoundJobsTraverseServingAndCorrection`, 7 tests — every one refusing with
`this Job names the whole runtime manifest digest`, the diagnostic added for
review206898 [R3]. It was not a fixture. `_DerivedJudgment.__init__` composes
`self.input` from its own runtime manifest digest and `poll` hands that
dictionary to `operations.admit` **in the Job's place**, because a derived
judgment has no stage row and no pool allocation to read a real Job from. So it
is read by the rule that compares a JOB's identity, and left as the whole
manifest digest it refused every derived judgment against the judge's own
configuration — the one shape that cannot be a mismatch.

Corrected to the projection, with the runtime half explicitly preserved: the
launch still states `given["input_manifest"]["manifest_digest"]` as its runtime
input, and `_claim` reads the same projection off the offer the judgment mints
for itself. **The four suites are now 13 errors, 0 failures — exactly the
pre-change baseline.** The delta is zero; nothing is attributed to
"pre-existing" by assertion.

The surviving 13 are unchanged and enumerated: 8 `'object' has no attribute
'proposal'` in `TheIntegrationStageConsumesTheAcceptedPort`, 4
`'SimpleNamespace' has no attribute 'reconciles'` in
`AFreshPortReentersANeverStartedDelivery`, and 1 `ModuleNotFoundError:
integration_placement`.

**The proof label was wrong and is corrected.** Review207096 is right that
`ThreeWorkersOneJobThreeImages` constructs through `__new__` and calls only
`_held`/`_matches`: that is configuration and preflight eligibility, not
execution. It is kept for what it is.

**`TheHeterogeneousPoolTraversesTheSameLifecycle` is the execution proof.** It
subclasses the accepted one-Job lifecycle case and therefore **re-runs all ten
of its cases** — implementation, handoff, a real reviewer container's verdict,
a changes-requested round, the correction round, the integration port and the
integration stage advancing through it — over a pool whose three workers select
three different immutable images and carry independently composed manifests
(own id, own creation instant, own image, toolchain, credential policy and role
instructions). 15 OK.

Five of those cases are new and specific:

- the three images and three runtime manifests are asserted distinct, so the
  inherited ten cannot silently pass over a homogeneous pool;
- every worker's manifest produces the ONE Job input identity the fixture
  actually submitted;
- **runtime attribution survives** — the implementation and review attempts
  really ran, and the manager's own attempt rows are read back through its
  private reader: each records its own image, its own whole manifest digest and
  its own toolchain, and the two roles are asserted to differ in both;
- a worker whose image is not its own manifest's refuses at `operations_from`,
  the boundary that composes a real deployment;
- a worker that moved a shared member cannot produce the Job's identity.

`runtime_profile_digest` is deliberately not varied here — `_held` ties it to
the worker's `profile_digest` and `_matches` ties that to the stage's, so
varying it needs per-stage profile rows. Its independence is fixed directly in
`test_manifest_rules`, and the omission is stated at the fixture rather than
left to be discovered.

**The unretained producer manifest refusal is now covered**
(`test_a_producer_manifest_this_manager_does_not_retain_refuses`): admission
reads the producing worker's manifest rather than trusting the proposal's
digest, and a proposal naming one this manager does not retain is refused as a
candidate whose Job membership cannot be established, with nothing written.

**FINDING's live rule is superseded in place.** The five-member paragraph and
the compatibility paragraph are marked superseded; the eight-member
classification is recorded with the reason each member is on its side; and the
assertion that "only one host deployment is affected" is **withdrawn as
unsupported** — I inspected one host's instance directories and cannot
enumerate every deployment, retained Job or historical record. What is
established is stated with its limits, including that one `_matches` refusal is
**not** completed legacy recovery coverage across every stage and entrypoint.

**Verification, measured.**

| suite | result |
| --- | --- |
| `test_stage_execution` + `test_managed_integration` + `test_integration_worker` + `test_lifecycle_composition` | 348 tests, **13 errors, 0 failures** — exactly the pre-change baseline |
| `TheHeterogeneousPoolTraversesTheSameLifecycle` | **15 OK** (10 inherited lifecycle + 5 new) |
| `test_single_worker` + `test_manifest_rules` + `test_claude_context` | **246 OK** |
| `test_driver` + `test_execution` + `test_reconciliation` | **267 OK** (1 new) |
| `job_manager` | **879 OK** |

**Still open.** Steps 7, 8, 9 and 3a: the pool on the selected instance, one
deterministic report-and-hold Job with usable logs, concrete commands naming
immutable digests, and the complete copied-input provenance including
`source_profiles`. Recovery/historical attribution beyond the attempt-row
evidence above is also unproved and is named in PLAN rather than implied.

**Boundaries kept.** No live model, no credential read, no Git operation, no
worker-add interface, no prior instance touched, no frozen schema asset or
image changed.

**Spending this claim.** About fifteen focused suite runs across eleven suites,
one full error-enumeration run over the four suites, and no container, image
build or engine execution. Per-command wall-clock unrecorded and marked
unknown.

**Step 3a, the half that can be done now.** `copied-inputs-207111.py` reads
each recipe's own `COPY` instructions rather than a hand-written list — a
recipe that gains a path cannot leave this record describing the old set —
expands directories, and compares every resulting path checkout-side against
the same path inside a container run from the artefact. 7 paths for the
provider image, 9 for the integration image, **all equal**, and
`source_profiles/__init__.py` and `source_profiles/checkout.py` are now
enumerated where review206578 correctly found them missing. `PROVENANCE-202663.json`'s
eight-file list is marked superseded by it. The remaining half — a PRE-build
input snapshot — cannot be produced after a build and is recorded as open
against the next build of either recipe, rather than simulated.

## claim207219 — the pool is composed and APPLIED; steps 7 and 9 done

**R1a — my description was overstated and is corrected at the source.**
`TheHeterogeneousPoolTraversesTheSameLifecycle` now states exactly what it
drives: REAL — the Job and control stores, admission, allocation, the offer,
the claim, the attempt rows, launch composition, the mount boundary, the
endings and their route changes, the review verdict's effect, and the
integration port's composition; NOT REAL — the container, because
`ComposedOneJobCase.serving` uses the simulated `Engine` and `turn` calls
`serve_exchange` in-process with a fake provider. The three image digests are
identities the deployment carries and the manager records, not three artefacts
that ran, and full terminal heterogeneous integration is named OPEN.

**R1b — the shared-member negative is now a real refusal.** It submits the
moved configuration through the module's own public admission and asserts the
refusal text, that no worker was allocated, and that no admit receipt
committed; a positive control asserts the intact pool IS admitted and allocates
`implementation-worker`. The old version compared two digests and established
nothing at that boundary, exactly as the review said.

**Provenance wording narrowed.** `copied-inputs-207111.py` and the provenance
record now say EQUALITY AT OBSERVATION TIME — a file changed after the build
and changed back would satisfy it — instead of my earlier claim that nothing
had moved since the build.

### Step 7 — done, and it is the payoff of the whole correction

`compose-pool-207219.py` composes the pool for
`/home/sl/baton-v12-instance-2026-09-18T10-38-52Z` with every identity measured
rather than restated: the declared base read from the instance target's own
`packed-refs`, the principals asked of the instance Authority through
`bootstrap.principals_for`, per-recipe toolchain digests, the adapter's
measured bytes, and this dossier's own digests as the record binding.

**Three workers, TWO images, ONE Job input identity** — the pool that could not
be expressed before this Work:

| role | participant | image | runtime manifest |
| --- | --- | --- | --- |
| implementation | `baton.claude-coder` | provider `sha256:9ff3322f…` | `sha256:e3bd9547…` |
| review | `baton.claude-reviewer` | provider `sha256:9ff3322f…` | `sha256:ecbca685…` |
| integration | `baton.merge` | integration `sha256:b9b75acc…` | `sha256:98ff830f…` |

Job input identity `sha256:514f591d…`, proved equal across all three before
anything else was composed. Every accepted validator held:
`check_manifest_structure` ×3, `bootstrap.held`, `bootstrap.configuration`,
`stage_execution.held_configuration`, `bootstrap.validated`,
`job_manager.documents.owned_submission`. `complete: true`, `refused: []`.

**Applied** through `tools.bootstrap --inputs`, the deployment-preparation form
that does not reinstall the runtime: Work `a92e1d71-W1` created on `impl`,
routes `impl → baton.claude-coder`, `rview → baton.claude-reviewer`,
`integration → baton.merge`, the four grants in that Work's scope, and the
canonical target established at `e486652c…`.

**The policy pin was predicted wrong and the gate caught it.** First prediction
8 against generation 9. The bug was mine and structural: I added the bump to a
reading taken before the bootstrap, while the pin must equal what the bootstrap
LEAVES. Measured on this instance — first capacity bootstrap 1 → 9 (+8), repeat
9 → 16 (+7) — recomposed at 16, re-applied, and `check_policy_pin` now reports
configured 16 against generation 16, **equal**. Both numbers are observations
of this instance, not a contract.

### Step 9 — done

`COMMANDS-202663.md` is rewritten. The part-2 template both reviews refused is
gone; every value is read out of an artefact that exists, including the
worker table, the Job input identity, the applied routes and grants, the pin
check with its measured bumps, and the exact submission command.

### Step 8 — open, with an exact reason

**The pool composed in step 7 cannot serve it.** The implementation and review
workers run the provider image, whose entrypoint is `dogfood_entry.py` →
`ClaudeAgent` → a real provider, so a Job that reaches them makes a model turn
and owner 206702 forbids that. `pool-submission.json` is therefore composed,
validated and deliberately NOT submitted.

Step 8 needs a deterministic provider at the same boundary — a separately
provenanced fixture image configured as its own pool on the same instance —
then one Job carried to report-and-hold with retained logs. That is
implementation under the existing ruling, not a new decision.

**Verification.** The four suites 348 tests / 13 errors / 0 failures, the
pre-change baseline, unchanged by this claim's test edits.
`test_single_worker` + `test_manifest_rules` + `test_reconciliation` 304 OK.
The heterogeneous lifecycle class is 16 OK with the corrected negative.

**Boundaries kept.** No live model and no Job submitted. No credential read,
staged or verified — the deployment names a locator. No Git operation. No
worker-add interface. No prior instance touched. No image rebuilt. The only
durable writes outside this dossier are to the selected instance the owner
named: its own `jobs/<job>/task.json`, `integration-instructions.txt`,
`deployment.json` and its Authority.

**Spending this claim.** About ten focused suite runs, two composer runs, two
bootstrap runs, two pin checks and two read-only container runs. Per-command
wall-clock unrecorded and marked unknown.

## claim207307 — R1 answered; it found a real blocker (D3)

**Review207292's R1 was right to ask, and the answer is worse than a doubt.**
Measured rather than inferred from a timestamp:

- the installed runtime at the owner's instance is sha256 `378ec932…`, equal to
  `instance.json` `identity.sha256`, and its in-bundle `build-stamp.json`
  records the source state it was packaged from: commit `e486652c`, dirty,
  **77 changed entries**;
- a runtime built from this tree now is sha256 `48b12f15…`, same commit, dirty,
  **92 changed entries**.

Different artefacts, packaged from different source states. The build stamp is
captured at package time and travels inside the bundle, so that is a content
fact rather than a file-date inference.

**My own first probe was inconclusive and is reported as such.** Searching
either executable for `job_input_identity` finds nothing — including the fresh
one, which certainly contains it — because the modules are compressed `.pyc`
inside the frozen archive. The reviewer's warning against turning weak evidence
into a content proof applied to my probe as much as to the timestamp.

**The supported path refuses to fix it, measured, non-destructively.** Running
`tools.bootstrap --inputs … --destination … --distro …` against the instance
exits 2 with *"there is already a runtime at …; nothing here upgrades a
deployment in place. Stop that instance and prepare a new destination if you
mean a different runtime."* `_admissible` runs that check before the
destination lock, so nothing was copied, replaced or removed. `v12/STACK.md`
states the same rule in prose; it is a deliberate product decision.

**So step 8 cannot honestly run on the owner's instance.** It would either
exercise the checkout and call it installed-runtime proof — which review207292
forbids — or start a scheduler whose `_matches` still compares the whole
manifest digest and would refuse the very pool claim207219 composed.

Three resolutions are recorded in `FINDING.md` D3. Resolution 3 — run the
deterministic verification on a SEPARATE disposable destination prepared with
the corrected runtime, leaving the owner's instance untouched — needs no
decision and is the next implementation step. Resolutions 1 and 2 destroy or
move the instance the owner named by path and are reported, not taken.

**Record inconsistencies the review named, both fixed.** PLAN step 6 no longer
says "done": it says partly done, with terminal heterogeneous integration and
recovery attribution named as NOT done. Step 9 now reads "written, not ready".
`COMMANDS-202663.md` lost the heading claiming something must be decided first,
and its part 3 no longer says the lifecycle commands are safe to run — `status`
and `monitor` are, `start` is not until D3 is resolved.

**Not started.** Step 8 itself, on any destination; recovery/historical
attribution; 3a's prospective build snapshot; re-verifying the pool, pin and
commands after a fixture pool has been used.

**Boundaries kept.** No live model, no Job submitted, no credential read. No
Git operation. No prior instance touched, and the owner's selected instance is
exactly as claim207219 left it — the refusal above changed nothing. The one new
artefact outside this dossier is a freshly built distro at
`v12/python/build/out/distro`, which is build output and is installed nowhere.

**Why this claim ends here, named accurately rather than as a milestone.** The
reviewer is right that the claim-release invariant is not a reason to stop. The
actual constraint is this turn's own length: resolution 3 is a fixture image
build, a second composition, a bootstrap, a started stack, a submitted Job
driven to terminal and its logs collected, and beginning it here would leave it
half-done with a live stack and no account. The scope resumes unchanged.

**Spending this claim.** One runtime build, one refused install (no effect),
two digest/stamp comparisons, two archive-content probes (one inconclusive, and
said so). No suite run: no product or test file changed. Per-command
wall-clock unrecorded.
