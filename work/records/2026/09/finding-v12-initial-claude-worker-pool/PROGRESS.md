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

## claim208217 — the installed runtime serves a heterogeneous pool, measured

**The owner's supersession is pinned first**, in `FINDING.md`: the development
instance is now `/home/sl/baton-v12/instance-2026-09-19T02-05-20Z`, the old
roots are under `/home/sl/baton-v12/archive/`, and every earlier absolute path
in this dossier now describes an archived location. Verified read-only: the new
instance's `identity.sha256` is `48b12f15…`, its build stamp records 92 changed
entries, its Authority is `cf92cbff…` (a different identity from the superseded
instance), its pool was empty and its `policy_generation` was 1.

### Two deterministic images, which is itself the point

`fixture-context/Dockerfile.producer` and `Dockerfile.integrator`: W198667's
reviewed worker bytes, snapshotted with attribution into this dossier, on
W197661's own base digest, entered at **two** entrypoints — `proposing_entry`
and `importing_entry`. W197661's fixture recipe opens by explaining why it had
to be ONE image and records that a second one was built and "three validators
refused the composition". Two images is that refused composition, built to be
served.

Producer `sha256:6ae290f9…`, integrator `sha256:9944eef7…`, both
`--pull=false --no-cache --network none`.

### What the INSTALLED runtime actually did

Composed by `compose-verification-208217.py` (every accepted validator holding,
`complete: true`), applied through `tools.bootstrap`, and started through the
instance justfile — the documented installed path, not the checkout.

| stage | worker | image | state |
| --- | --- | --- | --- |
| implementation | `baton.fixture-coder` | `6ae290f9…` | **completed** |
| review | `baton.fixture-reviewer` | `6ae290f9…` | **completed** |
| integration | `baton.fixture-integrator` | `9944eef7…` | claimed, runtime not started |

The scheduler's own allocation row labels this pool
`"separation_class": "provider-diverse"`.

**Runtime attribution, read from the manager's own attempt rows**
(`HETEROGENEOUS-RUN-208217.json`): three attempts, **two distinct
`image_digest` values**, **three distinct `input_digest` values** and two
distinct `toolchain_digest` values — while the Job names ONE input identity.

**This is the behavioural evidence review207292 asked for.** A runtime without
this Work's projection correction compares a Job's `input_digest` against a
worker's whole manifest digest and refuses at admission with "the Job names
another bootstrap input". This runtime admitted three workers carrying three
different manifests and ran two of them. What was **Inferred** from a build
stamp is now **Confirmed** by behaviour.

**Attempt logs are readable through the supported reader**
(`attempt-logs-208217.txt`): `tools.attempt_logs_command … locators` answers
per stream, and reports the native room as "the room exists and the provider
wrote nothing in it" — correct and honest for a deterministic fixture that
enters no provider.

### Terminal report-and-hold was NOT reached, and one reason is my own defect

Integration is `claimed` with `execution_runtime: "not-started"`; its admit
receipt committed and the offer expired at 02:16:28.

**A defect in my composition, found by reading the retained line.** The
producer wrote `w197661-fixture.txt` — `ProposingAgent` is W197661's reviewed
deterministic stand-in and writes that exact filename; it does not read the
task instructions. My task document asks for `w202663-fixture.txt` and its
verification command asserts that file's contents, so the command cannot pass
over the candidate this agent actually produces. The task text must name what
the reviewed agent writes, or the agent must be a different one. Recorded
rather than patched blind, because the composition, the Job and the Work on
that instance are already durable and the correction should be composed
deliberately.

Whether that is the only reason integration did not start is **not
established** — the expired offer may have its own cause. Unmeasured, and said
so.

### Two deployment facts measured the hard way

- **A workspace store is MANAGER-scoped, not worker-scoped.** Giving each role
  its own refused: "this manager is already configured with workspace store …
  and is being told to use …; every attempt already allocated under the first
  store would become unfindable, so a changed store is a fresh store rather
  than a reconfiguration."
- **A changed store is a fresh store**, so the second correction had to adopt
  the path the control store already held rather than a tidier one. The
  composer records why at the site.

### Verification

Three bootstraps on the new instance, each with its pin predicted and then
CHECKED: 1→9 (configured 9, equal), 9→16 (equal), 16→23 (equal). The
first-bootstrap bump of +8 and repeat of +7 measured on the superseded instance
held here too — still observations, not a contract.

### Still open

Terminal report-and-hold; the task/agent filename correction above; recovery
and historical attribution; refusal coverage on the live deployment; 3a's
prospective build snapshot; and re-verifying the Claude pool, its pin and the
launch commands against the new instance — the Claude pool composed in
claim207219 targets the SUPERSEDED instance and must be recomposed for the new
destination.

**Boundaries kept.** No live model — both images are deterministic fixtures and
no provider was entered. No credential opened: the slot holds a synthetic
non-bearer marker this run wrote 0600, and the fixture agents never read it. No
Git operation. No worker-add interface. No archived instance touched.

**Spending this claim.** Two image builds, three composer runs, three
bootstraps, three pin checks, two starts (one refused, one served), one
submitted deterministic Job, one stop, and several read-only store reads. No
suite run — no product or test file changed. Per-command wall-clock unrecorded.

## claim208326 — R1 diagnosed to the exact missing step; my earlier guess was wrong

**Review208310 [R1] is right that offer expiry is not the cause.** The claim
committed at `02:14:33.041Z` against an expiry of `02:16:28.012Z`. I traced the
chain through retained state instead of guessing again.

**And my claim208217 guess was wrong.** I wrote that the task/agent filename
mismatch was "one reason" integration did not start. The retained review-cycle
state says otherwise:

| fact | retained value |
| --- | --- |
| review line | `line-be019c3b…`, state **`accepted`** |
| checkpoint | `checkpoint-24f4db7a…`, state `frozen`, and it IS the line's `current_checkpoint_id` |
| verdict | `verdict-dcac2d5d…`, disposition **`accepted`**, by `baton.fixture-reviewer` |
| review attachment | `review-7de4f6f4…`, state `ended` at `02:14:22.727Z` |
| integration eligibility | **1 row present** |
| Authority `proposal` | **1 row present** |
| Authority `receipt` | **0 rows** |

So the review really did accept, the line really is eligible, and a proposal
really was published. `integration_checkpoint`'s every condition — line
`accepted`, checkpoint `frozen`, checkpoint current — holds. The filename
mismatch did not block any of that, and I am withdrawing the suggestion that it
did. It remains a real defect in my composition; it would bite where the
integrator re-runs the SAME verification argv over the imported tree, which is
one step past where this run stopped.

**Where it actually stops: no receipts exist.** `admission._proved` requires a
verification, a review and an approval receipt for the proposal, and the
Authority holds none. The integration stage sits `claimed` with `admit` and
`claim` both `performed`, **no further receipt, no deferral and no recorded
refusal** — so the tick is returning without acting rather than refusing with a
reason, which is why nothing explains itself in the snapshot.

**What is NOT yet established, and I am not guessing again.** Which call
returns without acting, and why. The candidates are the port's own
preconditions and the receipt-issuing path under the configured receipt
participants (`baton.fixture-verifier`, `baton.fixture-judge`,
`baton.fixture-approver`), none of which has been exercised here. Measuring it
needs either a tick driven with its refusal captured, or the retained stores
read through the accepted driver — and doing that through the CHECKOUT would be
diagnosis only, never installed-runtime evidence, which is a line
review207292 drew and I am keeping.

**R2 and R3 are accepted as stated and are not yet answered.** The attempt-log
reader reports all six streams absent and the native room empty: that proves
the reader works, not that usable bytes were captured, and I did not claim
otherwise in the artefact but did overstate it in my handoff sentence "logs are
readable" — narrowed here. A capture proof needs a deterministic workload that
actually emits on stdout/stderr and a verification command, then nonempty
retained bytes read back after cleanup. And supervisor stop is not cleanup
evidence: the snapshot records two runtimes `destroyed` and the integrator
`not-started`, which are three distinct facts, and fresh supported cleanup and
fencing observations are still owed before any retry.

**Also owed before a retry, from R1:** the first run's Job input, task bytes
and attempt records are immutable evidence. A corrected task must arrive as an
explicit supported recovery or a fresh Job/Work/attempt within the same
owner-selected instance — never by overwriting the existing input or
repointing historical attempts.

**Not done this claim.** Terminal report-and-hold; the capture proof; cleanup
and fencing evidence; recovery and historical attribution; refusal coverage;
build provenance and the development-source prerequisite check; and
recomposing the real Claude pool for the new authority and destination.

**Boundaries kept.** No live model, no submission, no credential read, no Git
operation, no archived instance touched, no store repaired by hand, no
destination change. Every read above was read-only.

**Spending this claim.** Six read-only store and snapshot reads and one review
of the retained run artefacts. No build, no container, no bootstrap, no start,
no suite run — nothing was executed and no file outside this dossier changed.

## claim208373 — my withdrawal was wrong; the corrected run hit D4

**Review208349 is right and my claim208326 correction was itself wrong.** The
installed `state/manager.log` records at 02:20:37 that the integration was
deferred `policy`/`denied` with *"the required tests for task
'w202663-deterministic-verification' exited 1 in this producer's container; a
failing required command is not admitted and an accepted technical review is
not a substitute"*. So the filename/content mismatch WAS the cause, my
claim208217 statement was right, and my claim208326 withdrawal of it was an
over-correction I made from an incomplete reading of that log — I tailed it and
saw only historical traces and the startup line, and concluded "no refusal
recorded" when the refusal was recorded in the tick report. Zero receipts is
correct enforcement by `_ordinary_tests_passed`, not a missing issuer.

**The correction, made properly.** `ProposingAgent` writes
`w197661-fixture.txt` holding "w197661 deterministic fixture candidate" and
does not read task instructions. The task now names exactly that, name AND
content, with the reason recorded at the site so nobody "fixes" it back. The
verification was not weakened and no receipt was manufactured.

**Cleanup and fencing, observed fresh before any retry.** Supervisors absent;
the two destroyed runtimes have no container on the host; the integrator never
started so there is nothing to fence; one unrelated container runs
(`mariadb:11.4`). The integration stage's reserved allocation remains held and
is accounted for as durable scheduler state, not cleaned up by hand.

**Fresh identities, with the first run preserved.** New Job
`w202663-deterministic-verification-2` on new Work `cf92cbff-W2`, new workers,
new participants. The first Job, its task bytes, its attempts and its refusal
evidence are untouched, and the composer now carries the prepared Job and its
workers **verbatim out of the destination's own configuration** rather than
recomposing them, so the deployment the first run ran under is not rewritten.

**Then D4 closed the path** — recorded in `FINDING.md`. Four rules, each
measured by its own refusal: a repeat bootstrap preserves prepared Jobs; one
participant per worker across the pool; a changed pool is a new generation; and
a live canonical target is not re-described. The stored target document embeds
`"at pool generation 1"`, so 3 and 4 cannot both be satisfied. **A Job that
brings its own workers cannot be added to an instance whose target is live.**

**The consequence I caused, said plainly.** The owner's instance now holds a
two-Job, six-worker configuration at `pool_generation: 2` and **`just start`
refuses**. Nothing was lost — both Jobs, both Works, every attempt, the
accepted checkpoint and verdict, and the first run's refusal evidence are
intact, and no store was hand-repaired — but the instance will not start until
this is resolved, and setting the generation back to 1 does not recover it
because the durable pool really does have six workers.

**Also measured this claim: the policy-pin bump is PER WORK.** One Work moved
7 per bootstrap; two Works moved 14 (23→37, 37→51). My prediction was wrong
twice and `check_policy_pin` caught it both times; the composer now multiplies
by the number of Works and the final three bootstraps were equal at 65, 79 and
93.

**Not done.** The terminal report-and-hold; captured nonempty logs;
integration-image execution; recovery/historical attribution; refusal coverage;
prospective build provenance; development-source prerequisites; and recomposing
the real Claude pool for the new authority and destination.

**Boundaries kept.** No live model, no credential read, no Git operation, no
archive edit, no hand-repaired store, no destination change. The corrected Job
was submitted but has not run.

**Spending this claim.** Six composer runs, six bootstraps, six pin checks,
three starts (all refused, each by a different rule), one submission, one
cleanup observation sweep, and several read-only store reads. No suite run —
no product or test file changed. Per-command wall-clock unrecorded.

## claim208463 — the D4 repair, and two of my claims measured wrong

**The owner's ruling is pinned first** in `FINDING.md`, with both corrections
review208415 made to my own D4 write-up adopted rather than argued:

- **D4's "both resolutions are outside this Work's authority" is superseded.**
  Decoupling a stable target descriptor from mutable capacity is narrower than
  the excluded worker-add interface. My equating of the two was wrong.
- **My durable-state claim is withdrawn, and now measured wrong.** I asserted
  the instance holds `pool_generation: 2` durably and that reverting could not
  recover it. Read through the public reader,
  `scheduler.active_generation` answers **generation 1 with three workers**,
  activated 02:13:33. The failed start did NOT commit a new pool. The reviewer
  predicted exactly this from the source order — targets activate before
  `scheduler.activate_pool` — and was right.

### The repair

`StageDeployment.activate_targets` composed `at pool generation {n}` into the
target description, and `queue.activate_target` compares the whole document
digest for a live key. Two halves, because review208415 warned that only doing
the first re-describes the target just as surely:

- a **new** target gets a description naming the deployment and nothing that
  moves with capacity;
- an **existing** target is read back through the public `target_of` and
  presented **unchanged**, taking the exact-replay path — so a legacy
  generation-bearing descriptor keeps working and its identity, fence, queue
  and history are untouched.

`activate_target`'s refusal is not weakened; this caller simply stopped
manufacturing a difference out of capacity. Nothing rewrites a durable row.

### Coverage — `TheTargetDescriptorIsNotCapacity`, 7 cases, all driving the
real method against a real `IntegrationStore`

Initial activation carries no generation; an exact repeat replays rather than
colliding; **a capacity change no longer re-describes a live target** (the
regression); a legacy generation-bearing descriptor is preserved byte for byte;
a genuinely different document is still refused `policy`/`denied`; a refused
activation leaves the target intact and this deployment still adopts it
afterwards (failed-start recovery); and a deployment adopts exactly the targets
its own bindings name.

**Reversal probe:** with the old line restored, 4 of the 7 fail; with the fix,
all 7 pass.

### Verification

`TheTargetDescriptorIsNotCapacity` 7 OK. The four baseline suites 348 tests,
**13 errors, 0 failures** — the unchanged pre-existing baseline.
`test_driver` + `test_execution` + `test_reconciliation` +
`test_single_worker` + `test_manifest_rules` **479 OK**.

### The installed instance still refuses, and that is expected

Starting it after the repair refuses identically, because the installed frozen
runtime predates the correction — D3 again. Owner ruling 208460 resolves it:
the owner installs a fresh timestamped instance once the correction has been
independently reviewed. **I did not replace, reset or work around the current
instance**, and its evidence — both Jobs, both Works, every attempt, the
accepted checkpoint and verdict, the first run's refusal — is intact.

### Deliverables for the deployment step

`COMMANDS-202663.md` is rewritten against the current state; every earlier
version described the superseded, now-archived destination. It carries the four
image builds with their digests, the runtime rebuild (which must be redone
after this repair, since `48b12f15…` predates it), the exact `just bootstrap`
the owner runs, `install-inputs.json` beside it as the fresh-install document,
and eight ordered verification steps — each naming what it proves and what it
does not, with the installed-versus-checkout line kept.

### Still open

Terminal report-and-hold; capture proof; integration-image execution;
recovery/historical attribution; refusal coverage on a live deployment;
prospective build provenance; development-source prerequisites; and the real
Claude pool recomposed for whichever authority the next instance has.

**Boundaries kept.** No live model, no credential read, no Git operation, no
archive edit, no hand-repaired store, no instance replaced or reset, no
destination change, and no worker-add interface.

**Spending this claim.** Two supported state observations, one product edit,
one new test class with a reversal probe, and four suite runs. No image build,
no bootstrap, one refused start (no effect). Per-command wall-clock unrecorded.

## claim208531 — R1 and R2 completed

**R1 — composition-level failed-start and capacity coverage.**
`TheTargetSurvivesACapacityChangeOverRetainedHistory` drives the real
`stage_execution.operations_from` — the function whose target adoption
precedes `scheduler.activate_pool`, which is the order D4 lives in — over a
target that already carries a **legacy generation-bearing document, a queue
entry and its fence**, all made through the public operations rather than
written as rows.

- *a capacity change composes over retained history*: generation 1, then a
  genuinely different pool at generation 2, with the legacy document, fence,
  state and queue asserted unchanged after each.
- *a startup that fails after adoption leaves the target alone*: the pool is
  established first, then `scheduler.activate_pool` is patched to raise — a
  start that adopted the target and then died. The retained state is unchanged
  and the ordinary retry then composes, with no repair in between.

Three measured facts shaped these and are recorded at the sites: a `/1`
deployment refuses two workers for one stage, so the capacity change moves
*who serves review* rather than adding a producer; a configured worker carries
exactly `worker_id`, `role` and `deployment`; and `_pool_generation` predicts 1
for an absent pool, so the failure case must establish generation 1 first.

**Reversal probe:** both cases fail against the old line; all **9** D4 cases
(7 method-level + 2 composition-level) pass with the fix.

**R2 — runnable owner commands, no placeholders.**
`install-next-instance.sh` selects one fresh UTC timestamp under
`/home/sl/baton-v12/`, prints the destination it chose, writes it to
`selected-instance.txt`, refuses if it already exists, and invokes the
supported installer with real absolute paths.
`verify-next-instance.sh` reads that file, so no later step can describe a
different instance and nothing has to be edited by hand.

**And the composer no longer needs editing.** `compose-verification-208217.py`
takes `--instance`, reading the destination's own persisted
`authority-identity.json` rather than taking a uuid on the command line. Its
claim208217 constants are untouched as the record of that run — verified both
ways: `--instance` against the current instance composes `complete: true`, and
the module without the flag still reports its recorded `DEST`/`WORK`.

**The installer-input convention is documented, and my earlier reading
corrected.** `install-inputs.json`'s `state_root` placeholder is never read on
this path: `tools.bootstrap.main` overrides it from `--destination` before
validation. Validating that document alone would refuse it, and **that refusal
is not an installation defect** — review208507 verified the override in source
and I am not reporting one.

**Prospective build provenance — step 3a's remaining half, now closed for this
build.** `prospective-snapshot.py` recorded **106 inputs**, digest
`sha256:e37c5e5b…`, at commit `93da9d62`, **before** the build it describes.
Then `just build` produced `sha256:7040dd00…` with stamp `93da9d62`, dirty, 38
changed entries. `RUNTIME-BUILD-208531.json` binds the two and states plainly
what a digest does not establish: identity, not behavioural acceptance. It
supersedes `48b12f15…`, the runtime installed at the current instance, which
was built before the D4 correction existed — **not by replacing it**, which
owner 208460 forbids, but as the artefact the owner's fresh installation will
carry.

**Verification.** The four baseline suites 348 tests, **13 errors, 0
failures** — the unchanged pre-existing baseline. `test_coordinator` +
`test_driver` **326 OK**. The nine D4 cases OK.

**Still open, unchanged.** The installed verification itself, which
review208507 says not to attempt before the owner deploys: terminal
report-and-hold, capture proof, integration-image execution,
recovery/historical attribution, refusal coverage, development-source
prerequisites, and the real Claude pool for whichever authority the next
instance has.

**Boundaries kept.** No live model, no credential read, no Git mutation, no
archive edit, no hand-repaired store, no instance replaced or reset, no
destination change, no worker-add interface, and no installed run attempted.

**Spending this claim.** One product-free test addition with two reversal
probes, one prospective snapshot, one runtime build, two composer runs, and
four suite runs. Per-command wall-clock unrecorded.

## claim208647 — the three deployment-package corrections, R1–R3

Review208585 accepted D4 (nine cases, independently run) and returned three
bounded package corrections. All three are done; no D4 test was touched and
nothing was installed.

**R1 — the installer now binds the reviewed artefact instead of rebuilding.**
The defect was mine to see in `v12/justfile` all along: `just bootstrap
INPUTS DEST` with no DISTRO runs `just build` first, so the previous script
installed *whatever the tree built at execution time* while the dossier cited
the reviewed digests. Now `install-next-instance.sh` names
`build/out/distro` explicitly as the third operand, and it is fenced on both
sides: BEFORE installing it refuses unless the executable digests as
`RUNTIME-BUILD-208531.json` records (`sha256:7040dd00…`) **and** the whole
one-folder bundle digests as `BUNDLE-MANIFEST-208647.json` records
(`sha256:dbdee27a…`, 81 files, digested by `tools.instance.manifest` — the
same digester the installer's admission and post-copy check use); AFTER
installing it reads the destination's `instance.json` back and compares the
installed runtime digest and executable hash against the same two records.
The bundle manifest was taken at the identity review208585 itself confirmed
(executable equal to the recorded digest), extending that confirmed identity
from the executable to the whole bundle — identity, not behavioural
acceptance, and not a rebuild presented as the old build.

**Exercised without installing** (`installer-binding-test-208647.log`): the
pre-check standalone against the real distro ACCEPTS; the post-check against
a bounded fake destination ACCEPTS when identity matches and REFUSES (exit 1)
after one appended byte on the fake installed executable.

**R2 — the pin check selects the instance it answers for, and the submission
is a command, not a discovery.** `check-policy-pin.sh` reads
`selected-instance.txt` (or an explicit path), calls `select_instance` BEFORE
`check_policy_pin`, prints the answer with the instance and authority it
answered for, and exits nonzero on inequality — a gate, not a remark.
`verify-next-instance.sh` step (d) now prints the exact submission:
`tools.job_manager --store $DEST/db/jobs.sqlite3 --incarnation
w202663-verification-submit --authority-uuid <read from the instance's own
authority-identity.json> submit --document <dossier>/pool-submission.json`,
with every value filled from the retained selection at print time.

**Proved on a bounded fake instance** (`test-pin-command-208647.py`,
`pin-command-test-208647.log`, 9/9): a fake with `authority-identity.json`, a
real tiny Authority store made through the public `Authority.create`, and a
`deployment.json` pin. Equal pin exits 0 and the reported instance/authority
are the fake's with the historical instance appearing nowhere (so
`select_instance` really ran); a moved pin exits 1 with the refusal on
stderr. Nothing real was read or written; the retained selection file was not
touched.

