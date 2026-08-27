# Reference-worker launch environment through OCI

Date: 2026-08-27
Parent discovery: W6636, `work/records/2026/08/finding-v12-local-oci-lifecycle-composition/`

## Finding

**Observed:** The reference worker image contract requires four non-secret launch values: `BATON_WORKER_POSTURE`, `BATON_WORKER_SESSION`, `BATON_WORKER_CONTRACT`, and `BATON_WORKER_ROLE`.

**Confirmed:** The current manager-to-OCI adapter start path does not deliver those values, so an adapter-started reference worker is not runnable under the declared contract. W6636's approver authorized a separate correction Work.

**Confirmed boundary:** This Work owns the exact manager/adapter seam for those four non-secret values and no credential-bearing environment. It does not change the reference worker implementation or absorb the broader W6636 lifecycle matrix.

**Proposed:** Represent the four values explicitly in the launch request, validate them before the engine call, and translate them into the OCI environment without broad arbitrary-environment pass-through.

## Acceptance

- The manager supplies exactly the four required `BATON_WORKER_*` values through the typed adapter contract.
- The OCI adapter starts the reference worker with those exact values.
- Missing, duplicate, malformed, or unexpected launch values fail before container execution.
- Credential or other secret material cannot enter this environment seam.
- A positive real-Docker regression replaces the current expected launch failure and proves the reference worker becomes runnable.

## Open

- Exact type placement and validation ownership must be revalidated against the current launch request and adapter modules.
