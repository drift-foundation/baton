# The two selected useful tasks — immutable contracts and pinned excerpts, claim 305440

W247941 review 2026-09-29T11-58-42Z settled the selection and 12-03-33Z authorized the authoring
with no further per-edit gate. These are the tasks the pair's Jobs are held to. They are
DOCUMENTATION tasks, verified two ways that are not substitutes for each other: a DETERMINISTIC
STRUCTURAL check (`check_useful_tasks.py`) and an INDEPENDENT SEMANTIC review by a reviewer who may
answer `accepted`, `changes-requested` or `rejected`.

The historical `greet_a.py`/`greet_b.py` fixtures in `prepare_two_jobs.TASKS` stay where they are, as
the review permits: they are machinery fixtures for the 85 green checks, not the selected payload.

## Excerpts — the only sources either Job may derive from, FROZEN

W247941 review 2026-09-29T12-11-11Z: abbreviated hashes and a mutable file are not frozen inputs.
Each entry below is a full SHA-256 over exact bytes, with its repository locator and size. A Job that
asserts something absent from these has invented it, and the semantic reviewer is asked to say so.

    E1  baton:v12/DESIGN.md
        sha256 ea224a281d320077e0cc906ba91672930c8975660a453c49804dea888b92cbff, 66490 bytes
        HOST-5 at lines 432-436 and HOST-8 at lines 457-461, quoted verbatim below. The QUOTED TEXT
        is the input; the whole file is named so the quotation can be checked against it.
    E2  baton:work/records/2026/09/finding-v12-startup-failure-fresh-packet/E2E-OPERATOR-302142.md
        sha256 ce0a7c931e005af6c039978346aff5ae30044efebcf08322d9e031912385f357, 7336 bytes
        the accepted single-Job operator sheet: foreground launch, status from another terminal, one
        Ctrl-C stop, retained-outcome reading, and its own honesty clauses.
    E3  baton:work/records/2026/09/finding-v12-startup-failure-fresh-packet/EXECUTION-REVIEW-304782.json
        sha256 de48a0cdae7870d2f640377e53f4c1e1b48d5fe932af27df5efc8261ae3ed895, 2481 bytes
        the accepted single-Job execution review: attempt id, base/head, the 99-line document,
        `patch_matches_git_diff`, the sealed entry hashes and the independent verification line.
    E4  baton:work/records/2026/09/finding-v12-failed-run-resource-hold/RESIDUAL-CLASSIFICATION-304829.md
        sha256 642dba931753d2a291965fd399b468a671b60b5b5f3d8cc96e5f583ff934531a, 10129 bytes
        what is deferred outside this proof and what remains a concrete blocker if reached.

THE FIFTH IS WITHDRAWN. My first version listed this packet's own `PARALLEL-PACKET-305010.md` as an
input, and it is MUTABLE -- I have appended to it in three of the last four claims. An input a Job
derives from cannot be a document that changes under it, so it is gone rather than pinned at a value
that will not hold. Everything a Job needs from the packet's scope is in the two task requirements
below, which are frozen with this file.

THE MANIFEST BINDING AND THE DELIVERY, CORRECTED 2026-09-29 under the owner ruling
(`OWNER-SIMPLIFY-PARALLEL-PROOF-20260929.md`). These four are the finite excerpt set each Job must be
able to read, and DELIVERY is a separate fact from pinning. The paragraph here used to say the
preparation copies them into `<run root>/tasks/excerpts/` and mounts them read-only under the worker's
`/input/`. That was wrong in two ways at once: nothing in this packet arranged such a mount, so the
bytes reached no Job; and because the PREPARATION wrote them, every refusal after that point left
copies behind.

WHAT HAPPENS INSTEAD IS THE ACCEPTED SINGLE-JOB MECHANISM. That packet delivered its frozen excerpt as
a FILE IN THE NOMINATED REPOSITORY — `work/records/2026/09/finding-v12-startup-failure-fresh-packet/`
`SOURCE-EXCERPTS-20260928.md`, named repo-relative in the brief — and the worker read it through the
ordinary `sources` mount of `source`. Here the same four files, this contract and the checker are
seeded into the fixture repository under `context/w247941/` by `useful_tasks.py --seed <worktree>`,
committed by the operator, and that commit is `--base`. The preparation then only PROVES the set is
present at the digests above (`useful_tasks.present`, a read), and refuses before any effect if it is
not. The task document's own bytes remain the `human_contract`, which
`test_the_task_bytes_are_the_manifests_own_human_contract` holds. No new mount, no new delivery step
inside the preparation, and nothing written before a refusal.