**R3 — the snapshot's completeness claim is superseded; the artefact is
preserved.** `PROSPECTIVE-INPUTS-208531.json` stays byte for byte
(sha256 `8b10b6de…`); `PROSPECTIVE-SUPERSESSION-208647.json` withdraws only
its completeness: the 106-member set omitted `requirements.build.lock`,
`packaging/stack.spec` and the recipe `v12/justfile` — all direct inputs of
`just build` — and those omissions cannot be reconstructed for that build.
What stands is the identity binding in `RUNTIME-BUILD-208531.json`.
`prospective-snapshot.py` now emits `/2`: it scans the packaging tree,
requires every declared file by name (absence refuses rather than silently
narrowing the set), excludes `packaging/build-stamp.json` as a
packaging-time PRODUCT (the spec writes it while PyInstaller reads the spec),
and states its scope — the RUNTIME build only; no runtime snapshot, partial
or complete, retroactively attests the earlier production/fixture image
builds, which keep their own provenance artefacts. Verified: 109 inputs
including the three omitted ones (`snapshot-correction-check-208647.log`);
that verification run is NOT retained as a build binding — the corrected
script counts only when run immediately before the next selected build.

**Documents aligned.** `COMMANDS-202663.md` part 1 records the built artefact
and forbids a rebuild; part 2 is now the one-command
`./install-next-instance.sh`; part 3 steps 2–4 carry `--instance`,
`check-policy-pin.sh` and the exact submission. `PLAN.md`'s current action
and step 3a distinguish the two provenance scopes.

**Verification this claim.** `bash -n` on all three scripts; the 9-check
fake-instance pin proof; the installer pre-check (accept) and post-check
(accept + refuse) without any installation; the corrected snapshot script
run once for behaviour only. The current instance and the archive are
untouched; `selected-instance.txt` does not exist yet and nothing here
created it.

**Boundaries kept.** No live model, no credential read, no Git mutation, no
archive edit, no hand-repaired store, no instance replaced or reset, no
destination change, no worker-add interface, no installed run, no rebuild,
no D4 test iteration.

## claim208777 — the installed run: real heterogeneous execution, one poisoned target, two findings

The owner installed the reviewed artifact (pass 208775; executable and
81-file bundle verified against the recorded manifests by the install script
itself). This claim ran the accepted installed verification as far as this
instance can carry it.

**What RAN, on the installed runtime, for the first time.**
`verify-next-instance.sh` (identity 7040dd00..., fresh authority 56cebb70...,
empty pool). Compose with `--instance`, apply, pin gate 1->9 predicted and
CHECKED equal. First start REFUSED: the workspace store directory did not
exist -- the manager demands an existing owned directory and refuses to
invent it; the composer's `stage_inputs` now creates the per-role launch and
credential homes and the one manager-scoped store, and the refusal is
retained (start-208777.log). Second start composed and served. The exact
printed submission command recorded the Job. Implementation and review
COMPLETED through the real producer image in containers on network none;
integration EXECUTED the real integration image (container 83cae02, real
bundle, real launch document) and PUBLISHED a refused result:
target-drift. That is genuine integration-image execution -- the open item --
and genuine live-deployment refusal coverage, on a composition that was
wrong in exactly one fact.

**D5, the fact that was wrong.** `declared_base` bound the HISTORICAL
instance's target path in its signature at import time -- the same defect
class review208585 [R2] named in the pin check. The Job declared e486652c...
while this instance's target holds 93da9d62..., and the first bootstrap
established the Authority's ONE canonical target policy from the poisoned
value. Full chain, measurements and why no supported path can recover THIS
instance are in FINDING.md D5. The composer is corrected (call-time default;
read-only verification in declared-base-check-208777.log) and `select_job`
was added so a corrected Job composes under fresh identities -- its
composition on this instance was attempted and HONESTLY refused at
preflight: two Jobs, two bases, one canonical target (compose-208777b.log).
The refused composition's pool-*.json are on disk as its record; the applied
configuration is durable at the instance.

**D4, live.** Stop, then start, over the retained target, fence, queue and
durable Job: the installed runtime adopted the whole retained history and
composed -- the exact path the D4 correction repaired, now measured on a
real deployment (start-208777c.log), with the restarted manager re-attaching
to all three recorded attempts (historical attribution in the tick record).

**D6, found by watching.** The refused integration result is durable and
readable; serving ticks across minutes and a restart observe the runtime
quiescent and take NO act; the Job never reaches report-and-hold and the
refusal reason surfaces nowhere in the projection. Measured boundaries and
the open question (who owes the collection act; whether offer expiry is the
cause) are in FINDING.md D6.

**Capture.** Locators and reads ran over the completed attempts
(capture-locators-208777.log): all streams absent, native rooms empty -- the
reader works; the fixture agents emit nothing. Nonempty retained bytes still
need an emitting workload.

**State left behind.** Stack STOPPED, stores and evidence retained; the
instance, both prior instances and the archive untouched beyond the
composed deployment's own files; final status projection retained
(run-status-208777.json). selected-instance.txt still names this instance.

**Still open.** Owner install of a fresh instance with the corrected
composer; then terminal report-and-hold, nonempty capture, D6's collection
question, recovery/historical attribution beyond the restart evidence,
development-source prerequisites, and the real Claude pool
(compose-pool-207219.py still targets the superseded instance and carries
the same signature-default defect -- port it when recomposing).

**Boundaries kept.** No live model (fixture images only, network none), no
credential read (synthetic non-bearer marker), no version-control mutation
(the integration runtime's own import refusal is the product's), no
hand-repaired store, no instance replaced or reset, no archive edit, no
worker-add interface, no agent installation.

**Spending this claim.** One verify run, three composer runs (one refused),
two bootstraps (one refused at preflight), two pin checks (one gate pass),
three starts (one refused, two served), one stop pair, one submission, one
served lifecycle to the integration refusal, capture locators + reads, two
read-only measurements, and the retained logs named above. Per-command
wall-clock unrecorded.

## claim208916 — D6 disproved by measurement; emitting workload and isolation checks prepared

Review208890 returned three bounded preparations. All three are done, and
the biggest one went against my own finding.

**1. D6 is superseded, and the measurement is the reviewer's distinction.**
Read through the PUBLIC queue readers over the integration store opened
READ-ONLY: the entry settled `refused` at 03:33:20.169Z -- five seconds
after the runtime published its result, ~109 seconds BEFORE offer expiry --
with the settlement carrying the exact target-drift reason; the lease is
`released`, ending `entry-refused` (d6-settlement-208916.log). So the
driver collected, settled and released within one tick.
`Integration.account` maps a refused entry to a held account and
`projection._integrating` deliberately owes no act for held: the
non-terminal Job under report-and-hold is the DESIGNED hold path. My
"never collected" claim is withdrawn in FINDING.md. What remains is
narrower and real: neither the plain nor the observation-enabled status
surfaces the settlement reason (the observed status reports bare
`exceptional`, exchange null -- status-observe-208916.json); an operator at
the supported reader cannot see WHY a held integration holds. That bounded
visibility question is preserved for pinning BEFORE any implementation, per
the review; no automatic retry or policy repair is in its scope.
ALSO MEASURED: the reviewer's observation-enabled status failure did not
reproduce for this handler. The factory refuses BY NAME when
BATON_V12_STAGE_EXECUTION_CONFIG is unset (first run), and succeeds with
the four exports the bootstrap prints; JobStore opened normally throughout.

**2. The emitting deterministic workload exists, with its assertions,
before any run.** `emitting_agent.py` composes the UNCHANGED
`ProposingAgent` with deterministic labelled prose on the wrapper's stdout
AND stderr -- exactly the scope `_WorkerCapture`'s tee retains, which is why
the silent fixture left every stream absent. `emitting_entry.py` is the
one-line documented-seam composition; `Dockerfile.emitting` is the producer
recipe plus exactly those two files; built --no-cache --network none ->
sha256:e48e72df... (build-fixture-emitting.log), imports proven in-container.
`compose-verification-208217.py --emitting` swaps the IMPLEMENTATION role
only, so one lifecycle measures an emitting and a silent capture and stays
heterogeneous three ways. `assert-capture-208916.py` asserts, through the
supported reader as subprocesses: both worker streams present and NONEMPTY,
the exact deterministic lines present, and (re-runnable after cleanup)
retention. Every emitted line says it is fixture output; no provider
evidence is claimed.

**3. The composer default audit is done, with isolation checks.**
`declared_base` was the ONLY computed signature default in either composer;
it is call-time in BOTH now (compose-pool-207219.py ported with a note that
it still carries only the superseded instance's constants and must gain
instance selection before composing for another destination).
test-composer-isolation-208916.py: two fake instances (text-file refs, no
version-control tool), 16/16 checks -- DEST/UUID/WORK/credential-registry/
declared-base follow each selection, nothing answers the historical
constants after selection, select_job rebinds Job+participants together,
select_emitting moves implementation only, and a fresh load still answers
the historical record (composer-isolation-208916.log).

**Documents.** COMMANDS part 1 records the emitting image and its build;
verify-next-instance.sh step (a) composes with --emitting and step (f) runs
the capture assertions; PLAN's current action rewritten.

**Still open.** Fresh owner install (D5 poisoned this instance's canonical
target -- unchanged reviewed installer); then the full installed lifecycle
to terminal report-and-hold with the emitting producer, the capture
assertions, cleanup/recovery observations, the pinned D6-visibility
question, source prerequisites, and the real Claude pool with its
instance-selection port.

**Boundaries kept.** No live model, no credential read, no version-control
mutation (fake refs are text files this test wrote), no store write (the
integration store was opened read-only through its own API), no instance
replaced or reset, no archive edit, no agent installation, no product edit.

**Spending this claim.** One observation-enabled status (plus one refused
without the environment, retained as the reproduction answer), one
read-only settlement read, one image build, one in-container import check,
one 16-check isolation run, three dossier scripts written, and the retained
logs named above. Per-command wall-clock unrecorded.

## claim208996 — the deterministic lifecycle COMPLETED on the installed runtime

