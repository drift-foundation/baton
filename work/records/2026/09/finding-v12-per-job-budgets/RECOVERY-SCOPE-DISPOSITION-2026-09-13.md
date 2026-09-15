# W156162 — scope disposition for the remaining host recovery boundary

Prepared by baton.codex under claim160499 at2026-09-13T12:21:26Z.
**Proposed. No new implementation authority or acceptance amendment.**
Candidate and evidence are bound by review-2026-09-13T12-21-26Z.md and
provenance-160468.json. The independent review has completed the authorized
explanation/provenance corrections sufficiently for this scope decision.

## The decision needed

Owner159347 approved HOST-FAILURE-PROPOSAL-2026-09-13.md with **no acceptance
waiver**, and added only reconciliation.py and execution.py to the finite source
scope. Step4 requires isolation across Jobs/results/harnesses and says changes
needing a new execution use **existing explicit recovery/new-result mechanisms**.
The composed host-failure path does not currently reach those runtime mechanisms.

**Recommended disposition:** preserve the positive recovery/isolation acceptance
and schedule a bounded host-failure terminality/recovery prerequisite. Keep
W156162 open and its reviewed candidate unapproved for completion/import. The
prerequisite first needs an exact design and path/authority plan for independent
review; this recommendation grants no blanket source, schema or test changes.
Its behavioral target is an explicit owner-authorized ending of the exact failed
host attempt and its allocation, retaining all failure custody and refusing
without positive evidence that the old execution cannot continue. A legitimate
new-result path must be specified independently of releasing an old allocation.
Once implemented and reviewed, finish W156162's two-valid-result isolation proof
through that real boundary, with no forced release or fabricated runtime.

**Alternative requiring an explicit owner amendment:** accept the current durable
fail-closed result/target behavior and the measured recovery refusals as W156162's
delivery boundary, and defer positive host recovery and the dependent composed
isolation acceptance to separately scheduled Work. This changes step4 acceptance;
it is NOT supplied by the prior no-waiver ruling, this review, the tests, or the
new documentation saying the limitation is not delivered. The reviewer has not
selected this alternative on the owner's behalf.

## What already works, and what stops the remaining proof

- Actual three-Job setup admits B77/C61 with distinct bound tasks/manifests.
  B's configured host timeout is durably retained as its blocked IntegrationResult.
  C remains queued with the capacity owner's explicit deferral. The public
  composition recovery report contains no abandoned or recoverable offers.
- The first causal blocked result retains the only integration allocation. There
  is no model runtime and no validated completion that releases it. A second
  actor is not a configuration remedy: integration eligibility is restricted to
  the deployment's one configured integrator participant. Another independent
  deployment does not exercise collision isolation in this shared retention.
- Post-import failures durably hold the target before reference advance and
  receipt. The runtime-oriented held_status/abandon_held_lease refuse the host
  account. The lower trusted queue abandonment leaves the target blocked and
  entry held; it neither authorizes repair/reopen/new result nor releases the
  Job scheduler allocation.
- Normal continued serving and reopen do not repeat the retained host command
  or its materialization. Runtime-owned scratch cleanup and repeat close are
  independently accepted. These successful boundaries are not being reopened.

## Exact research seams and required design constraints

`v12/python/tools/stage_execution.py`: Integration.reconciled,
_reconciled_account and _job_workers bind actual results, absence of a model
runtime and the one configured integrator. The host execution boundary and its
durable failure must supply their own proof; no runtime identity can be borrowed.

`v12/python/src/baton_v12/job_manager/scheduler.py`: reconcile_allocations
settles logical capacity from accepted episode/runtime/completion facts. A host
failure ending would need equally exact allocation/stage/episode/attempt/actor
binding. Public release alone is not authority to bypass those checks.

`v12/python/src/baton_v12/job_manager/delegation.py`: the closed integration
observation contract and the owner adapter are candidate seams for carrying a
validated host terminal account. Existing completion must not be relabelled to
report success after failure. No new observation member/state is preapproved.

`v12/python/src/baton_v12/worker_manager/offers.py`: recover_on_restart handles
issued/accepted offers; it does not visit the claimed host stage. The empty report
is about offer state, not itself evidence of runtime quiescence. `intake.py`'s
abandon_attempt explicitly requires an attached runtime; `attempts.py`'s
request_cancellation requires a fixed manager attempt and preserves the separate
positive-quiescence gate. Extending these APIs is not currently authorized.

`v12/python/src/baton_v12/integration/recovery.py`: held_status and
abandon_held_lease bind a runtime delivery/assignment and positive manager-owned
quiescence/destruction. Absence and silence expressly do not satisfy that proof.
`integration/queue.py`: abandon_lease is a trusted lower boundary that retains
an exact account, not an operator proof of exclusion or target repair policy.

The design must distinguish causal failure with no integration entry/lease from
post-import failure holding an actual lease/target account. It must define the
owner and evidence for host terminality, explicit intent/replay after interruption,
the exact Authority assignment/manager offer/scheduler allocation ending, and
negative checks for stale, wrong-result, wrong-attempt or uncertain execution.
It must preserve failure custody, publication refusal, held target bytes and
legacy runtime recovery. A target repair/new-result decision is separate from
abandonment and cannot be silently supplied by this Work.

**No crash-before-record expansion.** Exactly-once execution across a crash before
the failure record was explicitly excluded by the accepted proposal. The recent
explanatory constant mentions it beside terminal settlement, but that does not
make the two one acceptance requirement. This disposition does not request an
execution-attempt journal, exactly-once guarantee, automatic retry, new capacity
pools, live provider run or installation.

## Candidate, spending and handoff

29 audited paths at HEAD f3fc9e12cc89bebf9524cd173103df7af67d5212; six new,
16 modified product/docs, seven existing tests. Existing-test authority and exact
W71879 attribution remain in the provenance packet; textual separation proves no
semantic independence. Immutable proposal and baton.merge preflight remain.

Author246 measured runs2530.5844189850177s plus four previously disclosed
unknown-duration activities. Reviewer147.72804738899322s cumulative, including
the earlier failed research probes. No numeric W156162 cap, reset or W103525
transfer. Reuse accepted deterministic evidence; do not repeat the unchanged
one-integrator drive while the required ending is absent.

Route this scope disposition to baton.decide. A ruling must be appended to
FINDING and reflected in PLAN before dependent implementation or an acceptance
amendment. No full-feature or import sign-off is requested here.

## Superseded — owner ruling2026-09-13T13:47:40Z

The proposed standalone host-terminality/recovery direction and either/or
recommendation above are superseded by the confirmed owner ruling in FINDING,
recorded by baton.prompt at M161029. Integration execution including reconciliation
verification must use managed Docker and be relocatable through the existing
input/output protocol. Keep positive recovery/isolation acceptance; do not add a
parallel host-only recovery architecture. Current planning proposal:
MANAGED-INTEGRATION-DESIGN-2026-09-13.md, claim161035. The historical evidence and
spending in this packet remain; its old recommendation is no longer actionable.
