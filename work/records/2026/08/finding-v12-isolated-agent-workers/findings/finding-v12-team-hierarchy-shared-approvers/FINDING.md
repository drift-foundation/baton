# V12 team hierarchy and shared approvers

## Parent campaign

This is a deferred M6 adoption finding under
`work/records/2026/08/finding-v12-isolated-agent-workers/`.
Its authoritative ledger item is W9901. V11 refused `baton.prompt` attaching
the child directly to W10 because only W10's resolved `baton.feat` handler may
mutate its containment. W9901 therefore remains top-level until an authorized
handler places it; the dossier and roadmap preserve its intended M6 ownership.

## Confirmed requirement — 2026-08-25

V12 needs organizational team hierarchy and principals that are not owned by
one leaf team. A single approver may oversee several related subprojects;
another leaf team may use a dedicated one-to-one approver. The authority must
preserve that these are scoped grants to one principal rather than unrelated
copies of a person under several team addresses.

Example shape:

```text
infrastructure
  orch
  tls
  uflow

product
  pc
```

An infrastructure approver may receive an approval grant over the
`infrastructure` subtree, while `pc` may bind its own approver. This hierarchy
does not place repositories inside one another and creates no Work dependency.

These node names and shapes are deployment choices. For example, Slawomir may
instead create one grouping-only `admins` node above every working team and
grant one Slawomir principal approval authority over that complete subtree.
The `admins` node need not own a repository or Work. Another deployment may
have no administrative root and use only leaf-local one-to-one approvers.
Baton supplies the model and deterministic resolution; it does not prescribe
either topology.

## Required properties

- Principals, organizational/team scopes, repositories, and routes are
  separate canonical entities.
- Organizational nodes may be grouping-only, with no repository and no owned
  Work.
- A role grant names one principal, one role, and one explicit scope.
- A shared principal has one inbox, runtime identity, availability/capacity
  view, and audit history across every scope it serves.
- Every act records both the principal and effective team/scope.
- Leaf-local one-to-one bindings remain possible.
- Resolution is deterministic and inspectable and refuses missing or
  ambiguous authority.
- Organizational ancestry never implies Work containment, dependency,
  scheduling order, repository ancestry, or filesystem access.

## Cross-team manager clarification — confirmed 2026-09-04

V12 must let one principal act as a team manager for several explicitly scoped
teams without creating or selecting a separate `<team>.member` identity for
each team. The manager has one authenticated identity, session, inbox,
capacity view, and audit history. A deployment grants that principal the
desired management roles or capabilities over one organizational node or
subtree; it may grant approval, recovery, configuration, dispatch, or a
smaller deployment-defined set without changing the principal's identity.

Each authorized operation still records the one principal, the effective team
or scope, the exercised grant, and its provenance. Cross-team management does
not make Work ownership, repositories, routes, or worker identities global,
and it does not grant authority outside the configured scope. `team manager`
is the operator-facing concept; it is not an alias-generation scheme and does
not require one durable identity per managed team.

## Historical open design questions — resolved 2026-08-25

**Superseded by the confirmed M6 baseline below.** These questions are
retained as the chronological record of what the reviewer design pass had to
rule; none remains open after Slawomir's approval in T9901 message 10740.

- Whether the organizational structure is strictly a tree or a constrained
  DAG.
- Whether a leaf binding overrides, augments, or must explicitly mask an
  inherited grant.
- How multiple approvers express alternatives versus quorum approval.
- How shared-principal capacity and absence affect routing without silently
  changing authority.
- How the TUI shows inherited versus local grants and provides one cross-team
  inbox for the principal.

These questions are intentionally deferred until M6 ordering. They are not a
reason to expand v11's team-local participant model.

## Reviewer baseline — 2026-08-25

**Observed:** the current Python v12 authority has no principal, organization,
team, repository or role records.  `authority/schema.py` stores an opaque
`work.route`, maps that route directly to a `team.member`-shaped participant in
`route_handler`, grants deployment-global capabilities directly to that same
participant, and keys the one live `claim_slot` by participant.  Workflow
receipts record only `actor`; neither the effective Work-owning scope nor the
grant that authorized the act survives in the row.

**Observed:** `authority/identity.py`, `authority/session.py`, and
`worker_manager/authority_port.py` deliberately bind a runtime session and an
assignment to one `team.member` participant.  That is the correct v11-shaped
fence, but it cannot represent one principal acting for two scopes without
minting two participant identities.  `receipt_one_per_kind` also admits only
one approval receipt per proposal, so quorum is not expressible by treating
multiple approvers as more route handlers.

**Confirmed:** the current global `claim_slot` is a useful invariant to retain
at the principal level.  One human or agent serving several scopes is still one
resource and must not acquire one live claim per spelling of its team address.
The key must change identity, not become scope-local.

**Inferred implementation boundary:** eventual adoption reaches
`authority/{schema,identity,api,core,session}.py`, the authority tests and
boundary inventory, assignment/receipt manifests, and the Worker Manager's
participant-bound port, offers, attempts, sessions, capacity and projections.
The TUI has no v12 Teams/Inbox implementation yet.  No production edit belongs
in this design Work, and M6 remains gated behind W1431/W1433.

## Proposed M6 model — approved in the confirmed ruling below

The `Proposed` labels in this section preserve its pre-approval decision
history. The complete package was subsequently approved without replacement;
the confirmed ruling after the conformance matrix is now authoritative.

### 1. Organizational structure is a strict forest

**Proposed:** each organizational scope has zero or one parent.  The accepted
configuration is a forest: unique scope ids, no cycles, no multi-parent nodes.
A node independently declares whether it may own Work, routes or repositories;
grouping-only nodes declare none of them.

A shared principal receives multiple grants when it crosses unrelated roots.
That is clearer than making the organization a DAG: every target then has one
ancestry chain, one subtree meaning, and one deterministic place to inspect
inheritance.  Cross-cutting authority remains explicit in grants instead of
being hidden in a second parent edge.

### 2. Canonical records stay separate

**Proposed records:**

- `principal(principal_id, display, state)` — one human/agent identity;
- `org_scope(scope_id, parent_scope_id, kind)` — the strict forest;
- `membership(principal_id, scope_id, relation)` — directory/roster evidence
  only, never authorization;