The owner installed a fresh instance through the reviewed installer
(instance-2026-09-19T04-02-31Z, authority 91b5031d..., identity 7040dd00...
verified by the script's own pre/post checks). This claim carried
review208960's accepted verification to the end.

**The run, in order, every step logged.** verify-next-instance.sh (fresh
authority, empty pool). Compose --instance --emitting: declared base read
93da9d62... -- THE CORRECT VALUE, D5's correction proven on a real install
-- and the canonical target was established from it (bootstrap-208996.log).
Pin gate 1->9 predicted and CHECKED (pin-check-208996.log). Start composed
first try -- the workspace directories the composer now creates were there.
The exact printed submission recorded the Job. Implementation completed
through the EMITTING producer image; review through the silent producer;
integration EXECUTED the real integration image, imported
w197661-fixture.txt onto the target room, ran the accepted verification
argv (exit 0), settled the entry INTEGRATED at 04:04:31Z, released the
lease, and advanced the Authority's canonical target policy to the
candidate commit 617f4621.... All three stages COMPLETED under
report-and-hold (status-observe-208996.json); every log, artifact, store
and result retained.

**Capture, exactly as review208960 required.** CORRELATED: the
implementation attempt's committed allocation names worker
...-implementation, whose configured deployment names image
sha256:e48e72df... = the emitting build (capture-attribution-208996.log) --
not newest-directory guessing. ASSERTED: both worker streams present,
nonempty, carrying the exact deterministic lines, through the supported
reader (capture-assert-2-208996.log). CLEANUP ESTABLISHED SEPARATELY: the
implementation and review runtimes were DESTROYED by the manager
(execution_runtime: destroyed in the observed projection; no container
holds their mounts), the integration runtime retained-exited; supervisor
stop recorded its own non-cleanup semantics. RETENTION: the SAME attempt
re-read after cleanup and stop -- all assertions pass again
(capture-assert-3-retention-208996.log).

**One assertion corrected by measurement.** My prepared REQUIRED_LINES
assumed one process serves both phases; the retained streams carry ONLY the
work-phase lines (capture-assert-1-208996.log, 2 failures). The deployment
launches the runtime per phase and the room retains the final launch's
stream, declared finished. The assertion now requires what the deployment
actually retains, and the per-phase retention question is recorded as a
bounded observation in FINDING.md -- not silently asserted away.

**Three bounded observations recorded in FINDING.md** (none a defect
claim): per-phase capture retention; no job-level terminal field in the
projection (terminal report-and-hold is established from stage states plus
retained evidence); and the policy/repository divergence after a path-level
import -- the canonical target policy holds the candidate commit while the
repository's main still holds the base, which the real Claude pool work
must answer before composing a SECOND Job on one instance.

**State left.** Stack STOPPED; stores, logs, artifacts, result and both
prior instances plus archive untouched and retained; selected-instance.txt
names this instance.

**Still open.** Development-source prerequisites; the real Claude pool:
compose-pool-207219.py instance-selection port, the continuity question
above, its pin and its exact launch commands.

**Boundaries kept.** No live model (fixture images only, network none), no
credential read, no version-control mutation (the path-level import is the
product's own act inside its container), no hand repair, no policy edit, no
instance replaced or reset, no archive edit, no agent installation.

**Spending this claim.** One verify run, one compose, one bootstrap, one
pin gate, one start, one submission, one full lifecycle to integrated
settlement, four status reads (plain and observed), one read-only
settlement read, one attribution read, three capture-assertion runs, one
stop, and the retained logs named above. Per-command wall-clock unrecorded.

## claim209102 — D7: the second Job cannot even start on the current runtime; corrected, tested, rebuilt

Review209080's corrections adopted first: the per-phase-loss explanation is
SUPERSEDED in FINDING.md and in assert-capture-208916.py's commentary --
`baton_worker.py` serves OPERATIONS (describe, work), `consider` is refused
by entitlement before any agent code, so the missing markers were an
unreachable expectation; capture-assert-1-208996.log is preserved as that
record. No logging repair is made from absent markers.

**The continuity reproduction found something harder than the expected
publication refusal.** Composing the second deterministic Job
(...verification-3, fresh -3 identities, base 93da9d62 -- the SAME base as
the preserved Job, so the two-base preflight passes) applied cleanly, and
the pin gate earned its keep twice: the per-Work bump model predicted 16
against a measured 9->24, the composer now predicts PER JOB PREPARED
(7 x jobs), and the re-apply checked EQUAL at 38. Then `just start` KILLED
the manager: raw unhandled KeyError (1, 'w202663-...-2-implementation')
(start-209102.log; full traceback in the instance's manager.log).

**D7, pinned in FINDING.md before the fix.** The completed first Job's
allocations are durable at pool generation 1, all `released`
(cleanup-retained / integration-completed). `_required_workers` attaches
only the active generation plus RESERVED/RECOVERY-REQUIRED prior
allocations -- deliberately -- so attachment succeeded with generation-2
pairs only. `scheduler._reader` then answered observe/refresh for every
live stage by an UNCONDITIONAL `self.workers[(generation, worker_id)]`
lookup over an allocation read in ANY state: the released generation-1 key
is absent, KeyError, the serve loop unwinds. A PRODUCT continuity defect,
distinct from the fixture questions: any instance whose pool ever advances
-- exactly this Work's recorded first development task, user-managed
addition of workers to an existing pool -- could not restart once prior
work was cleaned up. No policy edit, rewind or reset is involved in
reaching it.

**The correction, exactly the pinned scope.** `_reader` alone (both callers
read-only): a settled allocation whose key is not attached answers through
`_any()` -- the same store-global read the no-allocation branch already
uses; a live allocation on an unattached key (unreachable past attachment)
refuses by name instead of crashing. No acting path touched. TESTS:
`TheReaderSurvivesARetiredGenerationsSettledAllocation` -- the released
retired-generation case answers with the allocation row untouched, and the
live-allocation path still routes to its own worker, not `_any()`.
REVERSAL PROBE: old line restored -> the new test errors with the KeyError;
fix restored -> 61 scheduling tests OK, sweep+restart+status 107 OK,
tests.tools.test_stage_execution 12 errors 0 failures -- the RECORDED
pre-existing SimpleNamespace-fixture baseline, untouched by this change.

**The publication-boundary half of the continuity question is BLOCKED
behind D7 and stands as the pinned expectation, not a measurement**: with
the D7-corrected runtime installed, job-3's producer should publish against
canonical_target policy 617f4621 while declaring 93da9d62 and refuse at
publication -- the policy/repository divergence already pinned as
observation 3. Measuring it requires the corrected runtime; the current
instance's frozen 7040dd00 predates the fix (the D3/D5 shape again).

**The artefact for the next owner install, prepared on the reviewed
cadence.** Corrected /2 prospective snapshot BEFORE the build: 109 inputs,
digest e3014158..., commit 93da9d62 (PROSPECTIVE-INPUTS-209102.json). Then
`just build` -> executable sha256:6af693b2..., whole 81-file bundle
sha256:425e624e... (RUNTIME-BUILD-209102.json, BUNDLE-MANIFEST-209102.json,
build-runtime-209102.log). install-next-instance.sh now binds THESE
records; the 7040dd00 records remain as the preserved history of the
current instance, which is untouched with its completed-lifecycle evidence.

**State left.** Stack STOPPED on the current instance (one refused start,
nothing served); job-3's submission is durable and unserved there; every
store, log and prior instance retained.

**Still open.** Independent review of D7 + this package; owner install;
then the publication-boundary measurement, the continuity resolution it
informs, development-source prerequisites, and the real Claude pool
(composer port with the same instance-selection pattern, pin, exact launch
commands).

**Boundaries kept.** No live model, no credential read, no version-control
mutation, no policy edit, no hand repair, no instance replaced or reset, no
archive edit, no agent installation. Product edit: scheduler._reader only,
with tests, per the pinned D7 scope.

**Spending this claim.** One compose+apply+pin cycle refused at the gate,
one corrected compose+apply+pin cycle equal, one refused start (the D7
evidence), two D7 test cases with one reversal probe, four suite runs, one
prospective snapshot, one runtime build, one bundle manifest, one stop.
Per-command wall-clock unrecorded.

## claim209204 — R1 completed: the real observation contract proven; boundary pinned locally

Review209188 accepted the D7 diagnosis and returned R1: prove the real
observation contract over composed history, not the absence of a KeyError.
Done, and two of my own claims were corrected on the reviewer's reading.

**Corrections adopted.** refresh_runtime is NOT a pure read -- it asks the
engine and RECORDS; non-launching is the property that matters, and the
docstring and FINDING now say so. And _any() was never proven
interchangeable: observation adopts worker-specific launch/role/manifest
context. The routing is refined WITHIN the pinned D7 scope: settled history
is answered by the SAME worker id in its newest attached generation
whenever the pool still names it; only a worker removed from every
attached generation falls to _any()'s store-backed runtime answer; a live
allocation on an unattached key still refuses by name.

**The composition proof, with the real observers**
(TheRestartOverAnAdvancedPoolPreservesSettledHistory, 2 cases): a real
composed implementation attempt to completed (real stores, real
version-controlled line, actual claude_agent workload, accepted ending),
allocation RELEASED by cleanup; the pool genuinely advanced (replacement
reviewer, generation 2); restart over the SAME durable stores; the first
sweep -- the tick that raised the KeyError -- observes the EXACT history:
same completed state, same attempt, byte-identical allocation row, runtime
observation and retained publication, and no engine start after the
restart names the settled attempt. Measured on the way and recorded: a
LIVE prior-generation allocation makes the generation-2 composition refuse
at ATTACHMENT by name -- correct and loud -- because operations_from does
not attach across generations; that separate bounded fact is recorded, not
repaired. The unattached-live branch is defence in depth
(require_recovery refuses a released allocation, measured at composition
level) and is covered at unit level with an injected answer; same-worker
routing asserted directly (newest generation's same-named worker answers,
every other worker observes nothing). Scheduling class now 4 cases.

**Suites.** 170 unit tests OK (scheduling incl. the four D7 cases, sweep,
restart, status); the 2 composition cases OK; tests.tools.test_stage_execution
at the recorded 12-error/0-failure SimpleNamespace baseline.

**The publication-base boundary, established locally as required.** The
gate is integration/driver.publish_candidate ("a proposal is offered
against the revision it was built from", refused/precondition) with
existing focused deterministic coverage asserting exactly that refusal
(tests/integration/test_driver.py:1221). Applied to the selected instance:
job-3 declares 93da9d62 against policy 617f4621 -> publication refuses with
that named precondition. The remaining continuity RESOLUTION -- how a next
Job's base and line can follow an advanced policy when a path-level import
delivers no candidate commit to the nominated source -- exceeds this
Work's authority and is pinned in FINDING.md for a ruling, with the three
candidate shapes named, none implemented.

**The package, rebuilt because inputs changed.** Prospective /2 snapshot
BEFORE the build (109 inputs, f1aa1bb2..., PROSPECTIVE-INPUTS-209204.json);
just build -> executable sha256:d5d1e9fb..., 81-file bundle
sha256:e7384ab2... (RUNTIME-BUILD-209204.json, BUNDLE-MANIFEST-209204.json,
build-runtime-209204.log); install-next-instance.sh binds these records;
the 6af693b2... build was never installed and its records remain as
history; the installed 7040dd00... instance is preserved untouched.

**Still open.** Independent review; owner install; installed second-Job
boundary measurement; the routed continuity ruling; source prerequisites;
the real Claude pool port/pin/commands.

**Boundaries kept.** No live model, no credential read, no
version-control mutation (test fixtures commit in their OWN temp
repositories through the harness's existing helpers), no policy edit, no
hand repair, no instance replaced/reset, no agent installation. Product
edit confined to scheduler._reader per the pinned scope, with tests.

**Spending this claim.** One routing refinement, two composition tests
(one measured attachment-refusal detour), two unit tests added (guard via
injected answer; same-worker routing), four suite runs, one prospective
snapshot, one build, one bundle manifest. Per-command wall-clock
unrecorded.

## claim209386 — the D7 correction field-proven; the consecutive-Job boundary recorded

Owner209384 deployed the d5d1e9fb... runtime experimentally
(instance-2026-09-19T05-02-46Z, authority 9db3a29d...) and asked for the
deterministic installed consecutive-Job and restart testing. Done; every
outcome recorded, nothing repaired.

**Job-2, complete again on the corrected runtime.** Compose --instance
--emitting read the correct base, pin 1->9 checked, start, the exact
submission, and the whole lifecycle ran: implementation (emitting image)
and review completed, integration EXECUTED and settled INTEGRATED at
05:05:03Z, all three stages completed under report-and-hold, every
allocation RELEASED (cleanup-retained x2, integration-completed) -- the
exact D7 precondition state, reproduced on purpose.

**The D7 field proof.** Pool advanced to generation 2 (job-3's three fresh
-3 workers beside the six... i.e. three -2 preserved + three -3 new), pin
gate EQUAL at 24, and `just start` COMPOSED AND SERVED over the retained
settled history -- the sequence that killed the old runtime with the raw
KeyError. History preserved after the restart (job-2 stages completed,
allocations unchanged), ZERO new containers -- no redispatch of settled
attempts -- and the capture assertions pass again on this instance's
emitting attempt.

**The consecutive-Job boundary, and it lands BEFORE publication.** Job-3
submitted; its implementation offer is issued, and the CLAIM refuses:
"the authority refused this claim: route 'integration' does not resolve to
'baton.fixture-coder-3'" (refused/precondition, retained as an outstanding
deferral each tick; implementation `offered`, review and integration
`blocked`). Both Jobs share ONE Work -- select_job changes the Job id and
participants, not the Work -- and the second bootstrap rebinds the three
route names over that shared Work to the -3 participants. Whether the
correction is the composer's (a second Job should carry its own Work, as
the first instance's two Jobs did) or a product rule is NOT established;
it is pinned in FINDING.md as the next bounded question. CONSEQUENCE: the
publication-base gate was NOT REACHED installed; that outcome remains
measured at the source level only (tests/integration/test_driver.py:1221).

**Prior-generation attachment outcome**: succeeded here because every
prior allocation was released; the live-prior attachment refusal remains
the composition-measured boundary, unchanged.

**State left.** Stack STOPPED; job-2's complete evidence, job-3's durable
submission and its retained claim deferral, all stores and logs retained;
final observed projection in run-status-209386.json; all prior instances
untouched.

**Still open.** The route/Work continuity question (pinned, unresolved);
the routed policy/source continuity ruling; the deferred coverage items
review209260 lists (removed-worker fallback, same-id changed-context,
live-prior attachment) -- explicitly not deployment gates; source
prerequisites; the real Claude pool port/pin/commands.

**Boundaries kept.** No live model, no credential read, no
version-control mutation, no policy repair, no per-Job reset workaround,
no hand repair, no instance replaced or reset, no agent installation, no
product or test edit this claim.

**Spending this claim.** One verify, two compose runs, two bootstraps, two
pin gates, two starts (both served), two submissions, one full lifecycle,
one restart proof, capture assertions, five status polls plus two observed
projections, one settlement read, two stops. Per-command wall-clock
unrecorded.

## claim209474 — route account superseded; Work selection explicit; the stalled episode's exact decision reported

Review209459's corrections adopted and its bounded preparation done;
nothing hand-released, nothing repaired.

**The route-rebinding causal claim is SUPERSEDED in FINDING.md.** The
reviewer's source reading stands: add_route_handler ADDS membership and
replaces nothing; bootstrap creates a missing Work on the implementation
route and leaves an existing Work alone. What happened: select_job reused
the ONE Work, job-2's completed lifecycle had moved it to the integration
route, and job-3's fresh implementation stage attached to it there -- the
claim correctly met a Work routed at integration. Experiment's
reused-Work lifecycle, not a product defect; submission and refusal
preserved.

**Job/Work selection is now explicit.** select_job selects Job,
participants AND a fresh authority-qualified Work together (number from
the job's suffix, or --work explicitly); --work without --job refuses.
The isolation check grew three cases: the Work FOLLOWS the job, an
explicit --work overrides the suffix, and the historical record still
answers on a fresh load -- 19/19 pass (composer-isolation-208916.log).

**Job-3's reserved allocation, accounted through supported transitions
only -- and the exact decision reported.** Restarted the stack at the
UNCHANGED generation; ordinary ticks retried the claim (refused each
time), allocation reserved throughout. Read-only offer row: state
ACCEPTED, issued by the prior incarnation, expiry long past, episode 1
unended. recover_on_restart's deliberate asymmetry RETAINS an accepted
offer (durable authorization and claim operation -- recoverable, never
abandoned), so the claim retries forever against the Work routed at
integration. No deployment-surface transition settles it
(submit/status/serve only). THE DECISION, pinned in FINDING.md: (a) a
supported settlement path for an accepted offer whose claim refuses on a
durable precondition, or (b) retain the stalled episode on this
experimental instance -- which blocks further pool-generation changes
here (no cross-generation attachment, measured) -- and run the fresh-Work
experiment on the next instance, where the corrected composer prevents
the reused-Work refusal entirely. Episode retained; stack stopped.

**Consequence for this claim's experiment plan.** The fresh-Work job-4
run on THIS instance requires a pool change and is therefore blocked
behind that decision; not attempted, per instruction.

**Still open.** The (a)/(b) decision; the publication-base installed
measurement (reachable immediately after either resolution); the routed
policy/source continuity ruling; deferred coverage items (not gates);
source prerequisites; the real Claude pool port/pin/commands.

**Boundaries kept.** No live model, no credential read, no
version-control mutation, no policy repair, no hand release/reset, no
per-Job reset workaround, no instance replaced or reset, no agent
installation; composer + isolation-check edits only.

**Spending this claim.** One FINDING supersession, one composer change
with three new isolation cases (19/19), one restart at unchanged
generation with four settlement polls, two read-only store reads (offer
row, episode row), one stop. Per-command wall-clock unrecorded.

## claim212143 — two Jobs, two Works, one instance: the publication-base boundary measured installed

Owner212133 selected review209517's fresh-deployment alternative
(instance-2026-09-19T12-39-13Z, runtime d5d1e9fb..., authority
117afd1c...; the stalled instance preserved untouched) and asked for TWO
deterministic Jobs with distinct explicit Works. Both ran; the pinned
boundary was reached and measured; nothing repaired.

**Job A (Work 117afd1c-W1).** compose --instance --emitting, pin 1->9
equal, start, submit: all three stages completed, entry integrated,
every allocation released, policy advanced to candidate 784081a4... --
the third complete lifecycle on the corrected runtime, this one in under
a minute of polling.

**Job B (Work 117afd1c-W3 -- the corrected composer's fresh-Work
selection in its first field use).** Stop; compose --job
verification-3 --emitting (fresh W3 + -3 participants); apply (pool
generation 2); pin equal at 24; RESTART over the settled history -- the
D7 path serving again; submit. THE CLAIM SUCCEEDED: the reused-Work
refusal is gone, review209459's correction field-proven. The worker's
turn RAN (emitting image; capture assertions pass on this instance too).

**THE INSTALLED PUBLICATION-BASE MEASUREMENT.** The ending's publication
refuses each tick with the exact pinned precondition: "the worker built
on '93da9d62...' and the Authority target is '784081a4...'; a proposal
is offered against the revision it was built from"
(job3-publication-boundary-212143.json; run-status-212143.json:
implementation answering, review/integration blocked, allocation
reserved). Durable precondition, permanent retention -- the same shape
as the stalled claim, now at the publication gate, exactly where the
source-level coverage said it would land.

**What this establishes for the ruling.** A second independent Job on
one instance passes admission and claim with its own Work and is stopped
exactly and only by the policy/repository divergence of a path-level
import: the policy advances to the candidate commit, the repository and
nominated source never receive it, so the next Job can neither declare
the advanced base nor publish from the old one. The three candidate
resolutions stand pinned in FINDING.md; the choice is routed, not taken.

**State left.** Stack STOPPED; both Jobs' evidence durable (Job A
complete; Job B's retained publication deferral and reserved
allocation); all stores, logs and prior instances untouched.

**Still open.** The routed continuity ruling (now with installed
evidence); the (a)/(b) stalled-episode decision for the PREVIOUS
instance (unchanged); deferred coverage items (not gates); source
prerequisites; the real Claude pool port/pin/commands.

**Boundaries kept.** No live model, no credential read, no
version-control mutation, no policy repair, no hand release/reset, no
per-Job reinstall, no instance replaced or reset, no agent installation,
no product or test edit this claim.

**Spending this claim.** One verify, two composes, two bootstraps, two
pin gates, two starts, two submissions, one complete lifecycle, one
restart proof, six boundary polls, one observed projection retained, one
capture-assertion run, two stops. Per-command wall-clock unrecorded.

## claim212204 — the continuity ruling already existed; the delta was one configuration member

Review212187 found what my three-option ruling request missed: an
APPROVED, IMPLEMENTED decision already covers consecutive-Job continuity.
AMENDMENT-direct-target-finalization-v1.md (owner137905, W133129): the
coordinator delivers the accepted candidate from proved producer custody
and CAS-advances the configured target reference BEFORE Authority
completion -- fenced, exactly my option (b). Implemented in
execution.finalize_direct_target via driver._authority_completed, gated
by Integration._run supplying finalize ONLY when deployment.reconciles()
-- integration_target + integration_workspace + integration_observer all
configured. MY COMPOSITION NEVER SET THE OBSERVER, so every measured
divergence (D5's poisoned successor, claim212143's publication refusal)
ran with the approved finalizer silently disabled. The ruling request is
WITHDRAWN in FINDING.md; nothing was outstanding but configuration.

**Traced and pinned.** The observer is a participant (the reconciled
result's causal-harness runner; W133117 requires it distinct from the
three judges and the integrator); bootstrap passes the member through;
principals_for does not need it (it acts only on reconciled results,
which the deterministic direct path never produces). The finalize operand
set: profile, runner, target_root, the configured reference, and the
line's own path as source.

**Locally proven on the current tree.** The accepted suite's
test_the_direct_integration_finalizes_the_dedicated_target and
test_BOTH_JOBS_REACH_TERMINAL_ON_ONE_TARGET both pass (2 tests OK): two
Jobs, one target, terminal, the reference advancing with the policy.

**The composer configures it now.** OBSERVER = baton.fixture-observer
(deployment-scoped, distinct from every other identity);
bootstrap_inputs carries integration_observer; the observer-configured
composition for a prospective verification-4/W4 validates complete:true,
refused:[] through all six production validators
(compose-212204-observer.log; the regenerated pool-*.json are its
record, NOT applied). 22/22 isolation checks still pass.

**Deliberately not done.** No apply, no restart, no new run on the
current experimental instance: its job-B allocation is reserved at the
publication deferral and a pool change is blocked there by design; the
observer-configured consecutive-Job measurement (second Job rebasing
onto the advanced reference to terminal) belongs to the next
owner-selected experiment. Both experimental instances preserved
untouched.

**Still open.** Owner-selected observer-configured experiment (the
installed measurement of the locally-proven path); the stalled-episode
(a)/(b) decision for the first experimental instance; deferred coverage
items (not gates); source prerequisites; the real Claude pool
port/pin/commands.

**Boundaries kept.** No live model, no credential read, no
version-control mutation, no policy repair, no hand release/reset, no
apply to any instance, no agent installation; composer edit +
documentation only.

**Spending this claim.** One amendment read, one source trace (gate,
finalizer, call site, bootstrap passthrough, principals), two accepted
local tests run, one composer edit, one validated composition, one
isolation-check run. Per-command wall-clock unrecorded.

## claim212295 — the finalizer works installed; the next boundary is one preflight rule

Owner212293's observer-configured experiment ran on the fresh instance
(instance-2026-09-19T13-01-28Z, authority c1b38e2e…), B composed AFTER A
completed, exactly as directed.

**Job A, with reconciles() true for the first time installed.** Compose
`--instance --emitting` (integration_observer in the applied inputs), pin
1→9 equal, start, submit: all three stages completed and released.

**THE AGREEMENT MEASUREMENT — THE HEADLINE.** After A's integration, the
Authority canonical-target policy AND the target repository's main
reference both answer `9a478400…` (ref-agreement-212295.log). The
approved direct-target finalization (owner137905) ran installed: the
coordinator delivered the accepted candidate and CAS-advanced the
reference with the policy. The policy/repository divergence that produced
D5's poisoned successor and claim212143's publication refusal is RESOLVED
BY CONFIGURATION, exactly as pinned in claim212204.

**Job B, composed after A — the exact refusal, where the reviewer's
caveat said it would land.** declared_base() correctly read the ADVANCED
reference; the composition REFUSED at bootstrap.held: "an Authority holds
ONE canonical target and this deployment's Jobs declare 2 different bases
(93da9d62…, 9a478400…)". The preserved COMPLETED Job's binding carries
its historical base; the new Job carries the advanced one; the
document-level single-base preflight cannot express both, and a preserved
Job cannot be dropped. Nothing was applied; the refusal is the recorded
outcome (compose-212295b.log).

**Restart** over A's settled history: history preserved, ZERO new
containers, clean stop.

**The next bounded question, routed not taken**: whether bootstrap.held's
single-base rule should exempt completed/published preserved bindings —
the runtime stores line_declared_base PER binding and publication
compares each worker's base against the CURRENT policy, so the rule's
first-establishment purpose does not obviously extend to historical
bindings. Pinned in FINDING.md for decision.

**State left.** Stack stopped; A's complete evidence durable; B never
applied (refusal only); all prior instances and bindings preserved.

**Still open.** The single-base preflight decision; the stalled-episode
decision (first experimental instance, unchanged); deferred coverage
(not gates); source prerequisites; the real Claude pool
port/pin/commands.

**Boundaries kept.** No live model, no credential read, no manual object
copy, no policy repair, no hand release/reset, no per-Job reinstall, no
version-control mutation, no instance replaced or reset, no agent
installation, no product or test edit this claim.

**Spending this claim.** One verify, two composes (one refused at
preflight — the measurement), one bootstrap, one pin gate, two starts,
one submission, one full lifecycle, one agreement read, one restart
check, two stops. Per-command wall-clock unrecorded.

## claim212385 — the amendment pinned; incremental admission implemented and proven; materialization extension pinned

Owner212383 selected review212328's four-point bounded amendment. This
claim pinned it in FINDING.md before touching code, then delivered points
(1)+(2) and pinned point (3) exactly.

**(1)+(2) Incremental admission, implemented at the pinned scope.** The
distinct-base COUNT rule moved out of the pure `held` (every per-binding
form check stays) into the new store-aware `admissible_bases`, called in
`prepare` immediately after `conflicts` — still before ANY durable
effect, so the no-effects-on-refusal promise is intact. Retained bindings
are the persisted record's own (validated evidence; `conflicts` keeps
refusing their mutation/omission unchanged); a FRESH root keeps the
one-base first-establishment refusal byte for byte; an ESTABLISHED root
admits NEW bindings only when they agree on ONE base equal to the
Authority's CURRENT canonical target, read read-only — stale bases,
divergent new bases, missing stores and unestablished targets refuse by
name with nothing changed.

**Proven.** New class TheEstablishedRootAdmitsNewJobsAtTheCurrentTarget,
5 cases: the ADMITTED case (retained binding keeps its historical base,
new binding at the advanced target, full prepare COMPOSES, and the
established target is not rewound); stale new base refused by name
(naming both revisions); disagreeing new jobs refused; retained-binding
move to the new base still refused by conflicts; fresh two-base still
refused. Suites: test_bootstrap 130 OK (every existing fresh-multi-base,
no-durable-effects and refused-before-authority-opened case passes
against the moved rule); scheduling/sweep/restart/status 170 OK;
test_stage_execution at the recorded 12-error/0-failure baseline.

**(3) Source materialization: NO existing supported path — the exact
extension is PINNED in FINDING.md, not coded.** `materialize` clones from
the nominated source only; the advanced commit exists only in the
dedicated target (measured read-only by the reviewer). Pinned: an
explicit optional `supplement` operand (the deployment's own configured
integration_target, the repository the fenced finalizer wrote), used only
when the declared base is absent after the source clone, fetching exactly
the declared-base commit and refusing anything else; threaded
composition -> create_line -> profile; old attribution untouched; named
paths and tests recorded.

**(4)** The real-topology proof follows (3); accordingly NO new build or
experimental candidate is presented this claim — inputs changed, but a
candidate without (3) would clear admission and stall at materialization,
which is not the proof the owner selected. The snapshot/build/records
follow once (3) lands.

**Boundaries kept.** No live model, no credential read, no
version-control mutation, no policy repair, no hand release/reset, no
instance touched, no agent installation. Product edit: bootstrap.py
held/admissible_bases/prepare per the pinned amendment, with tests.

**Spending this claim.** One amendment pin, one product edit, five new
tests, three suite runs (130 + 170 + baseline), one source trace for the
materialization pin. Per-command wall-clock unrecorded.

## claim212454 — review212438 [R1]: the install-path pre-effect hole closed, proven through the real main

The reviewer's probe was right and the fix is exactly where the probe
pointed. `prepare_repositories` runs BEFORE `prepare` on the install
path, and its structure-before-effects block proved the document with
`held` alone -- so when the distinct-base count moved out of `held`, a
fresh multi-base input could create the destination and reach the clone
runner before anything refused. `admissible_bases` now runs inside that
block, before the mkdir: on a fresh destination there is no persisted
record, so it is the pure one-base first-establishment refusal with
nothing changed. One wrinkle fixed on the way: the install path hands
`tools.instance`'s layout to `prepare_repositories`, which lacks this
module's `configuration` key that `_previous` reads -- `admissible_bases`
now recomputes bootstrap's own layout from the document's state_root, so
both callers use one layout.

**The regression, through the REAL main**
(TheInstallPathRefusesBadBasesBeforeAnyEffect): a fresh two-base input
with --destination, a stand-in runtime for `admit`, worker storage named
under the destination but never created, and a runner that RAISES if
invoked: exit 2 naming "different bases", the destination path does not
exist afterwards, and the runner was never called.

**The held-caller audit.** Exactly two production callers: `prepare`
(followed by `admissible_bases` after `conflicts`) and
`prepare_repositories` (now followed immediately). The dossier composer's
`bootstrap.held` REQUIRED validator is composition-only with no effects;
its readiness claim is narrowed IN THE COMPOSER'S OWN TEXT: complete:true
claims document structure, not base admissibility -- the store-aware
apply is that gate.

**Suites.** test_bootstrap 131 OK (all six admission cases + the new
no-effect regression + every pre-existing protection);
scheduling/sweep/restart/status 170 OK; 22/22 composer isolation checks.
The reviewer's own environment-blocked 130-test failure is noted as not a
product result.

**Still queued, unchanged scope.** The pinned supplement materialization
(3) with its changed-operand/create_line-signature behavior defined
before coding; then the real-topology proof (4), candidate and exact
owner commands; the stalled-episode decision; the real Claude pool.

**Boundaries kept.** No live model, no credential read, no
version-control mutation, no policy repair, no hand release/reset, no
instance touched, no agent installation. Product edit: the one
`admissible_bases` call site plus the layout normalization, with the
regression test.

**Spending this claim.** One product fix (two edits), one regression
test through the real main (three fixture iterations to isolate the
right refusal), one held-caller audit, one composer-claim narrowing,
three suite runs. Per-command wall-clock unrecorded.

## claim212502 — the supplement materialization: operands pinned FINAL, implemented, proven at the profile boundary

Review212486 accepted R1 and directed finishing the authorized scope.
Delivered this claim: the pinned-final operands, the implementation, and
the focused profile proof. Remaining scope is stated exactly below.

**The operands, pinned FINAL in FINDING.md before code.** The supplement
is PROFILE configuration -- `GitCheckpointProfile(runner, *,
supplement=None)` -- never a create_line operand: line identity
(authority, work) and the committed creation signature are UNCHANGED, so
there is no changed-operand replay question; retries replay, recovery
resumes. Custody: the composition threads the deployment's OWN
configured integration_target (the repository the fenced finalizer
writes) at `_profile_of`; no other locator accepted. Behavior: clone
unchanged; detach; ONLY on refusal with a supplement, fetch EXACTLY the
declared-base commit (--no-tags) and detach again; still-absent refuses
naming BOTH repositories. Provenance truthful: source_path stays the
nominated source; the closed {profile, base, head} return is
deliberately unchanged (create_line validates that exact set); the
supplement act is visible in the profile's command stream.

**Implemented**: checkpoint_profiles.py (constructor + materialize) and
tools/stage_execution.py (`_profile_of` threads
given["integration_target"]).

**Proven at the profile boundary with real git**
(TheSupplementDeliversABaseTheSourceDoesNotHold, 4 cases): a base only
the target holds materializes through it (one fetch, closed evidence
shape, HEAD at the base); a base the source holds NEVER touches the
supplement; a base in neither refuses naming both (the exact-commit
fetch's own failure folded into that refusal -- measured, one
iteration); no supplement keeps today's refusal byte for byte. Suites:
checkpoint profiles 19 OK, bootstrap 131 OK, stage_execution at the
recorded 12-error/0-failure baseline.

**REMAINING SCOPE, exactly.** (a) The focused real-topology composed
proof: a variant of the TwoBoundJobsTraverseServingAndCorrection fixture
family whose integration_target is a SEPARATE clone of the source (the
accepted class sets integration_target = source, so B's base is trivially
present and the supplement never fires -- review212328's caveat), with
Job B's task/submission CREATED AFTER Job A reaches terminal, declaring
A's advanced candidate as base, materializing through the supplement,
publishing, reaching terminal, history/cleanup preserved. (b) Then the
coherent candidate inputs (prospective snapshot BEFORE build, build,
records, installer rebind) and the exact owner deployment commands.
Returned at this boundary rather than rushing a half-built composed
fixture into the tree; the turn's remaining budget was the constraint,
and every delivered piece is green.

**Boundaries kept.** No live model, no credential read, no
version-control mutation (test repositories are the suite's own temp
fixtures through its existing subprocess helpers), no policy repair, no
hand release/reset, no instance touched, no agent installation.

**Spending this claim.** One final operand pin, two product edits, four
profile tests with real git (one refusal-shape iteration), three suite
runs. Per-command wall-clock unrecorded.

## claim212569 — review212545 [R2]: absence proved first, causes preserved, invariant justified, provenance qualified

The reviewer's probe was exact and the correction follows it exactly.

**Proved absence before delivery.** `materialize`'s supplement branch now
asks `_present` (rev-parse --verify --quiet <base>^{commit}; runner
closed-shape enforced; nonzero is an ANSWER, not a failure) before
anything else: a PRESENT object re-raises the checkout's own refusal
untouched and never touches the supplement -- the probe's index.lock
scenario (base in BOTH repositories) now propagates the true cause with
ZERO fetches, as a regression test asserts. A failed delivery raises a
named refusal carrying the fetch's cause VERBATIM (unreachable supplement
and commit-lacking supplement are different operator facts -- second
regression, against an empty directory). A detach refusing after a
proved delivery speaks as itself. The in-neither message survives only
for the residual proved-absent-after-successful-fetch defence.

**The recovery invariant, justified without schema change** (pinned in
FINDING.md): the supplement supplies only OBJECTS for one
content-addressed commit, so any supplement that delivers the declared
base delivers byte-identical objects and a changed/replaced supplement
across recovery cannot diverge; objects an interrupted attempt already
fetched persist in the clone, so a recovery with NO supplement completes
whenever the base is present and refuses only when genuinely absent.
Line identity and the committed creation signature never include the
supplement.

**The provenance claim qualified** in FINDING.md: production _git_run
does not persist the command stream -- that visibility is the TEST
seam's recording runner. The durable provenance is the committed line
creation, the clone's own content-addressed git state, and the
deterministic behavior the focused tests prove. No stronger claim.

**Suites.** checkpoint profiles 21 OK (6 supplement cases incl. the two
new regressions); stage_execution at the recorded 12-error/0-failure
baseline; bootstrap 131 OK.

**Remaining scope, unchanged from claim212502's exact statement**: (a)
the composed separate-target A-completes-then-new-B terminal proof
(TwoBoundJobsTraverseServingAndCorrection variant, target as a separate
clone, B created after A); (b) candidate inputs on the reviewed cadence
and exact owner commands; alongside, the final Claude pool.

**Boundaries kept.** No live model, no credential read, no
version-control mutation, no policy repair, no hand release/reset, no
instance touched, no agent installation; product edit confined to the
supplement branch and its helper, with tests.

**Spending this claim.** One probe-directed product correction, one
helper, two regression tests, one existing-assertion strengthening, one
invariant justification, one provenance qualification, three suite runs.
Per-command wall-clock unrecorded.

## claim212616 — review212593: the presence classification completed; query failures are not absence

The reviewer's synthetic probe found the residual R2 gap and both halves
are corrected.

**Complete classification in `_present`**: 0 is present; 1 is the
`--verify --quiet` contract's SPECIFIC absence; every other status --
git's fatal 128 repository/query failure above all -- raises AS a query
failure with its detail preserved, BEFORE any supplemental delivery ("no
supplemental delivery is attempted over a clone that cannot answer").
Every runner field is validated exactly as `_run` validates them --
stdout/stderr must be text, so `stdout=None`/`stderr=[]` refuses at the
contract instead of being read past.

**The residual post-fetch message corrected**: a completed delivery with
a still-absent base claims only what the clone answers -- "what the
supplement holds is not established by this" -- never that the
supplement lacks the object.

**Regressions** (supplement class now 8 cases): a corrupted clone HEAD
drives the real fatal-128 path -- query-failure refusal, no "neither"
claim, ZERO fetches; a lying runner returning stdout=None on the
presence query refuses on the closed contract, ZERO fetches.

**Suites.** checkpoint profiles 23 OK; stage_execution at the recorded
12-error/0-failure baseline; bootstrap 131 OK.

**Remaining scope, unchanged from claim212502's exact statement**: (a)
the composed separate-target A-completes-then-new-B terminal proof
(including interrupted-materialization recovery, history/cleanup); (b)
candidate inputs on the reviewed cadence and exact owner commands;
alongside, the final Claude pool.

**Boundaries kept.** No live model, no credential read, no
version-control mutation (fixtures corrupt their own temp clones), no
policy repair, no hand release/reset, no instance touched, no agent
installation; product edit confined to `_present` and the residual
message, with tests.

**Spending this claim.** One classification correction, one message
correction, two regression tests, three suite runs. Per-command
wall-clock unrecorded.

## claim217230 — the composed fresh-successor proof: three boundaries crossed, one pinned open

(The 212653 claim was interrupted before any work; the owner released it
at 217227 and this claim resumed at 217230. Nothing was lost.)

The owner-selected topology now runs as a composed test
(ANewJobCreatedAfterAFollowsTheAdvancedTarget): Job A alone on a SEPARATE
dedicated target clone; A completes end-to-end and the finalizer advances
THAT repository while the nominated source provably lacks the candidate
(asserted with a nonzero cat-file); the successor B is created only
afterward, on its own Work, declaring the advanced base.

**Measured and crossed, in order.** (1) A stale policy pin defers the
successor's review ending BY NAME ("moved to policy generation 12 from
the configured 11") -- A's own receipts move the Authority, so the
successor composition now reads and pins the CURRENT generation, exactly
the installed re-bootstrap cadence. (2) THE SUPPLEMENT MATERIALIZATION
WORKS COMPOSED: B's line materializes AT THE ADVANCED BASE from a source
that does not hold it -- the extension's purpose, proven beyond the
profile boundary. (3) B's implementation and review COMPLETE on the same
stores with A's history retained.

**The pinned open boundary.** B's integration launch defers every tick
at integration.runtime.prior_runtime_witness: "the coordinator recorded a
grant to attempt <B's own> and this manager holds no such attempt" -- the
conservative coordinator/manager-contradiction refusal. Probed three
ways (deferral row, tick report started rows, first-launch capture): the
deferral is present from the FIRST launch and identical thereafter. The
test is retained under @unittest.expectedFailure with the blocker pinned
in its own text -- the traversal preserved, the suite green
(stage_execution: recorded 12-error baseline + 1 expected failure, 0
unexpected). Next probe pinned exactly: instrument admit_accepted's
prior-grant lookup on the shared target -- whose attempt does the
coordinator consult, and why does the manager hold no runtime row for
it; fixture-sequencing versus product rule deliberately not prejudged.

**Remaining scope.** Resolve the pinned integration-launch boundary and
flip the expected failure to a pass; then candidate inputs on the
reviewed cadence and exact owner commands; alongside, the final Claude
pool. (The interrupted-materialization recovery is covered at the
profile boundary by the recovery-resume clone case and the invariant
record.)

**Boundaries kept.** No live model, no credential read, no
version-control mutation (fixtures clone/commit in their own temp
repositories via the suite's existing helpers), no policy repair, no
hand release/reset, no instance touched, no agent installation, no
product edit this claim (test + composition-pin only).

**Spending this claim.** One composed test built across two phases (one
policy-pin measurement corrected in place), three instrumented probe
runs, one expected-failure pin, two full-suite runs. Per-command
wall-clock unrecorded.

## claim217345 — D8 diagnosed and asserted: the single-slot integration delivery namespace

Review217322's source finding (the witness serves the CURRENT attempt via
execution._unstarted / IntegrationRuntimePort.observed) redirected the
probe, and the diagnosis landed one read later:
**IntegrationDelivery.root joins the integration root with a CONSTANT** --
the attempt id is metadata only, so the delivery namespace is ONE SLOT
per deployment, exactly the deployment-state/integration/integration/
layout every installed instance showed.

**The full chain, now asserted in the test itself** (the expectedFailure
masking removed per the review): B's _published ADOPTS A's retained
delivery (report-and-hold retains it); its published assignment still
names A's integration attempt; _run sees a non-None assignment and SKIPS
port.prepare; no manager attempt row is ever recorded for B; the witness
refuses B's coordinator/manager contradiction every tick. Asserted on
public readers: adopt_delivery answers for ANY attempt id; the published
assignment equals A's attempt and not B's; attempt_runtime_of None for B,
present for A; the launch's deferred outcome carries the exact message.
The A-history/allocation/no-redispatch assertions were MOVED BEFORE the
boundary so they actually run (the review's point), and the class passes
58/58 with the suite at its recorded 12-error/0-failure baseline -- no
expected failure anywhere.

**Consequence pinned**: at most one direct container integration per
deployment lifetime under report-and-hold; the reconciled path never
takes a second delivery (why BOTH_JOBS passes). No weakening of the
missing-runtime refusal is proposed. **Remedy routed, not taken**:
per-attempt delivery roots, or a named refusal/authorized disposition for
a foreign-attempt delivery -- both alter an owned contract beyond this
Work's authority.

**Remaining scope.** The routed D8 decision, then flip the test's
boundary tail to the terminal proof; interrupted-supplement recovery
evidence beyond the content-hash rationale (reviewer's note); candidate
inputs on the reviewed cadence and exact owner commands; the final
Claude pool.

**Boundaries kept.** No live model, no credential read, no
version-control mutation, no policy repair, no hand release/reset, no
instance touched, no agent installation, no product edit -- test and
dossier only.

**Spending this claim.** One source diagnosis (three reads), one test
restructure with six new diagnostic assertions, one class run (58 OK),
one full-suite run. Per-command wall-clock unrecorded.

## claim217457 — D8 implemented at the pinned scope; the fresh-successor proof COMPLETES; candidate built

Owner217455 selected per-attempt collision-safe host delivery namespaces.
Pinned in FINDING.md first (exact paths, legacy compatibility), then
implemented, then the selected outcome proven end to end.

**Implemented.** IntegrationDelivery.root now joins the constant AND the
attempt id (container mount targets untouched); `_legacy` reconstructs
the single-slot shape for adoption only. adopt_delivery: per-attempt
first; else a LEGACY slot (recognized by its `assignment/` child) is
adopted ONLY when its own published assignment names the requested
attempt, answers None for a FOREIGN attempt (retained evidence; the new
attempt materializes beside it, touching nothing), and refuses BY NAME
when unpublished (unaccountable interrupted state). `_delivery_root`'s
inverse handles both shapes. The proving walk is factored
(`_proved_delivery`) and unchanged; predecessor quiescence, fencing and
identity validation untouched. One legacy-shape fixture expectation in
test_execution updated to the per-attempt path.

**Proven.** PerAttemptDeliveriesDoNotCollide (runtime level, 4 focused
cases): distinct roots side by side, each adopting back as itself;
legacy identity-proved adoption; foreign-legacy retained-not-adopted
with the new attempt materializing beside untouched bytes; unpublished
legacy refusing by name. THE SELECTED OUTCOME:
ANewJobCreatedAfterAFollowsTheAdvancedTarget now runs the FULL
fresh-successor topology to completion -- A completes on the separate
dedicated target, B (created after, own Work, advanced base via the
supplement) launches its OWN integration, runs its real turn over the
dedicated target, COMPLETES, the target advances again to B's candidate,
and both retained deliveries adopt back as themselves; A's history,
allocations and no-redispatch asserted before and after. (The turn
helper gained an overridable target root for separate-target cases; the
accepted same-tree default unchanged.)

**Suites.** stage_execution at the recorded 12-error/0-failure baseline
with the successor proof passing; integration 376 OK (+4);
scheduling/sweep/restart/status 170 OK; checkpoint profiles 23 OK;
bootstrap 131 OK.

**The candidate, on the reviewed cadence.** /2 prospective snapshot
BEFORE the build (109 inputs, 55063205...); just build -> executable
sha256:07aed036..., 81-file bundle f0bc5ee9...
(RUNTIME-BUILD-217457.json, BUNDLE-MANIFEST-217457.json,
build-runtime-217457.log); install-next-instance.sh binds these records.
EXACT OWNER COMMANDS, unchanged shape: cd <dossier>;
./install-next-instance.sh; then ./verify-next-instance.sh and its
printed steps (compose --instance --emitting, apply, pin gate, start,
exact submission).

**Still open.** Independent review of D8's implementation and this
candidate; the owner's next experimental deployment measuring the
successor topology installed; interrupted-supplement recovery evidence
(profile recovery-resume case stands; composed evidence pending); the
final Claude pool port/pin/commands.

**Boundaries kept.** No live model, no credential read, no
version-control mutation (fixtures in their own temp repositories), no
policy repair, no hand release/reset, no instance touched, no agent
installation. Product edit: integration/runtime.py delivery derivation +
adoption and oci_delivery's inverse, per the pinned scope, with tests.

**Spending this claim.** One pin, two product files edited, four
runtime-level tests plus one fixture-path update, the composed proof
completed (two turn-root iterations, one legacy-fixture iteration), a
five-suite regression sweep, one prospective snapshot, one build, one
bundle manifest, one installer rebind. Per-command wall-clock
unrecorded.

## claim217574 — review217558 R3/R4 closed: derived leaves, managed ancestors, dual-layout and identity validation; candidate rebuilt

Both probe-proven defects corrected at their exact sites.

**[R3] Safe collision-safe identity derivation with an unambiguous
inverse.** The per-attempt path component is now `delivery_leaf` = the
attempt id's sha256 -- fixed 64-lowercase-hex, no separator, no
traversal, no reserved name, collision-safe by content hash, never equal
to any layout constant; the id itself travels as metadata and inside the
published assignment, where identity is validated. Per-attempt
deliveries live under a SEPARATE managed ancestor
(`integration-deliveries`), never inside the legacy slot's own name, so
`_delivery_root`'s inverse is ONE basename comparison (legacy constant →
dirname; deliveries constant as parent → two dirnames; anything else
refuses by name).

**[R4] Managed descriptor-proved ancestors.** Creation refuses a linked
or foreign-typed ancestor by name and establishes it at mode 0o700;
adoption proves the ancestor with the descriptor walk FIRST and opens
the leaf RELATIVE to it (`_proved_delivery(..., within=)`), so a symlink
at either level is refused rather than followed.

**Pinned and enforced beyond the letter of the probes**: the DUAL-LAYOUT
same-attempt ambiguity refuses by name (a per-attempt delivery AND a
legacy slot whose published assignment claim one attempt is a
contradiction between layouts, never resolved by preference); NEW
adoptions validate identity too (a namespace whose published assignment
disagrees with its derived identity refuses -- tamper is not a
delivery).

**Proven.** Four new regressions in PerAttemptDeliveriesDoNotCollide
(class 30 OK): hostile ids (traversal, absolute, separators, layout
constants) stay under the ancestor with six distinct 64-hex leaves; a
linked ancestor refuses for BOTH creation and adoption; dual-layout
same-attempt refuses; a renamed (tampered) namespace refuses on the
identity check. Two legacy-shape fixture expectations updated to the
derived-leaf path. FULL SWEEP: integration 402 OK; stage_execution at
the recorded 12-error/0-failure baseline WITH the composed
fresh-successor proof passing unchanged; scheduling family 170 OK;
bootstrap + checkpoint profiles 154 OK.

**The candidate rebuilt as required** (07aed036 not accepted, preserved
as history): FRESH /2 snapshot BEFORE the build (109 inputs,
d6a68357...); executable sha256:9d26430e..., 81-file bundle a98c5730...
(RUNTIME-BUILD-217574.json, BUNDLE-MANIFEST-217574.json,
build-runtime-217574.log); install-next-instance.sh binds these
records; owner commands unchanged in shape.

**Still open.** Independent review of R3/R4 + this candidate; the
owner's next experimental deployment measuring the successor topology
installed; composed interrupted-supplement recovery evidence; the final
Claude pool port/pin/commands.

**Boundaries kept.** No live model, no credential read, no
version-control mutation, no policy repair, no hand release/reset, no
instance touched, no agent installation. Product edits confined to the
delivery derivation/ancestors/adoption and the inverse, per the pinned
scope, with tests.

**Spending this claim.** Two product files edited (leaf derivation,
ancestor management, dual-layout + identity checks, inverse), four new
regressions plus two fixture updates, a full five-suite sweep, one
fresh snapshot, one build, one manifest, one installer rebind.
Per-command wall-clock unrecorded.

## claim217672 — review217641 R4 creation custody closed: descriptors held through creation and every later use; candidate rebuilt

Review217641 accepted R3 and proved two creation defects with probes
(REVIEW-PROBE-217641.json): an existing managed ancestor at 0777 was
ACCEPTED, and a rename+symlink injected between the ancestor check and
the leaf creation redirected the whole delivery into the replacement
tree. Both closed at their sites, plus the requested reopen audit.

**Creation is custodied** (`materialize_delivery` rewritten). The
deployment root is opened and HELD; the managed ancestor is established
with `mkdir` RELATIVE to that descriptor or, when it already exists,
proved at exactly `DELIVERY_DIR` — a moved mode REFUSES and is never
repaired. Every descendant (leaf, assignment, result) is made with
`mkdir(dir_fd=held parent)`, opened back `O_NOFOLLOW` relative to the
SAME held parent, and finished on the OPENED object — `fchmod` for the
mode (umask-independent, and a custody proof: finishing somebody else's
directory refuses), `fchown` for the result namespace's configured
group, in `adopt_workspace_group`'s own order. There is no second
lookup of a checked pathname between any check and any effect.

**The return path is validated.** Before the capability is handed out,
the pathname it carries is re-walked through the same proof every later
use repeats, and the walked object must be dev/ino-identical to the
namespace just created — a replacement directory of the right shape
with a replica leaf still refuses ("no longer identifies").

**Later pathname reopens are audited out** (the requested adoption
audit, applied everywhere). New `_opened_root(delivery)` repeats the
FULL proved walk — each managed component opened `O_NOFOLLOW` relative
to the previously held descriptor at its established mode — and every
later read and write now goes through it: `published_assignment` and
`observed_delivery`'s two reads via `_namespace_read` (fresh walk per
read; absence anywhere is the ordinary None, wrong shape refuses);
`publish_assignment` holds ONE namespace descriptor across its
existing-check, staging, link and read-back (`_read_bounded` and
`_publish_once` now take a held descriptor, all operations
`dir_fd`-relative); and `oci_delivery`'s three binding-document sites
(publish+read-back under one held root, both recovery reads) walk the
same way. The capability carries its deployment root and layout so the
walk can always be repeated; fixed container mounts, target fences and
runtime guards untouched.

**Proven.** Four new focused regressions (class now 34 OK): the
0777-ancestor probe refuses for BOTH creation and adoption with the
mode left unrepaired; the reviewer's exact rename+symlink injection
fired immediately before the leaf mkdir redirects NOTHING (replacement
tree stays empty) and no capability is returned; a right-shaped
replacement DIRECTORY with a replica leaf refuses on the dev/ino
return-path validation; a pathname re-pointed AFTER adoption refuses on
the next read. All earlier identity/legacy/dual-layout/hostile-id tests
pass unchanged. SWEEP: integration 775 OK (test_runtime 132,
test_driver 112, plus execution/recovery/coordinator/managed/
reconciliation 663-strong block); tests.integration.test_admission
carries 11 pre-existing fixture-level failures in modules this claim
did not touch (git shows admission.py/manifests.py/test_admission.py
unmodified; the error is a store-fixture AttributeError, no delivery
involvement) — recorded, not repaired, out of pinned scope;
stage_execution at the recorded 12-error/0-failure baseline including
the composed fresh-successor proof; job_manager full family 883 OK;
bootstrap 131 OK; checkpoint profiles 23 OK.

**The candidate rebuilt as required** (9d26430e not accepted, preserved
as history): FRESH /2 snapshot BEFORE the build
(PROSPECTIVE-INPUTS-217672.json, 109 inputs, 01753be0...); `just build`
exit 0; executable sha256:7c3e5db2...; 81-file bundle 780059ae...
(RUNTIME-BUILD-217672.json — supersedes names 9d26430e by its FULL
digest — BUNDLE-MANIFEST-217672.json, build-runtime-217672.log);
install-next-instance.sh rebound to these records, `bash -n` clean, and
the installer's own pre-check replayed against the bundle on disk.
Owner commands unchanged in shape.

**Still open.** Independent review of the R4 custody work + this
candidate; the owner's next experimental deployment measurement;
composed interrupted-supplement recovery evidence; sequential-Job
recovery/history/cleanup evidence; the final Claude pool
port/pin/commands; the owner's stalled-episode (a)/(b) decision.

**Boundaries kept.** No live model, no credential read, no
version-control mutation, no policy repair, no hand release/reset, no
instance touched, no agent installation. Product edits confined to
delivery creation/walk/read/publish custody in runtime.py and
oci_delivery.py's binding sites, per review217641's pinned scope, with
tests.

**Spending this claim.** Two product files edited, four new regressions
plus two adapted `_publish_once` test call sites, a five-suite sweep
plus the driver family, one fresh snapshot, one build, one manifest,
one installer rebind with pre-check replay. Per-command wall-clock
unrecorded.

## claim219702 — installed A completes on the owner's instance; B surfaces D9 (pool cannot advance over a held episode); D9 fixed, candidate rebuilt

Owner219700: candidate217672 installed as
instance-2026-09-20T09-21-58Z; proceed with installed
A-completes-then-new-B on the SAME deployment, distinct Works, advanced
source materialization, separate delivery roots; apply review217777's
OCI fixture correction; return installed results.

**The OCI fixture correction applied exactly** (non-gating, assertion
unchanged): `above = self.delivery.deployment_root` replaces
`dirname(delivery.root)` — the reviewer's own replay operand — so the
containing-target scenario reaches the intended "two container paths"
overlap refusal instead of the managed ancestor's mode refusal.
tests.manager.test_oci_integration: 78 OK.

**Job A, COMPLETE INSTALLED on the accepted candidate** (verify
identity matched 7c3e5db2...; authority cf13a9d3, Work cf13a9d3-W1,
job w202663-deterministic-verification-2): compose --instance
--emitting, pin gate 9=9, start, submit; all three allocations
released (implementation/review `cleanup-retained`, integration
`integration-completed`), policy 9→10 at 09:25:13Z, canonical target
advanced 93da9d62→eaa758bc AND refs/heads/main agrees, capture
assertions all pass (nonempty retained streams, deterministic lines),
and the R4/D8 layout live: managed `integration-deliveries` ancestor
at mode 700 with exactly A's one 64-hex leaf
(run-status-A-219702.json).

**Job B (verification-3, W3) reached the advanced base and surfaced a
FIXTURE limit.** Composed AFTER A completed: its task declared
eaa758bc (call-time D5 default read the advanced target), and the
SUPPLEMENT materialized the line checkout AT eaa758bc — the first
installed field proof of the claim212502/212616 materialization; the
nominated source never carried that commit. The worker then faulted in
162ms: eaa758bc IS A's integrated candidate commit, so the fixture's
FIXED file staged nothing and `git commit` exited 1
(`ending: faulted, fault_code: agent`). The PRODUCT classified the
episode `exceptional` through the observing status and HELD the
reservation without redispatch — report-and-hold retaining evidence,
exactly its contract
(run-status-verification3-exceptional-219702.json). Fixture corrected
in the dossier: candidate name/line are now task-id derived in BOTH
the composer's task/verification and `proposing_agent` (deterministic
per assignment, distinct across Jobs; legacy name kept for tasks
carrying no id). Composer isolation checks pass.

**The composer's pool-generation prediction was two-state and stale on
the third compose** — `2 if store exists else 1` predicted 2 while
activation would mint 3; the gate refused with nothing written. It now
reads the durable pool and applies the scheduler's mint rule
(`_pool_generation_prediction`); the third apply then took generation
3 in deployment.json and the pin gate passed.

**D9, the product defect, measured installed and pinned** (FINDING.md):
with verification-3's reservation HELD at generation 2, starting the
generation-3 deployment refuses — `scheduler.PooledManagerOperations`
requires the active generation AND live prior generations' (generation,
worker id) pairs (`_required_workers` counts `reserved` and
`recovery-required`), but `tools/stage_execution.operations_from`
attached ONLY the active generation. So a pool can NEVER advance over
exactly the held episodes report-and-hold exists to retain. Activation
itself succeeded; attachment refused after it, before any operation.

**D9 corrected at the measured boundary.** New
`_attached_workers(job_store, generation, workers)` builds the
attachment map from the scheduler's own required set: every live prior
pair attaches the SAME-NAMED worker's operations (D7/review209188:
workers are not interchangeable; only its own context reads its
history), and a live prior pair whose worker is no longer composed
refuses by name before anything runs. Two focused regressions in the
scheduling family (a live prior pair attaches the same-named worker's
operations under both keys; a no-longer-composed worker refuses by
name); the stale D7-class docstring sentence calling the old refusal
"correct" is superseded in place. SWEEP: job_manager 885 OK (incl. the
two D9 cases), stage_execution at the recorded 12-error/0-failure
baseline, runtime+OCI+bootstrap 341 OK.

**Preserved and verified across two restarts:** A's settled history
byte-stable (same allocations, same release reasons, no re-execution —
no new episodes appeared in any poll), verification-3's held episode
retained un-redispatched, every instance and store untouched, no
manual release. Final state recorded (run-status-final-219702.json): A
settled; verification-3 held `reserved`/exceptional; verification-4
queued — it needs the D9-corrected runtime to serve.

**The candidate rebuilt on the reviewed cadence:** fresh /2 snapshot
BEFORE the build (PROSPECTIVE-INPUTS-219702.json, 109 inputs,
67910cc7...); executable sha256:a6dbd963...; 81-file bundle
7da17402... (RUNTIME-BUILD-219702.json — supersedes the INSTALLED
7c3e5db2 candidate by full digest, which stays preserved with its
instance since D9 was measured ON it — BUNDLE-MANIFEST-219702.json,
build-runtime-219702.log); install-next-instance.sh rebound, bash -n
clean, pre-check replayed green. Owner commands unchanged:
`cd <dossier>; ./install-next-instance.sh; ./verify-next-instance.sh`.

**Bearing on the 24-hour gate** (FINDING 2026-09-20T09:32:05Z): the
A-then-B flow on ONE persistent deployment is now blocked only by D9
on the installed runtime; with the corrected candidate installed, the
same deployment shape (A complete → B at the advanced base with the
task-derived fixture) is composed and ready to run. The separately
authorized real Claude Job remains unstarted and unauthorized here.

**Still open.** Independent review of D9 + the fixture/composer
corrections + this candidate; owner installation of the corrected
candidate and the re-run of A-then-B to completion; the held
verification-3 episode's disposition (owner, same class as the
stalled-episode decision); interrupted-materialization recovery
evidence; the final Claude pool port/pin/commands; the real Claude Job
authorization.

