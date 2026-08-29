# Carry principal-aware execution context through the Worker Manager

## Discovery and ownership

Discovered by W16793 as the Worker Manager consumer of the authority correction
in W16821. Ledger Work W16823 is bound to this record. The record is promoted to
a top-level dossier because the discovery record already occupies the permitted
second child level.

## Confirmed incompatibility

The Worker Manager correctly fences an execution by the frozen four-part
assignment `(authority UUID, Work id, participant, generation)`, but it treats
that endpoint participant as every identity needed below the authority:

- `worker_manager/authority_port.py` exposes a `participant`-bound port, calls
  `slot_holder(participant)`, and accepts claim answers containing only the
  four-part assignment;
- `worker_manager/schema.py` persists `offers.participant`,
  `attempts.assignment_participant`, execution `agent_sessions.participant`
  and interrogation assignment participants, with no principal or effective
  authorization context;
- `worker_manager/attempts.py:_runtime_labels` labels runtimes by authority,
  Work, participant and generation;
- `worker_manager/documents.py` seals `assignment` and `runtime.labels` to those
  same fields.

The four-part assignment remains useful operational fencing and must not be
weakened. It is insufficient for W9901's separate canonical principal and
authority-derived effective scope: two endpoint addresses mapped to one
principal produce unrelated runtime labels, stores and capacity observations,
and no retained record explains which scope/grant authorized activation.

The frozen worker-control and agent-session 1.0 schemas also use the four-part
assignment with sealed objects. That is not automatically a defect: the
sandboxed agent needs a fenced execution reference, not authority to choose its
principal or scope. Changing an existing required identity field would require
a new major protocol version under the frozen version rules. This Work must
first keep the authorization context on the trusted manager/adapter side and
only version a wire contract if a concrete remote consumer must receive it.

## Required correction boundary

1. Consume W16821's authority-owned claim/assignment projection with canonical
   principal, effective scope and authorization provenance in addition to the
   existing endpoint assignment.
2. Persist that context atomically with offer acceptance/claim activation and
   include it in manager replay signatures wherever changing it would change
   authorization meaning.
3. Label and reconcile execution runtimes by principal-global identity as well
   as the existing assignment fence, so two endpoint spellings cannot create
   two supposedly independent runtime identities for one principal.
4. Keep consent posture pre-claim and authority-free. Keep workers unable to
   select or mutate principal, scope, grant or policy generation.
5. Preserve the exact four-part assignment for generation fencing. Treat
   participant as an operational endpoint, not as proof of the principal.
6. Do not alter frozen 1.0 worker-control or agent-session meanings by stealth.
   If a wire-visible field is proved necessary, create the explicit negotiated
   version/provider Work required by the frozen compatibility policy.

## Acceptance

- With endpoint addresses `org_a.worker` and `org_b.worker` mapped by the
  authority to one principal, offers and attempts retain the same principal
  identity and cannot evade principal-global capacity/runtime reconciliation.
- An injected claim answer with a well-formed but wrong principal, effective
  scope, authorization provenance or policy generation is refused before a
  manager row or runtime is created.
- Replay under the same operation identity collides when the authorization
  context differs; an exact replay preserves the original result.
- A worker/agent input cannot supply principal or scope, and no new Baton,
  SQLite, repository or canonical-write capability crosses the isolation
  boundary.
- Existing assignment generation, runtime adoption, cancellation and cleanup
  tests remain green.

## 2026-08-28 — PLAN 1 revalidated, and one seam gap blocks the rest

**Confirmed — W16821 is closed satisfying and its context is complete, but the
manager cannot reach it exactly.** Measured against the delivered surface
through the only object the manager ever holds — a participant-bound `Session`
behind `AuthorityPort`. Evidence:
`evidence/w16823-seam-revalidation-2026-08-28.txt`.

- `claim` answers `{work_ref, participant, generation}` and nothing else. The
  four-part fence, no authorization context.
- The decision IS retained and complete — `endpoint`, `principal`,
  `effective_scope`, `role`, `grant`, `policy_generation` — but only on
  `assignment_events`, reachable by picking a claim event out of a list.
- **Picking the newest match is unsound and W16821's own re-review said so.**
  A v11 assignment mints no generation, so two claims through one endpoint are
  two acts with IDENTICAL four-part identities. Measured: two claim answers
  compared equal while the authority held claim events at seq 3 and seq 5. A
  manager matching on the answer cannot say which claim it just made.

**Confirmed — one half of correction boundary item 3 needs no change at all.**
Capacity is already principal-global: `slot_holder('org_b.worker')` answers
about the Work claimed through `org_a.worker`, because W16821 keyed the slot by
principal. The manager observes principal-global capacity today without any new
member.

