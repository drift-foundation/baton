# Owner setup and foreground execution — `two-jobs-247941-03`, W247941 / 307388

Owner reroute 307380 selects the fresh successor using the independently accepted brief correction
(E306893). This sheet supersedes `OPERATOR-306628.md` and `OPERATOR-306505.md`, which remain as the
records of the two spent runs.

Nothing here has been executed by me. Every path was derived from `prepare_two_jobs.supported_root`
and `layout`, not transcribed, and the plan form of the setup was run with these exact operands and
exited 0 having performed nothing.

## What is different from run 02, and what is not

    CHANGED, and only this   the emitted BRIEF. It now tells the implementation to plan to the line
                             bound before writing, to EDIT rather than re-emit the whole document, to
                             count with the checker already in its checkout, to read only the part of
                             a source it needs, and that `file` is not in the image.
    UNCHANGED                the source and its base, the four frozen excerpts, the contract, the
                             checker, the runtime and image pins, the supervisor, one Host manager,
                             two implementations and two reviews, and the limits below. NO RESEEDING:
                             `useful_tasks.py --prove` exits 0 against the source at `346a809b…`.

BUDGET ADEQUACY IS UNPROVED, and this sheet does not claim otherwise. Review 2026-09-29T15-19-17Z is
right that the transcript gaps bound WALL time between a tool result and the next tool use — model
output plus harness overhead together — so "110–130 seconds of re-emission" is an inference from those
gaps rather than a measurement of model-only cost. What is measured is that three or four whole-file
rewrites happened in each turn and that both turns hit the 180-second bound. Whether the corrected
brief fits inside 180 seconds is what this run finds out.

## 1. Setup — ONE command

The two spent roots are in `prepare_two_jobs.CONSUMED`, so neither identity can be taken or written
into. `-03` is fresh and does not exist yet.

```sh
export DOSSIER=/home/sl/src/baton/work/records/2026/09/finding-v12-real-jobs-adoption-gate
export RUN_ID=two-jobs-247941-03
export SOURCE=/home/sl/baton-runs/two-jobs-247941-01-inputs
export BASE=346a809bf0e4c47e52d881bd46d6d62a611c9816

bash "$DOSSIER/setup-two-jobs-305532.sh"            # the ordered plan; performs nothing
bash "$DOSSIER/setup-two-jobs-305532.sh" --commit    # performs it
```

The source keeps its `-01` name: it is the accepted INPUT repository at the accepted base, not a run
root, and reusing it is what the owner selected.

STEP 7 PRINTS THE OPERANDS THE NEXT COMMANDS TAKE, including the Authority uuid the bootstrap mints
for this run. Prefer what it prints over anything transcribed here; both are derived the same way.

## 2. Launch — foreground, one terminal, once

```sh
env BATON_V12_STAGE_EXECUTION_CONFIG=/home/sl/baton-instances/two-jobs-247941-03/run/deployment.json \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/home/sl/baton-instances/single-job-257627-291715/manager-source/v12/python/src:/home/sl/baton-instances/single-job-257627-291715/manager-source/v12/python \
    /home/sl/.local/state/baton-v12-venv/bin/python -B \
    /home/sl/src/baton/work/records/2026/09/finding-v12-real-jobs-adoption-gate/two_job_supervisor.py \
    --deployment /home/sl/baton-instances/two-jobs-247941-03/run/deployment.json \
    --submission /home/sl/baton-instances/two-jobs-247941-03/run/submission.json \
    --job-store /home/sl/baton-instances/two-jobs-247941-03/db/jobs.sqlite3 \
    --control-store /home/sl/baton-instances/two-jobs-247941-03/db/control.sqlite3 \
    --incarnation two-jobs-two-jobs-247941-03 \
    --outcome /home/sl/baton-instances/two-jobs-247941-03/run/outcome.json \
    --total-seconds 600 --cleanup-seconds 60
```

The supervisor submits both Jobs and is the ONLY Host manager: no separate submit, no second
supervisor, no launch from the installed `distro/` binary, no automatic integration and no retry. Its
product modules come from the accepted frozen manager-source on `PYTHONPATH`; the two-Job supervisor
and its digest-bound baseline come from the dossier tree.

LIMITS, unchanged and selected for this run: total 600 seconds INCLUDING 60 reserved for cleanup, so
admission and serving stop at 540. Four provider admissions at most — two implementations and two
reviews. The generated submission requests `provider_turn_seconds` 180 and
`verification_command_seconds` 180 for each Job. These are cooperative bounds, not a proven hard
deadline for arbitrary blocking I/O.

## 3. Status — another terminal, AFTER launch has created the stores

```sh
env BATON_V12_STAGE_EXECUTION_CONFIG=/home/sl/baton-instances/two-jobs-247941-03/run/deployment.json \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/home/sl/baton-instances/single-job-257627-291715/manager-source/v12/python/src:/home/sl/baton-instances/single-job-257627-291715/manager-source/v12/python \
    /home/sl/.local/state/baton-v12-venv/bin/python -B -m tools.stack_command manager \
    --store /home/sl/baton-instances/two-jobs-247941-03/db/jobs.sqlite3 \
    --incarnation inspect-two-jobs-247941-03 \
    --authority-uuid <the uuid step 7 printed, also in two-jobs-247941-03/bootstrap.json> \
    status --control /home/sl/baton-instances/two-jobs-247941-03/db/control.sqlite3 \
    --observe tools.stage_execution:observing_factory
```

Supported read-only status and observation, not a second manager. Before launch the Job and control
stores do not exist; their absence is not a failed Job and is not a reason to start another
supervisor. No raw SQLite inspection.

## 4. Stop

Press **Ctrl-C ONCE** in the foreground launch terminal and let the supervisor finish cancellation,
exact-runtime cleanup and outcome publication. SIGTERM is handled too, so no PID needs guessing. Do
not close the terminal, repeat the interrupt, or kill containers by name.

A Ctrl-C TRACEBACK IS KNOWN and belongs to W306614, not here: if one appears, read the retained
outcome anyway rather than treating the traceback as the result. If the supervisor does not return,
preserve the terminal output and instance state and report the uncertainty rather than retrying.

Read the retained outcome after it exits:

```sh
cat /home/sl/baton-instances/two-jobs-247941-03/run/outcome.json
```

## 5. What would NOT be success, from what the two spent runs actually did

    RUN 01  both providers answered `Failed to authenticate: OAuth session expired and could not be
            refreshed`. No content, no verdicts, `state: held`.
    RUN 02  both implementations hit the 180s bound. BOTH COMMITTED exactly their own path;
            job-b's `docs/v12-evidence-map.md` (99 lines) passes the STRUCTURAL check in its retained
            checkout and job-a's (103 lines) does not. No review was ever admitted, so NEITHER
            document has been semantically judged, and a structural pass is not acceptance.

So for this run: a held or uncertain outcome, incomplete cleanup, a missing outcome, fewer than two
attributed verdicts, or content a reviewer answers `changes-requested` or `rejected` are all NOT
success. What is owed is actual execution overlap, workspace isolation, per-Job proposal and result
attribution, completion with exact producer cessation, and honest INDEPENDENT SEMANTIC acceptance of
BOTH proposals.

Preserve the outcome and the per-Job proposal, review, attempt and runtime evidence. If this run fails
too, preserve it and return for diagnosis rather than rerunning this identity — `two-jobs-247941-03`
becomes consumed the moment it holds a run.
