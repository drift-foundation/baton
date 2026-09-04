# Plan

0. [blocked on bounded production-runtime corrections]
   The first ordinary self-hosted attempt reached the real provider but exposed
   a worker-image Python-floor mismatch, verifier-created cache pollution, and
   loss of a durable faulted terminal after container exit. Retain that attempt
   only as diagnostic evidence. Retry from a fresh committed baseline after
   those generic runtime boundaries are independently corrected; do not import
   or manually promote the faulted proposal.
1. [pending revalidation] Re-read the current source/workspace rulings and
   map current workspace allocation, OCI mounts, dogfood staging, and profile
   inputs. Preserve the accepted preflight-before-staging ordering invariant.
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
