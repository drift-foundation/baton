# W371072 — proposed bounded role-contract admission

Status: proposal for independent review and owner decision, **not an approved
contract or implementation assignment**. Prepared by baton.codxpc under E371102,
within owner E370866. Retain the existing architecture. Add one data-only
development contract and one installed capability binding, checked before ordinary
creation effects and again before dispatch. Keep result acceptance with its owners.

## Revalidated baseline and residual gap

**Observed:** `templates.py:115–191` freezes template `/1` and its logical
implementation/review consumes/produces graph. It does not describe concrete
output types, paths, constraints or adapter compatibility. `job_task.manifest_for`
changes the human-contract bytes/digest and reseals the manifest, preserving the
installed outputs. `creation._owned` reserves the Job, acquires creation ownership,
authorizes Work and publishes binding before `_servable`; the latter consults
`stage_execution.servable_workers`, whose `_disagreements` compares role, Work,
profile, Job input and policy identities. None of those identity comparisons
establishes that a role can answer the declared output set.

**Observed:** ClaudeAgent.work and _review are the two actual role adapters in
this selected workload, within one provider module. `_selected` refuses missing
role outputs and required outputs produced by another role. `baton_worker.answered`,
host `output._compare_declared`, `sealing`, `intake._compared`, integration
`driver._claim_of` and `review_driver._review_claim` impose distinct publication,
measurement, collection and semantic consumption checks. This is not a proposal
to replace them with a descriptor flag. Source locations and hashes are retained
in evidence/claim-371102/SOURCES.json; statements concern that tree, not installed
image equivalence.

**Accepted evidence reused:** W370688 INVENTORY-370820.json SHA256
`2cc804344888ca5d116a7965ac8523729c2a33a94f174294ba5bffe30493295b`, independently
accepted by review-2026-10-28T02-42-39Z.md, supplies the shared optional union and
the bounded octet-stream declarations. Its packet remains source-bound to
42bed8bb04a53380e565b1a63fb2bc702677f0d0 and refuses operational use after source
drift. Its simulated Git/provider proof is not real transport or native workflow
acceptance. No packet repair, source reselection or repeated execution is proposed.
The diagnostic review-2026-10-28T02-09-13Z.md remains evidence of incompatible
declarations, not a recovered exact runtime exception.

**Inferred:** checking a reviewed descriptor against independently pinned installed
capabilities prevents this known miscomposition before creation effects. This does
not prove that arbitrary adapter code implements a claimed capability: qualification
of exact image/adapter/profile bytes remains necessary.

## Concrete descriptor candidate

`ROLE-CONTRACT.proposed.json` is the complete candidate, canonical digest
`sha256:21b78036947430e3ae073a04fd5237b10a844471207a52cba9ea6186acdffdaf`.
Use `baton_v12.contracts.canonical_bytes` and `digest` over the entire JSON object,
without any embedded digest member. Whitespace in a file is not identity. Reject
duplicate JSON keys before canonicalization, floats, booleans-as-integers,
non-built-in object types and unknown members. Maximum decoded document depth 8
and encoded UTF-8 size 16384 bytes; these are proposed bounds, not current behavior.
Object key order is canonical; list order below is prescribed and duplicates refuse.

Every object is closed. No extensions, callbacks, scripts, module paths, regular
expressions or operator-provided validator code exist in this descriptor version.

| Field | Exact proposed type and rule |
| --- | --- |
| schema | Literal `baton.v12.development-role-contract/1` |
| template | Literal `baton.v12.job-template.implementation-review/2` |
| task_schema | Literal `baton.dogfood-task/2` |
| source_profile | Literal `git-line` |
| outputs | Exactly three descriptors, in proposal/findings/logs order, defined below |
| roles | Exactly two role objects, implementation then review, defined below |

