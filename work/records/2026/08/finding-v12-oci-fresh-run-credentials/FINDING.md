# OCI fresh-run credential delivery provider

Date: 2026-08-27
Parent discovery: W6636, `work/records/2026/08/finding-v12-local-oci-lifecycle-composition/`
Upstream implementation history: W6634, `work/records/2026/08/finding-v12-sealed-output-credentials/`

## Finding

**Confirmed:** W6636's diagnostic lifecycle review found that W6634's shared output/credential implementation remains provisional and cannot be used as the certification boundary for local OCI lifecycle composition. The W6636 approver ruling authorizes a separate provider Work for fresh-run credential delivery.

**Confirmed:** Assignment logical credential slots resolve through a trusted profile provider to opaque references. Bearer bytes must be registered as live before any materialization, written as mode-0600 files beneath an assignment-private mode-0700 volatile root, and mounted read-only at the fixed worker path `/run/baton/credentials`.

**Confirmed:** Bearer bytes must never appear in argv, environment, labels, durable records, diagnostics, or worker output. The live-secret registry remains armed through worker quiescence, output scanning, container removal, and credential-root deletion, and it forgets a bearer only after positive absence is established.

**Confirmed boundary:** This Work owns fresh-run delivery only. Output custody, the shared quiescence/removal/settlement crossing, restart adoption, recovery, reconciliation, and orphan convergence remain outside it and are owned by W6636 or its other providers.

**Proposed implementation boundary:** Revalidate the W6634 spike against the current manager and adapter contracts, then adopt only the portions that meet this finding. Provisional code is evidence, not accepted implementation.

## Acceptance

- Logical slots resolve without placing bearer material in assignment or runtime metadata.
- Fresh-run credential files and roots have the required permissions and fixed read-only mount semantics.
- Failure at every materialization/start boundary preserves live-secret tracking and converges to positive absence before forgetting.
- Tests prove secrets are absent from argv, environment, labels, durable documents, diagnostics, and output.
- Focused unit, mutation, failure-injection, and real-engine tests cover delivery and cleanup.

## Open

- Exact provider interface and volatile-root owner must be revalidated against the current v12 manager tree before implementation.
