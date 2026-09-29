# Two-Job parallel proof — bounded packet preparation, W247941 claim 305010

Owner reroute 305000 selects preparation of the bounded two-Job parallel proof against current
DESIGN and `RESIDUAL-CLASSIFICATION-304829.md`, for independent review and owner execution. Nothing
here runs a Job, builds or deploys anything, mutates the graph or touches Git. Read with `FINDING.md`
and `PLAN.md` (both pinned today), the accepted single-Job sheet
`baton:work/records/2026/09/finding-v12-startup-failure-fresh-packet/E2E-OPERATOR-302142.md`, its
`FINAL-PACKET-302142.json` and the accepted execution review `EXECUTION-REVIEW-304782.json`.

## 1. The selection

One Host manager for the instance (HOST-8), two useful independent tasks, two Jobs with distinct
Job/attempt identities, isolated workspaces, disjoint proposal paths, and four admissions — two
implementations and two reviews — with no fifth of any kind.

The machinery already exists in this dossier and is bound to the accepted single-Job machinery it
extends:

    two_jobs.py              09f2f7ef444c   the `/2` deployment document: pool, bindings, instance
    two_job_supervisor.py    5b3045e66bd4   the four-admission gate and the bounded run
    prepare_two_jobs.py      a3141d792aa3   the preparation command that derives every operand
    test_two_jobs.py         aa9a866a9784   85 focused checks over the above

`two_job_supervisor` SUBCLASSES `baseline.AdmissionGate` from
`finding-v12-single-implementation-proof/baseline.py` rather than reimplementing a second gate; it
changes exactly one rule, `_ours`, from one Job identity to two. That is the reuse the owner asked
for: the accepted single-Job supervisor is the machinery, and this is the smallest specialization
that serves two Jobs.

## 2. What I measured today, and the one thing I changed

REVALIDATED, against the current tree:

    tests/tools/test_scheduler_trace.py    144 OK, 39.5s   two-team / four-Job contention,
                                                           eligible-slot and per-Job attribution
    tests/tools/test_execution_limits.py   142 OK, 66.6s   per-Job ceilings, composed host
                                                           verification, blocked-result holds

Both of these were FAILING under W285465 as recently as this session — `test_scheduler_trace` with
9 failures ("no configured worker prepared attempt", empty eligible-slot lists) and
`test_execution_limits` with 4. They are green now, after the W301404 `create_line` correction and
the W285465 apply/identity corrections. THAT MATTERS FOR THIS PACKET: the deterministic multi-Job
admission and attribution evidence the parallel proof leans on is currently passing, and it was not
a week ago. I am reporting the transition rather than presenting the green result alone.

CHANGED, one file, `two_job_supervisor.py`:

    `BASELINE_SHA256` advanced from `f27f3cd766f9...` to `248e570d8f9d...`.

THE PIN DID ITS JOB FIRST: it refused, because the machinery underneath had moved to the bytes the
accepted single-Job run actually used. The new value is not "whatever the file is now" — it is the
`baseline.py` recorded in `FINAL-PACKET-302142.json`, the candidate whose execution
`EXECUTION-REVIEW-304782.json` accepted. Before advancing it I checked the dependency surface rather
than assuming it: all eleven `baseline.` symbols this module uses are present in those bytes, and
`_cancel_active` still accepts the operands the supervisor passes. The previous value is retained
beside it as `BASELINE_SHA256_BEFORE_302142` so a reader can tell which generation each earlier
result was measured against.

## 3. The current state of the two-Job checks, honestly

`test_two_jobs`, run as `DECOMPOSITION-257612.md` records it (PYTHONPATH of `v12/python/src`,
`v12/python` and this dossier; no live backend):

    85 tests, 73 pass, 3 failures + 9 errors, 68.1s

The three checks the decomposition names as the parallel core were run individually:

    test_both_implementations_are_waiting_at_the_same_instant           1 OK   0.210s
    test_both_verdicts_are_derived_from_their_own_frozen_results        1 OK   0.898s
    test_the_DOCUMENTED_COMMAND_reaches_four_attempts_and_two_verdicts  1 ERROR (before the pin;
                                                                        inside the 12 below after)

