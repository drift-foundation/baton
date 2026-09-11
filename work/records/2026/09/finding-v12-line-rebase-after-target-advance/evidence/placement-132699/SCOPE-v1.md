# Serial implementation and verification proposal — revision 1

baton.codex claim131466. Owner event131446 approves lifecycle direction only.
CONTRACT-v1.md and this exact scope/cost require approval before implementation.
All paths below are relative to v12/python. No product/test edits or runtime
have occurred on W131409. No executable child has been created speculatively.

## Serial slices and ownership

Use three child Works under this existing W131409 dossier, with each Work and
dossier created together after approval. Impl -> independent reviewer for each;
one active writer. Slice B depends on accepted A, C on accepted B; W131409 closes
only after all three independently accepted. W130224 remains blocked on W131409
through dependency131454. Retain exact candidate at each handoff; no Git mutation.

### A — custody, effective base and sealed prelaunch handoff

Product paths, and only these:

- src/baton_v12/checkpoint_profiles.py
- src/baton_v12/worker_manager/schema.py
- src/baton_v12/worker_manager/review_cycles.py
- src/baton_v12/worker_manager/target_rework.py (new)
- src/baton_v12/worker_manager/attempts.py
- src/baton_v12/worker_manager/offers.py

Tests:

- tests/manager/test_checkpoint_profiles.py
- tests/manager/test_review_cycles.py
- tests/manager/test_store.py
- tests/manager/test_attempts.py
- tests/manager/test_offers.py
- tests/manager/test_target_rework.py (new)

Own the v1 typed records/readers, schema19 fresh-store boundary, immutable
creation/effective-base distinction, retained history/current eligibility,
profile transplant/conflict evidence, writer/freeze rework binding, and atomic
seal versus claim/activation/start admission. Existing claim/launch signature
and refusal contracts remain except the explicit new sealed-attempt refusal.
The bound Authority pass is composed through the existing session, without
editing Authority/core, extending cancellation authority or clearing any gate.

Public provider acceptance: a real old accepted checkpoint plus actual advanced
target content prepares clean same-line evidence preserving both changes; old
audit/create-recover survives. Exact claimed-but-unstarted attempt is sealed,
canonically handed back and cannot start afterward. Conflict/started/uncertain/
unresolved claim inputs hold; identity/tamper/foreign inputs refuse. Prove
profile and cross-owner replay cutpoints. Do not claim ordinary Job completion.

Existing test edits are limited to the new schema/record/writer fields and
target-rework behavior, their exact boundary expectations, and the necessary
fixtures/registries. Preserve all prior isolation, generation and startup guards.

### B — target-driven Job rounds and capacity

Product paths:

- src/baton_v12/job_manager/target_rework.py (new)
- src/baton_v12/job_manager/episodes.py
- src/baton_v12/job_manager/documents.py
- src/baton_v12/job_manager/manager.py
- src/baton_v12/job_manager/projection.py
- src/baton_v12/job_manager/delegation.py
- src/baton_v12/job_manager/scheduler.py

Tests:

- tests/job_manager/test_target_rework.py (new)
- tests/job_manager/test_documents.py
- tests/job_manager/test_sweep.py
- tests/job_manager/test_launch.py
- tests/job_manager/test_scheduling.py
- tests/job_manager/test_status.py
- tests/job_manager/test_delegation.py

Own v1 target-driven intent/round, optional ordinary-sweep action and its public
capability boundary, whole-triple episode replacement, rederivation after acts,
stale-attempt guards, exact typed settlement-driven allocation release and
read-only projection of holds. Do not alter the verdict-only correction path
or add generic completed to release endings. No direct control/Authority store
read by the Job owner; consume A's typed readers.

Provider acceptance: one real custody outcome causes exactly one successor
triple and releases only its retired integration allocation. Competing seals/
starts and stale sweeps cannot grant an obsolete attempt. Replay after remote
pass/custody commit/Job round reuses original identities. Wrong/missing evidence,
live runtime/lease and foreign Job refuse or hold without partial episodes.
Fresh integration remains gated by fresh implementation/review. Ordinary
status performs no rework operation. No consumer terminal acceptance yet.

Existing test changes only cover new optional capability/document/endings,
the target-driven path and necessary fixtures/registries. Preserve old review
correction, exclusion, fault/principal capacity and read-only guarantees.

### C — configured composition and ordinary public witness

Product path:

- tools/stage_execution.py

Test path:

- tests/tools/test_stage_execution.py

