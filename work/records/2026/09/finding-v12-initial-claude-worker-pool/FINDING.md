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

## Owner supersession — 2026-09-19T02:07:56Z (W202663 pass event 208215)

**This supersedes the instance selection pinned at the top of this record.**
`/home/sl/baton-v12-instance-2026-09-18T10-38-52Z` is no longer the development
instance; it is preserved as evidence. Quoted from the canonical pass event:

> Owner installed and selects /home/sl/baton-v12/instance-2026-09-19T02-05-20Z
> as the replacement development instance. Runtime sha256
> 48b12f1559bdf08257c7d677df799171b0b43f6ecd6c4005ca93b52e953f5232; this
> establishes identity, not behavioral acceptance. Pin this supersession before
> proceeding. Older instances were moved to /home/sl/baton-v12/archive/ under
> their original basenames; preserve them as evidence and account for relocated
> paths. Future instances belong under /home/sl/baton-v12/, not directly under
> /home/sl. Continue W202663: verify installed runtime and development-source
> prerequisites, configure the distinct Claude pool with heterogeneous images,
> complete deterministic terminal report-and-hold, logs, recovery attribution
> and refusal coverage, then verify final pool/pins and provide exact launch
> commands. Preserve provenance limitations honestly. No live models,
> worker-add interface, Git mutation or another destination change.

### What this resolves, and what it does not

**D3 is resolved by owner act, not by anything this Work did to that
instance.** The blocker was real — the installer refuses in-place replacement —
and the owner's resolution is the one the refusal itself names: a fresh install
at a new destination. The old instance was moved, not modified.

**Verified here, read-only:** the new destination's `instance.json` records
`identity.sha256` `48b12f15…`, equal to the runtime built from the corrected
tree in claim207307, with in-bundle build stamp commit `e486652c`, dirty, **92
changed entries** — the same source state that runtime was packaged from. Its
Authority is `cf92cbff7ffc456c96e9a6345de293f5`, a **different** identity from
the superseded instance's `a92e1d71…`, which is what a separate installation
means. Its pool is empty, its Job bindings are none and its
`policy_generation` is 1: a fresh install that configures no capacity.

**The owner's own qualification is kept, not softened.** A matching digest
"establishes identity, not behavioral acceptance". Review207292 said the same
about the counts: 77 against 92 changed entries proves two different artefacts
from two different source states, **not** which functions differ. That the
installed runtime now carries this Work's projection correction remains
**Inferred** — from the build stamp and from the fact that I built that artefact
from this tree — until a bounded behavioural or archive proof measures it. The
deterministic terminal run through the installed path is what will measure it.

### Paths every later reader must account for

| was | is now |
| --- | --- |
| `/home/sl/baton-v12-instance-2026-09-18T10-38-52Z` | `/home/sl/baton-v12/archive/baton-v12-instance-2026-09-18T10-38-52Z` |
| `/home/sl/baton-v12-instance-2026-09-17T20-29-21Z` | `/home/sl/baton-v12/archive/baton-v12-instance-2026-09-17T20-29-21Z` |
| every other `/home/sl/baton-v12-*` instance and lifecycle root | `/home/sl/baton-v12/archive/<original basename>` |

Every absolute path in this dossier's earlier entries, in
`COMMANDS-202663.md`, in `compose-pool-207219.py` and in
`POOL-COMPOSITION-207219.json` that names one of those roots now describes an
archived location. Those records are **evidence of what was done at the time**
and are not rewritten; what is current is the new destination. Future instances
belong under `/home/sl/baton-v12/`.

## Review208310 — admission accepted; logs and terminal result remain open

review-2026-09-19T02-24-24Z.md distinguishes three attributed attempts from actual
integration-image execution (not started). Integration claimed before expiry;
expiry alone is not stall cause. Six absent streams establish reader behavior,
not captured useful logs. Preserve immutable first-run inputs and obtain fresh
cleanup/fencing observations before supported recovery/fresh execution.

## Review208349 — installed tick refusal found; prior silent-tick diagnosis superseded

review-2026-09-19T02-30-18Z.md and REVIEW-EVIDENCE-208349.json retain the installed
manager log: integration deferred policy/denied because producer required tests
exited1. Retained verification command expects a different filename AND content
from the fixture. Receipt issuance is correctly gated before any side effect.
This supersedes claim208326 silent-tick/no-refusal and mismatch-only-later claims.
Correct immutable inputs via supported fresh execution/recovery; do not weaken
verification or manufacture receipts. All remaining delivery scope stays open.

## 2026-09-19T02:4xZ — D4: a Job with new workers cannot be added to an instance whose target is live

**Confirmed, measured, and it currently leaves the owner's instance
unstartable.** Review208349 directed a corrected task "under supported fresh
identities/recovery inside the same owner-selected instance", preserving the
first run's immutable evidence. Carrying that out hit a closed chain of three
product rules, each individually sound.

### The chain, with the exact refusal each step produced

1. **A repeated bootstrap preserves what is there.** Composing only the new Job
   refused: *"job 'w202663-deterministic-verification' is already prepared here
   and this document does not name it; a Job that stops being named is not
   thereby unconfigured."* Correct, and exactly the preservation the review
   required. The composer now reads the destination's own emitted
   configuration and carries the prepared Job and its workers verbatim.
2. **One participant per worker, across the whole pool.** Six workers reusing
   three participants refused: *"a worker pool names one participant per
   worker; duplicate participant values are not distinct capacity."* Corrected
   by giving this run's three workers their own identities.
3. **A changed pool is a new generation.** Six workers where there were three
   refused at activation: *"activating this deployment's pool would answer
   generation 2 and the configuration names 1; a deployment resuming against a
   pool that has moved on refuses before it activates one rather than after."*
   Correct — W71877's pool generations are immutable.
4. **…but a live canonical target is not re-described.** Naming generation 2
   then refused: *"target 'w202663-verification-target' is already activated
   under another configuration; a live target's identity is not re-described."*

**Why 3 and 4 cannot both be satisfied, measured rather than reasoned.** The
target row stored in this instance's `integration.sqlite3` is:

```json
{"canonical_target_id": "w202663-verification-target",
 "description": "configured by stage-execution deployment cf92cbff… at pool generation 1",
 "schema": "baton.v12.integration-target/2"}
```

The description **embeds the pool generation**, and `queue.activate_target`
compares the stored digest against the digest of the document a start would
activate. So advancing the pool generation necessarily re-describes the target,
and re-describing a live target is denied. On an instance whose canonical target
has been activated, **a Job that brings its own workers cannot be added.**

### The consequence I caused, stated plainly

`/home/sl/baton-v12/instance-2026-09-19T02-05-20Z` now holds a configuration
naming two Jobs, six workers and `pool_generation: 2`, and **`just start`
refuses** at rule 4. Nothing was lost — both Jobs, both Works, every attempt,
the accepted checkpoint, the verdict and the first run's refusal evidence are
all intact, and no store was repaired by hand — but the instance will not start
until this is resolved. I caused that by adding a second Job, and I am not
leaving it unsaid.

Setting the configuration back to `pool_generation: 1` does not recover it:
rule 3 then refuses, because the durable pool really has six workers now.

### What this is, and what it is not

It is **not** a reason to weaken any of the four rules, and it is not an
argument for hand-editing a store. Each refusal is protecting something real:
prepared capacity, distinct identities, immutable generations, and a target
whose identity two configurations cannot both claim.

It IS the sharpest evidence yet for the first development task this Work was
told to record: **user-managed addition of workers to an existing pool,
independently of bootstrap and of individual Jobs.** That task exists because
bootstrap couples a worker to the Job it serves; D4 is what that coupling costs
the moment a second Job needs capacity on a live instance.