So OVERLAP and PER-JOB VERDICT ATTRIBUTION currently hold on this tree. What does not yet run is the
preparation/command family.

THE 12 REMAINING, and their single measured cause: the suite composes its run roots INSIDE the
checkout, and the product's own validator correctly refuses that —

    "the configured integration_store at '/home/sl/src/baton/v12/python/v12-w71917-.../
     integration.sqlite3' is inside the checkout at '/home/sl/src/baton'; mutable deployment state
     belongs outside it"
    "run root '/home/sl/src/baton/v12/python/v12-w71917-.../two-jobs-witness' is inside
     '/home/sl/src/baton', which this deployment's own validator treats as the checkout"

This is the same condition review 2026-09-23T17-25-40Z already classified: "author external
fixture-root setup needed for reproducibility, not a product defect". It is a MISSING OPERATIONAL
REQUIREMENT of this packet, not a product blocker, and it is named as such in section 6.

I tried the obvious knob and it was wrong: `BATON_V12_DISK_ROOT=/tmp/...` made the suite fail 78 of
85 in 0.376s — that variable belongs to a different harness. I am recording the failed attempt rather
than presenting a guess as the answer; the correct external-root mechanism for THIS suite is owed.

## 4. The two useful tasks

The owner requires useful work, disjoint paths and independently reviewable proposals. The accepted
single Job wrote `docs/v12-first-job-inspection.md` (99 lines, accepted at
`EXECUTION-REVIEW-304782.json`). Proposed for the pair, each under 100 lines, each touching a file
the other does not:

    JOB A   docs/v12-parallel-operator-notes.md   — how an operator starts, inspects and stops a
            two-Job instance, derived from the accepted single-Job sheet's own procedure.
    JOB B   docs/v12-evidence-map.md              — which accepted record answers which adoption
            question, derived from this dossier's own FINDING entries.

Both are documentation-only, so neither can change product behaviour under the other's feet, and
`test_the_two_tasks_touch_DISJOINT_paths` already exists to hold that property. Their content is
independently reviewable by reading, which is what "two independently reviewed proposals" needs.

## 5. Bindings, limits and commands to be frozen

Modelled exactly on the accepted single-Job sheet, with the pair's own identities. NOT YET FROZEN —
the values below are the shape to be filled by `prepare_two_jobs.py` once section 6 is closed, and
frozen only after that:

    runtime/image/profile   the accepted selection: Claude CLI 2.1.247,
                            image sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2,
                            opus profile, bridge network
    source                  one clean checkout per Job, fresh roots, disjoint from
                            LIVE-RUN-RESIDUE-260767/262516 inventories
    identities              one Authority; one Work and one Job per task; four distinct
                            participants (two producers, two reviewers) — already asserted by
                            `test_the_four_participants_are_four_DISTINCT_identities`
    limits                  per Job: provider 180s, verification 30s; run total to be selected with
                            its cleanup reserve inside the total, as `test_the_cleanup_window_is_
                            inside_the_total` requires
    launch / status / stop  the three commands of `E2E-OPERATOR-302142.md`, with
                            `two_job_supervisor.main` in place of `baseline.py` and the pair's
                            packet; stop remains ONE Ctrl-C in the foreground terminal
    expected overlap        an observed instant with both implementations executing, from the run's
                            own records — never inferred from two submits or from test counts

## 6. Concrete missing operational requirements — CORRECTED at claim 305097