**Confirmed — the six principal reads are absent from the session and that is
correct.** `principal_of`, `grants_of`, `decision_of`, `endpoints_of`,
`policy_generation` and `slot_holder_of_principal` are configuration on the
bootstrap face the manager never holds. A manager able to ask about other
principals would be a wider capability, not a fix. The gap is narrower than
that: the manager needs the decision for the claim IT just made.

**Proposed minimal shape, for the reviewer to route.** One additive member at
the claim seam, either

  (a) `claim` answers the assignment plus its exact decision, or
  (b) a new session read answering the decision of the caller's own live
      assignment,

with (b) preferred because it changes no shape any existing case asserts and
because a session can only ever ask about the assignment it holds. Both are
edits to `authority/` — W16821's closed deliverable — so which Work carries
them is not mine to decide.

**Nothing else in this correction can be built truthfully first.** Boundary
items 1, 2, 4, 5 and the labelling half of 3 all require the manager to HOLD
the principal and scope. Guessing the authority's answer is what this Work's
brief forbids in terms: it "consumes the reviewed authority projection and must
not guess it in parallel".

## 2026-08-28 — claim-context ruling proposal, pending approval

### Ownership and exact answer

**Confirmed from the approved compatibility matrix:** W16823 owns the claim
answer contract as well as its manager consumer. The matrix classifies the
Worker Manager port as “answer contract must fix now” and assigns that
disposition to W16823. W16821 owns the authority's principal/scope/decision
foundation; creating a follow-up merely because the consumer correction also
touches `authority/` would split one atomic provider/consumer boundary and
leave neither Work able to prove it.

**Proposed closed claim result:** replace the bare assignment answer with one
document written atomically by the claim transaction and retained whole in the
authority operation journal:

```text
{
  assignment: {work_ref, participant, generation},
  claim_event: <positive assignment_event.seq>,
  decision: {
    endpoint, principal, effective_scope, role, grant, policy_generation
  }
}
```

The assignment remains the unchanged four-part execution fence. `claim_event`
is the exact immutable act identity W16821's re-review established; it prevents
the manager from matching a nullable v11 assignment tuple. `decision` reuses
W16821's one vocabulary byte for byte rather than inventing a manager spelling.
An exact authority retry or lost-result settlement returns the original whole
document from the operation journal.

**Proposed version boundary:** raise the authority store version from 2 to 3
even though no table changes, because a schema-2 operation row may contain the
old bare claim result and this build would otherwise adopt it under the new
answer contract. M33752 already approves clean initialization boundaries for
disposable proof stores. Raise the manager store version from 11 to 12 for the
new offer/attempt context columns; both old stores refuse read-only with their
existing operator-directed policy.

### What the manager can and cannot independently prove

**Confirmed logical limit:** the manager can validate the closed shapes and
relations it already knows: decision endpoint equals the assignment endpoint
and bound session; decision scope and role equal the Work scope/route frozen at
offer issuance; grant uses the durable provenance vocabulary; policy generation
is positive; and claim event/operation identities are durable. It can refuse
any caller- or worker-supplied principal/scope/context operand because none is
accepted.

The manager cannot prove that a well-formed principal returned by its trusted
authority is “wrong” relative to the authority's private endpoint mapping. No
second principal fact crosses the boundary, deliberately: exposing
`principal_of` or reconstructing the mapping would make the manager a second
authority and contradict this Work. Fault injection that replaces the trusted
authority's answer with a different but internally consistent principal is
therefore not a manager-verifiable negative case.

**Proposed acceptance clarification:** supersede only that impossible clause.
Require refusal of malformed or relationally inconsistent injected context and
of every worker/caller context override; require exact persistence/replay of the
principal the trusted claim decision returns. Do not require an independent
manager verdict about whether that authoritative principal ought to have been
another value.

### Manager and downstream boundary

**Proposed W16823 implementation boundary:** persist the exact claim event and
decision on the claimed offer and activated attempt; include the complete
context in every manager replay signature whose meaning it changes; add
principal/effective-scope to trusted runtime labels and reconciliation while
retaining participant/generation fencing. Do not put the context into frozen
worker-control or agent-session 1.0 documents; no remote consumer needs it.

**Confirmed non-overlap:** W16823 supplies stable principal/scope context and
labels. W32649, already blocked on W16823, owns cross-attempt runtime-lane
acquire/release and predecessor cleanup capacity. W16823 must not pre-implement
that lane merely because its context makes the later invariant expressible.

## 2026-08-28 — claim-context ruling, with one revalidated version collision

