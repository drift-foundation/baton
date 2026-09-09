# Proposed concrete claim-refusal adapter

Research W124788 claim124875; **owner allocation required**. No source or test
change has been made. The concrete problem is one refused Authority claim
aborting a serving sweep; broader Authority transport/error redesign is excluded.

## Confirmed crossing

`evidence/probe-124875.py` drives the actual composed fixture. On the second
post-implementation tick the sweep raises `authority.errors.Refusal`, message
“route 'baton.impl' does not resolve to 'baton.reviewer'”, code=None,
durable=False. It is not ContractRefusal. Runtime0.1852s under declared1s.
The real fixture establishes escape; a future two-Job positive continuation
test is still required and has not been claimed by this research.

Call chain: manager._delegate -> pooled scheduler.claim ->
ManagerOperations.claim -> offers.submit_claim -> AuthorityPort.claim ->
tools.single_worker._AuthoritySession.claim -> concrete Session.claim.
The scheduler catches ContractRefusal, then reads the canonical manager receipt
to distinguish performed/adopted from deferred. submit_claim records only after
the remote answer returns; this refusal provides no successful manager receipt.

`authority.errors.Refusal` has an optional unstructured code and durable flag;
current claim raising sites provide no typed code. Parsing message text to infer
policy, stale identity or operation collision would invent an unstable mapping.
`contracts/errors.py` already permits refused/precondition, ambiguous/operation
and integrity/schema. No new wire vocabulary is needed.

## Recommended boundary and exact behavior

The generic AuthorityPort explicitly keeps the concrete Authority module graph
outside its import boundary. Importing the sibling Refusal there would violate
that separation. Teaching generic scheduler._delegate about one deployment's
Authority exception would make every injected operation depend on the same
concrete type. Changing Authority Refusal into ContractRefusal would redesign
the source contract and its operation journal.

Instead add a private deployment-side **manager claim session** in
`tools/single_worker.py`, reusing the explicit forwarding surface and overriding
only `claim`. The build factory supplies this adapter to AuthorityPort while
retaining `_AuthoritySession` for direct deployment/session calls. Both wrap
the same already-minted participant session; no new identity or capability is
minted. A small subclass of the explicit wrapper is sufficient; do not add
generic __getattr__ capability discovery or a second manager/session protocol.

Catch only the concrete Authority Refusal from the claim invocation. Preserve
successful answer identity, existing ContractRefusal identity and unrelated
programming/transport exceptions. Preserve every direct `_AuthoritySession`
forwarder's result/refusal identity, including accepted satisfy_gate behavior.

Proposed closed mapping (no message parsing):

- code=None, durable exactly False: ContractRefusal(refused, precondition),
  durable=False. The scheduler defers without recording success or retiring
  the fixed claim; ordinary retry may succeed when the actual precondition does.
- code=None, durable exactly True: ContractRefusal(ambiguous, operation),
  durable=False. A remotely durable failure is not proof of a canonical local
  manager receipt. Leave settlement to existing public operation recovery.
- Other code/flag shapes: ContractRefusal(integrity, schema), durable=False,
  with a static bounded diagnostic. Do not copy an unknown source code into
  the closed manager vocabulary or treat a malformed flag as truthy evidence.

Own diagnostic text before forwarding: bounded text, existing secret-safe
diagnostic mechanism, static fallback if it is not safe/valid. Avoid a chained
raw exception exposing a rejected diagnostic. No automatic disposal, route
change, slot release, claim retirement or invented absence follows this mapping.
Only the ordinary claim crossing is included; other operation boundaries need
their own semantics and allocation if a concrete gap is found.

## Proposed separate implementation allocation

High baton.impl, returning baton.bug, exactly these existing paths:

- `v12/python/tools/single_worker.py`
- `v12/python/tests/tools/test_single_worker.py`
- `v12/python/tests/tools/test_stage_execution.py`

These overlap W122060's reserved consumer paths: allocate this provider
**serially before consumer resumption**, reserving the three paths through
independent acceptance. It may coexist with the disjoint receipt/cleanup
providers only while those allocations remain intact. No manager, Authority,
schema, registry, stage_execution.py or other test edits.

Tests are additive except this exact required conversion:
`TheReviewStageCannotClaimTheOneWork.test_the_reviewers_claim_is_refused_against_the_implementation_route`
in test_stage_execution.py changes from expecting an escaping Authority Refusal
to asserting an ordinary deferred wrong-route claim, no successful claim receipt
and no review runtime start. Retain its pre-change bytes as dossier evidence.
This explicitly supersedes owner124767's future positive conversion of this
same method: preserve the wrong-route negative, and let W122060 add a separate
correctly routed same-Job positive once its routing provider is accepted.
No other assertion changes. The discharge-test conversion stays unchanged.

Add real-session wrong-route and blocked/capacity refusals, exact forwarding
and successful answer identity, existing ContractRefusal unchanged, malformed
and durable-source controls, safe diagnostics and non-Authority exception
propagation. Through actual serving construction, prove two independent Jobs
with distinct participants: one concrete claim refuses and stays owed while
the other progresses in the same sweep. Then correct the first precondition
through an authorized fixture action and prove the same fixed claim identity
can succeed without duplicate claims or released reservations. Fixture-only
Authority/bootstrap setup is not a production routing workaround.

Declare cumulative20s focused verification before running; retain exact
commands, timings, hashes/modes and real/fake fixture limits. No broad baseline
or inventory expansion. Report an excluded capability before expanding scope.

## Decision requested

Approve or amend this bounded adapter/mapping, three-path serial ownership,
exact negative-test conversion and acceptance tests. Create/bind a separate
implementation Work and install its actual-acceptance gate on W119114 and
W122060 before this research closes. That preserves the existing parent path
reservation and final proof gates; research itself accepts no implementation.
