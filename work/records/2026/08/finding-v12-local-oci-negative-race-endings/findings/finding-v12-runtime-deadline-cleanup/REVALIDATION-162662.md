# Runtime deadline revalidation and proposed implementation boundary

2026-09-13 — baton.tuner, W32577 claim162662. Source inspection and planning
only. No product/test edits, tests, probes, Docker, provider calls, environment
changes or Git mutation. Verification subprocess spending for this assignment: 0.

## Authority and current result

Read AGENTS.md, docs/EFFECTIVE-BATON.md, docs/AGENTS-MAILBOX-PROTO.md, the complete
three-file W32577 dossier, all W32577 events and T32577 messages. Canonical
phase queued succeeded at162661 and standalone claim at162662; poke162657 was
answered working at162663. Independently read the actual M33822 in T32382:
the ruling matches the newly pinned FINDING. No missing owner decision or
pickup blocker remains.

**Confirmed:** the runtime-attempt deadline gap remains. Later per-Job limits
and managed recovery supply useful owners, but neither supplies this deadline.
**Correction to the historical inventory:** deadline-related fields now also
occur in launch configuration, custody command bounds and offer settlement.
The old broad statement that only interrogation contains a deadline is not a
current inventory. The narrower statement remains true: no inspected owner
persists and enforces the M33822 runtime-attempt deadline/policy pair.

## Reusable owners and the remaining gaps

All source locators below are under baton:v12/python/.

| Owner | Confirmed behavior and consequence |
| --- | --- |
| src/baton_v12/job_manager/execution_limits.py: LIMIT_MEMBERS, GENERATIONS, resolved | Only provider_turn_seconds and verification_command_seconds; scope is per-invocation, with frozen compatibility generations. Do not use either number or that generation as a runtime-attempt deadline. The owning per-Job FINDING also distinguishes these boundaries. |
| src/baton_v12/worker_manager/launch.py: _configuration | Validates Job-owned execution limits and their digest. This is launch delivery of those limits, not deadline cancellation authority. |
| src/baton_v12/worker_manager/store.py: _now, transact, replay, operation_record | One injected manager clock, serialized writes and effectively-once records. Immutable deadline configuration/first observation can use the existing journal; a new table is not inherently required. |
| src/baton_v12/worker_manager/attempts.py: record_attempt, request_runtime_start | Attempt configuration already includes policy_digest. Start journals intent and takes the runtime lane before calling the adapter. It currently pins no runtime deadline. Bind a selected deadline policy before that external start, including restart paths. |
| src/baton_v12/worker_manager/attempts.py: request_cancellation, _order_quiescence | Journals exact intent, calls AuthorityPort.cancel, then orders agent cancellation and runtime stop. Stop return is not quiescence or absence; worker_disposition is not manufactured. A deterministic reason tied to the pinned deadline can identify the policy-selected cancellation. |
| src/baton_v12/worker_manager/attempts.py: unstarted_cancellation_of | W161230's current candidate proves fenced-before-start only with committed cancellation axis, matching intent/Authority fence, no attached runtime and no committed exact start. Preserve all six conditions. A runtime absent from the attempt row alone is insufficient. |
| src/baton_v12/worker_manager/intake.py: authorize_cleanup | Ordinary cleanup needs an actual intake receipt, retention authorization and an ended assignment. Without a receipt it returns blocked-on-intake. Merely adding a timer and calling this function cannot complete a deadline ending for a worker that never answered. |
| src/baton_v12/worker_manager/intake.py: abandon_attempt | Explicit operator/route-policy abandonment has its own intent/fence identity and excludes timer inference. Do not relabel a deadline cancellation as abandonment to obtain receiptless cleanup. Its ordering and retained-output behavior are reusable design evidence. |
| src/baton_v12/worker_manager/intake.py: _not_an_ending, _settle_recordless_cleanup | Uncertain absence/provider-unsettled results must remain retryable; positive absence plus settled providers precedes retained cleanup and lane release. Preserve untrusted results without inventing an intake receipt. |
| src/baton_v12/worker_manager/oci.py: OciAdapter._removed | Shared exact force-removal, observation, credential and launch teardown. A typed deadline cleanup wrapper can reuse this core without redesigning the engine. |
| src/baton_v12/worker_manager/intake.py: discharge_quiescence_gate, discharge_abandoned_quiescence_gate | Local cleanup and remote gate discharge are separate journalled acts. Current readers accept their own cleanup kinds; a new deadline cleanup kind needs a corresponding validated absence/discharge composition. Do not treat a destroyed axis alone as gate evidence. |
| src/baton_v12/worker_manager/schema.py and store.py:_validate | ControlStore is schema18 with a strict fresh-store boundary, not an automatic migration framework. Prefer journal-only additions; if implementation proves a new relation necessary, explicitly revise the path/compatibility plan before adding one. |

