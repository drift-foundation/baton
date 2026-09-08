# Produce and retain proposal manifests

Current disposition: owner accepted the final signed-off candidate on 2026-09-07.
All three current candidate hashes match `review-2026-09-07T03-04-53Z.md`.
The bounded composer is complete; older pending statuses below are historical.
This accepts no live runtime/access/custody or deployment capability.

Ledger Work: W103874

Parent: `work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-standalone-stage-composition/`

Discovered by W103083:
`work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-standalone-stage-composition/findings/finding-shared-stage-assembly/`

## Confirmed gap — 2026-09-06

The accepted W103077 publication driver selects a retained
`proposalManifest` by `proposal_manifest_digest`. No production path creates or
retains that document:

- `integration.driver._publish_operands` calls
  `load_manifest(manager, digest, "proposalManifest")` and refuses absence;
- `tests/integration/test_driver.py` supplies the document by mocking
  `load_manifest`, so its green publication cases do not prove a producer;
- `worker_manager.output` retains only the manager-authored `resultManifest`;
- the only production callers of `retain_manifest` retain `inputManifest`;
- the concrete Claude worker emits an empty `result_metadata` object for its
  proposal output; and
- no accepted custody operation returns arbitrary artifact bytes to a
  deployment-side caller.

W103083 can therefore compose every publication operand except the manifest
selector. Deferring publication is impossible because the accepted ordering
requires publication while the producer assignment is live, before checkpoint
freeze fences it.

## Clarification — `proposal.publish` is not the missing worker act

The frozen worker-control specification defines `proposal.publish` in the
manager-to-Authority/proposal-store direction. W103077's
`publish_candidate` implements that act. It is not a worker-to-manager
declaration operation and must not be duplicated inside the generic Worker
Manager.

What is missing is the upstream producer of the MANIFEST that authorizes that
act. The proposal manifest mixes two kinds of facts:

- worker-owned, proposal-specific claims such as the proposed head, author
  tests, implementation recap, and dossier evidence; and
- manager/Authority-owned facts such as the exact assignment, frozen result
  identity and digest, input/policy/profile account, artifact reference,
  current target, publish operation identity, and expected receipt digest.

Neither side may manufacture the other's half.

## Confirmed implementation boundary

Establish a proposal-specific producer seam before W103083 resumes:

1. The concrete Git proposal worker emits its bounded proposal claim through
   the already-frozen opaque `result_metadata` extension on its declared
   proposal output. `baton_worker` continues to treat that payload as opaque.
2. A proposal-specific integration owner reads the exact retained
   `resultManifest`, selects exactly one present `git-change-proposal` output,
   adopts the worker claim, and combines it only with facts re-read from their
   accepted owners. It does not read mutable `/output` paths or arbitrary
   custody bytes.
3. That owner validates the complete `proposalManifest`, retains it through
   `worker_manager.retain_manifest`, and returns its digest. Exact replay
   returns the same digest; a changed claim against the same frozen result
   refuses rather than publishing a second account.
4. W103077 remains the sole owner of Authority `proposal.publish`. W103083's
   adapter supplies the retained digest to `publish_candidate` at the existing
   pre-fence seam.
5. The generic Worker Manager remains artifact-neutral and never branches on
   the opaque proposal metadata namespace. The frozen worker-control schema is
   unchanged unless revalidation proves the recorded carrier cannot express
   the required claim; any such drift returns for targeted review before edit.

## Frozen path ownership

Subject to revalidation before the first edit, this Work owns only:

- `v12/worker/claude_agent.py`
- `v12/python/tests/manager/test_claude_agent.py`
- `v12/python/src/baton_v12/integration/driver.py`
- `v12/python/src/baton_v12/integration/__init__.py`
- `v12/python/tests/integration/test_driver.py`

Existing-test assertion or expected-behavior changes are explicitly authorized
only where the new proposal metadata and retained-manifest producer require
them. `worker_manager`, frozen schemas, `tools/stage_execution.py`,
`tools/single_worker.py`, and `tools/parallel_test.py` remain outside this
Work. If the producer cannot be completed in these five paths, return for
targeted review before editing anything else.

## Required regressions

- A real worker answer carries one namespaced proposal claim while
  `baton_worker` preserves it opaquely into the completion/result account.
- The exact frozen result produces one schema-valid retained
  `proposalManifest`, whose digest loads back through `load_manifest`.
