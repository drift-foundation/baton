# Plan: deliver assignment identity to the artifact-neutral worker

1. [approved 2026-08-26] Materialize the existing complete
   `assignmentManifest` at fixed read-only `/input/assignment.json`, alongside
   unchanged pre-claim `/input/input.json`. The manager adds the assignment
   document after claim and before execution mount; no container observes that
   transition, and the completed input surface is then read-only. Reject all
   environment, frame and compatibility aliases.
2. [done 2026-08-26] Supersede the conflicting W14251 and W6633 text explicitly
   while preserving chronological history. Both records now point here and
   distinguish the old observation from the approved resolution.
3. [done 2026-08-26] Align the schema copies, normative specification,
   contract model, vectors and conformance obligations. No frozen schema copy
   changed and none should have: `assignmentManifest` was already frozen, and
   this ruling adds a path and a lifecycle rather than a document. Delivered:
   the reserved second input name and the two-document pair rule in the shipped
   validator and the record's executable model, a canonical assignment vector
   plus a new `input_pairs` vector section, the §7.0/§7.1/§8.1/§8.2/§8.7
   rewrites and §12 rules 3 and 16, and obligations A-17/A-18 with nine cases
   (register 79, matrix 132).
4. [done 2026-08-26] Align manager launch/composition, worker-entry
   validation, completion publication and W6634 receipt validation.
   `workspaces.compose_input_root` materializes both documents in the ruled
   order, validating the pair before anything is written; the worker reads
   `/input/assignment.json`, holds the pair before agent dispatch, and copies
   the identity into the envelope; W6634's receipt comparison needed no change
   and now has a satisfiable other side.
5. [done 2026-08-26] Add positive exact-binding and negative missing/stale/
   session/generation cases across direct and built-image paths; run all
   contract and focused manager gates and return for independent review. The
   daemon-backed suite had never delivered an input root at all, so the built
   image had never been asked to do the work it is for; it now runs the real
   two-root delivery and is green.

Item 3 includes reserving
`assignment.json` in the input root, adding a canonical assignment-manifest
vector, and extending runtime conformance with missing, malformed, wrong-input,
wrong-work, stale-generation, wrong-attempt, and consent-visibility cases.

## Independent-review correction — 2026-08-27

The `[done]` labels above record the first implementation claim; they are
superseded for current scheduling by these changes-requested items:

6. [changes requested] At the real worker-entry boundary, validate both
   complete documents as closed, self-digest-bound manifests before comparing
   their pair bindings or dispatching the agent. Keep the four additive direct
   regressions for false self-digests and extra members, and add equivalent
   built-image coverage.
7. [changes requested] Give the manager's pre-mount composition/launch
   boundary the manager-owned expected assignment and runtime-attempt identity.
   Refuse a stale generation, another participant/Work or another runtime
   attempt before writing/exposing the execution input root. Wire that
   boundary into the production launch path; an uncalled helper is not the
   approved lifecycle delivery.
8. [changes requested] Move or add conformance cases for stale generation and
   wrong runtime attempt at the pre-mount/pre-dispatch boundary. The existing
   `output.freeze` cases remain useful completion/custody defense but cannot be
   the only proof of the earlier lifecycle rule.
9. [changes requested] Repair the mutation/evidence gate so restoration also
   invalidates matching bytecode, then capture one internally consistent
   transcript from the ordinary direct-worker command. Re-run the daemon-backed
   built-image suite where Docker is authorized; independent review could not
   reach the daemon.

6. [done 2026-08-27] Answer the independent review of 2026-08-27T00:40:45Z.
   The worker validates both delivered documents against closed member sets
   derived from the frozen contract, which now travels with the image as a
   fifth byte-identical copy; `compose_input_root` and the launch path hold the
   root to the manager's own assignment, runtime attempt and claimed input
   digest before anything is exposed; conformance certifies that identity
   before mount as well as before custody (matrix 135, SPEC 12 rule 17); and
   the direct gate can no longer execute stale bytecode.

## Second independent-review correction — 2026-08-27

10. [changes requested] Close the final authorization-to-mount seam. The
    exact root accepted by `authorize_input_root` must be the source the
    execution adapter exposes read-only at fixed `/input`; no independent
    mount plan, missing input mount or alternate target may survive. Refuse
    disagreement before journalling `runtime.start` or invoking the adapter.
    Preserve the additive cross-component regression in
    `test_attempts.py`, and add a production-OCI vector/integration case that
    proves the authenticated source and fixed target reach the engine argv.

7. [done 2026-08-27] Answer the second independent review. The root the manager
   authorizes is the root the runtime mounts: the adapter's declared plan is
   held to it before the start is journalled, the authenticated source crosses
   the seam and the adapter requires exactly that source read-only at the fixed
   `/input`, absence is decided rather than passed through, and an OCI vector
   case reads the engine's own argv. Conformance matrix 136; SPEC 12 rule 17
   extended.

## Third independent-review correction — 2026-08-27

11. [changes requested] Make the pre-journal declared-plan check enforce the
    same canonical source and target spelling the OCI boundary enforces,
    before normalization or resolution can erase `..`. Preserve the two
    additive source/target traversal regressions. The exact root, fixed target
    and early refusal are one rule; the manager must not journal a plan the
    adapter will necessarily refuse as noncanonical.

8. [done 2026-08-27] Answer the third independent review. The mount-spelling
   rule is `oci.canonical_target` beside `canonical_source`, called by
   `_mounts`, the adapter's authorized-root check and the manager's pre-journal
   check, so the earlier moment and the boundary cannot drift apart. Both
   reviewer regressions preserved.

12. [signed off 2026-08-27] Fourth independent review confirmed every
    accumulated W19784 regression and focused contract/manager gate. No open
    W19784 finding remains. The two direct-worker failures belong to W6633 and
    remain with that Work; they do not prevent this assignment-identity
    blocker from closing and unblocking W6633.