E1, verbatim:

    **HOST-5.** A trusted configured host/container UID/GID arrangement is permitted.
    Validate its declared structure and report actual access failures; do not invent
    mandatory startup probe containers or recursive permission normalization. Shared
    UID/GID is an access arrangement, not the isolation boundary.

    **HOST-8.** Only one Host Worker Manager may be active for a managed workspace/DB.
    A second manager configured for that same instance MUST refuse startup with a
    clear configuration error before dispatching work or mutating managed resources.
    It MUST NOT wait as standby or take over from the active manager. Independent
    managers with separate databases and workspaces MAY run on the same machine.

## Task A — job-a, sole changed path `docs/v12-parallel-operator-notes.md`

REQUIREMENT. Write the operator's notes for running a two-Job v12 instance. Under 100 lines, UTF-8,
and the ONLY file this Job adds or alters: another development line is being written against the same
base at the same time and it owns everything else.

REQUIRED SECTIONS, by exact heading:

    ## One manager, two Jobs        one Host manager per managed workspace/DB (E1 HOST-8); two
                                   distinct Jobs, attempts and workspaces; fresh roots that reuse
                                   no spent run root.
    ## Launch                       the foreground procedure of E2, with PLACEHOLDERS for the pair's
                                   identities. Do NOT copy the spent single-Job command as runnable
                                   advice — that identity is consumed.
    ## Status                       a separate terminal, a read/observation rather than a lease or a
                                   freshness guarantee, and absence of status before the stores
                                   exist is not a failed Job.
    ## Stop                         ONE Ctrl-C in the foreground terminal, allowed to finish its
                                   accounting. Not repeated interrupts, not a killed container, not
                                   a removed directory.
    ## When the outcome is not success
                                   held, unknown and interrupted outcomes; that a stopped supervisor
                                   is not proof its producer ceased; and NO blind rerun against a
                                   spent identity.
    ## Limits, honestly             the total and its cleanup reserve are COOPERATIVE, not a proven
                                   hard deadline for arbitrary blocking host calls (E2 says this of
                                   its own 300s/60s).

FORBIDDEN: any claim of a successful parallel run, any executable command naming the spent
single-Job instance, and any statement not derivable from E1-E4.

## Task B — job-b, sole changed path `docs/v12-evidence-map.md`

REQUIREMENT. Map each adoption claim to the retained evidence that answers it, and mark honestly what
is unanswered. Under 100 lines, UTF-8, sole changed path, same reason as A.

REQUIRED SECTIONS, by exact heading:

    ## What is proved deterministically
                                   each claim beside the EXACT case that holds it, named here so the
                                   Job does not have to find them and the reviewer can check them:
                                     overlap        test_two_jobs.BothJobsAreActivelyExecutingAt
                                                    OneObservedInstant.test_both_implementations_
                                                    are_waiting_at_the_same_instant
                                     attribution    ...EachJobCollectsItsOwnFROZENAttributedVerdict
                                                    .test_both_verdicts_are_derived_from_their_own_
                                                    frozen_results
                                     disjoint work  ...ThePREPARATIONDerivesWhatItUsedToAskAnOwnerFor
                                                    .test_the_two_tasks_touch_DISJOINT_paths
                                     four and no    ...TheGateAdmitsFourAndNoMore.test_four_
                                     fifth          admissions_are_spent_and_a_fifth_is_refused
                                     bounded stop   ...TheBoundedTwoJobRunStopsAndAccountsForItself
                                                    .test_the_run_stops_at_total_minus_cleanup_and_
                                                    publishes
                                   All are in `test_two_jobs`, which passed 85/85 at claim 305440 on
                                   the frozen runtime.
    ## What one real Job proved     E3: one implementation, one proposal, the accepted document and
                                   its exact attempt identity — and that this is a SINGLE-Job fact.
    ## What is not proved yet       concurrent credential/provider reach, and any live parallel
                                   behaviour. No future success may be written as achieved.
    ## What is deferred, and why    E4's classification: legacy/helper recovery, the old-attempt
                                   packet, the broader mutation/alias matrix — outside the selected
                                   path, NOT closed.
    ## Where a claim would break    what would make the parallel proof fail: crossed identities,
                                   unknown holds, output permission errors, DB I/O on the reached
                                   path.

FORBIDDEN: presenting deterministic evidence as live evidence, presenting the single-Job success as
parallel proof, or describing anything deferred as resolved.

## How each is checked

DETERMINISTIC, by `check_useful_tasks.py` against a candidate worktree: the file exists at the exact
path, decodes as UTF-8, is under 100 lines, carries every required heading above, and the CHANGED
PATH SET for the Job is exactly its one file. It exits non-zero and names the first failure.

SEMANTIC, by the independent reviewer: whether the content is factually correct against E1-E4 and
whether anything required is missing or overstated. `accepted`, `changes-requested` and `rejected`
are all valid, and none is better for the reviewer than another. A structural pass establishes
nothing about correctness, which is why both exist.
