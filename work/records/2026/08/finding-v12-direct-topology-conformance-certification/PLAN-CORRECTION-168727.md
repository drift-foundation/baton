# W33755 plan correction — 2026-09-14

Author: baton.codex under claim 168727. **Proposed, pending independent
planning review and selection of the expanded product scope.** This document
answers all four findings in `review-2026-09-04T14-40-59Z.md`; it is neither
an implementation report nor a certification. No contract or product bytes
were changed in this review turn.

## Version and authority decision proposed for selection

Use Worker Control **2.0**, Agent Session **2.0**, Worker Conformance **2.0**
and the explicit authority selector **`v12-assignment-2`** for the direct
reference profile. The assignment selector is an independent version axis;
the four versions form an explicitly supported tuple, not interchangeable
version numbers. Worker Control §2.2 requires a major version for changed
core meaning/required fields. Version 1.1 is withdrawn.

The new W151 assignment contract retains the exact full assignment identity,
generation minting, claim operation/signature/replay, verifier, fencing,
typed gates, receipt authority and three-store ownership split. It removes
the consent-runtime axis only for assignment-2. Offer/reservation is a manager
operation with no runtime, provider session, input delivery, workspace, tool,
credential or output capability granted to a worker. Metadata and digests are
not capability. A failed, declined, expired or losing claim creates none.
After a successful atomic claim, one attempt may open one fresh execution
session and one execution container. Existing retry/successor semantics still
require predecessor runtime absence AND provider settlement before lane reuse;
"one" does not outlaw a later, separately identified authorized successor.
The accepted W32577 deadline/provider/quiescence distinction remains required.

No lower-level schema may remove W151's axis while claiming assignment-1.
Old assignment-1 records keep their consent axis, including uncertain/live
observations; they are not mapped to "destroyed" or silently called direct
attempts. New assignment-2 records cannot emit, accept or infer a consent
session/observation. Unsupported or mixed tuples refuse before claim/runtime
creation as applicable. A 2.0 transcript is never assessed as 1.0 conformance.

Normative ownership uses these exact canonical repository-relative roots:

| Owner | Root under `work/records/2026/08/` |
| --- | --- |
| W151 assignment | `finding-v12-isolated-agent-workers/findings/finding-v12-assignment-state-machine/` |
| Worker Control | `finding-v12-isolated-agent-workers/findings/finding-v12-worker-contract/findings/finding-worker-control-api-manifests/` |
| Agent Session | `finding-v12-isolated-agent-workers/findings/finding-v12-worker-contract/findings/finding-acp-agent-boundary/` |
| Conformance | `finding-v12-isolated-agent-workers/findings/finding-v12-worker-contract/findings/finding-worker-runtime-conformance/` |

Each owner appends its decision in FINDING and updates its current PLAN when
selected. Preserve current SPEC/schema/model/fixture/generated-case bytes as
the historical version. Add a parallel `versions/2.0/` subtree with SPEC,
schema and evidence/model/tests; W151 uses `versions/assignment-2/`. Do not
append a supersession to an old frozen SPEC and also claim it stayed byte
identical: dated owner FINDING entries and the new SPEC carry the supersession
and reference the old SPEC digest. Snapshot all historical artifacts before
edits, including schema copies and sealed W6 evidence, and verify preservation.

## Product adoption belongs to this proposed scope

W33755 proposes to own the following bounded adoption in the same serial
implementation, rather than leaving an unnamed migration provider. This
replaces the earlier schema-selection-only scope; its expanded product
authority must be explicitly selected after planning review before an
implementer receives it. It does not change the production Job Manager,
single-worker/Claude default profile, Node authority, or existing deployment
stores. File ownership must be coordinated with active Work before editing.

The source prefix below is `v12/python/src/baton_v12/`:

| Paths | Required behavior and boundary |
| --- | --- |
| `authority/identity.py`, `authority/core.py`, `authority/schema.py`, `authority/api.py`, `authority/session.py`, `authority/store.py` | Add explicit assignment-2 selection/certification and contract-runtime gating; preserve the assignment-1 constant/default and identity, signature, generation, fence and receipt behavior. Select only on the fresh reference Authority. No live authority conversion. |
| `contracts/frozen.py`, `contracts/validate.py`, `contracts/manifest.py`, new `contracts/schema/worker-control-2.0.schema.json` and `agent-session-2.0.schema.json` | Load and validate exact versioned bytes; select the correct sealed validator per explicit tuple, including fragments, manifests and digest checks. Keep 1.0 files and default exports/behavior intact for existing callers. No fallback from unsupported 2.0 to 1.0. |
| `worker_manager/schema.py`, `store.py`, `attempts.py`, `offers.py`, `authority_port.py`, `handshake.py`, `documents.py`, `manifests.py` | Persist the exact selected tuple/profile with the attempt/offer and bind it into operation signatures and adoption checks. Preserve old-contract observations and enforce execution-only direct attempts. Neither restart nor a changed caller default may change selection. |
| `worker_manager/sessions.py`, `posture_slots.py`, `launch.py`, `worker_entry.py` | Bind the same tuple through session admission, launch document and worker entry. Refuse direct preclaim sessions and mixed profile/assignment/launch bindings; preserve exact replay and predecessor exclusion. If launch/entry shapes need new members, add a new closed document version; do not widen an existing version. |
| `v12/worker/baton_worker.py`, `v12/worker/Dockerfile`, new `v12/worker/worker-control-2.0.schema.json` | Package both historical and new control schemas, select explicitly for the reference invocation, negotiate 2.0 and emit 2.0 manifests. Preserve current worker default and existing 1.0 schema bytes; never select by filename presence or guessed compatibility. |
| `v12/python/tests/manager/test_lifecycle_composition.py` and new W33755 harness | Explicitly compose the fresh assignment-2/2.0 reference target. Bind actual selected tuple at every boundary; a mocked schema declaration alone cannot supply acceptance. |