**Inferred from these owners:** the smallest complete correction has two joined
pieces: immutable policy/clock observation, and a typed cancellation cleanup
crossing for the no-receipt case. A wrapper around request_cancellation alone
would leave a required acceptance unmet. No runtime result was measured here.

## Proposed bounded implementation

This is a proposal for independent baton.feat design review, not product-edit
authority from this planning claim. Preserve M33822 without another owner vote.

1. Add worker_manager/deadlines.py with closed policy, pinned-deadline and
   deadline-reached documents. Trusted manager composition supplies the selected
   route/runtime policy, its exact digest/generation, positive seconds and action
   report-only or cancel. Bind it to the recorded attempt policy and exact fixed
   assignment. Do not accept caller absolute timestamps or worker-provided policy.
   No universal numerical default or change to per-Job limits is proposed.
2. At request_runtime_start, persist the selected policy and manager-derived
   start instant/deadline before adapter.start. Use a stable per-attempt/assignment
   journal identity; put policy/action/duration/generation in the signed operands,
   not the identity, so changed policy collides instead of minting another timer.
   Pin an explicit no-deadline selection for legacy/unconfigured callers so a
   retry cannot silently add or remove a timer. The start transaction must verify
   its exact pinned selection; configured callers cannot bypass it by omitting
   the policy on retry. Keep lane acquisition and start intent ordering intact.
3. Provide an explicit manager observation/advance API and reader. Observation
   uses store._now, preserves the first accepted reached instant, and changes no
   execution/worker/output axis. A before-deadline read must not commit a permanent
   not-reached result that prevents later observation. Recheck eligibility under
   the write lock. Fresh stale/terminal attempts refuse; exact committed retries
   still replay. Clock rollback never moves the persisted deadline or authorizes
   early expiry; policy changes cannot reinterpret an existing attempt.
4. report-only returns that durable observation and makes no Authority, agent,
   engine or output act. cancel validates the pinned observation and policy,
   then uses the existing Authority-first cancellation. Read back the matching
   cancellation intent/fence before cleanup; an unrelated earlier cancellation
   must not acquire a second reason by retry. A collision holds for reconciliation
   through its existing owner rather than replacing its evidence.
5. With genuine frozen/collected output, retain ordinary receipt/retention cleanup.
   With no worker disposition/receipt, add a typed deadline cleanup authorization
   and OCI wrapper that reuse exact removal/provider settlement and retained
   directory custody. Do not call abandon_attempt or fabricate completed,
   cancelled, unable, a freeze or an intake receipt. Preserve existing accepted
   output; a race that changes output eligibility must choose the appropriate
   owner path or hold, never discard it. New terminal eligibility is checked in
   the journalled decision, not only before it.
6. Add the matching cleanup-proof reader and exact Authority gate discharge for
   deadline cleanup. Preserve ordinary discharge when ordinary cleanup was used.
   Remote commit/local receipt loss replays the same act. Uncertain engine state,
   provider-unsettled teardown and unknown start keep capacity held. Resolve an
   interrupted start by exact reconciliation before selecting a runtime. A truly
   never-started attempt uses the accepted no-start proof, never forged absence.
