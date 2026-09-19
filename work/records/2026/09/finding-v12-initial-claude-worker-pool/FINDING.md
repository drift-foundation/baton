# Prepare the initial Claude worker pool for v12 development

Baton Work `W202663` (`2b077949-W202663`), route `impl`, classification
`design-choice`, priority high. This record is the canonical dossier the Work
binds; it is created before implementation because `AGENTS.md` requires a
confirmed decision to be pinned in a repository record rather than left in a
message thread.

## The owner's decision — confirmed 2026-09-18T10:53:40Z (W202663 M202663)

Slawomir, through `baton.slaw`, selected the shape of the first Claude-backed
v12 development capacity. The decision is quoted from the canonical thread
`2b077949-T202663` message `202663` rather than paraphrased, because every
later step here is bounded by one of its clauses:

> Owner selects /home/sl/baton-v12-instance-2026-09-18T10-38-52Z as the fresh
> v12 development instance. Pin this decision and plan in a new bound canonical
> dossier before implementation. Prepare compatible Claude provider and
> integration images incorporating accepted W197661 and W198667 fixes, with
> exact source and image provenance. Configure distinct Claude coder and
> reviewer identities through the existing supported deployment path. Verify
> one small deterministic Job through independent review and report-and-hold,
> with usable logs. Preserve prior instances. No live-model execution, Git
> mutation or implementation of the new worker-add interface in this
> prerequisite. Return for independent review through baton.bug with exact
> commands to launch the first Claude-backed development Job. Record the
> intended first development task: user-managed addition of workers to an
> existing pool, independently of bootstrap and individual Jobs. Coordinate
> existing readiness follow-up Work rather than duplicating it.

### What that selects, clause by clause

**The instance.** `/home/sl/baton-v12-instance-2026-09-18T10-38-52Z` is the one
development instance this Work configures. **Observed** at claim time: it is an
installed standalone deployment carrying authority
`a92e1d717fcc40fe9972df8b2497c055`, schema
`baton.v12.stage-execution-deployment/2`, `"workers": []` and
`"job_bindings": []` — a fresh install that configures no capacity, which is
exactly what `tools/bootstrap.py` documents a fresh install to be. Its runtime
was packaged from source commit `e486652c…`, `dirty: true`.

**Preserve prior instances.** `/home/sl/baton-v12-instance` and
`/home/sl/baton-v12-instance-2026-09-17T20-29-21Z` are NOT touched, reused,
rebuilt, cleaned or repointed by this Work. The second of them is the nearest
working template for a Claude-identity pool and is read as evidence only.

**The images.** Two supported recipes, built from the current tree so that they
carry the accepted W197661 and W198667 corrections:
`v12/worker/Dockerfile.claude` (the provider image) and
`v12/worker/Dockerfile.integration` (the integration image, whose base is an
explicitly named provider digest and has no default). Exact source and image
provenance is a deliverable, not a by-product: both recipes' own comments, and
W55361, establish that these builds are not reproducible across days, so the
artefact is SELECTED by digest and a build is a CANDIDATE until a deployment act
selects it.

**Distinct coder and reviewer identities.** Two different participants, so that
`stage_execution`'s independence rule — implementation and review may share no
participant — is satisfied by construction rather than by convention.

**The existing supported deployment path.** `just bootstrap` with a worker-
bearing input document, re-run against the already-installed destination. The
owner explicitly excludes implementing the new worker-add interface here.

**One small deterministic Job, through independent review and report-and-hold,
with usable logs.** Deterministic, and `No live-model execution`, together
select the fake/replay provider default that `AGENTS.md` already makes the v12
standing rule. This Work therefore proves the *deployment and lifecycle*, not
the model.

## Confirmed inputs this record depends on

