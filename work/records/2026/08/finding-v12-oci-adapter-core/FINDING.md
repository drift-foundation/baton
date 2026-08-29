# Finding: build the constrained OCI adapter core

Promoted implementation record for the second bounded child of W5. Its Work is
contained by W5 while this permanent dossier is top-level because the parent
record is already at maximum nesting depth.
Canonical Work: W6632.

## Confirmed boundary

Implement a runtime-neutral Python adapter core for Docker and compatible
Podman: closed command vectors, image/profile/policy resolution, canonical
mount sources, fixed non-secret reconciliation labels, bounded diagnostics and
typed start/list/inspect/stop/destroy observations. The engine reports facts;
it never decides assignment authority, settlement or retry.

The adapter must prove the exact runtime identity and positive absence rather
than treating an empty list, a stop acknowledgement or engine prose as death.
Drop all capabilities, deny privilege escalation and nested runtime/socket
access, apply fixed user/resource/network/filesystem policy, and never mount
authority/config/database/repository internals or another worker's state.

No source materialization, provider code, output acceptance, credentials or
manager lifecycle orchestration belongs here.

## Acceptance

- Golden Docker and Podman argv/inspect vectors share one worker-control
  vocabulary and reject unknown/contradictory engine data.
- Exact label and image/profile/policy digests survive restart reconciliation.
- Stop, quiescent, destroyed and positive absence remain distinct.
- Duplicate starts, stale identities and ambiguous multi-match listings fail
  closed without inferring authority from engine state.
- Mutable engine smoke tests are isolated and leave their own resources absent.

The implementer creates and exclusively owns `PROGRESS.md` when claimed.

## Independent correction re-review — 2026-08-25

Disposition: **changes requested; the returned correction is partial**.

**Confirmed:** the six original reviewer regressions are corrected. Engine
names are valid derivations, inspection binds the exact runtime, absence prose
names the requested identity, label members use their semantic rules, unknown
manager-prefixed labels refuse, and mount spellings are canonical. The prior
39-case OCI module passes.

**Observed [P1]:** the required assignment-owned mount allowlist is still
absent. The adapter accepts `/srv/repositories/baton/.git` because it is not
under one of `_FORBIDDEN`'s system prefixes. Nothing in `run_vector` or
`OciAdapter` receives the assignment's permitted input/workspace roots, so the
boundary cannot distinguish a legitimate assignment mount from repository or
other-worker state. The additive
`test_a_repository_outside_assignment_owned_roots_is_not_mountable` fails.

**Observed:** resolved image/profile/policy/adapter identity is still not bound
as one input to argv and reconciliation labels; the constructor receives only
the image digest and accepts caller-supplied labels independently. The
receiving inventory/probes and the dossier-required isolated Docker cleanup
smoke plus compatible Podman coverage also remain absent, as PROGRESS states.

Review: `review-2026-08-25T00-19-47Z.md`.

## Assignment-root API ruling requested — 2026-08-25

**Confirmed:** adding `/srv/repositories` or `.git` to `_FORBIDDEN` would make
one regression pass while preserving the denylist defect. A mount is admissible
only because its canonical source equals or is segment-wise contained by a
root owned by this assignment, not because its spelling avoided known system
prefixes.

**Proposed for approval:** `run_vector` and `OciAdapter` require the exact
`assignment_workspace` root record plus a closed posture. The record has
exactly `inputs`, `workspace`, and `git`; `git` is manager-private and never
mountable. Consent permits no assignment-root mounts. Execution permits the
`inputs` root or its descendants read-only and the `workspace` root or its
descendants with the requested writability; a writable inputs mount refuses.
`_FORBIDDEN` is removed once this positive proof owns the question. Roots alone
are insufficient because they cannot select consent versus execution topology.

The approver must confirm this public contract change before implementation.

## Confirmed assignment-root API — 2026-08-25