- `role(role_id)` — the closed role vocabulary for the accepted generation;
- `role_grant(grant_id, principal_id, role_id, scope_id, extent)` where extent
  is exactly `local` or `subtree`;
- `role_mask(mask_id, role_id, scope_id, extent)` — an explicit stop to
  ancestor inheritance;
- `route(route_id, owner_scope_id, role_id, selection_policy)`;
- `repository(repository_id, owner_scope_id, root_binding)`; and
- `approval_rule(rule_id, scope_id, mode, threshold, policy_generation)`.

Membership never implies a role.  A repository never implies an organizational
parent.  A route never invents a scope from its spelling.  Work stores both its
owner scope and route id, and configuration validation requires the route to
belong to that scope.

### 3. Inheritance augments; replacement is explicit

**Proposed:** grants applicable along the unique root-to-target chain
accumulate.  A local grant therefore augments inherited grants and never
silently overrides them.  A deployment wanting a dedicated leaf approver adds
an explicit mask for the inherited approval role at that leaf and then adds the
leaf grant.  A mask affects only the named role and extent; it grants nothing.

Resolution is order-independent: apply the nearest applicable mask boundary,
then collect applicable grants at and below that boundary.  Duplicate grants
to the same principal collapse by principal identity while retaining every
grant id as audit provenance.  Missing grants refuse.  Multiple surviving
principals are valid only under an explicit route/approval selection policy;
otherwise resolution refuses as ambiguous.

### 4. Alternatives and quorum are policy, not handler count

**Proposed:** route execution uses explicit `one-of` selection: every resolved
principal is eligible, one successful claim wins atomically, and no grant is
promoted because another principal is absent.

Approval supports `one-of`, `all-of`, and integer `threshold` rules.  The rule
and the resolved eligible-principal set are frozen at the proposal's approval
policy generation.  One principal contributes at most one approval decision to
that proposal.  `threshold=1` expresses alternatives; `threshold=N` expresses
quorum.  Conflicting decisions or an unreachable threshold remain visible and
do not synthesize approval.

This requires approval attestations separate from the one aggregate approval
outcome; expanding `receipt_one_per_kind` into multiple indistinguishable
`approval` rows would lose both the rule and whether it was satisfied.

### 5. Availability and capacity never rewrite authority

**Proposed:** eligibility is resolved entirely from accepted grants, masks and
policy.  Runtime availability and capacity are separate operational facts.
The scheduler may offer only to a currently available eligible principal, but
zero available principals produces an inspectable `no-available-principal`
condition while Work stays at its configured route.  Absence never activates a
masked grant, changes a threshold, reroutes Work, or delegates authority.

The claim slot, runtime inventory, offer state and capacity counters key on the
global principal id.  Thus one Slawomir approver has one capacity and runtime
view across every scope.  The principal's inbox is the union of obligations,
offers, approvals and attention addressed to that principal, with each row
annotated by effective scope, role and source grant.

### 6. The authority derives and records the acting scope

**Proposed:** a runtime session is bound to one principal, not to a caller-
supplied team spelling.  For every act, the authority derives the effective
scope from the target Work/proposal/route, resolves the principal's role at
that scope under the accepted policy generation, and records:

- exact principal id;
- effective scope id;
- role id;
- source grant id(s) and mask boundary;
- accepted configuration/policy generation; and
- the existing exact Work/assignment/proposal identity.

The caller never chooses `effective_scope`.  Supplying another scope cannot
broaden a principal's session.  Standalone assignment and workflow receipts
carry the derived scope so evidence remains attributable without reopening the
live configuration.

## Required conformance matrix

**Positive:**

1. one principal approves `infrastructure/orch`, `infrastructure/tls` and
   `infrastructure/uflow` through one subtree grant and appears once in the
   unified inbox/capacity projection;
2. `product/pc` masks an inherited approver and authorizes its dedicated local
   principal;
3. one-of alternatives race safely and one atomic act wins;
4. a threshold rule records independent attestations and emits one aggregate
   outcome only when the frozen threshold is met; and
5. a grouping-only root owns no Work, route, repository or filesystem root.

**Negative/race/retry:**

1. cycles, a second parent, missing parents and duplicate scope ids refuse at
   configuration acceptance;
2. membership alone, repository ownership and name-prefix similarity grant
   nothing;
3. local-plus-inherited approvers without an explicit selection rule refuse as
   ambiguous;
4. a leaf mask for `approve` does not mask `review`, sibling scopes or its own
   local grants;
5. a principal absent or at capacity remains authorized but receives no new
   offer; no substitute is invented;
6. the same principal cannot consume two quorum seats through two grants;
7. policy-generation change cannot alter the eligible set or threshold of an
   existing proposal; and
8. an exact retry replays the same principal/scope/grant authorization proof,
   while reuse after a grant or scope change collides or starts a new operation
   under the new accepted generation.

## Decision package — superseded by approval

**Superseded 2026-08-25:** this approval request was answered affirmatively in
T9901 message 10740. It originally asked to adopt the package above as one
coherent baseline:
strict forest; augment-by-default plus explicit role masks; explicit one-of or
threshold policy; principal-global capacity and inbox; availability that never
changes authority; and authority-derived scope/grant audit evidence.  A change
to any member should name the replacement rule because the pieces determine
each other's ambiguity and audit behavior.

## Confirmed M6 baseline — 2026-08-25

**Approved by Slawomir in T9901 message 10740:** adopt the complete reviewer
package without replacement:

1. organizational scopes form a strict forest; cross-root sharing is expressed
   through explicit grants to one global principal, never multiple parents;
2. principal, scope, membership, role grant, role mask, route, repository and
   approval-policy records remain separate canonical entities;
3. inherited grants augment by default, while replacement requires an explicit
   role-specific mask;
4. approval policy explicitly selects `one-of`, `all-of`, or integer
   `threshold`, with the eligible principal set and rule frozen at the
   proposal's accepted policy generation;
5. runtime, inbox, claim capacity and audit identity are principal-global;
   availability may affect offers but never rewrites authority; and
6. the authority derives effective scope from the target and records principal,
   scope, role, source grant/mask provenance and accepted generation on every
   act.

