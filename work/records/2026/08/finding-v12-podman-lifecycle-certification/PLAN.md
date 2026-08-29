# Plan: Podman lifecycle certification

1. [done 2026-08-28, seq 32728] Parked by the Route handler until a real
   compatible Podman engine is available. Absence verified rather than
   assumed; see `PROGRESS.md`.
2. Record engine identity and revalidate the shared adapter contract.
3. Run the one-container lifecycle and applied-security inspection on Podman.
4. Resolve only genuine representation differences without changing the
   frozen lifecycle or security outcomes.
5. Run the full focused contract and return for independent certification.

## 2026-08-29 — environment revalidation required

1. [superseded premise] Podman is no longer wholly absent: W33936 retained a
   Podman 5.8.4 image plus partial ROOTFUL and failing ROOTLESS observations.
2. [required] Route handler revalidate the parked phase and whether privileged
   nested ROOTFUL Podman is a compatible certification environment.
3. [required] Retain exact commands, probe source and complete transcripts;
   account for all ROOTLESS failures/errors rather than extrapolating from one.
4. [required] Run the shared lifecycle and security matrix, including the
   configured supplementary-workspace-group cases, under meaningful
   manager-side permissions.
5. [decision if needed] Obtain an approver ruling before adding gid-map or
   user-namespace flags to the pinned launch vector.
