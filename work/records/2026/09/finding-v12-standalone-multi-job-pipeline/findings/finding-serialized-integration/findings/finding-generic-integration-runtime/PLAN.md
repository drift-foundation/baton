# Plan

1. [complete 2026-09-06] Revalidate the accepted coordinator, generic Worker
   Manager lifecycle and file-based exchange contracts. Three inherited
   assumptions were corrected against the tree and are recorded in FINDING.md;
   the material one is that agent quiescence is not runtime quiescence, so the
   prior-runtime proof reads the manager's execution-runtime axis rather than a
   session fact.
2. [corrections accepted at second review 2026-09-06] Define the narrow integration runtime boundary, with
   K as the sole owner of every shared interface and schema: the profile, the
   assignment, the result and the hold, each owned where it is read as well as
   where it is built. Bind the assignment's attempt to the live grant, source
   quiescence/absence from the exact durable Worker Manager runtime, and bind
   the runtime profile kind to the accepted entry's profile kind in the same
   coordinator relationship proof.
3. [complete 2026-09-06; publication, custody and parent-root proofs all accepted at the third review] Implement the durable delivery -- an assignment
   namespace this manager writes and the runtime mounts read-only, and a result
   namespace the runtime writes and this manager reads as untrusted input --
   with the atomic publication, quiescence proof and live-grant-controlled
   target access, and no VCS vocabulary. Use the shared exchange mechanism's
   current unique-stage/whole-write/no-clobber publication invariants and its
   descriptor-relative mode/group custody proof. A name gate and two AST gates
   keep the vocabulary boundary true rather than promised.
4. [complete 2026-09-06; every enumerated regression of the first two reviews is present and passing] Add
   focused positive, refusal, stale-grant and restart-observation tests. Add the
   grant-attempt, durable quiescence/absence, stored profile-kind, short-write,
   umask, publication-race, stale-stage, symlink, mode and group regressions
   enumerated in `review-2026-09-06T12-55-42Z.md`. Add the integration-root
   symlink/type/mode cases and make the public manager-observation schema match
   its returned document, as required by `review-2026-09-06T13-13-54Z.md`.
5. [complete 2026-09-06; bounded independent sign-off with no findings in
   `review-2026-09-06T13-48-09Z.md`; no immutable proposal digest supplied]
   Re-run focused runtime/coordinator gates after the corrections and obtain a
   new independent implementation review over a stable, digest-bound candidate.

   `review-2026-09-06T12-55-42Z.md` found three [P0]s and two [P1]s. The
   prior-runtime witness is no longer a caller document: the predecessor comes
   from the coordinator's own lease history and its runtime state from
   `attempts.attempt_runtime_of`. The assignment's attempt is the grant's and
   the runtime profile kind must equal the accepted entry's, both out of one
   new `granted_context` relationship pass that `live_grant` is now a
   projection of. Publication carries the CURRENT `exchange.py` invariants
   rather than its superseded shape, and adoption proves both namespaces on
   no-follow descriptors at exact modes with the result namespace's group
   checked against the manager-minted `WorkspaceGroup`.

   `review-2026-09-06T13-13-54Z.md` accepted those and found two [P1]s and a
   [P2], all corrected. Adoption now proves the manager-created delivery ROOT
   as well -- `O_NOFOLLOW` binds only a path's final component, so an
   intermediate `integration` symlink was followed -- and opens both namespaces
   relative to that root's descriptor, at a mode established with `chmod`
   rather than requested through `makedirs`. The superseded caller-witness
   tuple is gone: `OBSERVED_RUNTIME_MEMBERS` is exactly what
   `prior_runtime_witness` returns and a case asserts that equality. The
   publication docstring and the module header describe the mechanism actually
   reviewed.

This leaf composes the assignment and its delivery; it does not START a
runtime. That is W101492's, which this Work blocks, and the boundary is shaped
so that leaf composes rather than widens it: a published assignment is a
document at a fixed read-only target with a digest, and a result is read back
through one closed reader.

Not implemented here, by scope: candidate admission, target mutation, any
version-control operation, the Authority receipt, and every form of automatic
recovery. Under the owner ruling of 2026-09-06 an interruption or an ambiguity
produces a closed hold account this module composes and does not apply.
