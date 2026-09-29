# The pair's setup recipe — exact identities, roots, limits and commands, claim 305440

W247941 review 2026-09-29T12-03-33Z: "prepare actual repository-side setup script/recipe, exact
proposed fresh identities/roots and explicit per-stage/run/cleanup limits; four provider admissions
must be visible in the eventual execution request." This is that, and nothing here is executed:
NO setup, no live engine or provider, no build, no deployment, no Git or graph mutation is performed
or authorized by this document. The owner selects the one operation in section 5.

## 1. The fresh identities

    run id            <RUN_ID>                     ONE name, e.g. `two-jobs-247941-01`. It is the
                                                   `--run-id` the setup passes and DEFAULTS to the run
                                                   root's own basename, so the two cannot disagree;
                                                   `prepare_two_jobs` derives every path and both
                                                   incarnations from it, so it is one operand rather
                                                   than several names to keep in step.
    run root          /home/sl/baton-runs/<RUN_ID>
    instance root     /home/sl/baton-instances/<RUN_ID>
    Authority         one, created by the preparation; its uuid is READ BACK from the receipt rather
                      than chosen here (`receipt_of` already does this).
    Works             <AUTH8>-W1 for job-a and <AUTH8>-W2 for job-b, derived from the Authority's
                      first eight characters by `prepare_two_jobs.main` — not authored.
    Jobs              job-a, job-b
    participants      four DISTINCT: two producers and two reviewers, already asserted by
                      `test_the_four_participants_are_four_DISTINCT_identities`.

