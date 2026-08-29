# Finding: certify the local OCI lifecycle on Podman

Later-pass M2 portability certification split from W6636 by the 2026-08-28
approver scheduling ruling. Canonical predecessor evidence:
`work/records/2026/08/finding-v12-local-oci-lifecycle-composition/`.

## Observed limitation

Podman is absent on the current host. W6636 correctly records one narrow
availability skip and does not reinterpret Docker evidence as Podman evidence.
This Work must remain parked until a real compatible Podman engine is
available; a simulation or Docker alias cannot satisfy it. Its reviewer
creator cannot set the implementer Route's phase, so the Route handler has
been notified to park it before pickup.

## Confirmed boundary

Run the same adapter contract and one-container lifecycle against Podman,
including private/default PID namespace representation, exact mounts and
sources, claim-before-launch, effectively-once start, quiescence, custody,
retention, force-removal, provider teardown, clean settlement and observed
absence. Engine-specific syntax may differ only where the adapter contract
already permits it; lifecycle vocabulary and security outcomes do not.

## Acceptance

- A real Podman daemon is identified and its version/environment recorded.
- The shared lifecycle suite runs without Docker substitution.
- Applied mount, network, privilege, capability, PID, rootfs and user state is
  inspected from Podman's answer.
- Cleanup proves exact positive absence and provider endings.
- Independent review distinguishes portable contract facts from
  engine-specific representations.

## 2026-08-29 — a real nested Podman exists, with one pass and one constraint

**Observed through W33936:** a retained provisioned image identifies Podman
5.8.4. ROOTFUL Podman inside a privileged outer Docker container ran one
applied-group/write/denial probe successfully. ROOTLESS Podman reached the
19-case configured-workspace-group class but ended with two failures and two
errors; the retained output shows one failure in which supplementary gid 8291
is applied while the bind-mounted workspace gid maps to 65534 and worker write
fails.

**Not certification:** ROOTFUL ran one probe rather than the shared lifecycle
or configured-group matrix, and the ROOTLESS transcript omits three of its four
failed/error details. The retained record also lacks exact build/run commands
and the source of the custom Podman probe. The prior "Podman absent" premise is
therefore stale, but the acceptance is not met.

**Open compatibility question:** the only ROOTFUL environment measured needs a
privileged outer container and executes the manager as root, which makes
manager-side permission denials and collection non-probative. ROOTLESS keeps
the manager unprivileged but needs an explicit gid mapping the current launch
vector does not compose. Revalidate which environment counts as compatible,
then run the complete shared contract there or obtain the necessary ruling.