Each output has exactly `name`, `type`, `path`, `required`, `constraints`.
Names and paths are the same fixed literal. Proposal type is `git-change-proposal`;
findings/logs type is `directory-result`. All `required` values are Boolean false.
Constraints have exactly `max_bytes`=1048576, `max_entries`=100,
`allowed_media_types`, `link_policy`=`forbid`, `validator_digest`=null. Proposal's
media list is `["application/octet-stream", "text/plain"]`; each other list is
`["application/octet-stream"]`. Numbers are integers. These are exact equality
checks for this first bounded revision, not a general min/max constraint language.
Different limits, context-receipt output, task `/3`, alternate paths or a custom
validator require another explicitly selected descriptor/template revision.
This deliberately qualifies the accepted fresh-context baseline; it does not
retire existing context-enabled workloads or claim required reuse delivered.

Each role object has exactly `role`, `consumes`, `produces`,
`required_for_success`, `consumer`. Implementation has consumes=[],
produces=required_for_success=["proposal"], consumer=`git-proposal/1`.
Review has consumes=[{"role":"implementation","output":"proposal",
"delivery":"frozen-checkpoint"}], produces=required_for_success=["findings","logs"],
consumer=`checkpoint-review/1`. The consume object has those three literal fields.
Consumers are closed built-in development-profile IDs, never dynamic dispatch
names. They select the existing integration/review semantics and their required
verification/identity checks, not just artifact existence. Consumption of a proposal
means an exact immutable checkpoint with retained transport/provenance, not copying
a producer's metadata into a reviewer verdict.

### Optional shared declaration versus required stage result

| Role | Must publish for a usable successful result | Must answer absent | Consumer gate |
| --- | --- | --- | --- |
| implementation | proposal with actual measured transport, source/base/head claim and required verification evidence | findings, logs | Existing proposal/verification consumers validate exact candidate and retained bytes |
| review | findings and logs, one valid verdict bound to the consumed checkpoint | proposal | Existing review consumer validates mandatory measured artifacts, unique claim, base/head/tree and reviewer independence |

Generic completion may preserve an unable/failed result or a missing optional
artifact. It must not advance a successful stage, mint a verification/review
receipt, open an accepted delivery or satisfy dependent work merely because every
shared `required` bit is false. The development result-consumption gate runs before
successful stage advance. Execution cessation and release of stopped execution
ownership still follow ART-7 independently; admission does not add a post-stop
output prerequisite. W371074 owns the settlement proposal.

## Installed capability and exact version transitions

`CAPABILITY.synthetic.json` illustrates a second closed document. Its four repeated
digit hashes are explicitly synthetic, not qualified deployments or owner receipts.
Its canonical digest is
`sha256:4d6a3391facb990ac61090ab5e6b114203b27a27faeca1083458c7bd8f649601`.

Capability fields: `schema` literal `baton.v12.adapter-role-capability/1`;
`role_contract_digest`, `adapter_digest`, `image_digest`, `runtime_profile_digest`,
`qualification_digest` are lowercase `sha256:` plus 64 hex digits; `roles` is one
of ["implementation"], ["review"], ["implementation","review"]. No empty list,
duplicates, wildcard identity or additional field. Maximum 2048 UTF-8 bytes and
depth 3. Qualification digest refers to independently reviewed conformance evidence
for that exact image/adapter/profile tuple and descriptor, resolved by trusted
installation tooling. A self-authored worker advertisement grants nothing.
Separate implementations and images may carry distinct capabilities for one contract.

Recommended concrete carrier changes (all require approval; no version is silently
widened):

