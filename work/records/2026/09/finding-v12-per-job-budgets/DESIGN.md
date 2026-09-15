# Per-Job limits — accepted first slice and design history

Current disposition: owner event156258,2026-09-13T00:49:46Z, accepts the
per-invocation first slice, retained runner defaults and Job-wide overrides.
Cumulative accounting and separate role/stage pools are deferred. This explicitly
supersedes the undecided language in the original proposal below. FINDING pins
the ruling; PLAN now owns the bounded implementation path and acceptance list.
The original proposal is retained as decision history, including the deferred
cumulative section; its candidate path table is superseded by PLAN's finite list.

Prepared by baton.codex under W156162 claim156175,2026-09-13T00:39:13Z.
This is a source-based proposal, not an accepted schema or implementation plan.
No test, provider or application execution was performed.

## Decision requested

**Recommended first slice:** make the existing provider-turn and managed
verification-command ceilings configurable per Job, persist the resolved values
and expose their exact meaning. Preserve each runner's existing behavior when a
Job does not override it. Do not describe these ceilings as a cumulative Job
allowance or total agent working-time limit.

**Separate possible second slice:** cumulative execution and verification
allowances, with durable reservations and usage accounting across retries,
corrections and concurrent runners. The owner must select whether this is needed
in the first delivery. It is materially larger than substituting configuration
for timeout constants. A five-minute cumulative test ledger cannot be implemented
correctly by setting every subprocess timeout to five minutes.

The only confirmed product decision is per-Job configuration with explicit
resource/scope naming. No new numerical default, cumulative semantics, role split
or exhaustion behavior has yet been approved. In particular300 seconds is not a
new default. These recommendations require an owner ruling recorded in FINDING
before implementation.

## Existing boundaries, revalidated from current source

Paths below are relative to the configured `baton` repository.

| Owner and source | Current behavior | Meaning for this design |
| --- | --- | --- |
| `v12/python/src/baton_v12/job_manager/documents.py:JOB_MEMBERS`, `_job`, `_stage` | Closed submission/1 members contain Job input/policy digests, test scope, terminal policy and stage profile identities; no budget member | Put operator Job intent here through a deliberate document-version change; do not smuggle it through test_scope |
| `.../job_manager/submission.py:submit`, `_job`, `_stage`, `job_of` | Atomic normalized submission, signed operation identity, immutable Job insertion and public reads | Budgets must participate in the submitted identity and replay comparison; changing a file cannot change an already submitted Job |
| `.../job_manager/schema.py:JOB_COLUMNS`, `store.py:JobStore.transact` | Separate Job store, migrations and journaled operations | Own Job limits here, not in Authority assignment or Worker Manager lifecycle tables; any future budget ledger must not shadow runtime state |
| `.../job_manager/projection.py:status`, `tools/job_manager.py:_status` | Read-only status from durable owners | Show resolved values/provenance and accounting coverage without consuming allowance on a status read |
| `v12/worker/claude_agent.py:PROVIDER_SECONDS`, `_provider`, `_ran_provider` | 3600-second subprocess timeout for one provider invocation; reports timeout as provider failure | This includes provider reasoning, tools and waits within that invocation; it is not a whole Job, managed v11 turn, or sum across correction attempts |
| `v12/worker/claude_agent.py:VERIFICATION_SECONDS`, `_verify` | 900 seconds for one task verification command | Wrapper wall time, not CPU time or separately measured children; provider-internal test commands are not individually metered here |
| `v12/worker/integration_workload.py:VERIFICATION_SECONDS`, `run_verification` | 1800 seconds for one imported-target verification command | Another verification boundary that a Job setting must reach; retains structured failure on timeout |
| `v12/python/tools/stage_execution.py:_ConfiguredExecution._run`, `GIT_SECONDS` | Required tests in materialized causal/imported views use the300-second constant also used by Git helpers | Split test-command configuration from Git operation safety timeout; changing this constant would affect unrelated work |
| `v12/python/src/baton_v12/contracts/schema/agent-session-1.0.schema.json:sessionLimits` | Declares setup, turn and cancel-drain deadlines in milliseconds plus event/queue bounds | Existing profile vocabulary, not a cumulative Job ledger. `worker_manager/sessions.py` explicitly leaves turn/deadline execution outside that module; direct CLI provider uses the constants above |
| `.../contracts/schema/worker-control-1.0.schema.json:controlLimits` | Frame, extension, artifact, manifest and activity size bounds | Transport/data limits, not execution allowance |
| `.../worker_manager/offers.py:issue_offer`, `SETTLE_SECONDS`; `interrogation.py` | Offer expiry, claim settlement and interrogation deadlines | Keep protocol deadlines independent; a Job budget does not extend an offer or decide a claim's outcome |
| `.../worker_manager/oci.py`, `tools/single_worker.py:_engine_run` | OCI CPU/memory/pid isolation and bounded engine-client calls, default600 seconds for the latter | Container capacity and command-transport timeouts are not provider running time |
| `.../worker_manager/posture_slots.py`, `integration/schema.py` | Positive absence/quiescence governs release; integration leases do not expire by silence | Budget expiry never proves cleanup, lease release or writer exclusion |

