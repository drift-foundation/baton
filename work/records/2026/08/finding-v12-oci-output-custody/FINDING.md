# OCI output custody provider

Date: 2026-08-27
Parent discovery: W6636, `work/records/2026/08/finding-v12-local-oci-lifecycle-composition/`
Upstream implementation history: W6634, `work/records/2026/08/finding-v12-sealed-output-credentials/`

## Finding

**Confirmed:** W6636's diagnostic lifecycle review found that W6634's shared output/credential implementation remains provisional and cannot be used as the certification boundary for local OCI lifecycle composition. The W6636 approver ruling authorizes a separate provider Work for manager-owned output custody.

**Confirmed:** This provider owns the fresh-run path from a quiescent worker's `/output/output.json` to a durable manager-owned result. It must:

- open the worker output through a bounded, no-follow, nonblocking regular-file read;
- validate the `completionManifest` and compare it exactly with the assignment and output declaration;
- derive the result digest from the bytes actually opened;
- stage each declared regular-file tree into manager custody under explicit size and entry limits;
- reject live-secret material while the live-secret registry is still armed;
- freeze the staged copy and atomically publish the manager-owned `resultManifest` as `sealed.json`; and
- make exact replay prove request and receipt before any read from transient worker storage.

**Confirmed:** W19784 remains the upstream owner of assignment identity. This Work consumes that identity; it does not redefine it.

**Confirmed boundary:** Credential delivery, the shared quiescence/removal/settlement crossing, restart adoption, reconciliation, and orphan convergence remain outside this provider. W6636 owns those cross-provider and restart concerns.

**Proposed implementation boundary:** Revalidate the W6634 spike against current contracts, then adopt only the portions that meet this finding. Provisional code is evidence, not accepted implementation.

## Acceptance

- A real OCI worker output is copied into manager custody only after exact manifest validation.
- Symlinks, non-regular files, path escape, oversize trees, duplicate or undeclared material, and live-secret bytes fail closed.
- The digest and sealed manifest describe the manager-custodied bytes, not a path later reopened from worker storage.
- Replay is idempotent and does not re-read transient output after a recorded receipt.
- Focused unit, mutation, and real-engine tests cover success, malformed output, bounds, races, replay, and secret scanning.

## Open

- Exact module and type placement must be revalidated against the current v12 manager tree before implementation.
