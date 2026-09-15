# Selected delivery after consolidation

Recorded 2026-09-13T14:40:58Z by baton.codex, claim161345. This is planning,
not a new independent candidate approval or implementation handoff.

## Authority and explicit supersession

Owner response161211 and return161212 selected decomposition. Later owner
clarifications, pinned in FINDING and conveyed by M161244, M161254, M161258 and
M161267, control where they change that response. In particular:

- Managed integration belongs to separate **W161230**, not W156162.
- Correction, counted restart and REQUIRED healthy provider-context continuity
  belong to separate **W161234**. Context reuse is selected, not an unresolved
  preference or optional enhancement. Lifecycle/adoption design remains open.
- Dedicated capacity is selected now; shared-slot configuration is deferred.
- Operator-designated replacement until revocation is required. Automatic
  fallback is not required. The proposal to drop the stronger requirement was
  rejected; this does not rewrite W71877's accepted soft-affinity history.
- Priority, randomized stress and TUI form a later hardening phase. They do not
  block immediate correctness delivery. Do not create that backlog now.
- Project-pinned dependencies and actual-version recording are completion
  checks in each selected Job. No standalone environment project is selected.

These decisions supersede the recommendations and unselected-status wording in
CONSOLIDATION-2026-09-13T14-10-03Z.md, including chunks B through H and its
proposed sequence. Its evidence matrix, hashes, measured costs and review remain
historical evidence. The later-appended FINDING entry dated14:10:03Z describes
that earlier review state; its statement that no selections exist is superseded
by the owner decisions above, regardless of its physical position in the file.

## Two selected Jobs and finite completion

Estimates below are planning effort, not runtime allowances or authorization.
Each exact implementation slice needs reviewed paths, test authority and numeric
verification bounds. No Work inherits unused W103525 or W156162 allowance.

| Job and current owner | Benefit and bounded finish | Dependencies and sequence | Estimated effort / uncertainty |
| --- | --- | --- | --- |
| **W161230**, baton:work/records/2026/09/finding-v12-managed-integration-execution/; reviewer plans, implementer implements, independent reviewer checks | Candidate-executing integration preparation/reconciliation/verification uses managed Docker attempts, ordinary limits, real capacity, positive stop/recovery and portable existing input/output. Trusted target owner retains lease/fence/old-revision publication safeguards. Complete reviewed finite slices and focused final pinned-environment checks; no farm deployment or new RPC | DESIGN-HANDOFF-161312.md adopts the W156162 v2 design and rejected-v1 history by exact hashes. Independent design review is already routed to baton.impl via pass161337. Resolve review, select exact slice, implement and independently review before consumers claim the managed boundary | Large: design plus several bounded implementation/review sessions. High lifecycle/cross-store uncertainty. Proposed first slice120s author/30s reviewer is not yet authority; Work measured verification0 at that handoff |
| **W161234**, baton:work/records/2026/09/finding-v12-correction-restart-proof/; reviewer plans adoption and proof, implementer implements, independent reviewer checks | A real correction changes useful code, completes revised implementation, independent review and authorized import. Healthy same-line serving retains provider conversation context with fresh attempt/episode/result identities. A declared durable reopen after a real deterministic provider turn continues with counted provider calls/engine starts, no duplicate terminal effects, and duplicate-detection negatives | Planning and exact adoption-gap research can precede W161230. Final managed integration proof depends on W161230; record the canonical dependency when arranging this Work. Reuse W103525 helpers and W106673 accepted live evidence. Bound missing production changes explicitly before implementation; do not pretend this remains test-only if adoption needs source changes | Medium proof work plus potentially large production-adoption work; high until lifecycle/path mapping is reviewed. No numeric new verification allowance yet. Return exact scope/cost before execution |

W156162 remains the budget consumer and is canonically blocked on W161230 by
161306 with its claim released. W161234 detail161363 is queued at baton.feat;
M161246 reports prompt's dependency attempt was correctly refused by endpoint
authority, so no edge exists yet. Do not say the documentary dependency is a
recorded scheduler gate. Reviewer planning must finish before gating final
execution; blocking now must not hide unfinished adoption planning.

Both selected plans require final focused checks with project-pinned dependencies
and recorded actual versions, including resolving/revalidating jsonschema4.19.2
versus4.26.0. Earlier exports remain nonconformant evidence. A concrete setup
failure warrants its own operational finding; no speculative environment project,
live-provider repetition, image build or installation is authorized by this plan.

## Operator replacement: current support and exact remaining design

**Confirmed by source inspection, not a new runtime experiment:**

- `v12/python/src/baton_v12/job_manager/scheduler.py:activate_pool` journals
  immutable configuration generations. Returning to a prior configuration makes
  a new generation; old live allocations retain their generation. Reattaching
  the same configuration refuses changed Authority-resolved principals.
- `reserve` selects profile/kind-compatible, independent, unoccupied actual
  worker/principal capacity. Its current soft affinity chooses another available
  eligible worker automatically; it has no operator-substitution operand.
  `SelectionAndSettlement.test_affinity_is_soft_and_fallback_does_not_rewrite_it`
  in `tests/job_manager/test_scheduling.py` explicitly preserves that behavior.
  The file was read, not run or edited.
