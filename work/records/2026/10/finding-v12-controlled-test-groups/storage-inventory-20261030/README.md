# Storage inventory — 2026-10-30

Snapshot of untracked, non-ignored paths, excluding this inventory itself.
`untracked.tsv` records every path, size and conservative disposition. It is
an inventory, not independent acceptance or a staging/deletion allowlist.
Concurrent changes can make this snapshot stale.

- convenience-symlink: 1 files
- preserve-dossier-pending-artifact-review: 8777 files
- preserve-source-tests-docs: 13 files

All twelve previously untracked v12 source/test files must be preserved with
the changes that use them. Historical dossiers remain preserved pending
artifact-specific review: archives, databases and candidate trees cannot be
classified as disposable by suffix or location alone. No files were removed.
No external artifact backup was made or verified in this pass.

Existing ignores already cover Python caches, virtual environments, Node
modules, packaging builds and wheelhouse output. `work/scratch/` remains the
explicit disk-backed disposable scratch location. No broader ignore was added.

Before staging dossier artifacts, review candidate contents for credentials,
required references and duplication, and select Git or a verified durable
external store as appropriate. This snapshot does not claim that all 8,000+
artifacts have received that content review. Keep them intact meanwhile.
