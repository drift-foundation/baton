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