This baseline supports both one shared parent/subtree approver and dedicated
one-to-one leaf approvers as deployment choices. It does not authorize
production implementation in this design Work: schema/resolver, receipt,
scheduler/manager, conformance and Teams/Inbox implementation remains ordered
after W1431/W1433 and must be decomposed into independently reviewable M6 Jobs.

## Cross-milestone compatibility ruling — 2026-08-26

Parking W9901 defers the complete M6 hierarchy implementation and its Teams /
Inbox UX; it does **not** defer applicability of the approved model. The
baseline above is a binding architectural constraint on foundational M2-M5
work now. The purpose is to avoid completing earlier schemas, identities,
receipts, routes or runtime contracts that must later be discarded when M6 is
implemented.

Any earlier Work that touches principals/participants, organizational scope,
route ownership, repository ownership, grants, claim slots, approval receipts,
runtime/capacity or inbox identity must revalidate against W9901. It need not
implement the full hierarchy early, but it must preserve a representational
seam for global principal identity, authority-derived effective scope and
grant provenance rather than making `team.member`, actor-only evidence or a
flat team spelling irreversible.

If an active design cannot preserve that seam without guessing the later M6
schema, it stops and records a typed dependency/correction; it does not ship a
flat assumption merely because W9901 itself is parked. A bounded compatibility
audit is therefore required before foundational v12 authority/manager
contracts are treated as complete.

The earlier W1431/W1433 wording records the pre-migration schedule and is
superseded as a literal locator. In the current authority, W10 is the M6
rollout/adoption milestone and remains blocked behind W9. That ordering still
defers full feature implementation, not this compatibility constraint.

## Foundation compatibility audit outcome — 2026-08-26

W16793 completed the required source/schema audit in its bound child record.
The four-part authority/Work/participant/generation assignment remains a valid
endpoint execution fence, participant-bound sessions correctly prevent callers
from choosing an actor, opaque route spelling is usable, and absent repository,
hierarchy and Inbox models remain safely deferred.

Three flat assumptions cannot wait for M6: the authority lacks a distinct
principal, Work scope and grant-provenance decision and keys global claim
capacity by endpoint participant; the trusted Worker Manager persists and
labels execution without that principal/scope context; and the receipt schema
permits only one approval actor rather than immutable attestations plus a frozen
one-of/all-of/threshold decision. Bound provider Work W16821, W16823 and W16830
own those corrections respectively. Full forest resolution, inherited grants,
masks and Teams/Inbox UX remain deferred here. Approver obligation 16832 records
the serial scheduler edges because the reviewer has no authority to mutate
`impl`-routed Work.

## Owner delivery-model clarification — 2026-11-21

Owner confirmed this remains v12, not a renamed v13: multiple teams work concurrently across distinct Git repositories/root projects under one human operator, reusing agent capacity with explicit ownership and execution isolation. Work describes obligations and relationships; Jobs execute Work. A question can be Work without a coding Job. Advanced scheduling/hardening remains v13; migration is not a 1:1 copy or immediate dual-authority backlog.

Teams have shared internal visibility of work, findings, decisions and dependency chains; this grants no cross-team mutation authority or implicit filesystem/credential access. Team A may file a defect/request with project B. B owns triage and may decompose it or discover other work recursively. Containment is a tree; prerequisites form a separate cross-project dependency graph. Filing or containment alone does not start execution or create a dependency. Explicit satisfaction conditions distinguish response, accepted implementation, integration and usable revision; rejection/cancellation never silently count as a successful fix.

B may create clarification Work addressed to A and wait on its answer while A's feature waits on B's fix. The clarification must stay runnable independently of A's blocked feature: do not inherit the parent's blocker and deadlock the exchange. An answer satisfies only that clarification obligation, not the fix or feature. Routine answers route automatically to authorized participants; only unresolved decisions require the human.

These are confirmed requirements, not permission to redesign the approved principal/scope forest or alter live claims/dependency edges. They supersede any interpretation that full team/cross-project coordination is merely optional post-v12 work, while preserving prior identity/grant decisions and the requirement to revalidate historical milestone ordering. Before dependent implementation, reconcile current DESIGN and code with this ruling, amend DESIGN explicitly and decompose bounded outcomes. W385331 owns current clarification and subsequent discovery/dependency mechanisms; this record owns the team/project operating model and migration mapping.

## Owner priority and ambiguity ruling — 2026-11-21

Owner selected W9901 as the next planning priority after independent acceptance and checkpoint of the current W385331 clarification proof. W385331 retains discovery/dependency implementation ownership; this does not close its umbrella or silently move existing gates.

Any unresolved doubt or ambiguity affecting product/UX semantics must be escalated to Slawomir before dependent design or implementation: provide the concrete scenario, what current design settles versus leaves open, options/tradeoffs and a recommendation. Do not guess user-visible behavior to maintain momentum. Settle operator workflows (team/project selection, routing, ownership, dependency visibility, resource reuse and interruption) explicitly. Existing confirmed decisions and routine implementation details do not require repeated approval.

## Complete native workflow and execution selection — owner 2026-11-21

Owner explicitly confirms W9901 targets the complete native v12 workflow, not merely team configuration or messaging: define, route and execute Work across teams/projects; automatically deliver questions, answers, findings and review handoffs; create and resolve dependencies and resume retained work; involve the owner only for unresolved decisions. Mainline Git integration/publication remains exclusively human-owned. Completion requires an end-to-end demonstration without a human or model acting solely as a message courier; component tests alone are insufficient. Existing independent acceptance, isolation and honest failure requirements remain applicable.

Use v12 Jobs to develop this workflow, including the planning execution where supported. The absence of the completed target is not itself a reason to keep development outside v12. V11 temporarily retains the canonical W9901 record and owner decisions; this does not authorize copying the backlog or creating dual coordination authority. Identify concrete unsupported operations rather than assuming planning must run directly on the host. This supersedes M385538's default direct planning execution; codexpc first prepares the bounded native planning task using existing supported tools. No speculative semantics or broad implementation is authorized by this execution selection.

## 2026-11-21 — baton.codxpc E385541 native planning packet