**Confirmed by approver response M34905:** W16823 owns the atomic authority
claim result and its Worker Manager consumer. The result carries the unchanged
four-part `assignment`, the exact immutable `claim_event` identity and the
authority-owned `decision`. The manager persists and replays that exact
context, validates its closed shape and internal relations, and refuses every
caller or worker override without independently reconstructing the authority's
principal mapping. Trusted principal/scope runtime labels belong here;
cross-attempt runtime-lane capacity remains W32649's boundary. The earlier
proposal's “pending approval” status is superseded by this ruling.

**Confirmed acceptance clarification:** the original requirement to refuse a
well-formed but independently “wrong” principal is superseded. The manager can
refuse malformed or relationally inconsistent context and any untrusted
override. It cannot second-guess an internally consistent principal supplied
by the trusted authority without acquiring a duplicate principal-mapping
capability this correction explicitly forbids.

**Revalidated conflict — the approved authority version number cannot be used
against the current tree.** M34905 named authority schema 3 as the clean proof-
store boundary. Since the proposal was written, W29400 has assigned schema 3
to the Work-label model in `authority/schema.py`. A schema-3 operation journal
can therefore retain the old bare claim answer. Reusing 3 for the new closed
claim result would silently adopt bytes whose meaning this build no longer
accepts, defeating the reason for versioning the result contract at all.

**Proposed narrow correction, pending approval:** retain every substantive
part of M34905 and use authority schema 4, not 3, as W16823's clean
initialization boundary. Manager schema 12 remains unconflicted. This is a
version-allocation correction forced by the delivered tree, not a change to
the approved claim result, trust boundary, persistence model, labels or Work
ownership.

## 2026-08-28 — cumulative schema boundary approved

**Confirmed by approver response M35002:** authority schema 4 is W16823's
clean-initialization boundary. It represents the cumulative authority shape
after W29400's schema 3; no later Work may lower or independently reuse that
version. The preceding proposal's pending status and M34905's schema-3 number
are superseded only on this version allocation.

**Still confirmed without amendment:** manager schema 12, the atomic closed
claim result (`assignment`, exact immutable `claim_event`, authority-owned
`decision`), trusted persistence/replay and relational validation, refusal of
caller/worker overrides, no duplicate principal mapping, principal/scope
runtime labels, unchanged frozen 1.0 wires, and W32649 ownership of the cross-
attempt runtime lane.

## 2026-08-29 — implemented, and one observation the tree supplied

**Confirmed — the approved boundary is implemented in full.** Authority schema
4 and manager schema 12; `Core.claim` answers the closed
`{assignment, claim_event, decision}`; the port owns it whole and holds it to
three relations; the offer and the attempt persist the exact context
atomically; both replay signatures carry it; runtime labels carry the principal
and effective scope beside the unchanged fence; and no caller or worker operand
can supply any of it. Evidence: `evidence/w16823-mutations-2026-08-29.txt`.

**Confirmed — the frozen `assignmentManifest` ALREADY requires this fact, and
under this name.** `worker-control-1.0.schema.json` makes `claim_event_seq` a
required integer of an assignment manifest. Nothing in production composes one:
`check_input_pair` VALIDATES a manifest the caller supplies, and the only
composers in the tree are test fixtures writing a literal 7.

Two consequences, neither of which is this Work's to act on:

- the manager column is named `claim_event_seq` rather than `claim_event`
  because that is the frozen vocabulary's own spelling for the same fact -- not
  an invention, and not a change to any frozen document;
- when a production assignment-manifest composer arrives, the value it must put
  in that field now EXISTS on the activated attempt row. Before this cut there
  was no source for it in this build at all, which is worth recording because
  it is a second, independent argument for the closed claim result: the frozen
  wire had already decided the fact was necessary.

**Still confirmed and unchanged:** the frozen worker-control and agent-session
1.0 meanings are untouched -- no file under `contracts/` was edited. The
principal and effective scope stay on the trusted side exactly as the boundary
requires: they reach runtime LABELS, which are this manager own reconciliation
evidence, and no worker-visible document.

## 2026-08-29 — independent review signed off

**Confirmed:** the implementation satisfies the approved closed-result,
trusted-persistence, replay, relational-validation, no-override, and runtime-
label boundary. Review evidence is
`review-2026-08-29T01-17-35Z.md`.

**Observed, separately scheduled:** the boundary inventory derives adopted
column probes for offers and operations but not attempts. The two new probeable
context fields join two older attempt-column omissions; the complete table-
family correction is owned by W35557 at
`work/records/2026/08/finding-v12-attempt-boundary-probes/` and does not change
the W16823 verdict.
