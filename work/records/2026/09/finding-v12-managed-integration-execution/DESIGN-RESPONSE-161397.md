# Managed integration v2: conditions and disputed review findings

2026-09-13T14:46:38Z — baton.codex, claim161397.
DESIGN RESPONSE ONLY. No implementation, test execution or self-approval.

Responds to DESIGN-REVIEW-161344-2026-09-13.md, SHA256
`2b3b3c431725daa2ef11383e0b5d3c1823eec55c768aa598ad0d24d273380467`,
M161364 and return161365. V2 remains at its predecessor canonical path,
baton:work/records/2026/09/finding-v12-per-job-budgets/
MANAGED-INTEGRATION-DESIGN-v2-2026-09-13.md, digest
`aed73e10fa684af0d34160733de7199b453b6dffecffdd86ba79761ed016adf6`.
This addendum explicitly supersedes only the ambiguous conditions identified
below; unchanged v2 architecture, finite paths and evidence remain in force as
proposals. Do not rewrite the independent review or predecessor design.

## Source binding and method

Read the complete current handoff/review and current owning records, then the
actual functions below. These hashes were read with sha256sum, not produced by
running a test, database probe or provider. The two disputed files still match
research-161207.json, so these discrepancies are not explained by intervening
changes to those bytes.

| Path under v12/python | SHA256 |
| --- | --- |
| src/baton_v12/worker_manager/attempts.py | 99bd3f77f1968f76a6839632132e43cf6eecdfda0fe833b124b522e2895eaf55 |
| src/baton_v12/worker_manager/store.py | d776c90cb9332e7226fe6958cbff6ed80649f1135309e546e7a1f9949d2c843b |
| src/baton_v12/job_manager/scheduler.py | aec56f1fe1d78bd50798403b46648c63c6c6231678971399da339246a7901194 |
| src/baton_v12/integration/schema.py | 164de55dd44ab31f0e4a761dfa96eb1dddc893f0954d9697306f4306e0d4523d |

## Gate 1: accept both conditions

The guard applies only to transition **to released** in scheduler._move, never
to require_recovery. Root/member uncertainty must remain visible and occupied.
This clarifies v2's "every root release" wording; it does not forbid quarantine.
Apply the root/all-member check inside the release transaction, not in a stale
preflight. Existing unregistered allocation behavior stays as scoped in v2.

The success test must specifically drive reconcile_allocations through
_completed_integration, which is evaluated before the uncertainty branch. A
validated completion while the registered root remains open or a member remains
admitted must not release capacity. After admission closes and all actual members
end with owner evidence, the same completion may release that root once. Add a
negative proving require_recovery still works with open/admitted memberships.
These are focused additions within the proposed slice1 boundary, not new paths.

## Gate 2: disputed factual premise; narrow the proof, not the start API

**Confirmed source, contrary to the review:**

1. attempts.py:103 lists `cancel-requested` among transitions from
   execution_runtime `not-started`. The transition map at109 has no edge from
   `cancel-requested` back to `not-started` or `start-requested`.
2. `_order_quiescence` at2840 reads the actual attempt, and at2843–2845 calls
   observe on **execution_runtime**, value `cancel-requested`, when legal.
   Only AFTER that call does the runtime_id-is-None branch return ordered=false.
   Therefore cancellation of the ordinary activated/unstarted attempt does not
   leave its execution axis not-started. The source does not put this operation
   solely on worker_disposition as the review states.
3. request_runtime_start:1392 has the early execution_runtime check at1409.
   More importantly, its act at1480 calls observe(... execution_runtime,
   start-requested) at1499 INSIDE ControlStore.transact, after the lane claim.
   observe uses a savepoint; _decide:1076 rereads the attempt and rejects an
   illegal current transition. ControlStore.transact:592 uses BEGIN IMMEDIATE;
   a refusal rolls back the action, so the losing lane claim cannot remain.
   adapter.start is reached only after the start transaction returns at1504.
4. A cancellation-complete call followed by start therefore meets the early
   refusal. A stale start pre-read followed by the cancellation axis commit is
   refused by the transactional observation. This existing second check is the
   important fact missing from the review's analysis of only early preconditions.

**Qualification and explicit correction to v2:** the cancellation INTENT journal,
Authority fence, and execution-axis cancellation are THREE separate boundaries.
An intent/fence alone does not prove no future start. A start may commit between
them. Replace v2 §D's shorthand "if cancellation committed first" with "if the
execution-runtime cancellation observation committed before the start act".
The reader must require all the facts below, not merely the intent or ordered=false.

Proposed `unstarted_cancellation_of` remains a read-only owner operation in the
two already proposed worker_manager files. Read related ControlStore facts in
its existing `snapshot()` boundary: exact fixed assignment, committed matching
cancel intent, execution_runtime **cancel-requested**, no attached runtime, and
no committed or unresolved possibly-effective runtime.start for that exact
assignment. Independently verify the actual Authority cancellation/fence through
the current owner port/operation readers. Unknown/refused/mismatched evidence
refuses proof; no cross-store atomicity is claimed. The committed cancellation
axis is durable and does not permit a later fresh start transaction.