Review 2026-09-29T11-18-17Z corrected three of my five, and it was right on all three.

    M1  WITHDRAWN. `BATON_V12_DISK_ROOT` IS this harness's supported external disk operand --
        `tests/manager/disk_roots.py` consumes it, refuses memory-backed or unwritable roots, and
        otherwise defaults through candidates including the checkout. My `/tmp` failure showed that
        `/tmp` is not disk-backed storage for this fixture, not that the knob was wrong, and saying
        "wrong harness" was my error. With the already-authorized root
        `BATON_V12_DISK_ROOT=/var/tmp/baton-w257624` the suite runs: 85 tests, 78 pass, 1F+6E, 68.6s
        (my own run), and the reviewer's independent run of the documented-command selector is
        1 PASS 6.424s with four admissions, two own frozen accepted verdicts, no uncertainty, no
        held reasons, no outstanding cleanup, settled, exit 0. That case deliberately ends
        `stopped=serving-bound-exceeded`; it is not an immediate-completion proof and is not quoted
        as one here.
    M2  STANDS as a boundary, not as a blocker of this preparation: no setup is selected by 305000,
        and the repository-side work has to be finished first. That is section 5's remaining work.
    M3  RECLASSIFIED, per the review: concurrent credential and provider reach is the question a
        future selected real run answers. It is NOT a prerequisite for finishing preparation, and
        it is recorded here as the honestly unproved live question rather than a gate.
    M4  NOW THE ACTIVE ITEM, and narrower than before: see section 6b.
    M5  SUPERSEDED. I had elevated the deferred old R4 recovery matrix into a requirement to close;
        `RESIDUAL-CLASSIFICATION-304829.md` preserves it OUTSIDE the selected path and owner act
        304998 removed the broad gate. What IS required, and stays required, is the SELECTED
        two-Job stop/cancellation/uncertainty/per-Job accounting -- run on current bytes, not
        inferred from single-Job success. The supervisor's own bounded stop/accounting cases pass in
        the runs above; no historical old-attempt recovery is revived.

## 6b. The runtime rebinding, and exactly where it stands

R2 was correct: advancing `two_job_supervisor.BASELINE_SHA256` bound the supervisor and left the
PREPARATION importing `independent-review-247947`, a CONSUMED root two accepted generations back.
The seven preparation cases were refusing with the right sentence -- "this preparation derives
digests with contracts that are not the pinned ones".

DONE at claim 305097:

    `prepare_two_jobs.SNAPSHOT` is now an OPERAND (`BATON_W247941_SNAPSHOT`) defaulting to
      `/home/sl/baton-instances/single-job-257627-291715/manager-source`, the accepted single-Job
      instance's source. The old literal is preserved as `SNAPSHOT_BEFORE_302142`.
    `manager_source_files` 106 -> 126. MEASURED from `FINAL-PACKET-302142.json`'s own enumeration of
      that instance's `manager-source/` members and confirmed by counting the tree. THE REVIEW SAYS
      109; I did not adopt that number without measuring, and I am reporting the discrepancy rather
      than preferring one source silently. One of us is counting a different member set.
    `stage_execution_sha256` -> `38c4cf74db02...`, taken from the accepted manifest rather than the
      checkout. The old value is preserved beside it.
    `test_two_jobs.SNAPSHOT` now READS `prepare_two_jobs.SNAPSHOT` instead of holding a second copy
      of the same path, so the two cannot drift apart again.

MEASURED CONSEQUENCE, reported as it is: the failures MOVED rather than vanished — 85 tests, 75
pass, 5F+5E. The pin-refusal family is gone and what is now failing are the DIGEST-AGREEMENT checks
(`test_the_preflight_REFUSES_when_the_digest_pins_disagree`, `test_the_CHECK_mode_validates_and_
writes_NOTHING`, `test_every_flag_the_inspect_step_prints_is_one_the_TOOL_accepts`) plus the
preparation command family. That is the honest shape of a half-finished rebind: the remaining
`ACCEPTED` operands still carry the old campaign's provenance and must each be re-derived from the
accepted single-Job records.