- Exact replay returns the same retained digest and publication operands.
- Missing, malformed, extra, or wrong-namespace claim data refuses before
  Authority publication.
- Wrong assignment, result, input/policy/profile, target, proposal head,
  output digest, or artifact binding refuses before Authority publication.
- Zero or multiple proposal outputs, missing output, and a non-proposal output
  refuse.
- Target drift and changed claim replay retain no second manifest account and
  publish nothing.
- No credential, bearer, mutable host path, or raw output byte enters the
  manifest or a durable operation identity.
- Existing W103077 publication/replay tests and the Claude worker security and
  no-secret suites remain green.

## Open implementation detail

The exact namespaced `result_metadata` member and its bounded subdocument are
chosen during revalidation and recorded here before implementation. It must
carry only worker-owned facts; manager/Authority-owned members of
`proposalManifest` are forbidden from that claim even when the worker could
guess them.

## Approved ownership and checkpoints — 2026-09-06 — baton.prompt for Slawomir

Keep this five-path producer correction with baton.claude. It includes the
shared worker-claim contract, so splitting worker emission and host retention
before that contract is revalidated would create a dependent handoff rather
than safe parallel implementation. No sixth production path is authorized.

Publish three small progress checkpoints: (1) exact worker-owned metadata
contract and source of each manager-owned field pinned here; (2) emission and
real retention/load-back working together; (3) focused replay and refusal
checks plus independent-review handoff. Use actual manifest retention in the
positive proof, not a mocked proposal document. Existing producer regressions
remain required; the separate assembly hardening matrix is not added here.

If the present concrete worker cannot supply a real proposal head within this
boundary, report that specific incompatibility before inventing a head or
turning this fix into a Git/runtime redesign. Treat already accepted uncommitted
integration driver files as the inspected baseline and preserve their content.

## Revalidation before implementation — 2026-09-06 — baton.claude

PLAN item 2, run against the current tree before any edit. Re-read: the frozen
`worker-control-1.0` `proposalManifest`, `resultManifest`, `artifactOutput`,
`workerOutput`, `completionManifest`, `inputManifest` and `extensions`
definitions; `integration/driver.py` as accepted; `worker_manager/sealing.py`,
`output.py`, `manifests.py` and `worker_entry.py`; `worker/baton_worker.py`;
`worker/claude_agent.py`; and `source_profiles/checkout.py`.

**Confirmed — the gap section above is still exactly right.** Only
`inputManifest` is retained by a production caller of `retain_manifest`;
`output.record_frozen_result` retains the sealed `resultManifest` through
`manifests._retain_canonical`; nothing retains a `proposalManifest`; and
`driver._publish_operands` still refuses its absence. `check_manifest_structure`
does accept the `proposalManifest` definition, so the retention machinery
itself is ready — what is missing is entirely on the producer side.

**Confirmed — `proposal.publish` is still the manager-to-Authority act only.**
`publish_candidate` is its one implementation and no worker-side declaration
operation exists. That clarification needs no change.

The revalidation also found two incompatibilities that were not visible when
the boundary was frozen. Each of them, on its own, makes the pinned producer
unbuildable inside the five authorized paths, so none of those paths was
edited and this Work returns for targeted review as the frozen-path section
instructs.

### Incompatibility 1 — Confirmed — no worker-authored proposal fact reaches any document the producer may read

The pinned boundary has the concrete worker emit its claim through the frozen
opaque `result_metadata` extension, and has the integration owner adopt that
claim out of **the exact retained `resultManifest`**. The retained
`resultManifest` cannot carry it, and neither can anything else the owner is
permitted to open.

- `worker_manager/sealing.py:_answered` composes every present
  `artifactOutput` with a literal `"result_metadata": {}`. It is built from the
  manager's own output DECLARATION and the staged custody tree; the worker's
  answer is not one of its arguments. The `missing-optional` branch in the
  seal's own loop writes the same literal. The worker's per-output metadata is
  therefore discarded at the seal, not merely left unread.
- `sealing._completion_envelope` does open, validate, assignment-bind and
  digest the worker's `/output/output.json`, which is the one document that
  DOES carry `workerOutput.result_metadata` — `baton_worker.py:1207` copies the
  agent's object into it verbatim. But its caller binds the return as
  `_envelope, completion_manifest_digest = ...` and `_envelope` is never used
  again. Only the digest reaches the sealed body.
