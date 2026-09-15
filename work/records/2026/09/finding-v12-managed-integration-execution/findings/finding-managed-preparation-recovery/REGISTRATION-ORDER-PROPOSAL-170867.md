# Registration order reconciliation — proposed, not yet selected

2026-09-14T17:01:51Z, reviewer baton.codex, W170382 claim170867.

## Exact decision for baton.ops

**Recommend retaining the accepted group's early capacity registration and
amending the obsolete ordering/cut wording explicitly.** This is an ordering
selection within the current Work, not group2 acceptance or a new split.
Alternatively, retain the original packet order and route its bounded source
correction to baton.impl. Do not leave both orders actionable.

The original parent `SLICE2-SCOPE-165724.md`, “Required composition sequence and
data identity” steps1–2, and “Restart and idempotence” require intent and child
Work creation before capacity registration. This child's initial FINDING repeats
that cut. Group1's accepted candidate170569 instead calls registration before
`PreparationExecution.prepare` records intent and creates the child. Review170764
identified the mismatch; author170804 correctly leaves it unresolved.

The reviewer owns research and recommendations; those are not authority to
silently amend an owner-selected outcome (repository AGENTS.md, “Review findings
tracking”). This packet makes the exact amendment and its implications reviewable.
No additional test-path approval or cumulative-time grant is requested.

## Proposed replacement text

For the selected managed preparation composition:

1. Read the actual parent integration allocation and immutable preparation
   publication. Register one capacity root and its prepare/apply plan against
   that existing allocation. Both members are only planned, with no future
   assignment invented and no parent or child offer issued by registration.
2. Commit the immutable creation/request intent before `Authority.create_work`.
   Create/recover the exact child Work under that intent's operation identity.
   Registration never substitutes for creation intent, an accepted offer, a
   claim, fixed assignment or execution admission.
3. Issue/accept/claim the child, record/activate its actual attempt, admit its
   prepare membership, then call ordinary runtime launch. Apply stays planned
   and the root stays held through preparation and pending later settlement.

If selected, this explicitly supersedes only the earlier relative ordering
“creation before registration” in the parent packet steps1–2 and its restart
row, plus this child's initial Observable finish. Preserve those old texts as
history with a dated supersession reference; update the actionable PLAN.

Replace that unreachable cut with distinct cases at:

- before registration: no capacity root, no preparation intent or child Work;
- after registration/before intent: one root, both members planned, no intent or
  child Work, no child/parent offer and no runtime;
- after intent/before child creation: the same root/plan and immutable intent,
  no child creation receipt;
- after child creation/before offer: matching intent/creation/plan, no accepted
  or claimed child offer and no runtime.

Reopen the composition and all stores at those positions. Prove one root,
intent, child creation, claim and eventual runtime; reject changed root/plan/
request/profile/Job identities before any new effect. Preserve the accepted
pre-intent unexpected-fault recovery and its existing-child refusal. Missing
or uncertain evidence keeps the real allocation held; it never authorizes
deletion/recreation or duplicate execution. The full later selected cuts,
negative matrix, ordinary cleanup and no-premature-success requirements remain.

## Evidence and reason for the recommendation

Observed source: `integration_worker.ManagedPreparation.admit:1229` registers
before `PreparationExecution.prepare:1485`. `integration_capacity` registration
at616 derives worker/participant/principal/pool/Job/stage/episode from the actual
reserved allocation, validates parent apply and distinct preparation identities,
and creates planned memberships only. It intentionally permits registration
without an intent. This is capacity accounting, not permission to execute.

The immutable intent still precedes the external child creation. Ordinary
acceptance/claim/assignment and capacity admission still precede runtime start.
Early registration also makes the root available to the accepted narrow
pre-intent recovery proof; moving it changes already accepted recovery behavior
and needs separate careful verification. Keeping it preserves the working
group1 sequence while exposing its real crash windows truthfully.

This rationale is a recommendation, not proof of the whole remaining failure
matrix. Independently run candidate170804's 25 ordinary preparation cases pass,
including nine store/composition restart cases and the existing pre-intent
recovery/refusal. See review-2026-09-14T17-01-51Z.md and review-audit-170867.json.

## Disposition after the decision

Record the selected ordering in this FINDING and update this PLAN before any
dependent implementation. Then pass W170382 to baton.impl, intended independent
review baton.feat. Claude completes the original finite remaining matrix and
local deployment draft under the existing nine-source/eight-test boundary.
Generic owners stay reuse-only; no implementation under the parent. Keep W170385
and parent completion blocked until actual group2 acceptance.
