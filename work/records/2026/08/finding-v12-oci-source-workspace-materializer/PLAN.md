# Plan: exact source and workspace materialization

1. [implementation-ready] Pin the Python manifest and digest representation to
   the frozen worker-control contract and current canonicalization rules.
2. [pending] Implement strict directory verification/copy and immutable Git
   revision/ref verification with private metadata.
3. [pending] Create one non-overlapping writable workspace per assignment and
   preserve read-only source evidence.
4. [pending] Add positive, negative, race, retry and cleanup regressions.
5. [pending] Record focused evidence and return for independent review.

## Review correction — 2026-08-24

Status: **changes requested**.

1. [incomplete] Finish the four known `test_boundary_inventory` failures:
   effective path/helper delegation declarations and one probe per resulting
   owned entry. Return only after the receiving inventory is green.
2. [required] Validate directory and Git sources as the frozen closed
   `directorySource` and `gitSource` fragments before reading members or
   touching the filesystem. Retain caller-local taxonomy only where explicitly
   required; do not replace complete schema validation with another manual
   member list.
3. [required] Make staged file writes complete and prove the published tree is
   the measured tree under deterministic short-write behavior.
4. [required] Refuse a pre-existing staging symlink or other foreign entry
   without following or mutating it; apply the same rule to directory and Git
   paths and keep cleanup scoped to entries this operation created.
5. [required] Add deterministic directory-component replacement coverage; a
   no-follow final file open does not stop a raced ancestor directory from
   becoming a symlink. Correct traversal against opened directory identity.
6. [required verification] Run `test_workspaces`, boundary inventory,
   dependency/text sweeps, the full source suite and locked gate. W6592's known
   failures remain separately owned, but W6631's own focused and inventory
   suites must be green before another review handoff.
7. [scope] Do not create real Git repositories: the standing no-mutating-Git
   policy includes throwaway `/tmp` fixtures. Keep transport adapter work in its
   separately scheduled component.

## Re-review correction — 2026-08-25

Status: **changes requested; items 1, 5 and 6 remain incomplete**.

1. [confirmed corrected] Frozen closed fragment validation, complete writes,
   and refusal of pre-existing staging entries pass focused coverage.
2. [still required] Replace pathname-queued traversal with opened-directory
   identity or an equivalent no-follow containment mechanism. The deterministic
   post-listing swap regression currently follows the replacement symlink and
   accepts the outside tree.
3. [still required] Finish the receiving inventory beginning with the
   non-literal owner at
   `workspaces.py:materialize_directory_source:380`, then its delegations and
   probes. Do not treat the resulting cascade as unrelated to W6631.
4. [verification] Return only when the 44-case workspace module, boundary
   inventory, dependency/text sweeps, full source suite and locked gate are
   green apart from explicitly identified concurrent failures.

## Opened-directory correction re-review — 2026-08-25

Status: **changes requested; raced descent is corrected, descriptor ownership
and inventory remain incomplete**.

1. [confirmed corrected] The post-listing ancestor replacement is refused by
   descriptor-relative, no-follow directory descent. The adjusted first-
   listing trigger preserves the race window and is green.
2. [required] Close every directory descriptor on success and refusal. `_walk`
   currently leaks each popped child handle; `_reach` leaks its opened root and
   intermediate ancestors on every successful second read. Turn both additive
   descriptor-count regressions green.
3. [still required] Add the six currently missing W6631 probes: two GitPort
   capability labels, two assignment-identity crossings, and the directory/Git
   source-document crossings. Keep W7079's separate stale `seal_refusal` probe
   attributed to W7079.
4. [required record] Append this correction and current gate state to the
   implementer-owned `PROGRESS.md`; it still says opened-directory item 5 is
   not done.
5. [verification] Rerun workspaces (now 46 cases), the boundary inventory,
   dependency/text sweeps, full source suite and locked gate. Review:
   `review-2026-08-25T00-37-54Z.md`.

## Descriptor-ownership correction re-review — 2026-08-25

Status: **changes requested; descriptor ownership is complete, inventory and
the implementer-owned record remain incomplete**.

1. [confirmed corrected] Both descriptor-count regressions and all 46 workspace
   methods pass. No further traversal-lifecycle change is requested.
2. [still required] Add one non-vacuous probe for each of the same six W6631
   pairs: the two `GitPort.__init__.repository` capability labels, the two
   assignment-identity crossings, and the directory/Git source-document
   crossings. Make both probe execution and completeness green for W6631.
3. [still required record] Append the two descriptor correction rounds, the
   remaining six probes, and actual verification state to `PROGRESS.md`; it
   still ends by saying opened-directory item 5 is not done.
4. [verification] Rerun the focused inventory gates, workspace module,
   dependency/text sweeps, full source suite and locked gate. Review:
   `review-2026-08-25T00-49-21Z.md`.

## No-op return — 2026-08-25

Status: **unchanged**. The handoff after the preceding review added none of the
six probes and did not append `PROGRESS.md`. Items 2–4 above remain the exact
next actions. Review: `review-2026-08-25T00-51-58Z.md`.

## Inventory-declaration activation review — 2026-08-25

Status: **changes requested; six probes added during review, further active
declaration failures exposed**.