- The `completionManifest` document itself is never retained. `retain_manifest`
  has no production caller for it, so `load_manifest(manager, <that digest>,
  "completionManifest")` returns `None` by construction. The digest names a
  document the manager deliberately did not keep.
- The sealed body's other candidate carriers are manager literals too:
  `"evidence": []` and `"extensions": {}`.
- The framed `work` answer's `recap` is not an alternative route. It is
  validated as an envelope member by `worker_entry.ANSWER_MEMBERS` and is then
  dropped: `recap` appears nowhere else under `baton_v12/`, so nothing persists
  it and no accepted read answers it.

**Therefore:** after a successful attempt, the set of worker-authored facts a
deployment-side reader can obtain through an accepted operation is empty.
`source_base`, `implementation_recap` and `proposal_head` all fail on this
alone, before their individual availability is considered.

The corrections available are one line of `worker_manager/sealing.py` —
carrying the validated envelope's per-output `result_metadata` into the sealed
`artifactOutput` instead of the literal — or retention of the validated
`completionManifest`. Both are in `worker_manager`, which the frozen-path
section places outside this Work, and neither is an edit an implementer should
make unreviewed: the manager currently guarantees that a sealed
`artifactOutput`'s opaque member is manager-authored, and changing that changes
what every downstream reader of a sealed result may assume about its
provenance.

### Incompatibility 2 — Confirmed — the concrete worker produces no proposal head

`proposalManifest.proposal_head` is a `gitObject` — an `sha1`/`sha256`
algorithm word and a full 40- or 64-character lower-case object name — and
`driver._publish_operands` publishes `proposal_head["hex"]` to the Authority as
`candidate_digest`, having first required its algorithm to match
`target_revision`'s. It is the identity of the commit the Authority is asked to
make the new target.

`claude_agent.ClaudeAgent.work` never creates a commit, and no object name for
its candidate exists anywhere:

- `_checkout` runs `source_profiles.checkout_plan`, which clones the read-only
  mount to `/output/checkout` and detaches it at the declared base. That
  repository is left at the base commit and is never written to again.
- The provider edits `/output/candidate`, a plain `_copy_tree` of the checkout
  that **skips `.git`** (`VCS_METADATA`) under the git profile. It is not a
  repository, so nothing in it can name an object.
- `_publish` writes `proposal/{candidate/, change.patch, verification.txt,
  result.json}` — a content tree plus a unified diff. `result.json` is
  `baton.dogfood-proposal/1` and carries `disposition`, `why`,
  `changed_paths`, `source_entries`, `provider` and `verification`. No object
  name, no bundle, no pack.
- No commit-producing or object-naming Git vector exists in `claude_agent.py`
  or in `source_profiles`, and no producer of `proposal_head` exists anywhere
  under `v12/python/src`, `v12/python/tools` or `v12/src`.

This is the incompatibility the approved-ownership section anticipated, and it
is reported rather than worked around. The two available workarounds are
inventing a head, which the pinned scope forbids in terms, and having the
worker mint a commit in its workspace clone, which is the Git/runtime redesign
the same sentence forbids — and which would in any case publish to the
Authority an object name that exists only inside a container that is then
destroyed, since custody retains the proposal as a measured content tree and
not as a Git object store.

### Manager- and Authority-owned half — Confirmed available, pinned here

This is checkpoint 1's host side, and it is complete. Every member below is
reachable from `attempt_id` alone, through accepted reads only, with no mutable
`/output` path and no custody bytes:

- `assignment_ref` — `attempts.assignment_of(manager, attempt_id)`, projected
  as `driver._assignment` already does.
- `result_id`, `result_manifest_digest` — `output.frozen_output_of`'s
  `result_id` and `manifest_digest`, with `disposition == "completed"`.
- `input_manifest_digest`, `policy_digest` — the retained `resultManifest`.
- `runtime_profile_digest` — the retained `inputManifest`, loaded by the
  result's `input_manifest_digest`. It is retained in production, so this load
  succeeds.
- `output_digest`, `proposal_artifact` — the single present
  `git-change-proposal` `artifactOutput` of the retained `resultManifest`:
  its `content_manifest["tree_digest"]` and its `artifact`.
  `driver._one_proposal_output` already fixes the selection and cross-binding
  rule, so the producer consumes that rule rather than restating it.
- `target_revision` — the Authority's `canonical_target()`, with `algorithm`
  taken from the object-name width exactly as `source_profiles.BASE_KINDS`
  does. Nothing else may decide it.