NEITHER ROOT MAY BE A SPENT ONE. `prepare_two_jobs.CONSUMED` now lists every root under
`/home/sl/baton-runs` that holds earlier work, including `single-job-257627-291715` (the accepted
single Job's own root, whose files `EXECUTION-REVIEW-304782.json` hashes) and `w247941-witness`.
`fresh()` refuses any of them; the reviewer independently reproduced both refusals at 305418.

## 2. The four admissions, and where they are visible

`two_job_supervisor.CAPS` is `{"implementation": 2, "review": 2}` — four, and no fifth of any kind,
refused by kind at the gate rather than counted afterwards. In the execution request they appear as
four stage admissions under one orchestration: two implementation stages (job-a, job-b) and two
review stages (job-a, job-b), each with its own attempt identity.
`TheGateAdmitsFourAndNoMore` holds all of it: four spent and a fifth refused, a third Job refused
before anything is served, a stage of neither Job recorded as FOREIGN rather than as a cap refusal,
and a stopped gate admitting nothing further.

## 3. The limits, explicitly — RECONCILED against what the tools actually take

W247941 review 2026-09-29T12-11-11Z caught three errors in my first version of this section and all
three were mine. The values below are read from the code, not proposed at it:

    per stage   provider turn        180 s   verification 30 s, as the accepted single Job ran
    per run     --total-seconds      600     `two_job_supervisor.main`'s own default
                --cleanup-seconds     60     ALSO its default. My 120 was invented: the emitted
                                             command in `prepare_two_jobs` passes
                                             `"--total-seconds", "600", "--cleanup-seconds", "60"`,
                                             so serving stops at 540 s, not 480 s.

A DIFFERENT RESERVE WOULD BE A CHANGE, not a description: `--cleanup-seconds` is an operand, so an
owner may select 120, but then the EMITTED command must pass it and this document must say the code
was changed. Neither has happened, so the recipe states 60.

`test_the_cleanup_window_is_inside_the_total` and `test_a_reserve_outside_the_total_is_refused` hold
the relationship whatever the numbers are.

HONESTLY, and unchanged: the total and its reserve are COOPERATIVE. Neither is a proven hard deadline
for an arbitrary blocking host call, and a run that exceeds them ends `serving-bound-exceeded` with a
held outcome — a real result, not a failure to report.

## 4. The commands — the ACTUAL argv, corrected

My first version named a `--selections` flag the supervisor does not have. `two_job_supervisor.main`
takes exactly these, all required unless noted:

    LAUNCH   one foreground terminal, `two_job_supervisor.py` with
             `--deployment <run>/deployment.json`, `--submission <run>/submission.json`,
             `--job-store <run>/db/jobs.sqlite3`, `--control-store <run>/db/control.sqlite3`,
             `--incarnation two-jobs-<RUN_ID>`, `--outcome <run>/outcome.json`,
             `--total-seconds 600`, `--cleanup-seconds 60`. Environment:
             `PYTHONDONTWRITEBYTECODE=1` and PYTHONPATH of the frozen manager source's TWO import
             roots from `verify_247941.import_path()`. It owns submission: nothing is submitted
             separately and no second supervisor is started.
    STATUS   another terminal, `-m tools.stack_command manager --store <run>/db/jobs.sqlite3
             --incarnation inspect-<RUN_ID> --authority-uuid <AUTH> status --control
             <run>/db/control.sqlite3`. A read-only observation, not a lease; the stores do not exist
             until launch creates them and their absence before that is not a failed run.
    STOP     ONE Ctrl-C in the foreground terminal, allowed to finish its accounting. SIGTERM is
             handled too. No guessed PID, no container kill by name, no directory removal.

THE INCARNATIONS ARE THE EMITTED ONES, which my first version also got wrong: `two-jobs-<RUN_ID>`
for the run and `inspect-<RUN_ID>` for status, both derived by `prepare_two_jobs` from the run id —
not `two-jobs-247941-<SEQ>` as I wrote. `<RUN_ID>` is the `--run-id` the setup operation passes, and
every path above is the one `prepare_two_jobs.layout` derives for it, so the argv is EMITTED rather
than transcribed and `TheOPERATORRecipePrintsOperandsThatAGREE` holds that every printed flag is one
the tool accepts.

## 5. The ONE owner operation to select

`setup-two-jobs-305532.sh` IS the operation, parameterized and complete. It prints its plan and does
nothing without `--commit`, which is what makes the selection an explicit act:

    # THE OPERANDS ONCE, EXPORTED. A `NAME=value command` assignment lasts for THAT command only,
    # so giving them to the plan invocation and then running the --commit one bare would hand the
    # second command three empty operands and earn "refused: RUN_ID is required". W247941 review
    # 2026-09-29T13-32-53Z caught exactly that in my printed pair.
    export DOSSIER=/home/sl/src/baton/work/records/2026/09/finding-v12-real-jobs-adoption-gate
    export RUN_ID=<RUN_ID>
    export SOURCE=<fixture repository>
    export BASE=<that repository's HEAD, after step 0 is committed>

    # STEP 0, the operator's own, ONCE per fixture repository:
    python3 "$DOSSIER/useful_tasks.py" --seed "$SOURCE"
    #   -> then add and commit those files in $SOURCE; THAT COMMIT IS $BASE, so export it after
    python3 "$DOSSIER/useful_tasks.py" --prove "$SOURCE"    # read-only; exits 2 if anything is off

    bash "$DOSSIER/setup-two-jobs-305532.sh"                # prints the ordered plan, performs nothing
    bash "$DOSSIER/setup-two-jobs-305532.sh" --commit        # performs it

WHY STEP 0 EXISTS, and it is the owner ruling of 2026-09-29 applied rather than an extra hoop: the two
Jobs read their excerpts, this packet's contract and the checker THROUGH THEIR OWN CHECKOUT, which is
the mechanism the accepted single-Job packet used. So the frozen set has to be in the repository at
the base, and putting it there is a version-control act — the operator's, never this script's.

WHAT IT DOES, in order, and every step is the current script's rather than an earlier version's: it
validates that `<RUN_ID>` is one path component and not a consumed root (`prepare_two_jobs.fresh()`),
that `SOURCE` is a repository whose `HEAD` IS `BASE` and whose tree is clean (two read-only
interrogations of it), that it already carries the frozen context at the pinned digests
(`useful_tasks.present`), and that the pinned runtime is present; prints the ordered plan and stops
unless `--commit`; then creates ONE root, makes ONE read-only clone `source` from `SOURCE` (the only
repository act it performs, and it writes only inside the new run root), emits the bootstrap inputs,
installs the pinned runtime with `tools.bootstrap --destination <run root> --distro <pinned>`, and
runs the preparation with `--tasks useful`. THE DESTINATION IS THE RUN ROOT: `--destination` overrides
`state_root`, so an instance root and a separate run root could never have agreed, and my earlier
two-root version of this recipe was wrong. THE STORE PATHS ARE UNDER `db/`, which is
`tools.bootstrap.layout`'s rule and therefore `prepare_two_jobs.layout`'s — the earliest version of
this recipe omitted that directory and was wrong too.

THE PREPARATION'S REQUIRED OPERANDS, which the earlier version also omitted: `--run-root`,
`--source` and `--base` are all REQUIRED; `--run-id` defaults to the run root's basename and
`--operation-prefix` to `w247941-<run id>`. `--emit-bootstrap-inputs` derives the bootstrap document
and does nothing else, which is why the script runs that first.

Nothing before `--commit` produces an operational file, and this recipe claims none exists. After the
preparation, the emitted packet is what the final review reads, and the live run remains a separate
selection.

## 6. What this recipe does not settle

The per-Job provider reach for two CONCURRENT turns is unproved and is the question the run itself
answers; the accepted single Job answered it for one turn only. Deterministic evidence and real
evidence stay separately identified, here as everywhere in this packet.
