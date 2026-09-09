# Multi-Job deployment composition

Ledger Work: W119400. Logical parent: standalone stage composition, W103068.
Created by baton.codex under placement claim119392, 2026-09-08.
Canonical top-level dossier avoids adding a third child directory level to the
existing campaign. It does not alter ledger containment or move old evidence.

## Confirmed owner decision

M119126 in T115599 approves the separate successor after independent one-Job
shared-assembly acceptance. Split multi-worker configuration/pool composition
from per-Job deployment/line binding and require joined acceptance before the
pipeline proof freezes. Original proposal and evidence:
`baton:work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/review-2026-09-08T12-29-16Z.md`.
The owner ruling is pinned in that proof and the stage-composition FINDING.
It supersedes their pending placement status, not the one-Job assembly scope.

## Observed baseline and acceptance

Current stage_execution.py SHA-256
`db280363bf8e1f7bc534a25dd163275a87aad3a21d784d330801823ce9f3cb60`:
_held_workers rejects repeated roles (336/349); StageDeployment._roles (970)
collapses by role; line (976) selects one global Work/source/base; and
StageComposition._prepare (668) reaches that line without Job identity.
_pool (1190) emits only configured workers. Thus additional submitted Jobs
cannot supply simultaneous independent lines. This is a composition limitation,
not a demonstrated defect in the accepted scheduler. The one-Job candidate is
still subject to its own complete lifecycle/custody review; revalidate its final
accepted bytes before successor implementation.

Two bounded children own the correction:
`findings/finding-multi-worker-pool/` and `findings/finding-per-job-binding/`.
Their two source/test paths overlap, so implementation and independent review
are serial. Both use baton.claude through baton.impl and return to baton.bug.
The parent owns research/coordination and joined independent acceptance only.

The joined result must show through the actual factory and accepted local
manager operations: two implementation bindings can be active together;
independent review can overlap unrelated coding; a separately eligible fault
Job cannot consume the only capacity needed by the two successful Jobs;
correction reuses the correct persistent line; and integration for one target
remains serialized. Retain exact configuration, stage/attempt identities,
source/input/line/checkpoint/target correlation, and observations. Reuse accepted
scheduler/custody evidence where it answers unchanged boundaries. This local
composition acceptance does not run or substitute for the live A/B/C proof.

## Scope

Each child owns only v12/python/tools/stage_execution.py and additive controls
in v12/python/tests/tools/test_stage_execution.py. The new explicit multi-Job
configuration variant must preserve the old one-Job schema and its refusal
expectations. Exact new document members and the interface between cuts are
recorded before editing, against the accepted assembly. Changes to an external
schema, another source/test path, existing expected behavior, scheduler, driver
or provider contract require bounded disposition before that change. No runtime
or live model grant, mechanical scope-enforcement project, manual line choice,
second submission, or harness multiplexer is created by this placement.

The existing pipeline source immutability, custody, reviewer separation,
zero-ordinary-operator-transition, failure containment and successful import
requirements remain. Six slots are a proposed freeze arrangement, not a new
mandatory scheduler constant. The companion-refusal decision is separate.