- `proposal_id`, `publish_operation`, `publish_receipt_digest` — producer-
  derived and fully determined by the members above:
  `signature_digest = digest({"kind": "publish", "operands": <the eight
  operands minus operation_id>})`, and `publish_receipt_digest` the digest of
  the expected Authority answer. Both are spelled by
  `driver._publish_operands` today and must be composed from that one rule.
- `author_tests`, `dossier_evidence` — worker-owned in principle, but an
  `evidenceRef` requires a full `artifactRef` including a custody `locator`,
  which is a manager-owned fact a worker cannot know. The honest value from the
  present worker is the empty list, which the frozen schema permits. A worker
  claim carrying either of these would be a worker minting custody identities
  and must be refused.

### Open — `created_at` cannot be the clock

The required regression "exact replay returns the same retained digest" makes
`manifestHeader.created_at` a correctness member rather than a convenience
one: retention is keyed by the digest of the bytes, so a wall-clock instant
would retain a second, differently-keyed account of the same frozen result on
every replay — exactly the second account the same regression list forbids. The
one frozen instant available to the producer is the retained `resultManifest`'s
`manager_observed_at`. `manifest_id` is under the same rule and should be
derived from `result_id`. Recorded as **Proposed**; it needs the same review
round as the two incompatibilities.

### The `Open implementation detail` above stays open

The exact namespaced `result_metadata` member cannot be pinned yet: under
incompatibility 1 no such member is READABLE by the party that would adopt it,
and under incompatibility 2 one of the three facts it would carry does not
exist. The namespace SHAPE is **Confirmed** — the frozen `extensions`
definition fixes property names to `^[a-z0-9]+(?:[.-][a-z0-9]+)+/[1-9][0-9]*$`,
and `source_boundary.CONSUMPTION_KEY` (`baton.source-boundary/1`) is the
in-tree precedent for a bounded subdocument under one such key. The subdocument
itself is deliberately not pinned, because pinning a contract whose carrier and
whose content are both unresolved is the kind of ruling this dossier exists to
prevent.

### What was not done

No file outside this dossier was changed. `claude_agent.py`,
`test_claude_agent.py`, `integration/driver.py`, `integration/__init__.py` and
`test_driver.py` are byte-identical to the inspected baseline; `worker_manager`
and the frozen schemas were read only.

## Independent scope review — 2026-09-06 — baton.codex

**Confirmed:** both incompatibilities reproduce in the inspected tree. See
`review-2026-09-06T18-49-39Z.md` and
`evidence/repro-metadata-carrier.py`. The independent real-seal and actual
retention/load-back probe carries nonempty worker metadata in the completion
envelope and observes `{}` in the sealed and retained result. Exact seal replay
preserves that loss; the completion document is not retained. The concrete
worker produces no candidate commit or durable Git object transport.

**Explicit clarification superseding the provenance interpretation in
“Incompatibility 1”:** the empty literal is an implementation defect, not a
guarantee that opaque metadata is manager-authored. The frozen worker-control
SPEC.md sections 7.3 and 8.4 require carrying the worker's opaque metadata in
the manager-authored result receipt. The worker owns the claim; the manager
owns the measured integrity, custody and assignment binding. Restoring that
carrier need not change the frozen schema or make the manager interpret Git.
The characterization of this as a one-line correction is also superseded:
the implementation must bind by output name, handle optional/no-envelope
endings, and preserve committed-result replay without reopening worker state.

**Confirmed prior decision:** the 2026-09-01 superseding Git ruling and later
review-cycle clarification in
`baton:work/records/2026/09/finding-v12-proposal-import-base-closure/FINDING.md`
already require real private proposal commits, durable object transport and
continued private history across corrections. The 2026-09-06 integration-owner
clarifications retain format-neutral core orchestration and do not require a
new deterministic Git adapter. The missing concrete worker capability is not
permission to invent a head or reinterpret a plain tree digest as one.

**Proposed for owner scope approval:** repair opaque metadata carriage in a
separate small sealing leaf, initially `worker_manager/sealing.py` plus
additive `tests/manager/test_sealing.py` cases; separately plan the concrete
worker's real proposal-head and durable-object output against the existing
private-line ruling. Both block an honest publication demonstration and are
not later-pass hardening. Keep this Work as the bounded manifest composer
after those seams exist. No additional production path is authorized by this
review, and no sibling dossier was created without a Work.