The proposed positive authority model is approved. `run_vector` and
`OciAdapter` require both a closed `posture` and one exact
`assignment_roots` record containing exactly `inputs`, `workspace`, and `git`.
Roots alone never select posture.

Consent permits no assignment-root mount. Execution permits the canonical
inputs root or a segment-wise descendant only read-only, and the canonical
workspace root or a segment-wise descendant with the explicitly requested
read/write mode. The private git root is never mountable. Writable inputs,
foreign or other-assignment roots, ambiguous/overlapping roots, and nested or
overlapping source/target spellings refuse. `_FORBIDDEN` is removed when this
positive ownership proof lands; path admissibility is never inferred from
avoiding a list of known-bad prefixes.

This ruling does not close the other review corrections: resolved
image/profile/policy/adapter identity, receiving inventory/probes, isolated
Docker cleanup evidence, and compatible Podman coverage remain required.

## Assignment-root implementation re-review — 2026-08-25

Disposition: **changes requested**. The denylist is removed and the required
root/posture API corrects the original repository, host, socket, private-Git,
writable-input and consent cases. The positive proof remains incomplete:
lexical `normpath` containment accepts a symlink descendant resolving outside
the assignment, overlapping roots are accepted, and nested source/target
mounts are accepted despite the explicit ruling. Three additive methods
produce four focused failures; the prior 45 cases pass.

Resolved image/profile/policy/adapter identity remains split, the inventory
currently has 20 unowned and 17 owned-but-unprobed OCI entries, and isolated
Docker/Podman evidence remains absent. Review:
`review-2026-08-25T03-01-06Z.md`.

## Independent correction re-review — 2026-08-25

Disposition: **changes requested**.  The prior 56 OCI unit methods remain
green and the assignment-root/inventory correction is materially improved.
Three acceptance boundaries remain open.  Positive-absence prose can combine
an absence sentence for one runtime with the requested identity elsewhere in
stderr and report the requested runtime dead.  The resolved identity omits the
confirmed policy digest, and restart reconciliation never compares the
running image with the adapter's resolved image.  The engine cleanup proof
filters names by `baton-w6632-engine`, although that marker exists only in a
label and no generated container name contains it; failed cleanup queries also
pass as empty results.

Five additive review methods make these gaps durable.  Review:
`review-2026-08-25T15-07-37Z.md`.

## Implementation decision — 2026-08-25: the runtime labels carry the policy

Recorded by the implementer under the claim that answered
`review-2026-08-25T15-07-37Z.md`. It SUPERSEDES nothing: the confirmed record
has said image/profile/policy/adapter throughout, and the three-digest
`RESOLVED_IDENTITY` that preceded this was the narrowing the review names.

**The resolved identity is four digests again**, and the case that counts them
now asserts the member tuple rather than a number in its own name.

**The image half is the ENGINE'S fact, not a label.** A restart proves the
running image by reading it from the listing — Docker answers `Image`, which is
the `sha256:` reference because this adapter always starts by digest; Podman
answers `ImageID` as well and it is asked for first. Measured against a real
Docker 29.1.3 daemon rather than assumed, and the measurement is in
`evidence/gate-after-fifth-correction-2026-08-25.txt`. A listing that names no
image, or names a tag, is refused: a tag is a pointer that was true when
somebody last pushed, and the comparison this feeds decides whether a restarted
manager adopts a running worker.

**The policy half has no engine fact, so `runtime.labels` carries it.**
`documents.CONTRACTS["runtime.labels"]` gains `policy_digest`. This is the
SECOND time this build has extended those labels past the frozen Node host's
set, and it is the same argument that added `participant`: reconciliation
decides by comparing labels, so a member of the resolved identity the engine
cannot report is one that does not survive a restart at all. The frozen
worker-control schema does not define this document — it is this build's own
contract table — so extending it is within this distribution's authority rather
than a change to a frozen artefact.

