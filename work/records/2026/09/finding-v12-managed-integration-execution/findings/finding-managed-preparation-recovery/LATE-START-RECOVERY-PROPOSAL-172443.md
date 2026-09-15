# Late failed-start recovery — owner selection packet

**SUPERSEDED by owner2026-09-14T22:18:02Z / M172655.** Visible manual recovery
and human cleanup suffice for this uncertain-start case. The automatic late-proof
direction below remains historical evidence, not a pending prerequisite.
Current reporting/restart acceptance is in child FINDING/PLAN22:18:02Z.

2026-09-14T21:50:56Z, reviewer baton.codex, W170382 claim172443.
**Proposed, not selected.** Preserve W170382, its parent, evidence and gates.

## Concrete boundary

The selected outcome requires an initially unknown failed start to remain held
and later exact evidence to enable recovery. Current composition never repeats
that observation. Adding public reconcile_runtime alone is insufficient: the
original runtime.start-failed receipt names runtime_id=None, while late
reconciliation attaches runtime-single-3. authorize_failed_start_cleanup correctly
rejects the mismatch through intake._failed_start_record:3699. Both steps are
independently reproduced in this claim's probes and review.

This is not a reason to weaken the guard: it prevents a failure receipt for
runtime A authorizing destruction of runtime B. The unknown original receipt
must not be rewritten as if the runtime had been known at the original failure.

The selected parent SLICE2-SCOPE-165724.md:119-124 makes generic intake/OCI/output/
Authority and other generic owners reuse-only and says to return the exact
missing path/API and evidence when a new source boundary is necessary. The
current failed-start API has no operand/receipt for authenticated late binding.
No such alternative was found in the inspected public failed-start/reconciliation
owners. An explicit abandonment Route policy is a different authorization, not
an implicit substitute for failed-start cleanup.

## Recommended selection

Select a bounded prerequisite to design and implement an immutable late-identity
authorization for this failed-start case, then compose it into W170382. Its
record must bind the original failure receipt digest, original start operation,
exact attempt/fixed assignment and positively observed full runtime identity.
The original failure receipt stays immutable. Replays must name the same late
identity and changed or multiple identities must refuse. Cleanup is authorized
by the proved chain, never by merely allowing None to match any current runtime.

Known owning entry points are worker_manager/attempts.py:reconcile_runtime and
worker_manager/intake.py:authorize_failed_start_cleanup/_failed_start_record,
under v12/python/src/baton_v12. A prerequisite design must enumerate any needed
document/crossing/adapter contract changes and exact focused test paths before
implementation; this packet does not silently add those generic paths to the
nine selected composition source paths. Preserve current non-null identity
checks and existing failed-start cleanup behavior. Standalone candidate review
must bind the full resulting generic and composition path set before import.

Acceptance must cover one inconclusive listing followed by exact identity,
persistent uncertainty, wrong/multiple runtime identities, replay and coordinator
restart around late proof and cleanup, unchanged original receipt, ordinary
fencing and delivery cleanup, retained result custody, no duplicate execution,
and root/apply/parent holds. Use deterministic adapter-boundary simulation and
the actual owner APIs; no engine/model run or cumulative budget gate is needed.

## Alternative requiring an explicit ruling

Select an exact Route policy that declares this failed attempt abandoned after
late positive reconciliation, using the existing abandon_attempt API and its
immutable declaration. That API explicitly says an operator or Route policy
decides abandonment. If selected, pin the trigger and truthful reason, eligible
failure states, exact identity proof, custody and outcome semantics, and prove
that missing evidence never triggers it. This may reuse generic APIs but changes
the authorization used for this outcome. Do not silently classify a failed start
as an operator abandonment or invent such a declaration in a fixture.

Until selection, the implementation may complete independent remaining matrix
work within its existing scope when routed to it. Neither this proposal nor the
partial known-failure fixes accept group2, release W170385/parent, or authorize
generic implementation. Route to baton.ops for the recorded selection and then
back to baton.impl with the exact selected scope. No user-facing interactive
approval request is part of this managed turn.
