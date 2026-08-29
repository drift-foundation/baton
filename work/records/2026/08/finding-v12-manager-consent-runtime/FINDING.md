# Manager-owned consent runtime lifecycle

Date: 2026-08-27
Parent discovery: W6636, `work/records/2026/08/finding-v12-local-oci-lifecycle-composition/`

## Finding

**Observed:** W6636's diagnostic lifecycle test drives the consent runtime directly; no production manager operation currently owns its creation, durable association, and teardown as one lifecycle.

**Confirmed:** Without that composition seam the manager cannot certify that consent executes without an execution workspace, that consent resources are positively absent before execution creation, or that decline, refusal, and cancellation converge safely. W6636's approver authorized a separate correction Work.

**Confirmed boundary:** This Work owns the production manager operation that creates, records, observes, and removes the consent runtime before permitting execution-runtime creation. It does not absorb output custody, credentials, the full shared settlement crossing, restart adoption, or W6636's complete lifecycle matrix.

**Proposed:** Use stable operation identities and recorded receipts so retries are effectively once. Treat positive absence of consent runtime resources as a prerequisite to execution creation.

## Acceptance

- A production manager entry point owns consent-runtime create, record, observe, and teardown.
- Consent starts without an execution workspace or execution credential mount.
- Approve transitions only after positive consent-runtime absence; decline, refusal, cancellation, retry, and crash boundaries converge without execution creation.
- Stable identities and receipts prevent duplicate consent effects across retry.
- Focused unit, failure-injection, mutation, and real-engine tests cover positive and negative paths.

## Open

- Exact operation placement and durable receipt schema must be revalidated against current manager persistence and attempt orchestration.

## Superseded decision — 2026-08-27

The separate consent-runtime topology, positive-absence gate, and acceptance
criteria above are superseded before implementation. They remain here as the
chronological explanation for W26295, not as a compatibility requirement.

The approved lifecycle is reservation, canonical claim, then one execution
runtime. The trusted adapter reserves an eligible slot without launching an
agent or container; the Worker Manager atomically claims; only success launches
the execution container. Expiry or a lost claim race releases the reservation
without a runtime. The executing agent may still refuse through typed
`plan-rejected` or `unsupported` results after claim.

Dispatch explicitly authorizes the claimed runtime to receive the Work's exact
declared repository or other source through read-only `/input`. It does not
authorize access to the Baton authority store, integration credentials,
unrelated host paths, or a writable canonical checkout.

W26295 therefore has no implementation remaining and should close cancelled as
superseded. W6636 owns the direct claim-to-execution crossing and the typed
launch-failure/recovery behavior; it must not retain a consent-runtime axis.