STILL OWED, exactly:

    O1  re-derive the remaining `ACCEPTED` digests from accepted single-Job provenance --
        `adapter_sha256`, `adapter_digest`, `policy_digest`, `profile_digest`,
        `runtime_executable_sha256`, `runtime_path`/`runtime_build` -- each from a named record, none
        from the checkout.
    O2  reconcile the 126-vs-109 manager-source count with the reviewer before freezing the manifest.
    O3  rerun the preparation and operator-recipe families on those bytes and report exact remaining
        failures rather than assuming O1 closes them.
    O4  emit the launch/status/stop commands FROM the two-Job composer. Section 5's commands remain a
        sketch until then, which the review correctly refused to accept as emitted commands.
    O5  the immutable task documents and finite excerpt inputs of section 4 do not exist yet; a
        changing FINDING is not a pinned input, and the two names are not yet immutable tasks.

## 7. What this packet does NOT claim

It does not claim readiness, does not run or authorize a run, does not build or deploy, does not
retry or reuse anything, selects no automatic integration and no filesystem epilogue, and mutates no
graph edge. The single-Job outcome remains necessary evidence and not proof of overlap. Deterministic
provider evidence (the suites in section 2 and the checks in section 3) and real-provider evidence
(the accepted single Job) are identified separately above, and M3 states exactly what neither covers.


## 8. CURRENT STATUS at claim 305353 — sections 2, 3, 4 and 6 above are STALE

Read this section first; the ones above are the record of how the packet got here, and three of
their statements are no longer true.

    SECTION 3'S COUNT IS SUPERSEDED. The suite is 85 OK, 75.7s, run as review 2026-09-29T11-42-13Z
    specifies: the FROZEN runtime's two roots first on PYTHONPATH, the checkout's `v12/python` after
    them, `BATON_V12_DISK_ROOT=/var/tmp/baton-w257624`, cwd `/tmp`. The "12 remaining" and the
    73/85 and 75/85 figures above are history.
    SECTION 3'S `/tmp` PARAGRAPH IS WITHDRAWN. `BATON_V12_DISK_ROOT` is this harness's supported
    operand; `/tmp` is simply not disk-backed storage for the fixture. Saying it "belongs to a
    different harness" was wrong.
    SECTION 2'S DIGESTS ARE SUPERSEDED by the provenance chain now owned in `verify_247941`:
    snapshot `/home/sl/baton-instances/single-job-257627-291715/manager-source`, import roots
    `<snapshot>/v12/python/src` and `<snapshot>/v12/python`, `manager_source_files` 126,
    manifest `a8264fd390c4…`, `stage_execution_sha256` 38c4cf74db02…, `pins()` `agree: True`.
    THE SPENT ROOTS ARE NOW EXCLUDED: `CONSUMED` gained `single-job-257627-291715` (the accepted
    run's own root, whose files `EXECUTION-REVIEW-304782.json` hashes) and `w247941-witness`. I
    enumerated everything actually under `/home/sl/baton-runs` to find them rather than trusting
    the existing list.

### Section 4 is replaced: the tasks that EXIST, and the question they raise

`prepare_two_jobs.TASKS` already defines two immutable, deterministic, disjoint tasks, and they are
what the green suite exercises:

    job-a   greet_a.py   must print exactly `A-READY\n` and exit 0
    job-b   greet_b.py   must print exactly `B-READY\n` and exit 0

Each Job may touch ONLY its own file; `disjoint()` refuses otherwise and
`test_the_two_tasks_touch_DISJOINT_paths` holds it. The shared `INSTRUCTIONS` contract is delivered
to both stages of both Jobs, tells the implementation not to judge its own work, and tells the
reviewer its checkout is read-only, to RUN the file rather than read it, and that all three verdicts
are valid. `test_the_task_bytes_are_the_manifests_own_human_contract` binds those bytes to the input
manifest's `human_contract` digest, so the task is immutable by construction rather than by promise.

THE OPEN QUESTION, which is the owner's and not mine to settle: these are machine-VERIFIABLE but
they are not USEFUL WORK, and 305000 asks for two useful independent tasks. The documentation tasks
I proposed in section 4 are the reverse — useful, but a reviewer can only judge them by reading.
Either is defensible and they are not interchangeable:

    KEEP THE GREET TASKS and the proof is about parallel execution, attribution and cessation with a
    trivially checkable payload. Nothing in the packet changes; the suite is already green on them.
    MAKE THEM USEFUL and each Job's file must still be the only one it touches and must still have a
    deterministic output check, so the change is to TASKS' content and `INSTRUCTIONS`' requirement,
    not to the machinery. That is a real authoring step with its own revalidation.

I am not choosing silently. The packet stands on the existing tasks, and the substitution is named
as the selection the owner or reviewer should make.

### What is still owed, exactly

    O1  the remaining `ACCEPTED` operands -- `adapter_sha256`, `adapter_digest`, `policy_digest`,
        `profile_digest`, `runtime_path`, `runtime_build`, `runtime_executable_sha256` -- each
        re-derived from a NAMED accepted record. The runtime executable already matches its pin;
        the others still carry the earlier campaign's provenance strings, and the whole suite passes
        without exercising them against the accepted single-Job records.
    O4  the concrete repository-side recipe: the pair's limits (per-Job provider/verification
        seconds and a total with its cleanup reserve inside it), and the launch/status/stop argv
        DERIVED by the composer rather than transcribed. The mechanism is proved --
        `TheOPERATORRecipePrintsOperandsThatAGREE` passes, so the recipe's printed operands are ones
        the tool accepts -- and what is missing is the derivation for THIS pair's identities.
    O5  resolved to the question above rather than to a file: the immutable tasks exist; whether
        they are the USEFUL ones is the selection named above.