7. Expose the manager API and document its explicit invocation/configuration
   boundary. This delivery does not claim a background timer or deployed Job
   runner configuration: adding a periodic driver or a Job submission setting is
   a separately named consumer change, not required to prove the manager seam.

Independent review should resolve the concrete policy-supplier signature and
the no-receipt command/proof shapes against these invariants before source work.
In particular, confirm that preserving untrusted output through the existing
recordless custody core satisfies M33822; do not silently widen abandonment
semantics. These are implementation-design questions, not an unanswered ruling
about what deadline expiry means.

### Proposed exact path set

Under baton:v12/python/:

| Path | Change / ownership |
| --- | --- |
| NEW src/baton_v12/worker_manager/deadlines.py | Policy pin, observation, policy-selected advance and typed proof orchestration |
| src/baton_v12/worker_manager/attempts.py | Minimal start-policy pin/check hook; reuse existing cancellation. Shared with W161230; serial handoff required. |
| src/baton_v12/worker_manager/documents.py | Closed deadline/policy/cleanup documents. Shared with W161230; serial handoff required. |
| src/baton_v12/worker_manager/intake.py | Narrow deadline authorization/proof/discharge composition reusing settlement/custody owners |
| src/baton_v12/worker_manager/oci.py | Typed deadline destroy wrapper over _removed |
| src/baton_v12/worker_manager/__init__.py | Export the new public manager APIs |
| NEW tests/manager/test_runtime_deadlines.py | Deterministic policy, replay, ordering, negative and race coverage |
| NEW tests/manager/test_runtime_deadline_engine.py | Deadline-specific real-engine composition using existing Lifecycle fixture |
| tests/manager/test_boundary_inventory.py | Register new closed boundary ownership if its exhaustive inventory requires it |
| tests/manager/test_contracts_inventory.py | Register new public document/API contracts if required |
| DEPLOYMENT.md | Describe the explicit manager API and limitations; W161230 owns this path now, so serialize this small documentation addition too. |

No changes proposed to interrogation.py, Job execution_limits.py, launch.py,
worker images, Authority protocol, schema.py/store.py, tools/single_worker.py or
W161230's test_reconciliation_worker.py. They are inspection/reuse dependencies.
If the concrete implementation needs another path, record why and coordinate
ownership; standing test authority already covers necessary test adjustments.

## Exact overlap coordination

Canonical W161230 at snapshot162665 is active with baton.claude, claim162592.
Read its current PLAN, IMPLEMENTATION-HANDOFF-162279, SLICE1-SCOPE-161491 and
newest review-2026-09-13T18-02-07Z.md. Current owner clarifications M162617 and
M162634 retain local managed execution and existing input/output reuse. They do
not transfer Worker Manager ownership to W32577.

Directed asynchronous M162672 in T32577 asks baton.impl for exact release of
attempts.py/documents.py and any additional runtime/launch/schema/test overlap.
No answer was present at snapshot162679. W161230 retains its live candidate;
no product path has been acquired or edited here. DEPLOYMENT.md is also shared
per its accepted path table. The first safe parallel work is this dossier and
design review. After that, new deadline/test files can be assigned explicitly;
shared hooks and documentation follow an exact file handoff and fresh base
comparison. W161230 completion is not a prerequisite for the independent files.

## Focused verification proposal and acceptance mapping

No test execution belongs to this initial assignment. For implementation,
propose 120 seconds cumulative deterministic author subprocess time and
60 seconds independent reviewer time, with failures charged and a persisted
remaining-budget check before each command. These are proposed bounds for
the next bounded handoff, not an allowance consumed or granted here. No
predecessor spending transfers. Use project-pinned dependencies and record actual
versions; W161230 currently records a jsonschema version gap, which is not proof
that this future environment will have the same gap.

- Policy and clock: before/exact/after deadline; rollback; malformed duration;
  caller timestamp exclusion; changed digest/generation/action; omitted policy on
  retry; restart preserving the original instant; concurrent first observers on
  separate connections. Compare durable records, not just returned dictionaries.