M385539 execution selection revalidated. Preparation complete at evidence/native-planning-385541/REPORT.md and KICKOFF.md, task TASK.txt. Existing /3 template supports native planning and independent review; do not perform substantive planning on host. Installed source ac17a5ad/7ac02c7f cannot be replaced by manager create --source (installed only); current selected base9fa0ec37 requires the prepared fresh bootstrap/composer sequence. Latest owner ruling is carried explicitly in task statement. No live actions, product edits or new launcher. Static command/input checks passed; future installation/readiness and launch remain operator steps. Return packet to baton.decide; native planning results and later complete automatic-workflow proof remain pending.

## Owner-confirmed Work lifecycle — 2026-11-22

Owner confirms the natural lifecycle discussed during native planning: design/discussion, plan creation, independent plan review, implementation, verification/review, and integration/acceptance. These are activities of one durable Work; Jobs supply bounded agent execution. The Work conversation and decisions survive individual Jobs. Acceptance of a planning Job supplies a plan and does not close the feature Work.

Templates express activities and explicit transition conditions rather than forcing every Work through one rigid sequence. A well-defined fix may begin at implementation; a new capability can require design and plan review first. Verification occurs where needed throughout the lifecycle, including experiments, focused implementation tests and joined integration checks. Parallel implementation Jobs may follow an accepted plan where dependencies and ownership permit.

Backward paths preserve evidence and context: review corrections return to the relevant activity; unresolved design questions hold only dependent execution; separately discovered defects become separate Work with explicit blocking dependencies when needed; failing tests are diagnosed and returned to the responsible activity. No silent success, lost evidence or human/model courier is implied.

Routine transitions follow established policy automatically. Unresolved design/UX decisions reach Slawomir. Exact authority for satisfying each transition condition remains a planning decision to make explicit, not a guessed implementation detail. Human mainline Git ownership remains unchanged. This confirms the lifecycle requirements, not a new status vocabulary or authorization to implement unsettled transition semantics.

## Owner-confirmed Job versus phase — 2026-11-22

Owner explicitly confirms: Job is not phase. Every Job has phases; applicable phases differ by Job type. The user-facing Job is the durable objective, with its conversation, decisions, deliverables and overall acceptance. Phases advance that objective and have completion conditions. A child Job has a separate bounded outcome and its own phases; phase nesting must not silently manufacture separate Jobs. Dependencies may cross the Job hierarchy.

This supersedes the earlier conversational suggestion that the user must understand Work as the durable root and Job only as an execution. Preserve existing implementation identities and historical evidence: the mapping of current Work/Job/stage/attempt concepts to this user-facing model must be proposed explicitly before code or schema changes. Do not confuse these lifecycle phases with v11's scheduler phase (queued/active/block/parked). The owner has confirmed the conceptual distinction, not a concrete type catalogue, transition authority, persistence schema or migration mechanism; unresolved semantics still require owner decisions.

## Owner-selected defect Job phases — 2026-11-22

Owner selects the defect Job sequence: reproduce/diagnose -> fix -> write tests (based on the reproduction) -> review -> verify. This supersedes the earlier illustrative defect sequence that omitted explicit reproduction and test-writing phases. The regression tests derive from the reproduced defect; review evaluates the fix and those tests, followed by verification. This ruling selects the conceptual sequence, without silently choosing new persistence or transition-authority semantics.

## Owner-confirmed immutable templates and evolving Job plans — 2026-11-22

Owner confirms that multiple templates for different Job types are expected. Templates themselves are immutable. A Job begins from a specific template, but its own phase plan can evolve as work reveals new needs. Changes to that Job plan are explicit and recorded with what changed, why and who authorized it; completed work and evidence remain intact, and required acceptance cannot silently disappear.

A Job may result in one or more new templates derived from its experience. Publishing a new template preserves the originals and provenance; it does not silently alter existing Jobs or mutate the template from which they began. This supersedes any interpretation that an immutable template makes every instantiated Job phase plan immutable, or that adapting one Job edits its reusable template. Shared phase behavior remains reusable across templates. Concrete template identity/versioning, publication authority and permitted in-flight plan-change rules remain to be made explicit in planning, with unresolved product/UX decisions brought to the owner.

## Owner-confirmed model-diverse review preference — 2026-11-22

Owner confirms that future implementation and independent review should preferably use different model families, such as Claude -> Codex or Codex -> Claude. If the alternate model is unavailable, same-model review may be used as an explicitly recorded fallback in a separate context. This is a model-diversity preference with an availability fallback, not permission to omit independent review or weaken its acceptance requirements.

The current w9901-native-planning-1 Claude implementation/Claude reviewer run remains unchanged. For future Jobs, make model selection and any fallback visible in the execution record. Concrete availability criteria and fallback-selection mechanics remain to be specified without guessing unresolved product/UX semantics.

## 2026-11-22 — E385551 independent retained planning review

Candidate7a030bc0 over9fa0ec37 verified against original bundle/patch/extracted72907-byte document; SHA256 dc2c516c298f0703f626361640f2caae44670e8e62956fd17cf328fe8cd618c4. Malformed submitted verification argv independently fails compilation; intended five heading checks pass. Evidence: evidence/review-385551/provenance.json. External recovery review only, not successful native review. Verdict: retain useful research; required corrections before executable-plan acceptance. Append-only review-2026-11-22T00-28-23Z.md reconciles M385544–548, corrects the purported thin owner-answer step (existing API refuses escalation replies), separates settled requirements from five owner choices, and proposes smallest next native read-only message/escalation surface followed by authorized owner-decision→retained-continuation under W385331. Preserve unchanged deadlines and no-courier final acceptance. No repeated provider work, live action, product import or protected Git change. Return review to baton.decide; plan/spec implementation remains separately selected.

## Owner-confirmed conservative exceptional-phase analysis — 2026-11-22

Owner confirms that an exceptional phase must automatically invoke an analysis agent with the failure evidence and retained outputs. It diagnoses what happened and presents the owner with options, tradeoffs and a recovery recommendation. Initially the owner decides the recovery disposition. Analysis must not silently retry, change the Job phase plan, waive verification, discard work or turn a failure into success. Baton records the decision and performs the authorized continuation through supported transitions. Later automation of well-understood recovery cases needs a deliberate policy selection.