**Boundaries kept.** No live model, no credential read, no
version-control mutation, no policy repair, no manual release/reset,
no instance replaced or reset, no agent installation. Product edit
confined to the D9 attachment boundary; fixture/composer edits
dossier-scoped; the installed instance received only starts, stops,
composes, submissions and reads.

**Spending this claim.** One OCI fixture correction, one verify, three
composes, three bootstraps, three pin gates, three starts, two
submissions, one complete installed lifecycle (A), ~40 status polls,
one faulted-turn diagnosis to root cause, one D9 product fix with two
regressions, three suites re-run, one fixture + one composer
correction, one fresh snapshot, one build, two records, one installer
rebind, two stops. Per-command wall-clock unrecorded.

## claim219950 — review219927 closed: the corrected fixture DELIVERED in rebuilt images, proved on the images themselves, exact owner commands prepared

Review219927's finding was exact: the task-derived candidate lived in
`fixture-context/worker/proposing_agent.py` and in NO artefact -- the
composer pinned the immutable historical images (emitting e48e72df...,
silent 6ae290f9...), whose Dockerfiles COPY the fixture bytes at BUILD
time. Editing the host file and rebuilding the host runtime changed
nothing any container launches.

**Both consumers of `ProposingAgent` rebuilt from the corrected
context.** The exact COPY inputs of both recipes were recorded BEFORE
the builds (FIXTURE-IMAGE-INPUTS-219950.json, 12+13 files, context
digest bec3a2bf...). `docker build` from `fixture-context/`: silent
producer sha256:3c43c4e3..., emitting producer sha256:4638bae6...;
the corrected agent's byte-identity verified INSIDE each new image
(sha256 of /opt/baton/proposing_agent.py equals the checkout's; the
historical e48e72df image measurably still carries the OLD bytes). The
integrator copies `importing_agent.py`, not `ProposingAgent` -- read
from its recipe, unchanged. FIXTURE-IMAGES-219950.json binds each new
digest to its recipe, its inputs record, its proof, and the historical
digest it supersedes; historical images, bindings and instances all
preserved (every already-bound Job keeps the image it was bound to).

