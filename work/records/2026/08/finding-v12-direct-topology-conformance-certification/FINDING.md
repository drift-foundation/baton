# Revise direct-topology conformance and certify local OCI

## Discovery and scheduling

Created from W6's 2026-08-28 capability-pass revalidation and approver ruling
M33739. This is independent later Work: it must not hold the present M2
vertical-slice finish line, and its top-level record avoids a third nested
finding level.

Ledger Work: `W33755` (parked as later capability work).

## Confirmed gap

The frozen register currently has 135 cases applicable to `local-oci`.
`A-consent-sees-neither-input-document`, `C-preclaim-no-execution`, and
`H-consent-then-execution` require the superseded consent-container topology,
while the approved architecture reserves without a runtime, claims atomically,
and starts one execution container only after claim. The current register
cannot honestly certify that architecture until its topology assumptions are
explicitly revised.

## Required boundary

- Revalidate the current register and every later topology ruling before edits.
- Append explicit chronological supersessions for consent-container cases;
  never silently rewrite historical requirements as though they never held.
- Audit every `local-oci` case for the same topology assumption and revise only
  the ruled contract boundary, preserving unrelated isolation and evidence
  requirements.
- Version and digest-bind the revised register/cases/fixtures and update their
  owning durable records before implementation consumers rely on them.
- After revision, run exhaustive black-box local-OCI certification over every
  applicable current case. Counts are supporting evidence only; every case
  identity and outcome must be present.

## Acceptance

- The direct claim-to-one-container topology is expressed without weakening
  pre-claim denial, consent isolation, authority, credential, output, cleanup,
  restart, retry, race, or sibling-preservation requirements.
- All superseded case text remains traceable through dated durable decisions
  and the new register/case digests are independently recomputed.
- Every applicable local-OCI case is assessed from sealed evidence by the
  frozen assessor; `certified` is published only when none is failed,
  unobserved, conflicting, or unable.
- Both input families and the full negative/restart/race matrix are retained,
  followed by append-only independent review.

## Relationship

W6 owns the earlier bounded `not-certified` capability pass. This record owns
the later specification revision and exhaustive certification and is not a
child that can block W6 or W3 by containment.

## 2026-09-04 scope resolution after independent review

### Confirmed target: the current deterministic W6636 reference composition

This Work certifies the direct-topology successor of W6636's reference-worker
composition, revalidated against the tree after its required lifecycle provider
closes. It does **not** certify the historical August bytes merely because W6
observed them, and it does not certify the later production
`tools.job_manager` / `tools.single_worker` / Claude deployment.

The target is closed as follows:

- the manager boundary is the public Worker Manager operation chain exercised
  by `v12/python/tests/manager/test_lifecycle_composition.py`, driven afresh by
  a W33755 black-box harness; `tools.job_manager` is outside this profile;
- the adapter is `baton_v12.worker_manager.oci.OciAdapter`, bound by the exact
  adapter-build digest computed from the source used by the run;
- the only engine claimed is Docker on the manager host. The exact daemon
  version is evidence, not a claim about other Docker versions. Podman remains
  excluded and W32391 is not a prerequisite;
- the worker is built from `v12/worker/Dockerfile`, runs
  `/opt/baton/baton_worker.py` with the deterministic `ScriptedAgent`, and is
  selected by the resolved immutable image digest. This preserves the
  conformance contract's model-free core gate;
- the fixture binds the exact input, policy, runtime-profile,
  agent-session-profile, adapter-build, image and case/register digests. The
  execution container receives the exact authorized read-only input root and a
  separate private writable workspace only after claim;
- launch and credential delivery use the public Worker Manager `launch`,
  `credentials`, `workspaces`, `sealing`, `intake`, `retention` and `oci`
  boundaries composed by the reference lifecycle, not the production
  single-worker deployment's task document, durable file exchange or Claude
  credential-source registry.

Therefore W71917 and W85500 are explicitly outside this certification target;
their production source/workspace and exchange corrections must not be
silently imported into its verdict. W32382 is a required provider because this
Work retains deadline, negative, retry, race, exact-absence, provider-ending
and lane-reuse coverage. Certification cannot begin until W32382 closes
satisfying and is re-read. The provider's still-open W32577 deadline ruling
currently exists in Baton discussion but not its bound finding, so provider
revalidation must also confirm that the ruling was pinned before its
implementation began.

### Confirmed contract conflict: three cases are symptoms, not the whole owner

The frozen conformance spec gives `worker-control 1.0` and `agent-session 1.0`
precedence and says the suite adds no rule. Those upstream contracts still
require the topology that W6636 superseded:

- `worker-control-1.0.schema.json` requires a `consent_runtime` axis, and its
  `SPEC.md` says consent sees neither input document;
- `agent-session-1.0.schema.json` requires both `consent` and `execution`
  posture bindings, while its `SPEC.md` requires a pre-claim consent provider
  session; and
- conformance obligations `A-17`, `C-01` and `H-03` cite those exact clauses.