**The lifecycle consequence, named because it reaches past this Job.**
`attempts.policy_digest` is nullable, so an attempt recorded without one can no
longer start a runtime. `attempts._runtime_labels` refuses it explicitly, with a
message naming the missing policy digest, rather than letting it surface as a
digest complaint about `None` from inside the label constructor. The refusal is
the right answer — a delivery whose policy this manager cannot name is one no
later reconciliation can describe — but *when `request_runtime_start` refuses*
is a lifecycle rule owned by W5/W6636 rather than by this adapter core. It is
implemented here because the label member is useless without it, and it is
flagged for the reviewer to confirm or reroute rather than left implicit.

Five test modules carried fixtures that record an attempt or build runtime
labels without a policy digest — `test_attempts`, `test_sessions`,
`test_boundary_inventory`, `test_oci` and `test_oci_engine`. Each is updated to
record one. None of their assertions is weakened; what changed is that their
fixtures now satisfy an extended contract.

## Independent fifth re-review — 2026-08-26

Disposition: **changes requested**. The prior five review regressions are
corrected, but exact engine filters on the resolved profile/policy/adapter
labels hide a stale same-attempt runtime before the new comparison can see it.
`start` consequently reaches `run` instead of refusing the duplicate. Candidate
discovery must use stable attempt/assignment identity and compare the full
resolved identity only after rows return.

A second focused defect remains in target canonicalization: `_mounts` calls
`normpath` before looking for `..`, so `/workspace/../etc` is accepted and
emitted as a writable `/etc` bind. The raw spelling must be checked before
normalization.

Two additive regressions and the complete analysis are in
`review-2026-08-26T00-03-30Z.md`. The older test requiring every label to be an
engine filter is explicitly superseded as an unsafe expectation; complete
label/image comparison remains required after broader candidate enumeration.

The missing-policy lifecycle precondition is not separately blocked by this
review. It follows from the confirmed policy label, while W6636 remains
responsible for revalidating where lifecycle surfaces that refusal.

## Independent sixth-review findings — 2026-08-26

**Observed, P0.** `list_vector` filtered on all eight runtime labels,
including the three resolved-identity digests. A real engine applies every
filter before returning a row, so a runtime from this exact attempt under an
OLD policy never appeared in stdout, never reached the identity comparison, and
`start` read the empty candidate set as "nothing exists" and created a second
runtime for one attempt.

**Observed, P1.** `_mounts` normalized the target before testing for `..` as a
segment, so the test could never see traversal normalization had consumed. A
workspace requested at `/workspace/../etc` was emitted as `target=/etc`, moving
the assignment's writable bind over the image filesystem.

Full analysis in `review-2026-08-26T00-03-30Z.md`, which also gives explicit
case-specific confirmation to revise `test_the_listing_filters_on_every_label`.

## Implementation decision — 2026-08-26: discovery is broader than comparison

Recorded by the implementer under the claim that answered the sixth review.

**The candidate query and the identity comparison are two different questions,
and asking the engine both was the defect.** The engine answers which runtimes
belong to this ATTEMPT — the attempt id and the four parts of the assignment.
This adapter decides, in process, whether each candidate is this delivery's:
the three labelled digests and the engine-reported image. A stale candidate is
then REFUSED rather than filtered away, which is what this module's own
docstring has claimed from the start — "it is not absent, it is WRONG, and
dropping it leaves a mislabelled runtime running" — and which was true of
everything except the query that finds the runtime.

`_CANDIDATE_LABELS` is DERIVED from the frozen label set minus the resolved
identity rather than listed, so a label added to the contract tomorrow becomes
a selector or a comparison by which list it belongs to rather than by somebody
remembering this site.

**Narrowing the filters did not narrow the ownership.** `list_vector` still
owns the whole label set before the engine is asked anything; only which of
those proved values become filters changed.