| Carrier | Proposed encoding and reader behavior |
| --- | --- |
| Template | Add immutable `implementation-review/2`; keep `/1` unchanged. `/2` fixes the descriptor digest; ordinary request schema `/1` can select the new version because its template operand is already text. No descriptor override in requests. Do not change the configured default implicitly. |
| Stage deployment | Add `baton.v12.stage-execution-deployment/3`: exact `/2` fields plus `role_capabilities`, a list of 1–256 closed `{worker_id, capability}` objects, sorted by worker_id and unique. worker_id follows existing bounded identity grammar, additionally at most128 UTF-8 bytes; capability is the closed document above. Every eligible `/2` template worker must have one; extra unknown worker IDs refuse. |
| Derivation | For template `/2`, the manager-owned port uses a new closed response variant: existing six required per-Job derivation fields plus `schema`=`baton.v12.role-contract-derivation/1`, `role_contract`, `role_capabilities`. Both latter documents are owned copies from the template and trusted deployment, not request prose. Old unversioned responses retain the old path only. |
| Resolution | Add `baton.v12.job-template-resolution/2`: exact existing `/1` members plus `role_contract` and `role_capabilities`, with the same closed structures. Retain full documents and hash entire resolution in existing template-job provenance; do not change normalized legacy submission meanings. Consumers must use supported resolution reads for `/2` Jobs. |
| Runtime launch/input | No new worker-launch, assignment or generic input-manifest field proposed. Continue exact existing launch adoption and manifest digests. The selected descriptor is bound in Job resolution; selected capability must match exact adapter/image/profile before launch. Worker defensive checks still validate the actual declarations. |
| Result/terminal | No result or terminal schema change in this Work. Descriptor consumer IDs select existing strict consumers. W371073 separately proposes safe typed defensive faults. |

Store compatibility needs an explicit migration/reader-support gate for resolutions
`/2`, even if stored JSON columns can physically hold them. An old binary must
refuse the new deployment/resolution before dispatch, not start some legacy stage.
No native authority receipt schema is widened. This is one versioned admission
slice, not an extensible template language or plugin framework.

## Reader/writer ownership and pre-effect admission

| Owner | Writes/owns | Reads/checks |
| --- | --- | --- |
| Development contract package | Frozen descriptor and pure closed validator | Generic owned JSON only; built-in semantics, no provider import |
| Image/profile qualification and installer | Exact trusted capability tuples and new deployment generation | Real adapter role conformance, evidence digest, exact package/image provenance |
| tools deployment derivation | Owned data snapshot through configuration owner | Task, per-lane manifest, installed capabilities; preserves each lane's runtime fields |
| Job manager creation/resolver | Pinned resolution and creation intent | Pure compatibility check before reservation; owner-supported reads outside transactions |
| Selector/serving | Eligibility and exact selected execution | Same pure predicate and retained resolution; current installed identity against admitted capability |
| Worker/adapter | Actual result claims and measured completion | Actual launch/task/declarations; defensive refusal before provider work |
| Host output owners | Generic measurement, seal and collection | No proposal/verdict semantics or imports of provider code |
| Development consumers | Candidate/verdict validation and stage result | Exact measured result, checkpoint, assignment, required evidence and independence |

Proposed fresh admission trace:

1. Preserve request validation and committed-operation replay first. A completed
   create replay returns its recorded result without consulting today's capabilities;
   replay is not a new dispatch grant. Changed caller intent still collides.
2. Under the existing non-DB instance/configuration ownership mechanism, obtain
   immutable owned configuration/capability/task snapshots through current owners.
   Resolve the selected template and descriptor. No engine/provider invocation.
3. Before `_reserved`, `_acquired`, `_authorized` or `_bound`, run the pure validator
   on the final per-role task/manifests and installed tuple. Require exact descriptor
   outputs and role semantics, supported source/task schema, matching capability
   digests and at least one independently eligible candidate per required stage.
   No creation reservation, Work authorization, binding, Job submission, allocation,
   claim, root staging, token or launch effect occurs for this incompatibility.
   Read locks and the existing instance OS guard are not acceptance side effects.
4. Persist the pinned `/2` resolution via the existing owned reservation operation.
   Keep existing idempotent cross-owner authorization/binding and final servability
   checks: the new pure check cannot certify authority or replace scheduler admission.
   Failures of these later owners may leave a recorded incomplete creation exactly
   as today; do not misreport those as zero-effect descriptor refusals.