### The exact owner setup operation, named once the above closes

No operational file is claimed to exist and none is required before setup. When O1 and O4 close, the
single owner operation to select is: create the pair's instance and two clean source clones under a
FRESH root that is not in `CONSUMED`, then run `prepare_two_jobs.py` against it to EMIT the packet,
selections, task documents and the three commands. Until then there is nothing to run and nothing to
freeze, which is why this packet asks for no setup yet.


## 9. CURRENT STATUS at claim 305959 — the owner simplification, applied

`OWNER-SIMPLIFY-PARALLEL-PROOF-20260929.md` (owner, discussed in T247941/305879) and review
2026-09-29T13-08-19Z govern from here, and they supersede the accumulated instruction to build
bespoke contract, checker, mount and diff-validator layers. Section 8's open question is also SETTLED:
the useful tasks are the payload, the greeting fixture stays as machinery.

### What the ruling changed in this packet, and it made it smaller

    THE FROZEN CONTEXT NOW TRAVELS IN THE NOMINATED SOURCE. The accepted single-Job packet put its
    excerpt in the repository -- `work/records/2026/09/finding-v12-startup-failure-fresh-packet/`
    `SOURCE-EXCERPTS-20260928.md`, named repo-relative in the brief, read through the ordinary
    `sources` mount of `source`. This packet now does the same under `context/w247941/`. NO new mount
    plumbing was written, and none is needed.
    TWO DEFECTS DIED WITH ONE CHANGE. My previous version copied the excerpts into
    `<run root>/tasks/excerpts` and mounted NOTHING, so no Job could read them; and because the
    PREPARATION copied them, every refusal after that point left bytes behind. I had already moved
    that call twice for exactly that reason. `prepare_two_jobs` now calls `useful_tasks.present`,
    which is a READ, so it sits with the other refusals and there is nothing to leave behind.
    THE AUTHORITATIVE DIFF IS NOT A NEW VALIDATOR. Review 2026-09-29T13-08-19Z: existing
    proposal/custody mechanisms may prove path attribution. The product already compares the
    proposal's patch to the repository's own diff (`patch_matches_git_diff` in the accepted
    single-Job execution review, E3 of the contract), and the structural checker reports what the
    caller declares. I am not writing a second comparison, and I am not claiming the checker's
    `--changed` proves attribution by itself.
    THE EMITTED VERIFICATION CAN NOW START. It named `/input/checker/check_useful_tasks.py`; it names
    `context/w247941/checker/check_useful_tasks.py`, which is in the checkout it runs in.

