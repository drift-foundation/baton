# Owner setup and foreground execution — the FRESH successor run, W247941 / 306628

Owner reroute 306626 selects a fresh successor to the authentication-failed parallel run. This sheet
is for `two-jobs-247941-02` and replaces `OPERATOR-306505.md`, which is for the spent
`two-jobs-247941-01` and stays as that run's record.

Nothing here has been executed by me. Every path below was derived from `prepare_two_jobs.layout` and
`supported_root`, not transcribed, and the plan form of the setup was run with these exact operands
and exited 0 having performed nothing.

## 1. Why run 01 failed, from its own retained evidence

`/home/sl/baton-instances/two-jobs-247941-01/run/outcome.json` and the retained provider logs say it
exactly, and it is not a manager defect:

    admissions            implementation 2, review 0 -- BOTH implementations were admitted
    both runtimes         started, then `execution_runtime: destroyed`, `cleanup: retained`,
                          `state: absent` for each -- no residue
    both providers        answered `Failed to authenticate: OAuth session expired and could not be
                          refreshed`, `terminal_reason: api_error`, 0 input and 0 output tokens
    then                  one `KeyboardInterrupt: signal 2`, `stopped: interrupted`, `state: held`,
                          `held_because` naming both Jobs as having produced no attributed verdict
    verdicts              none

WHAT THAT DOES AND DOES NOT SHOW. The manager reached the provider TWICE, concurrently, through the
accepted path -- which is real and worth keeping. It shows nothing about overlap of actual model work,
attribution of produced content, completion or semantic acceptance, because no turn produced any.