The new runtime paths are an explicit proposal, not authority to edit every
file in those directories. Other production source paths remain outside this
proposal. Any additional source dependency discovered at implementation
revalidation must be recorded with its concrete reason and routed for scope
selection, rather than silently changing a shared default. `oci.py`,
`deadlines.py`, `lanes.py`, provider implementations and the W32577 supervisor
are acceptance inputs, not preselected redesign targets.

### Store compatibility and transition

Current `worker_manager/schema.py` declares schema 18 and expressly prohibits
migration; earlier shapes cannot supply missing durable facts. Preserve that
policy. Add durable selected-contract tuple fields to offers and attempts,
binding assignment selector, control version, session version and profile
digest, with closed values and agreement checks at admission and replay.
Bump control-store schema 18 to 19, subject to file-ownership revalidation if
another selected Work has already occupied 19; record any new number explicitly.
Keep the historical consent column for assignment-1 rows; assignment-2 rows
carry no consent observation and cannot transition that axis. A shared physical
column is not an assignment-2 protocol axis. The exact SQL invariant must be
reviewed with the candidate. The selected certification run uses NEW
Authority/control/artifact stores with no imported operations or attempts.
Pin the tuple columns and reopen/refusal checks before executing the image proof.

Do not alter old stores or synthesize contract facts for persisted attempts.
A new build opening an unsupported old schema refuses before any write;
an old build opening a newer schema likewise refuses. Existing stores and
their matching build remain available for operator recovery; this Work does
not drain, migrate or delete them. Within a supported fresh store, explicit
assignment-1 attempts retain historical behavior and assignment-2 attempts
retain their selected tuple across reopen. Reusing an operation with a
different tuple refuses. Contract advancement uses W151's existing atomic
assignment-end/gate rules, never mutates an active attempt's contract, and
cannot claim a profile certified merely because a harness registered it.
Any test registration is explicitly fixture authority, not production proof.

### Focused verification and test ownership

The four parallel normative model suites are mandatory. Runtime tests are
bounded to affected behaviors in `v12/python/tests/authority/`:
`test_identity.py`, `test_contract.py`, `test_assignment.py`, `test_store.py`,
`test_session.py`; and `v12/python/tests/manager/`: `test_frozen.py`,
`test_handshake.py`, `test_manifest_rules.py`, `test_store.py`,
`test_attempts.py`, `test_sessions.py`, `test_launch.py`,
`test_input_delivery.py`, `test_worker_image.py`, `test_worker_container.py`,
`test_lifecycle_composition.py`, `test_negative_race_endings.py`.
Record actual affected tests/reasons in the implementation handoff. The
Sep13 standing test authority supersedes the old per-path permission gate;
it does not remove independent review of changed expectations. New targeted
test files may be added when useful without another test approval.

Require positive 2.0 composition and unchanged 1.0 behavior; wrong/mixed
tuple refusal; exact replay and changed-tuple refusal; persistence/reopen and
unsupported-store zero-write refusal; decline/expiry/lost-claim race with
zero effects; two competing opens/start retries with exactly one effect;
generation/fence rejection; cancellation, deadline, uncertain-provider and
successor-lane retention. Carry forward all genuine unrelated defect coverage.
Default to deterministic public-boundary tests. No live provider is needed.

## Executable definition of carried-forward equivalence

Add a W33755 `equivalence.py` and a reviewed explicit `transition-map.json`
before regenerating 2.0 cases. Inputs are digest-pinned old/new normative
trees, obligation registers and generated case sets. Refuse duplicate IDs,
unknown fields, missing inputs, dangling references and unmapped differences.
Emit every old/new identity and classified changed JSON pointer, not only a
pass count. The transition map itself is immutable in the reviewed candidate.

For generated cases, match by case_id. Outside the three retired IDs,
compare the entire parsed object after removing ONLY its top-level `version`
and `document_digest`; validate the former as exactly the selected version
and independently recompute the latter with the owning canonical algorithm.
All arrays preserve order. All stimulus, required faults/facts, expectations,
verdict inputs, applicability, evidence kinds, source strings and statements
remain in comparison. No recursive stripping of fields named version/digest,
whitespace normalization, substring replacement, or blanket exclusion of
cases citing a changed obligation is allowed. A versioned source citation
change is allowed only at an exact pointer whose old/new value is enumerated
in the transition map and whose clause is mapped below.