### The operator commands, exactly

    # THE OPERANDS ONCE, EXPORTED -- see below for why this is not cosmetic.
    export DOSSIER=/home/sl/src/baton/work/records/2026/09/finding-v12-real-jobs-adoption-gate
    export RUN_ID=<RUN_ID>
    export SOURCE=<fixture repository>
    export BASE=<that repository's HEAD, after the seeding below is committed>

    # ONCE per fixture repository, the operator's own act:
    python3 "$DOSSIER/useful_tasks.py" --seed "$SOURCE"
    #   -> writes context/w247941/{excerpts,contract,checker}, six files, each compared to its pin
    #   -> the operator adds and commits them; THAT COMMIT IS $BASE
    python3 "$DOSSIER/useful_tasks.py" --prove "$SOURCE"     # read-only, refuses by path

    bash "$DOSSIER/setup-two-jobs-305532.sh"                # prints the ordered plan, performs nothing
    bash "$DOSSIER/setup-two-jobs-305532.sh" --commit        # performs it

WHY THEY ARE EXPORTED, and it was a real defect in the pair I printed at claim 305959: a
`NAME=value command` assignment lasts for THAT command only. I gave `RUN_ID`/`SOURCE`/`BASE` to the
plan invocation and then showed the `--commit` one bare, so an operator following it would have handed
the second command three empty operands and got "refused: RUN_ID is required; this script invents no
identity". W247941 review 2026-09-29T13-32-53Z caught it.

Step 1 of that script proves the context is present before anything is created, so a repository that
was never seeded is refused before the run root exists. Seeding and committing are the OPERATOR's acts
throughout: no agent performs a version-control mutation on the fixture.

### O1 is CLOSED at claim 306116, and here is what it actually was

Every remaining `ACCEPTED` operand carried a DECISION for provenance -- "W239528 claim 244216",
"accepted by W239533" -- rather than a record, and two of those labels named
`/home/sl/baton-runs/independent-review-248377/run/deployment.json`, a SUPERSEDED campaign's
deployment. `verify_247941.accepted()` now MEASURES each one from the accepted single Job's own
records and `verify_247941.py --pins` reports it under the same `agree`, so the command fails closed
on either pin set. What the measurement found:

    ALREADY CORRECT, now bound to a record rather than a label: `adapter_sha256` is the accepted
    packet's `worker_image.worker_files["opt/baton/claude_agent.py"]` -- the adapter source the
    executed image ran; `image_reference` and `image_digest` are `worker_image.reference` and
    `.config_digest`; `runtime_build` and `runtime_executable_sha256` are `manager_runtime`'s;
    `stage_execution_sha256` is `manager_source.files["tools/stage_execution.py"]`; the supervisor's
    `baseline.py` digest is `supervisor.sha256`; `code_boundary` is the selected snapshot.
    THE THREE DESCRIPTOR DIGESTS are read from BOTH configured workers and required to agree, which
    is what makes them the instance's descriptors rather than one worker's.
    ONE ACTUAL MISMATCH: `profile_name` said `claude-context-review` beside the accepted run's
    profile digest `93fdea4a…`, and BOTH accepted workers are configured
    `claude-fresh-implementation`. A name from one campaign beside a digest from another is exactly
    the pairing this reconciliation exists to catch, and the product does compare a line's profile
    name against the profile it is handed. The name now comes from the record the digest came from.
    THE TWO RUNTIME PATHS ARE NOT A CONFLICT. `runtime_path` is the DISTRO, the bootstrap input
    `tools.bootstrap --distro` takes; the accepted packet's `manager_runtime.path` is the INSTALLED
    copy that ran. The executable at both hashes to `04aa459a…`, so the digest is the pin and each
    path is a locator. It has to be: that runtime's build stamp records `dirty: true`, so the build
    commit alone does not identify the bytes. The emitted arrangement now carries
    `runtime_executed_path` beside `runtime_path` so a reader of the packet can tell them apart.