- Ordering: report-only leaves a real fake-adapter execution untouched; cancel
  records observation then Authority fence before any agent/engine effect.
  Authority refusal/unknown result makes zero destructive calls. Cover crashes
  after pin, start intent, reached observation, fence, removal and gate discharge.
- Endings: genuine output follows intake/retention; receiptless output remains
  untrusted and retained with worker_disposition unchanged. Already-quiescent,
  stale/terminal, concurrent completion, already-started recovery and no-start
  cancellation follow their actual owner facts.
- Settlement: exact runtime/assignment/generation only, sibling preservation,
  uncertainty and provider-unresolved retry, no lane reuse before positive absence
  and both providers settle, correct remote gate receipt before scheduler reuse.
- Run the new deterministic module, then selected existing cancellation,
  interrogation, lane and receiptless-cleanup regression classes affected by the
  final diff. Name selectors and expected cost in the implementation handoff;
  do not run a broad suite because the work changed hands.
- Preserve the historical required real-Docker acceptance as a separate final
  gate. Named engine-specific question: while the exact container is present at
  expiry, does policy-selected fencing precede real force-removal, positive exact
  absence and real credential/launch settlement, with a sibling preserved and
  lane reuse blocked until settlement? A fake engine cannot prove daemon removal
  or mount/provider effects. Reuse Lifecycle/production providers with a
  deterministic workload; no live model is needed. Require the selected case
  rather than skip on missing Docker. Propose one case with a 180-second hard
  outer bound after image/daemon readiness is established, no pull/build/install
  in that run; record any failure and reassess before another run. This later
  gate is not executed or authorized by the present planning claim.

W32382/W33755 remain unsatisfied until joined implementation and this required
evidence pass independent review. Design acceptance alone cannot close W32577.

## Inspected source fingerprints

These bind the observations, not an integration candidate. Shared files must be
revalidated when their owner releases them. Paths are under baton:v12/python/.

| Path | SHA256 |
| --- | --- |
| src/baton_v12/worker_manager/attempts.py | 8c321ac7d9c1c5764c4f181e50a1e99d911c481dad0c20ea1ac11d7a2b349730 |
| src/baton_v12/worker_manager/documents.py | b3fc43f26ffef5a76f1329b273ea722f04c4544b722511c681c3c1a0418b20bd |
| src/baton_v12/worker_manager/intake.py | d326fe41d0ad8ca90950be9735f4c05b1c537e70e6827f760867969830eae7b7 |
| src/baton_v12/worker_manager/oci.py | 68bb8831331ec1ac07b7b6bdb8a559573be348fe80ba796e50607d4b94af7b2f |
| src/baton_v12/worker_manager/store.py | d776c90cb9332e7226fe6958cbff6ed80649f1135309e546e7a1f9949d2c843b |
| src/baton_v12/worker_manager/schema.py | 56c54054b5170b49a77ef4af0b13dd7f8ff8ee14564785c449e726df48ed7df1 |
| src/baton_v12/worker_manager/lanes.py | f2a086de468c84d0cd7eb3cbcedec55c2cd12415a051b93bdcc8342341e2f21c |
| src/baton_v12/job_manager/execution_limits.py | 073ea7104df1aa4cf097cf12e7c7371a2cc918c95e2dd0c7de9225b734230442 |
| src/baton_v12/worker_manager/launch.py | d89159a36a40c383ba3e838b70e31eaa836b4e2d37b919e2020ef7b41e70e508 |
| tools/single_worker.py | 3b78842c59a46b30a2a542cac6e7ed860e32c5e5645baed643c478a4eddd3c49 |

Operational notes: initial bare detail omitted required work= and was corrected;
an ownership request on T161230 with on=W32577 correctly refused because that
thread does not label W32577, then succeeded on T32577. Initial guessed source
paths (top-level worker_manager and cleanup/policies/runtime_profiles/authority/
retirement modules) do not exist; rg --files located the actual owners above.
These are lookup/invocation mistakes, not unavailable required policy/dossier
files or Baton defects. All required policy and W32577 dossier files were read.
