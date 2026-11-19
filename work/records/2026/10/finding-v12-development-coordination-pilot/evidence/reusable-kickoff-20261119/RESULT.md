# W321608 — reusable native Job kickoff: candidate and evidence

K, 2026-11-19, under the owner-held assignment (W321608 active, handler slaw, route baton.decide, claimed 2026-11-19T02:10:07Z; K holds no claim). Base `f34e1576e051feabf4b1d1664eeb9cca9897c38c`. Candidate identity `sha256:2b10b1844097b9d6773e8aa62d64cc13c8749a76b16f0559d750b8922c329866` over 10 changed paths (`source.json`, `CANDIDATE-SHA256.txt`; sha256 over the sorted `<path> sha256:<digest>` lines); bytes in `candidate.diff` (898 lines). No build, install, engine, live provider, full suite or Git mutation. Answers HANDOFF-REUSABLE-KICKOFF-20261119.md.

## The supported path, revalidated at `f34e1576` (no change needed)

- **Install once** (`v12/STACK.md`): `just build` → `bootstrap <inputs.json> <DEST> <DISTRO>` with the instance-only document (no workers, no Job; identity minted) → one-operand repeat `bootstrap <updated-inputs.json>` naming `workers[]` (+ optional `jobs[]`), which clones each worker's nominated source and composes the deployment. `pool add-worker` admits one more complete worker document into an installed instance.
- **Ordinary kickoff** (`tools/job_manager.py`): `manager create --task --statement --acceptance… --work-scope… [--test-scope…] [--control-profile …]` — input-only; the Work is created or reused by the deployment (`creation_ports.NewJobBinding` appends the Job to the install document and runs `bootstrap.prepare`), the per-Job task is composed from the installed task document (`tools/job_task.py`), and `start` serves it. `create` takes the manager instance lock, so on a serving instance the idle-first-run path is stop → create → start; create-while-serving stays W375518's outcome.

## The two concrete blockers found, and the bounded corrections

