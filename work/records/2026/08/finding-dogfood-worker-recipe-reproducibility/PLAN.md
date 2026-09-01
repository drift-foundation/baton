# Plan: make the dogfood worker recipe reproducible across days

Status: approved reuse-by-digest correction; implementation-ready

Work: `W55361`

## Current decision gate — resolved 2026-08-31

The approver selected reuse-by-immutable-digest and removed cross-day
byte-reconstruction from MVP acceptance. The other two supply-chain designs
remain historical alternatives and are not implementation authority.

## Proposed implementation sequence after approval — superseded

**Superseded in full by the approved sequence below.** This preserved sequence
describes the content-locking design that was presented but not selected.

1. In an authorized build environment, inventory the exact explicit platform, base digest, Debian packages, npm package graph/integrities, and provider native/postinstall payload used by the chosen known-good worker artifact. Record facts rather than inferring them from the current mutable upstream state.
2. Define and review a durable lock/provenance manifest for every external input. Assign ownership and retention for any foundation image, snapshot, or staged artifact store.
3. Revalidate the `W6633` normalization contract against the selected recipe. Preserve true content differences; qualify only the overbroad independent-execution prose.
4. Change the canonical dogfood recipe to use an immutable base and either the approved foundation digest or fully locked, verified inputs. Remove silent canonical overrides such as an untracked `CLAUDE_VERSION` build argument, or make every override part of the explicit artifact identity.
5. Add positive independent-build coverage and negative substitution/missing-input coverage for each external input class. Exercise an offline or network-disabled final assembly where the selected design permits it.
6. Run the worker-image unit suite, dogfood image boundary suite, no-secret checks, and one supervised end-to-end control using the recorded digest. Append exact commands and identities to `PROGRESS.md`.
7. Request independent review against this finding and the recorded approval ruling.

## Approved implementation sequence

1. Append the ruling to any active dogfood Work whose current plan still says
   a fresh attempt requires a rebuild. Mark that instruction superseded; do not
   rewrite the historical attempt account. Record its current selected digest,
   selection event, approved reason, and validation evidence in that Work's
   chronological finding and reflect the digest in its current plan.
2. Qualify `tools/worker_image.py` so its convergence claim is explicitly
   conditional on identical base identity and content inputs. Preserve the
   content-sensitive normalizer and all of its existing assertions.
3. Document at the dogfood operator and recipe boundaries that the artifact is
   selected by validated digest, a new attempt reuses the current selection,
   and build output is only a candidate until a recorded update explicitly
   selects its digest. Preserve the operator's existing not-an-authorization
   boundary: the owning Work record authorizes selection; the operator consumes
   the exact digest grant and reports what it launched.
4. Revalidate the existing executable fences: grants reject mutable tags,
   sealed input and evidence name the selected digest, and retry binding
   refuses a changed digest. Add only the smallest regression necessary to
   keep the new operational boundary from being contradicted again.
5. Run the focused `test_worker_image_build`, `test_dogfood_operator`, and
   recipe-inspection tests. The authorized environment may run the existing
   real-image/no-secret gates if already required by its release gate, but this
   Work does not authorize a rebuild or provider attempt merely as evidence of
   the policy correction.
6. Record the exact selected digest and selection event in the next dogfood
   attempt's durable record, then request independent review.

## Review focus presented before approval — superseded

The content-locking checks below belong to the design the approver did not
select for MVP. They are retained as decision history, not current acceptance.

- no mutable tag, package index, transitive dependency, redirect, or postinstall download remains outside the lock;
- locked artifacts are durably obtainable, not merely checksum-verified while upstream happens to serve them;
- target platform is explicit and included in provenance;
- reproducibility evidence uses independently assembled inputs, not only a warm local cache or one build session;
- image normalization never maps different payload bytes to one claimed identity;
- no bearer, registry credential, npm token, or provider credential enters the image, manifest, evidence, or build logs.

## Approved review focus

- the next attempt reuses the currently selected digest unless a recorded
  approved update event selected another;
- a build result cannot select itself and an attempt cannot silently select a
  digest merely by placing it in a newly written grants file;
- every attempt still seals and reports the exact digest it launched, and a
  handoff retry rejects a changed digest before outward action;
- the normalizer remains content-sensitive and its prose no longer promises
  convergence across different fetched content; and
- no image build, provider call, credential access, or supply-chain redesign
  is smuggled into this bounded operational correction.

## 2026-09-01 implementer round

The approved sequence is implemented, bounded as ruled.

1. [done, verified not assumed] W51487 carried the dated supersession with its
   selected digest, selection event and reason; appended while that Work was
   active and not rewritten when it closed.
2. [done] `worker_image.py`'s convergence claim is conditional on identical
   base identity and fetched content, with the measured cause recorded. The
   normalizer and its assertions are untouched.
3. [done] The selected-by-digest boundary is documented at the dogfood operator
   and at the recipe, preserving the operator's not-an-authorization boundary.
4. [done] The three fences revalidated; the retry-digest one was documentary
   and now has `test_a_retry_cannot_quietly_select_a_different_worker_image`.
   Dropping the digest from `_RETRY_BINDING` is CAUGHT.
5. [done] 277 focused tests OK. No build, no provider attempt, no credential.
6. [belongs to the next attempt] Record the selected digest in that attempt's
   durable record.
7. [done; signed off in review 2026-09-01T03-48-23Z] Independently verify the
   approved reuse-by-digest boundary, executable retry fence, W51487
   supersession, and absence of content-locking or rebuild scope.