**Proposed deterministic composition:** use the frozen result's
`manager_observed_at` as proposal `created_at` and derive the manifest identity
from the exact frozen result account. A fresh per-call wall clock is unsuitable;
a separately persisted first clock read is possible but adds unnecessary state.
The namespace subdocument remains open until the real head producer is scoped.

State: targeted review complete, owner scope decision needed. The approved
five-path restriction remains unchanged. No implementation candidate is signed
off; the append-only review is research evidence, not integration authority.

## Approved prerequisite split — 2026-09-06 — baton.prompt for Slawomir

Slawomir approved two parallel prerequisite leaves, superseding the pending scope
decision above and the expectation that this composer alone supplies the missing
concrete head and carrier:

- W105574, tuner: `work/records/2026/09/finding-v12-sealed-worker-metadata/`.
  Bounded sealing repair and additive tests; artifact-neutral carriage.
- W105575, K: `work/records/2026/09/finding-v12-concrete-worker-proposal-head/`.
  Bounded concrete-worker output planning, then implementation after exact reviewed
  scope acceptance. Real private head and durable objects, no core Git adapter or
  renewed whole-candidate archive ceremony.

This composer waits on BOTH accepted providers through ledger dependencies, not
parking. Its existing five-path ceiling remains; it may not overlap concrete
worker edits while that provider is active. Revalidate against accepted provider
bytes before resuming. Shared assembly continues to wait on this composer. Later
hardening stays outside this first-demonstration prerequisite split.

## Both incompatibilities are resolved — 2026-09-07 — baton.claude

Revalidated against the tree before writing anything. The two 2026-09-06
incompatibilities are **superseded as blockers**; their findings stay above as
the record of why the split happened.

- **Incompatibility 1 is gone.** `sealing._seal` now takes the validated
  envelope's per-output `result_metadata` by declaration NAME and carries it
  into the sealed `artifactOutput` — `_answered` receives it as an argument and
  the `missing-optional` branch uses the same map. So a worker claim now
  reaches the retained `resultManifest`, which is exactly the carrier boundary
  item 2 always described.
- **Incompatibility 2 is gone.** The concrete worker's `git-line` profile works
  in the manager's prepared private line and authors one real commit, and
  `baton.git-proposal/1` carries `base`, `head`, `transport` and `recap` on the
  declared proposal output.

Provider bytes at the moment of this revalidation, matching their signed-off
records: `worker_manager/sealing.py`
`fa127f926785eb0e3b56cda2359141f066b4de4851b3de1e7cd7d6d3f87fdada`;
`worker/claude_agent.py`
`5f5e553b86c143cfd5969c7737ef6811a9c9d5e97b0206a04bf17ef80bed95d8`;
`source_profiles/checkout.py`
`037f197ad2cfc3dd9c373bcddf447adaa62160a74f7e5d1b4af0a783e73185c7`.

### The `Open implementation detail` is now CLOSED

The namespaced member could not be pinned while its carrier was unreadable and
one of its facts did not exist. Both are fixed, so it is pinned here as the
producer consumes it:

```json
{"baton.git-proposal/1": {"base": "<B>", "head": "<Hn>",
                          "transport": "objects.bundle",
                          "recap": "<bounded worker recap>"}}
```

Exactly four members; an extra one is REFUSED rather than ignored, because the
members a producer would be tempted to accept are precisely the ones it must
compose itself. `base` is the immutable publication base and stays B across
correction rounds, which is what keeps `source_base == target_revision` true
while the canonical target has not moved. `transport` is a locator INSIDE the
worker's own measured output and is cross-bound against the frozen content
manifest's entry list — it never stands in for the manager's retained artifact
account, which the composer binds from `artifactOutput` as before. The three
manifest members it feeds are `source_base`, `proposal_head` and
`implementation_recap`; `author_tests` and `dossier_evidence` are the empty
list, because an `evidenceRef` is made of a custody `artifactRef` no worker can
mint.

### What the producer is, and where it lives

`integration.driver.retain_proposal(manager, publisher, *, attempt_id)` →
the retained proposal manifest digest. It reads the frozen output summary, its
retained `resultManifest`, that result's retained `inputManifest`, the fixed
assignment, the one present `git-change-proposal` output, and the Authority's
current canonical target; adopts the worker claim; validates and retains one
`proposalManifest`; and answers the digest `publish_candidate` selects on.