1. [done by reviewer] Add and verify both GitPort-constructor capability
   probes, both assignment-identity probes, and both source-document probes.
2. [required] Implement the three missing `StatedRules` witness methods named
   by the seven W6631 Git forwarding entries, and run the witness-existence
   gate plus each witness behavior.
3. [required] Add non-vacuous probes for the seven filesystem-root crossings
   and the two `_resolved` repository-answer member crossings.
4. [required correction] Retire the unreachable `_pinned` delegations for
   `base_revision.algorithm/hex`; attribute those members to the earlier frozen
   `gitSource` document owner and probe its actual “a git source” refusal.
5. [required record] Append both descriptor rounds, the inventory corrections,
   and actual verification state to `PROGRESS.md`.
6. [verification] Make W6631's witness-existence, probe execution and probe
   completeness gates green; rerun workspaces, dependency/text sweeps, full
   source suite and locked gate with concurrent failures attributed. Review:
   `review-2026-08-25T01-01-23Z.md`.

## Partial witness return — 2026-08-25

1. [partial] The three witness methods exist; the missing-capability witness
   passes, while forwarding and component-created-placement error.
2. [required] Change the shared witness helper and second workspace lookup to
   call the `workspaces` component module's public operations. Do not depend on
   unrelated aggregator composition.
3. [still required] Complete items 3–6 from the preceding review: nine
   reachable probes, correction/probes for the two unreachable `_pinned`
   declarations, durable progress, and the focused/broader gates.
4. [next] Return only after executing each stated witness, not merely checking
   that a method with its name exists. Review:
   `review-2026-08-25T01-04-07Z.md`.

## Inventory-probe return — 2026-08-25

Status: **changes requested; declaration coverage is syntactically complete,
but eight probes and two behavioral witnesses do not execute**.

1. [required] In both inventory probe helpers and `StatedRules.deliver_revision`,
   create roots through `workspaces.assignment_workspace`.
2. [required] In `StatedRules.deliver_revision`, materialize through
   `workspaces.materialize_git_source`; then run all three W6631 witness methods.
3. [required correction] Retire the two unreachable `_pinned` delegations and
   attribute malformed `base_revision.algorithm/hex` to the earlier frozen
   Git-source document owner with a non-vacuous probe of its actual label.
4. [required] Make all eight currently failing W6631 declared probes reach
   their exact labels; recheck that `_resolved` member probes are non-vacuous.
5. [required record] Append the descriptor corrections, inventory work, and
   actual gate state to implementer-owned `PROGRESS.md`.
6. [verification] Require all three W6631 behavioral witnesses, declared-probe
   execution, completeness, and all 46 workspace methods to pass before the
   next review handoff. Review: `review-2026-08-25T01-09-06Z.md`.

## Second no-op return — 2026-08-25

Status: **unchanged**. No requested correction or durable progress update was
present. Items 1–6 in the preceding section remain the exact next actions.
Review: `review-2026-08-25T01-11-18Z.md`.

## Frozen-fragment attribution return — 2026-08-25

Status: **changes requested; attribution is corrected, execution and durable
progress remain incomplete**.

1. [done] Attribute malformed `base_revision.algorithm/hex` to the frozen
   Git-source fragment and name its behavioral witness.
2. [required] Replace every remaining `worker_manager.assignment_workspace`
   setup call in W6631 inventory helpers/witnesses with
   `workspaces.assignment_workspace`.
3. [required] Replace `StatedRules.deliver_revision`'s remaining top-level
   materialization call with `workspaces.materialize_git_source`, and use the
   component surface in the placement witness's second root lookup.
4. [required] Make the six failing declared probes and all four W6631 witness
   methods execute successfully.
5. [required record] Append all descriptor/inventory corrections and actual
   gate state to implementer-owned `PROGRESS.md`.
6. [verification] Rerun witness existence, every W6631 witness, declared-probe
   execution/completeness, and the 46 workspace methods before return. Review:
   `review-2026-08-25T01-14-13Z.md`.

## Component-surface correction review — 2026-08-25

Status: **code accepted; durable-progress correction required before signoff**.

1. [done] All component-surface helper calls, W6631 probes, stated witnesses,
   ownership attribution, and focused materializer behavior are green.
2. [attributed] The full inventory's five remaining failures belong to W6632's
   concurrent `oci.py` surface and do not reopen W6631.
3. [required record only] Append the complete descriptor and inventory
   correction history plus actual verification state to implementer-owned
   `PROGRESS.md`; mark W6631 awaiting independent review.
4. [next] Return without further code changes unless the record update itself
   exposes a discrepancy. Review: `review-2026-08-25T01-22-52Z.md`.

## Record-only no-op return — 2026-08-25

Status: **unchanged**. Code remains accepted. The sole next action is item 3
from the preceding section: append the actual delivered and verified state to
implementer-owned `PROGRESS.md`, then return. Review:
`review-2026-08-25T01-24-32Z.md`.

## Final independent review — 2026-08-25

Status: **complete and signed off**. The durable progress record now matches
the accepted implementation and evidence. W6631 may close satisfying. Review:
`review-2026-08-25T01-25-49Z.md`.