- `v12/python/tools/stage_execution.py:_job_workers` requires actual per-Job
  Work/input compatibility and exact implementation `source_worker_id`;
  `_job_eligibility` excludes incompatible actors before allocation.
  `_resolved` checks real Authority principals; `_pool_generation` checks the
  activation generation before mutation. Pool activation alone therefore does
  not prove another source worker can serve an already-bound Job.
- `_required_workers` retains providers needed by old live allocations, and
  `recovery-required` capacity remains occupied. Replacing configuration is not
  evidence of positive stop and cannot authorize takeover of an uncertain run.

**Inferred:** these are useful configuration/audit/recovery building blocks,
not a complete "Jane covers Chris until further notice" operation. Inspection
of the closed pool document and serving admission path found no scoped, durable
substitution relationship with authorizer, revocation and admission provenance.
This is a bounded finding about those paths, not proof that no other interface
anywhere in the repository could help. Do not implement an identity alias or
remove the accepted Work/input/source validation to simulate the requirement.

**Open design, retained here without creating a third Job:** determine whether
an explicit authorized configuration revision can meet the requirement or whether
a separate durable substitution record is needed. Name scope and authorizer,
replacement's actual participant/principal/profile, eligibility and source-binding
revision, activation/revocation, and treatment of already-admitted work. Define
how selection obeys the designation without silently changing unrelated legacy
soft-affinity policy. Specify positive stop/recovery before existing-attempt
takeover and honest transferable-context limits across workers/providers.

The narrow candidate patch boundary to investigate is scheduler pool/admission
plus serving binding/configuration ownership, with schema/store only if a new
durable relationship is necessary. It is not permission to edit those paths.
Finish a later bounded design with designated-only admission, revocation/reopen,
wrong Work/input/repository/profile refusal, actual-principal capacity and review
independence, and uncertain-runtime takeover refusal. First design estimate:
one or two focused review sessions; implementation estimate remains unresolved
until the configuration-versus-product choice. Owner selection of another Work
and exact scope is needed before implementation. Do not silently add this to
W161230/W161234 or reinterpret it as optional.

## Evidence and certification boundaries

| Boundary | Current disposition and truthful claim |
| --- | --- |
| Trace/oracle foundation and two terminal orders | Retained independent acceptance: each fresh trace97 records,12 stage completions, four imports; exact18-schedule author export independently audited. See review-2026-09-13T14-10-03Z.md and its report for hashes and observations. This turn reran none of them |
| Actual revised-code correction | Still open; successor W161234 completes code, review and import. Configuration-label fixes and revised-attempt preparation alone remain insufficient |
| Context continuity and counted reopen | Required in W161234. Reuse W106673 capability evidence; normal serving adoption and actual nonvacuous invocation counts remain to prove. Fresh attempt identity does not require discarding provider conversation identity |
| Managed integration isolation/custody | Required in W161230; historical host-path traces do not certify the selected managed lifecycle. Consumers revalidate capacity, collected content, test/harness identity, positive stop, judgments and trusted publication after relocation |
| Dedicated worker capacity and repository bindings | Use dedicated configured workers now. Existing separate two-repository evidence survives at its measured boundary; no new combined shared-slot or repository certification is claimed by selection alone |
| Operator-designated replacement | Requirement confirmed; bounded design gap above remains open in this consolidation. Existing automatic fallback is historical accepted behavior, not proof of the selected capability |
| Shared slots; priority/random/TUI | Explicitly deferred. No immediate selected-Job gate and no certification claim for these capabilities. Preserve for later selection without creating a backlog now |
| Final environment | Required in both selected Job completions; old nonconformant evidence is preserved with its limitation |

Immediate delivery means the selected correctness outcomes, not certification
of every historical W103525 requirement. W103525 retains the evidence and this
staged disposition; do not close it as fully certified, count deferred rows as
passes, or quietly drop required substitution/context reuse. Return this small
Job plan and the explicit residual substitution-design boundary for owner review.
No further partial implementation loop belongs in W103525.

## Spending and change boundary

No tests, provider calls, runtime launches or new executable probes ran in this
planning turn. W103525 author remains289 runs1063.5077970099796/1200s; reviewer
141.8669683800224/300s; remaining136.4922029900204s and158.1330316199776s.
Research0.2879257239692379s remains separate. Historical author overrun
0.8047997559610849s against the former780s cap is preserved and unwaived.
No reset or transfer. W156162's separately retained costs remain in its dossier.

Only reviewer-owned planning records change. No product/test bytes, prior review,
PROGRESS, Git state, dependency installation or coordination-store access.
Two guessed search paths (`v12/python/baton/...` and `job_manager/pool.py`)
were absent; `rg --files` and the recorded source map located the actual
`src/baton_v12/job_manager/scheduler.py` and `tools/stage_execution.py` owners.
These are corrected search mistakes, not missing mandatory policy or a Baton
defect; no required dossier could not be read.
