# Finding: retire v10 deployments, configuration, and mailbox data

## Context

Child of W99. Once v11-only operation is certified, remove the deployed v10 executables/aliases, readiness processes, configuration references, and mailbox data selected by Slawomir's explicit inventory approval. This is the destructive operational track; filing it does not authorize deletion.

## Boundary

- Enumerate exact processes and filesystem targets before mutation.
- Stop and verify every v10 consumer before touching data.
- Leave no alias, service, monitor, or configuration that can restart v10.
- Report what was removed and whether recovery is possible; never broaden a failed cleanup.

