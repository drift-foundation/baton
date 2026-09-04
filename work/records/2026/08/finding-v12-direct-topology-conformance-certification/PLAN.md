# Plan

1. [done, reviewer revalidation 2026-09-04] Fix the certification target as
   the current deterministic W6636 reference Worker Manager/OCI composition on
   Docker, using `v12/worker/Dockerfile` and `ScriptedAgent`. Exclude the
   production Job Manager/single-worker/Claude profile and Podman.
2. [pending independent review] Approve or correct the proposed parallel 1.1
   transition in `FINDING.md`. Frozen Worker Control 1.0 and Agent Session 1.0
   require consent axes, so no conformance-only edit may proceed while those
   contracts retain precedence.
3. [blocked on approved item 2] Preserve every 1.0 artifact byte-for-byte and
   add parallel Worker Control 1.1 and Agent Session 1.1 specs, schemas, models,
   traces and runtime schema copies. Express reservation-without-runtime,
   no-runtime decline/expiry/lost-claim endings and one post-claim execution
   session/container without weakening any unrelated closed vocabulary.
4. [blocked on item 3] Add Worker Conformance 1.1. Append dated supersessions
   in the owning `FINDING.md` and `SPEC.md`; revise `A-17`, `C-01` and `H-03`;
   replace only the three retired consent-topology case identities with
   `A-preclaim-has-no-input-delivery`, `C-preclaim-creates-no-runtime` and
   `H-claim-opens-one-execution-session`; regenerate and seal the register and
   cases rather than hand-editing generated JSON.
5. [same implementation round] Run a bidirectional normative audit: every
   generated case maps to every cited obligation, every old consent fact and
   current-version identity is absent from 1.1, all unrelated obligations and
   cases retain byte-equivalent semantics, all tracked schema copies match
   their canonical owner, and exact current counts/digests are recorded rather
   than assumed.
6. [blocked on W32382 closing satisfying] Re-read W32382 and all its providers,
   especially W32577's now-discussed deadline decision, against the integrated
   tree. Refuse certification if the deadline ruling is not durably pinned or
   any required negative/race/ending/lane surface remains open.
7. [after items 3–6] Build a new W33755-owned black-box driver. Bind the exact
   Docker daemon version, resolved reference image digest, adapter-build and
   runtime/input/policy/session profile digests, 1.1 schemas, register, cases,
   fixture and scripted-agent program. Use a fresh run name and refuse any
   overwrite; import no W6 observation.
8. [certification run] Exercise every applicable local-OCI 1.1 core case from
   sealed evidence, including both input families and the complete negative,
   restart, retry, race, cancellation, quiescence, credential, output, intake,
   cleanup and sibling-preservation matrix. Required Docker capability fails
   or yields `unable`; it never skips or passes by absence.
9. [assessment and review] Have the frozen assessor derive every case outcome
   and the overall verdict. Independently recompute all document and evidence
   digests, case/register coverage and authority projections. Publish
   `certified` only with exactly one passing observation for every applicable
   case; otherwise publish `not-certified` with every failed, unable,
   conflicting or unobserved identity. Append independent review before any
   certification claim is consumed.

## Scheduling

- W32382 is the required implementation/certification provider. Its dependency
  must be live on the Baton graph before this Work leaves plan review and must
  remain until it closes satisfying.
- W71917, W85500 and W32391 are deliberately not dependencies: their
  production Claude, durable-exchange and Podman surfaces are outside the
  fixed reference-Docker target.
- Provider closure is a gate on implementation and proof, not permission to
  skip immediate independent review of this plan and its 1.1 contract proposal.