Two rules were extracted rather than restated, as the pinned host half
required: `_publish_signature` and `_expected_answer` are now one spelling used
by both the producer and the publisher, so a signature the producer composes
cannot drift from the one its own consumer recomputes. `_one_output` is the
selection half of `_one_proposal_output`, separated because the producer has no
proposal to cross-bind against yet.

`created_at` is the frozen result's `manager_observed_at` and `manifest_id` is
derived from `result_id`, which is what makes exact replay return the SAME
retained digest: retention is keyed by the digest of the bytes, so a clock read
would retain a differently keyed account of one result on every call.

Target drift refuses BEFORE retention and before publication, so a moved
canonical target leaves no second durable account behind.

## Independent candidate review — 2026-09-07 — baton.codex

**Confirmed:** all three candidate hashes and the unchanged concrete-worker and
sealing provider hashes match M106783. The worker claim remains proposal-specific;
the generic manager remains opaque. Actual retention validates and reloads the
proposal; the frozen timestamp makes ordinary replay deterministic. The existing
publication signature/expected-answer extraction preserves the accepted rule.

The new tests retain real manifests, but mock `frozen_output_of` and
`assignment_of` as well as supplying the Authority. The handoff phrase "only the
Authority supplied" overstates that coverage. Independent
`evidence/review-producer-boundaries.py` fills those two read boundaries using the
existing disposable attempt fixture and real `request_freeze`, record, assignment
read, retention, load-back and publication driver. Its ordinary publication/replay
case passes; a changed claim cannot replace the same frozen result, and the
original proposal digest still replays. The runtime seal and Authority are fixture
providers, so this remains a bounded manager-composition proof, not live execution.

**Confirmed [P2], changes requested:** `retain_proposal` sets `manifest_id` to
`proposal-` plus `result_id`. Frozen `opaqueId` permits 160 characters for both
members. A result ID of 152–160 characters therefore becomes a 161–169-character
proposal manifest ID and fails retention even though the result is valid. The
independent probe records a 160-character result through real `request_freeze`
successfully, then fails in proposal retention with `manifest_id breaks maxLength`.
The concrete seal's `result-<attempt_id>` construction can also reach this valid
result width; this is not malformed input being correctly refused.

**Proposed bounded correction:** derive a bounded deterministic manifest identity
from the exact frozen result account, for example through the existing digest-based
identity helper. Do not truncate away distinguishing suffixes, introduce a clock or
new journal, shorten the frozen schema's accepted result IDs, or widen schema scope.
Add maximum-width and adjacent-boundary cases plus replay coverage in the already
authorized `tests/integration/test_driver.py`; the existing exact manifest-ID
expectation may change only as required by this bounded identity correction.
This is inside the original accepted five-path scope, not new edit authority.

State: changes requested, not signed off. Review and candidate fingerprints are in
`review-2026-09-07T02-59-03Z.md`. Provider blockers are resolved; the identifier
construction is the current actionable correction. PROGRESS remains untouched.

## Final independent review — 2026-09-07 — baton.codex

**Resolved and superseded as a blocker:** the P2 identifier overflow above is
fixed. `manifest_id` now uses `_identity("proposal-manifest", account)` over the
same frozen assignment/result/digest/head account as `proposal_id`. Its bounded
digest-based construction preserves distinctness and deterministic replay for
the full accepted result-ID width. No schema change, truncation, clock or new
journal was introduced.

The exact delta was independently verified by reversing the bounded edits in
memory and reproducing both previous candidate SHA-256 values. Production changes
are only the shared account extraction and manifest-ID construction; test changes
are two added boundary/distinctness cases and the one necessary existing ID
expectation. Width cases cover 151, 152, 159 and 160; distinctness covers four IDs
across widths 159/160. Provider bytes remain unchanged at their accepted hashes.

The implementer reports the unchanged reviewer probe passing all three cases,
integration 401, job-manager 387 and supporting suites 347 passing. Reviewed the
test/code changes and those results; no redundant successful-suite rerun was
needed. Earlier independent evidence already exercised real frozen-result and
assignment reads, publication composition and changed-claim refusal. Runtime
seal/Authority fixtures remain the explicit limit, not a live assembly claim.

State: **signed off**, pending owner acceptance/closure. Exact three-path candidate
and test-authority evaluation: `review-2026-09-07T03-04-53Z.md`. This supersedes
the changes-requested status above without changing its historical review.
Shared assembly can consume the retained digest through the pre-fence publication
seam after owner disposition; runtime access and custody remain their own gates.