Own per-target read-only nominated content injection and pure preflight, exact
per-Job effective-base task/input generation, ordinary rework action composition,
new proposal/port binding and historical publication lookup through
integration.driver.publication_for_attempt. Do not modify provider semantics.
Retain original deployment creation bindings and immutable manifests/results.
Support /1 and no-drift /2 unchanged; missing rework capability holds specifically.

Acceptance is CONTRACT-v1 section7's actual A/B path on ordinary configured
ticks, with immutable identity evidence and final content preserving both
changes. Keep the stale-candidate negative; add the positive, fresh review/
required-test proof, conflict and target-race controls. The existing fixture
comes from W130224's retained candidate below, not an invented new canned path.
Only those bounded fixture/tests plus necessary shared setup/registries change.

This prerequisite may produce the full consumer witness under approved C scope.
W130224 still independently judges its complete serving acceptance afterward;
the evidence is reused, not the consumer obligation transferred or waived.
W119405 retains joined reconstruction and any warranted final module check.

## Exact current base and drift checks

Snapshot source/test identities are in evidence/contract-131466/base.json.
New paths must be absent at dispatch; if any appear, stop for ownership
coordination and rebind rather than overwriting. Each later slice revalidates
the independently accepted predecessor bytes and current unmodified paths.

Shared consumer baseline from review claim131441, both mode0664:

- tools/stage_execution.py:
  28ee42a2aaca4e9f596ff5accfebb60f5bc1c6f888e1c9e3c128d7ee93993302
- tests/tools/test_stage_execution.py:
  1ebba932945b8f1c93f80aaa61835b3188ef489073fb39887a20806d6b7fe93c

Retained in W130224 evidence/review-131441/candidate/. The accepted scheduler
prerequisite is aec56f1f and scheduling test79ba448c, both0664, full digests in
W131187 evidence/review-131324/candidate.json. Slice B's reviewed scope is the
only new authority proposed to change that accepted scheduler.

Paths outside the exact lists require a recorded scope decision first. Existing
helper/public contracts should be reused. In particular no Authority, integration
admission/driver/runtime, OCI adapter, registry, native provider, deployment store
or human Git edits are granted. Tests own their disposable resources through
their existing execution boundary. No proposed schema migration or live rollout.

## Separate verification envelope proposed for approval

Propose200s NEW cumulative W131409 verification, carrying0s used. This is a
ceiling and serial allocation, not a prediction or fresh budget per child.

| Slice | Implementation | Independent review | Scope of execution |
| --- | ---: | ---: | --- |
| A | 80s | 8s | Focused real-profile transplant/conflict, custody, seal races and typed replay; relevant existing guard selectors once. |
| B | 65s | 7s | Exact triple/settlement/capacity, stale-sweep race, reconstruction and read-only controls; relevant old guards once. |
| C | 25s | 5s | Actual two-Job terminal witness, fresh evidence and bounded /1/preflight/negative selectors. |
| Owner-held reserve | 10s | — | No automatic use or borrowing; reallocate explicitly if a measured gap warrants it. |
| Total | 180s including reserve | 20s | 200s cumulative. |

Every runtime attempt, failing probe, setup failure and selected rerun counts
by subprocess wall time. Record exact selectors, outputs and cumulative use.
Focused failing boundary first, then changed acceptance and relevant regressions.
No whole assembly module, manager package, broad suite, live model or OCI run.
Do not repeat a passing selector absent a relevant subsequent change or failure.
Stop and report insufficiency BEFORE a slice cap, preserving its unfinished
acceptance. No silent transfer of unused implementation/reviewer/other-slice time.

The estimate reflects a new custody/profile operation and startup race guard,
a separate transactional three-stage round, and one real composed witness.
It is intentionally separate from W119405383.25/450s, its remaining serving4.63s,
observation20s, joined40s and2.12s margin, and its historical uncertainties.
W131187's26.679468629s and prior overrun remain separate history.

Standing W71830 test-change authority applies throughout; this document records
the affected existing paths and bounded reasons, not a new per-test gate.
Independent reviews bind every changed test expectation to CONTRACT-v1 and exact
candidate bytes. No required acceptance result or defect guard may be removed
to fit the budget.

## Concrete owner approval requested

Approve CONTRACT-v1 and these three serial exact scopes plus200s split above.
Specifically approve the schema19 fresh-store compatibility boundary and the
initial automatic prelaunch-only settlement support, with begun/uncertain
integrators held pending existing canonical exclusion. These are explicit
bounded implementation choices beyond the already approved lifecycle direction.
After approval, reviewer creates the three bound children, installs serial
dependencies and dispatches A only. No further undivided continue grant.