For obligations, match by id and compare the complete object. Only `source`
may be projected through an exact, reviewed old-clause -> new-clause mapping
for carried-forward obligations. Every referenced clause must be present in
the clause inventory and its preserved text compare byte-for-byte, apart from
explicitly enumerated version-token locations. Root format identifiers are
checked as explicit expected values, never silently ignored. Covers, cases,
observables, statements and each verdict remain compared.

The initial changed set is obligations A-17, C-01, H-03 and exactly:

| Retired 1.0 case | New 2.0 case |
| --- | --- |
| `A-consent-sees-neither-input-document` | `A-preclaim-has-no-input-delivery` |
| `C-preclaim-no-execution` | `C-preclaim-creates-no-runtime` |
| `H-consent-then-execution` | `H-claim-opens-one-execution-session` |

These are not ignored: compare their exact planned old/new bodies against
the transition map, require the explicit replacement assertions and all
decline/expiry/losing-claim variants, and independently review the semantic
change. If generating required variants changes the count, every new identity
must be mapped and assessed; 136/135 are historical observations, not a cap.
Every other mismatch stops the audit until explicitly resolved. A new consent
reference elsewhere is a finding to classify, not permission to weaken it.

For upstream schemas, compare all JSON pointers with an explicit list of
old/new values for version/ID/ref changes and the consent-axis/session removal
under the new assignment selector. No wildcard pointer exemptions. For model
and normative text, preserve carried-forward source blocks in parallel files
with an exact block map; topology-dependent blocks require reviewed semantic
delta plus their positive/negative/race tests. Structural equality establishes
unchanged encoded requirements, not a proof that prose or runtime is correct.
The reviewer still checks the changed clauses and tests against the ruling.

The audit must itself refuse at least these deliberate mutations: weaken an
unrelated expected refusal, remove one required fault, change applicability,
drop/duplicate a case, change an unlisted source citation, alter a nested
digest, tamper a document digest, or expand the exception map after sealing.
An old-vs-old comparison with matching declared versions supplies the positive
baseline; an absent 2.0 tree must refuse, never report equivalence.

## Execution sequence and honest certification boundary

1. Obtain fresh independent review of this complete proposal; select the
   expanded product/contract scope and release scheduling before product work.
   Current readiness authorizes this planning correction, not silent protocol
   implementation. No implementation or proof has started.
2. Implement the selected normative/adoption delta with coordinated file
   ownership, preserve old artifacts, and pass the focused deterministic
   checks and the explicit equivalence audit. Independently review the exact
   candidate including actual store/profile persistence and every test delta.
3. Re-read W32382 and its four accepted providers against that candidate.
   W32382 closed satisfying at 168717; its final review is
   `work/records/2026/08/finding-v12-local-oci-negative-race-endings/review-2026-09-14T11-10-46Z.md`.
   W32577 closed satisfying at 168561, final review
   `work/records/2026/08/finding-v12-local-oci-negative-race-endings/findings/finding-v12-runtime-deadline-cleanup/review-2026-09-14T10-44-34Z.md`.
   The old open/unpinned-provider statement is superseded. Reuse this evidence
   for provider acceptance, not as fresh W33755 case observations.
4. Prepare and independently review a run-specific supervisor/harness with
   explicit Docker build/run/termination/cleanup limits, owned resource names,
   immutable candidate/schema/register/profile/image inputs and a frozen
   assessor. A time estimate is not execution evidence. Existing Python-to-
   Docker policy restrictions must be handled through an authorized execution
   boundary, never an interactive managed-turn escalation or shell workaround.
5. Run the fresh model-free Docker reference proof for both input families and
   every applicable case. Record Docker daemon version, actual image/build
   digests, real vs simulated boundaries, raw observations and exact assessed
   outcomes. No W6 observation reuse. Missing capability is failed/unable,
   never a skipped pass. Preserve unsuccessful attempts and cleanup evidence.
6. Publish certified only if the frozen assessor and independent reviewer
   establish complete passing applicability coverage. Otherwise publish
   not-certified with all failed/unable/conflicting/unobserved identities.

W71917/W85500 production corrections and W32391 Podman remain outside the
fixed target. W168703's unregistered-test classification is separate; do not
edit the shared runner to admit supervised engine tests as ordinary tests.
The current main deployment guide is outside this planning correction.

**Release classification proposed:** exhaustive certification of this
reference-only profile is later capability work, consistent with the original
W6/W3 exclusion, and a candidate for v13 execution using delivered v12 Jobs.
The Sep14 W2 release ruling does not itself defer this live assignment or
waive a known delivery defect. Keep W33755 open in v11 and request explicit
scheduling selection; do not change graph containment/dependencies or migrate
its authority here. Any discovered work-loss, duplicate-effect, isolation or
false-success defect invalidating v12 remains required v12 correction.