5. Before offer/allocation, read the retained resolution and current deployment
   through owners outside DB transactions. Apply the same predicate. Before external
   launch, compare the actual selected tuple and composed manifest again under the
   existing execution/configuration generation fence. Drift holds/refuses with no
   new provider or container. Already reserved ownership is settled through its
   existing path, never silently erased or attributed to a completed attempt.
6. Worker validates actual delivered inputs; downstream consumer decides whether
   required results are usable. Neither adapter success nor generic completion
   decides independent review or owner acceptance.

No callback supplied by a template or deployment runs in a DB transaction.
Configuration reads and capability-file verification happen before transaction
entry; the pure validator accepts built-in copied data only. The short reservation
transaction records the already selected version/digests and conditionally checks
the owner generation. Do not open another store under it. If startup ownership is
changed by W371075, its admitted configuration revision/fence must replace the
current OS-guard assumption explicitly; do not rely on rereading mutable files.

### Binding and heterogeneous execution

Descriptor digest binds output semantics; resolution digest binds the selected
contract and capabilities; Job input identity binds common input/output policy;
each full manifest/launch still binds its own runtime. Compare common input via
`job_input_identity`, never force equal full manifests or equal capability digests
across roles. Current `DeploymentDerivation._for_task` additionally compares whole
manifest text, which can reject otherwise Job-equivalent heterogeneous manifests.
The proposed composition must instead establish common Job-scoped facts and task,
then retain each lane's full runtime fields through its owning composer. This is a
concrete current constraint to resolve in the admission slice, not proof existing
heterogeneous ordinary creation already works. W370555's exact launch/observation
adoption fix remains intact and is reused, not relaxed to accept a convenient digest.

## Compatibility and refusal matrix

| Case | Proposed outcome |
| --- | --- |
| New template, qualified lanes, exact union | Admit; two distinct role principals; distinct runtime digests allowed |
| Missing findings/logs, proposal required for review, findings required for implementation | Pure pre-reservation refusal |
| Wrong type/path/media set, lower or higher limit, link policy or validator | Exact-contract refusal; changing limits needs a version, not guessed compatibility |
| Missing/unqualified capability; mismatched descriptor/image/adapter/profile digest | Refuse before fresh creation effects; never invoke adapter to discover compatibility |
| Configuration drifts after creation | Committed create replay unchanged; new dispatch refuses/holds until exact admitted configuration is available or an explicitly selected new Job is created |
| Unsupported deployment/descriptor/resolution version or unknown field | Closed refusal before execution, no fallback |
| Existing single-role workload or already admitted template `/1` Job | Preserve existing contract and replay; no injected review outputs or rewritten digest; never claim new admission qualification |
| Fresh explicit template `/1` on new deployment | Legacy semantics remain available and clearly identified; recommend `/2` only after qualification, not silent reinterpretation |
| Context-enabled or task `/3` workload | Continue its explicit legacy path; this descriptor refuses new `/2` qualification until its distinct contract is approved |
| Both lanes advertise one principal | Existing independence rule refuses; two IDs do not create independence |
| Generic completed envelope omits proposal/verdict/logs or gives malformed claim | May retain generic evidence, but role-success consumer refuses; no accepted stage/result or receipt |
| Adapter fails despite accepted declaration | Retain fault, use W371073 diagnostics and W371074 settlement; no automatic accepted verdict or unselected retry |

## Code/spec gap and proposed DESIGN delta

| Normative requirement | Observed gap | Bounded proposed change |
| --- | --- | --- |
| SCH-1a template input/output contract | Logical names do not constrain concrete installed outputs | Versioned data descriptor with exact supported baseline |
| ART-3 / RUN-1 before effects | Role-output incompatibility first found in runtime adapter | Validate before creation effects, then recheck exact selected dispatch |
| DB-1/3/5, SCH-6 | Existing servability follows reservation/binding | Add pure earlier predicate without removing final owner checks or cross-store journals |
| ID-4 / Job-versus-runtime identity | `_for_task` whole-manifest agreement overconstrains lanes | Compare common projection while preserving per-role full identities |
| ART-6/7, REV-1/2 | Shared optional outputs can be mistaken for successful stage completion | Keep semantic consumer gates explicit and separate from execution release |
| DEP-2/3 | No selected installed role-capability evidence binding | New closed capability/deployment/resolution versions; explicit qualification/migration |