The `.../` prefix in the table abbreviates `v12/python/src/baton_v12/`, except
the first `.../job_manager` rows which use that same prefix. Source inspection
found no token/cost accounting configuration at the mapped Job/direct-provider
boundaries. This is a bounded finding, not a claim about every provider API or
historical prototype. The JavaScript agent-profile implementation also certifies
sealed session-profile limits; no JS runtime change is proposed for this Python
deployment slice.

## First slice: two explicit per-invocation settings

**Proposed field names**, within a versioned Job `execution_limits` member:

- `provider_turn_seconds`: ceiling for each supervised provider invocation
  belonging to this Job, including implementation, independent review and
  derived-result judgment invocations.
- `verification_command_seconds`: ceiling for each owner-launched required test
  command belonging to this Job, including ordinary, reconciliation observation
  and imported-result verification.

Values are positive whole seconds within the supported runner range. Reject
booleans, fractions, zero, negative values, unbounded sentinels and unknown
members. Omission means inherit, not unlimited. Do not introduce per-role or
per-stage override trees in this first slice; a Job may set different execution
and verification values, and different Jobs may set different values while
sharing a worker. Role attribution remains visible.

Resolution is **Job override, otherwise versioned runner/profile compatibility
default**. Do not add a new deployment-default hierarchy until requested. Preserve
the observed3600/900/1800/300 values at their respective boundaries for legacy
Jobs, rather than pretending verification already has one uniform default.
An explicit verification override applies to all mapped verification runners
for that Job. Display the resulting per-boundary table, units, origin and
configuration digest, so inheritance is inspectable.

If a certified runner/profile has an independent hard maximum, reject an
unsupported override before admitting a new attempt. Do not silently clamp a
requested value and report it as applied. Existing setup/cancel-drain and
transport limits remain separately named. A profile change must not silently
reinterpret the admitted Job's resolved values; refuse incompatibility or use
the pinned compatible profile.

The Job store owns immutable intent and resolved configuration identity. The
composition passes a digest-bound read-only execution-limits document to each
worker/judgment/integration delivery. The worker uses that exact document,
cross-bound to Job/attempt and the accepted input/policy context. It never reads
host configuration or a mutable environment variable as a second authority.
Validate both the copied content and its binding on replay/adoption. Do not edit
the source task after submission or mutate a sealed profile merely to inject a
Job value. The exact delivery document/version must be pinned during the first
implementation plan; do not silently add members to task/2, exchange/1 or frozen
worker-control/session schemas.

The public submission and status need explicit version handling. Preserve
submission/1 semantics for existing documents and their original operation
signatures; migrate legacy records with a distinguishable compatibility origin.
Do not normalize old signed operands into new operands before replay lookup.
Reusing a submission ID with different limits must conflict. A retry/restart or
correction keeps the same Job limits; each new physical invocation gets its own
ceiling. **No cumulative remaining allowance exists in this slice.** A replayed
result must not create an invocation or renew a running invocation's deadline.
For a running adopted invocation whose remaining duration cannot be established,
preserve an explicit unknown/recovery condition rather than restarting its timer.

Visibility: show requested/resolved value, runner, scope `per-invocation`,
configured-versus-applied status, and the exact invocation/attempt identity. If
duration is published, label it measured, estimated or unknown and preserve
timeout/failed-start distinctions. Do not render a cumulative `remaining` value
from a per-invocation ceiling.

## If cumulative allowances are selected

This section is a proposed accounting contract for a separately bounded plan.
Do not implement half of it and advertise cumulative enforcement.

1. **Resources:** `execution_elapsed_ms` sums elapsed time of supervised provider
   invocations; `verification_elapsed_ms` sums elapsed time of owner-launched
   verification commands. Reasoning/tools inside an invocation count toward
   execution. Queue waits, human approval waits and manager idle time do not.
   Total submission-to-terminal wall time is a separate informational duration.
   W103525's v11 author/reviewer external-test ledger is not automatically input
   to this v12 Job ledger.
2. **Scope:** cumulative per Job across its stages, correction episodes, retries,
   worker replacement and manager restart, with stage/role attribution. Derived
   candidate checks and verification/review/approval workers are attributed back
   to the original Job. Separate hard author/reviewer pools are not implied;
   require an explicit owner decision if desired.
3. **Measurement:** one physical command/turn measured at its supervising runner
   boundary with a monotonic clock; charge nonzero exits, cancellations and
   timeouts. Parallel independent commands add their durations. A wrapper and
   its children are one measurement, not recursively charged. Commands invoked
   internally by the provider are execution time and are not advertised as
   separately observed verification. A live receipt must state coverage.
4. **Concurrency:** reserve a bounded allowance atomically in the Job budget
   owner before dispatch, keyed by Job/attempt/operation/configuration digest.
   Two workers cannot each spend the entire same remainder. Pass the granted
   maximum to the runner; settle actual elapsed and refund unused reservation
   exactly once. A retried physical command has a new operation identity and
   adds usage; a replayed receipt changes no usage.