**The target's spelling is checked before `normpath` can erase it**, the rule
`_canonical` already followed for a host source. The source/target asymmetry is
unchanged and still stated at the site: a source is a host path the engine will
resolve, so it is resolved here; a target is a path inside a container that
does not exist yet, so it is normalized as text and never resolved against this
host.

## Independent sixth re-review — 2026-08-26

Disposition: **changes requested**. The resolved-digest and traversal
corrections are present, but candidate discovery still pre-compares four
assignment labels in the engine. A runtime carrying the requested attempt id
and a contradictory generation is consequently hidden as an empty result, and
`start` creates a second runtime instead of refusing before the side effect.

The other half of the same defect is post-read validation: `OciAdapter.list`
compares the engine-reported image and the three digest labels, but never
compares a returned candidate's attempt/authority/work/participant/generation
labels with the request. Engine-side filters are selection hints, not proof of
the returned record. A returned runtime with a contradictory generation is
currently adopted.

The complete P0 analysis and two additive regressions are in
`review-2026-08-26T02-14-24Z.md`. Candidate enumeration must be broad enough
that an assignment-label contradiction reaches the adapter, and the complete
returned label record must be compared in process before either adoption or an
empty-set decision permits `run`.

## Independent seventh-review finding — 2026-08-26

**Observed, P0.** The previous correction moved the three resolved digests out
of the engine filters and stopped there, leaving the attempt id, the four parts
of the assignment and the generation as exact filters. A runtime carrying this
exact attempt id under a stale generation is therefore still hidden by the
engine, `start` reads absence, and it creates the duplicate. The post-read half
was incomplete in the same way: `list` compared only the engine image and the
three digests, never the assignment values it had asked for. Analysis in
`review-2026-08-26T02-14-24Z.md`, which also gives explicit confirmation to
revise the selector assertion a second time.

## Implementation decision — 2026-08-26: the minimal ownership key

Recorded by the implementer under the claim that answered the seventh review.

**The general rule, which is what the previous correction was missing.** ANY
assignment fact used as an engine filter hides a runtime that contradicts it,
and a contradictory runtime is exactly what this adapter exists to refuse. It
was never about digests specifically, and it was not about generation either.

**So the selector is the minimal ownership key**: `runtime_attempt_id` alone —
the one label that answers "is this runtime this attempt's" and cannot disagree
without meaning a different attempt entirely. Everything else is compared in
process against the record that was asked for, member by member across the
whole frozen label set.

**Two comparisons, answering two questions.** The whole-record loop asks
whether a candidate is the runtime the CALLER named; the resolved-identity loop
asks whether it is the one THIS ADAPTER resolved. `list` is reachable without
`start`, so neither implies the other and both are kept. The engine-image
comparison and the ambiguity behaviour are untouched.

## Independent seventh-correction review — 2026-08-26

**Confirmed:** the minimal-selector correction closes the remaining P0.
Engine discovery filters only on `runtime_attempt_id`; every other member of
the complete returned label record is compared with the request in process
before adoption or create. The independent engine-image and
profile/policy/adapter resolved-identity comparisons remain intact.

The focused OCI gate is 74/74 and source/build mirrors agree. The returned
real-Docker evidence exercises the duplicate-start selector against Docker
29.1.3; this managed reviewer cannot access the Docker socket, so its same
module skips under the record's explicit availability rule. **Signed off; no
W6632 finding remains.** Full review:
`review-2026-08-26T03-38-48Z.md`.

## 2026-08-28 — fixed-user clarification for workspace authority

Approver response M34630 under W33936 preserves this record's fixed primary
runtime identity exactly: `--user 65532:65532` does not change. An execution
container may additionally receive one explicit deployment-configured,
nonzero, non-authority workspace group through supplementary `--group-add`,
after the adapter proves its canonical workspace root carries that exact
group. Consent receives no such group, and an arbitrary manager/filesystem gid
is never inherited. This clarifies the fixed-user boundary; it does not
supersede the image/adapter primary identity or any mount-authority ruling.
