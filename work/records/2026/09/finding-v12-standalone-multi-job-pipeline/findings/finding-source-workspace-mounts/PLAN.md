# Plan

0. [ready after W81115 closed satisfying 2026-09-03]
   Submit this accepted scope as the first ordinary self-hosted Job through
   the integrated persistent v12 manager; do not use dogfood or a new complete
   candidate archive.
1. [pending revalidation] Re-read W62098's latest source/workspace rulings and
   map current workspace allocation, OCI mounts, dogfood staging, and profile
   inputs. Preserve W62535's preflight-before-staging ordering invariant.
2. [pending] Define a generic nominated-source and manager-created persistent
   workspace capability with explicit storage quota and bounded scratch.
3. [pending] Implement direct read-only local source mounting and disk-backed
   writable workspace mounting without manager Git knowledge or a mandatory
   source walk/copy/hash step.
4. [pending] Add a Git-aware profile that names/verifies an immutable base and
   clones copy-safely inside the workspace, plus one non-Git fixture using the
   same generic mount boundary.
5. [pending] Retire ordinary copied/tmpfs Git staging after the replacement
   launches the same useful assignment; preserve explicit generic snapshots.
6. [pending] Prove source immutability, containment/replacement refusal,
   >64 MiB disk-backed work, quota/scratch behavior, restart adoption, and no
   manager Git/source-enumeration operation.
7. [pending independent review] Bind the immutable proposal and enumerate all
   changed test paths before integration.

Do not add review-cycle or scheduler policy to this leaf.
