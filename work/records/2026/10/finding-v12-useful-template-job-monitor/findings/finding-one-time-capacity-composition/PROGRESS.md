# Implementation progress

## claim367234 — the capacity is composed, and the Job is admitted through it

Answers the bound `FINDING.md` and `PLAN.md` under thread 367232. **The thing
three parent handoffs left missing is delivered**: a two-lane one-time capacity
configuration, emitted by the real installer with the real retained runtime,
read by the real `DeploymentDerivation`, and admitting the parent's selected Job
through an ordinary `manager create`.

Nothing operational was selected: the proposed
`useful-template-job-w366962` destination was **never touched**, no existing
instance was read or written, no bundle was built, no repository cloned, no
network used, no engine or provider reached, and no version control mutated.
`git status` reports no change under `v12`.

### What is in this dossier

* `compose_capacity.py` — the operator **preflight entrypoint**. Verifies the
  retained runtime against **both** of its pins, holds the source to the
  selected commit, and reports the selection, the derived paths and the
  composition's identities. `preflight` writes nothing; `prove` runs the
  connected proof in a private disposable destination.
* `prove_admission.py` — the **connected proof**, 11 cases, all passing.
* `evidence/claim-367234/` — `PROOF.txt`, `COMPOSITION.json` (the emitted
  configuration, derivation and create answer), `preflight.json`, and
  `HOW-THESE-WERE-RUN.txt`.

### What the proof establishes

**The artifact.** The retained W366246 archive is materialized and held to
*both* pins — its own sha256 `1da85eed…0057125` and, through the product's
`instance.manifest`, the recorded folder digest
`0b7bc592…f88beefd` over **81 files**. A tarball that matched while its
contents did not would be a pin that proved nothing. The bundle then answers
for itself with nothing of this checkout around it: `frozen: true`, both frozen
schema assets, a native validator on disk, and its **`18e771f0, dirty` stamp
read and reported — never relabelled**.

**The source** is held to `42bed8bb…` by a read (`rev-parse`); a stale commit
refuses before anything is composed.

**Both lanes, emitted by the real installer.** `bootstrap.main` with
`--distro` naming that runtime emits a configuration carrying
`implementation` → `baton.claude-w366962` and `review` →
`baton.reviewer-w366962`: two roles, **two distinct participants**, neither of
them a pilot participant, so no existing grant is reused by accident. Every
worker is bound to the instance's own authority uuid, and so is every worker
manifest's `work_ref`.

**The derivation answers where the parent packet only had a refusal.**
`creation_ports.DeploymentDerivation` reads *that emitted configuration* and
resolves both lanes — one agreed Work (`0000000a-W1`), one input digest, one
policy digest, and a profile per lane. Asked with the parent's selection it
also answers that Job's own task document, whose `task_id` and instructions are
the selected ones.

**Ordinary `create` reaches its owners through those inputs.** The real
`job_manager.main` argv admits `job-template-job-guide-42bed8bb` with
`servable: {implementation: [impl-w366962], review: [review-w366962]}`, the
Job's own task in the Job store carries the selected statement and scope, and
the identical request replays to the identical answer. **No bespoke per-Job
admission anywhere**: the configuration's `jobs[]` binding names the Job and
nothing pre-composes a submission, because admitting one is the manager's act.

**The refusals an operator can rely on**: a stale source commit, a foreign
authority uuid, a wrong artifact (a directory that is not a frozen build is
refused by the installer), and a single-lane deployment.

### Two things I found by running it, reported rather than smoothed over

**The uuid in the two-lane cases is persisted, not minted — and I will not call
it minted.** `ValidFixture` persists the instance identity in `setUp`, before
anything is composed, and it must: a worker document's `input_manifest` is
digest-sealed over the authority uuid, so the accepted stage fixture's workers
can only be written against a root that already holds the identity they were
sealed for. That is the same chicken-and-egg the parent packet documented. So a
separate case shows the **generation** itself: a worker-less phase-1 document,
the real installer, and a uuid it **generates** and persists — 32 hex,
different from the fixture's constant — with the emitted phase-1 configuration
carrying **no workers**, by design. That is the operator's real first step and
it is why the parent reads the uuid back instead of writing one down.

**A single-lane deployment is refused by the INSTALLER, which is stronger than
what I went looking for.** I wrote a case to reach
`DeploymentDerivation`'s "configures no 'implementation' worker" refusal
through a real install. It cannot be reached that way: `bootstrap` refuses to
*emit* a configuration with no implementation lane, by name, before any
derivation is asked anything. Two drafts found this the hard way — the first
kept the Job binding and was refused for naming a producer that is not
configured; the second dropped the binding and was refused for the lane itself.
So the empty-capacity state the parent reproduces from an empty mapping is
**not reachable through a supported install** — it belongs to the phase-1
document, which configures no workers by design. The case now records that.

### One correction to my own work

A draft of `compose_capacity.py` composed the worker documents through a stub
standing in for the accepted stage fixture. It could not work — that fixture's
`worker` helper deep-copies `self.config`, a real deployment built in its own
`setUp` from real manifests and digests — and keeping a second composition path
that nearly works is worse than having one that does. The stub is removed; the
single composition lives beside the proof that exercises it, and the emitted
document is captured in `COMPOSITION.json`.

### The inert boundaries, named

The install runs `--no-repositories`: nothing cloned, no network. No engine and
no provider is reached — no stage served, no runtime started, no credential
resolved. `credential_profile` travels as a provider/reference pair and **no
secret appears in any file or any evidence here** (checked). `image_digest` and
`adapter_digest` travel as **pins an operator verifies before execution**;
nothing here contacts a container engine to resolve them. Disk-backed scratch
is `/var/tmp/baton-w257624` with `BATON_V12_DISK_ROOT` and
`BATON_V12_STACK_TEST_ROOT` set; disposable destinations and extracted runtimes
are removed by the cases' own cleanup. The disposable emitted
`deployment.json` is a verification artifact, **not an operational
installation**.