**Proved ON THE IMAGES, in the review's exact shape.**
`test-image-task-derivation-219950.py` runs INSIDE the image under its
own fixed uid (no network; one mounted staging directory): two `work`
turns with distinct task ids, the SECOND on a line whose head IS the
first turn's output -- the successive-Job shape that faulted installed.
Both producer images pass: each turn commits exactly its task-derived
file with exact content, the second commit based on the first head
(IMAGE-TASK-DERIVATION-EMITTING-219950.json and
-PRODUCER-219950.json).

**Composer pins updated coherently.** PROVIDER_IMAGE and
EMITTING_IMAGE now name the rebuilt digests, with the claim207111 and
claim208916 digests retained in place as recorded history; composer
isolation checks pass. The host candidate is UNCHANGED -- review219927
independently established a6dbd963.../7da17402...'s identity, no host
build input moved this claim, so no rebuild (the reviewer's own rule).

**Exact owner commands prepared** (OWNER-RUN-219950.md): install +
verify the corrected instance, Job A (`--job verification-1
--emitting`) through compose/apply/pin/start/submit with the poll and
capture commands, then Job B (`--job verification-2 --emitting`)
composed AFTER A on the SAME deployment -- B's task declares A's
advanced base, materializes through the supplement, and proposes its
own task-derived file so the successive base stages a real change --
and the four separate completion checks (A history, ref agreement
twice, per-attempt delivery leaves, cleanup-with-retention). Job
suffixes are numeric because `select_job` requires them.

**Preserved untouched:** instance-2026-09-20T09-21-58Z, its held
verification-3 episode and queued verification-4 (owner disposition),
every historical image and record. The `--job` composition on the new
pins was NOT run against any instance this claim -- pool-*.json still
record verification-4 as bound.

**Still open.** Independent review of the image delivery + proofs +
pins + commands; the owner's install and A-then-B run (the 24-hour
gate's first criterion; deadline 2026-09-21T09:32:05Z); installed
complete recovery evidence; held-episode disposition; final Claude
pool; the separately selected/authorized real Claude Job.

**Boundaries kept.** No live model, no credential read, no
version-control mutation by this agent (the proof's git acts inside
the container on its own staged line), no product/test source edits
this claim, no instance touched, no manual release/reset, no assertion
weakened.

**Spending this claim.** One inputs snapshot, two image builds, three
in-image byte-identity checks, two in-image two-task proofs, one
binding record, two composer pin edits, one isolation-check run, one
owner-commands document with one suffix correction. Per-command
wall-clock unrecorded.

## claim220080 — the directed A-then-B run: A completes, B's implementation and review complete at the advanced base, and D10 stops B's integration both ways

Owner220078 directed executing OWNER-RUN-219950.md on the freshly
installed instance-2026-09-20T10-23-11Z (runtime identity verified
a6dbd963 = the D9-corrected candidate) under review219992's evidence
qualifications.

**Job A (verification-1, Work e89219fb-W1): COMPLETE in ~55s** with the
corrected emitting image 4638bae6. All three allocations released
(cleanup-retained ×2, integration-completed); policy 9→10; canonical
target AND refs/heads/main agree at 4a424f0c whose commit adds exactly
`w197661-fixture-verification-1.txt` — the task-derived candidate's
first installed lifecycle. Capture assertions green. Per
review219992: A's explicit attempt and stream locators with sha256
digests preserved BEFORE B (A-LOCATORS-220080.json,
run-status-A-220080.json).

**Job B (verification-2, fresh Work W2, composed after A): the
advanced-base path WORKED end-to-end through review.** Task declared
4a424f0c; the supplement materialized B's line AT it; the corrected
fixture proposed `w197661-fixture-verification-2.txt` (a real change
over the base carrying A's file — the exact shape that faulted last
time); implementation and review both completed and released with
retained streams; checkpoint 4a424f0c→4863888a frozen, verdict
accepted, integration eligibility recorded at 10:26:28Z.

**D10, measured BOTH ways and pinned** (FINDING.md;
D10-EVIDENCE-220080.json): B's integration cannot proceed under any
configuration. With per-Job integrators retained, launch defers every
tick — "this deployment names 2 integration workers; one deployment
names one integrator" (`integration_served`; found via `serve --once`
after the deferral was SILENT in stores — no deferral row, no log
line). With one integrator composed, the manager dies at the first
sweep — `worker_for` refuses observing verification-1's SETTLED
integration history ("...which this deployment does not configure"),
the D7 defect class alive in the configuration-level resolver. Two
resolutions pinned and ROUTED (constant integrator identity from the
first Job — the forward shape, moving the per-Job-actors rule for the
integration role; and/or worker_for adopting D7's settled-history
rule — a product change); neither taken here because each moves a
pinned rule.

**Composer corrections kept from the attempt, gate-proven:** the
pool-generation prediction now compares the WHOLE composed membership
(ids/lanes/participants) against the active generation's rows (a
removal-shaped change is invisible to the old presence check), and the
policy-pin repeat model carries the new measurement (+15 = 7×2+1
adding a job; +13 = 7×2−1 re-applying two) — the pin gate then went
green three consecutive times (63, 76, 89). The one-integrator
composition attempt is retained in `prepared_workers`' docstring as
the D10 pin; the filter itself is reverted so compositions stay
startable-shaped.

**A restoration boundary measured honestly:** the one-integrator apply
overwrote deployment.json, and `pool_generations.document` retains
only the scheduler's NORMALIZED worker rows — verification-1-
integration's full deployment entry is not recoverable from durable
records, and recomposing it today would re-derive against the advanced
base (the rewrite this dossier must not perform). No manual repair.

**State left, preserved:** the instance with all stores/evidence; A
complete (locators pinned); B implementation/review retained,
integration allocation reserved on verification-2-integration; stack
STOPPED, currently refusing start at the worker_for gate — loud and
named (manager-log-D10-220080.txt; run-status-final-220080.json).
Prior instances, held verification-3 and queued verification-4 on the
09-21-58Z instance untouched.

**Bearing on the 24-hour gate:** A-then-B now completes through
REVIEW at the advanced base on one deployment; the sole remaining
boundary is D10 at integration, with the resolution choice routed.
With (a)+(b) selected, a rebuilt candidate and one fresh install, the
composed run finishes the first criterion; the useful real Claude Job
(second criterion) remains to be selected and separately authorized.

**Still open.** The D10 resolution ruling; its implementation + tests
+ candidate on the reviewed cadence; the re-run; the held
verification-3 and stalled-episode dispositions; interrupted-
materialization recovery; final Claude pool port (which should adopt
the constant-integrator shape); the real Claude Job selection and
authorization before 2026-09-21T09:32:05Z.

**Boundaries kept.** No live model, no credential read, no agent Git
mutation, no product/test source edits, no manual repair/reset, no
per-Job reinstall, no instance replaced; every instance and all
evidence preserved.

**Spending this claim.** One verify, five composes, five bootstraps,
five pin gates (two refusals caught by the gate, three greens), three
starts (one clean, two refused loudly), two submissions, one complete
lifecycle (A), one B implementation+review lifecycle, ~35 status
polls, one `serve --once` diagnostic, two integration-store and three
control-store inspections, one D10 diagnosis both ways, one
restoration attempt stopped at the durable-record boundary, four
dossier records, one FINDING pin. Per-command wall-clock unrecorded.

## claim220329 — the owner's PR model mapped: the first durable reviewed candidate demonstrated, PR-mode composition validated, the continuity gap pinned, the real Claude Job proposed

Owner220327 selected the PR-producing model
(OWNER-HANDOFF-PR-JOBS-2026-09-20T11-02-49Z.md): Jobs deliver durable
REVIEWED candidates; Slawomir merges; the accepted commit is the next
base; automated integration and review220212's stable-integrator
proposal are NOT required (that review preserved as history).

**1. The reviewed-candidate handback demonstrated from durable
records** (CANDIDATE-PR-220329.json). verification-2 on the stopped
instance IS the PR contract, read-only from its stores: commit
4863888a over base 4a424f0c, changed paths
[w197661-fixture-verification-2.txt], patch/bundle/result/verification
in the line's proposal tree with test status 0, and the independent
reviewer's durable ACCEPTED verdict (verdict-23cac7cc, checkpoint
d59b63a3). Its reserved integration stage is explicitly NOT
represented as complete. OWNER-PR-FLOW-220329.md carries the exact
inspection commands (git show/patch/result/verdict query), a
scratch-clone re-run of the candidate's own test, the bundle-transport
acceptance commands (Slawomir only), and the accepted-base record
shape.

**2. PR-mode composition implemented and shape-validated.** `--pr` in
the verification composer: TWO stages (implementation → review), TWO
workers per Job, no integration worker or stage. Composed against the
retained instance through the composer's full validators (complete:
true; stages and workers verified two-and-two); the dossier's
verification-2 documents restored afterwards so the recorded bound
state stays exact; nothing applied to any instance. On a fresh
PR-mode deployment the D10 gates have nothing to bind to (no
integration allocations exist). Honest limit: the review-terminal
Job-completion semantics are validated on paper; the installed
PR-mode run on a fresh instance is the outstanding proof and needs no
new candidate (no host source changed this claim; a6dbd963 stands).

**3. The accepted-base continuity gap pinned with its bounded
correction** (FINDING.md): `bootstrap.admissible_bases` admits new
bindings on an established root only at the CURRENT canonical target,
which nothing advances in the PR model — so today the demonstration
path is a fresh install seeded at the accepted base, and the pinned
correction is one operator-facing tools verb advancing the canonical
target and dedicated target ref to the owner-accepted commit with the
acceptance record as receipt (contract/paths/acceptance to pin before
any edit).

**4. The real Claude Job proposed for separate authorization**
(REAL-JOB-PROPOSAL-220329.md): the recorded worker-add task BOUNDED to
one `add-worker` verb in a new tools/pool.py with its own
tests + the bootstrap family as verification; exact scope paths, base
selection, claude credential-slot binding, independent Claude
reviewer, and the exact launch command sequence. Nothing launches; the
tradeoff against a smaller task is stated.

**Still open.** Independent review of this mapping; the installed
PR-mode A-then-B (fresh install, owner deploys; then a new Job at the
human-accepted base — via fresh seed today, via the pinned transition
once implemented); the accepted-base verb's pin-then-implementation;
owner authorization of the real Claude Job; D10's product half
(worker_for settled-history) now non-gating but pinned; held
verification-3/stalled-episode dispositions; deadline
2026-09-21T09:32:05Z.

**Boundaries kept.** No live model, no credential read, no agent Git
mutation, no product/test source edits, no instance touched (compose
validation wrote and restored dossier documents only), no manual
repair, every prior record preserved.

**Spending this claim.** Three durable-store reads, one candidate
record, one owner-flow document, one composer PR mode with one
shape-validation compose (documents restored), one real-Job proposal,
one FINDING pin. Per-command wall-clock unrecorded.

## claim220385 — review220364 items 2 and 3 delivered; the accepted-base verb pinned in full; items 1-impl and 4 returned with exact scope

**[3] Supported candidate readout DELIVERED and proven.**
`read-candidate-220385.py`: `ControlStore.open_readonly` (never
initializes or changes the store) plus `review_cycles`' public PROVING
readers — `line_of`, `checkpoint_of`, `verdict_of` — replacing the
policy-incompatible SQL recipe in OWNER-PR-FLOW section 1. Run against
B's candidate: checkpoint 4a424f0c→4863888a frozen, verdict accepted
by baton.fixture-reviewer-2, line accepted — the same facts, through
surfaces that prove them against the committed acts. The REMAINING
logged gap is narrower and explicit: no supported work-id→identities
LIST surface (identities come from the Job status projection or the
retained candidate record); the bounded read-only exposure stays
pinned.

**[2] The Claude pool composition is now actually selectable and the
task is actually bounded.** compose-pool-207219.py: `__main__` passes
argv; `select_instance` (ported from the reviewed verification
composer) reads the destination's own persisted identity;
`select_pr` composes coder+reviewer only. The task bytes now REQUEST
the bounded task: one `add-worker` verb in NEW tools/pool.py, tests in
NEW tests/tools/test_pool.py, exactly two allowed paths, bootstrap's
worker rules preserved, `tests.tools.test_pool` +
`tests.tools.test_bootstrap` as the verification gate. Validated with
`write=False` against the retained instance (no document written, no
instance touched): two-role manifests and images compose
(implementation d717878b..., review c40d174c...);
`bootstrap.held` refuses on that OCCUPIED root — it already holds
Jobs the pool document does not name — and the fresh-instance
validation is an explicit step of the authorized run before start.
REAL-JOB-PROPOSAL updated: launch flags real, and the enforceable
limits stated exactly (one episode per stage by construction under
report-and-hold with recovery unauthorized; provider_turn 3600s;
verification_command_seconds bounds), so the promised one-producer-
one-reviewer spend is the deployment's own hard bound.

**[1] The accepted-base transition pinned IN FULL** (FINDING.md):
contract (tools/accepted_base.py `record`, operator-run, acceptance
document with expected_old), effect in the finalizer's own order with
the located surfaces (fetch-prove into repo/target.git under operator
invocation → CAS the reference from expected_old →
`Authority.set_policy("canonical_target", ...)` core.py:188 → receipt
under accepted-bases/), the review's exact acceptance list (identity
proof, expected-old, idempotent replay, conflict refusal without
touching state, interruption resume, no fabricated integration
receipt), tests one-per-bullet, new-files-only ownership,
`admissible_bases` unchanged. Implementation is the NEXT claim's
first item; nothing else blocks it. Fresh-install-per-base language
in OWNER-PR-FLOW section 5 stands only as the gap explanation, per
the review.

**[4] PR-mode terminal proof NOT delivered this claim** — returned
with exact scope: a composed two-stage lifecycle test with
deterministic providers (impl completes → review completes → Job's
terminal report-and-hold state named, restart, no redispatch),
then the owner-deployed PR-mode experiment; no new candidate build
required (no host source changed; a6dbd963 stands).

**Still open.** Items 1-impl and 4 (next claim, in that order); the
work-id→candidate list exposure; owner authorization of the real Job;
the installed PR A-then-B + accepted-base continuation (gate
criterion 1); deadline 2026-09-21T09:32:05Z.

**Boundaries kept.** No live model, no credential read, no agent Git
mutation, no product/test source edits, no instance touched (readout
read-only; pool validation write=False), no SQL against stores (the
readout replaced it), no manual repair.

**Spending this claim.** One readout script with two runs (one
clock-grammar correction), one OWNER-PR-FLOW section replacement, one
compose-pool port (argv/select_instance/select_pr) with one bounded
task rewrite and one write=False validation, one proposal update, one
full contract pin. Per-command wall-clock unrecorded.

## claim221639 — the accepted-base transition IMPLEMENTED per review220421's amended contract; candidate rebuilt

(Resumes the interrupted claim220434; the owner released it untouched
and no new instruction arrived between.)

