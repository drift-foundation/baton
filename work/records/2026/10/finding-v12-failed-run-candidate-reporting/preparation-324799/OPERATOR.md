# W321528 continuation preparation — claim324799

Preparation only, under E324794 and review-2026-10-18T17-35-03Z.md.
No launch recommendation or execution selection is made by this packet. Return
it to baton.bug for independent review, then fresh execution selection is required.
All earlier invocations, including M324526/run324477, are spent and preserved.

Current committed base: 372281f4a473300efb474d5a6573954c15ade367. This includes the human W321689 checkpoint;
staging freezes111 manager modules/resources and3 supervisor files from committed
objects, excluding any working-tree changes. The five retained unaccepted files
from head1bb8c162e12dbcf9bbd0f9023d867759fba5e00b reconstruct exactly at this base.
Four existing base files equal priorfba1a7fc; the fifth is absent in both bases.
PROVENANCE.json binds original run/Job/attempt, custody and reviewer hashes.

CHECKPOINT.md, TEST-CANDIDATES.log and continuation.diff carry the diagnosed
remaining work. The normal TASK.md input embeds the full retained patch and exact
14-failure log so the worker starts from the latest candidate. Only baseline.py
advanced in the preceding run; tests remain unchanged. Complete actual artifact
custody/task-association regression proof and necessary focused correction. No
scope expansion, provider probe, timeout increase or whole-suite run is proposed.

## Commands after independent review and fresh execution selection

Run from /home/sl/src/baton. Destination must not exist; preserve spent identities.
The first three commands prepare only; the fourth is the sole proposed launch.

```sh
python3 -B work/records/2026/10/finding-v12-failed-run-candidate-reporting/preparation-324799/prepare.py stage --root /home/sl/baton-instances/failed-reporting-w321528-324799
env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/sl/baton-instances/failed-reporting-w321528-324799/code/v12/python/src:/home/sl/baton-instances/failed-reporting-w321528-324799/code/v12/python python3 -B -m tools.bootstrap --inputs /home/sl/baton-instances/failed-reporting-w321528-324799/bootstrap-inputs.json --destination /home/sl/baton-instances/failed-reporting-w321528-324799/instance --distro /home/sl/baton-runs/managed-correction-236087/build/stack/out/distro --no-repositories
python3 -B work/records/2026/10/finding-v12-failed-run-candidate-reporting/preparation-324799/prepare.py bind --root /home/sl/baton-instances/failed-reporting-w321528-324799
env BATON_V12_STAGE_EXECUTION_CONFIG=/home/sl/baton-instances/failed-reporting-w321528-324799/packet/deployment.json PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/sl/baton-instances/failed-reporting-w321528-324799/code/v12/python/src:/home/sl/baton-instances/failed-reporting-w321528-324799/code/v12/python /usr/bin/python3 -B /home/sl/baton-instances/failed-reporting-w321528-324799/supervisor/baseline.py --packet /home/sl/baton-instances/failed-reporting-w321528-324799/packet/PACKET.json --incarnation failed-reporting-w321528-324799
```

Check generated packet/commands.json against the proposed launch and preserve
PREPARED.json. Start owns submission; do not also submit manually or use the
installed justfile start. One fresh Claude invocation,900s provider,30s verification,
1500s total,60s cleanup; no retry. Image baton-v12-claude-worker:w239528-244216,
config digest sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2,
CLI2.1.247, bridge network. Registry /home/sl/.baton/credential-sources.json,
claude operator-file/w202663-development. No credential read/authentication proof.
The selected question remains completing useful proposal authorship in isolated
v12; correctness checks use deterministic fixtures. This preparation does not
select another real-provider invocation.

Earlier managed target creation failed errno30. No access repair is presumed;
after selection use authorized operator access or repaired managed access for these
exact commands. The /tmp disposable authority is evidence only, never a live target.
Do not delete or overwrite a preexisting root. No direct product fallback.

## Evidence and remaining acceptance

PREFLIGHT.json: disposable stage/bootstrap/bind passed, including held_packet and
verify_imported_sources. PATCH-CHECK.json: complete reconstruction matches all five
reviewer-retained file hashes. PACKET-INPUTS.json binds all preparation artifacts.
No actual Job/attempt submitted, no provider/engine or product tests this turn.
Generated preflight artifacts remain /tmp/w321528-preflight-324799; reconstructed
input remains /tmp/w321528-patch-check-324799. No new product correctness claim.

The task requires genuine valid/missing/damaged/substituted/unreadable retained
artifact evidence, exact task id/digest/argv, no-status/unreported separation and
existing focused behaviors. Fix stale fixtures without weakening custody checks.
The fixed future supervisor/image is not running this Job: manually collect all
retained candidates on every ending even when the pinned collector omits them.
Record actual Job/attempt, execution/failure, verification, cessation/uncertainty
and cleanup separately; return exact candidate to baton.bug before integration.

Only new packet artifacts and attributable PROGRESS belong to this preparer.
Reviewer owns FINDING/PLAN/reviews/evidence. Preserve W321689 authority/disposition,
W324214 visibility and W321776 task /3 ownership; W321776 remains gated. Human Git
checkpoint follows accepted product delivery, not preparation. Proposed eventual
commit: `v12: report retained failed-run candidates and effective timeouts honestly`.

## Preserved spending

This turn product verification0s; measured preparation steps in PREFLIGHT.json and
patch reconstruction in PATCH-CHECK.json. Prior author about98s plus2.195s comparison
and73s; prior preparation about0.955s plus patch/reviewer0.2s; claim324477 bootstrap
0.459155593s, bind0.224034887s plus patch, stage unknown. Run324054 served
907.5756254049998s, run324477 served906.974666s, both timeout900s with null formal
verification. Reviewer35-test check0.003s failed14; retain worker145-test7.401s and
49-test6.741s observations without treating them as acceptance. Historical aggregate
is unknown. No budget reset or new execution permission inferred.
