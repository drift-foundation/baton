# Plan

## Current disposition — 2026-09-07

Owner accepted the final three-path candidate after independent sign-off and
hash revalidation. Retained proposal composition is complete and available to
shared assembly. Prior stages below are historical. Live access/custody remains
separately scheduled; no Git or deployment action is implied.

1. [done; baton.codex 2026-09-06] Confirm the missing production producer,
   distinguish it from the already implemented manager-to-Authority
   `proposal.publish` act, and freeze the five-path boundary.
2. [done; baton.claude 2026-09-06] Revalidate the proposal schema, frozen
   result, worker output, Authority target, and current Git-proposal artifact
   account. Outcome in FINDING: the manager/Authority half of the manifest is
   confirmed available and pinned, and two incompatibilities block the
   worker-owned half. The namespaced worker-claim subdocument is therefore NOT
   pinned, and no authorized path was edited.
3. [done; providers accepted 2026-09-07] W105574 preserves opaque per-output
   metadata in the retained result, and W105575 emits real private proposal heads
   with durable object transport. Both earlier incompatibilities are resolved;
   the generic Worker Manager does not interpret the proposal claim.
4. [done; baton.claude 2026-09-07] Add the proposal-specific
   owner that cross-binds the worker claim with the retained result and
   accepted manager/Authority facts, validates and retains one
   `proposalManifest`, and returns its digest for the publication driver. The
   exact four-member worker namespace and manager-owned sources are pinned in
   FINDING; the real head provider now satisfies the former missing source.
5. [done; baton.claude 2026-09-07] Added positive, replay, corruption,
   cross-wire, target-drift, no-publication and no-secret regressions over a
   REAL Worker Manager store: really retained input and result manifests, a
   really retained proposal manifest, a real `load_manifest` load-back, and a
   real `publish_candidate` over that digest. Focused integration, job-manager,
   worker, sealing and contract suites all pass.
6. [done; independent review 2026-09-06] Both incompatibilities confirmed;
   see `review-2026-09-06T18-49-39Z.md`. The frozen contract already requires
   opaque worker metadata carriage. Earlier Git rulings already require a
   real private proposal head and durable object transport. This historical review
   led to the now-completed split. Deterministic frozen timestamp composition is
   implemented.
7. [done; providers closed satisfying 2026-09-07] The artifact-neutral sealing repair
   is owned by `work/records/2026/09/finding-v12-sealed-worker-metadata/`;
   concrete proposal-head/object delivery planning and accepted implementation by
   `work/records/2026/09/finding-v12-concrete-worker-proposal-head/`.
   The provider bytes match their accepted records. The original composer
   five-path ceiling remains; no further provider edits are scheduled here.
8. [signed off; independent review 2026-09-07] The manifest
   composer is `integration.driver.retain_proposal`. Three of the five
   authorized paths changed — `integration/driver.py`,
   `integration/__init__.py` and `tests/integration/test_driver.py`; the two
   concrete-worker paths are the accepted provider's and are byte-identical to
   its signed-off record. Nothing moved `proposal.publish` or generic artifact
   semantics into the Worker Manager. Once accepted, the retained digest is
   what shared assembly supplies to `publish_candidate` at the existing
   pre-fence seam.
9. [done; baton.claude 2026-09-07] Fixed the bounded manifest identity in
   `integration/driver.py`: a valid 152–160-character result ID overflowed
   `opaqueId` after the `proposal-` prefix. The manifest id is now
   `_identity("proposal-manifest", account)` over the same account
   `proposal_id` is taken from — deterministic, distinct, bounded by this
   module's own composition rather than by its input's length, and never
   truncated, because truncation is how two distinct results become one name.
   Boundary cases added at 151, 152, 159 and 160 characters plus a distinctness
   case; only the one existing manifest-id expectation changed. No schema,
   provider or assembly expansion. The reviewer probe re-runs at exit 0 and the
   focused producer/publication suites pass. Independently reviewed and signed off
   at review-2026-09-07T03-04-53Z.md; no remaining finding.

Newest review: `review-2026-09-07T03-04-53Z.md`. Prior valid-ID failure is fixed;
the unchanged reviewer probe is reported passing all three cases. Candidate delta,
test authority and successful suite evidence were audited, not redundantly rerun.
Owner acceptance/closure is next. No live runtime proof is claimed.