## 2. Why a fresh run will consume current credentials, checked rather than assumed

    the registry          `/home/sl/.baton/credential-sources.json`, schema
                          `baton.user-credential-sources/1`, maps reference `w202663-development`
                          (this packet's `credential_profile`) to `/home/sl/.claude/.credentials.json`
    nothing was copied    `two-jobs-247941-01/run/credentials/credentials` and
                          `.../credential-state` are BOTH EMPTY. The run root holds no credential
                          snapshot, so a run resolves the source at launch rather than reusing a copy
                          taken at setup
    the timing            run 01 submitted at `14:33:04Z` and finished at `14:40:24Z`; the credential
                          file's mtime is `14:42:45Z`, and the owner's host provider-check completed
                          `14:43:10Z`. The file was refreshed AFTER that run ended

So the existing mechanism is what makes fresh attempts current, and no change to it is needed or made.
I read the registry's structure and the file's mtime only; no credential bytes were read or printed,
and none pass through this packet.

## 3. Setup for the fresh run — ONE command

The spent root is now in `prepare_two_jobs.CONSUMED`, so `two-jobs-247941-01` is refused as an
identity and nothing can be written into it. No reseeding and no new source commit:
`useful_tasks.py --prove` exits 0 against the source at its base.

```sh
export DOSSIER=/home/sl/src/baton/work/records/2026/09/finding-v12-real-jobs-adoption-gate
export RUN_ID=two-jobs-247941-02
export SOURCE=/home/sl/baton-runs/two-jobs-247941-01-inputs
export BASE=346a809bf0e4c47e52d881bd46d6d62a611c9816

bash "$DOSSIER/setup-two-jobs-305532.sh"            # the ordered plan; performs nothing
bash "$DOSSIER/setup-two-jobs-305532.sh" --commit    # performs it
```

The source keeps its name from the first run: it is the accepted INPUT repository, not a run root, and
reusing it is what the owner selected. The derived run root is
`/home/sl/baton-instances/two-jobs-247941-02`, which does not exist yet.

STEP 7 PRINTS THE OPERANDS THE NEXT COMMANDS TAKE, including the Authority uuid the bootstrap mints.
Prefer what it prints over anything transcribed here; they are derived the same way and should agree.

## 4. Launch — foreground, one terminal, once

```sh
env BATON_V12_STAGE_EXECUTION_CONFIG=/home/sl/baton-instances/two-jobs-247941-02/run/deployment.json \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/home/sl/baton-instances/single-job-257627-291715/manager-source/v12/python/src:/home/sl/baton-instances/single-job-257627-291715/manager-source/v12/python \
    /home/sl/.local/state/baton-v12-venv/bin/python -B \
    /home/sl/src/baton/work/records/2026/09/finding-v12-real-jobs-adoption-gate/two_job_supervisor.py \
    --deployment /home/sl/baton-instances/two-jobs-247941-02/run/deployment.json \
    --submission /home/sl/baton-instances/two-jobs-247941-02/run/submission.json \
    --job-store /home/sl/baton-instances/two-jobs-247941-02/db/jobs.sqlite3 \
    --control-store /home/sl/baton-instances/two-jobs-247941-02/db/control.sqlite3 \
    --incarnation two-jobs-two-jobs-247941-02 \
    --outcome /home/sl/baton-instances/two-jobs-247941-02/run/outcome.json \
    --total-seconds 600 --cleanup-seconds 60
```

The supervisor submits both Jobs and is the ONLY Host manager: no separate submit, no second
supervisor, no launch from the installed `distro/` binary, no automatic integration and no retry. Its
product modules come from the accepted frozen manager-source on `PYTHONPATH`; the two-Job supervisor
and its digest-bound baseline come from the dossier tree.

LIMITS ARE UNCHANGED from the agreed pair: total 600 seconds INCLUDING 60 reserved for cleanup, so
admission and serving stop at 540 and cleanup uses the remainder. Four provider admissions at most --
two implementations and two reviews. The generated submission requests `provider_turn_seconds` 180 and
`verification_command_seconds` 180 for each Job. These are cooperative bounds, not a proven hard
deadline for arbitrary blocking I/O.

## 5. Status — another terminal, AFTER launch has created the stores

```sh
env BATON_V12_STAGE_EXECUTION_CONFIG=/home/sl/baton-instances/two-jobs-247941-02/run/deployment.json \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/home/sl/baton-instances/single-job-257627-291715/manager-source/v12/python/src:/home/sl/baton-instances/single-job-257627-291715/manager-source/v12/python \
    /home/sl/.local/state/baton-v12-venv/bin/python -B -m tools.stack_command manager \
    --store /home/sl/baton-instances/two-jobs-247941-02/db/jobs.sqlite3 \
    --incarnation inspect-two-jobs-247941-02 \
    --authority-uuid <the uuid step 7 printed, also in two-jobs-247941-02/bootstrap.json> \
    status --control /home/sl/baton-instances/two-jobs-247941-02/db/control.sqlite3 \
    --observe tools.stage_execution:observing_factory
```

Supported read-only status and observation, not a second manager. BEFORE launch the Job and control
stores do not exist; their absence is not a failed Job and is not a reason to start another
supervisor. No raw SQLite inspection.

## 6. Stop

Press **Ctrl-C ONCE** in the foreground launch terminal and let the supervisor finish cancellation,
exact-runtime cleanup and outcome publication. SIGTERM is handled too, so no PID needs guessing. Do
not close the terminal, repeat the interrupt, or kill containers by name. If it does not return,
preserve the terminal output and the instance state and report the uncertainty rather than retrying.

Read the retained outcome after it exits:

```sh
cat /home/sl/baton-instances/two-jobs-247941-02/run/outcome.json
```

## 7. What this run is for, and what would NOT be success

The selected question is whether the accepted path supports CONCURRENT INDEPENDENT USEFUL JOBS and
their separate reviews. Exit 0 is not adoption acceptance, and neither is a structural check passing.

    NOT SUCCESS   a held or uncertain outcome, incomplete cleanup, a missing outcome, fewer than two
                  attributed verdicts, or content a reviewer answers `changes-requested` or
                  `rejected`. Run 01 ended `held` with no verdicts and that is exactly what it was.
    WHAT IS OWED  actual execution overlap, workspace isolation, per-Job proposal and result
                  attribution, completion with exact producer cessation, and honest INDEPENDENT
                  SEMANTIC acceptance of BOTH proposals. A checker exit is not acceptance.

Preserve the outcome and the per-Job proposal, review, attempt and runtime evidence. If this run fails
too, preserve it and return for diagnosis rather than rerunning this identity — `two-jobs-247941-02`
becomes consumed the moment it holds a run.
