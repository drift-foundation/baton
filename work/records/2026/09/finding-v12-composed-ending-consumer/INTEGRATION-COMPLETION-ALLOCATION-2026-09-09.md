# Proposed allocation: observe and finish the integrated stage

**Accepted 2026-09-09 by owner M126545; recorded under review claim126550.**
The owner approved this exact allocation, scheduled tests, seven-path provider
via baton.impl returning baton.bug, then two-path W122060 consumer via baton.tune
after independent provider acceptance. The terminal pass recommendation below
is confirmed: current integrator fixed assignment, configured outgoing
review_route, proved worker exclusion and owned committed integration completion.
This supersedes the proposal-only/unallocated status in the historical text
below. Provider Work is W126558, bound to
`findings/finding-integration-stage-observation/`; its exact document is pinned
in `OBSERVATION.md` there before implementation. No broader allocation follows.

Reviewer proposal, claim125625; **not implementation authority**. Evidence and
diagnosis: `review-2026-09-09T06-15-16Z.md` and its independent probe. The existing
fixture now reaches a real integrated worker result. A diagnostic consumer call
also commits the Authority receipt and releases the coordinator lease; it still
does not complete the Job stage or end its current Work assignment.

## Requested decision

Approve the two implementation pieces below, including the exact added source
allocation and bounded tests. Recommended terminal disposition: reuse the
integration worker's existing configured outgoing `review_route` and existing
Authority `pass_work` on its own fixed assignment, behind proved worker
exclusion and the owned committed integration result. Do not introduce a close
grant, terminal destination setting, new scheduler role, or a special no-gate
interpretation. Confirm this disposition as the campaign's terminal handoff;
handler absence alone is not its specification.

No new planning Job is proposed. After allocation, reviewer creates the one
implementation provider Work/dossier and its gate immediately, then routes
the disjoint pieces under successful claims. W122060 retains all existing
evidence and the final joined acceptance. Until then its current four-path
reservation remains; no other participant may assume these proposed paths.

## Provider: integration observation and owed-act boundary

Proposed Handler baton.claude via baton.impl, independent review baton.bug.
New causal child under this dossier, provisionally
`findings/finding-integration-stage-observation/`; create and bind only together.

Exact proposed paths relative to `v12/python`:

- `src/baton_v12/job_manager/delegation.py`
- `src/baton_v12/job_manager/projection.py`
- `tools/job_manager.py`
- `tests/job_manager/test_delegation.py`
- `tests/job_manager/test_status.py`
- `tests/job_manager/test_exchange.py`
- `tests/job_manager/test_tool.py`

Bounded outcome: a distinct integration observation capability through the
serving and observation-only surfaces; ordinary ticks select integration's
conclude operation when its owned result/handoff still needs consumption, and
the Job projects completion only from the committed terminal account. Preserve
the existing exchange vocabulary and behavior for implementation/review. The
provider does not read private integration storage or perform integration,
handoff, refresh or credential acts in a reader.

Proposed interface: an optional `observe_integration(stage)` capability, absent
for existing deployments. Its closed answer distinguishes unstarted/pending,
answered with conclusion owed, committed terminal completion, and held/invalid
evidence, bound to this stage/episode/attempt/claimed offer and fixed assignment.
The deployment owns discovery and exact receipt cross-binding; the provider
owns validating the closed observation and projecting/owing the appropriate
act. Provider and consumer must pin the exact document before implementation;
this is an implementation detail under the accepted outcome, not another owner
approval if it stays inside these paths and boundaries.

Tests: add focused positive/negative cases for integration pending/answered/
completed/held, missing capability, foreign attempt or offer, uncommitted result,
and read-only operation. Existing non-integration expected behavior stays
unchanged. Bounded fixture/expected-document additions for the optional
observation member are requested explicitly; do not relax existing assertions
or revise unrelated test results. No store schema, registry, integration driver,
Authority, worker runtime or manager loop source allocation is requested.

## W122060: consume the interface and finish the same Job

Proposed Handler baton.tuner via baton.tune, independent review baton.bug, after
the provider's independently accepted interface is available. For this pass,
edit only `tools/stage_execution.py`, `tests/tools/test_stage_execution.py`, and
the owning dossier's attributable progress/evidence. Keep the reviewed
single_worker.py/test_single_worker.py bytes and all accepted negatives.

Use public delivery, assignment, coordinator and Authority readers to supply
the integration observation in both serving and read-only factories. Re-enter
the existing accepted driver through ordinary scheduling. A worker result is
not completion until its owned Authority receipt and coordinator settlement/
release exist. End the current integrator assignment through the confirmed
terminal handoff only after required exclusion evidence. Use fixed operation
identity and exact readback; replay a lost answer without targeting a later
assignment or repeating an external integration. If the existing public runtime
or custody operations cannot prove that boundary, report the exact missing
capability before editing another path; do not substitute abandonment or
invent successful cleanup evidence.

Reuse `OrdinaryTerminalLifecycle` unchanged in meaning, strengthen its terminal
checks within this bounded scope, and retain the actual factory/ordinary-tick
path. Assert corrected bytes, required-test success, immutable integration
receipt, integrated entry, released lease, completed stage, exact terminal
handoff and no remaining handler. Preserve held/uncertain-effect behavior and
prove status reads perform no external act. Only after ordinary completion,
finish the existing committed-handoff-before-local-ack reconstruction cut;
W119114 reuses these bytes and owns the remaining final custody acceptance.

Each implementation piece declares its evidence question before testing and
enforces a cumulative20s test/probe-process limit. Do not rerun accepted provider
suites. Reassess the split at each handback; a repeat stall at this boundary
requires whole-handoff diagnosis before another allocation. This proposal
does not claim the requested repair will prove any untested later transition.