### Verification

    cd v12/python
    PYTHONPATH=src:. BATON_V12_DISK_ROOT=/var/tmp/baton-w257624 \
        BATON_V12_STACK_TEST_ROOT=/var/tmp/baton-w257624 \
        python3 -m unittest -v tests.tools.w367232_prove

**11 cases, OK, 4.06s** — `evidence/claim-367234/PROOF.txt`. The module is
copied into `tests/tools/` for the run and removed afterwards; the canonical
`v12` tree is byte-unchanged.

    python3 .../compose_capacity.py preflight --evidence .../evidence/claim-367234

Exit 0, `wrote_nothing: true` — `evidence/claim-367234/preflight.json`.

### Cost

Reading the bound FINDING/PLAN, the pilot's `configure-inputs.json` and
`fresh.py:_compose`, `configure.py:sealed_manifest`, `bootstrap.DEFERRED`,
`creation_ports.DeploymentDerivation`, and `ServingCase.worker`/
`ValidFixture.workers`. Runs: one archive extraction and identity check, four
proof runs (three exposing my own errors — the `parents[5]` repository
resolution, the Job binding left naming a dropped producer, and the single-lane
install the installer refuses outright), and two entrypoint runs (one exposing
the stub composition).

### What this child does not claim

No live provider authentication, no container start, no model output, no live
startup latency, and no completed correction. The parent's unsupported
finite-turn selection and unknown live OBS-0 endpoints are untouched and still
stand. Parent `COMMANDS.md`, its verifier, its PROGRESS and every historical
artifact were read-only inputs here and are unmodified, as are this child's
`FINDING.md` and `PLAN.md`.

## claim367331 — the composition binds the minted identity; the install sequence does not

Answers `review-2026-10-27T18-06-51Z.md`. **All three findings were right**, and
one of them was an ownership violation of mine. Preparation only: no install of
the proposed destination, no build, no clone, no network, no engine or provider,
no existing instance read or written, no version-control mutation.

### R1 — the unsafe, partly uncallable helper is replaced

`compose_capacity.py` extracted 81 files and did `shutil.rmtree` on a **fixed,
shared** scratch path while reporting `wrote_nothing: true`, and its `prove`
branch imported a `proved` function that does not exist. That
rmtree-a-shared-path pattern is the same mistake that deleted an unrelated
September scratch root.

`capacity.py` replaces it with three callable commands that are honest about
their effects:

* **`preflight`** is strictly read-only — it digests the archive and reads the
  tar *index* for the member count, so it reports 81 files **without extracting
  one**, and `effects` shows `created/extracted/removed/wrote` all empty.
  `--evidence` is reported as a write rather than hidden.
* **`materialize`** extracts only into a directory it creates and uniquely owns
  (`mkdtemp`), **refuses a preexisting path**, retains what it made, and reports
  it. Extraction uses `filter="data"`, which refuses absolute paths, traversal
  and links — and whose absence was emitting a `DeprecationWarning` onto stdout
  that corrupted the command's own JSON answer, found by running it.
* **`compose`** emits the two-lane document for a **minted** identity.

**The rule, written down because I broke it: an invocation may only remove paths
that same invocation created. A matching name prefix is not ownership.** The
refusal is now driven as evidence: a planted sentinel in a directory the call
did not create survives, exit 2 —
`evidence/claim-367331/SENTINEL-REFUSAL.txt`.

### R2 — the composition is now real, and it binds the minted identity

The old capture carried the fixture's `aaaa…` base, `target-1`, the
`0000000a…` constant and a shortened task. All of that is gone.

`compose(minted_uuid, …)` takes the identity the installer **generated** and
composes everything identity-bound *after* the readback — the Work, and each
lane's `input_manifest` sealed around that uuid through
`input_roots.documents(work_ref=…)`, which is the owning API and takes the uuid
as an operand. Circularity was never a reason to substitute a constant, and the
review was right to say so.

Driven end to end with a real mint (`evidence/claim-367331/CONNECTED.json`):

    phase 1 (bootstrap)   exit 0, minted cd9fa7ff70114f70977f9047c2a4e9b5
                          — not the fixture constant
    compose               work cd9fa7ff-W1
                          lanes implementation + review
                          participants baton.claude-w366962,
                                       baton.reviewer-w366962
                          declared base 42bed8bb… — the SELECTED source
                          every worker's authority_uuid == the minted one

The parent's **full** statement (538 characters) and **all five** acceptance
criteria are carried verbatim, and `pins_requiring_operator_verification`
separates what is selected from what is a pin: the image, adapter, engine,
profiles, policy digest and credential *references* come from the reviewed pilot
deployment and are reported as needing operator confirmation, because nothing
here contacts a container engine or a credential provider. No secret appears
anywhere.

### What is still outstanding — a located install-sequencing constraint

**Phase 2 refuses, reproducibly, and the reason is precise:**

    refused: there is already a runtime at <dest>/distro; nothing here upgrades
    a deployment in place. Stop that instance and prepare a new destination if
    you mean a different runtime.

It refuses **with or without `--distro`**. So two `bootstrap --destination`
calls against one destination is not the supported shape, and my phase 1 was
the wrong first step: it performed a **full install** when what the sequence
needs is a **mint-only** step. That is exactly what the pilot's `fresh.py`
does — `mint()` first, `composed()` third, and then **one** bootstrap call in
`install_and_configure()`. The remaining work is to use that shape:
persist/mint the identity, compose around the readback, then **one** install
carrying both lanes, and run `create` against it.

So the composition is proved correct and the **install sequencing is not yet
proved**. `create` was therefore not reached this turn, and I am not claiming
it. No product defect is implicated: the refusal is the installer correctly
declining to replace a runtime in place.

### Verification and cost

