# Compose multiple workers in the deployment pool

Ledger Work: W119403. Parent: ../../ (multi-Job deployment composition).
Created 2026-09-08 by baton.codex under placement claim119392.

## Confirmed boundary

Owner M119126 accepts the first result of the parent placement. Add an explicit
multi-Job configuration variant in stage_execution.py. Its worker identities,
participants/principals, role-correct launch documents, profiles and capacity
compose through the existing scheduler pool rather than a second allocator.
The old one-Job configuration remains closed and continues rejecting duplicate
roles; do not loosen that existing assertion to enable the new variant.

## Observed and proposed patch boundary

_held_workers rejects a repeated role and validates each launch document through
single_worker._held. _pool already iterates configured workers but emits only
what the former admits; factory/session validation and StageDeployment._roles
also assume singleton roles. Inspect every consumer before changing the shape.
Own only v12/python/tools/stage_execution.py and additive tests in
v12/python/tests/tools/test_stage_execution.py. Revalidate the eventual accepted
assembly, enumerate the exact new variant and internal role-to-workers interface
in this plan before editing, and preserve old one-Job behavior. No external
schema/path change or driver/scheduler modification is implicitly authorized.

## Acceptance and interface to the next cut

Use the real configuration/factory and public pool readers to show distinct
implementation workers and independent review workers survive configuration,
activation and reconstruction with intended eligible kinds/profile/capacity.
Duplicate worker identity, forbidden participant/principal role sharing, wrong
Authority and role/launch mismatch refuse before durable setup. Preserve old
variant refusal controls. Confirm accepted pool activation/replay and occupied
worker/principal exclusion without inventing a second scheduling policy.

The handoff names the exact new configuration variant and held worker/pool shape,
including how the next cut selects an eligible worker without reducing a role
to a singleton. That seam is the accepted configuration/pool shape, not an
implemented global default for every Job. Per-Job source/task/line/target binding
belongs to the next cut. Pool acceptance alone cannot claim multi-Job execution.

## 2026-09-09T18:17:21.155286+00:00 — bounded pool result accepted

review-2026-09-09T18-17-21Z.md independently accepts the exact two-file candidate under
claim129906. /2 admits multiple workers, /1 duplicate-role refusal remains,
and actual factory-to-scheduler capacity, endpoint-alias exclusion and replay
are verified. All old test methods except the justified foreign-schema selector
are AST-identical. This supersedes pending pool implementation/review.

Clarification: canonical author claim129810 is mislabeled129811 in provider
evidence. Role uniqueness never implied worker-id uniqueness; the new check
exposes the existing pool-owner rule earlier. PLAN wording that all singleton
consumers now call sole_worker is superseded: required_tests keeps its old
guard, Integration.account still chooses the first integrator, and global
Job/source/task/line/target inputs remain for W119405. Those are explicit next-cut
obligations, not a multi-Job execution or observation acceptance here.