**The Authority operation** (`accept_base`, authority/core.py, with the
api delegation): `integrate`'s stale-target door applied to the HUMAN
transition — ONE operation identity, `signature_of("accept-base",
{acceptance})` bound to the FULL immutable document, the expected-old
check INSIDE the committed `_replay` body, `set_policy` only within
it, replay answering the committed result with NO second policy bump.
A target already AT the accepted commit under a DIFFERENT operation
refuses by name — nothing synthesizes an acceptance from a
coincidentally agreeing value. Document validation refuses missing
members, a wrong schema, non-40-hex commits, and accepted==expected
(moves nothing). Registered on the CONFIGURATION face with the
boundary tests' enumerations updated (a session must not carry it),
and every refusal message bounded per the diagnostic rule.

**The operator tool** (`tools/accepted_base.py`): one invocation under
an EXCLUSIVE lifecycle flock (the same lock the stack serializes
under — a running stack or competing operator refuses; the stopped-
instance boundary is enforced, not assumed); durable byte-proved
INTENT before any effect (a changed document under one identity
refuses); the accepted commit fetch-proved into the deployment's own
target.git (absent-object rc-128 classified as the ordinary miss,
strict recheck after the fetch); reference compare-and-swap via
git's own `update-ref old new` (already-at-accepted is the resume
path; any other value refuses touching nothing); the Authority
transition; the receipt staged and `os.replace`d atomically, the
intent finalized away. Receipt-present invocations validate byte
provenance and answer success touching nothing.

**Nine focused tests** (`tests/tools/test_accepted_base.py`), one per
pinned boundary: advance+receipt with exactly ONE policy bump;
replay bumps nothing and leaves the receipt byte-identical; changed
document under one intent identity refuses; moved canonical target
refuses leaving the foreign value standing; foreign reference refuses
before any write (a third commit at main, everything untouched);
interruption-after-reference resumes and completes; interruption-
after-Authority finalizes the missing receipt WITHOUT a bump;
coincidentally agreeing target synthesizes NO receipt; a held
lifecycle lock refuses the whole invocation. All 9 OK.

**Sweep.** tests/authority 388: 3 failures, ALL pre-existing committed
baseline (`open_readonly` on the api surface and two store.py
diagnostic-registry entries — git shows store.py unmodified; my
accept_base sites appear in NEITHER list after the bounded-message
rewrite); tools.test_bootstrap 131 OK; tools.test_accepted_base 9 OK;
job_manager full family OK.

**The candidate rebuilt** (runtime inputs changed: core.py, api.py,
tools/accepted_base.py): fresh /2 snapshot BEFORE the build
(PROSPECTIVE-INPUTS-221639.json, 110 inputs, 3d7e37e5...); executable
sha256:10e7b23f...; 81-file bundle 04df7071...
(RUNTIME-BUILD-221639.json supersedes the installed a6dbd963 by full
digest, preserved with its instance; BUNDLE-MANIFEST-221639.json;
build-runtime-221639.log); installer rebound, bash -n clean,
pre-check replayed green. OWNER-PR-FLOW section 4 now carries the
implemented verb's exact command; after it records,
`admissible_bases`' UNCHANGED rule admits the next Job at the
accepted base on the same deployment.

**Still open (exact scope).** The PR-mode terminal/restart composed
proof (review220421 item 4: two-stage lifecycle with deterministic
providers, terminal state named, restart without redispatch —
the harness's review-stage serving exists in the three-stage
classes; the two-stage subclass remains to write); fresh-target pool
validation (compose-pool on a fresh instance); owner install of
10e7b23f + the installed PR A-then-B + accepted-base continuation
(gate criterion 1); owner authorization + execution of the bounded
real Job (criterion 2); deadline 2026-09-21T09:32:05Z.

**Boundaries kept.** No live model, no credential read, no agent Git
mutation (test and tool git acts on temporary fixture repositories or
under the operator contract), no instance touched, no manual repair;
product edits confined to the pinned accept_base/accepted_base paths
plus the two boundary-test enumerations.

**Spending this claim.** One product operation + one operator tool +
nine tests (three fix iterations), two boundary-enumeration updates,
one bounded-message rewrite, four suites run, one snapshot, one
build, two records, one installer rebind with pre-check, one
owner-flow update. Per-command wall-clock unrecorded.

## claim221705 — review221684's three probe-proven tool defects corrected; 16 tests; candidate rebuilt

**[R1] Stopped is PROVED, not inferred from a lock.** The probe was
exact: `stack.start` releases its admission when start returns and
O_CLOEXEC keeps the flock out of the children, so a free lock says
nothing. The tool now enters the stack's OWN `admission` (the lock
every lifecycle transition serializes on, short wait) and then
requires `stack.ownership` of BOTH recorded processes — manager and
publisher — to answer absent or gone; live or unknown refuses by
name. Tests: a LIVE record (the test's own pid+start-time) refuses
with the lock free; a GONE record (reused pid) proceeds; the
held-lock case now refuses through the stack's own admission message.

**[R2] Every refusal precedes every repository effect.** The probe
caught the reference advancing R0→R1 BEFORE the stale-policy refusal.
Now the FULL document validates first (a malformed document reaches
no effect at all — not even the custody directory), and BOTH the
Authority's canonical target and the reference are read and judged
BEFORE any fetch or swap: stale policy, coinciding policy, foreign
reference each refuse with the repository holding exactly what it
held. The moved-target test now carries the probe's omitted
assertion (the reference never moved). The fetch, when it runs, is
named honestly: additive objects that remain as RECOVERABLE
SAME-OPERATION partial state on a later refusal, never "nothing
happened".

**[R3] A receipt file alone is not authority.** The probe wrote
{"acceptance": document} at the receipt name and the old tool
answered replayed:true with nothing committed. Replay now requires
the receipt to carry this acceptance's operation id and
byte-identical content AND to match the Authority's own COMMITTED
`operation_result` for that identity — fabricated and well-shaped-
but-uncommitted receipts both refuse. The explicit historical-receipt
contract is implemented and tested: an old acceptance replays
successfully AFTER a newer base is recorded and rewinds nothing. A
reference coincidentally at the accepted commit without prior
evidence (byte-identical intent or committed operation) is NOT this
invocation's resume — refused by name. Intent and receipt writes now
fsync the file AND the containing directory (staged + `os.replace` +
directory sync), custody directories at 0o700.

**Tests: 16 OK** (the 9 pinned boundaries, now with the strengthened
assertions, plus 7 new: live-record refusal, gone-record proceed,
malformed-no-effect, fabricated receipt, uncommitted well-shaped
receipt, historical replay after a later acceptance, coincidence-not-
resume). Sweep: authority 388 at its 3-test pre-existing committed
baseline; bootstrap 131 OK; job_manager family OK.

**Candidate rebuilt** (PROSPECTIVE-INPUTS-221705.json, 110 inputs,
3c2dac24..., taken BEFORE the build): the EXECUTABLE hash equals
candidate221639's — only tools/accepted_base.py changed and the
bundle carries it under _internal — so the candidates are
distinguished by the 81-file BUNDLE digest (af5639cc... vs
04df7071...), which the installer verifies beside the executable;
the record says so in its identity_note and supersedes 221639 BY
FULL BUNDLE DIGEST. Installer rebound, bash -n clean, pre-check
replayed green. 221639 preserved as unaccepted history.

**Still open (exact scope, unchanged).** The composed PR-mode
terminal/restart proof and fresh-target pool validation
(review221684 continuation); owner install + installed PR A-then-B +
accepted-base continuation (gate criterion 1); the separately
authorized bounded real Job (criterion 2); deadline
2026-09-21T09:32:05Z.

**Boundaries kept.** No live model, no credential read, no agent Git
mutation (fixture/operator-contract git only), no instance touched,
no manual repair; edits confined to tools/accepted_base.py and its
tests.

**Spending this claim.** One tool rewrite under the amended contract,
seven new tests + two strengthened assertions (one message-shape fix
iteration), three suites re-run, one snapshot, one build, two
records with the shared-executable identity note, one installer
rebind with pre-check. Per-command wall-clock unrecorded.

## claim221761 — the refused-intent hole closed; the composed PR terminal/restart proof PASSES; candidate rebuilt

**Review221748's confirmed defect corrected at its site.** The refused
coincidence call used to PUBLISH the intent first, and the identical
second call trusted that refused intent as resume authority and
advanced the Authority. The initial state — committed answer, policy,
reference, and pre-existing byte-identical intent — is now judged
BEFORE any intent is published: this invocation's own intent is
written strictly after every admission check passes, so a refused call
leaves nothing behind and repetition never grants resume authority.
Durability completed: `_durable_write` accounts every byte (short
`os.write` refuses on no progress) and custody directories are made
durable in order (each new directory's PARENT synced before anything
is written inside it), with `_finalize` ensuring its own directory.

**Two new regressions, per the review.** (1) The probe's exact
two-call shape: both calls refuse, NO intent exists after either, and
the Authority never moves. (2) A GENUINE post-reference interruption
driven through the tool itself: the acting Authority open raises after
the intent published and the reference swapped; the identical second
call completes through its own intent without a second swap. 18 tests
OK.

**The composed PR terminal/restart proof — review's continuation item
— now EXISTS and PASSES** (`APRJobSettlesAtItsReviewAndSurvivesRestart`
in tests/tools/test_stage_execution.py, on `ComposedOneJobCase`'s real
machinery: real stores, real line, actual workloads, ordinary ticks).
A TWO-stage Job (producer → reviewer, no integration stage) reaches
implementation=completed AND review=completed; settlement lags by
ordinary cleanup ticks and then EVERY allocation releases
`cleanup-retained`; the candidate's publication reads back through the
supported reader; and a RESTART over the same durable stores observes
both completed stages with ZERO redispatched starts and the same two
attempt ids — no new episodes. The proof distinguishes exactly what
the owner's model asks: producer completion, independent review,
candidate availability; owner-mainline acceptance is the human act
recorded by tools/accepted_base.py and is NOT claimed. Measured note:
D10's gates never bind by construction (no integration allocations
exist). stage_execution stays at its recorded 12-error/0-failure
baseline plus this new passing class.

**Candidate rebuilt** (PROSPECTIVE-INPUTS-221761.json, 110 inputs,
df37c3ee..., BEFORE the build): executable again identical
(bundle-carried tool change only); bundle 31a3a818... distinguishes
it, identity_note says so, supersedes 221705 by full bundle digest;
installer rebound, bash -n clean. 221705 preserved as unaccepted
history.

**Still open (exact scope).** Fresh-target pool validation (the one
review continuation item remaining — compose-pool on a FRESH
instance, owner-installed); owner install of 31a3a818 + installed PR
A-then-B + accepted-base continuation (gate criterion 1); the
separately authorized bounded real Job (criterion 2); deadline
2026-09-21T09:32:05Z.

**Boundaries kept.** No live model, no credential read, no agent Git
mutation, no instance touched, no manual repair; edits confined to
tools/accepted_base.py, its tests, and the new composed test class.

**Spending this claim.** One admission-order correction + durability
completion, two regressions, one composed PR proof class (three fix
iterations: inheritance shape, settlement lag, row key), four suites
run, one snapshot, one build, two records, one installer rebind.
Per-command wall-clock unrecorded.

## claim221832 — the generic-reference model applied at its two pinned sites; the PR proof now runs the TRUE no-integrator topology

Under owner 2026-09-20T14:57:48Z (message221781) and review221816,
with the scope pinned in FINDING before editing, and the revised
boundary acknowledged as promised in poke-answer221820.

**Site 1 — the PR admission coupling.**
`bootstrap.admissible_bases`' ESTABLISHED branch no longer reads the
Authority or compares anything to the canonical target: a new
binding's `line_declared_base` is an OPAQUE reference carried verbatim
to the Job's agents, per-binding (independent Jobs may declare
different bases), with only a nonempty-string shape check. The
FRESH-root one-base rule stays (it guards the integration flow's first
publication, which the PR flow never reaches); retained-binding
conflict checks untouched. Tests: the stale-base and one-base-across-
new-jobs refusal tests became their admission counterparts (the
successor at the human-accepted reference; three concurrent new
bindings at three references), and the untouched-live-Authority case
now exercises the branch's remaining refusal (empty reference).
bootstrap 131 OK.

**Site 2 — the obligatory integrator.** Review221816 was right that
the PR proof's inherited document still configured an integrator; the
overridden composition then MEASURED the product refusing:
"this deployment serves implementation, review, integration and names
no worker for integration". The pinned one-line correction makes the
INTEGRATION role optional in the role-coverage gate (implementation
and review remain required); the PR proof class now composes TWO
workers and NO integrator and passes END TO END on that true topology
— both stages complete, allocations release cleanup-retained,
publication readable, restart observes with zero redispatches. The two
coverage tests that asserted integration-required became their
required-role (review) counterparts plus explicit
no-integrator-admitted cases, in both the one-job and multi-worker
families. stage_execution at its recorded 12-error/0-failure baseline
with the new passing cases; job_manager OK; manager+accepted_base
119 OK.

**Preserved as history, per the owner:** `Authority.accept_base`,
`tools/accepted_base.py` and their 18 tests (all still green) — the
Git-synchronizing transaction is superseded as a prerequisite, not
deleted; OWNER-PR-FLOW section 4 now states the revised boundary
(acceptance is a durable generic record; the successor simply DECLARES
the accepted reference, which admission now admits) with the old
transition retitled historical.

**The candidate rebuilt** (PROSPECTIVE-INPUTS-221832.json, 110 inputs,
307834c8..., BEFORE the build): executable sha256:30f32ca8...,
81-file bundle 244400e8... (both product files changed, so the
executable moved this time); records supersede 221761 by bundle
digest with the superseded-transaction note; installer rebound,
bash -n clean.

**Still open (exact scope).** The successor-continuity composed test
(job-b at job-a's candidate head as opaque explicit input on the SAME
deployment — the recipe: the second-Work machinery already in
tests/tools/test_stage_execution.py ~line 5940, the human acceptance
simulated by fetching the candidate head into the nominated source,
job-b declaring it verbatim; admission for it is now PROVEN at the
bootstrap layer); fresh-target pool validation (owner-installed fresh
instance); the installed PR A-then-B (criterion 1); the separately
authorized bounded real Job (criterion 2); deadline
2026-09-21T09:32:05Z.

**Boundaries kept.** No live model, no credential read, no agent Git
mutation, no instance touched, no manual repair; product edits
confined to the two pinned sites; nothing deleted or silently closed.

**Spending this claim.** One FINDING pin, two product-site edits, five
test updates + two new admitted cases, one measured topology refusal
driven to its correction, five suites run, one snapshot, one build,
two records, one installer rebind, one OWNER-PR-FLOW boundary
revision. Per-command wall-clock unrecorded.

## claim221940 — the A-acceptance-new-B composed proof DELIVERED; the last global-base gate corrected; the runnable successor path exists

**The proof review221919 required, written and PASSING**
(`AAcceptedPRSeedsTheSuccessorOnTheSameStores`): Job A runs
producer-and-reviewer only to its accepted, completed review; the
HUMAN acceptance is simulated EXPLICITLY — a durable
`baton.w202663.accepted-base/1` record written beside the root AND
the accepted candidate fetched into the nominated source, the merge
in miniature; Job B is created only then, on the SAME durable stores,
under its own distinct Work, its binding declaring the accepted
candidate as an OPAQUE reference; B materializes AT it from the
source and completes its own accepted review; A's allocation and
states are byte-identical afterwards and nothing redispatched.