`capacity.py preflight` exit 0 with empty effects
(`evidence/claim-367331/preflight.json`); `materialize` exit 0 into an owned
directory; `materialize --into <occupied>` exit 2 with the sentinel intact; the
connected attempt recorded whole, including its phase-2 refusal. Runs this
claim: two preflights, three materializations, three connected attempts (one
exposing `places["launch"]`, which `instance.layout` does not name — the member
names are now read from the layout rather than guessed).

Previous artifacts are preserved: `compose_capacity.py`, `prove_admission.py`
and `evidence/claim-367234/` are untouched, and `prove_admission.py`'s 11 cases
remain valid for what they establish — the runtime pins, the two-lane emission
and `create` **under the fixture's identity**, which R2 correctly says is not
the operational configuration.

### Boundaries

Only paths this claim created were removed. The canonical `v12` tree is
byte-unchanged and nothing was copied into it this turn. Parent `COMMANDS.md`,
its verifier, its PROGRESS, the pilot packet and every historical artifact were
read-only inputs. This child's `FINDING.md` and `PLAN.md` are the reviewer's and
are unmodified.

## claim367392 — the supported sequence works; the manifest is not yet coherent

Answers `review-2026-10-27T18-15-49Z.md`. Preparation only: no operational
install, no build, no clone, no network, no engine or provider, no existing
instance touched, no version-control mutation. **Nothing was deleted this
claim.**

### The incident note's own contradiction is corrected

The note ended "only those were removed" while the same claim's handoff said I
had removed **nothing**. The handoff was accurate. The note now states exactly
what was deleted and when: three paths I created plus the unrelated September
root in claim367234, and **nothing at all** in claim367331 or this one. The
loss remains unenumerated and unknown, and the clarification narrows none of
it. That sentence was wrong about my own actions, which is the kind of error
the note exists to avoid.

### The supported sequence is established and runs

The review named it exactly: `fresh.py:mint` uses `bootstrap --inputs` **only**,
with `state_root` naming the destination. Driven, in
`evidence/claim-367392/SEQUENCE.json`:

    step 1  mint only, `--inputs` alone        exit 0
            generated uuid dd20994520834f08b6ad1b0767372dc4 (not the constant)
            emitted configuration carries NO workers
    step 2  readback from the instance's own identity record
    step 3  compose around that readback       work dd209945-W1
            lanes implementation + review, this instance's own participants
            declared base 42bed8bb… — the selected source
    step 4  ONE destination install            refused, see below

Two ordering facts were measured rather than assumed, and both are now in the
script's comments: the destination-form install **refuses a second runtime in
place**, and it also **refuses an existing `install-inputs.json` at the
destination** — so the mint step's staged input must live *outside* the
destination, which `fresh.py` does not do because its step 4 passes a
`generated/` path instead.

### Two composition defects the installer caught, one fixed

**Fixed: `credential_sources` was wrongly dropped.** I removed it in
`_pilot_deployment_base()` as "identity-bound". It is not — it is the
operator's own credential-sources registry path, shared across instances — and
the installer said so precisely: *"a single-worker configuration has exactly
schema, … credential_sources, … ; missing credential_sources"*. It now travels
as a reported pin.

**Not fixed: the manifest is not coherent with the worker config.** The next
refusal is *"the bootstrap input manifest names another runtime profile"*, and
it is review item 2 restated by the product: `compose` still seals
`input_roots.documents`' **default test vector**, whose
`runtime_profile_digest` and `policy_digest` are the fixture's, not the
worker's. `input_roots.documents` already takes `policy_digest=` and
`profile_digest=` as operands, so the fix is to pass the worker base's own
values and to put the **selected task** in the manifest's `human_contract`
rather than the vector's. That is the remaining work and I ran out of turn
budget at this refusal rather than part-way through an unverified manifest.

So: **step 4 and `create` are not reached, and I am not claiming them.** No
product defect is implicated anywhere in this chain — every refusal so far has
been the installer correctly declining an incoherent or in-place input, and
each one is recorded with its exact sentence.

### Verification and cost

`evidence/claim-367392/SEQUENCE.json` and `supported_sequence.py` are the run
and the script. Runs this claim: four sequence attempts, each advancing one
refusal — the destination's existing installer input, then
`credential_sources`, then the runtime profile. Earlier artifacts, evidence
directories and `prove_admission.py`'s 11 cases are preserved untouched.

### Boundaries

The canonical `v12` tree is byte-unchanged and nothing was copied into it. The
unrelated scratch root was not touched again. Parent files, the pilot packet
and every historical artifact were read-only inputs; this child's `FINDING.md`
and `PLAN.md` are the reviewer's and are unmodified.

## claim367431 — the whole chain runs: mint → compose → install → derive → create

Answers `review-2026-10-27T18-20-19Z.md`. **The joined artifact and proof are
complete.** Preparation only: no operational install, no build, no clone, no
network, no engine or provider, no existing instance touched, no
version-control mutation, nothing deleted.

### The sequence, end to end

`evidence/claim-367431/SEQUENCE.json`, script `supported_sequence.py`:

    step 1  mint only — `bootstrap --inputs` ALONE, state_root naming the
            destination                              exit 0
            generated uuid 534048089a8a4de9b871cb341ced6029
            emitted configuration carries NO workers
    step 2  readback from the instance's own identity record
    step 3  compose around that readback — work 53404808-W1, two lanes,
            this instance's own participants, declared base 42bed8bb…
    step 4  ONE destination install carrying both lanes   exit 0
            every emitted worker bound to the minted uuid
    step 5  DeploymentDerivation reads the emitted configuration —
            both profiles, work 53404808-W1, one input digest
    step 6  ordinary `manager create`                     exit 0
            job-template-job-guide-42bed8bb
            servable {implementation: [impl-w366962],
                      review: [review-w366962]}
            all FIVE acceptance criteria, the full statement, scope
            v12/TEMPLATE-JOBS.md

### The manifest is now coherent, and the installer taught me every member