The failed w9901-native-planning-1 is the concrete acceptance scenario: malformed submitted verification Python caused SyntaxError before inspecting a retained planning candidate. The coordinator and codexpc manually supplied analysis/recovery review this time. In the target system, initial analysis and delivery of options/recommendations must happen automatically without an external agent or human arranging that handoff. Preserve candidate identity and original failure; prove owner decision gating and subsequent authorized recovery without duplicate execution or false success. Exact analysis-role binding, its own failure handling and concrete recovery acts still require bounded design; this ruling does not authorize arbitrary instance mutation.

## Owner-confirmed team boundary and accountable cross-team delivery — 2026-11-22

A team is a shared working domain with explicitly configured access to repositories/folders/data/tools and continuity of project knowledge across Jobs/phases. Durable team knowledge is distinct from reusable agent session context and survives model/member replacement. Access remains role-specific; knowledge visibility does not grant write/approval authority. A member does not join another team's coding sessions. Cross-team defects, feature requests and questions are normal, carried through explicit interfaces and dependencies rather than cross-team execution/context sharing.

Example: an app-team member files a compiler defect at the compiler team's public interface, without needing to know its internal members, phases or routing. The compiler team handles those internally. The request retains its submitting member, originating Job/phase and stable conversation/request identity. Replies return specifically to the submitting address in that context, not merely to a general pile of team Jobs. A response may name another reply-to for subsequent replies while preserving original request/Job/conversation links.

The responding team does not manage the caller's internal availability or escalation. The receiving team immediately resolves delivery/fallback as needed through member -> originating project responsible role -> originating team responsible role -> human operator (Slawomir). Owner confirms the operator is the final accountable endpoint. This establishes the fallback chain, not a guessed timeout for offline/busy recipients.

Every response requiring action remains an accountable obligation until explicitly resolved, with an escalation path that cannot disappear at a missing/unavailable member. Delivery or seen status alone is not resolution. Escalation preserves context and avoids duplicate ownership. Do not infer that purely informational messages require recursive acknowledgments. Concrete timers, responsible-role bindings, resolution acts and race/replay behavior remain to be specified explicitly; do not invent their semantics. The earlier proposal permitting members to participate in another team's coding work is not selected; broader project/repository cardinality is not decided by this ruling.

## Owner-selected phase-plan change authority — 2026-11-22

For now, every change to a Job's phase plan requires Slawomir's explicit approval, including changes within an otherwise accepted design and acceptance scope. An assigned agent may propose a change and an independent reviewer may assess it, but neither may authorize the phase-plan mutation. Record the proposed change, rationale and owner decision before applying it; preserve completed evidence and required acceptance.

This supersedes the proposed split in review-2026-11-22T00-28-23Z.md question 2 and the subsequent conversational recommendation that an independent reviewer could approve in-scope phase-plan revisions. Routine progression through the already approved plan remains automatic when its existing conditions are satisfied; progressing a phase is not itself a plan change. Exceptional-phase recovery retains its separately confirmed owner-decision gate. This conservative authority stays in force until explicitly superseded.

## Owner-selected template publication authority — 2026-11-22

For now, publishing any new reusable template requires Slawomir's explicit approval. Agents may propose a template with review evidence; neither a designated maintainer nor an independent reviewer may authorize publication in place of the owner. This supersedes review-2026-11-22T00-28-23Z.md question 4's recommendation of scoped maintainer plus independent-review publication authority. Templates remain immutable, new templates preserve provenance, and publication never silently changes existing Jobs. This conservative authority remains until explicitly superseded; ordinary instantiation of an already approved template is not template publication.

## Owner-selected open cross-team intake — 2026-11-22

Owner confirms that any team may file a defect, feature request or question through another team's public interface. The receiving team owns triage. Filing alone grants no repository/data/credential access, authorizes no cross-team coding, starts no execution and creates no implicit dependency. Preserve the specific submitter return address, originating Job/request context, reply-to support and receiving-team escalation through to the operator.

This selects open internal intake rather than requiring individual destination-team consent or a separate grant decision for each filing. It supersedes any interpretation of review-2026-11-22T00-28-23Z.md question 3 that makes per-team intake permission an owner decision for ordinary cross-team requests. Supported identity validation and explicit configured intake authority must represent this selected policy; membership alone still grants no unrelated capability. Exact answer-role resolution remains distinct from permission to file.

## Owner-selected wait for busy alternate reviewer — 2026-11-22

When the preferred alternate model family for independent review is busy, the Job waits rather than automatically falling back to the implementation's model family. Owner should be able to intervene and reassign, with the concrete operator reassignment capability potentially delivered later. Busy capacity is not actual unavailability. This supersedes review-2026-11-22T00-28-23Z.md question 5's proposed bounded-wait-then-fallback policy for busy reviewers: elapsed waiting alone does not authorize that fallback.

The prior permission for a disclosed separate-context same-model fallback when the alternate model is actually unavailable remains distinct; its detection and authority are not further selected here. No silent reset of admitted execution deadlines or bypass of claim/independence rules is authorized by waiting or reassignment. Preserve the original assignment and reasons in the eventual supported reassignment record; this ruling does not claim the intervention interface already exists.

## Owner-selected shared subscription pools and manual failover — 2026-11-22

Owner clarifies the separation between team/project and agent capacity. One team per project is the current useful mental model for addressing responsibility; it does not permanently allocate one agent to that team. Shared pools can supply agents to any eligible project/team. Pool identities such as codex-1-pool, codex-2-pool and claude-1-pool represent separate subscriptions/accounts/plans, each capable of multiple concurrent agents. Assigned workers prefer compatible team/project context reuse; stickiness is a scheduling preference, not permanent reservation. This supersedes any reading of the earlier team execution boundary that permanently pins an underlying worker resource to one team. Team-specific identity/access/context remain bounded on each assignment; reassignment does not implicitly share another project's session or credentials.

Owner selects initially “infinite” pools as an empirical starting point: no Baton-imposed per-pool concurrency cap, not unlimited provider or host capacity. Existing isolation, ownership, independent review and per-execution limits remain applicable. Collect pool-attributed concurrency, provider refusal/throttling, waiting/completion time and context-reuse observations to inform later scheduling. Do not invent one-agent-per-project allocation or claim advanced capacity scheduling is already implemented.