Changing only three generated cases would therefore make the assessor claim
conformance to contracts the target intentionally violates. The direct
topology needs a versioned contract transition before the conformance register
can follow it.

### Proposed version transition for independent approval

Preserve every `1.0` spec, schema, model, generated case and sealed W6 artifact
byte-for-byte as historical authority. Author parallel `1.1` Worker Control,
Agent Session and Worker Conformance documents for the already-approved direct
topology; never rewrite a `1.0` case under its old version and digest. The 1.1
contracts keep all unrelated closed vocabularies and requirements and change
only the consent-runtime/session premise:

- an offer or eligible-slot reservation exposes bounded metadata and digests
  only and creates no container, provider session, input/output delivery,
  workspace, tool or credential capability;
- expiry, decline or a lost atomic-claim race releases the reservation without
  creating any runtime or provider session;
- exactly one successful atomic claim is the gate to one fresh execution
  provider session and one execution container, each bound to the exact
  assignment generation and runtime attempt; and
- that execution receives the exact authorized input and private workspace.
  No absent consent runtime is fabricated as in-runtime evidence.

In the 1.1 conformance register, revise the statements, observables and verdicts
of `A-17`, `C-01` and `H-03`, and retire the three 1.0 case identities in favor
of new identities that say what they measure:

- `A-preclaim-has-no-input-delivery` observes no runtime or delivery before a
  successful claim, then the exact read-only input pair in the sole execution
  container;
- `C-preclaim-creates-no-runtime` covers offer/reservation, decline, expiry and
  a losing claim race with zero runtime/session/delivery/workspace/output/tool/
  credential creation; and
- `H-claim-opens-one-execution-session` proves zero pre-claim provider sessions
  and exactly one fresh, assignment-bound execution session after claim.

All unrelated 1.0 obligations and cases must carry forward byte-equivalent
semantics. A bidirectional generated audit decides whether the expected total
remains 136 cases / 135 `local-oci`; those counts are never acceptance. The
three old definitions and their digests remain reachable as version-1.0
history and are absent from the current 1.1 core.

### Normative and evidence path boundary

The implementation plan must enumerate, version and cross-check all owners:

- Worker Control `FINDING.md`, `SPEC.md`, schema and contract-model tests under
  `finding-worker-control-api-manifests/`, plus every tracked runtime copy of
  its selected schema;
- Agent Session `FINDING.md`, `SPEC.md`, schema, executable model, traces and
  tests under `finding-acp-agent-boundary/`, plus every tracked runtime copy of
  its selected schema;
- Worker Conformance `FINDING.md`, `SPEC.md`, schema,
  `evidence/obligations.json`, `evidence/build_cases.py`,
  `evidence/cases.json`, `evidence/conformance_model.py` and its tests; and
- the current reference lifecycle driver
  `v12/python/tests/manager/test_lifecycle_composition.py`.

W6's `evidence/w6-conformance-seal.py`, transcripts and sealed artifacts are
immutable lineage. They are not edited, copied into, or accepted as observations
for W33755. This Work authors a new run-named, refusal-on-overwrite harness and
evidence pack that independently seals the selected 1.1 contracts, every case,
the fixture, adapter/profile/image identities, raw observations and derived
report.

## Test-change authority — 2026-09-04

This Work authorizes additive tests and bounded edits to existing expectations
only where needed to express the versioned direct-topology transition in the
three owning contract-model suites and
`v12/python/tests/manager/test_lifecycle_composition.py`. Version-1.0 fixtures,
assertions and sealed evidence remain immutable; unrelated control vocabulary,
isolation, identity, credential, output, cleanup, restart, retry, race and
failure-containment expectations may not be weakened or deleted. Any product
runtime change beyond selecting and validating the parallel 1.1 schemas must
return for scope review.

## 2026-09-14 — correction under reviewer claim 168727

**Confirmed:** the latest independent review,
`review-2026-09-04T14-40-59Z.md`, requested four planning corrections, not a
certification run. Revalidation confirms Worker Control §2.2 requires a major
version; W151 still owns the consent-runtime axis; Python/worker consumers
still select 1.0 and assignment-1; and control-store schema 18 expressly
refuses cross-version migration. These are current observations, not merely
historical review assertions.

**Explicit supersession:** the September 4 proposed 1.1 transition and its
schema-selection-only runtime path boundary above are withdrawn. The currently
actionable proposal is `PLAN-CORRECTION-168727.md`: explicit Worker Control,
Agent Session and Conformance 2.0 with assignment-2, W151 owner participation,
bounded Authority/manager/worker adoption, fresh-store compatibility and a
precise fail-closed equivalence comparison. It is a proposal for independent
review and expanded scope selection, not a newly approved protocol ruling.
Historical normative bytes remain untouched. Frozen SPEC supersessions will
be recorded in owner FINDING/new-version SPEC, avoiding the contradictory old
plan instruction to edit a frozen SPEC while preserving its bytes.