**Open, and it needs a decision I do not own.** The supported resolutions are
a fresh `state_root` — which owner ruling 208215 forbids ("no… destination
change") — or a product change to how a target's identity is described or how
pool generations are activated, which is the worker-add interface the same
ruling excludes from this prerequisite.

## Review208415 — D4 confirmed, narrower than worker-add UI

review-2026-09-19T02-39-01Z.md independently reproduces description-generation collision.
Stable target identity must not vary with capacity; correction need not implement
worker-add UI. Target activation precedes pool activation, so a failed start
does not itself establish durable generation2. Owner decision recommended for
bounded compatible correction AND supported corrected-runtime delivery under
208215 constraints. No deployed state changed by reviewer.

## Owner ruling — 2026-09-19T02:44:19Z (W202663 pass event 208460)

**Pinned before implementation, as required.** Quoted from the canonical pass
event:

> Authorize the bounded D4 correctness repair described in
> review-2026-09-19T02-39-01Z.md under
> baton:work/records/2026/09/finding-v12-initial-claude-worker-pool. Pin this
> ruling before implementation. Decouple stable integration-target identity
> from mutable pool generation. Preserve existing target documents, keys,
> queues, fences and history; reject genuine identity conflicts. Cover initial
> activation, replay, capacity changes, legacy descriptors and failed-start
> recovery with focused deterministic tests. Establish current deployed state
> through supported observations; do not assume failed startup committed the
> new pool. This repair is not the excluded worker-add interface. Complete and
> independently review the correction before asking the owner to deploy again.
> Owner will install a fresh timestamped instance under /home/sl/baton-v12/
> afterward; no agent replacement/reset of the current instance. Preserve its
> evidence. Return exact deployment commands using real input paths and the
> remaining installed-verification steps. No live models, Git mutation or
> unrelated redesign.

### Two corrections to D4 as I wrote it, both adopted

**D4's "both resolutions are outside this Work's authority" is superseded.**
Review208415 drew a distinction I missed: decoupling a stable target descriptor
from mutable capacity is *narrower* than the excluded worker-add interface. The
existing supported bootstrap path meets a correctness defect, and repairing it
preserves the target refusal invariant rather than weakening it. My equating of
every target/pool correction with the excluded interface was wrong.

**My durable-state claim is withdrawn as unestablished.** I wrote that the
instance "now holds … `pool_generation: 2`" durably and that reverting the
configuration "does not recover it". Review208415 traced the order:
`operations_from` activates targets at `stage_execution.py:5894` **before**
`scheduler.activate_pool` at 5943, so the target refusal precedes pool
activation on this path. The generation preflight can *predict* 2 from an
active generation 1 plus a changed configuration. A failed start therefore does
**not** establish that the durable pool holds six workers at generation 2. What
the instance actually holds must be established by supported observation before
any restoration is chosen, and no raw store may be altered.

### The patch boundary this authorizes

- new stable target descriptors are decoupled from pool generation;
- retained target documents, identities, fences and queues are preserved
  exactly, and a legacy generation-bearing descriptor keeps working;
- **merely removing the generation string and presenting a new document for an
  existing key is explicitly NOT the fix** — that re-describes the target and
  triggers the very same refusal;
- genuine incompatible target identity changes are still rejected;
- focused deterministic coverage for initial activation, exact replay, a
  capacity-generation change on the same target, a legacy descriptor, a genuine
  conflict, and failed-start side effects and recovery.

Out of scope by the same ruling: the worker-add interface, any database
rewrite, deleting first-run history, live providers, Git mutation, and
replacing or resetting the current instance — the owner will install a fresh
timestamped instance under `/home/sl/baton-v12/` after the correction has been
independently reviewed.

## Review208507 — bounded D4 method accepted; deployment package incomplete

review-2026-09-19T02-53-39Z.md records221 passing tests with existing finalizer warnings.
New seven cases prove method-level replay, not full startup/pool recovery or
populated queue/fence preservation. Complete focused composition proof and
runnable owner commands before owner deployment. Raw input state_root is
overridden by installer destination; isolated held refusal is not install defect.

## Review208585 — D4 accepted; package corrections before owner install

review-2026-09-19T03-04-44Z.md accepts nine passing D4 cases including composition
failure/retry. Installer currently rebuilds instead of binding recorded distro;
pin command reads old default instance; submission is help only.106-input
snapshot omits actual build lock/spec: completeness claim superseded, preserve
as partial. Correct package only; no new D4 work or agent installation.

## 2026-09-19T03:4xZ — D5: an import-time default poisoned the fresh Authority's canonical target

The owner installed the reviewed artifact at
`/home/sl/baton-v12/instance-2026-09-19T03-28-13Z` (pass 208775) and the
installed verification ran. Implementation and review completed through the
real producer image on the installed runtime; integration EXECUTED the real
integration image and REFUSED: `target-drift` — "the target is not at the
revision this candidate was reviewed against"
(`deployment-state/integration/integration/result/result.json`).

### The chain, measured

1. `compose-verification-208217.py`'s `declared_base` carried
   `target=DEST / "repo/target.git"` **in its signature**, so the default was
   bound to the HISTORICAL instance's path at module load. `--instance`
   redirected every other fact; the line's declared base still read the OLD
   instance's target: `e486652c…`. **The same import-time-default defect
   class review208585 [R2] named in the pin check.**
2. The new instance's target repository holds `main` at `93da9d62…` (the
   checkout's HEAD at install time). The composed Job declared `e486652c…`.
3. The first capacity bootstrap **established the Authority's canonical
   target policy from that poisoned base** (`bootstrap._canonical_target`:
   "established from line_declared_base e486652c…").
4. Publication gates passed (declared base equals the poisoned policy);
   physical import correctly refused (the target is at `93da9d62…`, one
   commit AHEAD of the candidate's base; a fast-forward to the candidate is
   impossible without rewind).

### Why this instance cannot reach a successful terminal lifecycle

- The canonical target policy is ONE value, set once when unestablished, and
  advanced only by an ACCEPTED integration (`bootstrap.py` records both).
- A corrected Job declaring the real base `93da9d62…` cannot coexist with the
  preserved Job (`bootstrap.held`: "this deployment's Jobs declare 2
  different bases" — measured, `compose-208777b.log`), and alone it could
  never publish against the `e486652c…` policy.
- A Job declaring `e486652c…` publishes but can never import.
- Moving the target repository or the policy by hand is a version-control
  mutation / hand-repaired store, both excluded.

**The composer is corrected** (`declared_base` resolves its default at call
time; verified read-only: the module default still answers the historical
`e486652c…`, after `select_instance` it answers this instance's `93da9d62…` —
`declared-base-check-208777.log`). The correction cannot be proven end-to-end
on THIS instance; a fresh owner installation with the corrected composer is
the same resolution shape as D3. The instance, its Jobs, lines, refusal
result and stores are preserved as evidence.

## 2026-09-19T03:4xZ — D6: a refused integration result is published, durable, and never collected

After the integration runtime published the `refused` result and exited 0,
the stage holds `starting` with `execution_runtime: quiescent`. Serving ticks
(5s interval, observed across minutes and across a stop/start) report the
attempt `quiescent` with `acts: []`, no deferral, no retry, no receipt beyond
`admit`/`claim`, and the Job never reaches its `report-and-hold` terminal.
The refusal reason exists ONLY in the result document at the destination —
nothing surfaces it through the status projection.

What is measured: the result is readable and well-formed;
`integration/runtime.py`'s observation function answers `answered` for
exactly this shape; the serving loop took no act on it before or after the
offer expiry (03:35:09Z). What is NOT established: which component owes the
collection act and whether the expired offer is the cause — that is the next
bounded product question, and it is the same silent-stall family (W197661's
"deferred forever") this Work exists to close. Evidence: manager.log tick
records and the retained status projection `run-status-208777.json`.

### SUPERSEDED (claim208916): the refusal WAS collected; the designed hold path was measured

Review208890 required the observation-layer distinction before this claim
could stand, and the measurement disproves it. Read through the public
queue readers over the integration store opened READ-ONLY
(`d6-settlement-208916.log`):

- the ENTRY `integration-driver.entry:fe386adf…` is settled **`refused`** at
  `2026-09-19T03:33:20.169Z` — 5 seconds after the runtime published its
  result — with the settlement carrying the exact reason
  (`target-drift`, "the target is not at the revision this candidate was
  reviewed against");
- the LEASE `integration-driver.lease:f7601b8d…` is **`released`** at the
  same instant with ending outcome `entry-refused`.

So the driver read the result, settled the entry and released the lease
within one tick. `Integration.account` maps a refused entry to a `held`
account, and `projection._integrating` deliberately owes NO automatic act
for held — the non-terminal Job under `report-and-hold` is the DESIGNED
hold path, not a stall. Offer expiry played no role (settlement preceded it
by ~109 seconds).

**The claim "never collected" is withdrawn.** What remains, narrower and
real: a VISIBILITY limitation. The observation-enabled status reports the
stage as bare `exceptional` with `exchange: null`
(`status-observe` run this claim), the plain status reports generic
`starting`, and NEITHER surfaces the settlement reason that the entry and
the result document both carry. An operator at the supported reader cannot
see WHY a held integration holds. That is a bounded projection-surface
question, not a missing collection act — any correction must be pinned
before implementation (review208890), and no automatic retry or
policy-repair is in its scope.

Also measured: the reviewer's observation-enabled status failure did not
reproduce for the authorized handler. `tools.stage_execution:observing_factory`
REFUSES by name when `BATON_V12_STAGE_EXECUTION_CONFIG` is unset (measured
first), and succeeds with the four deployment exports the bootstrap prints;
the JobStore itself opened normally throughout.

## 2026-09-19T04:1xZ — the deterministic lifecycle completed; three bounded observations (claim208996)

On the owner's fresh installation (`instance-2026-09-19T04-02-31Z`) the whole
deterministic heterogeneous lifecycle COMPLETED on the installed runtime:
correct declared base (`93da9d62…`, D5's correction proven end-to-end),
canonical target established from it, pin 1→9 checked, implementation
(emitting image, correlated through committed records) and review completed,
integration executed the real integration image, imported the candidate path,
ran the accepted verification (exit 0), settled the entry **`integrated`**,
released the lease, advanced the canonical target policy to the candidate
(`617f4621…`), and left all three stages `completed` under `report-and-hold`
with runtimes destroyed/retained as distinct projected facts and every log
and artifact retained. Capture: nonempty streams with exact deterministic
content, same attempt re-read after cleanup and supervisor stop
(`capture-assert-{1,2,3}*-208996.log`, `status-observe-208996.json`).

Three MEASURED OBSERVATIONS, recorded for pinning before any implementation
— none is a defect claim:

1. **Per-phase capture retention — SUPERSEDED by review209080's source
   correction.** My inference that consider-phase prose was LOST to a later
   launch is withdrawn: `fixture-context/worker/baton_worker.py` carries
   `OPERATIONS = (describe, work)` — `consider` is not an operation this
   worker serves, and `handle` refuses it with an entitlement refusal BEFORE
   any `agent.consider` could run. The missing markers were an UNREACHABLE
   expectation in `EmittingAgent.consider`, not a measured overwrite; the
   capture writer opens with `O_APPEND` and no truncation was demonstrated.
   `capture-assert-1-208996.log` is preserved as the record of a mistaken
   expectation, not of a logging defect, and no logging repair is to be made
   from those absent markers.
2. **No job-level terminal field.** The status projection's job object
   carries `terminal_policy` but NO terminal state; "terminal
   report-and-hold" is established from stage states plus retained evidence.
   Related to the pinned reason-visibility question from D6's supersession.
3. **Policy/repository divergence after import.** The import is PATH-level
   into the target room and the Authority's canonical target policy advanced
   to the candidate COMMIT (`617f4621…`), while the target repository's
   `main` remains `93da9d62…` and no such commit object exists in it. A
   SECOND Job composed later would read `declared_base` from the repository
   while publication compares against the policy — the consecutive-Job
   continuity question the real Claude pool work must answer first. Also
   minor: both attempts' log rooms sit under the implementation worker's
   launch home.

## 2026-09-19T04:2xZ — D7: a settled allocation from a retired pool generation kills the manager at restart

Found by running review209080's required reproduction: the second
deterministic Job (`…-verification-3`, fresh identities, base `93da9d62…` —
same base as the preserved Job, so preflight passes) composed, applied, and
pin-gated (the gate caught and corrected a per-Job generation-bump
prediction on the way: 9→24 measured against a per-Work model; the composer
now predicts per Job prepared and the re-apply checked equal at 38). Then
`just start` KILLED the manager with a raw unhandled
`KeyError: (1, 'w202663-deterministic-verification-2-implementation')`
(`start-209102.log`, full traceback in the instance's `state/manager.log`).

### The chain, in source and in the store

- The pool advanced to generation 2 (six workers) when job-3's capacity was
  applied; the completed job-2 stages hold durable allocations at
  generation 1, all `released` (`cleanup-retained` ×2,
  `integration-completed`) — read from the retained observed status.
- `scheduler._required_workers` attaches prior-generation workers ONLY for
  allocations in `('reserved', 'recovery-required')`; released ones are
  deliberately not required, so attachment held exactly the generation-2
  pairs and SUCCEEDED (`serving initialization complete` precedes the
  crash).
- `scheduler._reader` (line ~731) then answers `observe`/`refresh_runtime`
  for EVERY live stage — including the completed, retained job-2 stages —
  by `self.workers[(allocation["generation"], allocation["worker_id"])]`
  with the allocation read in ANY state. A `released` allocation from the
  retired generation is returned by `allocation_of`, its key is absent from
  the attached map, and the lookup raises a raw `KeyError` that unwinds the
  whole serve loop.

### What this is

A PRODUCT continuity defect, distinguished from the fixture questions: the
attachment contract ("exactly the active generation and live prior
generations") and the read path disagree about settled history. Any
instance whose pool EVER advances — which is precisely this Work's recorded
first development task, user-managed addition of workers to an existing
pool — cannot restart its manager once a prior generation's work has been
cleaned up. No policy edit, rewind or reset is involved in reaching it.

### The pinned correction, exact scope

`_reader` alone (both its callers, `observe` and `refresh_runtime`, are
read-only): when the allocation's `(generation, worker_id)` is not in the
attached map — reachable past attachment only for allocations OUTSIDE
`('reserved', 'recovery-required')` — answer through `_any()`, the same
store-global read the no-allocation branch already uses ("every attached
store answers the same … document"); if a `reserved`/`recovery-required`
allocation ever reaches an unattached key, refuse with prose naming the
attachment contract rather than raising `KeyError`. No acting path
(`launch`/`dispatch`/`conclude`/`claim` via `_worker`) is touched: those
require a live allocation, which attachment guarantees is present. Focused
tests with a reversal probe accompany the change.

### Review209188 [R1] completed: the real observation contract, proven over composed history

Two of that pin's claims were corrected on review209188's reading and the
routing was refined within the pinned scope:

- **`refresh_runtime` is NOT a pure read** — it asks the engine through the
  selected callback and RECORDS what it observed; it is non-launching, which
  is the property the correction relies on. Wording corrected in the
  `_reader` docstring and here.
- **`_any()` was not proven interchangeable** — observation adopts each
  worker's own launch home, role and manifest context. The routing now
  answers settled history through **the SAME worker id in its newest
  attached generation** whenever the pool still names it, and only a worker
  removed from every attached generation falls back to `_any()`'s
  store-backed runtime answer.

PROOF, at the composition boundary with the real observers
(`TheRestartOverAnAdvancedPoolPreservesSettledHistory`): one real composed
implementation attempt carried to `completed` (real stores, real line, real
workload, accepted ending), its allocation RELEASED by cleanup; the pool
genuinely advanced (replacement reviewer, generation 2); the composition
restarted over the same durable stores; and the first sweep — the tick that
raised the KeyError — observes the exact history: same completed state,
same attempt, byte-identical allocation row and runtime observation,
byte-identical retained publication, and every engine start after the
restart names other stages, never the settled attempt. MEASURED ON THE WAY:
with a live (reserved) prior-generation allocation, the generation-2
composition refuses at ATTACHMENT by name — the loud correct boundary for
live prior work, which `operations_from` does not currently attach across
generations (a separate bounded fact, recorded, not repaired here). The
unattached-LIVE `_reader` branch is defence in depth: `require_recovery`
refuses a released allocation ("is not quarantined again", measured), so no
public act reaches it; the branch is covered at the unit level with an
injected answer, and same-worker routing is asserted directly (the newest
generation's same-named worker answers; every other worker observes
nothing).

### Installed consecutive-Job and restart outcomes (claim209386, experimental deployment)

On the owner's experimental instance (`instance-2026-09-19T05-02-46Z`,
runtime `d5d1e9fb…`, authority `9db3a29d…`), recorded per owner209384 —
observed, not repaired:

- **D7 field-proven.** Job-2 ran to all-stages-completed with every
  allocation released; the pool advanced to generation 2 (job-3's six
  workers); `just start` COMPOSED AND SERVED over the retained settled
  history — the exact sequence that killed the `7040dd00…` runtime with a
  raw KeyError (`start-209386-advanced.log`).
- **History preserved, no redispatch.** After the restart job-2's stages
  project completed, allocations unchanged, and ZERO new containers
  appeared; capture assertions pass again on this instance's emitting
  attempt (`history-after-restart-209386.log`, `capture-assert-209386.log`).
- **Prior-generation attachment**: succeeded, because every prior
  allocation was `released`; the live-prior case remains the
  composition-measured attachment refusal, unchanged.
- **THE RECORDED CONSECUTIVE-JOB BOUNDARY LANDS BEFORE PUBLICATION**: job-3's
  implementation claim REFUSES — "the authority refused this claim: route
  'integration' does not resolve to 'baton.fixture-coder-3'"
  (refused/precondition, retained as an outstanding deferral each tick;
  `job3-boundary-209386.log`, `run-status-209386.json`: implementation
  `offered`, review/integration `blocked`).

  **My route-rebinding causal claim is SUPERSEDED by review209459's source
  reading.** `authority.core.add_route_handler` ADDS membership (ON
  CONFLICT DO NOTHING) and replaces nothing; `bootstrap._compose` creates a
  MISSING Work on the implementation route and explicitly leaves an
  existing Work alone. What actually happened: `select_job` reused the ONE
  Work, job-2's COMPLETED lifecycle had moved that Work to the
  `integration` route, and job-3's fresh implementation stage attached to
  it there — so the coder's claim correctly met a Work routed at
  integration. This is the EXPERIMENT'S reused-Work lifecycle, not a
  product routing defect and not overwritten handler membership. The
  original submission and its refusal are preserved as evidence. The
  bounded consequence stands: the publication-base gate was NOT reached
  installed; a fresh authority-qualified Work per independent Job is the
  ordinary composition, made explicit in the composer.

### Job-3's reserved allocation, accounted through supported reads only (claim209474) — the exact decision needed

Review209459 required job-3's RESERVED allocation accounted before any
pool-generation change, through supported transitions only. Measured:

- the stack was restarted at the UNCHANGED generation and ordinary ticks
  ran; the allocation stayed `reserved`, the stage `offered`, the claim
  deferral outstanding on every tick;
- the offer row (read-only): state **`accepted`**, issued by the PRIOR
  incarnation, `expires_at` long past; episode 1 unended;
- by `worker_manager.offers.recover_on_restart`'s deliberate asymmetry an
  ACCEPTED offer is RECOVERABLE, never abandoned — its authorization and
  fixed claim operation are durable — and the claim retries forever against
  the Work still routed at `integration`, refused each time;
- no deployment-surface transition settles it: `job_manager` exposes
  submit/status/serve only, and no cancellation/settlement verb exists for
  a permanently-refused accepted offer.

**THE DECISION REQUIRED** (episode retained, nothing hand-released): either
(a) a supported settlement path for an accepted offer whose claim refuses
on a durable precondition (a product decision — today's design retains it
for recovery, correctly for transient refusals, indefinitely for this
permanent one); or (b) accept that THIS experimental instance retains the
stalled episode — which, combined with the measured
no-cross-generation-attachment fact, blocks any further pool-generation
change here — and run the fresh-Work consecutive-Job experiment on the
NEXT instance, where the corrected composer (`select_job` now selects
Job + participants + WORK together, 19/19 isolation checks) prevents the
reused-Work refusal from arising at all. No third option was found in
source.

### The two-Job distinct-Work experiment: the publication-base boundary MEASURED INSTALLED (claim212143)

Owner212133 selected review209517's fresh-deployment alternative and
installed `instance-2026-09-19T12-39-13Z` (runtime `d5d1e9fb…`, authority
`117afd1c…`); the stalled instance is preserved. Two deterministic Jobs ran
with DISTINCT EXPLICIT WORKS through the corrected composer:

- **Job A** (`…-verification-2`, Work `117afd1c-W1`): full lifecycle to all
  three stages completed, entry integrated, every allocation released — in
  under a minute; the canonical target policy advanced to its candidate
  `784081a4…`.
- **Job B** (`…-verification-3`, Work `117afd1c-W3` — `select_job`'s fresh
  Work in its first field use): composed, applied (pool generation 2, pin
  gate equal at 24), the stack RESTARTED over the settled history (the D7
  path again, serving), and the submission's implementation claim
  **SUCCEEDED** — the reused-Work refusal is gone, the composer correction
  field-proven. The worker's turn RAN.
- **THE INSTALLED PUBLICATION-BASE MEASUREMENT**, exactly the pinned
  boundary: the ending's publication refuses each tick with "the worker
  built on '93da9d628360590e30d7dd899781c9e5db4cc2b1' and the Authority
  target is '784081a462ef05b9381527974ac775b30cf825af'; a proposal is
  offered against the revision it was built from"
  (`job3-publication-boundary-212143.json`, `run-status-212143.json`:
  implementation `answering`, review/integration `blocked`, allocation
  `reserved`). The refusal retries on a DURABLE precondition — the same
  permanent-retention shape as the stalled claim, now at publication.

**The continuity ruling request now carries installed evidence.** A second
independent Job on one instance passes admission and claim with its own
Work, and is stopped exactly and only by the policy/repository divergence
a path-level import leaves behind: the policy advances to the candidate
commit, the repository main and the nominated source never receive it, so
the next Job can neither declare the advanced base (no commit object to
materialize a line from) nor publish from the old one. The three candidate
resolutions stand as pinned earlier — (a) the nominated source receives
accepted candidates, (b) the git profile's import advances the repository,
(c) declared bases read the policy with line materialization from retained
checkpoints — and the choice among them is a design ruling this Work
routes rather than takes.

### SUPERSEDED (claim212204): the ruling already exists, implemented and locally proven; the delta was CONFIGURATION

Review212187 found the existing approved decision:
`AMENDMENT-direct-target-finalization-v1.md` (owner137905, W133129) — the
coordinator delivers the accepted candidate commit from proved producer
custody and CAS-advances the configured target reference BEFORE Authority
completion, exactly resolution (b) with fenced semantics. It is
IMPLEMENTED: `execution.finalize_direct_target`, called by
`driver._authority_completed` when the deployment supplies `finalize`,
which `Integration._run` builds ONLY when `deployment.reconciles()` —
requiring `integration_target`, `integration_workspace` AND
`integration_observer`. **This composition set the first two and never the
observer, so every measured divergence (D5's poisoned successor instance,
the claim212143 publication refusal) ran with the approved finalizer
silently disabled.** The three-option ruling request is withdrawn; no
design choice was outstanding.

The observer is a PARTICIPANT — the identity that runs a reconciled
result's causal harness, required by W133117 to be distinct from the three
judges and the integrator; `bootstrap` passes the member through and
`principals_for` does not need it (it acts only on reconciled results,
none of which the deterministic direct path produces). LOCALLY PROVEN on
the current tree: the accepted suite's
`test_the_direct_integration_finalizes_the_dedicated_target` and
`test_BOTH_JOBS_REACH_TERMINAL_ON_ONE_TARGET` both pass — two Jobs, one
target, terminal, with the reference advancing. The composer now
configures `integration_observer: baton.fixture-observer`
(deployment-scoped, distinct from all other identities), and the
observer-configured composition validates `complete: true, refused: []`
through all six production validators
(`compose-212204-observer.log`; the regenerated `pool-*.json` are its
record, NOT applied anywhere). The current experimental instance is left
untouched: its job-B allocation is reserved at the publication deferral,
a pool change is blocked there by design, and the observer-configured
consecutive-Job run belongs to the next owner-selected experiment, where
the second Job should REBASE onto the advanced reference and reach
terminal — the locally-proven behavior, measured installed.

### The observer-configured experiment: the finalizer WORKS INSTALLED; the next boundary is the bootstrap document rule (claim212295)

On owner212293's fresh instance (`instance-2026-09-19T13-01-28Z`, runtime
`d5d1e9fb…`, authority `c1b38e2e…`), the observer-configured two-Job
experiment ran with B composed AFTER A completed:

- **Job A** (W1, `integration_observer` configured, `reconciles()` true):
  full lifecycle to all-stages-completed and released. **THE AGREEMENT
  MEASUREMENT: the Authority canonical-target policy and
  `target.git refs/heads/main` BOTH answer `9a478400…`** — the approved
  direct-target finalization ran installed and advanced the reference with
  the policy (`ref-agreement-212295.log`). The divergence that stalled
  every prior consecutive-Job attempt is resolved by configuration alone.
- **Job B** (fresh W3, composed after A): `declared_base()` correctly read
  the ADVANCED reference (`9a478400…`) — and the composition REFUSED at
  `bootstrap.held`, exactly the reviewer's named caveat: "an Authority
  holds ONE canonical target and this deployment's Jobs declare 2
  different bases (93da9d62…, 9a478400…)". The preserved COMPLETED Job's
  binding carries its historical base, the new Job carries the advanced
  one, and the document-level single-base preflight cannot express both —
  while a preserved Job cannot be dropped either ("a Job that stops being
  named is not thereby unconfigured"). Nothing was applied; the refusal is
  the recorded outcome (`compose-212295b.log`, the regenerated
  `POOL-COMPOSITION` record).
- **Restart** over A's settled history at the unchanged generation:
  history preserved, ZERO new containers, stop clean.

**THE NEXT BOUNDED QUESTION, for pinning before any change**: the
`bootstrap.held` single-base rule exists so `_canonical_target` can
establish ONE first value; on a repeat over an established target with a
COMPLETED preserved binding, it conflates historical bases with new ones.
Whether the rule should exempt completed/published bindings (the runtime
already stores `line_declared_base` PER binding, and publication compares
each worker's declared base against the current policy) is a bounded
product-preflight decision — routed, not taken here.

### PINNED (claim212385): owner212383 selects review212328's bounded amendment — exact scope before implementation

Owner212383 selects the four-point amendment in
`review-2026-09-19T13-09-11Z.md`. Pinned here before any code:

**(1)+(2) Incremental admission** — `v12/python/tools/bootstrap.py`:
- `held` stays PURE and keeps every per-binding form check; the
  distinct-base COUNT rule moves out of it.
- A new store-aware preflight runs in `prepare` immediately after
  `conflicts` — still before ANY durable effect, preserving the module's
  no-effects-on-refusal promise:
  - retained bindings are those in this root's PERSISTED record
    (`record_of`'s file, the same evidence `conflicts` compares —
    validated persisted evidence, never an input assertion), and
    `conflicts` continues to refuse their mutation or omission unchanged;
  - a FRESH root (no persisted record) requires exactly ONE distinct base
    across all bindings — the first-establishment rule, byte-for-byte the
    current protection;
  - an ESTABLISHED root admits NEW bindings only when they share ONE base
    EQUAL to the Authority's CURRENT canonical-target policy, read
    read-only before composition (stale new base, unestablished policy
    with divergent bases, and any retained-binding drift refuse by name);
  - live-allocation guards, `dropped_selections`, and every existing
    refusal stay untouched.
- Affected tests: `tests/tools/test_bootstrap.py` — the fresh multi-base
  refusal keeps its protection (site moves); new established-history
  cases: new-binding-at-current-policy admitted, stale new base refused,
  retained mutation still refused.

**(3) Source materialization — NO existing supported path; the exact
extension pinned before coding.** `checkpoint_profiles.GitCheckpointProfile
.materialize(source, repository, declared_base)` clones from the nominated
source ONLY and refuses a base the source does not hold; the advanced
commit exists only in the dedicated target (`9a478400…` measured present
in `target.git`, absent from `repo/workspace`). The pinned extension: an
explicit optional `supplement` operand on `materialize` — the deployment's
OWN configured `integration_target` path, threaded from
`stage_execution`'s composition through `create_line` — used ONLY when the
declared base is absent after the source clone, fetching EXACTLY the
declared-base commit from the supplement and refusing anything else
(custody: the same repository the fenced finalizer wrote; no manual
copying, no old-line rewriting, no operator repair; old source/checkpoint
attribution unchanged). Affected paths: `checkpoint_profiles.py`,
`worker_manager/review_cycles.py` (`create_line` threading),
`tools/stage_execution.py` (composition supplies the supplement), plus
their focused tests.

**(4) The focused real-topology proof** (A completes → B created after
with distinct Work and advanced base → old bindings remain → B
materializes, publishes, reaches terminal on ONE instance, restart
attribution accounted) follows once (1)–(3) land, on the composed harness
first and then the owner's next experimental deployment.

### PINNED FINAL (claim212502): the supplement's retry/custody/provenance operands

Review212486 required these pinned before code:

- **Operand placement**: `GitCheckpointProfile(runner, *, supplement=None)`
  — the supplement is PROFILE configuration (how a declared base is
  obtained), never a `create_line` operand. Line identity (authority,
  work) and the committed creation signature are UNCHANGED, so there is
  NO changed-operand replay question: an exact retry replays the committed
  creation, and recovery re-runs `materialize`, which is already
  resumable by design.
- **Custody**: the composition supplies `supplement` = the deployment's
  own configured `integration_target` — the repository the fenced
  finalizer writes — threaded at profile construction
  (`stage_execution._profile_of`). No input document names a separate
  locator and no other repository is accepted.
- **Behavior**: the clone from the nominated source is unchanged; the
  detach runs; ONLY on a detach refusal with a supplement configured, the
  profile fetches EXACTLY the declared-base commit
  (`fetch --no-tags <supplement> <base>`) and detaches again; a base
  still absent refuses naming both repositories. When the nominated
  source holds the base, the supplement is never touched.
- **Provenance, truthful**: the line's recorded `source_path` remains the
  nominated source — the tree it was actually cloned from;
  `materialize`'s closed return `{profile, base, head}` is DELIBERATELY
  unchanged (`create_line` validates that exact set); the supplement act
  is visible in the profile's own command stream and proven by focused
  tests (base-in-source never touches the supplement; base-only-in-
  supplement succeeds; base-nowhere refuses naming both; no supplement
  configured keeps today's refusal byte for byte).

### Review212545 [R2] corrections (claim212569): proved absence, preserved causes, the recovery invariant, the provenance claim qualified

- **Absence is PROVED before any supplemental delivery.** The reviewer's
  probe measured the earlier catch-all masking a non-absence cause (base
  in BOTH repositories, detach blocked by a private `index.lock`, false
  "in neither"). `materialize` now asks `_present` (`rev-parse --verify
  --quiet <base>^{commit}`, runner-shape-enforced, nonzero-as-answer)
  first: a present object re-raises the checkout's OWN refusal untouched
  and never touches the supplement; a failed delivery raises a named
  refusal carrying the fetch's own cause VERBATIM (an unreachable
  supplement and one lacking the commit are different operator facts); a
  detach refusing after a proved delivery speaks as itself. Regressions:
  the probe scenario (lock, both-repos, zero fetches, checkout-named
  refusal) and the unreachable-supplement delivery failure.
- **The recovery invariant, justified WITHOUT any schema change.** An
  unfinished line resumed under a CHANGED, REPLACED or MISSING supplement
  cannot diverge, because the supplement supplies only OBJECTS for one
  content-addressed commit: any supplement that delivers the declared
  base delivers byte-identical objects (git object identity is the
  content hash), and one that cannot deliver it refuses. Objects already
  fetched by an interrupted attempt persist in the clone, so a recovery
  with NO supplement completes whenever the base is already present
  (`_present` short-circuits) and refuses only when it is genuinely
  absent. The line's identity and committed creation signature never
  include the supplement, so replay/recovery semantics are exactly the
  pre-existing ones.
- **The provenance claim is QUALIFIED.** Production `_git_run` does not
  persist the command stream; "visible in the profile's command stream"
  is a TEST seam (the suite's recording runner), not a durable record.
  The durable provenance is: the line's committed creation record
  (unchanged operands), the clone's own git state (the fetched objects
  and their content-addressed identity), and the deterministic profile
  behavior proven by the focused tests. No stronger claim is made.
### The composed fresh-successor proof: three boundaries crossed, one pinned open (claim217230)

`ANewJobCreatedAfterAFollowsTheAdvancedTarget` in
`tests/tools/test_stage_execution.py` drives the owner-selected topology:
Job A alone on a SEPARATE dedicated target clone; A completes and the
finalizer advances THAT repository while the nominated source provably
lacks the candidate (`cat-file` nonzero, asserted); the successor Job B is
created only then, on its own Work, declaring the advanced base. PROVEN
INSIDE IT, in order:

1. **The successor pins the CURRENT policy generation** — measured first
   as a named deferral ("the Authority has moved to policy generation 12
   from the configured 11") because A's own receipts move the Authority;
   the successor composition reads and pins the current generation exactly
   as an installed re-bootstrap does.
2. **THE SUPPLEMENT MATERIALIZATION WORKS COMPOSED**: B's line
   materializes AT THE ADVANCED BASE from a source that does not hold it,
   through the profile supplement — the extension's whole purpose, now
   proven beyond the profile boundary.
3. B's implementation and review COMPLETE on the same stores with A's
   history retained.

**THE PINNED OPEN BOUNDARY**: B's integration launch defers every tick at
`integration.runtime.prior_runtime_witness` — "the coordinator recorded a
grant to attempt <B's own> and this manager holds no such attempt" — the
conservative coordinator/manager-contradiction refusal. The test is
retained under `@unittest.expectedFailure` with the blocker pinned in its
own text, so the whole traversal is preserved and the suite stays green.
The next probe is exact: instrument `admit_accepted`'s prior-grant lookup
on the shared target to establish whose attempt the coordinator consults
there and why the manager holds no runtime row for it — fixture-sequencing
versus product rule deliberately NOT prejudged.

### D8, DIAGNOSED (claim217345): the integration delivery namespace is SINGLE-SLOT per deployment

Review217322's source finding redirected the probe (the witness is called
for the CURRENT attempt via `execution._unstarted` /
`IntegrationRuntimePort.observed`), and the diagnosis is now complete and
ASSERTED in the test itself — the `expectedFailure` masking is removed per
the same review:

- `IntegrationDelivery.root = <integration_root>/<DELIVERY_DIRECTORY>`
  joins a CONSTANT; the attempt id is carried as metadata only. The
  delivery namespace is one slot per deployment — exactly the
  `deployment-state/integration/integration/{assignment,result}` layout
  every installed instance showed.
- Job B's `_published` therefore ADOPTS Job A's retained delivery
  (report-and-hold retains it), whose published assignment still names
  A'S integration attempt; `Integration._run` sees a non-None assignment
  and SKIPS `port.prepare`, so no manager attempt row is ever recorded
  for B; `prior_runtime_witness` then refuses B's CURRENT attempt's
  coordinator/manager contradiction on every tick.
- ASSERTED on the public readers in
  `ANewJobCreatedAfterAFollowsTheAdvancedTarget`: the single-slot
  delivery is adopted for ANY attempt id; its published assignment equals
  A's integration attempt and not B's; `attempt_runtime_of` is None for
  B and present for A; the launch's deferred outcome carries the exact
  witness message. A-history/no-redispatch assertions run BEFORE the
  boundary. The suite is at its recorded baseline with NO expected
  failure.
- **Consequence**: under report-and-hold retention, at most ONE direct
  container integration per deployment lifetime; the reconciled path
  never takes a second delivery (why `BOTH_JOBS` passes), and no
  weakening of the missing-runtime refusal is proposed.
- **The remedy is ROUTED, not taken**: (a) per-attempt delivery roots
  (namespace change at `IntegrationDelivery`), or (b) a named
  refusal/authorized disposition when `_published` adopts a delivery
  whose assignment names a FOREIGN attempt — either alters an owned
  contract beyond this Work's authority.

### D8 PINNED (owner217455, claim217457): exact paths and legacy compatibility, before implementation

Owner217455 selects review217381's per-attempt collision-safe HOST
delivery namespaces. Pinned exactly:

- **New host layout**:
  `IntegrationDelivery.root = <integration_root>/integration/<attempt_id>`
  with `assignment/` and `result/` beneath it — one namespace per attempt,
  collision-safe by the attempt id's own identity shape
  (`boundaries.identity`; never "assignment"/"result").
  `_delivery_root`'s inverse becomes two `dirname`s. CONTAINER MOUNT
  TARGETS ARE UNCHANGED (`/run/baton/integration/{assignment,result}` are
  fixed); only the host side moves. Mode establishment and
  descriptor-relative adoption proving are unchanged at the new leaf; the
  intermediate `<root>/integration` directory carries the same trust the
  root itself always has.
- **Creation/publication/observation/launch/results/recovery** all flow
  through the delivery object's properties and the `(root, attempt_id)`
  operand pair every caller already passes
  (`execution.integrate_next`/`settle_observed`, `stage_execution
  ._published`, `oci_delivery`'s three adoptions, `recovery`) — one
  derivation change covers the set; predecessor quiescence, target
  fencing, identity-bound assignment/result validation untouched.
- **Legacy compatibility, identity-proved, no silent disposition**: a
  LEGACY single-slot delivery (`<root>/integration/assignment` exists) is
  adopted for a requested attempt ONLY when its PUBLISHED assignment
  names exactly that attempt (an in-flight legacy integration resumes
  across the upgrade); a legacy slot whose assignment names a FOREIGN
  attempt is retained evidence — adoption answers None and the new
  attempt materializes its own per-attempt namespace beside it, touching
  nothing; a legacy slot with NO published assignment is unaccountable
  interrupted state and REFUSES BY NAME. Nothing migrates, overwrites or
  deletes legacy bytes.
- **The selected outcome**: the composed proof's boundary tail flips —
  fresh B completes DIRECTLY on the same deployment while A's retained
  delivery, history and allocations stay untouched, with no redispatch.
  Focused runtime-level cases cover distinct-attempt separation, side-by-
  side materialization, per-attempt adoption, legacy identity-proved
  adoption, foreign-legacy None, and unpublished-legacy refusal.

- **Review212593: the presence classification completed.** `_present`
  treated any nonzero status as absence — git's fatal 128
  (repository/query failure) included — permitting a fetch over an
  unanswerable clone and a false absence assertion; and it validated
  only the status field, reading past `stdout=None`/`stderr=[]`. Now:
  0 is present, 1 is the `--verify --quiet` contract's SPECIFIC absence,
  and every other status raises AS a query failure (detail preserved)
  BEFORE any delivery; every runner field is validated exactly as `_run`
  validates them. The residual post-fetch message no longer claims the
  supplement lacks the object — a completed delivery with a still-absent
  base claims only what the clone answers. Regressions: a corrupted
  clone HEAD (fatal 128 → query-failure refusal, zero fetches) and a
  lying runner (`stdout=None` → closed-contract refusal, zero fetches).

Review209188 required the boundary from focused deterministic composition
rather than another installation. The gate is
`integration/driver.publish_candidate`: "the worker built on X and the
Authority target is Y; a proposal is offered against the revision it was
built from" (refused/precondition), with existing focused deterministic
coverage asserting exactly that refusal
(`tests/integration/test_driver.py:1221`). Applied to the selected
instance's state: job-3's producer declares `93da9d62…` (the repository's
main) while the policy holds `617f4621…` — publication will refuse with
that named precondition. THE CONTINUITY QUESTION THAT REMAINS FOR DECISION:
a next Job can only publish if its declared base equals the ADVANCED
policy, and its line can only materialize if the nominated source carries
the candidate COMMIT — which a path-level import does not deliver. Whether
the resolution is (a) the nominated source receiving accepted candidates,
(b) the git profile's import advancing the repository, or (c) declared
bases reading the policy with line materialization from retained
checkpoints, exceeds this Work's authority and is routed for a ruling
rather than implemented.

## Review208712 — deployment package accepted for owner installation

review-2026-09-19T03-22-03Z.md accepts the bounded R1-R3 corrections. Executable and81-file bundle identity confirmed;9 fake-instance pin checks pass. Historical snapshot completeness remains unavailable and explicitly withdrawn. Owner208460 installation is next; installed behavior and whole-Work acceptance remain open. See REVIEW-EVIDENCE-208712.json for exact reviewed file hashes.

## Review208890 — D5 accepted narrowly; D6 collection claim unproved

review-2026-09-19T03-50-04Z.md records two isolated selected-base checks and actual target-drift result. D6 never-collected assertion is not established: Integration.account maps refused entries to held and the projection deliberately owes no automatic act for held. Supported observation/settlement correlation is next. Reviewer status attempt failed opening JobStore; no direct-store workaround used. No fresh installation or policy repair authorized by review.

## Review208960 — preparations accepted for owner installation

review-2026-09-19T03-59-59Z.md accepts the D6 supersession, emitting fixture preparation and16 passing isolation checks. Capture assertion behavior independently checked against synthetic positive/negative content; installed capture/cleanup remains unproved and must correlate the exact attempt. Prior reviewer status failure had the configuration environment set; unset-environment refusal is not its explanation.

## Review209080 — installed success accepted; per-phase loss explanation superseded

review-2026-09-19T04-18-22Z.md accepts bounded completed-stage and retained work-stream evidence. The per-phase-loss explanation above is superseded: the fixture worker permits describe/work and rejects consider before calling the emitting agent. Missing consider markers were an unreachable test expectation, not proof of overwrite. Work-only assertions are appropriate; general log-preservation scope remains. Consecutive-Job continuity, source prerequisites and final Claude pool remain actionable.

## Review209188 — D7 fallback not yet accepted for deployment

review-2026-09-19T04-33-56Z.md confirms61 scheduling tests pass and the missing-key diagnosis. The empty-observation stub does not prove retained completed history survives arbitrary-worker fallback. Real observation includes worker-specific exchange callbacks; refresh reconciles durable runtime state and is not a pure read. Those overbroad rationale claims are superseded pending actual composed-history proof.

## Owner209215 — deployment-first experimental iteration (2026-09-19T04:36:20Z)

> Owner selects deployment-first iteration. Finish the focused check currently underway, then prepare the current candidate and exact commands for my fresh experimental deployment. Additional coverage is not a prerequisite to that experimental run. Record unresolved review concerns explicitly; deployment does not imply acceptance or closure. Prioritize installed consecutive-Job and restart testing, preserving completed execution history and checking for redispatch. Keep deterministic providers, preserve existing instances, and retain the no-live-model/no-Git-mutation boundaries. Pin this decision in FINDING and PLAN.

Pinned by reviewer209260 from canonical thread message209215. This supersedes review209188 additional-coverage-before-deployment sequencing; it does not accept unresolved behavior or close Work.

## Review209459 — Work reuse explains the earlier claim gate

review-2026-09-19T05-15-54Z.md accepts the observed completed/released historical stages in run-status-209386.json. Supersedes the claim that bootstrap rebinds routes to new participants: it adds handlers and leaves existing Work routing alone. The new implementation reuses the completed Work still on integration; new handler membership does not reroute it. Prepare fresh Job/Work selection on the same instance while preserving Job3 and accounting for its reserved allocation. Publication-base continuity remains a separate unmeasured installed boundary.

## Review209517 — existing claim settlement semantics found

review-2026-09-19T05-24-05Z.md accepts19 passing composer checks and records an owner execution choice. Qualifies the settlement discussion: no deployment CLI verb exists, but worker_manager.offers.settle_claim already implements signature-bound settlement with deadline/refusal safeguards. Existing public operation investigation is an alternative to inventing new semantics; no invocation or direct release authorized by reviewer. Fresh experimental instance remains a selectable alternative, not recovery of this stalled episode.

## Review212187 — existing direct-target finalization supersedes unmade-choice framing

review-2026-09-19T12-48-47Z.md accepts the installed publication refusal. Owner137905 already approved coordinator-owned accepted-candidate delivery and target-ref CAS in the canonical direct-target amendment. Current finalize_direct_target implements it, but StageDeployment.reconciles gates its use on integration_observer, absent from this retained deployment. Revalidate that accepted path and source materialization before seeking a new continuity design ruling. This supersedes framing all three options as previously undecided, not the observed refusal. No manual repair authorized.

## Review212237 — observer correction and test-boundary clarification

review-2026-09-19T12-56-53Z.md accepts observer configuration for experimental deployment. Two accepted tests independently pass (3.313s); isolation script passes19, not22. The two-Job test prepublishes B before A advances and uses source=target, unlike a fresh successor from separate deployed clones. Supersedes claims that configuration alone proves the complete consecutive-fresh-Job path. Same-base admission/source materialization remain measurable boundaries; additional coverage is not a deployment gate under209215. Prior instances preserved; owner selection of next fresh experiment is next.

## Review212328 — incremental admission and absent advanced source object

review-2026-09-19T13-09-11Z.md independently reproduces the two-base bootstrap refusal. Advanced candidate exists in dedicated target but is absent from nominated workspace, with original base still readable. This supersedes the implication that a preflight exemption alone places terminal continuity one experiment away. Owner selection should cover immutable retained-binding admission plus supported isolated source materialization, preserving no-effects refusal and no policy rewind. Current restart/no-new-container statement is author-reported, not independently verified from retained before/after evidence.


## 2026-09-19T13:19:08Z — owner UX ruling: bootstrap is initial setup only

Recorded by baton.prompt from the owner's interactive instruction: “we also shouldn't be using bootstrap for any post-bootstrap processes. It's very misleading - ok for short term/now but that's bad UX”.

Confirmed normal operation is initialize once, manage the worker pool, then submit successive Jobs (A: R0 to R1; B: R1 to R2) while preserving prior history. Bootstrap must name initial setup only in the intended user-facing interface. Reusing the existing bootstrap command for post-install Job/capacity preparation is accepted only as a temporary experimental workaround, not the final UX. This explicitly supersedes any implication in earlier deployment recipes that repeated bootstrap is the intended ongoing workflow; those recipes remain historical evidence and temporarily usable instructions.

Provide clearly named post-install operations for worker-pool management and Job submission/preparation; exact command names remain to be designed. This ruling does not require a new deployment before the current continuity experiment or turn UI work into a gate for the selected correctness repair. Track the UX correction with the recorded first development task for user-managed worker addition, and carry the ruling into its implementation handoff. No implementation changes made by this entry.

## Review212438 — fresh installation effects precede base refusal

review-2026-09-19T13-25-29Z.md confirms R1: prepare_repositories now passes fresh multi-base input through held, creates directories and reaches clone before prepare/admissible_bases. REVIEW-PROBE-212438.json records intercepted-runner proof without executing Git. Supersedes the claim that every no-effects boundary is preserved. Correct all pre-effect entry points under owner212383 and continue the selected materialization extension; no further owner ruling needed. Full suite independently blocked by external disk fixture prerequisites.

## Review212486 — R1 corrected at fresh repository-preparation boundary

review-2026-09-19T13-31-54Z.md independently repeats the original probe: distinct bases refused before destination creation, zero clone calls. R1 corrected; prior regression remains chronological history. Continue already selected owner212383 materialization and sequential-Job proof; no new owner gate. Full suites remain author-reported under unchanged reviewer fixture limitations.

## Review212545 — supplement misclassifies non-absence failures

review-2026-09-19T13-40-55Z.md records R2: base present in both repositories plus private index.lock causes unnecessary fetch and false “in neither” refusal. Independently19 tests pass but omit this case. Supersedes claims that the implementation only fetches on absent base and that arbitrary fetch/detach failures prove absence. Production durable command-stream provenance and in-progress retry behavior remain unproved; profile configuration alone does not settle them. Continue within owner212383; no new approval gate.

## Review212593 — absence proof still conflates fatal errors

review-2026-09-19T13-48-06Z.md accepts lock/cause fixes but retains R2: _present treats fatal nonzero results as absent and does not validate text streams. Synthetic probe proves fetch after fatal presence failure and malformed-stream acceptance. Supersedes “proved absence/closed shape enforced” claim for this helper.21 tests independently pass but omit these cases. Content identity rationale accepted as rationale; recovery/composed proof remains unfinished under owner212383.

## Review212640 — R2 corrected at profile boundary

review-2026-09-19T13-53-16Z.md independently confirms23 passing profile tests, including fatal128 and malformed-stream zero-fetch regressions. Explicit result classification and corrected postfetch wording resolve R2; historical reviews remain evidence. Composed sequential-Job/recovery proof and candidate/final pool remain unfinished under owner212383.

## Review217322 — missing-attempt wording does not identify the caller

review-2026-09-20T02-54-41Z.md qualifies claim217230: prior_runtime_witness is also used for current-attempt pre-start/observation checks and proves no grant itself. Trace the first caller plus prepare/publication/store identity. Whole-test expectedFailure proves no prefix; A-history/no-redispatch assertions after blocked integration remain unreached, and12 errors is not green. Interrupted supplemental recovery remains pending evidence. Continue under owner212383 without invented runtime state.

## Review217381 — D8 namespace collision confirmed

review-2026-09-20T03-02-54Z.md independently confirms distinct attempt identities resolve to identical host delivery root. Source supports foreign retained assignment skipping B preparation. Diagnostic test now asserts the blocker and reaches history checks; terminal proof remains open. Recommend owner select per-attempt host namespace with fixed container mounts, retained legacy evidence, identity-bound adoption and unchanged fencing. Refusal-only does not meet consecutive direct-Job outcome.

## Review217558 — raw identity paths and intermediate symlink regression

review-2026-09-20T03-30-16Z.md records R3/R4: generic identities allow traversal/absolute/reserved names; raw basename also breaks the inverse for integration. New managed integration parent can be symlinked and adoption follows it. Independent probes confirm both despite26 passing namespace tests. Supersedes collision-safe/full-custody-preserved claims for candidate217457; candidate not accepted. Correct within owner217455, pin ambiguous dual-layout and identity-adoption handling, then rebuild on fresh provenance.


## 2026-09-20T03:40:07+00:00 — owner requests incident operator documentation

Recorded by baton.prompt: after handling the usage-limit incident, the owner requests incident handling/dismissal in docs/BATON-WORK.md so operators need not rescan source. Scope: inspection, action-owner authority, numeric incident selector, explicit claim recovery versus dismissal, and retained dismissed history. Revalidated against CLI incidents/dismiss and incident_dismiss; dismissal does not mutate Work. Documentation only.

## Review217641 — R3 accepted, creation still lacks held-object custody

review-2026-09-20T03-42-33Z.md independently confirms30 passing namespace tests and accepts hash/inverse correction. R4 remains: creation accepts0777 ancestor and follows replacement symlink between pathname check and leaf creation (temporary probe). Supersedes full managed-custody claim for candidate217574. Correct descriptor-relative creation/mode proof and audit subsequent pathname use within owner217455; candidate unaccepted.

## Review217777 — R4 accepted for experimental deployment

review-2026-09-20T04-04-35Z.md accepts the descriptor-relative correction at the reproduced boundaries and independently verifies candidate217672 executable/bundle plus109 source inputs. Supersedes R4-open status for this candidate. Runtime tests have no product failures; OCI coverage has one stale parent-geometry fixture, independently shown to reach the intended overlap refusal with deployment_root. Carry its bounded setup correction as non-gating. Owner experimental deployment choice next; installed acceptance and final pool remain unfinished.


## 2026-09-20T09:32:05Z — owner: 24-hour v12 investment gate and conditional one-week improvement phase

Recorded by baton.prompt from the owner's interactive ruling. Within 24 hours, v12 must demonstrate BOTH the working flow and a separately authorized real Claude Job producing an independently accepted useful result. Deadline anchored when recording the ruling: 2026-09-21T09:32:05Z (2026-09-21 03:32:05 America/Denver, MDT). This is an investment/cutover decision deadline, not a cumulative verification stopwatch budget.

The flow discussed with the owner is A completing R0-to-R1, followed by newly created B completing R1-to-R2 on the SAME persistent v12 deployment, with distinct Works, retained history and restart without redispatch. Separate worker containers are expected; per-Job redeployment/reset does not demonstrate this outcome. Deterministic proof alone does not meet the investment gate. The useful real Claude Job needs a concrete selected task, separate live-execution authorization and independent result acceptance before the deadline. This ruling does not itself authorize an unspecified live model run.

If both criteria pass within the window, owner selects continued investment and moving Jobs to v12: first v12 improvements, including TUI and robustness, with another week allocated; other business Jobs follow that phase. The week follows the successful go decision; its exact start/end and bounded Job selections are to be recorded then. This conditional phase does not authorize wholesale backlog migration or establish a second coordination authority.

If evidence is incomplete at the deadline, the continuation condition has not been met; report the missing evidence for the owner's cutoff decision. Do not label another partial fix, experimental deployment or unaccepted output as success or assume an extension. No automatic cancellation or unsafe interruption of active execution is selected here.

This supersedes any implication of open-ended investment or business cutover based solely on earlier bounded readiness signoff. Prior evidence, individual Work identities, active claims and correctness requirements remain intact. Deployment testing and focused coverage continue together; UX naming cleanup and broad optional coverage do not displace this immediate proof. Decision is cross-recorded at baton:work/records/2026/09/finding-v12-initial-claude-worker-pool/FINDING.md and baton:work/records/2026/08/finding-v12-isolated-agent-workers/FINDING.md.

## D9 (claim219702) — pooled operations do not attach live prior generations, so a pool cannot advance over a held episode

Measured installed on the owner-installed candidate217672 instance
(instance-2026-09-20T09-21-58Z), third compose on one deployment. Job
verification-3's implementation runtime faulted (fixture-idempotence,
see the same claim's fixture correction) and its allocation is
correctly HELD `reserved` at pool generation 2 under report-and-hold.
Applying the pool for the NEXT Job (verification-4, generation 3) then
refuses at start: `scheduler.PooledManagerOperations` requires "exactly
the active generation and live prior generations' configured
(generation, worker id) pairs" (`_required_workers` counts `reserved`
and `recovery-required`), but `tools/stage_execution.operations_from`
attaches ONLY the active generation's pairs
(`{(generation, one["worker_id"]): ...}`). The scheduler's D7 doctrine
REQUIRES the prior pair; the operations composer never provides one, so
any deployment holding a live allocation from a retired generation
cannot restart under an advanced pool — pool evolution is blocked by
exactly the held episodes report-and-hold exists to retain.

The exact refusal, verbatim: "pooled operations must provide exactly
the active generation and live prior generations' configured
(generation, worker id) pairs". Store evidence: stage_allocations has
(generation 2, verification-3-implementation) `reserved`;
pool_generations 3 activated; deployment.json names 3 with 9 workers.
Activation itself succeeded — the refusal is attachment's, after
activation, before any stage operation.

Correction at the measured boundary: `operations_from` builds its
attachment map from the scheduler's own required set — every live
prior (generation, worker id) pair attaches the SAME-NAMED worker's
operations from the composed membership (D7/review209188: the same
worker's own launch home, role and manifest context reads its own
history; workers are not interchangeable), and a live prior pair whose
worker is no longer composed refuses by name before anything runs.

Also pinned this claim, dossier-level (not product): the composer's
pool-generation prediction was the claim208217 two-state literal
(`2 if store exists else 1`) and refused correctly-but-lately on the
third compose; it now reads the durable pool and applies the
scheduler's mint rule. And the deterministic fixture's fixed candidate
filename was measured EMPTY at a base that already integrated it (Job B
materialized AT A's integrated commit); the candidate is now task-id
derived — deterministic per assignment, distinct across Jobs — with the
composer's verification command derived from the same field.

## D10 (claim220080) — the integrator identity contradiction: per-Job integrators satisfy launch OR settled observation, never both

Measured installed on instance-2026-09-20T10-23-11Z (the owner's fresh
install of candidate a6dbd963, D9 corrected), during the directed
A-then-B run. Job A (verification-1) COMPLETED — all three allocations
released, policy 9→10, canonical target and refs/heads/main agreeing at
4a424f0c carrying exactly the task-derived
`w197661-fixture-verification-1.txt`, capture green. Job B
(verification-2, fresh Work W2, composed after A) completed
implementation AND review with the corrected images — its line
materialized AT the advanced base 4a424f0c via the supplement, its
checkpoint (4a424f0c→4863888a) froze, the verdict accepted, eligibility
recorded — and then its INTEGRATION could not proceed, both ways:

1. WITH the composer's per-Job integrators retained (2 integration
   workers configured), the launch defers every tick at
   `stage_execution.integration_served`: "this deployment names 2
   integration workers; one deployment names one integrator". Silent in
   the durable stores; visible only in the serve tick report
   (manager-log/`serve --once`).
2. WITH prior integrators dropped (exactly one composed), the manager
   DIES at the first sweep: `stage_execution.worker_for` refuses
   observing SETTLED history — "stage 'verification-1/integration' is
   allocated to worker 'verification-1-integration', which this
   deployment does not configure". This is the D7 defect class
   (settled history vs current configuration) alive in the
   configuration-level resolver that the scheduler-level D7/D9
   corrections do not reach.

With per-Job integrator IDENTITIES already durable in allocations, no
configuration satisfies both gates: consecutive Jobs cannot complete on
one deployment. D10-EVIDENCE-220080.json,
manager-log-D10-220080.txt, run-status-final-220080.json.

THE TWO CANDIDATE RESOLUTIONS, routed rather than taken (each moves a
pinned rule, so the choice is the owner's/reviewer's):

(a) A CONSTANT integrator identity composed from the FIRST Job — one
    worker id, one participant, one principal across every Job, exactly
    `_PerJobIntegration`'s stated contract ("one worker id, one
    participant ... two Jobs' integration stages serialize"), with
    per-Job operands staying in the job bindings. Fresh instances then
    never drop a configured worker and both gates hold. This MOVES the
    measured one-participant-per-worker/per-Job-actors composition rule
    for the integration role, and the integrator participant's grants
    must cover every Work.
(b) `worker_for` adopts D7's settled-history rule (same-named worker in
    the newest configuration, else a configuration-independent
    observation for settled stages; live stages keep refusing by name).
    This is a product change enabling per-Job integrators to retire
    with their Jobs.

They compose: (a) is the correct forward shape for the real Claude
pool; (b) is still needed so a deployment can ever retire a worker name
that holds settled history. NEITHER is implemented in this claim.

Also measured while converging: the policy-pin repeat cost is NOT
uniform per Job (an apply adding a job moved +15 = 7×2+1; re-applies
moved +13 = 7×2−1 twice); the composer's model now carries that
measurement and the gate went green three consecutive times at 63, 76,
89. The one-integrator apply also demonstrated that
`pool_generations.document` retains only the scheduler's NORMALIZED
worker rows — a dropped worker's full deployment entry is NOT
recoverable from durable records, which is itself part of why (a)'s
never-drop shape is right.

State left: the instance preserved with all stores and evidence; A
complete with explicit locators (A-LOCATORS-220080.json); B's
implementation/review complete and retained, integration reserved;
the stack STOPPED and currently refusing start at gate 2 — loud,
named, and awaiting the D10 resolution; no manual repair performed.

## The PR model mapped (claim220329, under OWNER-HANDOFF-PR-JOBS)

The owner-selected PR-producing model maps onto EXISTING surfaces with
one composition change and one pinned gap; review220212's
stable-integrator proposal is not selected (owner220327) and its
review stands as history.

**The result contract already exists.** A Job's implementation+review
half produces everything the handoff's PR contract names: attributable
immutable commit on a durable line, base revision, changed paths,
patch/bundle transport, test evidence (the task's own verification
command with status), and an independent reviewer's durable verdict.
CANDIDATE-PR-220329.json demonstrates it from the stopped instance's
durable stores — verification-2's commit 4863888a over base 4a424f0c,
test status 0, verdict accepted — read-only, with its still-reserved
integration stage explicitly NOT represented as complete.

**The composition change:** `--pr` in compose-verification-208217.py
composes TWO stages (implementation → review) and TWO workers per Job,
no integration worker or stage. Shape-validated through the composer's
own validators against the retained instance (documents restored after
validation; nothing applied). With no integration allocations ever
minted, `integration_served`'s one-integrator gate and `worker_for`'s
settled-integration observation never bind — the D10 contradiction has
nothing to attach to on a fresh PR-mode deployment. NOT yet proven
installed: the Job-completion/report-and-hold semantics of a Job whose
LAST stage is review are revalidated on paper only; the installed
PR-mode run on a fresh instance is the required proof and needs no
new candidate build (no host source changed).

**The pinned gap — accepted-base continuity on one deployment.**
`bootstrap.admissible_bases`: an ESTABLISHED root admits NEW bindings
only at the Authority's CURRENT canonical target, and in the PR model
nothing automated advances that target. Review220364 [1]: a fresh
install per base does NOT satisfy owner item 4; the transition is
authorized under owner item 1 and is pinned here IN FULL for
implementation (claim220385):

- CONTRACT: `tools/accepted_base.py`, one verb `record`, operated by
  the OWNER against a stopped or running instance. Operands: the
  instance state root and an acceptance document (schema
  `baton.w202663.accepted-base/1`: repository, accepted_commit,
  included_candidates, acceptance_evidence, accepted_by, recorded_at,
  and expected_old — the canonical target the owner believes current).
- EFFECT, in the finalizer's own order (`authority/core.py` 2264-2282
  is the pattern; `Authority.set_policy("canonical_target", ...)` at
  core.py:188 is the one writer): (i) prove the accepted commit
  exists in the deployment's dedicated target repository (fetch from
  the OWNER's named repository into `repo/target.git` under the
  operator invocation — the operator's own transition, not an agent
  Git mutation); (ii) CAS the target reference from expected_old to
  accepted_commit, refusing by name if the reference is not
  expected_old; (iii) `set_policy("canonical_target",
  accepted_commit)`; (iv) retain the acceptance document as a receipt
  beside the instance (`accepted-bases/` under the state root).
- ACCEPTANCE (the review's own list): repository/commit identity
  proved before any effect; expected-old target/ref conditions
  enforced; IDEMPOTENT REPLAY (the same document re-recorded when
  target and policy already equal accepted_commit answers success
  without writing); CONFLICT REFUSAL (reference or policy at neither
  expected_old nor accepted_commit refuses without touching either);
  INTERRUPTION HANDLING (ref advanced but policy not → re-running the
  same document completes the policy write and the receipt; never a
  blind update); no fabricated integration receipt (the receipt is
  the acceptance document, labelled as human acceptance, never an
  integration result).
- TESTS: new `tests/tools/test_accepted_base.py` — one case per
  acceptance bullet over a temporary instance-shaped root.
- FILE OWNERSHIP: new files only (`tools/accepted_base.py`,
  `tests/tools/test_accepted_base.py`); `admissible_bases` itself is
  UNCHANGED — once the canonical target equals the accepted base, its
  existing rule admits the new Job as-is.

Implementation is the immediate next claim's first item; nothing else
blocks it.

**Prepared for separate authorization:** REAL-JOB-PROPOSAL-220329.md
bounds the recorded worker-add task to a single `add-worker` verb with
its own test gate, names scope/base/credentials/reviewer, and carries
the exact launch commands. Nothing launches without the owner.

## Review219927 — corrected fixture absent from selected immutable images

review-2026-09-20T10-03-01Z.md records the host fixture/task change while composer still selects historical emitting/silent image digests. Supersedes the claim that only a corrected host-runtime install is needed for the ready A-then-B experiment. Rebuild and pin affected fixture images with task-derived behavior before the next deployment handoff. Runtime candidate identity and88 focused tests independently verified; A retained Job document identical across snapshots. Sequential completion and real Claude acceptance remain unmet.

## Review219992 — corrected fixture images accepted for experiment

review-2026-09-20T10-10-28Z.md supersedes review219927 missing-image status: both rebuilt image pins independently present and matched to current composer;25 recorded recipe/file hashes match;19 isolation checks pass. Author two-task in-image proofs reviewed, not rerun. Owner installed experiment next; capture newest-only helper cannot alone prove both Jobs retained, so preserve/read explicit A locators after B. Installed success and real Claude criterion remain open.

## Review220212 — D10 confirmed with bounded forward recommendation

review-2026-09-20T10-46-19Z.md confirms both guards from retained logs/source and independent synthetic probes; A Job snapshot unchanged, B integration reserved. Qualifies all-configurations-impossible and guaranteed-next-run-success claims. Recommend owner select stable shared integrator from first Job, explicitly superseding integration-only per-Job actor rule; any retirement repair must prove durable settled history without arbitrary worker fallback or waived identity/fencing/cleanup. Concrete useful live Job proposal still missing; owner selection next.


## 2026-09-20T10:56:55+00:00 — owner clarifies contributor and integration-Job flow

Recorded by baton.prompt from the owner's interactive clarification. Contributors are independent workers: each takes a base commit, produces changes and submits a commit/PR proposal. Many contributors may work from the same base. Integration is itself another Job: it gathers selected commits 1 through N and produces a combined commit proposal. Prompt plus human test, evaluate, review and merge that proposal into official mainline. The resulting accepted mainline base supports the next wave of parallel work. Producing or internally accepting an integration candidate is not itself owner acceptance into official mainline.

There is no requirement for one permanent integrator identity in this model. Integration Job identities/qualified workers may differ. Correct attribution, preserved history, and controlled/fenced writes to a shared target remain required; these do not imply a singleton worker identity. This clarification supersedes the foreground recommendation to treat one stable integrator as the intended long-term workflow. Review220212's stable-integrator recommendation remains historical decision support, NOT an owner-selected architecture. At most it is a possible temporary experiment, not proof of the full selected contributor flow; no selection of that workaround was made in this clarification.

Revalidate D10 and integration selection/history against this ruling before implementation. Identify the exact relationship between current internal integration stages/Jobs, candidate targets and the official mainline acceptance boundary; do not assume existing automatic target finalization authorizes an official-mainline merge. This is not an instruction to mutate Git, bypass independent review, rewrite historical decisions, or change live claims. Preserve the prior accepted direct-target evidence; clarify any conflicting scope explicitly before changing implementation.

Sequential A-to-B continuity remains a useful prerequisite, but does not by itself prove many contributors from one base feeding a distinct integration Job and owner-accepted next mainline. The existing 24-hour investment deadline remains unchanged; report evidence against its selected criteria honestly and make any delta explicit. Canonical cross-references: baton:work/records/2026/09/finding-v12-initial-claude-worker-pool/FINDING.md and baton:work/records/2026/08/finding-v12-isolated-agent-workers/FINDING.md.


## 2026-09-20T10:57:26+00:00 — owner permits prompt/human integration for the 24-hour gate

Recorded by baton.prompt: owner says “if integrator is a major milestone for our 24 deadline, we can be the integrator”. Prompt plus human may perform the integration role for the deadline demonstration. Automated integration execution, D10 singleton resolution and a dedicated automated integration Job are therefore not prerequisites to passing that demonstration. This explicitly supersedes the automated-integration requirement implied by the earlier A/B terminal-flow gate, for this bounded investment decision only; it does not declare D10 repaired or automated integration accepted.

Minimum demonstrated flow: v12 produces a candidate from R0 with independent review; prompt/human evaluate and integrate it into official R1; a subsequent v12 Job uses accepted R1, produces another reviewed candidate, and prompt/human can accept it into R2. Use the same persistent deployment, preserve attribution/history and account for restart without redispatch. Separately selected and authorized real Claude execution must produce an independently accepted useful result. No unspecified live run is authorized by this role substitution. Deadline remains 2026-09-21T09:32:05Z.

Human integration is an explicit selected workflow, not manual repair of a stuck runtime/store or policy. Git ownership is unchanged: Slawomir performs all Git mutations; prompt can review, test, prepare files and supply commands within authorized scope. Do not manufacture integration receipts, falsely mark held attempts complete, reset the deployment per Job, or claim automated end-to-end success. Establish the supported handback and next-base preparation path, and report any missing boundary as the concrete remaining blocker. Preserve automated-integration findings for subsequent work.


## 2026-09-20T11-02-49Z — owner selects PR-producing Jobs as ongoing v12 model

Owner confirms this can be the permanent operating setup and requests implementation handoff to Claude. Canonical ruling and execution handoff: baton:work/records/2026/09/finding-v12-initial-claude-worker-pool/OWNER-HANDOFF-PR-JOBS-2026-09-20T11-02-49Z.md. Independent Jobs produce reviewed proposals; prompt/human integrate, or explicitly request an integration Job producing another proposal. Dependents wait for an accepted commit containing their required results. This supersedes mandatory singleton/automatic integration and temporary-only framing of human integration, without claiming current product support or repairing historical failures. Investment deadline and separate live authorization remain unchanged.

## Review220364 — selected PR flow remains incomplete within authorized scope

review-2026-09-20T11-10-21Z.md accepts owner220327 supersession of automatic integration/stable-integrator prerequisites. Corrects fresh-install-at-each-base framing (not selected continuity), records nonfunctional Claude launch flags against historical composer, and logs unsupported direct-SQL inspection recipe as an operational gap. Complete supported candidate readout, PR terminal proof, accepted-base continuation and usable Claude configuration under existing owner pin-before-edit authority; live submission still requires separate authorization.

## Review220421 — partial PR preparation accepted; transition pin needs concurrency/replay completion

review-2026-09-20T11-18-20Z.md accepts locator-based public readout and ignored-argv correction with independent temporary selector/task probe. Accepted-base tool and PR terminal proof remain unimplemented. Qualifies claimed finalizer-equivalent ordering: unconditional set_policy after Git CAS lacks transactional expected-old proof; success-without-writing after both targets advance loses a missing receipt. Pin durable document-bound intent, exclusion and complete interruption/replay contract, then implement under existing owner220327 without a new approval gate.

## Review221684 — accepted-base exclusion/refusal/replay gaps confirmed

review-2026-09-20T14-47-50Z.md records lifecycle lock released after start (not stopped-instance proof), independently reproduces Git ref advancement despite stale-policy refusal, and exit0 replay from receipt containing only acceptance with no committed operation.9 focused tests pass but omit those assertions. Supersedes implemented-full-contract claims for candidate221639; candidate unaccepted. Correct complete operation/durability boundaries under existing scope, then PR terminal proof/pool validation and fresh candidate.

## Review221748 — refused preflight becomes false resume authority

review-2026-09-20T14-56-14Z.md accepts earlier correction sites with16 independent passing tests but reproduces first coincidence-refusal creating intent and second identical call advancing Authority successfully. Supersedes complete-resume-proof claim for candidate221705, which remains unaccepted. Establish admitted intent only after initial validation (or explicit phases), strengthen retry regressions and whole-write/directory durability, then complete PR proof and pool validation.


## 2026-09-20T14:57:48+00:00 — owner: generic artifact references, no Git semantics in coordination

Recorded by baton.prompt from the owner's explicit confirmation: retain a commit ID or PR location as artifact information crucial to agent operations, without interpreting Git semantics. This is generic support, not Git-specific machinery. Agents interpret task instructions such as “take commit X, make changes, offer PR” or “combine PRs 1–3” and use their authorized tools. Commit IDs, PR locations and equivalent non-Git artifact references/metadata must be retained and delivered accurately to agents. They are operationally important context, not executable Git instructions for the coordinator.

Baton coordinates explicit inputs/dependencies, isolated execution, attributable outputs, independent review and human acceptance. An accepted result can satisfy dependencies and be passed as an explicit input to later Jobs without the core parsing revisions, fetching objects, moving Git refs or enforcing one global Git base. Reference metadata does not alone prove content, review or acceptance; preserve provenance and evidence without assuming a Git-specific proof mechanism. Agent Git operations remain subject to the actual task's authority and repository Git policy; this ruling does not lift Slawomir's Git ownership here.

This explicitly supersedes the selected-core interpretation in earlier accepted-base plans/reviews that recording human acceptance must synchronize a deployment Git ref and canonical Git policy, and that this cross-system Git transaction is required for the 24-hour demonstration. Earlier review findings about that implementation remain valid historical evidence, not requirements to finish the wrong abstraction. Revalidate the pending implementation against generic result acceptance and explicit successor inputs before further Git-transaction work. Preserve existing artifacts/partial code and active claims; do not silently delete, migrate or declare them accepted. Any exact product migration/patch scope must be pinned before editing. Deadline and separate authorization for the useful real Claude Job are unchanged.

## Review221816 — generic-artifact ruling supersedes transaction gates

review-2026-09-20T15-05-54Z.md applies owner2026-09-20T14:57:48+00:00/prompt221781: earlier reviewer Git accepted-base transaction gates are superseded for the selected flow; retain their evidence and partial code. Author221806 handoff remains on old scope and needs revalidation. Two-stage PR proof is useful author evidence but inherited composition still includes integrator; add actual two-worker factory topology and opaque accepted-result successor continuity. No current-scope deployment signoff for candidate221761.

## Pinned correction scope (claim221832) — the generic-reference model applied at its smallest exact sites

Under owner 2026-09-20T14:57:48Z and review221816, before editing:

1. `tools/bootstrap.admissible_bases`, ESTABLISHED branch only: a new
   binding's `line_declared_base` is OPAQUE reference metadata carried to
   agents; the coordinator neither compares it to the Authority's
   canonical target nor forces all new bindings to one value. The
   established branch's canonical-target reads and both equality rules
   are removed; the FRESH-root one-base rule stays untouched (it guards
   the integration publication comparison, which the PR flow does not
   reach, and relaxing it is not needed for the selected demonstration).
   Conflict/mutation checks for RETAINED bindings stand exactly as they
   were. Tests updated in `tests/tools/test_bootstrap.py` only where
   they assert the removed equality.
2. The composed PR proof gains the review's two required halves:
   (a) the factory topology REALLY composes two workers and no
   integrator — `composed_document(workers=<impl+review>)`, measuring
   what `operations_from` does with no integration worker configured and
   pinning the smallest correction if it refuses; (b) successor
   continuity — after job-a settles at its accepted review, job-b is
   admitted on the SAME deployment with `line_declared_base` set to
   job-a's candidate head AS AN OPAQUE STRING (explicit successor input,
   no canonical-target involvement), reaching its own completed review.
3. `Authority.accept_base` and `tools/accepted_base.py` stay AS HISTORY
   (unfinished Git-synchronizing halves not deployed, per the owner);
   no deletion, no further work on them this claim.
4. OWNER-PR-FLOW's section 4 gets the revised boundary note (acceptance
   recording is generic metadata; the Git-transaction verb is
   superseded); OWNER-RUN/candidate records refreshed only if runtime
   inputs change.

## Review221919 — explicit successor input remains unfinished

review-2026-09-20T15-22-37Z.md accepts scoped established opaque-reference admission and optional integration role; independent boundary probe accepts non-Git metadata without Authority read. Actual successor composed proof remains unwritten. Current composer still reads dedicated target and exposes no accepted-reference operand, so supply runnable explicit successor input/commands and supersede stale OWNER-PR-FLOW section5. No installed-readiness or completed-flow signoff yet.

## Review222023 — proof delivered, input-availability commands incomplete

review-2026-09-20T15-39-26Z.md accepts scoped publication changes with112 independent passing driver tests (2.467s) and author-attributed two-Job composed proof. Operator recipe omits the proof's fetch into the nominated source; real Claude composer still lacks explicit accepted-reference input. Complete workload-specific source/input preparation and exact commands, without reviving core Git synchronization. Append actual publication correction history and supersede the stale no-publication PR rationale. Installed continuity and useful authorized live result remain open.


## 2026-09-20T15:40:33+00:00 — owner: typed artifact metadata, consumer-interpreted protocol

Owner clarifies generic metadata may carry a MIME-like type/protocol hint saying this reference uses a Git workflow. Baton retains and transports the reference and its hint; agents or explicitly selected consumers interpret the protocol and perform authorized operations. Core metadata validation may check the generic envelope, but must not universally impose Git revision syntax (such as 40 hexadecimal characters), parse Git ancestry, fetch objects or move refs. Type hints are descriptive, not execution authority, acceptance proof or permission to invoke tools. Unknown types remain opaque metadata subject to generic structural limits; a consumer may explicitly refuse an unsupported type. Exact field names/type identifiers remain unselected; no new registry or automatic adapter dispatch is required for the deadline.

This refines the generic-artifact ruling and supersedes treating reference typing itself as forbidden Git coupling: retaining a Git type hint is allowed; coordinator Git semantics are not. Any Git-specific validation must be confined to an explicitly selected Git workflow/consumer, not the general artifact-reference contract. Revalidate the current --base 40-hex check against that distinction. Recorded by baton.prompt; no implementation changed.

## Pinned publication correction (claim221940, appended at claim222049 per review222023 R3)

The claim221832 pin above said the PR flow "never reaches" the
integration flow's publication comparison. That was WRONG and is
superseded: the implementation stage's CONCLUDE publishes the proposal
through `integration/driver.py`, and its two offer-time comparisons of
the proposal's base against the Authority's canonical target ("a
proposal is offered against the revision it was built from" — once at
the offer, once again in `publish_candidate`) were measured by
deferral probes blocking the PR successor's conclude in the composed
proof.

The correction, applied at claim221940 under the same owner ruling:
the proposal's recorded target IS its own declared base — for every
proposal the removed gates ever admitted the two values were equal, so
no admitted document changed — the offer-time canonical-target reads
are gone entirely, and `integrate`'s stale-target door, inside its own
committed Authority transaction, remains the integration flow's
enforcement exactly where it was. The two drift tests became their
admission counterparts. Proven end-to-end by
`AAcceptedPRSeedsTheSuccessorOnTheSameStores`.

Also appended per review222023: [R1] successor lines materialize from
the deployment's nominated source, so the owner flow now carries the
explicit owner-run transport of the accepted object into
`$DEST/repo/workspace` plus the resolve preflight (OWNER-PR-FLOW
section 3); [R2] the Claude pool composer now exposes the same
explicit `--base` accepted-reference input as the verification
composer, and the real-Job launch commands carry it.

## Review222071 — bounded owner experiment accepted

review-2026-09-20T15-44-09Z.md accepts corrected source transport, Claude explicit base input and appended publication history. Independent probes confirm target-read bypass;110 inputs and81-file bundle360fa9a4 match candidate221940/executable76528d51. Git-SHA1 composer restrictions are workload-specific, not a generic metadata contract, per owner222050. Review supplies current two-stage PR commands superseding old three-stage run instructions and requires source preflight for the real Claude recipe too. Pass to owner; installed continuity and separately authorized useful live result remain open.

## Review222192 operational observation — status open mode

The supported tools.job_manager status command with control/observe failed in this managed read-only installation context with sqlite3.OperationalError: unable to open database file at JobStore.open. Source shows status opens stores through writable open despite its read-only projection. No escalation or raw SQL attempted. Reviewer will use the existing public open_readonly methods with the same status/observation composition as a bounded read-only diagnostic; this is a disclosed stopgap, not a CLI repair. Exact deployment is instance-2026-09-20T15-53-26Z.

## Review222192 — canonical A review evidence required

review-2026-09-20T16-04-31Z.md independently verifies candidate2fb0612c content and refreshed110-input/81-file bundle456c75cc. Saved A status is canonical=false with claimed states/null observations, so cleanup release does not establish accepted completed review. Both normal and public read-only Job-store opens failed in reviewer context; cause not established. Return for supported canonical projection and exact accepted verdict/checkpoint/line/log locators from stopped instance, without rerun or repair. Append bootstrap/pin correction history. Owner acceptance and B remain pending.

## Pinned corrections (claim222138, appended at claim222215 per review222192)

Two corrections were applied at claim222138 and are pinned here with
their measurements:

1. `tools/bootstrap`'s role-coverage gate required an integration
   worker ("no worker is configured for the integration stage",
   measured refusing the first installed PR composition on the fresh
   221940 instance). The integration role is now optional there,
   mirroring `stage_execution`'s accepted gate; implementation and
   review remain required; the coverage test split into the
   required-role refusal plus the producer-and-reviewer admitted case.
   The APPLY runs from the checkout, so the installed experiment was
   unaffected; candidate 222138 (executable 0b5455a3..., bundle
   456c75cc...) carries the corrected gate coherently.
2. The verification composer's policy-pin prediction misread "first
   bootstrap" from the JOB STORE's existence — the first START creates
   that store, not bootstrap — so every pre-start compose predicted
   the fresh bump; and PR mode costs ONE LESS policy bump per
   preparation (measured: fresh +7 vs the three-stage +8; repeat +6 vs
   +7). Both corrected in the composer (first = the deployment
   record's existence; PR reduction applied); the pin gate caught the
   stale model three consecutive times and went green at generation 26
   — the gate, not the prediction, protecting the deployment
   throughout.

Evidence completion (claim222215, review222192 R1): the canonical
observing status of the stopped instance answers canonical:true with
both stages COMPLETED; the accepted verdict-checkpoint-line-candidate
association is proved end-to-end through `review_cycles`' public
proving readers with the verdict id derived by `record_verdict`'s own
rule (attachment + disposition); A's retained stream locators are
digested from the stopped instance. The reviewer's read-only JobStore
OperationalError was not reproduced through the ControlStore public
path used here; the JobStore-side canonical read went through the
installed binary's own status --observe surface instead.

## Review225163 — canonical A evidence accepted

review-2026-09-21T00-18-54Z.md resolves review222192 R1: canonical author snapshot shows both stages completed; independent public proving readers confirm accepted fixture verdict linked to exact frozen2fb0612c candidate and accepted line. All four A stream/status hashes match. Pass to owner for actual acceptance/source preparation and B authorization on the same stopped deployment. No human acceptance, B execution or useful live Claude result is inferred; deadline unchanged.

## Review225331 — existing-clone recovery missing from proposed unblock

review-2026-09-21T00-45-32Z.md accepts owner A acceptance and initial source-ref diagnosis, superseding earlier presence-only source-preflight sufficiency. Existing B clone is confirmed; materialize retry skips clone and fetches absent base only from dedicated target, never refreshed source. Independent mock probe corroborates. Source-ref fetch plus restart alone is not a proven unblock. Preserve reserved attempt and prepare deterministic same-line recovery plan; installed-runtime changes require applicable owner selection. Record serve-once escape and source-retry limitation before workaround.

## Source-retry limitation and serve-once exception (claim225345, recorded before any workaround per review225331)

LIMITATION, confirmed in source (`checkpoint_profiles.materialize`): on
recovery over an EXISTING line checkout the clone step is skipped by
design ("the one existing checkout is resumed, never cloned or copied
again"), and a proved-absent declared base earns exactly ONE delivery
attempt — from the dedicated-target SUPPLEMENT. The NOMINATED SOURCE
is never refreshed, so an object that arrived in the source AFTER the
clone (the PR flow's human-acceptance transport) can never reach the
existing checkout, and the retry loops on the two refusals measured at
claim222268.

EXCEPTION, recorded: a materialization `ProfileRefusal` CRASHES the
`serve --once` reconcile surface (the launch exception propagates
through `reconcile`) instead of recording a deferral; the live serve
retries each tick. Robustness note, not repaired here.

PINNED BOUNDED CORRECTION (product, `checkpoint_profiles.py` only):
after the absence proof on an existing checkout, refresh from the
NOMINATED SOURCE first (a fetch of the source's refs into the line,
the transport that carries the owner's accepted ref and its objects),
re-prove presence, and only then fall to the dedicated-target
supplement exactly as today, every cause preserved verbatim. One new
deterministic test: materialization over an existing clone refusing
while the declared base is absent everywhere, then the base made
ref-reachable in the source, then the SAME line materializing
successfully — plus the supplement fallback unchanged. A runtime input
changes, so a corrected candidate follows on the reviewed cadence.

OWNER SELECTION RETURNED (owner225266 selected the installed runtime
and no reinstall; the correction cannot reach that runtime without an
install, so the choice is the owner's):
(a) IMMEDIATE, on the CURRENT installed runtime, no product change:
    make the accepted commit ref-reachable in the DEDICATED TARGET —
    the repository the EXISTING supplement already fetches from — then
    start; B's reserved attempt retries and the supplement delivers
    the now-reachable object. Exact commands in
    OWNER-UNBLOCK-B-225345.md. An owner act on the owner's deployment
    repository, interpreted by nothing in the coordinator; no manual
    clone repair, no resubmit, no rerun.
(b) FORWARD: install the corrected candidate on a fresh instance and
    re-run the PR A→acceptance→B there (contradicts no-reinstall for
    THIS experiment; the source-refresh correction then serves every
    later deployment without target-side acts).

## Review225408 — existing supplement recovery recommended; source-refresh diagnostic gap

review-2026-09-21T00-56-57Z.md recommends owner-selected option(a) in OWNER-UNBLOCK-B-225345.md with exact accepted-ref equality before start; existing supplement delivers to retained clone without runtime replacement, main/policy update or resubmission. This remains a disclosed workload input workaround, not completed recovery.33 profile tests pass independently in0.529s. New candidate225345 loses source-refresh cause on later supplement refusal (mock reproduced); correct diagnostic chaining/regression before forward-candidate signoff, without gating current installed recovery.

## Claim225452 — B completed on the accepted base; both-causes diagnostic corrected

The owner's option-(a) unblock (accepted commit 2fb0612c made ref-reachable in
the deployment's dedicated target, event 225450) let B's reserved attempt
retry on an ordinary tick: candidate 446fa8f7 ON base 2fb0612c, review
accepted, both allocations released cleanup-retained. Canonical, association
and A-comparison evidence: `run-status-PR-B-canonical-225452.json`,
`CANDIDATE-ASSOCIATION-B-225452.json`, `AB-COMPARISON-225452.json`,
`CANDIDATE-PR-B-225452.json`. A's history byte-identical after B. This
demonstrates gate criterion 1 on ONE persistent deployment.

Review225408's diagnostic gap is corrected in the FORWARD candidate only: the
supplement-refusal message now preserves a failed nominated-source refresh
alongside the supplement's own cause
(`AFailedRefreshTravelsWithTheSupplementRefusal`, 42/42 green). Rebuilt on the
reviewed cadence as candidate 225452 (executable 786af0d5…, bundle 7305d1c7…);
NOT installed; the running instance untouched. Candidate 225345 superseded as
history.

## Review225497 — same-deployment deterministic chain accepted

review-2026-09-21T01-10-00Z.md independently confirms accepted B candidate446fa8f7 based on owner-accepted A2fb0612c, entire A Job projection unchanged, eight retained A/B log/status hashes matching. Technical continuity criterion1 demonstrated with explicit owner supplement workaround; B human acceptance/final gate determination not invented.42 profile tests pass0.686s; reproduced diagnostic gap fixed. Candidate225452 executable786af0d5/bundle7305d1c7 and110 inputs verified for bounded owner experiment. Useful real-Claude authorization/fresh-target validation and criterion2 remain open.

## Claim225533 — real-Claude PR pool prepared and gated on the 225452 instance

Owner accepted B and installed candidate 225452 at
instance-2026-09-21T01-12-21Z. All launch preflights passed: identity,
accepted-base ref-reachability in the nominated source, PR composition at
--base 446fa8f7 (zero refusals), provider image identity engine-held,
bootstrap applied, policy pin 14==14 through the corrected pool-mode gate.
Defect found and fixed: compose-pool-207219.py's policy_pin lacked the
PR-mode measurements (gate refused 9≠8; ported, re-applied, passed).
verify-next-instance.sh and check-policy-pin.sh corrected for the pool
stage. LIVE-LAUNCH-PACKAGE-225533.md holds the two remaining
owner-authorized commands and limits. No start, no submission, no
credential read; A/B instances preserved.

## Review225576 — live verification cwd mismatch

review-2026-09-21T01-22-13Z.md independently verifies installed/image/task identities, actual source accepted tip and policy14 equality. Launch task verification argv names tests.tools modules from repository-root worker cwd, but modules live under v12/python; correct explicit working-directory/import setup and prove it deterministically before live authorization. Recompose/reapply frozen inputs and pin. Package source-path statement must name actual deployment workspace; report numeric resolved limits. No live launch authorized.


## Owner ruling 2026-09-21 — deadline-focused implementation and review

Recorded by baton.prompt from the owner's instruction: instructions to Claude and reviewer must be razor focused; no needless tests or long sweeps. The deadline remains 2026-09-21T09:32:05Z. This supersedes any broader verification or polish sequencing that would delay the bounded live trial without addressing a concrete blocker.

Current critical path: correct review225576's frozen verification cwd/argv error; demonstrate the affected command reaches the intended suites from the actual candidate root with the selected toolchain; refresh changed input identities and policy pin; return the concrete launch package for separate owner live authorization. Reuse accepted runtime/image/source/A-B evidence unless a relevant change invalidates it. No broad suite discovery, repeated A/B runs, stress tests, unrelated cleanup or coverage expansion. Tests required by the selected live task and focused checks needed for a concrete correctness defect remain required. Review only the changed boundary and launch-blocking issues, then hand back promptly. Record unrelated findings for later without expanding this round. No live execution authority is supplied by this focus ruling.

## Claim225590 — verification argv + provider image corrected; fresh deployment fully gated

R1 (review225576) fixed: task argv enters v12/python via the interpreter;
demonstrated from a candidate-root context (126 OK exit 0 with labeled
fixture; exit 1 on failure). The demonstration exposed a SECOND blocker:
the provider image lacked jsonschema — the product's one declared
dependency — so the frozen gate died at collection in-image.
Dockerfile.claude adds python3-jsonschema (in-recipe rationale mirrors the
version-control-client precedent); candidate image 448c98c9… runs the
exact argv 126 OK in-image; test_dogfood_image green. In-place task-byte
change correctly refused by the manager → fresh
instance-2026-09-21T01-28-41Z from the same reviewed 225452 distro;
composed at the accepted base, staged bytes verified, pin 14==14 (after
the gate caught the "first = no configured capacity" prediction defect —
this installer writes an empty deployment.json).
LIVE-LAUNCH-PACKAGE-225590.md supersedes 225533: correct nominated-source
path, resolved numeric limits (3600/900 s), episode vs internal turns.
01-12-21Z and all A/B instances preserved; no start, no submission, no
credential read.

## Review225653 — revised live package accepted for owner decision

review-2026-09-21T01-33-21Z.md accepts corrected staged argv and missing-jsonschema image correction. Independent image448c98c9, installed786af0d5, both staged task/manifests and Job87033f1b identities, actual source446fa8f7 tip and pin14 verified.126-test in-image discovery-fixture proof remains author-attributed, not useful implementation coverage. Owner must explicitly select new01-28-41Z instance/image and separately authorize live start/submit per LIVE-LAUNCH-PACKAGE-225590.md. Criterion2 remains open.


## 2026-09-21 — owner live start refused: missing workspace directories

Recorded by baton.prompt. Owner selected the reviewed LIVE-LAUNCH-PACKAGE-225590 and ran its start/submit block. Start refused before submission at configure_workspace_storage: configured directory not visible. Read-only filesystem inspection confirms BOTH workers/implementation/storage and workers/review/storage are absent on instance-2026-09-21T01-28-41Z; workers has no role subdirectories. This is a concrete preparation omission, not evidence of provider/authentication failure. compose-verification-208217.py explicitly prepares worker directories; the live composer names the paths without equivalent preparation. Exact preparation ownership/correction remains for implementer revalidation. Review225653 identity/pin success did not establish startup readiness. No workaround or installed mutation performed by prompt.

Next bounded action: correct live-pool directory preparation, check exact required startup paths/types/ownership without reading credentials, and validate actual startup before reporting ready. Preserve instance, frozen task and provider image, prior A/B evidence, and owner-selected one producer/one reviewer episode limits. No broad suites, deterministic A/B reruns, new deployment, or manual database/attempt repair. Owner start failed in set-e block, so that block never reached submission.

## Claim226109 — start refusal corrected (two composer preparation defects); startup demonstrated

Owner's authorized start refused at configure_workspace_storage: the pool
composer named worker directories without creating them AND named a
workspace store per role where the manager scopes ONE store (second
refusal measured at this claim's own start attempt: "a changed store is a
fresh store"). Both corrected in compose-pool-207219.py (preparation
ported from the verification composer; one manager-scoped store, the
implementation worker's, per W197661's accepted composition). Frozen task
bytes and candidate image unchanged; instance preserved; repeat applies
moved the pin 14→20→26 with the gate equal each time; submission/staged/
deployed identities agree at 4f18ef79. Startup then demonstrated and left
running: "ready ... an empty configured stack is a valid idle state"
(STARTUP-DEMONSTRATION-226109.json). Only the submit command remains,
owner-authorized.

## Review226135 — preparation accepted; process-view caveat

review-2026-09-21T02-52-47Z.md independently verifies required directories/types/owners, shared workspace store, separate homes, unchanged staged task/image, Job4f18ef79 and pin26 equality. Author startup success accepted as evidence. Reviewer status shows fresh canonical zero-Job snapshot but both PIDs stale and absent from local ps; visibility/state cause unproved. Owner checks process health in launcher context before exact absolute-path submit command; no repeat image/live selection or broad sweep. Criterion2 remains open.

## Claim226329 — live launch failed pre-runtime: credential reference unresolvable; zero spend

Owner-submitted Job observed read-only: implementation released
`launch-failed-before-runtime` (no runtime, no container, offer expired),
review blocked. Checkout materialized fine first. Cause: credential
profile reference `w202663-development` absent from the operator registry
(sole entry: `w64268-run1`); resolver refuses at launch preparation. No
provider contact, no credential read, no restart/resubmit/registry edit.
Options and evidence in LIVE-LAUNCH-FAILURE-226329.json: (a) owner adds
registry entry (no recompose needed) or (b) owner selects the existing
reference (recompose+review). Stack left exactly as found.

## Review226363 — pre-runtime failure confirmed; ordinary tick is not recovery

review-2026-09-21T03-30-36Z.md independently confirms canonical exceptional implementation/released allocation/no runtime and blocked review. Missing registry mapping remains author-attributed, consistent with exact-pair resolver behavior; no credential inspected by reviewer. Supersedes claim226329 ordinary-tick retry speculation: durable failure and released assignment require an explicitly selected supported recovery/new episode or fresh Job, with prior assignment disposition checked. No useful result accepted; zero billing not independently established. Owner226327 resolves stale-PID caveat. Owner selects account mapping and authorizes recovery; preserve instance/evidence, deadline unchanged.

## Claim226458 — fresh-Job recovery prepared beside the preserved pre-runtime failure

Review226363's correction honored: no tick retry exists for the released,
live-episode failure; REPLACEABLE_ENDINGS are the two abandonment endings,
neither reachable here without new product surface. Recovery = fresh Job
beside preserved evidence (this Work's accepted cadence).
compose-pool-207219.py gained the verification composer's two-Job support
(select_job, prepared workers/jobs verbatim, pool-generation prediction,
per-job pin arithmetic, principals union — its validator caught the
narrow-principals defect on first run). Job-2 (W2, coder-2/reviewer-2,
same frozen task/image/base) composed, applied, pin 26→38 equal; 4
workers/2 bindings/one store; submission names job-2 only; next
activation mints pool generation 2. Owner commands (credential mapping
w202663-development → w64268-run1's file, secret-safe; stop/start;
submit job-2) in RECOVERY-PATH-226458.md. No live acts, no credential
mutation, no reinstall; failed Job and all instances preserved.

## Review226502 — credential-command conflict handling and supported pool observation

review-2026-09-21T03-51-01Z.md accepts unchanged failed-Job projection, pin38 equality, fresh Job2-only submission and task semantic preservation. Requests exact destination mapping validation/private exclusive replacement and fail-closed owner sequence; current command can silently accept wrong-provider or different-path mapping. Newly ported composer raw SQL violates coordination policy; replace with public read-only readers, no bootstrap rerun needed. Supersedes claim226458 command-ready claim until these narrow corrections pass. No live/credential acts.

## Claim226516 — R1/R2 corrections: fail-closed registry command; public-reader pool prediction

R1: RECOVERY-PATH-226458.md's registry command refuses
conflicting/ambiguous w202663-development destinations, no-ops only on
the exact owner-selected mapping, creates the replacement exclusively
(O_EXCL 0600, unpredictable name, unlink-on-failure), and every owner
block is fail-closed with absolute store paths; behaviours demonstrated
on temporary metadata fixtures only
(registry-command-fixture-226516.json, 4/4, no real reads). R2: the
composer's _pool_generation_prediction now reads the durable pool through
JobStore.open_readonly + scheduler.active_generation/pool_workers (no raw
SQL); validated answering 2 against the applied two-Job deployment. No
recompose/rerun; applied state (pin 38, job-2 submission, preserved
failed Job) stands as independently accepted.

## Review226539 — corrected owner recovery package accepted

review-2026-09-21T03-55-09Z.md closes review226502 R1/R2: five independent metadata cases pass0.056334s; public pool helper independently predicts2. Exact mapping/refusal/private replacement and fail-closed commands accepted for owner execution decision. No real credential/live acts; reuse Job2/pin38/failed-Job evidence. Owner runs selected package then returns observation; criterion2/deadline unchanged.

## Claim226576 — first real episode: complete candidate work in the line; fault at authoritative verification capture

Job-2 producer ran 19.3 min and completed the task (two allowed files at
the accepted base in the retained line, 35 new tests, agent-run
verification 160 OK, two out-of-scope findings reported). Work operation
faulted (agent): adapter's authoritative verification captures not whole
— the agent's killed background full-suite run left ~498 zombies in the
512-PID cgroup (no reaping PID 1), later forks failed. No frozen
proposal/checkpoint/verdict; review blocked; allocation reserved;
cleanup unrun; preserved as found. Evidence + owner decision points in
LIVE-JOB2-OUTCOME-226576.json (salvage / job-3 with PID-hazard
mitigation / attempt disposition). One producer episode spent; no
reviewer episode.
## Review226905 — failed Job2 evidence and retry prerequisites (2026-09-21)

review-2026-09-21T04-50-00Z.md confirms canonical exceptional/faulted Job2,
blocked review, reserved allocation and unended episode. Docker independently
confirms the runtime exited1 without OOM, init unset, PID limit512. Two retained
untracked files and exact log/status hashes are bound in REVIEW-EVIDENCE-226905.json;
these are unreviewed source, not a completed task or accepted candidate.

This explicitly qualifies claim226576's completed-task and single-root-cause
wording: zombie count and160-test success are producer-reported. Verification
stdout contains identifiable nested test-fixture output and sidecars preserve
an earlier failed declaration; exact first failure writer is still open.
Additionally, actual bootstrap tests require a writable external fixture root:
manual success set BATON_V12_STACK_TEST_ROOT, but frozen argv/closed verifier
environment omit it and /var/tmp is read-only. Before a live retry, prove
reaping/capture isolation and the exact verifier environment deterministically.
Fresh Job3 requires supported disposition/pool revalidation for Job2's reserved
allocation and new owner execution selection; no blind repeat of Job1 recovery.
No retry, cleanup, product/test or deployment change by reviewer. Criterion2
remains open; accepted A/B evidence and deadline remain unchanged.

## Owner decision 227095 — bounded deterministic recovery preparation (claim227097 pins this before implementation)

The owner's pass 227095 (2026-09-21T05:05:53Z), verbatim:

> Owner selects bounded deterministic recovery preparation from
> review-2026-09-21T04-50-00Z.md. Pin this decision in FINDING/PLAN before
> implementation. Address process reaping, nested capture isolation, exact
> frozen verifier environment, and supported disposition/pool revalidation
> for Job2's reserved allocation. Preserve failed Jobs, unreviewed source
> bytes, logs and accepted A/B evidence. Return a concrete recovery package
> for independent review and owner execution decision. No live episode,
> restart, resubmission, cleanup or broad test sweep authorized. Existing
> model, execution limits and deadline remain unchanged.

What this selects and what it does not: the four review226905 questions are
to be answered DETERMINISTICALLY (provider-boundary checks and the exact
frozen verification), producing a reviewable package; the owner executes
nothing until after independent review, and this claim runs no live episode,
no restart, no resubmission, no cleanup and no broad sweep. Job1, Job2, the
two retained unreviewed source files, every retained log/sidecar byte and
the accepted A/B evidence are preserved exactly as found. Default model,
one-producer/one-reviewer, 3600 s provider / 900 s verification limits and
the 2026-09-21T09:32:05Z deadline are unchanged.

## Claim227097 — the recovery package: four corrections, each measured

Full account in PROGRESS.md claim227097; the package is
RECOVERY-PACKAGE-227097.md with RECOVERY-IMAGE-227097.json and
VERIFIER-ENV-DEMO-227097.json as its evidence. Nothing live, applied,
restarted, submitted, cleaned or credential-touching ran.

**D9 — the container has NO compliant verifier fixture root at the
accepted base (measured, new).** test_bootstrap's eleven
ValidFixture-derived classes (75 of 125 tests) demand, via
`_disk_root_outside_the_checkout` (which refuses rather than skips), a
root at once disk-backed, writable and OUTSIDE the checkout. By the mount
contract the container offers none: read-only rootfs, memory /tmp and
/dev/shm, and /output IS the git-line checkout. The only in-container
paths that could satisfy the rule are manager-owned delivery mounts — and
writing fixture material there is the contamination class this recovery
removes, which is also the plausible mechanism of the producer's manual
"160 OK" that review226905 already declined to credit. Consequence: the
Job2 frozen gate could never have passed legitimately in-container, PID
exhaustion aside. Bounded correction applied at the task bytes (fixture
root made by the argv itself; the eleven impossible classes excluded by
name with a 51-test floor; full family still gates host reruns); the
COMPLETE in-container fix — a dedicated writable disk-backed fixture
delivery mount — is manager product surface for separate owner selection.

**The reaping correction is the image entry's own PID-1 supervisor**
(worker unchanged one process down; stop contract unchanged), proven by
new deterministic tests and as real PID 1 in the built image under the
composed 512-PID limit. **The capture correction makes the log room an
explicit delivery** (`BATON_ATTEMPT_LOG_ROOM`, set by the entry, provably
absent from both composed child environments; retained sidecars untouched)
— with the residual stated exactly: candidate-sourced old bytes and the
reference worker's `_WorkerCapture` can still reach the writable room
mount by absolute path; the complete fix is a manager-side room-target
change. **The Job2 disposition is revalidated from the product's closed
sets** with four new composed tests: a widened pool is a new generation,
the RESERVED row stays untouched and required from its own generation,
and fresh identities reserve beside it; the W128698 exclusion path now
matches Job2's shape but requires runtime destruction and a checkout
restore that would destroy the preserved unreviewed bytes — recorded, not
recommended. Candidate image sha256:b44f55220e9f… awaits the owner's
selection; the three fail-closed owner command blocks are in the package.
Criterion 2 remains open.
## 2026-09-21T05:39:16Z — owner: immediate investment cutoff

Recorded by baton.prompt from the owner's interactive statement: "the deadline is almost here, and I need to take a break too. IF we don't get this up and running within the nxt few min. I'm going to consider v12 a failed attempt".

The owner now gives only a few more minutes for an operational result before treating v12 as a failed attempt. This supersedes reliance on the previously recorded 09:32:05Z deadline as an available continuation window; no precise replacement instant was supplied and none is invented. A prepared patch, deterministic fixture pass or unreviewed source is not the previously required independently accepted useful live result. No extension is presumed. Preserve incomplete evidence and report the actual outcome honestly. This investment constraint does not authorize a live retry, restart, resubmission, unsafe interruption, claim change or waiver of review. The current recovery-preparation assignment remains bounded by its existing authority.

## Review227324 — recovery package not execution-ready

review-2026-09-21T05-43-00Z.md records three concrete gaps: compose-only owner block omits apply/pin verification; reduced verifier proof uses a stub while real retained pool tests inherit the excluded disk-root fixture; image-only marker leaves the measured candidate-source capture path open. Ten focused reaper/scheduler tests independently pass1.057s, not full package acceptance. Owner05:39:16 immediate investment cutoff supersedes the handoff/package old-deadline claim. No live or deployment action; return actual incomplete result for owner decision. Required acceptance is not waived by test-change authority.

## 2026-09-21T05:53:07Z — owner approves disk-backed scratch mount

Recorded by baton.prompt: owner says "I approve spare mount" in response to the proposal for a writable disk-backed scratch directory/volume per worker attempt, outside the candidate checkout, with each worker seeing only its own directory. One backing disk may serve those isolated directories. Point BATON_V12_STACK_TEST_ROOT at the selected mount and verify the actual required tests against their path and filesystem checks. Retain failed-attempt evidence until disposition; cleanup follows disposition, not an automatic deletion of evidence. /scratch is a suggested mount path, not a frozen spelling.

This selects the direct environment correction for review227324 R2 and supersedes excluding the required tests as the proposed remedy. The exact mount wiring and full real-test proof remain to be prepared and independently reviewed. Approval is recorded, not implemented or deployed here; it does not itself select another live episode or extend the investment deadline. Log isolation and the missing apply/pin command remain unresolved separate items.

## 2026-09-21T05:54:40Z — owner selects disposable nested-test logs

Recorded by baton.prompt: owner says "I agree with own/disposable logs" after the explanation of nested candidate adapters writing into the outer worker's verification room. Each nested test execution must use its own disposable log location, separate from the outer worker's authoritative evidence. The correction must cover candidate-source adapters and reference-worker paths as well as the image adapter. Demonstrate with the affected nested tests that the outer log bytes and capture-status files remain untouched. Preserve existing failed-attempt evidence; disposable new test logs do not authorize cleanup of retained Job2 logs.

This supersedes the image-only marker as a sufficient proposed correction for review227324 R3. Exact implementation remains to be prepared and independently reviewed. No product edit, dispatch, live retry or deadline extension is made by recording this decision.

## 2026-09-21T05:56:02Z — owner selects another bounded Claude correction round

Owner agrees to correcting the missing deployment application/check sequence and instructs: "let's kick these back to Claude for another round". Recorded by baton.prompt. Implement the three selected corrections together: (1) isolated disk-backed scratch mount per attempt, with the actual pool/bootstrap tests and no substitute stub or required-test exclusions; (2) separate disposable nested-test logs, including candidate-source/reference-worker paths, with proof outer evidence remains untouched; (3) a complete compose, supported apply, installed-policy/pin equality check, restart and submit command package that fails closed before restart on any apply/check failure. Prepare and deterministically verify the package; provide commands for owner execution, not an actual live restart/submission in this round.

This explicitly authorizes one further bounded implementation and independent-review round despite the immediate investment cutoff recorded at 05:39:16Z. It supersedes waiting for a continuation decision for this round only; it neither reinstates the older 09:32:05Z window nor invents a new deadline or grants open-ended continuation. Return promptly with the actual result or concrete blocker. Preserve failed Jobs, retained source/log bytes, accepted A/B evidence, default model and existing limits. Reuse accepted focused reaper/scheduler evidence when applicable; no broad sweep, live model episode, deployment restart/resubmission or cleanup is selected.

Implementation owner is baton.claude after successful claim; reviewer is the configured baton.bug route. Claude pins exact product/test path ownership in PLAN before editing; baton.prompt owns only these attributable decision/coordination additions and performs no product implementation. Review must evaluate all three gaps from review-2026-09-21T05-43-00Z.md and return to baton.decide for the owner's execution/investment decision.

## Claim227424 — round 2 complete: scratch delivery, moved room + decoy, full command package

All three owner selections implemented and deterministically proven
(RECOVERY-PACKAGE-227424.md, RECOVERY-EVIDENCE-227424.json; PROGRESS
claim227424 carries the full account).

**R2 closed with the REAL tests:** the per-attempt disk-backed scratch is
provisioned with every assignment home, adopted on the start path, and
mounted writable at the constant `/scratch`; the frozen argv runs the FULL
`test_pool` + `test_bootstrap` (exclusion remedy superseded and removed).
In a container from the rebuilt image, over the accepted base plus the
ACTUAL retained `pool.py`/`test_pool.py` (hash-bound), the exact frozen
argv ran **160 tests OK, exit 0** — where 75 failed without a compliant
root. Demonstration only; the retained line is untouched and nothing is
accepted by it.

**R3 closed for old bytes too:** the authoritative room moved to
`/run/baton/attempt-logs` (one shared constant; manager mount, entry
marker and reference-worker capture all derive from it) and the legacy
spelling is a disposable decoy tmpfs in the unconditional restrictions.
The accepted base's own adapter and reference-worker bytes, driven
in-container through the measured nested path, landed every write in the
decoy while the pre-seeded real room stayed byte-identical.

**R1 closed:** fenced fresh install (runtime rebuilt and recorded:
executable c45ff6d9…, bundle 8616ab85…/81; installer re-fenced and its
BEFORE gate re-run green) → compose job-3 (fresh coder-3/reviewer-3,
corrected task and image d1e2869e…) → SUPPORTED APPLY via
`tools.bootstrap --inputs` → `check-policy-pin.sh <dest> pool` failing
closed BEFORE start → start → submit job-3 only, with a no-secret
credential-registry preflight. Commands only; nothing executed this
claim. The current instance, both failed Jobs and all retained evidence
stay preserved. 1023 focused tests green across the touched suites; 15
real-Docker input-delivery failures measured PRE-EXISTING against
pristine base sources on this host. Criterion 2 remains open pending the
owner's execution decision.

## Claim227653 — job-3 observed: the package worked; the CREDENTIAL is expired

The owner-executed sequence installed, composed, applied, gated, started
and submitted cleanly on instance-2026-09-21T06-27-56Z. The runtime
launched with EVERY round-2 correction live and observed in the real
container: the per-attempt `/scratch` disk bind, the room at
`/run/baton/attempt-logs` (provider streams captured there with clean
`finished` sidecars), and the decoy tmpfs at the legacy path. The
provider then answered in 39 ms: **"Failed to authenticate: OAuth
session expired and could not be refreshed"** (`terminal_reason
api_error`, cost 0) — the operator-file bearer behind
`w64268-run1`/`w202663-development` has expired since Job2 ran at 03:59Z.
The work operation faulted `agent`; implementation exceptional, review
blocked, allocation reserved, episode unended; ~4.5 s of container time
and zero provider spend. This is a credential failure squarely outside
the coordinator, which by design never reads or refreshes that bearer.
Evidence: LIVE-JOB3-OUTCOME-227653.json. Owner decision: refresh the
Claude authentication behind the operator file, then the same reviewed
cadence composes job-4 beside the preserved job-3 (`--job …-job-4
--work 2`; the round-1 scheduler proofs cover reserving beside a reserved
row). Nothing retried, cleaned or resubmitted; everything preserved as
found. Criterion 2 remains open.


## 2026-09-21T06:24:00Z — independent recovery preparation review (baton.rvpc, claim227560)

Review-2026-09-21T06-24-00Z.md (lowercase filename `review-2026-09-21T06-24-00Z.md`) addresses the prior three blockers for the pinned old-source Job3 only; evidence is REVIEW-EVIDENCE-227560.json. Independent 37 tests passed in 1.990s; 110 runtime inputs and executable/bundle identities match. Author 160-test transcript and retained-source hashes checked, not rerun. The log-path move is a compatibility stopgap: nested sources carrying the new constant can still reach outer logs, so this is not general nested isolation and must be revisited before updating that task base. No workaround for that remaining limitation is undertaken. Earlier exclusion/stub remedy remains superseded. Return to baton.decide for the owner investment/execution decision; criterion 2 remains open and no live action is authorized by this review.

## 2026-09-21T06:30:32Z — owner reports Job3 command sequence executed

Recorded by baton.prompt: after requesting and receiving the reviewed RECOVERY-PACKAGE-227424.md install, compose/apply/pin-check and start/submit commands, the owner reports "done". selected-instance.txt currently names /home/sl/baton-v12/instance-2026-09-21T06-27-56Z. This is an owner execution report, not independent confirmation of Job3's runtime or outcome. Observe w202663-first-development-job-3 through supported read-only surfaces, collect the actual candidate, verification, independent verdict and retained logs, and report concrete failures promptly. Do not resubmit, restart, recover automatically, clean up or change model/limits. Preserve previous failed Jobs and A/B evidence. Criterion 2 remains open until a useful result is independently accepted. Canonical W202663 is currently held by baton.slaw; owner pass is required before Claude may claim observation.


## 2026-09-21T06:37:00Z — Job3 authentication failure independently confirmed (baton.rvpc, claim227682)

See review-2026-09-21T06-37-00Z.md and REVIEW-EVIDENCE-227682.json. Status, stopped container, corrected mounts and finished provider captures confirmed. Provider reports expired OAuth/unrefreshable session,39ms, zero usage/cost; no verification or independent review ran. This explicitly qualifies claim227653: exact expiry timing/refresh cause are unproved; successful generation/verification/acceptance were not demonstrated, so “every other layer” and “one working credential away” are not accepted conclusions. Return to owner credential/continuation decision; preserve attempts; criterion2 open.

## 2026-09-21T06:40:26Z — owner relogged; prepare the bounded Job4 recovery commands

Recorded by baton.prompt: owner reports "I relogged" and explicitly says "do it" to preparing Job4 recovery commands for independent review. Read-only registry metadata inspection confirms w64268-run1 and w202663-development both name operator-file /home/sl/.claude/.credentials.json. No credential contents were read; relogin is owner-reported and successful worker authentication is not yet demonstrated.

Select Claude preparation of the exact fail-closed Job4 sequence on the existing instance-2026-09-21T06-27-56Z, preserving failed Job3, its reserved allocation and all prior evidence. Revalidate fresh Job/work/participant identities, supported compose/apply/pin checks and any required stop/start against current state. Reuse the accepted runtime/image and prior evidence unless a concrete mismatch prevents it; avoid reinstall, rebuilding unchanged inputs, broad tests or unrelated product changes. Prepare any necessary new documents and focused deterministic checks, but no live provider call, operational apply, restart, submission, credential mutation or cleanup in this preparation round. Return a concrete reviewed command package for owner execution; do not simply relaunch failed Job3 or claim that relogin proved recovery.

This supersedes awaiting a continuation decision solely for this bounded preparation. Existing model, 3600/900 limits, independent acceptance and old-source log-isolation limits remain; no old deadline window or open-ended continuation is inferred. Pin exact changed paths before edits. Pass to baton.bug with next baton.decide for independent review then owner execution decision.

## Claim227726 — job-4 composed; the mapped credential file is measurably STALE

The bounded preparation is done (JOB4-RECOVERY-227726.md): job-4 composed
with zero refusals beside preserved job-3 (coder-4/reviewer-4, Work
baf2e7fe-W2, input identity fd273ef0…, image d1e2869e… verified in the
composed deployments; submission names job-4 only), against read-only
revalidated current state (generation 1 = job-3's workers, one reserved
allocation, manager running — the reviewed scheduler proofs cover exactly
this widening). **Concrete finding, metadata only:** the operator file
both registry references map to, `/home/sl/.claude/.credentials.json`,
was last modified 2026-09-17T15:29:42Z and nothing under `~/.claude` or
`~/.config/claude*` changed after job-3's 06:30:25Z failure — the
reported relogin did not reach the file the workers mount, and submitting
job-4 now would repeat job-3's authentication failure. The package
therefore opens with a fail-closed metadata-only FRESHNESS GATE (refuses
while the file predates the failure; it refuses today, correctly) and
tells the owner exactly how to satisfy it. The refresh-token-rotation
mechanism consistent with Job2-then-Job3's timeline is recorded as a
HYPOTHESIS, not a proved cause (per review227682's qualification); if it
holds, persisting refreshed credentials between episodes is separate
product surface. Nothing applied, restarted, submitted, called live,
read from or written to any credential, or cleaned this claim; job-3's
attempt and all prior evidence preserved. Criterion 2 remains open.


## 2026-09-21T06:48:00Z — Job4 preparation review (baton.rvpc claim227766)

See review-2026-09-21T06-48-00Z.md and REVIEW-EVIDENCE-227766.json. Composition validates; Job3 workers are unchanged, Job4 identities fresh, only task_id differs. Apply/pin/stop/start/submit sequence is consistent. The credential mtime is confirmed old, but this explicitly supersedes claim227726 certainty that relogin failed, next authentication must deterministically fail, or a newer mtime is technically necessary. Timestamp is diagnostic, not authentication proof; package step1 requires qualification or explicit owner selection as a conservative rule. Rotation and reliable-first-episode claims are unproved. Return to baton.decide; no live act or further correction round inferred.

## 2026-09-21T06:49:52Z — owner reports reviewed Job4 sequence executed

Recorded by baton.prompt. Owner clarified the first relogin used CLAUDE_CONFIG_DIR=/home/sl/.local/state/acp-baton-bridge/baton.claude/claude, a different source from the worker's /home/sl/.claude/.credentials.json. After the owner reported another relogin, metadata-only stat showed the worker file updated at 2026-09-21T06:48:30.575959561Z. No secret contents were read and this timestamp was presented only as evidence of file update, not successful authentication or a mandatory authentication gate.

Owner now reports "done" after receiving the reviewed apply/pin-check and stop/start/Job4-submit blocks from JOB4-RECOVERY-227726.md, with the timestamp gate omitted as required by the review qualification. Treat execution as owner-reported until supported current state confirms it. Observe w202663-first-development-job-4 on instance-2026-09-21T06-27-56Z (authority baf2e7fe4ec04612aa9d28805cafea78), through actual provider outcome, verification, independent review and retained result evidence. Report concrete failures promptly. Preserve Job1/2/3 and all source/log/A-B evidence. No resubmission, restart, automatic recovery, credential mutation, cleanup or new implementation authorized by this observation handoff. Default model, existing 3600/900 limits, one producer/reviewer and report-and-hold remain. Criterion2 remains open; successful submission is not accepted useful output.

## D10 (claim227806) — the real repository cannot pass the line-candidate revalidation walk

Job-4 authenticated (the owner's second relogin reached the correct
file), ran a FULL real producer episode — 74 turns, ~13.7 min, $7.37,
clean completion summary, the two-file candidate present in its line at
exactly the accepted base, `/scratch` used live, provider streams
captured in the moved room with `finished` sidecars, zero contamination —
and then the work operation FAULTED (`agent`) with NO verification
captures at all, which places the fault at `claude_agent.work()`'s
post-provider `_checked_tree(candidate, …)`, before `_verify`.

**Deterministically reproduced outside the container** against the
retained job-4 line checkout with the exact composed skip set:

1. `the candidate line carries a link at
   work/open/finding-protocol-11-reference-semantics` — the repository
   COMMITS symlinks (`work/open/finding-*`), and the walk refuses any
   link at any depth;
2. with links tolerated, the same walk meets **19,553 entries /
   652,339,071 bytes** against `MAX_SOURCE_ENTRIES=2000` /
   `MAX_SOURCE_BYTES=64 MiB`.

The accepted A/B jobs never met this because their nominated source was
the SMALL w197661 fixture repository; job-2/3/4 are the first line
candidates whose checkout is the real baton repository. Hypothesis only
(consistent with review226905's "exact first failed writer unproved"):
Job2's image carried the same walk over the same shape, so its fault may
have been THIS refusal too, with all of its verification.* artifacts
being nested contamination rather than adapter captures.

Bounded correction for owner selection (not implemented under this
observation handoff): for the LINE profile, hold the provider to its
CHANGES — the committed checkout is manager-delivered line custody
already proven at materialization, so the link/type/bounds rules should
walk the changed/pending set and what publication actually copies, not
the whole repository. Raising bounds/skipping committed links instead
would weaken every profile and is not recommended.


## 2026-09-21T07:13:00Z — independent D10 review (baton.rvpc claim227929)

See review-2026-09-21T07-13-00Z.md and REVIEW-EVIDENCE-227929.json. Provider completed74 turns/$7.370573, but Job4 faulted with no verification/candidate acceptance. Reproduced _checked_tree refusal on committed link in0.001574s; independent non-following inventory confirms19553 entries/652339071 bytes/102 links. This qualifies D10 localization: generic live fault and absent verifier logs are consistent with the reproduced first check, not a captured exact exception. The correction proposal must also address _measured/_revalidated/_representable/publication whole-tree assumptions and preserve ignored-addition and no-follow/byte/set protections; merely restricting to Git diff is insufficient. No implementation selected by this review. Return owner decision; preserve all attempts; criterion2 open.

## 2026-09-21T12:41:22Z — owner selects bounded D10 correction and deterministic publication proof

Recorded by baton.prompt: owner says "lets contintue for now" after the explicit choice between authorizing the deterministic collection/publication fix and stopping. Select implementation and independent review of D10: make the line-profile candidate validation/publication path support the real repository baseline with committed symlinks and size above candidate-payload limits while retaining protections on provider-authored changes. Revalidate review-2026-09-21T07-13-00Z.md against current code, pin exact source/test ownership before editing, and address the full chain (_checked_tree, _measured, _revalidated, _representable and publication), not just the first refusal. Git diff alone is not a complete filesystem-change inventory.

Preserve anchored no-follow reads, checks on added/replaced links and special files, ignored additions, reserved paths, changed-payload byte/entry limits, bounded discovery, HEAD stability, legitimate deletions/renames, and post-verification byte/set integrity. Keep copy-profile behavior intact. Demonstrate a focused deterministic fake-provider flow through actual verification and publication with a representative baseline, plus the relevant negative cases; no paid model rerun is needed to prove this correction. Reuse applicable earlier evidence and avoid broad suites. Preserve Jobs1-4 and their retained source/log bytes; no adoption of unreviewed output as accepted code.

This explicitly supersedes waiting for a correction/investment decision for this bounded continuation despite the elapsed cutoff; it does not retroactively declare the cutoff met, set a new deadline, or grant open-ended investment. Return the corrected candidate, focused proof and concrete operational next steps through baton.bug independent review to baton.decide. No actual installation, operational apply, restart, new Job submission, live provider episode, credential mutation or cleanup is selected by this continuation. Existing model/limits and independently accepted useful-result criterion remain.

## Claim230107 — collection narrowed to the owner's 12:47:17Z selection; review230027 R1/R2 closed

The whole-baseline regime is GONE, not re-thresholded (design pinned in
PLAN 13:11Z before the affected edits; D10-EVIDENCE-230107.json): the
line profile's inventory is Git's own status listing — no baseline tree
read, no whole-tree hashing, no repository-wide ceilings, no mode
policing — with the payload ceilings applying to exactly the changed
set and one collection bound on the listing itself. An unrelated
ignored file is STRUCTURALLY not a veto (it never enters the
inventory); ignored and special exclusions are DISCLOSED to the human
integrator in a new `collection` result member, with the
relied-upon-by-verification question put in the record rather than
adjudicated. The retained vetoes are exactly the ruling's: a link among
the CHANGES (no-follow/external-file protection), and
verified-to-delivered byte/set integrity (revalidation, both-direction
set equalities, `_identical_bytes`, committed-mode proofs, type changes
refused). The superseded whole-tree guarantees (ignored-addition veto,
assume-unchanged catching) are retired BY NAME in the two rewritten
tests, which now assert the narrow truths that remain. Copy profile
byte-untouched.

Proven: 221/221 in the owned suite, including review230027's own R1
probe rewritten as the positive it must be (unrelated ignored cache +
constant harness → publishes, disclosed), the verification-relied
ignored dependency (publishes, disclosed, provably undelivered), the
representative real-shape baseline, and the narrow negative set.
Closure: the narrowed inventory answers the RETAINED job-4 checkout in
0.066 s with exactly the two candidate files at review227929's recorded
hashes. R2: D10-EVIDENCE-230107.json is valid JSON (the 229926 artifact
stays as history), and JOB5-PACKAGE-230107.md is one explicit
fail-closed compose/apply/pin/stop/start/submit sequence with exact
instance, authority, job-5/W3 and incarnation operands — no
placeholders. Candidate image sha256:5c2eb55d… (gates green), pinned in
the composer. Nothing live, applied, restarted, submitted,
credential-touched or cleaned; Jobs 1–4 preserved. Criterion 2 open.

## Claim229926 — D10 corrected across the whole chain, proven, and closed against the retained checkout

The line profile's subject is the DELTA now (D10-EVIDENCE-229926.json;
scope pinned in PLAN 12:43Z before editing; copy profile byte-untouched):
a new baseline inventory at the pinned entry head, a git-blind anchored
no-follow walk that passes byte-identical blobs and exactly-committed
links (file and directory) as baseline and holds everything else to every
unchanged provider rule — payload ceilings over the changed set, new
discovery ceilings over the walk itself, link/special-file refusals by
name, deletions as their own honest set — with revalidation re-proving
the delta after the provider-authored verification and `_identical`
keeping every rule plus delta-scoped representability (the
ignored-addition refusal exactly where it was) and committed-mode proofs
for every measured path. `_measured` is retired with the whole-tree
assumption; `_publish_line` needed nothing.

Proven: 220/220 in the owned suite — 14 new deterministic fake-provider
cases through the REAL work(), including a baseline committing links and
sitting past BOTH payload bounds that publishes a small patch through
actual verification and publication, and the negative set the review
required. Closed against the live evidence: the corrected adapter's own
inventory over the RETAINED job-4 checkout answers in 0.836 s with
exactly the two candidate files at the reviewer's independently recorded
hashes and no deletions — the exact live refusal is gone. Candidate
image sha256:d447cf38… (gate 16 OK, in-image byte identity), pinned in
the composer; the HOST runtime is unchanged by D10, so the operational
next step needs no reinstall: compose job-5 beside the preserved jobs,
apply + pin gate, restart, submit (exact commands in the evidence file,
for after independent review and the owner's decision). Nothing live,
applied, restarted, submitted, credential-touched or cleaned; Jobs 1–4
and all retained bytes preserved; the retained candidate files remain
unreviewed evidence, not adopted code. Criterion 2 remains open.

## 2026-09-21T12:47:17Z — owner simplifies line-profile collection; human is integrator

Recorded by baton.prompt. Owner questioned disabling the checker because the owner is the integrator, then said "proceed" to removing whole-checkout rejection for the line workflow while retaining safe collection and accurate evidence. Selected behavior: collect the proposed changes and verification evidence for human acceptance; do not reject the proposal merely because the existing checkout has committed symlinks or exceeds whole-tree payload limits. Remove that whole-checkout rejection gate rather than redesigning it as a comprehensive repository-policing system.

Keep the narrow handoff requirements: do not follow output symlinks into files outside the workspace when collecting; ensure delivered changes match the bytes/set actually verified; report failed verification or incomplete collection honestly. Capture a faithful proposal including relevant additions/deletions/renames, without treating code quality or every unrelated checkout entry as a collection veto. Ignored or unrelated files are not an automatic reason to reject the entire line; distinguish files actually delivered or relied upon by verification and disclose material collection limitations. Existing operational resource limits still apply to actual collection, not as a ban on the size of the pre-existing repository. Human acceptance remains explicit. This is not permission to expose credential/external files, fabricate success, mutate Git history or accept unreviewed code.

This supersedes the 12:41:22Z requirement to preserve the broad whole-tree/ignored-addition rejection regime for the line profile and narrows the corresponding review227929 correction recommendations. Keep copy-profile behavior outside this bounded change. Retain a focused fake-provider proof through verification and publication on a representative real-repository shape, plus narrow no-follow and verified/delivered-content integrity cases; avoid expanding the correction into general hardening. Current claimant baton.claude must acknowledge/revalidate this ruling and update its implementation plan before further affected edits; preserve partial work and ownership, no claim/route transfer is performed by this record. Independent review uses this newest accepted behavior, then returns to owner. Prior no-live/deployment/retry/cleanup boundaries remain.


## 2026-09-21T13:01:00Z — D10 review against newest owner scope (baton.rvpc claim230027)

Changes required; see review-2026-09-21T13-01-00Z.md and REVIEW-EVIDENCE-230027.json. Owner12:47:17Z supersedes broad checker preservation, but current candidate still rejects unrelated ignored material and polices whole-baseline discovery. Independent fake-provider probe reproduces unrelated-cache veto in0.021s; all14 new focused cases pass6.153s under their current expectations, which does not satisfy the superseding behavior. D10-EVIDENCE-229926.json is invalid JSON and next-step commands retain placeholders/prior-block substitution. Candidate/image not approved; return baton.decide. No product/live/deployment action; preserve evidence; criterion2 open.

## 2026-09-21T13:01:56Z — owner reaffirms no hardening; align the correction handoff

Owner objects that unrequested checks/processes keep denying release, then requests "job is with us, review, align it and send me the cmds". Recorded by baton.prompt as interactive decision alignment, not independent candidate review. The 12:47:17Z behavior remains controlling. Complete the already-selected simplification rather than seeking another product decision: remove whole-checkout policing and unrelated ignored-file vetoes for the human-integrated line workflow. Do not replace them with larger whole-tree ceilings, an automatic verification-dependency analysis system, or another general hardening gate. Collect the actual proposal safely, identify the verification performed and its material limitations, preserve verified/delivered content integrity and report failures honestly. Human integration decides acceptance.

Exact bounded correction handoff: OWNER-HANDOFF-D10-SIMPLIFY-20260921T130156Z.md in this dossier. Scope is the existing behavioral mismatch and concrete evidence/command defects in review230027, followed by focused independent review. No broad hardening, live execution or deployment action is selected. This supersedes interpreting the prior return-to-owner disposition as requiring another approval of the same behavior. Prompt prepares the owner command to route unclaimed Work; no workflow mutation by this entry.


## 2026-09-21T13:24:00Z — narrowed D10 preparation approved (baton.rvpc claim230179)

review-2026-09-21T13-24-00Z.md and REVIEW-EVIDENCE-230179.json address prior R1/R2 under latest owner narrow scope.15 focused tests pass5.412s; retained Job4 inventory matches both prior hashes in0.067726s. Replacement evidence parses and explicit Job5 package has correct operands. Candidate image5c2eb55d and adapter5c216c03 bound in review. Preparation approved for owner selection, not live success or retained-output acceptance. Status/disclosure limits and prior old-source log limitation remain explicit. Return baton.decide; no operational action; criterion2 open.

## Claim230245 — JOB-5 COMPLETED WITH INDEPENDENT ACCEPTANCE (observed to terminal)

The first complete real Claude Job on this Work, observed read-only from
submission to its report-and-hold terminal (LIVE-JOB5-OUTCOME-230245.json):
the producer (61 turns, ~11.5 min, $5.79) wrote the bounded task's two
files; the EXACT corrected frozen verification — full test_pool +
test_bootstrap with the delivered /scratch — exited 0 IN-CONTAINER for
the first time; the narrowed collection published a clean two-file
candidate (head a12759d2 over the accepted base, disclosure null); the
FIRST real Claude reviewer episode (27 turns, ~3.6 min, $1.82) ran and
its durable report opens "VERDICT: accepted", verified against the tree;
the checkpoint froze and the LINE state is ACCEPTED through the public
readers; both stages completed with every allocation released
cleanup-retained, canonical. One non-blocking defect and the known
admission-does-not-route limitation are recorded in the findings. Every
corrected layer held live: credential, scratch, moved room with finished
sidecars, reaping, narrowed collection, and scheduling beside two
preserved reserved rows. Job-5 spend $7.61 total. Jobs 1–4 untouched.
Criterion 2's independent acceptance now EXISTS, durably frozen and held
for the owner's explicit integration — the owner's acceptance decision is
the remaining act.

## 2026-09-21T13:29:56Z — owner reports Job5 execution sequence completed

Recorded by baton.prompt: owner reports "completed" after receiving the reviewed Job5 compose/apply/pin-check/stop/start/submit sequence. This selects the reviewed image for the reported run; it is not a report of completed coding or acceptance. Confirm current supported state for w202663-first-development-job-5, Work baf2e7fe-W3, on instance-2026-09-21T06-27-56Z. Claude observes the actual provider, verification, publication and independent review outcomes, retains exact artifacts/log evidence and reports concrete failures promptly. Pass observation evidence to baton.bug with next baton.decide. No new implementation, restart, resubmission, automatic recovery, credential mutation or cleanup. Preserve Jobs1-4 and their evidence. Existing one producer/reviewer, default model,3600/900 limits and report-and-hold remain. Narrow collection/disclosure and old-source log-isolation limitations remain as reviewed; criterion2 is not met until useful output is independently accepted.


## 2026-09-21T13:56:00Z — Job5 independently confirmed accepted (baton.rvpc claim230381)

See review-2026-09-21T13-56-00Z.md and REVIEW-EVIDENCE-230381.json. Public readers confirm accepted line, frozen checkpoint rev1 at a12759d2, ended distinct-reviewer attachment, completed stages/released allocations. Four artifact hashes match. Captured producer verification158 tests OK19.101s; reviewer report accepted with separate tests and one non-blocking diagnostic defect. Provider total$7.609709 confirmed. Owner handback includes exact proposal/bundle/report locators and digests, pool_generation deviation and admission-does-not-route limitation. No integration/closure performed; return owner decision. Null disclosure is not exhaustive proof and snapshot episode-ending fields remain null. No operational or candidate mutation.
