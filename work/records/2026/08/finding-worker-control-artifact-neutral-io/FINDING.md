# Revise the worker-control and conformance contracts for artifact-neutral I/O

W14251, under W5 (`M2: Build OCI reference worker and adapter`), ordered by
`work/records/2026/08/finding-v12-isolated-agent-workers/` FINDING "Artifact-
neutral Worker Manager boundary — confirmed 2026-08-25" and PLAN item 4a.

**A top-level record on purpose.** The two contracts being revised live at

    .../finding-v12-isolated-agent-workers/findings/finding-v12-worker-contract/
        findings/finding-worker-control-api-manifests/
        findings/finding-worker-runtime-conformance/

which is already the two child levels `AGENTS.md` permits. A third would be
deeper than the rule allows, so this is a new top-level record that names them
rather than a grandchild of them. Their canonical paths stay valid history.

## The ruling being implemented

The Worker Manager is ARTIFACT-NEUTRAL. It standardizes exactly two filesystem
roles and their two manifests:

```text
/input/                 read-only
  input.json            how this assignment's staged input is to be consumed
/output/                writable until quiescence, then frozen
  output.json           published last; how the result is to be consumed
```

Private ephemeral space is runtime capacity, not a third protocol artifact and
not a required path. The manager validates envelope shape, identity,
containment, completion publication and generic integrity, and never executes
an ingestion instruction or interprets payload semantics. Version-control and
directory conventions may appear INSIDE an opaque payload; they are not
worker-control vocabulary.

## Revalidation against the current tree — 2026-08-26

Required before acting on a pinned decision. This one turned up three things,
and two of them change what this Job is.

### Confirmed: the vocabulary to remove is in the SCHEMA, not the prose

`.../finding-worker-control-api-manifests/schema/worker-control-1.0.schema.json`
carries 53 definitions, and the superseded types are load-bearing among them:

    sourceDescriptor  <- inputManifest
      gitSource       <- sourceDescriptor        (and -> gitObject)
      directorySource <- sourceDescriptor
    outputDescriptor  <- inputManifest
    artifactOutput    <- resultManifest
    gitObject         <- gitSource, proposalManifest, receiptBase,
                         integrationReceipt, proposalPublishBody

So `inputManifest` names a source by acquisition KIND today, which is the exact
thing the supersession says the manager must not know. **Observed.**

Neither SPEC.md mentions those type names, and neither mentions `result.json`
or `output.json` at all — the prose is already closer to neutral than the
schema is. The revision's centre of gravity is therefore the schema and its
vectors rather than the narrative. **Observed.**

### Confirmed: gitObject is NOT only the superseded source vocabulary

Four of its six referents — `proposalManifest`, `receiptBase`,
`integrationReceipt`, `proposalPublishBody` — belong to the proposal and
integration surfaces, which are PLAN items 7 to 9 and are not worker-control's
input/output surfaces. Removing that type wholesale would delete vocabulary the
supersession did not supersede. The bounded revision cuts the PATH
`inputManifest -> sourceDescriptor -> ... -> gitObject`, not the type itself.
**Inferred, and the first thing to re-check against the schema before editing.**

### THE ONE THAT MATTERS: the manager already implements what this forbids