### Deterministic evidence at this claim

    test_two_jobs.py            96 checks, 0 failures, 77.5s -- the 89 plus SEVEN O1 cases, under
                                `-W error::ResourceWarning` with ZERO warnings printed; the six
                                unclosed-read warnings the previous review reported are gone.
                                Of those 96: FOUR CONNECTED cases drive `main --tasks useful` --
                                the selected pair emitted and attributed through
                                `prepared.jobs`/`tasks_touch`, and THREE no-effects refusals (an
                                unseeded source, a tampered member, and the create-only/changed-base
                                pair) each proved to leave no `tasks/`, no `run/` and no selections.
                                SEVEN hold O1: every pin measured, the preparation bound to the
                                measurement, the profile name and its digest from one record, the
                                two runtime paths carrying one digest, the descriptors agreeing
                                across both workers, the emitted arrangement carrying both runtime
                                facts, and `--pins` failing closed on a drifted accepted pin.
    test_useful_tasks.py        19 checks, 0 failures, 0.075s -- the 15 component checks plus the
                                brief/verification path check and the three `present` checks.
    verify_247941.py --pins     `agree: true`, `accepted_run.agree: true`, exit 0.
    useful_tasks.py --seed      six members written, each digest equal to its pin; --prove on the
                                result exits 0 and on an empty tree refuses by path with status 2.
    setup-two-jobs-305532.sh    the embedded validation program compiles and names the new proof; the
                                plan mode refuses a non-repository. THE SCRIPT HAS NOT BEEN RUN WITH
                                --commit: it installs a runtime and clones, which is the owner's
                                operational selection, not mine.

### What is still owed

    P1  the live run: implementation execution OVERLAP, isolation, per-Job proposal/result
        attribution, completion and exact producer cessation. No deterministic evidence substitutes
        for it, and it is the owner's selection.
    P2  independent SEMANTIC acceptance of both useful proposals. A structural pass or a provider
        exit is not acceptance, and this packet does not treat either as one.
    O1  CLOSED at claim 306116, above. Nothing in it remains open.


## 10. THE OWNER'S SETUP FAILED, and why — claim 306333

Owner reroute 306323, recorded here as the concrete finding it asked for. The owner selected the setup
and it failed BEFORE the run root was created.

### The finding

`setup-two-jobs-305532.sh` built its run root from a literal of its own:

    RUN_ROOT="/home/sl/baton-runs/${RUN_ID}"

and `prepare_two_jobs` REFUSES that directory. It is in `BOUNDARIES`, because the pinned validator's
rule is that mutable deployment state never lives inside the checkout, and `/home/sl/baton-runs` was
the checkout under an earlier selection. So the script proposed a root the preparation it drives could
only reject. TWO PLACES HELD ONE DECISION AND THEY DISAGREED — the same class of defect as the
manifest/Job-projection mismatch earlier in this Work, and it cost the owner a failed setup.

### The correction

One place decides now. `prepare_two_jobs.supported_root(run_id, under=None)` builds the path under the
module's own `SUGGESTED_ROOT` and validates it through `fresh()`; the script ASKS for it and holds no
run-root literal at all. `INSTANCE_ROOT` overrides the parent directory for a different disk and is
validated identically — there is no unchecked path in.

AND THE BOUNDARY IS NOW MEASURED RATHER THAN LISTED. `stage_execution._checkout()` walks three parents
up from its own file, so the boundary MOVES when the selected snapshot moves — and it has moved twice
in this Work, which is exactly how the literal went stale. `prepare_two_jobs.product_checkout()` asks
the pinned product what the checkout is in this process, and `fresh()` refuses a root inside THAT as
well as inside the campaign's historical literals. The literals are kept: they are roots that WERE the
checkout under earlier selections, and excluding them is conservative rather than wrong.