If a pool exhausts credits/tokens or its provider is down, work must be transferable to another pool to preserve progress. The operator may select a same-vendor pool or a standby pool with a weaker model. Model diversity is a preference, not an obstacle to this explicitly selected fallback; independent reviewer identity/context and required acceptance remain mandatory. Preserve Job/phase identity, progress and evidence; reuse provider context only when compatible, otherwise use a durable checkpoint. Prior execution must be stopped or fenced before replacement execution. An unavailable pool is not itself proof that its executing processes have ceased.

For now, switching pools is NEVER automatic. Baton reports the unavailable pool and may recommend alternatives; Slawomir directs which replacement pool to use. No automatic choice of another subscription, provider or weaker model is authorized. This is distinct from merely waiting for busy alternate-review capacity, which remains the selected behavior. Exact availability classification, scope of a reassignment (selected execution versus a wider pool allocation), supported resume mechanics and failure reporting need explicit bounded design; do not guess them or reset admitted deadlines. No current Job, credentials, instance configuration or pool assignment is changed by this ruling.

## Owner-selected pause-first pool incident handling — 2026-11-22

Owner observes that provider trouble seen by one agent commonly indicates trouble affecting its subscription pool. Treat such a provider/pool-related signal as reason to investigate the pool, not automatically as an isolated Job defect or proof that every active execution failed. The initial response to a transient provider refusal such as “busy, please try again later” is to pause the affected work and allow roughly a minute or two before taking further action; do not immediately abandon the pool or switch providers.

If the problem persists, owner intends to retire the affected pool from service and reassign its work elsewhere. This is pool-wide operational recovery rather than always moving only the initially failing Job. The prior manual-failover ruling remains: Slawomir directs the replacement pool; no automatic switching. “Scrap the pool” does not authorize deleting retained work, evidence or credentials, or assuming running executions stopped. Preserve execution attribution, progress, cessation/fencing and recovery safeguards. Exact grace duration, persistence/recheck criteria, admission suspension and treatment of still-healthy executions remain to be settled explicitly. A grace period alone authorizes neither duplicate dispatch nor silent deadline reset.

## Owner-confirmed queue admission versus execution capacity — 2026-11-22

Owner confirms that assignments continue entering a pool's queue during provider trouble; slow draining or queue growth is not itself a reason to stop assigning. Transient provider refusal pauses affected execution without automatically suspending queue admission, moving work or reassigning the pool. The operator observes queue growth, oldest waiting work and provider trouble, and decides when to reallocate. This supersedes the proposed automatic admission hold for a suspect pool; that hold is not selected.

Queue admission and execution capacity are separate. This model also supports future bounded pools: continue accepting assignments, but enforce the configured concurrent-execution limit when starting work. A concurrency limit is not a queue-size limit or a one-agent-per-team allocation. Initial pools still have no Baton-imposed per-pool concurrency cap; later bounded capacity is an extension, not an implementation claim or an implicit cap selected here. Existing ownership/isolation and independent-review constraints remain applicable. Queue placement does not itself grant a live execution claim or authorize dispatch.

## Owner-confirmed pool throttling and reviewer reassignment — 2026-11-22

For scheduling, an unavailable pool has effective execution capacity zero: assignments may queue, but new execution does not start. Preserve configured capacity separately from availability; zero capacity is not evidence of cessation for existing executions. A pool may also have an operator-selected temporary concurrency limit to conserve credits while continuing work at lower throughput. Throttling does not remove the pool, its assignments or retained context. Initial uncapped pools and future bounded capacity remain distinct from automatic credit-based tuning, which is not selected.

Owner confirms that reviewer responsibility is separate from the execution provider/model. The operator can reassign an individual review from a Codex pool to a Claude pool when Codex is unavailable, without requiring every Job in the old pool to move. Preserve Job, phase, exact candidate, instructions and prior evidence. Reuse context only if compatible; otherwise supply a durable handoff. If Claude also performed implementation, independent review still uses a separate identity/context; record the owner-selected same-model fallback and preserve acceptance requirements. Safe cessation/fencing and attribution remain required for replacement execution. No automatic switching is authorized.

This supplements pool-wide retirement/reassignment as another explicit operator scope, not an inferred mass move. Concrete limit-change handling for already-running executions remains to be specified; merely configuring lower capacity does not authorize killing them. No live pool limit or review assignment is changed by this ruling.

## Owner clarification — provider reassignment applies to all roles, 2026-11-22

The operator-directed provider/pool reassignment rule is general, not review-specific. It applies to design, planning, coding, review, testing, failure analysis and other agent responsibilities. Review was an example only. Responsibility and its authority are separate from the supplying provider/model/pool. Reassignment retains the Job/phase, task and acceptance, progress and attributable evidence; uses compatible context or durable handoff; and observes execution cessation/fencing before replacement. Role-specific constraints, including independent review, remain intact. No automatic switch, additional authority or silent phase-plan change follows from changing the supplying pool.

## Owner-selected non-preemptive capacity reduction — 2026-11-22

When pool concurrency is reduced, always let already-running agents finish. A lower limit affects only new starts: hold them until current usage is below the selected limit; at zero, start none. Never interrupt, evict or kill running execution merely to meet a reduced pool capacity. Queue admission remains unchanged. This resolves the previously open limit-change treatment of active executions. Existing execution deadlines and explicit cancellation remain separate; this is not permission to extend an admitted execution limit or ignore its outcome.

## Owner-selected non-preemptive pool reassignment — 2026-11-22

Owner confirms that pool-work reassignment moves queued work to the selected replacement pool while healthy running agents finish in their original pool. Do not interrupt or launch a replacement for a healthy active execution merely because its pool's queued work was reassigned. Preserve exact assignment/result attribution. Failed or interrupted executions remain subject to the separate analysis and owner-approved recovery process, with cessation/fencing before replacement execution. This complements non-preemptive capacity reduction and resolves the queued-versus-healthy-running reassignment distinction. It does not silently determine the destination of future assignments or authorize automatic pool switching.

## Owner-selected persistent pool redirection — 2026-11-22

Owner confirms pool redirection is permanent unless explicitly changed again. It redirects queued work and new assignments to the selected replacement pool; recovery of the original provider does not automatically revert it. Keep the active redirect visible and its changes attributable. Healthy agents already running in the original pool finish there, under the prior non-preemptive reassignment ruling. Exceptional executions retain the separate owner-approved recovery path. This resolves the previously open future-assignment routing question; it does not authorize automatic failover/failback or alter any live pool in this record.