**Provider state correction:** W32382 closed satisfying at 168717, with final
review `work/records/2026/08/finding-v12-local-oci-negative-race-endings/review-2026-09-14T11-10-46Z.md`.
All four children are closed, including W32577 at 168561 with final review
`work/records/2026/08/finding-v12-local-oci-negative-race-endings/findings/finding-v12-runtime-deadline-cleanup/review-2026-09-14T10-44-34Z.md`.
The earlier open/unpinned-deadline statement above is superseded. The retained
W32382 dependency is now satisfied. Provider acceptance supports planning;
it does not supply new W33755 certification observations.

**Policy correction:** September 13 standing test authority supersedes this
record's older per-path test permission gate. September 14 removed cumulative
development stopwatch admission gates. Neither authorizes an unselected
protocol/product expansion or an unsupervised engine run. No tests, image
builds, live providers or engine runs occurred in this planning correction.

**Proposed release classification:** reference-only exhaustive certification
remains later capability Work, outside the original W6/W3 finish line. The
September 14 W2 release boundary makes it a candidate for v13 execution, not
an automatically deferred or closed Work. Request explicit classification
after independent plan review; preserve W33755's identity, dossier and v11
authority. No dependency/containment change is made. Known correctness defects
invalidating v12 delivery cannot be deferred under this recommendation.

**Operational locator finding, resolved:** initial reads using shortened
top-level Worker Control/Agent Session paths failed with ENOENT. A repository
file search resolved both to the canonical worker-contract descendants listed
in the proposal; the required source sections were then readable. The old
review also uses a shortened Worker Control locator. This is a stale/shortened
documentation locator, not evidence of a missing contract or a Baton defect.

Current PLAN names the replacement proposal and its remaining gates. No
PROGRESS, normative artifact, test source, application source or Git state was
changed by this planning correction. Prior 74-test evidence belongs to the
earlier planning handoff; no elapsed duration was reconstructed for it here.

## 2026-09-14 — independent planning disposition, tuner claim168902

Technical plan accepted for concrete expanded-scope selection in
review-2026-09-14T11-39-30Z.md. All four September4 planning findings are resolved
by PLAN-CORRECTION-168727.md, whose SHA256 remains
eb11029fa8dc358567fbec63fa8136e838547a17595b4652cd36ddbb2fb062e9.
This is not implementation/candidate acceptance or local-OCI certification.
The expanded2.0/assignment-2 normative and product scope still needs recorded
selection before implementation; the current PLAN separates that decision.

**Explicit limited supersession of release-selection wording:** M168850 and
independent reading confirm W2 FINDING2026-09-14T09:04:44Z already adopted the
W33755 v13-hardening row in RELEASE-CLASSIFICATION-165799.md, repeated in
RELEASE-CHECKLIST-167877.md. The preceding proposed-release paragraph and the
proposal/author review's requests to select that classification are superseded.
Do not request the same release strategy again. Preserve the digest-bound
proposal and prior reviews unchanged. The row's older1.1 label is not authority
to violate the major-version rule or to implement the new expanded scope.
No v13 execution, authority migration or graph/containment change follows.

Canonical provider snapshot168914 confirms W32382 and all four children closed
satisfying; its retained dependency is satisfied. Static review independently
matches author-bound inputs, all136 current case digests and bidirectional links
for79 obligations, with135 local-OCI cases. review-audit-168902.json preserves
the pre-review input identities. Measured static checks0.00541068401071243s;
other reads unmeasured, runtime/tests0s. No fresh certification observation,
product/test/normative/PROGRESS edit or Git mutation occurred. Return to
baton.feat for concrete expanded-scope selection only.

## 2026-09-14 — scope decision packet, reviewer claim168961

Read the complete returned handoff and discussion, current dossier, unchanged
proposal and independent acceptance review. SCOPE-SELECTION-168961.md packages
the remaining concrete decision for baton.decide: adopt the independently
reviewed 2.0/assignment-2 normative and enumerated runtime-adoption scope for
the already selected v13 outcome. This recommendation is not an owner ruling.
No further technical planning correction is requested by the independent review.

The W2 owner ruling09:04:44Z already selects classification and keeps v13
execution parked until readiness. Scope adoption and permission to start
implementation are distinct. Do not reopen release strategy or automatically
dispatch implementation after this planning handoff. Preserve W33755's identity,
open outcome, v11 authority and satisfied W32382 dependency; no graph edit or
new Work is needed. Later execution requires current ownership coordination,
candidate/equivalence review and separately prepared supervised proof.

selection-audit-168961.json finds all 28 rechecked proposal/historical/source
inputs unchanged, measured0.0010344820038881153s. No tests or runtime execution
occurred. Earlier static costs and unknown historical test duration remain
attributed in the packet. Only dossier planning/decision evidence changed;
the frozen proposal digest, prior reviews, PROGRESS and product/normative/test
bytes remain preserved. Current PLAN now routes this concrete decision packet
to baton.decide rather than another planning-review loop.