5. **Crash/restart:** retain reservations and outstanding operation identities.
   A lost final measurement is unknown, never zero. Preserve the reservation
   until positive terminal evidence or an explicit owner resolution; expose
   measured usage separately from reserved/uncertain usage. Do not compare
   monotonic timestamps from different boots or refund on silence. Receipt
   attribution/duplicate detection must survive disconnected worker delivery.
6. **Resolution:** cap the next grant by both its per-invocation ceiling and
   remaining cumulative allowance. Exhaustion holds further chargeable work
   for that resource; it does not imply successful completion, a refused review,
   expired Authority claim, stopped process or free worker slot. Supervision,
   cancellation, result retention and safety cleanup remain owed under their
   own bounded authority. A test already run unsuccessfully cannot be credited
   as a passing required test.
7. **Changes:** changing an active Job's limit requires a separately authorized,
   journaled revision with actor/reason and preserved usage. No reset via new
   attempt/submission identity. First implementation can omit live amendment
   and expose a hold requiring a later explicit operation; it cannot silently
   use changed deployment defaults. Any decrease below spent/reserved allowance
   must retain that evidence and stop new grants, not invent negative usage.

**Open choices:** whether both cumulative resources are wanted now, their
numerical defaults, whether a Job aggregate or separate role pools should govern,
and whether a live increase operation belongs in the first cumulative slice.
Token or monetary ceilings are deferred until an actual provider usage/currency
owner and charging contract are established; elapsed seconds are not token cost.

## Exhaustion and correctness boundaries shared by both slices

A timeout requests/observes the runner's interruption, preserves partial
evidence and names the exhausted resource. `subprocess.run(timeout=...)` handles
its direct child; source already warns that descendants can survive. Continue
existing manager/session/custody reconciliation before asserting quiescence or
releasing capacity. Read-only status must never cancel, settle or replenish.

For per-invocation expiry preserve the current structured failure behavior; no
automatic re-offer/retry is added by this proposal. For cumulative expiry the
future plan must specify its explicit budget hold and resume authorization,
without hijacking offer expiry or marking a stage completed. A completed
integration with pending required tests remains incomplete regardless of budget.

## Implementation and deterministic acceptance map

These are proposed boundaries, **not authorization to edit**. After the owner
chooses the slice, pin the exact versioned delivery path and finite test list in
PLAN before assignment. No inherited W71830 test exception applies.

| Slice | Candidate paths/symbols to revalidate | Focused acceptance |
| --- | --- | --- |
| Job intent, persistence, replay, status | `v12/python/src/baton_v12/job_manager/{documents,submission,schema,store,projection}.py`; `v12/python/tools/job_manager.py` | Two Jobs with distinct limits; strict invalid values; omitted compatibility defaults; same-ID replay/conflict; migration; status read leaves stores unchanged |
| Resolve and deliver exact Job settings | `v12/python/tools/{stage_execution,single_worker}.py`; `v12/python/src/baton_v12/worker_manager/{launch,exchange}.py`; `v12/worker/baton_worker.py`; integration delivery/contract only if selected carrier needs it | Shared worker serves A then B without limit bleed; derived judgments bind correct Job; copied limits/Job/digest mismatch refused before provider/test execution; adopted attempt keeps its original limits |
| Provider and test enforcement | `v12/worker/claude_agent.py:_provider,_verify`; `v12/worker/integration_workload.py:run_verification`; `v12/python/tools/stage_execution.py:_ConfiguredExecution._run` | Inject fake runners/clocks, assert received timeout for each boundary; timed-out/failed command remains nonpassing; cleanup/unknown runtime semantics preserved; changing test limit does not change Git timeout |
| Operator documentation | `v12/python/DEPLOYMENT.md` and Job CLI examples | Names measured resource, scope, units, defaults and effective value; no claim of whole-agent-turn or cumulative enforcement from invocation settings |
| Cumulative accounting, only if separately selected | Proposed new `v12/python/src/baton_v12/job_manager/budgets.py` plus Job schema/public API and trusted runner receipt delivery | Competing grants, duplicate settlement, stale/cross-Job receipts, failure/timeouts, correction/retry accumulation, crash before/after dispatch/settlement, unknown usage, independent resource exhaustion and read-only visibility |

Existing test homes: `v12/python/tests/job_manager/test_documents.py`,
`test_submission.py`, `test_sweep.py`; `v12/python/tests/tools/test_single_worker.py`,
`test_stage_execution.py`, `test_stage_execution_status_hardening.py`;
`v12/python/tests/manager/test_claude_agent.py`, `test_integration_worker.py`.
Prefer new additive budget-specific cases/modules and reuse fixtures; do not
rerun their inherited suites under another subclass. Schema/delivery changes may
need bounded edits to existing expectations, which must be named in the accepted
implementation plan. Verification budget for that implementation is an owner
choice for this Work; do not borrow W103525's remaining seconds.

All ordinary verification uses deterministic runners/providers at the normal
boundary, real configuration and owner operations, and no sleeps or live models.
This preparation ran none of those tests. Reading code is not a passed baseline.