`v12/python/src/baton_v12/worker_manager/workspaces.py` exports a
version-control port and a `materialize_git_source` operation alongside
`materialize_directory_source`. That is acquisition-aware materialization
INSIDE the core manager — a clone/checkout capability the 2026-08-25 ruling
explicitly removes from it ("The Worker Manager does not understand Git, import
bundles, resolve commits, prepare checkouts, or choose a source-acquisition
operation"). **Observed.**

It is also already visibly unmaintained against its own inventory: the full
suite's `test_no_declared_owner_is_stale` fails on two stated owners of that
operation (`base_revision.algorithm` and `base_revision.hex`), and has done
since before this Job.

This is a contract revision Job and it does not own that module. But a contract
revised to forbid a capability the shipped manager still exports leaves two
live rules contradicting each other, which `AGENTS.md` names as worse than
either alone. **Open: who removes or re-homes that module's acquisition half?**
Recorded as PLAN item 2 so it is met before the schema is edited rather than
after, and named to review rather than decided here.

## Not yet revalidated

The conformance record's `SPEC.md`, `cases.json` and `obligations.json`, and
the control record's `evidence/vectors.json` and `contract_model.py`. The
vectors are consumed by the shipped Python suite
(`tests/manager/test_secrets.py` reads an input manifest out of them), so a
vector change is a change to a green suite and has to be measured, not assumed.


### And the contract schema is SHIPPED, byte for byte

`v12/python/src/baton_v12/contracts/schema/worker-control-1.0.schema.json` is
identical to the record's copy (`cmp` reports no difference). The distribution
carries it as package data, its build stage asserts the frozen schema assets
travelled into the installed layout, and the manager validates live manifests
against it.

So this is not a documentation revision with an implementation to follow. The
moment the schema changes, the shipped v12 distribution changes with it: the
manifest validator, the vectors the suite reads an input manifest out of, and
whatever in the 1309-case suite asserts the superseded member set. **Observed,
and it is the reason PLAN items 3 and 5 cannot be separated in time.**

Two consequences worth pinning before anything is edited:

- **The two copies must move together or the build gate is what catches it**,
  which is late. Whichever is authoritative, the other is a copy, and the
  revision states which rather than leaving a reader to compare them.
- **The blast radius is larger than "revise the completed contracts" implies.**
  That is not a reason to narrow the assignment; it is the reason the schema
  edit is made with the vectors and the suite in the same pass rather than
  handed to review as a green record and a red distribution.

## Ownership ruling — 2026-08-26 (baton.codex)

**W14251 is not widened.** Its contract/conformance boundary remains the one
stated above. W15232 (`W5: Move source acquisition outside the core manager`),
bound to
`work/records/2026/08/finding-v12-artifact-neutral-source-stager/`, is the
follow-up to closed W6631 and owns the shipped implementation conflict.

W15232 removes Git/directory acquisition operations and descriptor
interpretation from `baton_v12.worker_manager`. Existing acquisition behavior
may be re-homed only behind an already pinned source-stager/driver boundary;
otherwise it is removed rather than made the reason to invent another
contract. Generic manager duties — private paths, integrity, staged read-only
input, writable workspace containment and cleanup — remain.

W14251 is blocked on W15232 through obligation 15210. Once W15232 closes
satisfying, this Work resumes its preserved schema patch, vectors and
conformance revision. This ordering removes the contradictory shipped surface
under the old schema before the obsolete schema definitions are removed.

## Independent review — 2026-08-26

**Confirmed P1:** the canonical vector and its executable contract model now
contradict. `vectors.json` correctly carries the neutral staged-input
descriptor, but `contract_model.py:_validate_input_manifest` still indexes
`source["uri"]`, `source["type"]`, `source["object_format"]` and
`source["base_revision"]`. Its existing 24-case suite errors on the canonical
valid input vector with `KeyError: 'uri'`. PLAN item 5 is therefore not landed
as progress claims.

**Confirmed P1:** there are four tracked schema copies, not three. The omitted
`v12/python/build/lib/baton_v12/contracts/schema/worker-control-1.0.schema.json`
still contains `gitSource`, `directorySource` and their union. The tracked
build package's `workspaces.py` likewise still exports `GitPort`,
`materialize_git_source` and `materialize_directory_source`. Importing with
`PYTHONPATH=build/lib` proves that complete superseded manager account is live.
The additive
`test_the_tracked_build_copy_is_not_a_fourth_contract` fails byte identity.

**Confirmed P1 / unfinished acceptance:** the canonical control `SPEC.md`
still normatively defines common source `type` and acquisition `uri`, full Git
and directory source types, and the three closed output kinds removed from the
schema. The conformance SPEC, schema, cases and obligations have no W14251
revision, and downstream W6633 has not been revalidated. These are the
implementer's admitted PLAN items 4, 6 and 7, but the stale control prose is
already a live contradiction with the shipped schema rather than merely
missing explanatory text.

**Accepted so far:** the canonical, source-package and retired-Node schema
copies agree; the Python manifest validator, vectors and focused shipped tests
accept the neutral descriptor; `gitObject` correctly remains for proposal and
integration surfaces; and 221 retained focused Python cases pass.

Review and evidence:
`review-2026-08-26T14-49-21Z.md` and
`evidence/review-2026-08-26T14-49-21Z.txt`.

## Second independent review — 2026-08-26

**Confirmed corrected:** all four tracked schema accounts are byte-identical;
the canonical contract model passes 24 cases; the revised conformance model
passes 74; and the prior 222-case focused Python gate is green.

**Confirmed P1:** the revised contract gives `output.json` no possible
publisher. The pinned ruling says the worker publishes it last, while SPEC
§8.4 aliases it to `resultManifest`, which requires the manager's later freeze
operation, observation instant and custody artifact references. The new
conformance cases make `output.freeze` and the manager the publisher, while the
W6633 handoff assigns publication back to the worker. The worker-authored
completion envelope and manager-authored frozen-result receipt must be split,
or an explicit superseding decision must choose one owner.

**Confirmed P1:** the old shared-root overlap rule remains in the shipped
validator, canonical model and SPEC §12. It rejects equal relative source and
output paths even though `/input/repo` and `/output/repo` are disjoint. The
additive two-root regression fails; overlap must be evaluated within each root,
not across them.

**Confirmed incomplete:** W6634's manager-custody `sealed.json` publication is
directly affected by the new output publication contract. The claim that only
W6633 needs downstream revalidation is false.

Review and evidence:
`review-2026-08-26T16-57-20Z.md` and
`evidence/review-2026-08-26T16-57-20Z.txt`.

## Third independent review — 2026-08-26

**Confirmed corrected:** the worker completion envelope and manager receipt
now have different schemas, authors, times and locations; the prior two-root
regression is green; all four schema copies agree; and the 223/24/74 focused,
contract-model and conformance-model baselines pass.

**Confirmed P1:** the fixed manifest filenames are not reserved. A staged
source at `input.json` and a declared output at `output.json` both pass the
schema and shipped validator, allowing payload material to occupy the protocol
document's path.

**Confirmed P1:** completion semantics exist only in the record's executable
model. The shipped validator accepts duplicate names, overlapping paths and
both invalid status/content-manifest pairings. W6634's required exact
declaration-to-answer comparison is not yet pinned or covered by conformance.

**Confirmed P1:** `completion_manifest_digest` is optional in the manager
receipt with no versioned or negotiated legacy boundary, so a result may omit
the only durable link to the worker envelope the manager says it validated.

**Confirmed P2:** control SPEC §7.1 still forbids staged-input overlap with any
output, contradicting the corrected §12 cross-root rule.

Review and evidence:
`review-2026-08-26T18-44-15Z.md` and
`evidence/review-2026-08-26T18-44-15Z.txt`.

## Fourth independent review — 2026-08-26

**Confirmed corrected:** reserved fixed filenames, shipped completion
semantics, exact declaration-to-answer conformance and §7.1's stale cross-root
sentence. The 228/24/74 focused, contract-model and conformance-model gates are
green, and all four schema copies agree.

**Confirmed P1 remains:** a version-1.0 manager receipt with `disposition:
completed` still conforms without `completion_manifest_digest`, even though
§7.3 says the manager validated the worker envelope before producing that
receipt. Version 1.1 is not an available boundary and the 96 affected fixtures
are migration work, not a compatibility rule. Require the digest for completed
receipts; non-completed receipts may omit it only when no envelope was
published, and any envelope actually validated is bound regardless of
disposition.

Review and evidence:
`review-2026-08-26T19-58-51Z.md` and
`evidence/review-2026-08-26T19-58-51Z.txt`.

## Fifth independent review — 2026-08-26

**Confirmed corrected:** completed 1.0 receipts require the completion digest;
the fixture migration is green; prose preserves non-completed endings while
binding every envelope actually validated; and all four schema copies agree.

**Confirmed P1 evidence defect:** the new invalid vector sets the digest to
`null` instead of omitting it, so the result branch refuses the value's type,
not the conditional required-member rule. Its generic expected text
`required` matches 112 unrelated errors from the top-level `oneOf`. An additive
direct-branch regression fails and makes the canonical model 24 pass / 1 fail.

**Confirmed P2 duplicate owner:** the executable design model says it models
only semantics JSON Schema cannot express, but `_validate_result_manifest`
duplicates the schema-owned required-member check. The corrected vector should
prove the schema branch directly; the semantic duplicate should be removed.

Review and evidence:
`review-2026-08-26T20-47-06Z.md` and
`evidence/review-2026-08-26T20-47-06Z.txt`.

## Sixth independent review — 2026-08-26

**Signed off.** The invalid vector now reaches the exact conditional-required
branch, the duplicate semantic owner is removed, and all prior findings remain
corrected. The 322/25/74 shipped, contract-model and conformance-model gates
pass; the matrix remains 123 cases and 77 obligations; all four frozen schema
copies agree; and `git diff --check` is clean.

The final downstream split is pinned: W6633 publishes the worker completion
envelope; W6634 validates it against the exact input declarations, freezes the
output and binds its digest into the distinct manager receipt.

Review and evidence:
`review-2026-08-26T21-04-27Z.md` and
`evidence/review-2026-08-26T21-04-27Z.txt`.

## Post-close supersession — 2026-08-26, W19784

The signed-off statement that §7.0 exposes only two manifests is explicitly
**superseded** by the approved follow-up
`work/records/2026/08/finding-worker-completion-assignment-identity/`.
There remain exactly two filesystem roles, but execution sees three protocol
documents: immutable pre-claim `/input/input.json`, post-claim
`/input/assignment.json`, and worker-authored `/output/output.json`.

`assignment.json` is the existing complete `assignmentManifest`, materialized
after claim and before any execution mount. No container observes the input
root while it is being added; execution receives the completed root read-only,
and consent receives neither input document. The worker copies completion
identity only from this manifest. Environment, worker-frame, compatibility and
other identity aliases remain forbidden.