- **Confirmed.** `W197661` ("V12 worker launch version mismatch silently waits
  on stdin") is closed `satisfying`; dossier
  `work/records/2026/09/finding-v12-worker-launch-version-mismatch`.
- **Confirmed.** `W198667` ("Retain raw attempt logs for v12 development
  diagnosis") is closed `satisfying`; dossier
  `work/records/2026/09/finding-v12-durable-development-logs`. Its PLAN step 1
  is the recipe change this Work builds: both supported images carry
  `attempt_log_format.py`, and "any new image is its own provenance".
- **Observed.** Both recipes in the current tree carry the
  `COPY python/src/baton_v12/attempt_log_format.py /opt/baton/attempt_log_format.py`
  layer, so the W198667 correction is in the bytes a build from this tree
  produces. No production image carrying it has been built yet — W198667's own
  evidence covers a private fixture image only.

## The intended first development task (recorded, not implemented)

The first Claude-backed v12 development Job is to deliver **user-managed
addition of workers to an existing pool, independently of bootstrap and
individual Jobs**. Today the only supported way to add capacity is to re-run
`just bootstrap` with a worker-bearing input document, and `tools/bootstrap.py`
states the coupling out loud: "A worker is configured WITH the Job it serves:
its `deployment` carries a digest-sealed input manifest naming an Authority and
a Work". That coupling is the defect the first development Job addresses. It is
**Open** here and is deliberately NOT implemented by this prerequisite.

## Boundaries

- No live-model execution. No Git mutation of any kind.
- No implementation of the worker-add interface.
- No change to prior instances.
- Existing readiness follow-up Work is coordinated, not duplicated: no new Work
  is created for a readiness gap that an open Work already owns.

## 2026-09-18T21:3xZ — Two defects measured while preparing the pool

### D1 — The accepted W198667 recipe change could not build (corrected here)

**Confirmed, measured.** Both supported recipes carry
`COPY python/src/baton_v12/attempt_log_format.py /opt/baton/attempt_log_format.py`,
which is W198667 PLAN step 1. `v12/.dockerignore` is a deliberate ALLOWLIST —
`*` followed by re-includes — and it was not widened with them. Every build of
either supported image therefore failed:

```
COPY failed: file not found in build context or excluded by .dockerignore:
stat python/src/baton_v12/attempt_log_format.py: file does not exist
```

Measured with a two-line probe recipe over the real `v12` context before any
production build was attempted, so the diagnosis is not inferred from a long
build's failure. W198667's own PLAN named "and the prepared build contexts that
mirror them" as part of step 1; the checked-in context was the one that did not
get it, which is why its fixture smoke passed while no supported image could be
produced at all.

**Corrected in this Work**, because the owner's deliverable is images that
carry that fix and there is no way to produce one otherwise. The correction is
one re-include naming the ONE file — not the `baton_v12` directory — so the
allowlist keeps the property its own comments defend: nothing else can appear
in the context, so nothing else can change under it. `v12/.dockerignore` is a
file W198667 owned; the change is flagged in the handoff for the reviewer to
rule on rather than presented as uncontested.

### D2 — One Job cannot serve implementation/review and integration from two images

**Confirmed, measured** by `probe-one-image-per-job-202663.py`, results in
`PROBE-one-image-per-job-202663.json`. This BLOCKS the pool the owner selected,
and it is a product limitation rather than a composition mistake.

Three product rules compose into it:

1. `tools/single_worker.py:267` — a worker's configured `image_digest` must
   EQUAL its own `input_manifest["worker_image_digest"]`.
2. `tools/single_worker.py:1303` — a Job's `input_digest` must EQUAL that
   manifest's `manifest_digest`, and `baton.v12.job-submission/2` gives a Job
   exactly ONE `input_digest` beside a list of stages.
3. `worker_manager/oci.py` `run_vector` ends `argv.append(image_digest)` and
   returns: the runtime is started from the image and runs the image's own
   ENTRYPOINT. No program operand is composed, so a role cannot select a
   different program inside one image. (`exec_vector` does take a program, but
   `worker_entry.converse` is the diagnostic/test transport, not the production
   launch.)

Therefore every worker serving one Job is on one manifest, on one image, on one
entrypoint. The two supported recipes are two images with two entrypoints:
`Dockerfile.claude` → `dogfood_entry.py`, `Dockerfile.integration` →
`integration_entry.py`. A pool using both cannot be configured for a Job that
reaches integration.

**What was actually measured**, on the REAL validators and a REAL composed
document (the prior instance's integration worker, read only):

| probe | result |
| --- | --- |
| the document unchanged, held as `integration` | accepted (the control) |
| the same document moved onto the implementation workers' image | `ContractRefusal: the bootstrap input manifest names another worker image` |
| this Work's own integration image under a resealed manifest naming this Work's provider image | `ContractRefusal: the bootstrap input manifest names another worker image` |

The third probe's manifest is RESEALED with the product's own canonical digest.
A first draft moved `worker_image_digest` and left `manifest_digest` alone, so
it refused one rule earlier — "a manifest that does not identify itself is not
one" — and proved nothing about the image pairing.

Rule 2 is READ from the source and from W197661's own measured account of it
("three role-specific manifests produce three seals of which the Job can name
exactly one … review and integration were refused with 'the Job names another
bootstrap input'"). It is not claimed as newly measured here.

**The prior instance carries this latent.** `2026-09-17T20-29-21Z` is
configured with two images (`2e222e4c…` for implementation and review,
`d739fefe…` for integration) and two manifest digests (`17081efd…` and
`c0e1f238…`). It is a configuration that `bootstrap` accepts and that refuses
at launch. It was read and NOT changed, started or reused, as the owner's
"Preserve prior instances" requires.

**Why this Work does not route around it.** W197661's fixture solved the same
wall with a single image whose entry dispatches on the delivery. Doing that for
production means a new recipe and a new entrypoint — product design, adjacent
to the worker-add interface the owner explicitly excluded from this
prerequisite, and a selection only the owner can make. Configuring all three
roles on the provider image instead would put `dogfood_entry.py` on the
integration stage: a pool that starts and does the wrong work, which is worse
than one that refuses. **Open** — the decision belongs to the owner.

## Review206578 — D1 accepted; D2 confirmed and bounded choice proposed

review-2026-09-18T21-44-22Z.md and REVIEW-EVIDENCE-206578.json record independent validator
reproduction and image metadata/hash checks. D1 allowlist change accepted. D2
remains incomplete; recommend owner select combined delivery-dispatched image
without changing manifest equality or implementing worker-add. This is a proposal,
not owner selection. Pool/lifecycle/logs and concrete launch commands remain due.
Complete copied source_profiles provenance before final image selection.

## Owner ruling — 2026-09-18T22:01:51Z (W202663 pass event 206702)

**This supersedes the "Open — the decision belongs to the owner" ending of D2
above, and it supersedes review206578's combined-image recommendation.** Both
are preserved as the reasoning that led here; neither is current.

Quoted from the canonical pass event rather than paraphrased:

> Owner clarification: D2 is a gap/bug in realizing the existing provider-
> diverse architecture. Do not implement the combined-image recommendation. Pin
> this ruling in FINDING and update PLAN before implementation. Revalidate the
> existing contracts and correct the coupling between shared Job input identity
> and worker-specific runtime manifests. Workers must independently select
> immutable images with their own dependencies; provider image, credential
> profile, role and participant remain separate. The same Codex image can use
> different account profiles, including codex-pushcoin; images are not
> account-specific. Support different images across implementation, review and
> integration while preserving exact per-attempt input, image and provenance
> validation, identity separation and recovery attribution. Authorize the
> bounded contract/schema changes necessary for that correction; document
> compatibility consequences and coordinate existing Work. Prove heterogeneous-
> image execution deterministically, including mismatch refusal, then complete
> the original Claude pool and report-and-hold verification with usable logs
> and concrete commands. No live models, worker-add UI, Git mutation or
> unrelated redesign. Return the complete candidate for independent review;
> report any independently schedulable prerequisite explicitly.

### What changed, and what my D2 account got wrong

D2 measured the refusals correctly and drew the wrong conclusion from them. I
reported one image per Job as a property of the architecture. The owner rules
that it is a **gap in realizing** an architecture that is already meant to be
provider-diverse. The revalidation below establishes that the owner is right on
the code's own evidence, so this is not deference: the launch contract already
holds the two facts apart, and only the deployment preflight conflates them.

### Revalidation of the existing contracts — Confirmed, read from the tree

**The architecture already separates the two identities.**
`worker_manager/launch.py:137` closes the Job execution context over
`job_input_digest` AND `runtime_input_digest` as two distinct members, and its
own comment rules on exactly the question D2 raised:

> JOB INPUTS AND RUNTIME INPUTS ARE DIFFERENT FACTS and are both carried rather
> than compared: a review or a derived judgment legitimately consumes a frozen
> input that is not the Job's original one, so requiring them equal would refuse
> the ordinary case. What is required is that each is stated.

So a worker's runtime input is already, by contract, allowed to differ from the
Job's input. The coupling is not in the design; it is in two comparisons that
were written as though there were only one identity.

**The three rules D2 measured, reclassified against that finding.**

| rule | site | verdict |
| --- | --- | --- |
| a worker's `image_digest` must equal its own manifest's `worker_image_digest` | `tools/single_worker.py:267` | **Correct, keep.** It is worker-local: it binds a worker to the image its own manifest names, which is exactly the per-attempt image validation the ruling requires preserved. |
| a Job's `input_digest` must equal the worker's **full** `manifest_digest` | `tools/single_worker.py:1303` | **The gap.** It compares a Job-scoped identity against a worker-scoped document, so every worker-specific runtime fact — the image above all — is forced to be Job-wide. |
| the runtime runs the image's own `ENTRYPOINT`; `run_vector` composes no program operand | `worker_manager/oci.py` | **Correct, keep.** With the gap closed this stops being a limitation: each worker selects its own image, so each role gets the entrypoint its own image carries. It is what makes provider-diverse pools work, not what prevents them. |

**The second conflation, which D2 did not name.**
`integration/admission.py:265` does the same thing at import time:
`_same("the input digest", proposal["input_digest"], job["input_digest"])`,
where the proposal's value reaches it from `integration/driver.py:439` as the
producing worker's own `input_manifest_digest`. Correcting only the preflight
would let a heterogeneous Job run and then refuse at import, which is worse
than refusing early. Both sites are in scope for one correction.

**Sites that are already right and must not be touched.** Everything that
records or reads a RUNTIME identity stays runtime: `record_attempt(...
input_digest=manifest["manifest_digest"], image_digest=..., toolchain_digest=...)`
in `single_worker`, `output.py:394`, `provider_context.py:587` and
`review_cycles.py:1429` all load or compare the attempt's own manifest. That is
the per-attempt input, image and provenance validation and the recovery
attribution the ruling requires preserved, and it is preserved by leaving it
alone.

### The correction this selects

A Job's `input_digest` names the **shared Job input identity**: the canonical
digest of a worker's input manifest with the worker-runtime members projected
out. Each worker keeps its own full, immutable `manifest_digest` as its runtime
identity. The two comparisons above compare the derived shared identity;
everything else keeps comparing the runtime one.

The projected-out members are the worker-runtime axis and nothing else —
`worker_image_digest`, `toolchain_digest`, `runtime_profile_digest`,
`credential_policy_digest`, and `manifest_digest` itself. That set is the
ruling's own list: "provider image, credential profile, role and participant
remain separate", with `toolchain_digest` travelling with the image it
describes and `runtime_profile_digest` already expressible per stage because a
Job's stages each name their own `profile_name`/`profile_digest`.

Everything else in the manifest stays shared and therefore stays Job-identical:
`work_ref`, `human_contract`, `sources`, `outputs`, `record_binding`,
`role_instructions_digest`, `policy_digest`, and the resource, network, mount,
tool and retention policy digests. A worker that changed any of those would
still be refused, which is the identity separation the ruling requires kept.

**Compatibility consequence, stated rather than discovered later.** A Job whose
`input_digest` was composed as the full `manifest_digest` no longer matches.
Every such deployment must recompose its submission. There is exactly one on
this host — the prior instance `2026-09-17T20-29-21Z` — and it is already
unlaunchable for the D2 reason, so nothing that works today stops working. No
frozen schema asset changes and no image is invalidated: the correction is in
which digest a Job names and what two comparisons compute, not in the manifest
document's shape.

## Review206898 — migration boundary clarification

review-2026-09-18T22-36-46Z.md and REVIEW-EVIDENCE-206898.json reject incomplete migration.
Owner206702 supersedes reviewer206578 combined-image recommendation. The planned
dogfood_operator:1221 change is explicitly superseded: record_attempt must retain
the runtime manifest digest; line1210 is a standalone offer, requiring separate
caller analysis. Projection still includes manifest IDs/timestamps/role instructions;
classify and prove independently composed heterogeneous manifests and legacy
compatibility before acceptance. No additional permission gate for continuing
the authorized migration; preserve exact runtime attribution and old evidence.

## Review207096 — bounded projection/preflight slice accepted

review-2026-09-18T23-07-21Z.md and REVIEW-EVIDENCE-207096.json:325 focused tests pass.
Runtime/Job inventory correction and targeted projection/preflight slice accepted.
ThreeWorkersOneJobThreeImages invokes only _held/_matches: prior launch/claim
proof wording is superseded; heterogeneous execution/integration remains due.
Reported20-vs13 error delta remains unattributed beyond the named isolated subgroup;
no whole-regression-resolution conclusion. Finish authorized lifecycle/pool/logs/
provenance/commands, and pin current eight-member projection as explicit supersession.

## 2026-09-18T23:xxZ — the projection rule, superseded and widened

**This supersedes the two paragraphs above beginning "The projected-out members
are the worker-runtime axis and nothing else" and "Compatibility consequence,
stated rather than discovered later".** Both are kept as written because the
reasoning that was wrong is how the next reader knows why the current rule is
not the obvious one; neither is current.

### The five-member rule was not enough — measured

Review206898 [R2] probed the first projection over a valid retained conformance
manifest and measured that changing only `manifest_id`, only `created_at`, or
only `role_instructions_digest` changed the SHARED identity as well as the
runtime one. Reproduced here as
`test_manifest_rules.TheJobInputIdentityIsAClassification`.

That defeated the whole purpose. Three manifests **independently composed** for
three workers each carry their own id and creation instant —
`dogfood_operator.input_manifest` authors `manifest_id` from the attempt id and
`created_at` from the clock — so under the five-member rule they could never
have agreed about a Job. Only three CLONES of one document would have agreed,
and a pool of clones proves nothing about the heterogeneity the owner ruling
exists to permit.

### The current rule is eight members, and it is a classification

`contracts/manifest.JOB_INPUT_EXCLUDED`, with the reason each member is on its
side recorded at the tuple:

| projected out | why |
| --- | --- |
| `worker_image_digest` | the image this worker selects — owner ruling 206702 |
| `toolchain_digest` | travels with that image |
| `runtime_profile_digest` | already per-stage; a Job's stages each name their own `profile_name`/`profile_digest` |
| `credential_policy_digest` | the credential profile — owner ruling 206702 |
| `role_instructions_digest` | **new.** An implementer and a reviewer are told different things, and the ruling makes role separate |
| `manifest_id` | **new.** Authored per manifest, from an attempt id |
| `created_at` | **new.** Authored per manifest, from a clock; two manifests composed a second apart are not two Jobs |
| `manifest_digest` | the runtime identity itself |

Everything else stays shared and stays compared whole: `work_ref`,
`human_contract`, `sources`, `outputs`, `record_binding`, `policy_digest`, the
resource, network, mount, tool and retention bounds, `extensions`, `schema`,
`version` and `assignment_contract`. **The shared policy digests are
deliberately not dropped** — review206898 [R2] warned against mechanically
projecting out every policy member, and only the credential profile leaves,
because the ruling names that one separate.

### The compatibility claim above is WITHDRAWN as unsupported

The superseded paragraph asserted that "There is exactly one on this host — the
prior instance `2026-09-17T20-29-21Z` — so nothing that works today stops
working." **That is withdrawn.** I inspected one host's instance directories; I
did not and cannot enumerate every deployment, retained Job or historical
record that named an input manifest's whole digest, and review206898 [R3] is
right that a survey of one machine is not a product-wide guarantee.

What is actually established, and its limits stated:

- **Confirmed.** The projection differs from the whole manifest digest even for
  a single unchanged homogeneous manifest
  (`test_the_two_identities_are_different_documents`). Every Job submitted
  under the old rule therefore refuses at `_matches`. This is a semantic
  change, not a widening.
- **Confirmed.** The refusal is fail-closed and diagnosable: a Job naming the
  whole runtime manifest digest is told which digest it named, what a Job names
  now, and that its retained submission is evidence and is not rewritten for
  it. It is distinguishable from a Job about another input, and a case proves
  the two read differently.
- **Open.** That is ONE refusal at ONE boundary. It is **not** completed legacy
  recovery or migration coverage across every stage, entrypoint and retained
  record, and must not be read as such. What a retained pre-correction Job,
  attempt or proposal does on every other path is unmeasured.
- **Unchanged and deliberately so.** No retained submission, attempt record,
  result manifest or proposal is rewritten. Provenance is preserved; migration
  is resubmission, performed by whoever owns the deployment.

## Review207195 — correction accepted; proof limits and original delivery remain

review-2026-09-18T23-23-58Z.md and REVIEW-EVIDENCE-207195.json record 164 passing focused tests.
The heterogeneous fixture uses a simulated engine and locally executed workload;
real-container and full terminal integration claims are superseded by this
bounded description. The shared-member negative only compares digests. Complete
actual admission refusal, terminal heterogeneous/recovery proof and steps3a/7/8/9.
No new owner selection or combined image; no external blocker reported.

## Review207292 — installed runtime provenance gap

review-2026-09-18T23-38-01Z.md records16 passing focused tests and matching applied/prepared
configuration. Original frozen executable identity378ec932 remains paired with
new source-validated projection configuration. Compatibility is unproved;
resolve exact runtime provenance and use installed path for deterministic proof.
Pool preparation accepted; operational readiness and whole Work remain open.

## 2026-09-18T23:5xZ — D3: the selected instance cannot receive a corrected runtime

**Confirmed, measured, and it is a concrete blocker on step 8 as scoped.**
Review207292 [R1] asked whether the installed frozen runtime can execute the
pool composed in claim207219. It cannot be shown to, and the supported path
cannot give it one.

### What was measured

| fact | value |
| --- | --- |
| installed runtime | `/home/sl/baton-v12-instance-2026-09-18T10-38-52Z/distro/baton-v12-stack`, sha256 `378ec932…`, equal to `instance.json` `identity.sha256` |
| its packaged source state | `build-stamp.json`: commit `e486652c`, dirty, **77 changed entries** |
| a runtime built from the tree NOW | sha256 `48b12f15…` |
| its packaged source state | same commit, dirty, **92 changed entries** |

So the installed runtime is **a different artefact, packaged from a different
source state**, than one built from the corrected tree. The build stamp is
captured at package time and travels inside the bundle, which is what makes
that a content fact rather than a file-timestamp inference.

**What was NOT established, stated because the distinction matters.** Searching
either executable for `job_input_identity` finds nothing — in the fresh one
too, which certainly contains it. The application modules are compressed `.pyc`
inside the frozen archive, so identifier strings do not appear in the file. My
first attempt at this used exactly that search, and it was inconclusive in both
directions; review207292 was right to warn against turning weak evidence into a
content proof, and the warning applies to my own probe.

### The supported path refuses to replace it — measured, not read

```
$ python3 -m tools.bootstrap --inputs pool-bootstrap-inputs.json \
    --destination /home/sl/baton-v12-instance-2026-09-18T10-38-52Z \
    --distro /home/sl/src/baton/v12/python/build/out/distro
refused: there is already a runtime at
/home/sl/baton-v12-instance-2026-09-18T10-38-52Z/distro; nothing here upgrades
a deployment in place. Stop that instance and prepare a new destination if you
mean a different runtime.
```

Exit 2, and refused **before any effect** — `_admissible` performs this check
before the destination lock is taken, so nothing was copied, replaced or
removed. `v12/STACK.md` states the same rule in prose: *"Nothing here upgrades
a deployment in place."* It is a deliberate product decision, not a gap:
replacing a runtime under a stack that may be serving is not something a setup
command may do.

### What this blocks, exactly

- The pool composed and applied in claim207219 is valid **for the corrected
  code** — `stage_execution.held_configuration` from the current tree accepts
  it, and the reviewer independently confirmed the applied `deployment.json`
  equals `pool-stage-execution.json`.
- The documented `just start` path on that instance runs the **installed**
  runtime, and that runtime is not the corrected one.
- So step 8's deterministic terminal run **on this instance** cannot be honest:
  it would either exercise the checkout instead of the installed path — which
  review207292 explicitly forbids calling installed-runtime proof — or run a
  scheduler whose `_matches` still compares the whole manifest digest and would
  refuse this heterogeneous pool at admission.

### The resolutions, and which one is not mine to take

1. **Prepare a new destination** with the corrected runtime. This is the
   supported path the refusal itself names, it preserves every prior instance,
   and it is how W197661 ran its own lifecycle. But the owner selected
   `/home/sl/baton-v12-instance-2026-09-18T10-38-52Z` **by path** in message
   202663, and moving the selected development instance is an owner decision.
2. **Stop that instance, and re-prepare that destination.** The refusal names
   stopping it; re-preparing the same path still requires the runtime, justfile,
   instance selector and stores not to be there, so this is a destroy-and-
   recreate of the owner's selected instance, with its Authority, its Work
   `a92e1d71-W1` and its bootstrap record. Not something to do unasked.
3. **Use a separate disposable destination for the step-8 verification only**,
   leaving the owner's instance exactly as it is and reporting that the
   verification ran elsewhere. This is within implementation scope and is the
   path this Work should take next; it proves the runtime and the lifecycle
   without touching the owner's selection.

**Open.** Resolution 3 is the next implementation step and needs no decision.
Resolutions 1 and 2 concern the owner's named instance and are reported here
rather than taken.

## Review207341 — D3 owner decision recommended

review-2026-09-18T23-44-44Z.md corroborates installer refusal and runtime identity differences.
Exact old/new function contents remain unproved by stamp counts. Recommend
owner select /home/sl/baton-v12-instance-w202663-corrected for development,
preserving every old instance. This is a proposal, not a selection. Disposable
verification alone cannot discharge selected development readiness.
