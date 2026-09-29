# Owner foreground execution — W247941 / 307444

Owner307442 reports completed setup and asks for these commands. Independent inspection found no concrete launch blocker. Setup is complete; do not repeat it. Run once as the ordinary host user in a foreground terminal:

```sh
env BATON_V12_STAGE_EXECUTION_CONFIG=/home/sl/baton-instances/two-jobs-247941-03/run/deployment.json PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/sl/baton-instances/single-job-257627-291715/manager-source/v12/python/src:/home/sl/baton-instances/single-job-257627-291715/manager-source/v12/python /home/sl/.local/state/baton-v12-venv/bin/python -B /home/sl/src/baton/work/records/2026/09/finding-v12-real-jobs-adoption-gate/two_job_supervisor.py --deployment /home/sl/baton-instances/two-jobs-247941-03/run/deployment.json --submission /home/sl/baton-instances/two-jobs-247941-03/run/submission.json --job-store /home/sl/baton-instances/two-jobs-247941-03/db/jobs.sqlite3 --control-store /home/sl/baton-instances/two-jobs-247941-03/db/control.sqlite3 --incarnation two-jobs-two-jobs-247941-03 --outcome /home/sl/baton-instances/two-jobs-247941-03/run/outcome.json --total-seconds 600 --cleanup-seconds 60
```

The supervisor submits both Jobs and is the only Host manager. No separate submit, second supervisor, historical distro launch, automatic integration or retry. Its modules use the accepted frozen manager-source; the reviewed two-Job supervisor and digest-bound baseline come from the dossier tree. The new bootstrap installed its historical binary under `distro/`, not `installation-runtime/`; neither is the launch command above.

From another terminal AFTER launch creates the Job/control stores:

```sh
env BATON_V12_STAGE_EXECUTION_CONFIG=/home/sl/baton-instances/two-jobs-247941-03/run/deployment.json PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/sl/baton-instances/single-job-257627-291715/manager-source/v12/python/src:/home/sl/baton-instances/single-job-257627-291715/manager-source/v12/python /home/sl/.local/state/baton-v12-venv/bin/python -B -m tools.stack_command manager --store /home/sl/baton-instances/two-jobs-247941-03/db/jobs.sqlite3 --incarnation inspect-two-jobs-247941-03 --authority-uuid 3818fb6090eb493e939a419a884756c5 status --control /home/sl/baton-instances/two-jobs-247941-03/db/control.sqlite3 --observe tools.stage_execution:observing_factory
```

This is supported read-only status/observation, not another manager. Before launch the stores do not exist; do not interpret their absence as a failed Job or start another supervisor. No raw SQLite inspection.

Stop: press **Ctrl-C once in the foreground launch terminal**. Let the supervisor finish cancellation, exact-runtime cleanup and outcome publication. Do not close the terminal or substitute repeated interrupts/name-based container kills. SIGTERM is also handled, but the foreground procedure needs no guessed PID. If it does not return, preserve terminal output and instance state and report the uncertainty rather than retrying.

Read the retained outcome after exit:

```sh
cat /home/sl/baton-instances/two-jobs-247941-03/run/outcome.json
```

The selected total is600 seconds INCLUDING60 reserved for cleanup: admission/serving stops at540, then cleanup uses the remainder. These are cooperative bounds, not a proven hard deadline for arbitrary blocking I/O. Four provider admissions maximum: two implementations and two reviews. Actual submission requests provider_turn_seconds180 and verification_command_seconds180 for each Job; the historical single-Job verification30 does not describe this generated pair. No further execution is implied by retained unknowns or holds.

Authority3818fb6090eb493e939a419a884756c5; submission-two-jobs-247941-03; job-a/3818fb60-W1 produces docs/v12-parallel-operator-notes.md; job-b/3818fb60-W2 produces docs/v12-evidence-map.md. Both use source base346a809bf0e4c47e52d881bd46d6d62a611c9816 and separate development lines. Four distinct participants baton.impl-a/review-a/impl-b/review-b. Both reviews follow their own implementation only.

Exit0 or a structural check alone is not adoption acceptance. Retain outcome and per-Job proposal/review/attempt/runtime evidence. Independently establish actual overlap, workspace isolation, attribution, completion/exact cessation and honest semantic acceptance of BOTH proposals. Held/uncertain/incomplete cleanup, missing outcome or rejected/changes-requested content is not success. Preserve evidence and return for diagnosis without rerunning this identity. The selected real-provider question is whether the accepted path actually supports concurrent independent useful Jobs and their separate reviews; fake evidence cannot establish that real execution overlap or model-produced content.

Bindings and inspection: ACTUAL-PACKET-307444.json; repository candidate REVIEW-CANDIDATE-307416.json remains unchanged. Accepted126-file source manifest and runtime pins agree. Six useful inputs match; source clone HEAD matches and status is clean. Task bytes match both stage manifests. New distro executable hash04aa459aed61704971e98b9260929b19953c41caad906e28551aae0ba457a58a. At inspection Job/control stores and outcome were absent. No setup, live operation or store read was performed by this review.

Known presentation limitation: W306614 confirms failed pipelines can keep waiting and Ctrl-C can print SupervisorInterrupted after retaining the outcome. This remains separately owned and is not a prerequisite under owner306626/306724. Preserve and inspect the outcome even if that traceback appears; it neither proves nor disproves exact runtime cessation. Run01 remains spent and untouched.

Run03 carries the accepted revised drafting brief; its actual task documents match the accepted builder exactly. Owner307380 selects unchanged limits; budget adequacy remains unproved. Run01 and run02 are spent evidence, never launch targets.
