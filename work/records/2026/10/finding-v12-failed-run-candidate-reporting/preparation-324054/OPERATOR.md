# Current-base continuation packet — claim324054

Prepared for independent review and a new owner live selection. NOT LAUNCHED:
no actual Job or attempt identity exists. Prior packet321530 is spent and unchanged.

Selected base d0b211b42f724c6747ebdcd8fc71885388579761 includes the accepted
W321688 checkpoint433b09d6963ca9789700849b640e242e772b9867. Stage reads all
110 manager modules/resources and three supervisor helpers via read-only Git
object lookup at that exact commit, never from the concurrent dirty product tree.
The source driver clones that commit from the nominated read-only repository.
Runtime and supervisor hashes are frozen separately from the proposed corrections.

## Proposed commands (only after new owner live selection)

From /home/sl/src/baton; the final root must not exist. Do not launch the disposable
preflight authority. These first three commands prepare only:

```sh
python3 -B work/records/2026/10/finding-v12-failed-run-candidate-reporting/preparation-324054/prepare.py stage --root /home/sl/baton-instances/failed-reporting-w321528-324054
env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/sl/baton-instances/failed-reporting-w321528-324054/code/v12/python/src:/home/sl/baton-instances/failed-reporting-w321528-324054/code/v12/python python3 -B -m tools.bootstrap --inputs /home/sl/baton-instances/failed-reporting-w321528-324054/bootstrap-inputs.json --destination /home/sl/baton-instances/failed-reporting-w321528-324054/instance --distro /home/sl/baton-runs/managed-correction-236087/build/stack/out/distro --no-repositories
python3 -B work/records/2026/10/finding-v12-failed-run-candidate-reporting/preparation-324054/prepare.py bind --root /home/sl/baton-instances/failed-reporting-w321528-324054
```

Preserve PREPARED.json and verify the generated packet/commands.json. The exact
proposed launch (generated environment and argv must agree) is:

```sh
env BATON_V12_STAGE_EXECUTION_CONFIG=/home/sl/baton-instances/failed-reporting-w321528-324054/packet/deployment.json PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/sl/baton-instances/failed-reporting-w321528-324054/code/v12/python/src:/home/sl/baton-instances/failed-reporting-w321528-324054/code/v12/python /usr/bin/python3 -B /home/sl/baton-instances/failed-reporting-w321528-324054/supervisor/baseline.py --packet /home/sl/baton-instances/failed-reporting-w321528-324054/packet/PACKET.json --incarnation failed-reporting-w321528-324054
```

One fresh Claude invocation,900s provider,30s formal verification,1500s total,
60s cleanup; no retry. Reuse image baton-v12-claude-worker:w239528-244216,
config digest sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2,
Claude CLI2.1.247, bridge network. Credential registry reference remains
/home/sl/.baton/credential-sources.json, claude operator-file/w202663-development;
no secret read or authentication claim. Start owns submission; never also submit
manually or use installed justfile start. Capture output, exact Job/attempt IDs,
outcome, cessation/uncertainty/cleanup and every retained candidate on all endings.
Do not regenerate or reuse a spent identity. SIGINT/SIGTERM requests the existing
bounded accounting; it is not proof of cessation.

## Inputs and acceptance

PROVENANCE.json binds all five prior corrected files, correction322059 and sealed
candidate2c89d3aa. The four existing paths have identical old/current base bytes;
the fifth is absent in both bases. retained.patch carries those exact bytes,
embedded in TASK.md so the worker receives them through the normal task input.
This does not import or accept them. Their remaining defects are explicit in the
task: real artifact custody and exact task/digest/argv association. Preserve failed
execution, null formal verification and unobserved acceptance independently.

Required focused verification includes test_candidates, test_baseline and the
five historical worker classes; add real artifact and actual producer/task cases.
The verification command in prepare.py includes test_candidates so new regressions
are not silently omitted. No product tests were run on the host this turn.
Historical supervisor pins and old packet remain untouched. Current packet binds
the unchanged committed runtime; its outcome may still need independent retained
artifact inspection because this Job proposes future collector bytes.

PREFLIGHT.json records successful disposable stage/bootstrap/bind, held_packet and
verify_imported_sources checks plus dry-run application of the entire input patch.
No provider/engine, live Job, product correction, acceptance or integration occurred.
Preflight root /tmp/w321528-preflight-324054 is retained, not a live target.

The real-provider question remains useful proposal authorship and prompt completion
through the adopted isolated pipeline; deterministic artifact/timeout checks prove
correctness but cannot author that proposal or prove current authentication. Old
live evidence is reused; no certification/stress campaign is selected.

Return exact immutable candidate and focused evidence to baton.bug. Independent
review precedes owner integration and the human Git checkpoint. Suggested eventual
commit: `v12: report retained failed-run candidates and effective timeouts honestly`.
W321689 ownership is disjoint; W321776 remains gated on accepted W321528.