### The proposed root, CHECKED rather than assumed

    PREPARATION TIME, measured here: `product_checkout()` answers
    `/home/sl/baton-instances/single-job-257627-291715/manager-source`. The proposed root
    `/home/sl/baton-instances/two-jobs-247941-01` is not inside it, not inside either literal
    boundary, names its own run, and is not a consumed identity. `supported_root` answers it.
    RUN TIME, from the accepted run's own records rather than from a measurement of an instance that
    does not exist yet: frozen, `_checkout()` answers the DISTRO FOLDER, which after step 6 is
    `<run root>/installation-runtime`. The accepted single Job used this exact shape — runtime at
    `/home/sl/baton-instances/single-job-257627-291715/installation-runtime`, stores at
    `/home/sl/baton-instances/single-job-257627-291715/db/` — so the stores are siblings of the
    runtime rather than inside it, and the rule is satisfied by the layout the accepted run proved.

### The ONE corrected setup command, with the owner's existing inputs

No reseeding and no new source commit: `useful_tasks.py --prove` exits 0 against the owner's source at
its stated base, so the frozen context is already there.

    export DOSSIER=/home/sl/src/baton/work/records/2026/09/finding-v12-real-jobs-adoption-gate
    export RUN_ID=two-jobs-247941-01
    export SOURCE=/home/sl/baton-runs/two-jobs-247941-01-inputs
    export BASE=346a809bf0e4c47e52d881bd46d6d62a611c9816

    bash "$DOSSIER/setup-two-jobs-305532.sh"            # the ordered plan; performs nothing
    bash "$DOSSIER/setup-two-jobs-305532.sh" --commit    # performs it

    run root, derived and validated:  /home/sl/baton-instances/two-jobs-247941-01

I RAN THE PLAN FORM WITH THOSE EXACT OPERANDS, and every gate passed: the identity is one component,
the source is a repository whose HEAD IS `346a809b…`, its tree is clean, it already carries the frozen
context at the pinned digests, the pinned runtime is present, and the root validated. It printed the
seven steps and exited 0 having performed nothing. `--commit` remains the owner's selection; I did not
run it, because it installs a runtime and clones.


## 11. THE FIRST PARALLEL RUN HAPPENED, and it failed to authenticate — claim 306628

The owner completed that setup and ran it. `two-jobs-247941-01` is SPENT and is now in `CONSUMED`;
`OPERATOR-306628.md` is the successor's sheet and `OPERATOR-306505.md` stays as run 01's record.

### What run 01 established, and what it did not

From `/home/sl/baton-instances/two-jobs-247941-01/run/outcome.json` and its retained provider logs:

    admissions            implementation 2, review 0 — BOTH implementations were admitted
    both runtimes         started, then `execution_runtime: destroyed`; `cleanup: retained`,
                          `state: absent` for each, with `outstanding_cleanup` and `uncertainty` empty
    both providers        `Failed to authenticate: OAuth session expired and could not be refreshed`,
                          `terminal_reason: api_error`, zero input and zero output tokens
    then                  one `KeyboardInterrupt: signal 2`, `stopped: interrupted`, `state: held`,
                          `held_because` naming both Jobs as having produced no attributed verdict

THE MANAGER REACHED THE PROVIDER TWICE, CONCURRENTLY, through the accepted path, and cleaned up both
runtimes with no residue and no uncertainty. That is real. It establishes NOTHING about overlap of
actual model work, attribution of produced content, completion or semantic acceptance, because no turn
produced any — and a held outcome with no verdicts is exactly what section 9's "what would not be
success" describes.

### The credential mechanism, checked rather than assumed

`/home/sl/.baton/credential-sources.json` maps this packet's reference `w202663-development` to
`/home/sl/.claude/.credentials.json`. The run root's `run/credentials/credentials` and
`run/credentials/credential-state` are BOTH EMPTY, so nothing was snapshotted at setup and a run
resolves the source at launch. Run 01 submitted at `14:33:04Z` and finished at `14:40:24Z`; that
file's mtime is `14:42:45Z` and the owner's provider-check completed `14:43:10Z`. The credentials were
refreshed after that run ended, so a fresh run consumes them through the mechanism that already
exists. Nothing about it is changed here. Only the registry's structure and the file's mtime were
read; no credential bytes pass through this packet.