## Owner-selected pool redirection scope precedence — 2026-11-22

Owner selects project > team > global scope precedence for pool redirection: use the most specific applicable redirect, project before team before global. A project-scoped redirect affects that project's work, a team-scoped redirect applies to the team's work absent an applicable project override, and a global redirect supplies the fallback absent either more-specific rule. This resolves the prior ambiguity about implicit pool-wide redirection; global effect must be selected explicitly rather than inferred from a scoped change.

All earlier redirect rules remain: operator-selected, persistent until explicitly changed, visible and attributable, queued and future assignments affected, no automatic failback, healthy running agents finish in their original pool, and exceptional recovery has its own owner gate. Scope precedence neither grants cross-team execution/access authority nor changes the separate project/team organizational model. Concrete configuration representation and rejection of ambiguous/cyclic redirect arrangements require bounded design; no live redirect is installed here.

## Owner-confirmed provider/model pool options and deliberate deferral — 2026-11-22

Owner confirms a resource pool identifies provider and subscription/account and declares available model options. Each option has distinct capability/availability information, including a reset time when known; an assignment records the selected pool and model. A model-specific limit must not automatically be labelled whole-pool exhaustion. The operator may choose another model within the same pool, another pool, or deliberately defer work until the preferred stronger model becomes available. Deferred work preserves progress and context; unrelated eligible work can proceed, while work dependent on its result waits.

Changing model OR pool remains the owner's decision for now, including a same-model-family review fallback that does not change pools. This latest explicit confirmation resolves the authority ambiguity described by K's review F4; there is no automatic downgrade or model switch. Preserve independent-review identity/context, acceptance and compatible-context checks. The reported manual Fable-to-Opus change during K's review illustrates model selection within available capacity, not a verified provider capability catalogue or proof of portable session context. No live configuration is changed here.

## Owner-selected provider-problem disposition — 2026-11-22

When provider/model trouble is reported, surface the problem to Slawomir and let him decide. The operator can defer for N minutes or until a specified time, or select another model (with pool reassignment also retained under prior rulings). Do not automatically select a grace interval, model downgrade, fallback or retry policy. This supersedes treating the earlier roughly one-to-two-minute pause-first discussion as an automatic recovery decision or timer. The problem report and evidence remain attributable, and the chosen disposition is recorded.

This answers K F5's proposed automatic suspect-model grace policy by requiring an owner disposition rather than an inferred automatic start hold or automatic retry. It does not settle the scope of a deferral (affected execution, selected model queue, or entire pool), behavior of unrelated queued starts before disposition, or whether reaching the selected time authorizes a fresh attempt; these must not be silently inferred. Queue admission continues; healthy active executions are not interrupted. Existing execution deadlines remain in force, with supported retained recovery/new admission where necessary rather than a silent deadline extension.

## Owner-selected automatic resumption after timed deferral — 2026-11-22

An owner-selected timed deferral authorizes automatic resumption when the selected duration/time expires; do not ask the owner a second time merely to perform that authorized resumption. If the resumed work fails again, report the new failure and require a new owner disposition. There is no automatic repeated-retry loop.

This resolves the at-time resumption question in the preceding provider-problem ruling. Resumption remains subject to normal ownership, cessation/fencing, cancellation and admitted-limit checks and supported continuation/new-admission contracts; it does not resurrect a cancelled execution, extend an admitted deadline silently, or duplicate still-running work. Persist the owner decision, due time and resumption attribution so restart does not lose the deferral or execute it twice. Deferral scope is a separate selection, not implied by this ruling. No current work is resumed by this decision record.

## Owner-selected disposition scopes and selective downgrade — 2026-11-22

Owner selects all three explicit deferral/disposition scopes: individual work (a selected phase or Job), a selected model within a pool, or the entire pool. The operator may downgrade/change the supplying model for one phase/Job while leaving other assignments intact awaiting the preferred model's credit reset. Do not broaden a narrow choice to all queued work, remove another assignment's deferral, or change unrelated model selections.

Timed deferral still authorizes automatic resumption only for its selected scope; a renewed failure needs a new owner decision. Model/pool changes remain manual, with exact scope recorded. Preserve healthy running executions, retained evidence, role independence and compatible-context/safe recovery rules. This resolves the preceding open deferral-scope question. It does not silently define conflict resolution for overlapping active deferrals or supersede project > team > global precedence for persistent redirects; any additional interaction semantics must be explicit in planning. No current assignment or pool is modified here.

## Owner-selected transitive persistent pool substitution — 2026-11-22

Pool redirects are operator instructions, not actions taken by a pool. Owner confirms persistent nested substitution: when the operator selects A -> B and subsequently B -> C, work assigned through A follows the chain to C. The substitutions remain until the operator cancels or changes them; there is no automatic failback. This resolves K review F7's user-visible chaining question in favor of transitive resolution.

Apply this rule together with project > team > global applicability and the existing non-preemptive rule: queued/new assignments follow the effective substitution, while healthy running agents finish where they started. Preserve original assignment and effective destination/chain for explanation and attribution. A cyclic or ambiguous arrangement cannot provide a valid terminal destination and must not loop or silently invent one; validation mechanics remain bounded design. Concrete cancellation/overlapping-scope examples must reflect these selected rules rather than infer unselected effects. No live redirect is installed here.

## Owner-confirmed W9901 scheduling independence — 2026-11-22

Owner explicitly approves W9901 proceeding independently of the old W9 -> W10 milestone ordering. The selected complete native workflow is the current priority. This resolves K review-2026-11-22T03-50-15Z.md F6 and supersedes earlier wording that treats W9 -> W10 (or historical W1431/W1433 locators) as a prerequisite gate on W9901's selected scope. Preserve those Works and their unfinished obligations; this neither closes them nor asserts their requirements satisfied. Reuse existing provider Work such as W16830 rather than silently duplicate or dispose of it. Individual dependency/containment changes still require explicit classification and authorized graph operations. No graph edge is changed by this ruling and implementation remains subject to the corrected plan and independent acceptance.

## Owner-approved staged delivery and complexity boundary — 2026-11-22