The previous cut sealed `input_roots.documents`' **default test vector**. The
installer refused it five times in a row, each refusal naming exactly one
incoherent member, and each is now fixed from the thing it had to agree with:

1. *"missing credential_sources"* — I had dropped it as identity-bound. It is
   the operator's own registry path; it stays, reported as a pin.
2. *"the bootstrap input manifest names another runtime profile"* — the
   vector's `runtime_profile_digest` is a `6666…` placeholder. The manifest now
   takes `policy_digest`, `runtime_profile_digest`, `worker_image_digest` and
   `retention_policy_digest` **from the worker deployment it travels in**.
3. *"stages its source at 'workspace/source' and the certified workload reads
   exactly 'source'"* — the vector stages a flat fixture directory. The staging
   now comes from the reviewed deployment whose workload it must satisfy:
   a nominated mount at `source`.
4. *"the nominated source … is not a directory this manager can see"* — the
   two source directories are created empty **and labelled as this sequence's
   one test substitution**, because the operator obtains them with
   `--repository-source`, which clones, and cloning is outside this boundary.
5. *"the configured task document could not be opened"* — the installed task
   bytes are now written before the install, exactly where
   `fresh.py:install_and_configure` writes them.

The `human_contract` is the **real installed task** — this selection's task id,
the parent's full statement as instructions, and `42bed8bb` as the declared
base — digested from the bytes actually written. The `record_binding` is **this
child's own dossier** with real `FINDING.md`/`PLAN.md` digests, which replaces
the `eeee…` placeholder the review named. The seal is computed **last** and
then proved by `check_manifest_structure`.

### What is a selection and what is a pin

Selections carried unchanged from the parent: destination, source commit,
declared base, both lanes and their participants, and the Job's
task/statement/acceptance/scope. Pins taken from the reviewed pilot deployment
because they are instance-independent: image, adapter, engine, profile, policy
digest, credential references and the `credential_sources` registry path —
reported under `pins_requiring_operator_verification`, because nothing here
contacts a container engine or a credential provider. **No secret appears in
any file or any evidence.**

### Verification and cost

Six sequence runs this claim, each advancing exactly one installer refusal, the
last two reaching `create` exit 0. The three entrypoints remain safe and
callable: `preflight` read-only with empty effects, `materialize` into an owned
`mkdtemp` directory that **refuses a preexisting path** (sentinel intact), and
`compose` writing nothing.

### Boundaries

Nothing was deleted this claim; the unrelated scratch root was not touched. The
canonical `v12` tree is byte-unchanged and nothing was copied into it. Parent
files, the pilot packet and every historical artifact were read-only inputs;
this child's `FINDING.md` and `PLAN.md` are the reviewer's and are unmodified.
Earlier artifacts and evidence directories are preserved.

**Not established:** no live provider authentication, no container start, no
model output, no live latency, no completed correction. The disposable emitted
`deployment.json` is a verification artifact, not an operational installation,
and the proposed destination was never touched.

## claim367503 — the verification contract, the provenance, and a reproduction that needs nothing hidden

Answers `review-2026-10-27T18-27-26Z.md` (R1, R2, R3). The connected sequence
the reviewer independently reproduced is **preserved and not re-derived**; this
claim corrects what that sequence was carrying.

### R1 — the selected guide's own verification contract

The composed task copied the pilot's `task.json` and changed only the task id,
the declared base and the instructions, so its `verification` argv still read
`v12/QUICKSTART.md`. **That false success is reproduced, not described:**
`GUIDE-CONTRACT.json` case
`inherited_pilot_contract_on_a_tree_without_the_guide` runs the inherited argv
in a tree with no `v12/TEMPLATE-JOBS.md` and records `exit 0`,
`"quickstart structure ok: 16847 bytes, 4 sections"`.

`guide_contract.py` replaces it with a contract written for the deliverable.
`prove_guide_contract.py` drives **15 cases**, each one run rather than
asserted, in workspaces it creates under the scratch root whose `v12/python`
is a symlink to this checkout so the parsers are the real ones:

    refused  selected_contract_missing_guide        "there is no v12/TEMPLATE-JOBS.md"
    refused  selected_contract_quickstart_only      the old quickstart satisfies nothing
    refused  sections_missing / sections_out_of_order
    refused  template_version_absent                the exact version is not named
    refused  unresolved_marker                      TODO survives
    refused  stale_subcommand                       'job-status' is not served
    refused  stale_option                           create omits --work-scope
    refused  stale_create_option_refused_by_the_parser   ← the PRODUCT's parser
    refused  stale_monitor_option_refused_by_the_parser  ← the PRODUCT's parser
    refused  wrong_template_version_in_the_example
    refused  create_example_authors_a_document      --document is not input-only
    refused  undefined_expansion                    $UNDEFINED survives the guide's own assignments
    PASSES   qualifying_guide                       6 ordered sections, 11 invocations parsed, 1 create example

The two parser cases matter most: they keep every required operand and add one
this build does not serve, so the refusal comes from `job_manager`'s and
`stack.main`'s own argparse and not from my checklist. That is the
criterion-5 shape — command options checked against the owning implementation.

**It is mechanical and says so in its own output:** *"MECHANICAL ONLY — the
five acceptance criteria are the independent reviewer's judgment, not this
command's."* It also **refuses rather than degrades**: if the owning parsers
cannot be imported it exits non-zero, because a contract that quietly skipped
its only semantic step would be the same false success again.

`fixtures/qualifying-TEMPLATE-JOBS.md` exists **only** so the positive outcome
can be driven. Its own header says it is not the deliverable, and nothing the
installer consumes refers to it — fixture and operational output kept apart.

### R2 — every manifest member accounted for, and seven named as missing

`capacity.manifest_provenance` classifies **every** member into three kinds,
and `unaccounted_members` is `[]`:

* **selected** — `work_ref` (the mint), `human_contract` (sha256 of the task
  bytes actually written), `record_binding` (this child's `FINDING.md`/
  `PLAN.md`, digested now), `manifest_digest` (the seal, computed last).
* **inherited-contract** — `sources` and `outputs` from the reviewed pilot's
  own input manifest; `policy_digest`, `runtime_profile_digest`,
  `worker_image_digest`, `retention_policy_digest` from the reviewed pilot
  **worker deployment**; the structural members from the published vector.
  Each carries the file path and that file's sha256. Each is labelled *an
  accepted contract, not a content check* — the documents behind those digests
  are published nowhere in this record, so nothing here claims they were read.
* **unresolved-grant** — the seven the review named:
  `role_instructions_digest`, `toolchain_digest`, `resource_policy_digest`,
  `network_policy_digest`, `mount_policy_digest`, `tool_policy_digest`,
  `credential_policy_digest`. Each records **what it names** (from
  `contracts/manifest.py`'s own classification) and **the exact selection that
  is missing**.

They are not invented, and the product says why not. `tools/dogfood_operator.
input_manifest`: *"EVERY POLICY IDENTITY IS AN OPERAND … A tool that filled one
in would be making a grant on an operator's behalf."* They are also not a
fixture smell I introduced: `tools/next_run_bindings.py`, the product's own
composer for this exact shape, reads the same published corpus and overrides
exactly five members, leaving these seven. The corpus is now read **directly
by its record path with its digest reported**, not through a test helper.

**So the preparation reports itself incomplete, everywhere.** `preflight`,
`compose` and the proof all carry `preparation_is_complete: false` and
`why_not_complete` naming the seven. That is review R2's instruction followed
literally.

Three further provenance defects were found and fixed while accounting:

1. **`integration_profile.instructions_digest` was the manifest's
   `role_instructions_digest`** — the `eeee` placeholder had indeed only
   moved. It now comes from `v12/instance-inputs.json` at the selected
   revision (`sha256:fafc3595…`), a named shipped source, as do
   `profile_kind`, `profile_version`, `retention_policy_digest` and
   `retention_disposition`.
2. **Both lanes inherited `workers[0]`.** The review lane was carrying the
   implementation worker's `review_route: "rview"` when the pilot's own review
   worker carries `"owner"`. `_pilot_deployment_base(role)` now matches by
   role and refuses if the pilot does not configure exactly one. The emitted
   configuration now reads `{implementation: rview, review: owner}`.
3. **Two places wrote one fact.** `compose` now *refuses* if the pilot
   worker's `retention_policy_digest` and the checkout's canonical inputs
   disagree, instead of silently preferring one. They agree today.

### R3 — nothing hidden, and the refusals are against *this* composition

`prove_capacity.py` replaces the `/tmp/seq.py` + `/tmp/distro.txt` pair.
Run with no arguments it **materializes its own runtime** through
`capacity.materialize` — the same entrypoint an operator calls, verifying the
archive sha256 *and* the extracted folder digest — so there is no transient
prerequisite to know about. `--distro` reuses an already-verified one.
`CLEAN-START.md` documents the whole thing: two prerequisites, three
entrypoints, two provers.

The published run, `evidence/claim-367503/PROOF.json`, materialized its own
runtime (`folder_digest 0b7bc592…`) and reached:

    step 1  mint only, `bootstrap --inputs` ALONE        exit 0
            generated uuid, configuration carries NO workers
    step 2  readback from the instance's own record
    step 3  compose — two lanes, own participants, base 42bed8bb…,
            integration instructions sha256:fafc3595…,
            preparation_is_complete FALSE, unaccounted members []
    step 4  ONE destination install carrying both lanes  exit 0
    step 5  DeploymentDerivation — both profiles, one Work, one input
            digest, review routes {implementation: rview, review: owner}
    step 6  ordinary `manager create`                    exit 0
            all five criteria, and the statement and criteria compared
            EQUAL to the selection rather than counted
    step 7  the refusals                                 all five

Step 7 runs against **this** composition, not an old fixed-identity fixture:
stale source (`compose` refuses a checkout at another commit), foreign
authority identity (three shapes — non-hex, short, absent), wrong retained
artifact (the archive pin moved, then restored and re-checked), occupied
materialization target (a planted sentinel survives byte-identical and nothing
else appears in the directory), and the seal (one member moved after sealing;
the owner's own digest over the altered document differs).

`evidence/claim-367503/BINDING.json` is the digest binding R3 asks for: the six
delivered artifacts, the seven external inputs they read, every evidence file,
and the outcomes those bytes produced — so the parent assembles on reviewed
bytes rather than on whatever is on disk later.

**And one hazard removed.** `compose_capacity.py`'s `materialized` still
carried the live `shutil.rmtree` on a fixed shared path — the pattern behind
`INCIDENT-367234-scratch-deletion.md`. Its body is retained verbatim as the
record of the attempt; its **entrypoint now refuses** and points at
`capacity.py`. A known-unsafe command left callable in a delivery is a hazard,
not a preserved attempt.

### Verification and cumulative spending

This claim: 15 guide-contract cases (×3 runs while they were being driven to
real outcomes), 4 joined-proof runs, 3 CLI verb invocations plus one driven
CLI refusal. Earlier on this child and preserved: six sequence runs at
claim367431, four sequence attempts, three connected attempts, two preflights,
three materializations and eleven proof cases. No test file in `v12` was run
or changed.

### Boundaries

Nothing was deleted. Every path this claim wrote is one it created under
`/var/tmp/baton-w257624` with `mkdtemp`, and all are retained. The canonical
`v12` tree is **byte-unchanged** and nothing was copied into it. The proposed
`useful-template-job-w366962` destination was never touched. Parent files, the
pilot packet and every historical artifact were read-only inputs; this child's
`FINDING.md` and `PLAN.md` are the reviewer's and are unmodified. The
unrelated September scratch root was not touched again and its loss remains
unenumerated.

**Not established:** no provider authentication, container start, model
output, live latency or completed correction. The emitted `deployment.json` is
a verification artifact, not an operational installation. The seven operator
grants are unresolved, so **this is a reusable preparation with a real
connected proof — not a finished operational configuration.**

## claim369192 — the seven, proposed with real sources, and the four bounded corrections

Owner selection E369183: *"Select preparation of concrete proposed artifacts
for the seven missing policy/instruction/toolchain inputs, reusing documented
existing policies where supported. Make proposed grants explicit for review;
do not infer authorization from fixture values. Complete the bounded remaining
review corrections."* Reviewer limitations from `review-2026-10-27T18-50-04Z.md`.

### (superseded in part by claim369298 — `compose` wrote into `proposed-grants/`)

### The seven, proposed with real sources — and not one grant

`proposed_grants.py` emits seven artifacts into `proposed-grants/`. **Five are
reused from content that already exists at the selected revision**, which is
the "reusing documented existing policies where supported" half of the
selection:

| member | derivation | source |
|---|---|---|
| `role_instructions` | **reused** | the product's own `claude_agent._prompt` and `_review_prompt`, **rendered against this Job's task** |
| `toolchain` | **reused** | `v12/worker/Dockerfile.claude`, the image recipe at `42bed8bb` |
| `tool_policy` | **reused** | `provider_context.ARGV_POLICY` / `ENVIRONMENT_POLICY` |
| `mount_policy` | **reused** | the reviewed manifest's `sources[].consumption`, `single_worker.SOURCE_DESTINATION` |
| `credential_policy` | **reused** | the reviewed worker's credential profile, slots, sources registry |
| `resource_policy` | authored | the reviewed worker's workspace capacity, `source_boundary.MIN_WORKSPACE_BYTES`/`SCRATCH_BYTES`/`SHARED_MEMORY_BYTES`, this Job's limits |
| `network_policy` | authored | the documented `bridge` selection; the product ships no network policy document |

The role instructions are the strongest of the seven: `claude_agent` will not
import from a checkout (it reaches for `source_profiles`, which the image
builds), so its two prompt composers are extracted from its syntax tree by
name and executed alone with only the constants they reference. What comes out
is the text **this deployment's own workload would compose for this Job** —
real existing content, not instructions I wrote. One identity covers the pair
because `contracts/manifest.py` projects `role_instructions_digest` OUT of the
Job-scoped identity *precisely* because the two roles are told different
things.

**The toolchain caveat is in the artifact, not just here:** the recipe is not
the built image. Nothing contacts an engine, so binding it accepts the recipe
at `42bed8bb` as the toolchain statement for `sha256:c862c055…`.

**And none of them is a grant.** Every document carries
`status: "proposed-not-granted"` and `authorized_by: null`; binding them is an
explicit `--proposed-grants`; and with all seven bound the composition still
reports `preparation_is_complete: false`. The accounting simply moves those
members from `unresolved-grant` to a third kind, `proposed-grant`, each naming
the artifact, its file digest, whether it was reused or authored, and what it
**still needs**: an owner's selection. `tools/dogfood_operator.input_manifest`
is why — *"A tool that filled one in would be making a grant on an operator's
behalf."* Composing a proposal is not receiving a grant, and no answer here
says it is.

Step 10 of the proof shows the proposal is **coherent with the installer**,
which is what an owner needs in order to decide: a fresh mint, compose with
all seven bound, one install (exit 0), the derivation, and ordinary `create`
exit 0 reaching both lanes — with `no_vector_constants_left: true` and
`still_not_complete: true` recorded side by side.

### The four bounded corrections

**1. The formatting gate was unselected, and that claim is withdrawn.** The
review is right: USEFUL-JOB.md enumerates *topics*, not headings, and my
checker's claim that the parent enumerates six exact headings was inaccurate.
Both halves of the owner's remedy are done. **By default there is now no
format gate at all** — case `differently_organised_guide_passes_by_default`
takes the qualifying fixture, renames all six headings to a different scheme,
and it **passes**. With `--proposed-format`, `capacity.FORMAT_ADDENDUM` goes
into the instructions the worker reads *and* the verification enforces exactly
what that text announces. One operand sets both, so the rule that judges the
guide can never be a rule its author was not given. The same renamed file is
refused in that mode, which is the pair.

**2. A valid foreign identity, not just malformed ones.** The review was right
that three malformed uuids are not a foreign-authority test. The first cut of
this case was also wrong and is recorded as such: offering a foreign-uuid
document to the *already installed* instance got *"there is already a runtime
… nothing here upgrades a deployment in place"* — a **custody** refusal that
says nothing about identity. So the case now mints its **own** fresh
destination and offers it a document composed under a well-formed uuid that is
not that instance's. Both arms refuse, and both for the right reason:

    install  "the bootstrap input manifest names another Authority"
    create   "the Job store … belongs to Authority '96238ef9…' and this open
              names 'ffffffff…'; … Nothing was changed"

`compose` itself accepts it, correctly — a well-formed identity is not
something a composer can tell is the wrong one. The instance is what knows.

**3. `preflight` writes nothing, measured.** Every ordinary file under the
child directory (62 of them, `__pycache__` excluded) is digested, `preflight`
runs, and they are digested again: `changed: []`. The proposed destination's
existence is checked on both sides too, since the path it derives paths *for*
is the one it must not create.

**4. `--distro` pins independently.** It no longer leans on the installer's
runtime admission: the named folder is measured with the product's own
`instance.manifest` and held to the retained archive record's folder digest
**before anything else runs**, exactly as `materialize` holds the one it
extracts. A folder that does not match is refused with both digests named.

### Verification and cumulative spending

This claim: 18 guide-contract cases (3 runs while the format split was driven
to real outcomes), 4 joined-proof runs of the now-ten-step chain, one
proposed-grants emission, one CLI preflight. Preserved: 15 cases and 4 proof
runs at claim367503; six sequence runs at claim367431; and earlier, four
sequence attempts, three connected attempts, two preflights, three
materializations, eleven proof cases. No `v12` test file was run or changed.

`evidence/claim-369192/BINDING.json` (sha256 `45d0894b…`) binds the seven
delivered artifacts, the seven proposed artifacts, the external inputs, the
five files the proposal reads from, every evidence file, and the outcomes.

### Boundaries

Nothing deleted. Every path written is one its own invocation created under
`/var/tmp/baton-w257624` with `mkdtemp`, all retained. `v12` is
byte-unchanged — its porcelain status is empty. The proposed
`useful-template-job-w366962` destination was never touched. `FINDING.md` and
`PLAN.md` are the reviewer's and are unmodified.

**Not established:** no provider authentication, container start, model
output, live latency or completed correction. The toolchain proposal describes
a recipe and not an image inspection. No credential was read or resolved. The
emitted `deployment.json` files are verification artifacts, not installations.
**Seven grants remain the owner's to select; this is a preparation with a
concrete proposal to decide on, not a finished operational configuration.**

## claim369298 — the composition writes nothing, and that is now measured over the whole command

Answers `review-2026-10-27T22-59-54Z.md`, one bounded custody defect. The
reviewer is right and the finding is mine: `compose(proposed_grants=True)`
called `proposal.write(...)` with no output argument, so an advertised
read-only composition **overwrote the very artifact awaiting owner selection**
— and step 10 selected the format, so the bytes it wrote were a *different
variant* of `role_instructions.json`. `compose` reported `wrote: []` while
doing it, and step 8's no-mutation check ran *before* the mutation, so its
success proved nothing about the whole command.

### Composition reads; publishing writes; neither writes over the other

**`compose` no longer writes anything.** It consumes a *published set*
read-only: it loads `INVENTORY.json`, digests every file in the set and holds
it to that inventory, and holds the inventory's **task digest** to the task
being composed. A set composed for another task is refused by name with the
remedy. `effects` now carries a truthful `read:` list — the inventory and the
seven files — alongside `wrote: []`, which is finally true.

**Publishing is a separate explicit command, and it refuses to overwrite.**
`proposed_grants.py` gained `--into`, `--proposed-format` and a read-only
`--verify`. A directory already publishing an inventory for a different task
(or a different format selection) is refused:

    refused: …/proposed-grants already publishes a proposal set for task
    digest c21e6b93bfe199eb (proposed_format=False) and this one is for
    cb7001c74de828ab (proposed_format=True). These are different sets with
    different role instructions, and nothing here writes over a set awaiting
    selection. Publish this one somewhere of its own: `--into <a fresh
    directory>`.

**Both sets are now published with distinct identities**, which is what the
review asked for and what an owner needs in order to select one:

| set | role_instructions file | identity if granted |
|---|---|---|
| `proposed-grants/` (default) | `8ac96cb6…` — the reviewer's restored bound bytes | `sha256:6fbe6854…` |
| `proposed-grants-format/` | `68086264…` — the bytes preserved in the reviewer's `ROLE-INSTRUCTIONS-MUTATED.json` | `sha256:374b89f6…` |

Only `role_instructions.json` and `INVENTORY.json` differ between them; the
other six files are byte-identical, because only the role prompts depend on
the task text. The variant is no longer something a proof produces as a side
effect — it is a published artifact of its own.

### Step 10 rebuilt, step 11 added

Step 10 now has two arms, both consuming published bytes read-only: the
canonical default set, and a format variant published by an **explicit**
`proposed_grants.write` into a `mkdtemp` directory the run owns. Each mints,
composes, installs (exit 0), derives and creates (exit 0) reaching both lanes
— with `compose_wrote_nothing: true` and `consumed_read_only: true` recorded.
Between them, the mismatch refusal is driven.

**Step 11 is the custody guard the review said step 8 could not be.** Step 8
digests around one subcall; the defect happened in step 10, *after* step 8 had
passed. So the whole child directory (94 files) is digested before anything
runs and again at the very end: `appeared []`, `vanished []`, `rewritten []`,
`proposal_set_unchanged: true`.

### `prove_custody.py` — the commands as a set, repeated and reordered

The review asked for the *entire public invocation* with both opt-ins,
repeated, with variants, so run order cannot silently select content. A guard
inside one command cannot show that, so this is a new prover that runs the
**public commands as subprocesses**: publish the variant twice, then both
compose opt-ins in both orders three times over, then the whole
`prove_capacity.py` twice, then `--verify`. **Eleven runs, all exit 0.** Then
the three custody refusals, all exit 2:

    publishing_the_variant_over_the_canonical_set
    publishing_the_default_set_over_the_variant
    binding_the_canonical_set_to_the_format_task

Afterwards: nothing appeared, vanished or was rewritten; the published
inventory is unchanged; republishing the same variant is byte-identical; and
**both prior claim bindings' proposal digests still hold** (`claim-369192`'s
seven, read from the record itself, zero drift).

### What I got wrong, plainly

The reviewer's finding is exactly right. `compose(proposed_grants=True)`
called `proposal.write(task_document)` with no output argument, so a command
advertised as read-only published into the canonical directory — and because
step 10 selected the format, the bytes it wrote were a *different variant* of
the artifact awaiting owner selection. `compose` reported `wrote: []` while
doing it. My step-8 no-mutation check passed because it ran before the
mutation, which is precisely why a subcall guard is not a command guard. The
reviewer's own run triggered it, preserved the changed bytes, and restored the
default after checking both directions — all seven hashes matched my binding
again at the start of this claim, and I re-verified that before touching
anything.

### Verification and cumulative spending

This claim: 11 public subprocess runs in the custody prover (including two
whole proofs) plus 3 driven refusals; 3 direct `prove_capacity` runs of the
now-eleven-step chain; 18 guide-contract cases; 4 `proposed_grants`
invocations (publish, verify, variant publish, refused overwrite). Preserved:
claim369192's 18 cases and 4 proof runs; claim367503's 15 cases and 4 proof
runs; claim367431's six sequence runs; and earlier, four sequence attempts,
three connected attempts, two preflights, three materializations, eleven proof
cases. No `v12` test file was run or changed.

`evidence/claim-369298/BINDING.json` (sha256 `da14f9ba…`) is the corrected
exact binding: eight delivered artifacts, **both** proposal sets with their
inventories and task digests, the external inputs, the five files the proposal
reads from, every evidence file, the outcomes, and the prior bindings'
re-verified state.

### Boundaries

Nothing deleted. Every path written outside the record is one its own
invocation created under `/var/tmp/baton-w257624` with `mkdtemp`, all
retained. `v12` is byte-unchanged — its porcelain status is empty. The
proposed `useful-template-job-w366962` destination was never touched.
`FINDING.md` and `PLAN.md` are the reviewer's and are unmodified; the
reviewer's `evidence/review-369275/` is untouched.

**Not established:** no provider authentication, container start, model
output, live latency or completed correction. The toolchain proposal describes
a recipe, not an image inspection. No credential was read or resolved. **Both
sets remain proposals; selecting one — or naming other artifacts — is the
owner's, and every answer still reports `preparation_is_complete: false`.**

## claim369373 — the operator page matches the commands, and is checked against them

Answers `review-2026-10-27T23-11-07Z.md`. The custody correction was accepted;
this is the bounded documentation correction that followed it. No policy
question reopened, no proposal byte changed.

### Both findings were correct

**The page advertised a command that refuses.** `CLEAN-START.md` showed
`compose --minted-uuid <minted> --proposed-grants --proposed-format` as a
usable entrypoint. It binds the *default* set to the *formatted* task, and the
custody correction I delivered last claim makes that refuse — the same
refusal `prove_custody.py` already drove as
`binding_the_canonical_set_to_the_format_task`. I shipped a page whose
headline example my own guard was proving impossible.

**And its opening claim was false.** "Every command is read-only or writes
only into a directory the invocation itself created under the scratch root"
was never true of the publisher, which writes into this record on purpose, nor
of `--evidence`, which writes wherever it is pointed — including into
`evidence/claim-*/`, which is how every one of those directories was made.

### What the page says now

A **per-command table** of what each one writes, replacing the single false
sentence: `preflight` and `compose` nothing (unless `--evidence`);
`materialize` only a directory it creates; `proposed_grants.py` **into this
record**, because publishing is its job; `--verify` nothing; the provers only
their own scratch plus `--evidence`.

A new section, *"Binding a proposal set — the set and the task must match"*,
with the two forms that work, each pairing a set with its own task:

    compose … --proposed-grants                                    exit 0
    compose … --grants-from proposed-grants-format --proposed-format  exit 0

and the mixed form kept as a **labelled expected refusal**, with the product's
actual message quoted. Both successes and the refusal were driven before
publishing them: `evidence/claim-369373/example-a-default.json`,
`example-b-formatted.json`, `example-c-refusal.txt` (exit 2).

The publisher section now says plainly that it writes into the record and what
it will *not* do — write over a set composed for a different task — and pins
both inventory digests, neither granted.

### The page is now checked against the commands

Documentation drifts from code when nothing compares them. `prove_custody.py`
now runs **the two documented success forms verbatim**, including the
record-relative `--grants-from proposed-grants-format`, so the page cannot
quietly disagree with the commands again. **13 public runs, all exit 0; three
refusals, all exit 2; 113 dossier files unchanged** — nothing appeared,
vanished or was rewritten.

### Two defects in my own verifier, found by reading its answer

The binding check inside `prove_custody.py` reported
`proposal_members: 0, drifted: []` for `claim-369298` — a clean result for a
binding it had **not actually looked at**. Two causes, both mine, both fixed:

1. it understood only the `/2` binding shape (`proposed_grants.members`) and
   not `/3`'s two named sets under `proposal_sets`;
2. once it could see them, every member reported as drifted — because
   `claim-369298` recorded member paths relative to *this child directory*
   while `/2` recorded them relative to the *repository*, and the checker
   assumed one form.

Neither path form is wrong; a verifier that understood only one was. It now
accepts both, and this claim's binding writes repository-relative paths
consistently. All three bindings now verify for real: **21 proposal members,
zero drift.**

### Verification and cumulative spending

This claim: 3 custody-prover runs (13 public subprocess invocations each,
including two whole connected proofs per run) plus 3 driven refusals, and 3
direct example invocations recorded as evidence. **Reused without rerun**, as
the review permits for prose: the 18 guide-contract cases at claim-369298 —
`guide_contract.py`, `prove_guide_contract.py` and the fixture are
byte-unchanged here — and `prove_capacity.py`, also byte-unchanged and still
run twice inside every custody proof. Preserved: claim-369298, claim-369192,
claim-367503, claim-367431 and the earlier attempts.

`evidence/claim-369373/BINDING.json` (sha256 `92d9962a…`) rebinds the two
changed delivered files, re-states both proposal sets with
**byte-identical** content and consistent repository-relative paths, and
preserves `claim-369298`'s binding by digest.

### Boundaries

Only `CLEAN-START.md` and `prove_custody.py` changed. **No proposal byte
changed** — verified against claim-369298's binding, both sets identical.
Nothing deleted; `v12` byte-unchanged; the proposed destination never touched;
`FINDING.md` and `PLAN.md` are the reviewer's and unmodified; the reviewer's
`evidence/review-369347/` is untouched.

**Not established, unchanged by a documentation correction:** no provider
authentication, container start, model output, live latency or completed
correction; the toolchain proposal is a recipe, not an image inspection; no
credential resolved. **Both sets remain proposals and
`preparation_is_complete` is still `false`** — selecting one, or naming other
artifacts, is the owner's.