Proposed addition after SCH-1a, quoted for owner approval only:

> A versioned development template MUST bind its supported task/source and
> role-specific consumed and produced result contracts, including concrete output
> declarations and results required for successful stage consumption. Before fresh
> creation effects, the Job manager MUST validate that contract against trusted,
> versioned capabilities of the installed role adapters and the actual composed
> inputs. The selected contract and capabilities MUST be retained with the Job's
> resolved provenance and checked against the selected execution before dispatch.
> Unsupported or changed contracts MUST refuse without silently reinterpreting
> admitted Jobs. Shared optional declarations MUST NOT waive role-required result
> validation. This compatibility validation uses closed data and owning APIs,
> without provider imports into the generic host or external callbacks inside
> database transactions. Job-scoped identity and per-execution runtime identity
> remain distinct; execution cessation is not result acceptance.

No DESIGN edit has been made. Owner decision requested: approve this narrow fresh
context `/2` contract, exact bounds, capability trust/version scheme and delta, or
name specific amendments. Context qualification is intentionally a separate future
descriptor selection, not a claim that reuse is optional for v12 delivery.

## Finite implementation and acceptance plan

1. After owner approval, pin the decision and update DESIGN. Deliver closed
   contract/registry validators and frozen vectors for `/2`, with canonical digest
   and malformed/version/refusal cases. A single assigned author owns shared
   contract material. No standalone feature-framework milestone.
2. Add qualification and deployment/derivation/resolution carriers; enforce the
   predicate before fresh creation effects and through selector/serving rechecks.
   Preserve replay, migration and per-role input identities. Couple the current
   `_for_task` restriction correction here because the same new snapshot is the
   admission input. Independently review this finite admission result.
3. Qualify both actual role branches against the descriptor with deterministic
   providers at their real process boundary. Exercise real producer transport and
   frozen review checkpoint in the supported harness; W370688's invalid bundle
   fixture cannot certify those joins. Hand exact accepted candidates to W371076's
   joined ordinary-workflow proof plan; no deployment selection follows automatically.

Future likely overlaps: creation/templates/contracts/stage_execution and
creation_ports/job_task belong to the admission implementation slice; W371075's
startup changes may touch creation/stage_execution, so serialize those edits or
assign explicit non-overlapping symbols before execution. W371073 may touch
claude_agent/baton_worker; admission primarily consumes them and schedules role
qualification tests rather than assigning concurrent edits. W371074 owns ending
and release. No product file ownership is acquired by this proposal. Existing
W370555/W370688 delivery is reused. W371076 depends canonically on W371072; parent
W370747 joins planning acceptance and stays open.

Acceptance must demonstrate: both real roles and consumers; all matrix refusals;
zero recorded creation/authority/binding/submission/dispatch effects for initial
contract incompatibility; installation capability tamper and dispatch-time drift;
completed-create replay after configuration changes; old single-role and `/1`
replay unchanged; distinct lane runtime identities with equal common projection;
required missing/malformed role result unable to advance success; exact source and
reviewer independence; no provider/engine call during preflight; transaction probes
show every filesystem/cross-owner read outside DB transactions. Use existing owning
APIs and disposable stores, never insert synthetic authority receipts. Broader
restart/failed-settlement and two-Job joins belong to W371076's composed proof.
Tests are future proposed verification, not test results from this planning turn.

This turn runs only an inert source/descriptor check and hashes evidence. No product,
test-suite, DESIGN, installed instance or historical packet edits; no live run,
cleanup, installation, Git mutation or native closure. Independent planning review
precedes owner approval and implementation. At accepted planning milestone retain
the pending human Git checkpoint recommendation: `Plan template role-contract admission`.