| Blocker (exact failed contract) | Correction | Owner overlap |
|---|---|---|
| A defined Job could not carry its own verification: `job_task.SUBSTITUTED = ("task_id", "instructions")` and `creation._asked` admitted no such member, so a coding Job's focused test command could only change by reinstalling the deployment's task document — an installation per Job. | `creation._asked` admits optional `verification` (non-empty list of argument words, ≤64 words, ≤16384 chars each; part of the caller's intent/`request_digest`); `_resolved` hands it to the deployment's selection and strips it before `templates.resolve` (the resolver's contract is untouched); `job_task` admits `SELECTION_OPTIONAL = ("verification",)` and `compose_task(..., verification=None)` substitutes it only when stated (an installed task without one refuses; the installed argv travels otherwise); `manager create --verification WORD` (repeatable, `--verification=-m` for dash-leading words). The composed task bytes are the Job's input identity, so the verification is inside it and durable in `template_jobs.task_document`. | `creation.py`: W375517's initial ownership names "job_manager creation/store/schema owner modules" (`block`, unclaimed); `tools/job_manager.py`: W375518's named file (`block`, unclaimed). Both edits are additive (one optional member, one operand); listed with digests for coordinator resolution, as W383217 did for the same files. `tools/job_task.py` has no live owner. |
| A worker's `/4` deployment document (digest-sealed `input_manifest` over the instance's Authority/Work, `human_contract` over installed task bytes, derived paths) had no product producer; every installation to date composed it with a dossier script. `pool add-worker` admits only a complete document. | `pool compose-worker --deployment <instance deployment.json> --like <reviewed worker document> --worker-id --role --participant --image-digest --task-document <abs path> [--work-id] --into <fresh file> [--admit]`: binds Authority, Work (instance's `job_work_id` or `<uuid8>-W1`), image, task artifact, identity, `manifest_id`/`created_at`, and the same derived paths `bootstrap` derives (`workers/<id>/storage`, `repo/source-<id>`, `state/launch`, `state/credentials`); inherits every deployment fact and manifest policy member from `--like`; reseals by §12's rule and proves with `check_manifest_structure`; writes one fresh file (an existing path refuses) and changes no configuration unless `--admit`. Registered as the bundled `pool` subcommand (`stack_command.COMMANDS`) so the installed command reaches it. | `tools/pool.py`, `tools/stack_command.py`: no live owner (W202663, W321688/9 closed). `tools/bootstrap.py` (W375516) is NOT edited; its rules are called (`_safe_name`, `ROLES`, `held_worker`, `admit`). |

What was deliberately not changed: templates/submission contracts, bootstrap, the worker, DESIGN (OBS-0/OBS-0a already specify the outcome).

## Verification (prepared venv, `just`, TMPDIR=/var/tmp BATON_V12_DISK_ROOT=/var/tmp)

New cases (standing test-change authority; no existing expectation changed):
- `tests/tools/test_job_task_delivery.EachJobCarriesItsOwnVerification` (3): own vs installed verification from one installed task; manifests name each Job's bytes; the verification is inside the input identity; malformed/foreign members refuse; an installed task without a verification cannot take one.
- `tests/tools/test_creation_ports.TwoDistinctTasksOnOnePool.test_a_job_naming_its_own_verification_is_derived_with_it`: through the real derivation port over a held deployment.
- `tests/job_manager/test_creation.TheRequestedVerificationIsTheJobsOwn` (2): reaches the selection, is part of the intent (replay converges, another verification refuses), malformed refuses before any effect; `TheCommandRequestsTheOperation.test_a_verification_is_one_word_per_operand_and_absent_otherwise`.
- `tests/tools/test_connected_creation.TheConnectedCreation.test_a_created_job_carries_the_verification_it_named`: the real source command over a real install, two defined Jobs on one installed task — each receives its intended instructions and verification; nothing of the installation written per Job; replay converges; a changed verification refuses.
- `tests/tools/test_pool.ComposingAWorkerForThisInstance` (5): derived members and inherited facts; resealed manifest proved; two defined tasks compose two workers with no installation; a composed worker is admitted once its source exists and the manager accepts the configuration; refusals write nothing; CLI writes one fresh file, refuses a second, and `pool` is a bundled subcommand.

| what | result | wall | log |
|---|---|---|---|
| four touched modules before the new cases (baseline on the patched creation path) | 210 OK | 12 s | (scratch) |
| seven modules after the verification pass-through | 398 OK | 25 s | `focused-verification-passthrough.log` |
| twelve modules over both corrections (pool, stack, bootstrap, delivery, creation, creation_ports, connected/packaged creation, job_control, templates, dossier/disposition commands) | 803 OK, 0 skipped | 72 s | `focused-both-corrections.log` |
| group job_manager (reason: creation owner changed) | 1599/1599 OK, 0 skips | 15.5 s | `group-job_manager.log` |
| group tools-pure (reason: tools job_manager/job_task/pool/stack_command changed; new cases registered in existing modules) | 3379/3379 OK, 0 skips, 0 failures | 150 s | `group-tools-pure.log` |

Required-test accounting: the runner's ledger reports collected = executed with 0 required skips in both groups (see `groups.wall`). `tests.tools.test_packaged_creation` RAN (not skipped) in the focused set because this host holds a built bundle at `v12/python/build/out/distro` (stamp `f896bab0`, dirty, built 2026-11-18); that is a PRE-CHANGE bundle, so those cases prove only the pre-existing packaged behaviour and exercise neither `--verification` nor `pool compose-worker` through a bundle. A packaged proof of the new operand/verb needs a bundle built from the accepted source (the one-time host build of the operational selection); until then the source-level connected cases above are the evidence. Scans not rerun: no module/registry/doc path changed.

## Short supported commands (prepared; nothing executed here)

One-time install (reusable, task-independent), from `v12/`:
```sh
just setup && just build /home/sl/baton-instances/native-build                 # host bundle → native-build/out/distro
"$DISTRO/baton-v12-stack" bootstrap --inputs instance.json --destination "$DEST" --distro "$DISTRO" --repository-source /home/sl/src/baton   # instance-only document (STACK.md "A fresh installation has zero Jobs"); identity minted
"$DISTRO/baton-v12-stack" pool compose-worker --deployment "$DEST/deployment.json" --like <reviewed worker document> --worker-id impl-a --role implementation --participant baton.claude-native --image-digest sha256:… --task-document "$DEST/state/task/installed-task.json" --into workers/impl-a.json
"$DISTRO/baton-v12-stack" pool compose-worker … --worker-id review-a --role review --participant baton.reviewer-native --into workers/review-a.json
just --justfile /home/sl/src/baton/v12/justfile bootstrap updated-inputs.json  # one-operand repeat: instance document + state_root + the two composed workers (STACK.md "Reconfiguring an instance"); clones each worker's source
just --justfile "$DEST/justfile" start && just --justfile "$DEST/justfile" stop  # control store initialized; no Job, no container, no provider
```
Ordinary kickoff of a defined Job (idle first run):
```sh
just --justfile "$DEST/justfile" stop
"$STACK" manager --store "$DEST/db/jobs.sqlite3" --incarnation create-1 --authority-uuid "$UUID" create --instance "$DEST" --control "$DEST/db/control.sqlite3" --authority "$DEST/db/authority.sqlite3" \
  --task w29401-labels-cli --statement "$(cat task-statement.txt)" --acceptance "…" --work-scope v12/python/tools/work_command.py … --test-scope … \
  --verification python3 --verification=-c --verification "$(cat verify.py)" --control-profile documentation/1
just --justfile "$DEST/justfile" start
```
Timing: deterministic evidence here is the connected creation cases (real command, real install, measured per run in the log); the whole-path ≤60 s is measured on the selected native run from the instant the finished inputs are handed to the kickoff path to the first attributable substantive activity, as the r2 checkpoint §5 defines; nothing here claims it.

## Gaps that remain (recorded, not gates for the idle first run)

- Create while serving (W375518): the idle-first-run path is stop → create → start; the later same-instance second-Job proof under a serving manager belongs to W375518/W375519.
- Packaged proof of the new operand/verb awaits the one-time host build from accepted source (above).
- `pool compose-worker` inherits deployment facts from a reviewed worker document; a first installation on a host with no reviewed document still needs one (the pilot's reviewed `revision-4` deployment or the retained w366962 workers are such documents).

---

# r2 — corrections after review-2026-11-19T02-52-40Z

K, 2026-11-19, same assignment. Corrected candidate `sha256:01007a4c6cb7741d7efd30bc2fee609c39539a1651dc74210a9e7a6399694eda` over 13 paths on `f34e1576` (`source-r2.json`, `CANDIDATE-SHA256-r2.txt`, `candidate-r2.diff`, 1520 lines); supersedes `2b10b184…` (retained above). The per-Job verification path from r1 is unchanged.

## Finding 1 — the inputs traced to reusable product configuration

The product already composes a complete worker deployment from its own documents: `tools/next_run_bindings.compose` builds the runtime profile (`baton.single-implementation-runtime-profile/1`), execution policy and adapter identity from this build's constants and the input manifest from the published conformance vector; the pilot instance's deployment facts (profile `claude-fresh-implementation`, adapter `docker-single-worker`) are exactly these. So the "reviewed worker document" the r1 verb inherited from was never necessary. Corrections:

- `next_run_bindings.deployment_identities(...)` and `input_manifest(...)` are factored out of `compose` verbatim (byte-identical outputs; `compose` calls them; the three next-run modules pass unchanged, 50 OK).
- `pool compose-worker` no longer takes `--like`. It derives the three identities and the manifest from those functions and binds the instance's Authority, Work, image, task artifact, identity and paths. What the operator names is ordinary configuration only: `--image-reference`, `--image-digest`, `--cli-build`, `--network`, `--credential-sources`, `--credential SLOT=PROVIDER:REFERENCE`, `--workspace-group`, `--task-document`, the worker id/role/participant, and `--vectors` (defaults to the checkout's published vector). Review routes per role are the product's (`rview` for implementation, `integration` for review). Workers of one instance share `state/workspaces`, as the creation derivation requires.
- Two exact missing contracts found while proving the complete path, each corrected minimally in `tools/bootstrap.py` (W375516's named file; W375517's "coherent config/install-input pairs" outcome — overlap recorded below):
  1. A never-bound instance could not create its first Job: the bootstrap input document had no place for an instance-level declared base, and `creation_ports.NewJobBinding._entry` reads it from the kept install document. `OPTIONAL` now admits `line_declared_base` and `canonical_target_id` together (ordinary "which revision" configuration; both or neither; strings), kept in `install-inputs.json` and deliberately not written into the `/2` configuration, which carries no top-level base.
  2. The documented one-operand repeat (`just bootstrap updated-inputs.json`, STACK.md "Reconfiguring an instance") reconfigured the deployment but left `install-inputs.json` describing the previous one, so the next ordinary creation refused with "names 0 implementation workers". The repeat now keeps the document it consumed, published atomically after everything is proved (the destination install already did).

Proof of the complete supported path, by code: `tests/tools/test_connected_creation.TheReusableInstanceServesDefinedJobs.test_two_defined_jobs_run_on_one_product_configured_instance` — real installer (instance-only document, no worker, no Job, instance source named once) → two workers composed by `pool.composed` from product documents and operator configuration → the real one-operand `bootstrap --inputs updated-inputs.json` → two real `manager create` invocations with distinct instructions and verification → each Job's task bytes carry its own; the deployment's workers are byte-identical before and after both creations; both Jobs bound. No dossier document, no hand-sealed manifest, no per-Job installation.

## Finding 2 — exclusive fresh-file creation

`pool.compose` writes through `_written_fresh`: `os.open(O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW, 0o644)`; any existing entry (file, directory, symlink resolving or not, or one that appears between composition and the write) refuses and is left untouched. Cases: `ComposingAWorkerForThisInstance.test_an_existing_entry_is_never_replaced_or_followed` (occupied file keeps its bytes; dangling symlink preserved and its target never created; resolving symlink; directory) and `test_a_concurrently_occupied_path_refuses_at_the_write` (a file arriving after composition is refused at the write and keeps its bytes). The reviewer's probe rerun unchanged: `symlink-probe-after.txt` — refused, symlink preserved, nothing created elsewhere.

## Ownership overlap (for coordinator resolution, per the handoff)

`tools/bootstrap.py` (W375516 initial source owner; `block`, unclaimed): two additive changes — two optional input members with a pairing check in `held()`, excluded from the configuration pass-through; and the one-operand branch of `main` publishing the consumed document. The second realizes a slice of W375517's "coherent config/install-input pairs" outcome (`block`, unclaimed). `tools/next_run_bindings.py`: refactor only. Digests in `CANDIDATE-SHA256-r2.txt`; W375516/W375517/W375518 identities and scheduling untouched. r1's overlaps stand as recorded.

## Verification (r2)

New/changed cases: `test_pool.ComposingAWorkerForThisInstance` rewritten for product-derived facts (7 cases incl. the two fresh-file cases and the bundled `pool` registration); `test_bootstrap.AnInstanceMayNameItsSourceWithoutAJob` (2: accepted and kept by the real one-operand command, not in the configuration; one-without-the-other and a non-string refuse before any effect); `test_connected_creation.TheReusableInstanceServesDefinedJobs` (1, the complete path). r1's verification cases unchanged.

| what | result | wall | log |
|---|---|---|---|
| fifteen modules over everything touched (pool, bootstrap, stack, the three next-run modules, delivery, creation, creation_ports, connected/packaged creation, job_control, templates, dossier/disposition commands) | 858 OK, 0 skipped | 98 s | `focused-r2.log` |
| reviewer's probe rerun | refused; nothing created | <1 s | `symlink-probe-after.txt` |
| group job_manager (reason: creation owner unchanged since r1; rerun for the corrected tree) | 1599/1599 OK, 0 skips | 15.6 s | `group-job_manager-r2.log` |
| group tools-pure (reason: bootstrap, pool, stack_command, next_run_bindings changed) | 3384/3384 OK, 0 skips, 0 failures | 151 s | `group-tools-pure-r2.log` |

Packaged cases again ran against the pre-change local bundle (`f896bab0`) and prove nothing about the new operand/verbs through a bundle. Scans not rerun (no module/registry/doc path changed).

## The actual supported operator path (r2; prepared, not executed)

One-time install, reusable and task-independent (from `v12/`, `$DISTRO=<build>/out/distro`):
```sh
just setup && just build /home/sl/baton-instances/native-build
"$DISTRO/baton-v12-stack" bootstrap --inputs instance.json --destination "$DEST" --distro "$DISTRO" --repository-source /home/sl/src/baton
#   instance.json = STACK.md's instance-only document (no workers, no jobs) plus
#   "line_declared_base"/"canonical_target_id": the accepted source commit the instance's repositories are cloned at
"$DISTRO/baton-v12-stack" pool compose-worker --deployment "$DEST/deployment.json" --worker-id impl-a --role implementation --participant baton.claude-native \
  --image-reference baton-v12-worker:f34e1576 --image-digest sha256:… --cli-build 2.1.247 --network bridge \
  --credential-sources /home/sl/.baton/credential-sources.json --credential claude=operator-file:w202663-development \
  --workspace-group 1000 --task-document "$DEST/state/task/installed-task.json" --vectors /home/sl/src/baton/<published vector> --into workers/impl-a.json
"$DISTRO/baton-v12-stack" pool compose-worker … --worker-id review-a --role review --participant baton.reviewer-native --into workers/review-a.json
just --justfile /home/sl/src/baton/v12/justfile bootstrap updated-inputs.json     # instance.json + state_root + the two composed workers; clones each worker's source; keeps the document
just --justfile "$DEST/justfile" start && just --justfile "$DEST/justfile" stop   # control store initialized; no Job, no container, no provider
```
Ordinary kickoff of a defined Job: unchanged from r1 (`manager create … --verification …`, then `start`); the idle-first-run limit and W375518's ownership stand.

---

# r3 — corrections after review-2026-11-19T03-36-07Z

K, 2026-11-19, same assignment. Corrected candidate `sha256:f52ab1f6ab519cdc197219634049837c6aba4c0b74ad15800853b629e02fd826` over 15 paths on `f34e1576` (`source-r3.json`, `CANDIDATE-SHA256-r3.txt`, `candidate-r3.diff`, 2004 lines incl. the new resource); supersedes `01007a4c…` (retained above). Per-Job verification, the fresh-file contract and the instance-level source selection are unchanged from r2.

## P1 — fresh setup provisions the sources it names

Exact contract corrected: `bootstrap.main` cloned repositories only in the destination branch, so the documented one-operand repeat (`just bootstrap updated-inputs.json`) that adds workers left their nominated sources absent and the next start refused. New `bootstrap.prepare_worker_sources` runs in the one-operand branch before `prepare`: it plans the repositories exactly as the install does (`repository_plan`), clones each worker source that is ABSENT from the instance's own `target.git` with the same `git clone --no-local` form the install uses (`_cloning`), under the same lock (`serialized`) and agreement check (`repositories_agree`), then proves them with `repositories_proved`, which now also proves the instance-level `line_declared_base` is a commit in the target. An existing source is never touched; a repeat with every source present clones nothing; `--no-repositories` says which sources are absent and the manager's own nomination check then refuses the start; an instance installed without a target refuses by name. `custody` (the "already a runtime here" install guard) is deliberately not applied to a repeat.

Proof without hidden fixture effects: `tests/tools/test_connected_creation.TheReusableInstanceServesDefinedJobs` now installs WITH repositories through the real installer (fake `git` process boundary only; every issued argv asserted: target mirror + workspace at install), composes two workers with `pool.composed` (asserting their sources do NOT exist), runs the real one-operand `bootstrap --inputs updated-inputs.json --repository-source …` and asserts exactly two clones from the instance's target to `repo/source-impl-a` and `repo/source-review-a` plus the `cat-file -e <base>^{commit}` proof, then two real `manager create` with distinct instructions and verification; bindings carry the instance base and producer; the workers are byte-identical before and after both creations. The reviewer's `source-preparation-probe.py` rerun unchanged: `Fixture-only source mkdirs suppressed: 0`, test OK (`source-preparation-probe-after.txt`). Creation is what this proves; the Jobs are not run. Unit proof: `tests/tools/test_bootstrap.ARepeatProvisionsTheWorkerSourcesItNames` (3): clones+proof for missing sources and an idempotent second repeat; `--no-repositories` says the absence and the start refuses; no-target instance refuses by name.

## P1 — the manifest template is an installed product resource

`src/baton_v12/contracts/schema/input-manifest-template.json` ships beside the schema assets (the spec packages the whole schema directory); `contracts.frozen.INPUT_MANIFEST_TEMPLATE_BYTES` / `input_manifest_template()` read it from the package, and `identity` reports it under `schema_assets` so a bundle missing it fails at `identity`. `next_run_bindings.input_manifest(None, …)` composes from it; `pool compose-worker` no longer has `--vectors` or `VECTORS` and reaches no checkout or dossier (`test_pool.ComposingAWorkerForThisInstance.test_the_manifest_template_is_an_installed_resource_not_a_dossier`: template content equals the published conformance vector's valid document byte-for-byte in content, read from the package directory, composition succeeds from an unrelated working directory). Frozen-bundle execution of the new verb and asset is deferred to the selected build, as the review allows.

## Verification (r3)

| what | result | wall | log |
|---|---|---|---|
| sixteen modules over everything touched (r2 set + `test_packaging`) | 872/873 OK; ONE failure: `tests.tools.test_packaging.WhatTheBundleSaysItIs.test_every_subcommand_this_command_serves_is_offered` — the stale local bundle (`f896bab0`, pre-change) does not offer `pool` | 101 s | `focused-r3.log` |
| reviewer's source-preparation probe rerun | nothing to suppress; OK | <1 s | `source-preparation-probe-after.txt` |
| group job_manager | 1599/1599 OK, 0 skips | 16.3 s | `group-job_manager-r3.log` |
| group tools-pure (reason: bootstrap, pool, stack_command, next_run_bindings, frozen changed) | 3387/3388 twice (first run and stated retry), ONE failure both times: `tests.tools.test_next_run_flow.JoinedFlow.test_a_pre_runtime_source_refusal_is_accounted_and_not_cleaned`, the same 3 s turn-bound hit as in every earlier occurrence (`child_status -15` at 3.25 s under 32-way load); the class alone 5 OK 38 s (`next-run-flow-isolated-rerun-r3.log`); that flow calls `bootstrap.prepare` directly, never the one-operand branch this round changed, and its logs carry no provisioning output; retained as observed, not explained | 151 s + 152 s | `group-tools-pure-r3.log` |

The `test_packaging` failure is the bundle gate working as designed: that module belongs to the `tools-packaged` group, whose recipe (`just test-packaging`) builds the bundle first and then asks it; the local bundle predates this candidate, so it cannot offer the new subcommand. It is not a source defect and is left exactly as observed; it passes once the bundle is built from this source, which is the selected one-time host build. Packaged creation cases likewise prove nothing about the new verb/operand through a bundle.

## The actual supported operator path (r3; prepared, not executed)

```sh
cd /home/sl/src/baton/v12 && just setup && just build /home/sl/baton-instances/native-build      # DISTRO=<build>/out/distro
"$DISTRO/baton-v12-stack" bootstrap --inputs instance.json --destination "$DEST" --distro "$DISTRO" --repository-source /home/sl/src/baton
#   instance.json: STACK.md's instance-only document (no workers, no jobs) plus "line_declared_base"/"canonical_target_id" = the accepted source commit; the install clones target.git and workspace
cp <defined task document> "$DEST/state/task/installed-task.json"                                 # ordinary configuration: one file inside the instance
"$DISTRO/baton-v12-stack" pool compose-worker --deployment "$DEST/deployment.json" --worker-id impl-a --role implementation --participant baton.claude-native \
  --image-reference baton-v12-worker:f34e1576 --image-digest sha256:… --cli-build 2.1.247 --network bridge \
  --credential-sources /home/sl/.baton/credential-sources.json --credential claude=operator-file:w202663-development \
  --workspace-group 1000 --task-document "$DEST/state/task/installed-task.json" --into workers/impl-a.json
"$DISTRO/baton-v12-stack" pool compose-worker … --worker-id review-a --role review --participant baton.reviewer-native --into workers/review-a.json
"$DISTRO/baton-v12-stack" bootstrap --inputs updated-inputs.json --repository-source /home/sl/src/baton    # instance.json + state_root + integration_target/workspace as deployment.json names them + the two composed workers; clones each worker's source from the instance's target and keeps the document
just --justfile "$DEST/justfile" start && just --justfile "$DEST/justfile" stop                           # control store initialized; no Job, no container, no provider
```
Ordinary kickoff of a defined Job: unchanged (`manager create … --verification …`, then `start`); the idle-first-run limit and W375518's ownership stand.

---

# r4 — correction after review-2026-11-19T04-22-49Z

K, 2026-11-19, same assignment. Corrected candidate `sha256:5d04fb8509bb8730c30b0777bd890c32cada525a5b809729e79b57dc41d0e7ad` over the same 15 paths on `f34e1576` (`source-r4.json`, `CANDIDATE-SHA256-r4.txt`, `candidate-r4.diff`); supersedes `f52ab1f6…`. Only `tools/bootstrap.py::prepare_worker_sources` and its tests changed.

## P1 — existing paths are not proof

`prepare_worker_sources` no longer returns early when every named source exists. On EVERY repeat it runs the agreement check and the read-only proofs (`repositories_proved`: each repository identifies itself, borrows no objects, is one repository, and the target holds the instance's declared base) over the target and EVERY named worker source — present ones and ones this call cloned; a failed proof refuses the repeat again, publishes nothing, and deletes or replaces nothing. Cloning is still limited to absent sources and needs a named source checkout; with `--no-repositories`, present sources are still proved and absent ones are said. Reviewer's `retry-proof-probe.py` rerun unchanged (`retry-proof-probe-after.txt`): first repeat 2, identical retry 2, the retry issues the three `rev-parse` proofs and the `cat-file` base proof and no clone.

Tests (`tests/tools/test_bootstrap.ARepeatProvisionsTheWorkerSourcesItNames`): `test_a_failed_base_proof_refuses_every_identical_retry` (persistent base failure: both repeats refuse, the left-behind clones stay, no clone on retry, deployment.json and install-inputs.json byte-identical); `test_an_existing_source_that_is_not_a_repository_is_refused_and_kept` (an interrupted clone at a named source refuses, is never cloned over, keeps its bytes, nothing published); the valid-repeat case now asserts the second repeat issues the proofs for the target and both sources plus the base proof and zero clones. The connected two-Job creation proof is unchanged and passing.

| what | result | wall | log |
|---|---|---|---|
| bootstrap, pool, connected creation, the three next-run modules, stack | 379 OK, 0 skipped | 73 s | `focused-r4.log` |
| reviewer's retry-proof probe rerun | both repeats refuse; proofs issued; no clone | <1 s | `retry-proof-probe-after.txt` |

No group reruns this round (the review asked for none; r3's group results and the recorded unresolved `JoinedFlow` turn-bound failure stand). The stale-bundle `test_packaging` mismatch stands as recorded. Supported operator path: as r3.

---

# r5 — asset inventory alignment after packaging review 2026-11-19T05-02-14Z

K, 2026-11-19, same assignment. Base is now the owner checkpoint `387f29693bfc6bd81a2325373e7a32da4f70476d` (accepted candidate `5d04fb85…` committed). Delta candidate `sha256:a513185c79337f493e6d69c1af8ebc3c8ee9e73484140fb90d4a61ce32213a7d` over 7 paths (`source-r5.json`, `CANDIDATE-SHA256-r5.txt`, `candidate-r5.diff`, 333 lines).

## The one cause, corrected at one source

`identity` reported three assets; `bootstrap.EXPECTED_ASSETS` and `test_packaging` still named the old two, so the installer refused a correctly built bundle. Now `contracts.frozen.REQUIRED_ASSETS` (name → bytes) and `ASSET_NAMES` are the one inventory: `stack_command` reports `{name: len(bytes)}` from it; `bootstrap.expected_assets()` reads it and `bootstrap.admitted_identity(said, command)` (factored out of `_identity_of`, unchanged rule) holds a bundle to exactly those names with positive lengths — missing, unexpected and malformed entries refuse by name; `test_packaging` asserts the inventory both through `frozen.ASSET_NAMES` and spelled out, and that each reported length equals the shipped bytes. Every stand-in identity in `test_bootstrap`, `test_connected_creation` and `test_instance` (15 fixtures) now reports the full three-asset inventory, so a stand-in can no longer mask a producer/admission disagreement. New `test_bootstrap.TheAssetInventoryIsOneInventory` (4): the real three-asset identity is admitted; a bundle missing the template is refused by name; unexpected/missing/zero/non-integer/absent entries refuse; the live producer (`stack_command.main(["identity"])`) reports exactly the inventory and admission accepts it.

## Verification (r5)

| what | result | wall | log |
|---|---|---|---|
| bootstrap (incl. the four new cases), connected creation, instance, stack, packaging, packaged creation — against the owner's already-built clean `387f2969` bundle, no rebuild | 433/445 OK; 12 failures, ALL in `tests.tools.test_packaged_creation` | 54 s | `focused-r5-inventory.log` |

The 12 failures are the frozen bundle refusing itself: its BUILT `bootstrap` still carries the old two-asset admission while its `identity` reports three (`did not bring exactly … ['agent-session-1.0', 'worker-control-1.0']; it reports {…three…}`). Only a rebuild from this corrected source can change that; it is the owner's packaging gate (`just test-packaging`) the review names. `test_packaging.WhatTheBundleSaysItIs.test_the_frozen_schema_assets_travelled` passes against that bundle with the corrected gate. No Docker, live provider, full suite, group rerun or Git mutation; the recorded `JoinedFlow` timing failure stands.

Expected after the rebuild: `just test-packaging` runs 24 required cases against the rebuilt bundle with 0 failures; if it does not, the first refusal text is the next finding.

---

# r6 — prerequisite roots on the worker-adding repeat (review 2026-11-19T05-23-45Z)

K, 2026-11-19, same assignment. Base `e670e624334c7f924111300b33bd0e94b08011c0`. Delta candidate `sha256:0984e0702f88b91382de087c57336dc5e2e55754477002d7e442937be0f43e10` over 3 paths (`source-r6.json`, `CANDIDATE-SHA256-r6.txt`, `candidate-r6.diff`, 182 lines): `tools/bootstrap.py` and two test modules. No change to the retained instance, image, repositories or payload.

## The gap and the correction

`prepare_prerequisites` (W375516's accepted machinery: pinned ancestry, observed creation, existing usable roots only read, unsafe ones refused, effects ledgered) ran only in the destination install, which an instance-only installation reaches with no worker and so no root to prepare; the repeat that added the workers published a configuration whose `state/workspaces`, `state/launch` and `state/credentials` did not exist. Now the one-operand branch of `bootstrap.main` runs the SAME `prepare_prerequisites` over the repeat's document (instance layout) BEFORE sources are provisioned and before anything is published; on refusal the attempt's ledger is reported through the existing `_Unwind` (retained, never removed) and the refusal propagates, so nothing is published. After `prepare`, the read-only `prerequisite_report` must be empty or the repeat refuses naming the root and why. No manual directory creation anywhere; no new helper.

Tests (`test_bootstrap.ARepeatProvisionsTheWorkerSourcesItNames`): `test_adding_workers_prepares_the_roots_they_start_in` (instance-only install → add two composed workers → all three roots exist as private `0700` directories, `prerequisite_report` empty, the manager's own `workspaces.check_workspace_storage` accepts the store; an identical repeat keeps every root's identity and an operator's file inside it); `test_an_unsafe_root_refuses_the_repeat_and_publishes_nothing` (a symlink at the launch root: refused, not followed, not replaced, configuration byte-identical, no source cloned); `test_a_file_at_a_configured_root_is_refused_and_kept`. The end-to-end connected proof now also asserts the roots exist and the manager's workspace check accepts them after the repeat.

| what | result | wall | log |
|---|---|---|---|
| repeat class, connected end-to-end, startup-prerequisites module | 70 OK | 0.6 s | (scratch r6.log) |
| bootstrap, connected creation, startup prerequisites, instance, pool, stack | 522 OK, 0 skipped | 47 s | `focused-r6.log` |

No group reruns, image rebuild, live execution or Git; the recorded `JoinedFlow` timing failure stands. Supported update path for the retained instance `native-labels-1` (prepared, not executed; for review first): rebuild the host bundle from this source (`just build`), verify it (`just test-packaging` gate), then one more one-operand repeat with the SAME `config/native-workers-e670e624.json` document through the corrected bundle — it reads the existing sources (no clone, proofs only), prepares the three absent roots, and refuses rather than touching anything that exists; no fresh install, no deletion.

---

# r7 — a configured pool with no bound Job starts idle (review 2026-11-19T05-33-40Z)

K, 2026-11-19, same assignment. Base `e670e624`. Candidate `sha256:599b7ffd44a9885948fc34deafbc73683e4dceb6977f8fec2f5c8cfe0a612c6d` over 4 paths (`source-r7.json`, `CANDIDATE-SHA256-r7.txt`, `candidate-r7.diff`, 369 lines): this round adds `tools/stage_execution.py` and the end-to-end proof; the r6 prerequisite correction (bootstrap + its tests) is carried in the same candidate and was accepted at seq 385201.

## The gap and the correction

`stage_execution.operations_from` minted and authorized the receipt sessions eagerly in `_bound_scope(...)`, which is `None` when no Work is bound; `_sessions` then demanded `verify`/`review`/`approve`/`integrate` capabilities in `None` and refused the correctly configured idle instance (`baton.verifier-native holds no verify capability in None`). Separately, each ordinary worker's composition (`single_worker.worker_operations`) proves the Work its manifest names, and for a pool configured before its first Job that Work does not exist yet (bootstrap creates it when the first Job binds).

Now IDLE means "no bound Work", whether the deployment configures no capacity (the accepted zero-capacity instance) or configures workers awaiting their first Job. When idle: no receipt session is minted or authorized (no placeholder Work, no global grant), no pool is activated and no worker composition is built (the workers' preflights — engine, image, network, workspace group, control store — still run), the pooled attachment is empty with an empty principal map (the configured workers' principals are still proved by `_resolved`), and the existing durable-work guard refuses by name if the stores hold work the pool binds nothing for (zero-capacity wording for the empty case; "configures workers but binds no Job, and this instance holds work nobody is bound to serve" for the capacity case). When a Job is bound: everything is as before — the binding is read at composition, the Work exists, the sessions are minted and authorized in the bound Work's own scope BEFORE anything is dispatched or published, and a missing grant refuses by name.

## Proof (real composition/startup path, deterministic seams, no live model)

`tests/tools/test_connected_creation.TheReusableInstanceServesDefinedJobs` now continues past the repeat: (1) `stage_execution.operations_from` over the published configuration (configured implementation + review workers, zero bound Jobs) composes, `sessions is None`, one real `manager.sweep` performs no act, `status` reports `jobs: []`, and the engine stand-in recorded no call; (2) after the two real `manager create` invocations, the same composition mints every receipt session (verification, review, approval, integrator) in the bound Work's scope and `status` shows the two queued Jobs, still with no engine call; (3) with the configured verification participant replaced by a real participant that holds no `verify` grant, composition refuses naming `verify` and that participant before any dispatch or publication. Creation and composition are what this proves; no Job is run and no provider is reached.

| what | result | wall | log |
|---|---|---|---|
| the end-to-end proof | 1 OK | 0.1 s | (scratch r7.log) |
| stage_execution, connected creation, bootstrap, stack, next-run (2), single_worker | 1070 OK, 0 skipped | 379 s | `focused-r7.log` |

Supported runtime-update path for `native-labels-1` (prepared, not executed; for review first): rebuild the host bundle from this source, pass `just test-packaging`, then the instance's supported runtime update (install the corrected bundle for the retained instance per the owner's existing update tooling; no hand replacement of installed files or digests), then `just start`/`status` — expected: manager and publisher up, snapshot with `jobs: []`, no dispatch. No Job, no provider start.

## r8 — manifest provenance is bound to the documents that govern it (review 2026-11-19T06-06-42Z)

Base `093e6bbc`; candidate `sha256:e1deb2485d377046c222c3bc84833bef197fd0112b8393fdc40ba8f0bde9a5e8` over 6 paths (`CANDIDATE-SHA256-r8.txt`, `source-r8.json`, `candidate-r8.diff`, 499 lines). Nothing in `native-labels-1`, `native-labels-2`, their stores, the image or the created Job was touched.

**Trace (confirmed).** `next_run_bindings.input_manifest(None, …)` copied the installed template and bound only `work_ref`, `policy_digest`, `runtime_profile_digest`, `worker_image_digest`, `human_contract` and the source. Eleven members travelled as the template's specimen values into every composed worker: `record_binding` (isolated-agent-workers path, `dddd…`/`eeee…`), `retention_policy_digest` (`cccc…`, disagreeing with the deployment's own `0f4cd2d1…`), `credential_policy_digest`, `role_instructions_digest`, `toolchain_digest`, `mount_policy_digest`, `network_policy_digest`, `resource_policy_digest`, `tool_policy_digest`, `manifest_id`, `created_at`. `contracts.manifest` classifies the first two groups as Job intent (compared whole by `job_input_identity`) and the rest as per-worker delivery metadata; none is an arbitrary identifier.

**Correction (product-owned composition only; no bespoke launcher).**
- `next_run_bindings.deployment_bounds(...)` composes, from the same operator selections `deployment_identities` already takes, the digest of the product document governing each member: credential profile (slot→provider mapping the operator named), `tool_policy` (`provider_context.ARGV_POLICY`/`ENVIRONMENT_POLICY`, the policy the adapter embeds), `network_policy` (engine + the one approved network), `resource_policy` (runtime profile's scratch and workspace bounds), `mount_policy` (`single_worker.SOURCE_DESTINATION` + `source_boundary.source_consumption("git-line")`), `toolchain` (image reference, digest, CLI build), `role_instructions` (the selected template's own declaration of the role; implementation and review differ). `input_manifest(..., bound=)` accepts exactly `BOUND_MEMBERS` and refuses any other name; absent, the document is unchanged (template behaviour preserved).
- `pool.composed` binds those bounds plus `retention_policy_digest` = the deployment's own (`held["retention_policy_digest"]`, the value the worker's `deployment` already carries, so the two agree), `record_binding` from an explicit operator selection, `manifest_id = input-manifest-<worker_id>`, `created_at` from the clock; then `_no_specimen` refuses any composed manifest still carrying a template value for a bound member.
- **Genuine missing owner selection: the record binding.** A build cannot derive which durable record the instance's Jobs are bound to. `pool compose-worker` now requires `--record PATH` (repository-relative dossier) and reads `FINDING.md`/`PLAN.md` digests from `--checkout` (defaults to the checkout the command runs from; refused when there is none, which is the installed bundle's case, so the operator names it). Absolute/parent-relative paths and a dossier without a readable FINDING/PLAN refuse before anything is written. Recommended value for labels: `work/records/2026/08/finding-v12-work-tags/findings/finding-v12-work-label-protocol-cli` (W29401's own record; exists with FINDING/PLAN).
- `creation_ports` derivation: with per-worker identities now genuinely different between the implementation and review lanes, the whole-document agreement over the installed manifest refused every honestly composed pool. Lanes still must agree on the Job input identity (`_input_of`, the projection `contracts.manifest` defines) and on policy/task; the Job's recorded manifest is the producer lane's (the one `_correspondent` compares against and `_served_deployment` already serves each stage from its own worker's). The review lane cannot smuggle a different Job intent: the identity agreement is unchanged.

**Tests (standing authority; paths recorded).** `tests/tools/test_pool.py`: new `test_every_provenance_member_is_bound_and_none_is_a_specimen` (no member equals the template; retention equals the deployment's; exact record binding digests; manifest id/clock; credential, toolchain, network digests recomputed independently; role digest differs between implementation and review while tool/resource/mount/credential agree; refusals for absolute path, absent dossier, no checkout; nothing written); the template-resource test now asserts structure (`schema`, `version`, `extensions`, `assignment_contract`, output names) instead of equality on members that are now bound; CLI and fixtures pass `--record/--checkout`. `tests/tools/test_bootstrap.py`, `tests/tools/test_connected_creation.py`: composition helpers pass the record; the end-to-end case asserts every bound member differs from the template, the record path is the selected one and retention equals the deployment's. `tests/tools/test_creation_ports.py` unchanged and green under the producer-lane derivation.

| set | result | wall | log |
|---|---|---|---|
| pool, bootstrap repeat class, connected reusable class, creation_ports, next-run (3) | 130 OK | 29 s | (scratch r8.log) |
| pool, bootstrap, connected creation, creation_ports, job_task_delivery, job_manager creation, stack, next-run (3), stage_execution | 1059 OK, 0 skipped | 369 s | `focused-r8.log` |

**Disposition of the already-created, never-run `w29401-labels-1` on `native-labels-2` (prepared, not executed).** Its request, result and creation clock are history and stay as recorded; nothing edits the stores or changes replay. The instance records the runtime digest it was prepared with and refuses another (STACK.md: nothing upgrades a deployment in place), and a repeat refuses a binding that would change, so the corrected composition cannot reach `native-labels-2`. Supported path: (1) journal the cancellation with its reason through the installed command, no manager needed: `<native-labels-2>/… baton-v12-stack manager cancel-job --instance /home/sl/baton-instances/native-labels-2 --job w29401-labels-1 --reason "manifest provenance carried template specimen values (review 2026-11-19T06-06-42Z)"`; `cancel-status` reports the target pending while the manager stays stopped and the admission fence holds, so the Job can never dispatch; (2) after the human checkpoint of this candidate and a rebuilt packaging gate, install the corrected bundle into fresh empty `native-labels-3`, compose both workers with `pool compose-worker … --record work/records/2026/08/finding-v12-work-tags/findings/finding-v12-work-label-protocol-cli --checkout /home/sl/src/baton`, one-operand repeat, idle `start`/`status`, then the ordinary `manager create` from the unchanged `labels-job.txt`. Verify the composed manifest before the repeat: no `dddd`/`eeee`/`cccc`/repeated-character digest remains, `retention_policy_digest` equals `deployment.retention_policy_digest`, `record_binding.path` is the selected dossier. Owner decides between cancelling and retiring `native-labels-2` whole; both preserve its evidence.