If a start committed first, even if its adapter call has not happened and no
runtime is attached, the reader refuses. A replayed committed start can bypass
the act callback in ControlStore.transact; excluding its committed operation is
therefore essential, not redundant with the axis. Reconcile/positively exclude
that actual start through existing runtime owners, keeping capacity held. An
interrupted cancellation before its axis observation also refuses proof until
ordinary cancellation resumes. Never turn intent or an empty runtime_id into
quiescence, destruction, Authority-gate discharge or successful Work outcome.

**Inferred from source, not dynamically certified:** existing transition and
transaction boundaries can support this narrower no-start proof without a new
start latch or generic transition rewrite. Independent re-review must decide it;
the gate remains open and no reader is implemented on this inference alone.

Bounded future tests after approval: cancellation fully before start; stale start
pre-read losing to cancellation's axis write; start intent committed before the
axis with delayed adapter call; interruption after cancellation intent/fence but
before the axis; exact reopen/replay and foreign-assignment refusal. Count actual
fake adapter calls and inspect lane/journal outcomes. The existing
tests/manager/test_attempts.py test_an_attempt_with_no_runtime_orders_nothing
asserts ordered=false and no agent calls, but does NOT assert the resulting axis
or future-start refusal. Preserve it; add these cases in the proposed new test
scope. No tests were run or weakened in this turn.

## Gate 3: existing uniqueness is present; preserve strict upgrade admission

**Confirmed source, contrary to the review:** integration/schema.py:432 contains
`UNIQUE (canonical_target_id, source_proposal_id, target_revision)` inside
integration_results. The three key columns are NOT NULL. The reviewed claim that
only result_id and leases_one_live_per_target are unique overlooks this table
constraint. A separately named CREATE UNIQUE INDEX is not required for it.

IntegrationStore._adopt:452–524 validates the complete normalized object
definitions against expected_shape. `_shape`:177 explicitly explains that
SQLite auto-index names are omitted because their constraints are already in the
table definition being compared. A schema5 table lacking this uniqueness is
not a conformant historical store the proposed upgrade should accept.

Retain v2's one-result invariant and add the new table/cross-representation writer
checks in the same target-global transaction. Do NOT add a redundant unique index
to the old table or silently deduplicate old records. Explicit 5→6 upgrade must
first validate the exact old shape, then check for duplicate key groups as an
integrity diagnostic before mutation. If any exist, refuse with offending result
IDs and preserve the old store unchanged; do not relabel them valid history.
This diagnostic is defense against malformed/corrupt input, not a claim that
valid schema5 normally permits duplicates. Read-only5/6 open does not upgrade;
unknown shapes/versions and changed live-target exclusion remain refusals.

The new managed representation still needs a cross-table check: two separate
per-table constraints cannot enforce uniqueness across both. Test conflicting
legacy/new keys in both insertion orders, exact replay versus changed content,
unchanged legacy records/live leases, and malformed-old-shape refusal with no
partial migration. Keep one target-global store, not a writable copy.

## Gate 4: accept trusted evidence-source condition

The trusted placement owner's publish_collected_integration contract gains a
REQUIRED locally composed execution-owner capability (not a serialized worker
operand). It obtains positive exclusion from the trusted runtime adapter on the
node that executed the exact phase, binding actual assignment/attempt/start
operation/runtime identity and the frozen collected phase reference. The worker's
phase report, a stop order, timeout, or an unrelated coordinator-A runtime cannot
substitute for that owner's answer. An unavailable or mismatched execution owner
refuses publication. No remote backend/RPC or copied Authority credential is
introduced by this interface clarification.

The existing request operands and checks remain: canonical target, entry, current
lease/fence/grant, ADMITTED old revision, authorized candidate and collected phase
reference. Only the trusted target owner resolves local target/source capabilities
and performs CAS/settlement after exact exclusion and content validation. Test a
foreign-node/foreign-attempt stop answer and a worker-forged stopped report as
negative inputs, alongside stale grant and changed target. Those tests use fake
capabilities, labelled honestly, until separately selected runtime verification.

## Gate 5 and next handoff

Slice1's existing11 source paths and four proposed new test paths remain the
bounded proposal in v2 §C. No start/cancel mutation is added on the disputed
premise above. Existing-test expectations are unchanged; new bounded cases are
additive and do not cite the expired W71830 exception. Slice2/3 and actual runtime
delivery remain future independently selected work. Proposed120s author/30s
reviewer remains unapproved; this Work's measured verification is still0.

Return to baton.impl for **independent DESIGN re-review only**: verify the exact
axis/transaction and schema lines at the pinned hashes, then accept or refute the
narrowed no-start proof and the three accepted conditions. If it still needs a
new start transition, identify the precise interleaving satisfying every reader
precondition yet reaching adapter.start; return exact bounded scope rather than
implementing it. Review only this delta plus affected v2 contracts; no full new
research loop, tests, source edits or PROGRESS entry. Append a new review here;
never edit review161344. Owner exact-slice approval follows independent acceptance.

Final pinned-dependency checks remain mandatory in selected Job completion.
No environment changes, tests, executable probes, Git mutations or direct store
access occurred. W156162 retains author246runs2530.5844189850177s plus4unknown
activities and reviewer147.7342205499972s; W103525 retains its own ledger.
No spending reset/transfer. Two guessed test filenames were absent; rg --files
located tests/manager/test_attempts.py. This was a corrected search mistake,
not missing required policy/evidence or a Baton defect.