Owner approves the recap and staged delivery recommendation: the complete model is an umbrella outcome, not one implementation Job. W9901 retains the overall specification/acceptance record; deliver separately bounded implementation Jobs, reuse existing ownership (including W385331), and reuse identity, execution, custody and review mechanisms where they fit rather than authorize a rewrite. Earlier confirmed capabilities remain required outcomes; staging does not silently defer them out of scope or claim umbrella completion.

Selected delivery order:
1. First usable outcome: one complete recovery loop grounded in the actual malformed-verification failure. Retain candidate -> automatic diagnosis -> owner-facing options -> recorded owner choice -> safe re-verification/resumption -> independent review, without manual courier. A read-only message surface is a prerequisite within this delivery, not the acceptance endpoint.
2. Explicit Job phases and owner-approved plan changes, starting with a small template set and the already selected approval gates.
3. Complete cross-team requests and dependencies, proved with two projects and clarification that remains runnable without deadlock.
4. Shared-pool controls incrementally: visible pool/model selection and manual reassignment first, followed by timed deferrals, limits and scoped transitive redirect chains.

The planning revision must distinguish first usable outcome, subsequent required capabilities and genuinely unresolved choices. Pay particular attention to interactions of retries/retained progress, deferrals/deadlines, redirects/model selection, and dependencies/phase changes. Do not require every eventual pool/team control before the first useful loop or mistake a staged plan for authority to implement unresolved behavior. Preserve existing independent review, explicit owner selections and human Git ownership. This ruling refines M385585's consolidation correction; it launches no implementation or native Job.

## Owner-selected Stage 1 analysis role — 2026-11-22

Owner selects a dedicated analysis role for Stage 1, assigned through the configured agent pool. Its authority is to inspect the failed execution's attributable evidence and retained outputs, produce a diagnosis, and present recovery options and a recommendation. It may author its analysis report, but may not change product/candidate bytes, verification inputs or execution state, or authorize recovery. Slawomir authorizes recovery through the selected decision contract. This selects role responsibility and authority, not a permanently assigned model, pool, participant identity, or new live deployment. Bind concrete execution identity/configuration explicitly before implementation/execution as required.

## Owner-selected analysis-failure endpoint — 2026-11-22

If the analysis agent itself fails, retain its partial evidence and notify Slawomir directly for a decision. Do not automatically launch another analysis, retry the analysis, or recursively analyze that failure. Preserve the original failed execution/candidate and the failed analysis as distinct attributable records. The owner chooses any further action. This selects the finite analysis-failure endpoint for Stage 1; it is distinct from a corrected verification failure, which still produces one fresh analysis and then a new owner item under the previously confirmed rule.

## Owner-approved retained-candidate verification/review recovery — 2026-11-22

Owner approves the narrow Stage 1 recovery behavior: validate the retained candidate against its recorded identity/digest; present the original failed verification command and exact proposed correction; obtain Slawomir's approval of that correction and linked verification/review execution; create a new attributable verification execution using an isolated workspace materialized from those exact retained bytes; run the corrected command and record output/exit status; on success automatically deliver the same candidate to independent substantive review without repeating implementation.

Preserve the original immutable candidate, failed command and failure evidence. The proposed example removes the accidental newline inside the Python string in w9901-native-planning-1's submitted command. Its five required-heading checks are structural verification only, not proof that the plan is substantively correct. That judgment remains independent review. A new verification failure dispatches one new analysis and owner item, never an automatic further recovery execution. If analysis itself fails, preserve its evidence and notify the owner directly, without recursive analysis.

This is approval of the Stage 1 product contract, not authorization to change the historical Job or perform a live recovery now. The linked manager-owned successor must preserve cancellation/ownership/cessation/integrity constraints and must not reset old admitted deadlines. Concrete successor admission and execution-limit fields must be pinned before coding, with unresolved product semantics escalated rather than invented. The original fresh-attempt operation, which repeats implementation, is not an implementation of this selected contract.

## Owner-selected expiry after successful verification — 2026-11-22

Owner selects the conservative Stage 1 expiry disposition from K review-2026-11-22T04-35-09Z.md E2: if retained-candidate verification passed but the successor expires before independent review completes, preserve the successful verification evidence and present a held item to Slawomir. Do not treat this as verification failure, accepted review or automatic retry. The owner may authorize a new linked review-only execution. Neither implementation nor verification is repeated unless verification evidence is no longer valid; the validity checks and exact candidate binding must be explicit in the contract, not silently waived or inferred.

Original failure, successful verification, expired successor and any subsequent owner decision remain distinct attributable evidence. Preserve cancellation/cessation/ownership constraints, with no reset of old deadlines or duplicate review dispatch. This resolves E2's immediate disposition; it does not publish the proposed profiles, select a live recovery, or authorize automatic separate review admission. Profile publication remains a separate owner selection under E1.

## Owner-approved Stage 1 finite profiles — 2026-11-22

Owner explicitly approves publication of the two proposed initial reusable Stage 1 execution profiles with these values and clock semantics:

- Analysis: overall execution Job limit 4800 seconds (80 minutes), including queue time from accepted admission; analysis stage limit 4800 seconds from stage admission; model invocation limit 3600 seconds (60 minutes) from invocation start. No automatic correction/retry. Analysis expiry, cancellation or failure retains available evidence and goes directly to Slawomir; unknown cessation stays qualified and cannot authorize replacement execution.
- Verification plus review: overall successor Job limit 9960 seconds (166 minutes), including queue time from accepted admission; each stage limit 4800 seconds from that stage's admission; verification command limit 900 seconds (15 minutes), including any required review verification command; review model invocation limit 3600 seconds from invocation start. No automatic correction/retry. Expiry after successful verification preserves that result and holds an owner item under M385611. A new verification failure produces one analysis and owner item; it does not automatically admit another recovery successor.

Existing bounded shutdown handling remains unchanged; its deadline does not extend work time or prove cessation. This approval satisfies K E1's owner publication gate and supersedes the contract claim that coordinator pinning alone was sufficient. Pin immutable profile identities/digests and exact resolved values in the corrected contract/evidence before dependent coding. Do not mutate existing documentation/1 or native-handoff/1 profiles. This approves the reusable profile definitions, not a live installation, provider run or historical Job recovery. Subsequent changes require a newly approved profile. The separately owner-authorized review-only recovery must name its reviewed finite execution contract; do not silently apply a new unapproved profile to it.
