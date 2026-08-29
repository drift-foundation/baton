# Plan

1. Revalidate W16821's reviewed authority projection and W16793's manager
   inventory against the current tree.
2. Pin one trusted-manager authorization-context document that keeps endpoint
   assignment, principal, effective scope, role, provenance and policy
   generation distinct.
3. Version the manager control-store rows and port answer checks; bind context
   atomically at claim activation and into replay signatures.
4. Extend trusted runtime labels/reconciliation and execution session evidence
   with principal-global identity without changing consent posture.
5. Prove no worker-supplied operand chooses or widens the context and decide,
   with a recorded compatibility analysis, whether any frozen wire schema needs
   a new negotiated version.
6. Add positive, negative, restart, replay, multi-endpoint and cancellation
   tests, then return for independent review before M2 conformance.


## 2026-08-28 — the gate cleared, and PLAN 1 is done

1. [done] Revalidated against the delivered tree rather than the brief:
   `evidence/w16823-seam-revalidation.py`, retained with its transcript. The
   authorization context is complete and retained; the CLAIM SEAM does not
   carry it, and the only route to it is a match that W16821's own re-review
   established is not an exact identity.
2-6. [blocked on one additive member] Every remaining item needs the manager to
   hold the principal and scope for the claim it just made. Two candidate
   shapes are proposed in `FINDING.md`; both edit W16821's closed deliverable,
   so routing is the reviewer's call.

Already true and needing no change: principal-global CAPACITY, which
`slot_holder` answers today because W16821 keyed the slot by principal.

## 2026-08-28 — ruling requested before implementation

2. [proposed; awaiting approver] W16823 owns one closed claim result containing
   the unchanged four-part `assignment`, exact `claim_event`, and W16821's
   complete `decision`. The authority claim transaction and operation journal
   retain it atomically; there is no post-claim newest-event search.
3. [proposed; awaiting approver] Treat the claim-result contract as authority
   schema 3 clean initialization and the manager context columns as manager
   schema 12 clean initialization. Persist context on claimed offers and
   activated attempts and bind it into manager replay signatures.
4. [proposed; awaiting approver] Carry principal and effective scope in trusted
   runtime labels/reconciliation beside, not instead of, endpoint/generation.
   Leave cross-attempt lane capacity to dependent W32649.
5. [proposed; awaiting approver] Keep both frozen 1.0 wire contracts unchanged.
   Supersede the impossible “well-formed but wrong principal” manager test with
   relational-consistency and no-caller-override negatives: the trusted
   authority's returned principal is the only principal fact the manager has,
   and independently second-guessing it would duplicate authority.
6. [blocked] Implement and verify only after the recorded approver ruling.

## 2026-08-28 — substantive ruling approved; one version allocation re-opened

2. [approved by M34905] W16823 owns the atomic closed claim result:
   `assignment`, exact immutable `claim_event`, and authority-owned `decision`.
   Authority replay returns that whole original result; the manager never
   searches claim history for a newest tuple match.
3. [approved except one version number] Persist the exact context on claimed
   offers and activated attempts and include it in every replay signature whose
   authorization meaning it changes. Manager schema 12 remains the approved
   clean initialization boundary. Authority schema 3 is already allocated by
   W29400 and can contain the old bare result, so authority schema 4 is proposed
   as the narrow current-tree correction and awaits approval.
4. [approved] Carry trusted principal/effective-scope runtime labels beside the
   existing endpoint/generation fence. Do not implement W32649's cross-attempt
   runtime lane.
5. [approved] Keep frozen worker-control and agent-session 1.0 unchanged.
   Refuse malformed or relationally inconsistent context and every caller or
   worker override; do not duplicate the authority mapping to second-guess an
   internally consistent authoritative principal.
6. [blocked only on authority version allocation] After approval, implement
   positive multi-endpoint persistence, exact retry/restart replay, changed-
   context operation collision, malformed/relational negatives, override
   refusal, trusted-label reconciliation, cancellation/cleanup regression and
   clean incompatible-store refusal tests. Return for independent review before
   M2 conformance.

## 2026-08-28 — implementation gate cleared by M35002

3. [approved] Use authority schema 4 as the cumulative clean-initialization
   boundary after W29400's schema 3. Use manager schema 12. Neither store
   adopts the preceding version's incompatible result/row meaning.
6. [ready for implementation] Implement the complete approved boundary and
   its positive multi-endpoint, exact retry/restart, operation-collision,
   malformed/relational, no-override, trusted-label, cancellation/cleanup and
   incompatible-store regressions. Return for independent review before M2
   conformance.

## 2026-08-29 — implemented

2. [done] `authority/core.py` answers the closed
   `{assignment, claim_event, decision}`; `authority_port.py` owns it whole at
   the crossing that receives it, on BOTH paths a result arrives by.
3. [done] Authority schema 4, manager schema 12. The offer freezes the Work's
   scope and route at issuance and retains the exact claim event, principal,
   scope, role, grant and policy generation on the claim; activation copies
   them onto the attempt in the same UPDATE that fixes the fence. Both replay
   signatures carry the context.
4. [done] `runtime.labels` carries `principal` and `effective_scope` beside the
   unchanged four-part fence, at the manager's own derivation and at the two
   adapter doors that compose a selector.
5. [done] No file under `contracts/` was edited. The context reaches runtime
   labels -- this manager's own reconciliation evidence -- and no
   worker-visible document. The impossible negative is superseded by M34905 and
   the boundary is recorded as a case rather than as a check.
6. [done] Positive multi-endpoint, exact retry, restart replay, changed-context
   collision at both signatures, malformed and relational negatives on both
   claim paths, no-override, trusted labels and both clean-initialization
   refusals. Two new modules; every guard measured by removal.

## 2026-08-29 — independently reviewed

1-6. [signed off] No blocking finding remains. Review:
`review-2026-08-29T01-17-35Z.md`.

The pre-existing absence of table-derived adopted-attempt corruption probes is
separately scheduled as W35557 at
`work/records/2026/08/finding-v12-attempt-boundary-probes/`; it is not part of
this Work's implementation boundary.