**The path was blocked twice, measured by deferral probes, and
corrected at both `integration/driver.py` sites** under the same
ruling: the publication recorded the Authority's canonical target and
REFUSED any proposal whose base differed ("a proposal is offered
against the revision it was built from") at the offer, then the same
comparison again in `publish_candidate` — the last global base
enforcement on the PR path. The proposal's recorded target is now its
OWN declared base (for every proposal the old gates admitted, the
identical value), the offer-time canonical-target reads are gone,
and `integrate`'s stale-target door — inside its committed
transaction — remains the integration flow's enforcement unchanged.
The two drift tests became their admission counterparts.

**The runnable successor path** (review221919's composer gap):
`--base <reference>` on the verification composer carries the
accepted reference verbatim into the task, binding and manifests
(call-time, 40-hex validated, no repository read); OWNER-PR-FLOW
section 5 is superseded from fresh-install-per-base to the exact
same-deployment command sequence.

**Sweep:** integration 319 OK (driver corrected); stage_execution at
its recorded 12-error/0-failure baseline plus the new passing proof;
job_manager OK; composer isolation checks pass.

**Candidate rebuilt** (PROSPECTIVE-INPUTS-221940.json, 110 inputs,
e83d657c..., BEFORE the build): executable sha256:76528d51...,
81-file bundle 360fa9a4...; supersedes 221832 by bundle digest;
installer rebound, bash -n clean.

**Still open (exact scope).** Owner install of 76528d51 + the
installed PR A-then-B with real human acceptance and the --base
successor (criterion 1); the separately authorized bounded real Job
(criterion 2, REAL-JOB-PROPOSAL stands); fresh-target pool validation
at that install; deadline 2026-09-21T09:32:05Z.

**Boundaries kept.** No live model, no credential read, no agent
version-control mutation (test version control on fixture
repositories only), no instance touched, no manual repair; product
edits confined to the two publication-gate sites under the pinned
ruling.

**Spending this claim.** One FINDING-pinned scope, one composed proof
(two measured blockers driven to their corrections via deferral
probes), two driver-site edits + two superseded tests, one composer
--base operand, one OWNER-PR-FLOW supersession, five suites run, one
snapshot, one build, two records, one installer rebind. Per-command
wall-clock unrecorded.

## claim222049 — review222023's three bounded runnable gaps closed; no product change, candidate 221940 stands

**[R1] The acceptance-transport disconnect.** The composed proof
fetches the accepted object into the nominated source; the owner flow
merged into an unspecified official checkout and then composed against
the deployment's `repo/workspace` with nothing carrying the content
across. OWNER-PR-FLOW section 3 now states the owner-run
workload-input preparation exactly: capture `ACCEPTED` from the
official merge, `git -C "$DEST/repo/workspace" fetch <official>
"$ACCEPTED"`, and the PREFLIGHT (`cat-file -e "$ACCEPTED^{commit}"` in
the nominated source) before composing the successor — both the
owner's own version-control acts on the owner's deployment, no
coordinator involvement, no binding moved. Section 5's preamble points
at the transport+preflight explicitly.

**[R2] The Claude composer's explicit base input.** `select_base` /
`--base <reference>` ported to compose-pool-207219.py exactly as on
the verification composer (call-time, 40-hex validated, opaque, no
repository read; without the flag the historical target-refs read
stands for the recorded runs). Module loads and the operand validates;
REAL-JOB-PROPOSAL's launch commands and Job document now carry
`--base` explicitly.

**[R3] The publication-correction history appended to FINDING**: the
claim221832 pin's claim that the PR flow "never reaches" the
publication comparison is superseded in place — the conclude DOES
publish through `integration/driver.py`, both offer-time
canonical-target comparisons were measured blocking the successor and
removed at claim221940, the proposal records its OWN base (identical
values for every previously admitted proposal), and `integrate`'s
committed stale-target door stands unchanged.

**No product or test change this claim** — dossier composer, owner
documents and FINDING only; runtime inputs untouched, so candidate
221940 (executable 76528d51..., bundle 360fa9a4...) stands as bound by
the installer. Composer isolation checks pass.

**Still open (exact scope, unchanged).** Owner install of 76528d51 +
the installed PR A-then-B with real human acceptance (now with the
exact transport/preflight commands) and the --base successor
(criterion 1); the separately authorized bounded real Job (criterion
2, proposal launch commands now fully runnable); fresh-target pool
validation at that install; deadline 2026-09-21T09:32:05Z.

**Boundaries kept.** No live model, no credential read, no agent
version-control mutation, no instance touched, no product/test edits,
no manual repair.

**Spending this claim.** Three bounded document/composer corrections,
one load validation, one isolation-check run. Per-command wall-clock
unrecorded.

## claim222138 — THE FIRST INSTALLED TWO-STAGE PR CANDIDATE, on the owner-installed accepted candidate; two gates measured and corrected on the way

Owner222135 directed the review-2026-09-20T15-44-09Z two-stage recipe
on the freshly installed 221940 instance
(instance-2026-09-20T15-53-26Z; identity verified 76528d51).

**Two blockers measured, corrected, gate-proven:**
(1) `tools/bootstrap`'s OWN role-coverage gate still required an
integration worker — "no worker is configured for the integration
stage" on the fresh PR composition. The same pinned optional-
integrator correction applied (implementation/review remain required,
mirroring stage_execution's accepted gate); bootstrap 131 OK with the
coverage test split into required-role refusal + producer-reviewer
admitted. The APPLY runs from the checkout, so the installed
experiment was unaffected; a fresh candidate carries it (below).
(2) The composer's pin prediction read "first bootstrap" from the JOB
STORE's existence — which the first START creates, not bootstrap — so
every pre-start compose predicted the fresh bump; and PR mode costs
ONE LESS per preparation (measured: fresh +7 vs +8; repeat +6 vs +7).
Both corrected (first = the deployment record's existence; PR
reduction); the gate went green at generation 26 after catching the
stale model three times.

**Job A, INSTALLED, two stages, COMPLETE in ~50s** (--pr --emitting;
Work 62becc01-W1): implementation and review both released
`cleanup-retained`; NO integration stage existed; capture assertions
green; stack stopped with stores retained. THE CANDIDATE
(CANDIDATE-PR-A-222138.json): commit 2fb0612c... over base 93da9d62...
adding exactly `w197661-fixture-verification-1.txt`, test status 0,
proposal tree (patch/bundle/result/verification) on the durable line,
review accepted (run-status-PR-A-222138.json).

**The owner's concrete next commands** (OWNER-ACCEPT-A-222138.md, no
acceptance invented, no owner act performed): inspect/test the exact
candidate, merge via the proposal's own bundle, transport ACCEPTED
into the deployment's nominated source with the preflight, record the
acceptance document — then, on the go signal, B composes on THIS
deployment with `--job verification-2 --pr --emitting --base
"$ACCEPTED"`.

**Coherent artifacts:** fresh snapshot BEFORE the build
(PROSPECTIVE-INPUTS-222138.json, 110 inputs, 6dbd50f4...); executable
sha256:0b5455a3..., bundle 456c75cc... (81 files); supersedes the
installed 221940 by bundle digest (preserved with its instance — the
gate was measured ON it); installer rebound, bash -n clean.

**Still open.** The owner's acceptance of candidate 2fb0612c and the
go for B (criterion 1 completes there); the separately authorized
bounded real Job (criterion 2; package ready); fresh-target pool
validation; deadline 2026-09-21T09:32:05Z.

**Boundaries kept.** No live model, no credential read, no agent
version-control mutation, no owner act performed or invented, no
manual repair; product edit confined to the pinned bootstrap gate;
the installed instance received only compose/apply/pin/start/submit/
status/stop.

**Spending this claim.** One identity verify, five composes (three
caught by the pin gate driving the two model corrections, with one
instrumented), five bootstraps, five pin gates, one start, one
submission, one complete installed two-stage lifecycle, four polls,
one capture run, one bootstrap-gate product fix + test update, two
dossier records + owner commands, one snapshot, one build, two
records, one installer rebind, one stop. Per-command wall-clock
unrecorded.

## claim222215 — review222192's canonical-evidence gap closed through supported surfaces; the correction pins appended

**The canonical proof** (R1): the installed binary's own
`status --observe` on the STOPPED instance answers `canonical: true`
with BOTH stages COMPLETED
(run-status-PR-A-canonical-222215.json) — superseding the
non-canonical snapshot's released-only inference.

**The exact accepted association, all through public PROVING
readers** (CANDIDATE-ASSOCIATION-222215.json):
`review_for_attempt(attempt, generation=2)` discovered the attachment
and checkpoint from the review attempt id the projection carries; the
verdict id was DERIVED by `record_verdict`'s own rule
(`_id("verdict", {attachment_id, disposition})`) and proved through
`verdict_of` — verdict-e5332c53... `accepted`, Work 62becc01-W1,
reviewer baton.fixture-reviewer-1 → checkpoint-9120b870... `frozen`,
base 93da9d62... head 2fb0612c... (THE candidate) →
line-37baa08d... `accepted` at the declared base. Every member
validated against its committed act by the readers themselves.

**A's log locators** digested from the stopped instance
(A-LOCATORS-PR-222215.json, attempt-7a0f917a...); the candidate
record now links all three evidence records. The reviewer's
read-only JobStore OperationalError was not reproduced on the
ControlStore public path used here; the JobStore-side canonical read
went through the installed binary's own observe surface — recorded in
the FINDING note.

**The correction pins appended to FINDING** (the handoff-claimed pins
now durable): the bootstrap role-coverage gate correction with its
measurement, and the composer pin-model double correction
(job-store-vs-record first-signal; PR-mode minus-one) with the gate's
three catches.

**Nothing touched:** no restart, no rerun, no new install, no owner
act; the instance exactly as claim222138 left it, awaiting the
owner's acceptance of 2fb0612c per OWNER-ACCEPT-A-222138.md.

**Still open.** Owner acceptance + go for B (criterion 1 completes
there); the separately authorized bounded real Job (criterion 2);
fresh-target pool validation; deadline 2026-09-21T09:32:05Z.

**Spending this claim.** One canonical observe read, one
public-reader association proof (three discovery iterations), one
locator digest pass, three dossier records, one FINDING append.
Per-command wall-clock unrecorded.

## claim222268 — B authorized and launched at the accepted base; blocked at a PRECISELY measured transport boundary; exact owner correction returned

Owner225266 accepted A (ACCEPTED-BASE-2026-09-21T00-28-18Z.json,
accepted_commit 2fb0612c..., expected_old 93da9d62...) and authorized
B on the same instance. Executed: acceptance read; my claim222049
preflight PASSED (`cat-file -e` in the nominated source); B composed
(`--job verification-2 --pr --emitting --base 2fb0612c...`, Work
62becc01-W2, task/binding declaring the accepted base verbatim);
applied; PIN GREEN at 62 after two more measured PR-model amendments
(adding a PR job costs exactly 6 per job, no +1; PR re-apply the
same — the gate caught both, measurements now in the composer);
started; submitted.

**The blocker, measured to its root** (BLOCKER-B-222268.json;
`serve --once` diagnostic on the stopped stack): B's implementation
allocation RESERVED; materialization refuses TWICE —
declared-base checkout "fatal: --detach does not take a path
argument '2fb0612c^{commit}'" (the revision fell through to pathspec
parsing because THE CLONE LACKS THE OBJECT), then the supplement
"upload-pack: not our ref" (the dedicated target never integrated
it). Root cause verified: the accepted commit sits in the nominated
source's object store (`cat-file -t` = commit) but NO REF reaches it
(for-each-ref: only main@93da9d62 and a tag) — and a line CLONE
transfers only ref-reachable objects. My claim222049 preflight tested
PRESENCE, not CLONE-REACHABILITY, and passed misleadingly — corrected
in both owner documents to the REF-CARRYING transport
(`fetch <official> "$ACCEPTED:refs/heads/accepted-$ACCEPTED"`) with a
reachability preflight (`rev-parse --verify` the ref).

**Owner's exact unblock** (also in the blocker record): the
ref-carrying fetch, the reachability preflight, then
`just start` — B's reserved attempt retries materialization on
ordinary ticks; no recompose, no resubmit, no reinstall needed.

**Robustness note recorded:** a materialization refusal CRASHES the
`--once` reconcile surface rather than deferring; the live serve
retries each tick. Noted, not repaired.

**State left:** stack STOPPED; B reserved (report-and-hold); A's
history and logs untouched (comparison pending B's completion); no
owner act performed, no manual repair, nothing reinstalled.

**Still open.** Owner's ref-carrying transport + restart → B to
completion → candidate/evidence extraction + A-history/log
comparison (criterion 1 completes); the separately authorized real
Job (criterion 2); fresh-target pool validation; deadline
2026-09-21T09:32:05Z.

**Spending this claim.** One acceptance read + preflight, one
compose-apply-pin cycle ×3 (two PR-model catches by the gate), one
start, one submission, ~20 polls, one stop + once-diagnostic, one
root-cause verification, one blocker record, two owner-document
corrections. Per-command wall-clock unrecorded.

## claim225345 — review225331's same-line recovery: limitation recorded, correction pinned+implemented+proven, owner selection returned

**Recorded in FINDING before any change** (as required): the
source-retry LIMITATION (an existing checkout is resumed, never
re-cloned, and a proved-absent base earns only the dedicated-target
supplement — the nominated source is never refreshed, so the PR
flow's post-clone acceptance transport can never arrive) and the
serve-once EXCEPTION (a materialization refusal crashes the reconcile
surface rather than deferring; the live serve retries).

**The pinned correction, implemented in `checkpoint_profiles.py`
only:** after the absence proof on an existing checkout, the
NOMINATED SOURCE is refreshed first — all heads, explicit refspec
into a private `refs/baton/source/*` namespace (measured: a
refspec-less URL fetch transfers only the remote HEAD, exactly the
branch the clone already has) — presence re-proved, then the
supplement exactly as before; a failed refresh is preserved VERBATIM
in whichever refusal follows, never swallowed.

**Deterministically proven** (the review's exact shape,
`AnExistingCheckoutRecoversWhenTheSourceGainsTheBase`): materialize
at the base; the retry at a commit absent everywhere REFUSES; the
base is made ref-reachable in the source (the human acceptance); the
SAME line then materializes successfully with NO supplement
configured or touched — plus the supplement fallback unchanged when
the source never gains the commit. Profile family 33 OK; both
composed PR proofs pass; bootstrap + OCI OK.

**Candidate rebuilt** (PROSPECTIVE-INPUTS-225345.json, 110 inputs,
7bda77b6..., BEFORE the build): executable sha256:151060fb...,
bundle bb410f6c...; supersedes 222138 by bundle digest; installer
rebound, bash -n clean.

**The owner selection returned** (OWNER-UNBLOCK-B-225345.md;
owner225266 selected the installed runtime/no reinstall, which the
correction cannot reach without an install): (a) IMMEDIATE on the
current runtime — make the accepted commit ref-reachable in the
DEDICATED TARGET (the repository the existing supplement already
fetches from), then start; B's reserved attempt retries on ordinary
ticks; (b) FORWARD — the corrected candidate on a fresh instance.
No owner act performed; B stays reserved, A untouched, nothing
resubmitted or repaired.

**Still open.** The owner's (a)/(b) selection → B completion →
candidate/evidence extraction + A-history/log comparison (criterion
1); the separately authorized real Job (criterion 2); fresh-target
pool validation; deadline 2026-09-21T09:32:05Z.

**Spending this claim.** One FINDING record-before-workaround, one
product correction (three iterations: swallowed-failure fix,
refspec measurement via scratch probe, control-flow fix), two
deterministic recovery tests, four suites run, one snapshot, one
build, two records, one installer rebind, one owner-selection
document. Per-command wall-clock unrecorded.

## claim225452 — B COMPLETE on the accepted base; the A→acceptance→B chain is demonstrated

The owner executed option (a) of `OWNER-UNBLOCK-B-225345.md` — fetched the
accepted A commit `2fb0612c` into the deployment's dedicated target as
`refs/heads/accepted-2fb0612c` (preflight TARGET-REACHABLE) — and started
instance-2026-09-20T15-53-26Z (event 225450). This claim observed, extracted
and compared; no composition, no resubmission, no repair.

**B completed both stages.** verification-2's reserved implementation attempt
retried on an ordinary tick, materialized at the accepted base through the
existing supplement, produced candidate `446fa8f7` ON base `2fb0612c` (the
owner-accepted A candidate), and the review stage accepted it. Both
allocations released cleanup-retained at 2026-09-21T01:01:47Z; stack stopped
afterward; instance preserved.

**Canonical evidence** (all via supported public readers, observing status):
- `run-status-PR-B-canonical-225452.json` — `canonical: true`; all four
  stages of both Jobs completed on the ONE persistent deployment.
- `CANDIDATE-ASSOCIATION-B-225452.json` — verdict-4a165295 `accepted` for
  Work 62becc01-W2 → checkpoint-000f429b FROZEN (base 2fb0612c, head
  446fa8f7) → line-5f806d76 accepted at the declared base, proven through
  `review_cycles.verdict_of/checkpoint_of/line_of/review_for_attempt`.
- `AB-COMPARISON-225452.json` — A's attempt streams byte-identical after B;
  A's allocations unchanged (released, cleanup-retained); capture assertions
  green across both Jobs. B did not disturb A's history; no redispatch.
- `CANDIDATE-PR-B-225452.json` — the candidate record awaiting the owner's
  own evaluation per OWNER-PR-FLOW.

This demonstrates investment-gate criterion 1: a working PR flow where Job A's
accepted candidate became Job B's declared base on the same persistent
deployment, with human acceptance in between and the coordinator treating
every reference as opaque metadata.

**Forward candidate corrected (review225408), installed runtime untouched.**
The source-refresh recovery dropped a failed refresh's cause when the
supplement subsequently also refused; the supplement-refusal message now
carries BOTH causes ("…did not provide it (…); the nominated-source refresh
also failed (…)"). Regression class
`AFailedRefreshTravelsWithTheSupplementRefusal` (inherits the supplement
family; 42/42 green). Rebuilt on the reviewed cadence: prospective snapshot
FIRST (110 inputs, `PROSPECTIVE-INPUTS-225452.json`), `just build`,
`RUNTIME-BUILD-225452.json` (executable 786af0d5…) +
`BUNDLE-MANIFEST-225452.json` (bundle 7305d1c7…, 81 files),
`install-next-instance.sh` re-bound to the 225452 records. Built, NOT
installed anywhere — candidate 225345 is superseded as history.

Remaining: gate criterion 2 — the useful real-Claude Job
(`REAL-JOB-PROPOSAL-220329.md`, submission carries `--base`) needs the
owner's separate authorization and an independently accepted result.

## claim225533 — live-launch preparation complete on the owner-installed 225452 instance

The owner accepted B (`446fa8f7…`, `ACCEPTED-BASE-2026-09-21T01-11-48Z.json`,
official checkout fast-forwarded) and installed reviewed candidate 225452 at
`/home/sl/baton-v12/instance-2026-09-21T01-12-21Z` (pass 225531). This claim
prepared and validated the real Claude PR pool there per
REAL-JOB-PROPOSAL-220329.md — NO start, NO submission, NO provider contact.

**Gates passed, in order:** installed identity (executable equals
RUNTIME-BUILD-225452.json); source delivery (446fa8f7 is refs/heads/main's
tip in the nominated source — ref-reachable, read-only proven); PR pool
composed at `--base 446fa8f7…` with zero refusals (coder+reviewer, no
integration worker, job input identity sha256:1ad3c142…); provider image
`baton-v12-w202663-provider:e486652c` engine-held with ID equal to the
configured digest; bootstrap applied (routes impl→baton.claude-coder,
rview→baton.claude-reviewer, one-Job capacity); policy pin GATE equal at
14==14.

**Pin defect caught and corrected:** the gate first refused (configured 9 vs
generation 8). `compose-pool-207219.py`'s `policy_pin` had never received the
PR-mode measurements banked in the verification composer — PR costs one less
bump per preparation and "first" means no deployment record, not no job
store. Ported (with the claim225533 measurement note), recomposed, re-applied,
gate passed. The gate did exactly what it exists to do.

**Obsolete script instructions corrected (owner 225531):**
`verify-next-instance.sh`'s "remaining steps" now state the real Claude PR
pool sequence (a–c preparation, d–e owner-authorized only), superseding the
completed deterministic-verification listing; `check-policy-pin.sh` gained a
`pool` mode selecting the pool composer + `select_pr` so the gate answers for
the pool actually deployed. Both re-run green against the live deployment.

**Deliverable:** `LIVE-LAUNCH-PACKAGE-225533.md` — everything already
validated, the ONE owner input (credential reference `w202663-development`
behind `/home/sl/.baton/credential-sources.json`; nothing read by this Work),
the exact TWO remaining commands (start + submit), enforced limits, and the
observation/acceptance cadence. It supersedes the proposal's launch preamble.

Gate criterion 2 now awaits only the owner's separate authorization to run
the two commands.

## claim225590 — R1 corrected, a second launch blocker found and corrected, redeployed and re-gated

Review225576 returned R1: the frozen verification argv (`python3 -m unittest
tests.tools.test_pool tests.tools.test_bootstrap`) cannot discover its
modules from the candidate root, where `_verify` runs it. Corrected in the
composer's `task_document`: the shell-less argv now enters the subtree via
the interpreter (`os.chdir('v12/python')` + absolute `sys.path` inserts +
`unittest.main`, verdict in exit status).

**Demonstration from a repository-root candidate context** (scratch clone of
the actual nominated-source shape at exactly the accepted base, root `tests/`
= `conftest.py` + `work`, reproducing R1): with a clearly-labeled
launch-plumbing FIXTURE `test_pool.py` (discovery proof only, not coverage,
never enters the repository), the exact argv ran 126 tests OK exit 0 — the
fixture plus the entire bootstrap family; a deliberately failing fixture
exits 1.

**Second blocker found by that demonstration:** inside the configured
provider image (9ff3322f…) the argv dies at collection —
`ModuleNotFoundError: jsonschema`, the product's ONE declared dependency,
absent from the image that runs the product's tests (bare /usr/bin/python3,
no pip). Corrected `worker/Dockerfile.claude`: `python3-jsonschema` on the
apt line with the in-recipe rationale (the `git` rule's second instance).
Candidate image tag claim225590, digest 448c98c9…; the exact argv ran 126
tests OK exit 0 INSIDE it (network none, candidate read-only, entrypoint
overridden); `tests.manager.test_dogfood_image` (16) green. A CANDIDATE per
the recipe's selection doctrine — owner launch authorization selects it.

**Redeployment:** the manager correctly REFUSED changing the 01-12-21Z
deployment's task bytes in place, so a fresh root was installed from the
same reviewed 225452 distro (instance-2026-09-21T01-28-41Z, pre/post
identity equal; 01-12-21Z preserved untouched, never started). Composition
at --base 446fa8f7 zero refusals, new job input identity 87033f1b… (bytes
changed, identities re-checked per review); staged argv + candidate image
digest verified at the instance; nominated source refs/heads/main ==
accepted base. Policy pin gate PASSED 14==14 — after catching one more
prediction defect ("first" = no configured capacity; this installer writes
an empty deployment.json, so a file-existence test misread fresh roots;
recorded in the composer).

**Package refresh:** LIVE-LAUNCH-PACKAGE-225590.md supersedes 225533 —
correct nominated-source naming ($DEST/repo/workspace, not /home/sl/src/baton),
RESOLVED numeric limits (provider_turn 3600 s / ordinary_verification 900 s,
compatibility generation pinned at submission), and the episode-vs-internal-
turns distinction (one container invocation per stage; no total-spend claim
beyond the two-episode structure). Two commands remain, owner-authorized.

## claim226109 — owner's refused start diagnosed; TWO preparation defects corrected; actual startup demonstrated

The owner selected LIVE-LAUNCH-PACKAGE-225590 and ran its block; start
refused at `configure_workspace_storage` before any submission (owner
FINDING). Two concrete defects in the POOL composer, both corrected:

1. **Missing directories** — `deployment_for` named per-worker
   launch/credential homes and workspace storage but the write section never
   created them (the verification composer has carried that preparation
   since start-208777.log measured the same refusal). Ported, adapted.
2. **Per-role workspace stores** — found by THIS claim's own first start
   attempt after fix 1: the manager refuses a second store ("a changed
   store is a fresh store rather than a reconfiguration"). The store is
   MANAGER-SCOPED; one store (the implementation worker's) now serves both
   workers, separation staying in the private launch/credential homes —
   mirroring the verification composer and W197661's accepted composition.

**Preserved as the owner required:** frozen task bytes (1437, identical),
candidate image 448c98c9…, the instance itself (no reinstall), all prior
instances. The job input identity moved 87033f1b… → 4f18ef79… because the
policy pin travels in the composed documents and the repeat applies moved
the Authority 14→20→26 — the gate checked each step and the submission
document, staged manifests and deployment now agree at 4f18ef79; pin
26==26.

**Actual startup demonstrated and LEFT RUNNING:** `just start` answered
"ready: every manager this start ran acknowledged that its deployment
composed, and the publisher wrote a valid, freshly observed snapshot; no
Job was submitted; an empty configured stack is a valid idle state."
Evidence: `STARTUP-DEMONSTRATION-226109.json` (defects, preservation,
identity movement, the exact remaining submit command).

**The ONE remaining owner command** (submission was never reached by the
refused start, and none happened here):

    cd /home/sl/src/baton/v12/python
    PYTHONPATH=src:. python3 -m tools.job_manager \
      --store /home/sl/baton-v12/instance-2026-09-21T01-28-41Z/db/jobs.sqlite3 \
      --incarnation w202663-claude-job-submit \
      --authority-uuid 13c91b695bfe4625b4f22dabd35a54a4 \
      submit --document <dossier>/pool-submission.json

Execution limits unchanged: one producer episode + one reviewer episode,
provider_turn 3600 s, ordinary_verification 900 s, report-and-hold, no
automatic recovery.

## claim226329 — owner's live submission observed: launch failed pre-runtime; cause found (credential reference unresolvable); zero spend

The owner verified process health and submitted the live Job (pass 226327).
Observation through the supported surfaces found implementation stage
`exceptional`: allocation released at 03:21:27Z with release_reason
`launch-failed-before-runtime`, `execution_runtime: not-started`, no
container ever created; review blocked on that gate. The line checkout HAD
materialized correctly at the accepted base and the attempt inputs were
staged — the failure is squarely in launch preparation.

**Cause:** the deployment's credential profile demands slot `claude` →
provider `operator-file`, reference **`w202663-development`**; the operator
registry `/home/sl/.baton/credential-sources.json` holds exactly one entry,
reference **`w64268-run1`**. The resolver refuses an unresolvable
(provider, reference) pair at launch preparation, before any runtime —
matching the released allocation, empty launch logs and absent container.
Checked without reading any secret (registry structure + path
existence/mode only). **Zero provider spend; no credential read; the one
authorized producer episode executed nothing.**

**Nothing mutated:** no restart (per owner 226327 the sandbox's stale-PID
view is not grounds), no resubmission, no recovery, no registry edit —
selecting which account a deployment spends is the owner's act.

**Owner options** (recorded in `LIVE-LAUNCH-FAILURE-226329.json`):
(a) add a `w202663-development` entry to the registry — no recomposition
needed, the registry is read at launch; or (b) instruct recomposition to
`w64268-run1` (changes frozen bytes → recompose/reapply/pin/review). Then
either an ordinary tick retries the exceptional stage or a fresh
submission is needed — both authorization decisions, not mine.

## claim226458 — recovery path established: fresh Job 2 composed, applied and gated beside the preserved failure; owner credential commands prepared

Per owner 226456 and review226363's correction (ordinary ticks do NOT retry
a released, live-episode failure), the reviewed recovery is the FRESH-JOB
cadence this Work already accepted (review208349 / verification composer's
select_job): the failed Job stays preserved evidence; a new Job composes
beside it under fresh identities. The W128698 abandonment machinery was
examined and rejected for this case: its endings are the only replaceable
ones, but abandoned-after-restart settles only ISSUED offers from another
incarnation (ours was CLAIMED) and abandoned-after-exclusion's operator
flow targets attempts whose container ran and has no packaged command for
this pooled composition.

**Two-Job support ported into compose-pool-207219.py** (from the
verification composer's reviewed support): select_job/--job with
claude-actor naming, prepared_workers/prepared_jobs (retained verbatim),
durable-pool generation prediction, per-job pin arithmetic, and the
retained-participant principals union — the composer's own validator caught
the narrow document on the first run (KeyError: 'baton.claude-coder'),
the identical defect the verification composer had measured, fixed the
same way.

**Prepared and gate-checked, nothing live:** fresh Job
w202663-first-development-job-2 (Work 13c91b69-W2, actors
baton.claude-coder-2/reviewer-2) with the SAME frozen task content,
candidate image 448c98c9…, and accepted base 446fa8f7…; composed complete
with zero refusals, applied ("work 13c91b69-W1 already exists; left
alone"), deployment now 4 workers / 2 bindings / ONE shared store; job
input identity 28e095f0…; submission names job-2 only; pin gate 26→38
EQUAL (the ported 6-per-job arithmetic's first live check); pool
membership changed so the next activation mints generation 2 (activation
itself checks).

**RECOVERY-PATH-226458.md** carries the owner's exact commands in order:
(1) the secret-safe registry mapping (w202663-development → the same file
w64268-run1 names; prints no secret; 0600 preserved; refuses ambiguity;
provider model untouched), (2) stop/start to activate the two-Job pool,
(3) the exact job-2 submission, (4) signal for observation. Prior
assignment disposition verified and recorded: released
launch-failed-before-runtime, live episode preserved, no runtime ever
existed, W1/workers/routes left alone by the apply.

## claim226516 — review226502's two bounded corrections applied and demonstrated

**R1 — the registry command, corrected in RECOVERY-PATH-226458.md:** it now
REFUSES a conflicting or ambiguous destination (an existing
`w202663-development` entry with a different provider/path, or duplicated),
no-ops ONLY on the exact owner-selected mapping (provider `operator-file` +
the `w64268-run1` entry's own path), and writes the replacement registry
EXCLUSIVELY — `os.open(O_WRONLY|O_CREAT|O_EXCL, 0o600)` on an
unpredictable `secrets.token_hex` name, unlinked on any failure — so no
predictable file is truncated or followed. The ambiguous-origin refusal
(≠1 `w64268-run1` entries) already stood. Exit status is the gate and all
three owner blocks now run under `set -euo pipefail`, with the submit
command's store path absolute. The three behaviours plus the
ambiguous-origin refusal are DEMONSTRATED on temporary metadata fixtures —
fixture registries in fresh temp dirs whose "paths" name nonexistent
files; no real registry or credential read —
`registry-command-fixture-226516.json`: append / exact-match-no-op /
conflict-refusal / ambiguous-origin-refusal, all passed, mode 0600
preserved.

**R2 — `_pool_generation_prediction` through public readers only:** the
raw read-only SQLite connection is gone; the helper now asks the durable
pool via `JobStore.open_readonly` and the scheduler's own
`active_generation`/`pool_workers`. Validated against the applied
two-Job deployment: prediction 2, identical to the raw form's answer, no
operational limitation encountered. Per the review, NO recompose or
bootstrap rerun — the prediction runs at compose time and the applied
deployment stands (pin 38 equal, job-2-only submission 28e095f0…,
identical image, task bytes differing only in task_id, the entire failed
Job canonical record unchanged — all independently accepted by
review226502).

The owner's three command blocks in RECOVERY-PATH-226458.md remain the
only outstanding acts: registry mapping, stop/start activation (pool
generation 2), job-2 submission, then my observation.

## claim226576 — the FIRST REAL CLAUDE EPISODE: task completed in the line, then the work operation faulted at verification capture; full evidence extracted

The owner executed the recovery package (alias mapped, stack restarted,
job-2 submitted 03:58:36Z). Observed to terminal: the producer container
ran ~19.3 minutes (well inside 3600 s), streamed 1.35 MB, and the LIVE
CLAUDE CODER COMPLETED THE BOUNDED TASK — `tools/pool.py` (27 KB) and
`tests/tools/test_pool.py` (30 KB, 35 tests) exist in the retained line
checkout at exactly the accepted base, ONLY the two allowed paths touched,
with a full agent summary (frozen verification 160 OK in its own run; two
out-of-scope findings: the admitted worker is configured but not routed —
needs add_route_handler; stack.spec lacks tools.pool in hidden imports).

**Then the work operation FAULTED (fault_code agent):** the adapter's own
authoritative verification captures declared FAILED ("earlier capture ...
bytes were never restored ... not whole") — incomplete durable evidence
faults the exchange. Root cause per the agent's own summary: it killed a
background full-suite run, PID 1 does not reap, ~498 zombies filled the
512-cap PID cgroup, later forks failed (BlockingIOError), breaking the
authoritative verification/capture (its re-runs: 152 pass / 8 error, all
fork-related; test_pool 35/35). No proposal froze (result workspace
empty, no commit, no checkpoint, no verdict); review blocked; allocation
still reserved; cleanup unrun; everything preserved as found.

**Evidence:** LIVE-JOB2-OUTCOME-226576.json (timeline, stream statuses,
line state, fault chain, spend: ONE producer episode consumed, no
reviewer episode). Owner decision points recorded there: salvage of the
durable-but-unreviewed files (owner's own act), a fresh job-3 via the
reviewed --job flow WITH a selected mitigation for the PID hazard (task
instruction / image init reaper / raised pids limit — each reviewable),
and disposition of this reserved exceptional attempt. Criterion 2's
independently-accepted-result requirement is NOT met: real useful output
exists but no independent verdict was produced.

## Claim227097 — bounded deterministic recovery preparation (owner 227095)

**Pinned first:** owner 227095 verbatim in FINDING; selected scope per
question in PLAN (2026-09-21T05:06Z), before any edit.

**Corrections, each deterministically proven:**

1. **Reaping (image entry).** `dogfood_entry.py` is a minimal PID-1
   supervisor: unchanged worker one process down, signals forwarded, every
   orphan reaped, worker's own ending carried (128+N on a signal death).
   NEW `tests/manager/test_dogfood_entry.py` (6 tests, subreaper helpers)
   plus an in-image proof as REAL PID 1 under the composed 512-PID limit:
   orphan reaped, no child left, status carried.
2. **Capture isolation (adapter + entry).** `_log_room()` opens only what
   `BATON_ATTEMPT_LOG_ROOM` names; the entry sets it in the worker's own
   process; composed child environments provably never carry it. In-image:
   no marker answers `(None, None)` with a real room mounted; the marker
   opens exactly that room. Sidecars untouched. Residual stated exactly
   (candidate-sourced old bytes, the reference worker's `_WorkerCapture`,
   same-uid absolute-path reach): the complete fix is a manager-side
   room-target change, for separate owner selection.
3. **Verifier environment (task bytes).** Measured at the accepted base:
   test_bootstrap = 125 tests; 3 stack classes need any WRITABLE root
   (default /var/tmp is read-only in-container; ~1 MiB peak); 11
   ValidFixture classes (75 tests) demand a root at once disk-backed,
   writable and outside the checkout, and the container has NO such place
   by mount contract (/output IS the line checkout) — they refuse rather
   than skip, and the only paths that could satisfy them are manager
   delivery mounts (the plausible explanation of the uncredited manual
   "160 OK"). Corrected frozen argv: makes its fixture root itself
   (realpath'd mkdtemp under the invocation's own TMPDIR; an explicit
   export is respected), excludes the 11 impossible classes BY NAME with
   the reason frozen in the bytes, floors the count at 51. Demonstrated
   through the REAL `_verify` + `_pinned_environment` over an archive
   candidate at the accepted base: unset case makes one root under the
   held TMPDIR and exits 0; exported case is respected and exits 0
   (VERIFIER-ENV-DEMO-227097.json, acceptable: true). The full family
   still gates host reruns; the complete in-container fix (a disk-backed
   fixture delivery mount) is recorded for owner selection.
4. **Job2 disposition / pool revalidation.** From source plus 4 NEW
   composed tests (`AFreshJobComposesBesideAReservedAllocation`,
   test_scheduling 69/69): a widened pool is a new generation and the
   reserved row stays untouched; `_required_workers` keeps the reserved
   worker from its own generation; fresh identities reserve on the fresh
   worker; a shared-principal successor refuses by name. Disposition
   recommendation: preserve the reserved row as live evidence; the
   W128698 exclusion recovery exists and now matches Job2's shape but
   demands runtime destruction plus a checkout restore that would destroy
   the preserved unreviewed bytes — recorded, not recommended.

**Candidate image** sha256:b44f55220e9f... (RECOVERY-IMAGE-227097.json:
in-image byte identity, both demonstrations, gates: test_dogfood_image 16,
test_dogfood_entry 6, test_claude_agent 206, test_attempt_logs 213,
test_claude_context+test_fixture_dispatch 49, test_scheduling 69 — all OK).
Composer: PROVIDER_IMAGE moved with history; the task gains the
foreground-only pilot instruction; select_job mints job-3 identities.

**Package:** RECOVERY-PACKAGE-227097.md — corrections, evidence,
disposition options, and the three fail-closed owner command blocks
(compose and apply job-3; stop and start; submit job-3). NOTHING applied,
started, submitted, cleaned, credentialed or history-mutated this claim;
both failed Jobs, the retained files and all sidecar bytes preserved as
found. Spend this claim: zero provider episodes; deterministic tests and
two throwaway local containers only. Criterion 2 remains open.

## Claim227424 — round 2: the three owner-selected corrections, complete

Scope pinned in PLAN (06:05Z) before editing, per owner 05:56:02. Full
detail in RECOVERY-PACKAGE-227424.md / RECOVERY-EVIDENCE-227424.json.

**R2 (owner "I approve spare mount"):** per-attempt disk-backed scratch is
a real delivery — `workspaces.HOME_ENTRIES` provisions `scratch` with the
home (the home closes right after; a post-hoc mkdir measured 0o555 EACCES),
`single_worker._attempt_scratch` adopts it on the START path only, `oci`
composes one writable bind at the constant `/scratch` (execution-only,
absent-by-default, both-direction collision checks; 5 new vector/adapter
tests). The frozen argv selects `/scratch` (exported selection wins; host
fallback realpath mkdtemp) and runs the FULL families — claim227097's
exclusion remedy superseded and removed. IN-CONTAINER PROOF with the
ACTUAL RETAINED pool.py/test_pool.py (hash-verified, AdmissionCase→
ValidFixture): the exact frozen argv ran 160 tests OK exit 0, where the
same family measured 75 failures without a compliant root. Demonstration,
not acceptance; no retained byte moved.

**R3 (owner "I agree with own/disposable logs"):** the authoritative room
moved to `/run/baton/attempt-logs` (one constant,
`attempt_log_format.TARGET`; manager mount, image entry marker and the
reference worker's capture all derive from it), and the legacy
`/run/baton/logs` is a disposable decoy tmpfs in the unconditional
restrictions. IN-CONTAINER PROOF over the accepted base's OWN old bytes
(adapter `_log_room`/`_Captured` declaring failed AND reference-worker
`_WorkerCapture`): all four files landed in the decoy; the real room's
pre-seeded stream and finished sidecar were byte-identical after. No old
evidence reset.

**R1 (owner 05:56:02):** complete fail-closed sequence in the package —
fenced fresh install (runtime rebuilt this claim: executable c45ff6d9…,
bundle 8616ab85…/81, prospective inputs taken BEFORE the build, installer
re-fenced on the new records and its BEFORE gate re-run green), then
compose job-3 (--pr --base 446fa8f7 --job …-job-3 --work 1, fresh
coder-3/reviewer-3), then the SUPPORTED APPLY (`tools.bootstrap --inputs`),
then `check-policy-pin.sh <dest> pool` exiting nonzero BEFORE any start,
a no-secret credential-registry preflight, then start + submit job-3 only.
Provider image rebuilt: d1e2869e… (gate 16 OK), pinned in the composer.

Suites: 590 + 433 focused tests green (oci/oci_engine/oci_integration/
workspaces/attempt_logs/dogfood_entry/claude_agent/single_worker/
scheduling), golden vector updated for the decoy, home-layout test green
with `scratch` declared. Measured and recorded: 15 real-Docker
input-delivery tests fail IDENTICALLY against pristine accepted-base
sources on this host — pre-existing environment failures, not this
claim's. Nothing live/applied/installed/submitted; both failed Jobs and
all retained evidence preserved as found; zero provider episodes.
Criterion 2 remains open.

## Claim227653 — job-3 observation (owner 227649): credential expired, package proven live

Observed read-only through the publisher snapshot, the supported status
surfaces, the new room and read-only docker inspect; nothing retried,
restarted, resubmitted or cleaned. Timeline: submitted 06:30:08Z,
reserved 06:30:12Z on coder-3, claimed 06:30:17Z, container db0107ac…
ran 06:30:20.600→06:30:25.095Z (exit 1), exchange: describe answered,
work FAULTED `agent`. Root cause, from the captured provider stdout in
the NEW room: "Failed to authenticate: OAuth session expired and could
not be refreshed" — api_error, 39 ms, zero cost. The mounts of the failed
runtime are the reviewed corrections working live: per-attempt /scratch
disk bind (assignment home), room at /run/baton/attempt-logs with clean
`finished` sidecars, decoy tmpfs at /run/baton/logs, line checkout at
/output, credential slot ro. Verification streams honestly absent (the
provider failed first). Allocation reserved, episode unended — the
already-proven fresh-Job-beside-reserved cadence applies. Evidence with
stream hashes and owner decision points: LIVE-JOB3-OUTCOME-227653.json.
Spend this claim: zero provider tokens; read-only observation only.

## Claim227726 — job-4 recovery prepared; credential freshness measured STALE

Per owner 06:40:26Z (relogged; "do it"). Changed paths pinned first
(dossier only: composed documents, JOB4-RECOVERY-227726.md, these
entries). PREPARED: `compose-pool-207219.py --instance <06-27-56Z> --pr
--base 446fa8f7… --job w202663-first-development-job-4 --work 2` — zero
refusals; coder-4/reviewer-4, Work baf2e7fe-W2, job input identity
fd273ef0…, image d1e2869e… verified in the composed worker deployments;
submission names job-4 ONLY; bootstrap inputs carry both jobs' workers
(job-3's unchanged). Read-only revalidation: generation 1 holds exactly
job-3's workers, one reserved allocation (job-3 implementation), manager
running — the round-1 scheduler proofs cover this exact widening.
MEASURED BLOCKER, metadata only: the mapped operator file
/home/sl/.claude/.credentials.json has mtime 2026-09-17T15:29:42Z and
nothing under ~/.claude or ~/.config/claude* changed after job-3's
06:30:25Z failure — the reported relogin did not reach the mounted file,
so the package's step 1 is a fail-closed FRESHNESS GATE (refuses while
the file predates the failure; logic dry-run: refuses now, correctly).
Rotation hypothesis recorded as hypothesis only. NO apply, restart,
submission, live call, credential read/mutation or cleanup this claim;
job-3 and all prior evidence preserved. Owner commands:
JOB4-RECOVERY-227726.md (freshness gate → supported apply →
check-policy-pin pool → stop/start → submit job-4). Zero provider
spend. Criterion 2 open.

## Claim227806 — job-4 observed to terminal: auth + full episode + candidate, then D10

Observed live from submission to terminal (read-only polling of the
canonical snapshot, the room, and read-only docker inspect). AUTH
SUCCEEDED (the second relogin reached the correct file, 06:48:30Z);
container 0f9fd4e5… ran 06:49:52→07:03:36Z; the provider COMPLETED a
full real episode (74 turns, ~13.7 min, $7.370573, success summary);
the two-file candidate sits untracked in line-a705b15d at exactly the
accepted base; `/scratch` was used live and left empty; provider
streams captured in the moved room, sidecars `finished`, zero
contamination, no fork failures. Then work FAULTED (`agent`) with NO
verification captures — localized to the post-provider
`_checked_tree(candidate)` and REPRODUCED deterministically against the
retained checkout: refuses on the repository's own committed symlink
(work/open/finding-protocol-11-reference-semantics), and with links
tolerated would refuse again at 19,553 entries / 652 MB vs the 2000 /
64 MiB bounds. Pinned as FINDING D10 with the bounded correction shape
(line profile: hold the provider to its CHANGES, not the whole
committed repository) for owner selection — no implementation under
this observation handoff. Job2 reinterpretation recorded as hypothesis.
Everything preserved as found; job-4's allocation reserved, episode
unended, exactly job-2/3's terminal shape the scheduler proofs already
cover for a fresh successor. Spend: ONE real producer episode
($7.37, 74 turns); no reviewer episode; no verdict. Criterion 2 open.

## Claim229926 — D10 correction implemented, proven and closed on the retained checkout

Owner 12:41:22Z selection; review-2026-09-21T07-13-00Z.md revalidated
against the tree; ownership pinned in PLAN (12:43Z) before editing.
IMPLEMENTED in v12/worker/claude_agent.py (copy profile byte-untouched):
`_baseline_tree` (pinned entry head, three modes, bounded),
`_line_delta` (git-blind anchored no-follow walk; byte-identical blobs
and exactly-committed file/dir links pass as baseline; changed/added
files are candidate material under the unchanged 2000/64MiB payload
bounds; provider/retargeted/replacing links and special files refuse by
name; deletions their own set; NEW discovery bounds 200k visits / 4GiB
proof-reads on the walk itself), `_line_revalidated` (fresh delta:
ceilings again, measured bytes held, deletions held),
`_representable_delta` + `_measured_modes` inside `_identical` (all
existing rules kept; ignored-addition refusal in place; committed modes
proven regular per measured path), `_measured` retired with its
whole-tree subject. PROVEN: owned suite 220/220 (one existing case
updated where the assume-unchanged attack is now caught one gate earlier
with the same refusal-and-nothing-published outcome; 14 new cases:
real-shape baseline past both payload bounds with committed file+dir
links publishing a small patch through REAL verification and
publication; untouched linked baseline = honest no-candidate; the full
negative set). CLOSED ON THE LIVE EVIDENCE: `_line_delta` over the
retained job-4 checkout answers 0.836 s, exactly the two candidate
files at review227929's own hashes, no deletions. Image rebuilt
sha256:d447cf38… (gate 16 OK; in-image byte identity 1be1e197…);
composer PROVIDER_IMAGE moved with history; adjacent suites 219 OK.
Host runtime UNCHANGED by D10 → operational next steps (in
D10-EVIDENCE-229926.json, for owner execution after review): compose
job-5 beside preserved job-3/job-4, supported apply + pool pin gate,
stop/start, submit job-5 only — no reinstall. Nothing live, applied,
restarted, submitted, credential-touched or cleaned; Jobs 1–4 and all
retained bytes preserved; retained candidate files remain unreviewed
evidence. Spend this claim: zero provider episodes; deterministic tests
and one read-only retained-checkout inventory. Criterion 2 open.

## Claim230107 — narrowed collection (owner 12:47:17Z; review230027 R1/R2 closed)

Poke229962 was acknowledged mid-review (seq230039); on redelivery the
narrowed design was pinned in PLAN (13:11Z) BEFORE the affected edits.
IMPLEMENTED: `_line_status`/`_line_delta` collect from Git's own
porcelain listing (closed parse; rename/copy records refuse; one
collection bound MAX_LINE_STATUS_ENTRIES=20000) — the whole-baseline
walk, `_baseline_tree`/`_baseline_link`/`_git_blob_digest` and the
discovery ceilings are REMOVED, not re-thresholded. Per entry: regular
→ measured (anchored no-follow, payload ceilings on the changed set);
link among changes → refuses (the retained no-follow/external
protection); special → excluded+disclosed, never read; absent →
deletion. `--ignored=matching` feeds the disclosure only; the line
result gains `collection` (capped lists, whole counts, the
verification-context note). `_line_revalidated` re-proves measured
bytes and deletions; `_identical` keeps every rule with both-direction
set equalities, `_identical_bytes`, committed-mode proofs; the
measured-not-committed refusal is now a genuine delivery-integrity
message (an ignored file can never reach it). Two owned tests rewritten
to retire the superseded whole-tree guarantees BY NAME (ignored
dependency → publishes+disclosed+provably undelivered; assume-unchanged
→ hidden edit neither measured nor delivered, delivered bytes exact);
review230027's R1 probe added as a positive. Suite 221/221; image gates
22 OK. CLOSURE: the narrowed inventory answers the retained job-4
checkout in 0.066 s, exactly the two files at the reviewer's hashes.
R2: D10-EVIDENCE-230107.json validates with json.loads (229926 artifact
preserved as history); JOB5-PACKAGE-230107.md carries the explicit
fail-closed sequence with exact operands. Image sha256:5c2eb55d… built
and pinned. Nothing live/applied/restarted/submitted/credential/
cleanup; Jobs 1–4 preserved; zero provider spend. Criterion 2 open.

## Claim230245 — job-5 observed to terminal: COMPLETE, INDEPENDENTLY ACCEPTED

Review230179 had approved the preparation; the owner executed
JOB5-PACKAGE-230107.md (~13:29Z) and this claim observed read-only to
the report-and-hold terminal. Producer attempt-cc65c5de: 61 turns,
690024 ms, $5.787505, is_error false — wrote exactly
v12/python/tools/pool.py + tests/tools/test_pool.py at the accepted
base. The corrected frozen verification (FULL family, /scratch fixture
root) exited 0 in-container — first time ever. Narrowed collection
published disposition 'candidate', head a12759d2, two paths, collection
null; change.patch/objects.bundle/verification.txt/result.json hashed
in the evidence. Reviewer attempt-64e11719 (baton.claude-reviewer-5):
27 turns, 218985 ms, $1.822204 — report.json opens 'VERDICT: accepted',
tree-verified, one non-blocking defect + the known routing limitation
recorded. Durable through public readers: attachment ENDED
(13:41:55→13:45:38), checkpoint-dfabedb1 FROZEN rev 1, LINE ACCEPTED,
declared_base 446fa8f7. Both stages completed; allocations released
cleanup-retained; canonical snapshot. All corrected layers held live.
Evidence: LIVE-JOB5-OUTCOME-230245.json. Jobs 1–4 untouched; nothing
retried/restarted/resubmitted/cleaned; observation spend zero; job-5
provider spend $7.609709 total. Criterion 2's independent acceptance
exists and is held for the owner's explicit integration decision.
