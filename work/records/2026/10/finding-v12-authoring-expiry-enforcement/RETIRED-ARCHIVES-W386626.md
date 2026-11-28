# Retired verification-source archives (W386626 slice 2, follow-up history)

This dossier's Work (W333735) is closed. This note is follow-up history appended by W386626 (repository evidence
cleanup, slice 2; see `work/records/2026/11/finding-repository-evidence-cleanup/`). Nothing earlier in this dossier was
edited.

## What was retired from the repository tip

Three verification-source archives, 14,655,501 bytes in total:

| Path (relative to this dossier) | Bytes | SHA-256 |
| --- | ---: | --- |
| `candidate-333743/verification-source.tar.gz` | 4,883,961 | `da631d669e99c99b1721d9f39b19b3851601a4299bf4a40f69d66f8b6321e4c8` |
| `candidate-333964/verification-source.tar.gz` | 4,885,770 | `675c0d050b3ea5ce0de8f1fda6977c8d1b66bcad10af2f9869e2009167e7c882` |
| `candidate-333964-final/verification-source.tar.gz` | 4,885,770 | `675c0d050b3ea5ce0de8f1fda6977c8d1b66bcad10af2f9869e2009167e7c882` |

- **What they held:** the packets' exported verification sources. Their source was integrated at a9f4fa4d.
- **The last two are byte-identical:** one Git blob.
- **Kept in place:** every other file of each packet, including each packet's `MANIFEST.json`, which still records the
  archive's SHA-256, and its `README.md`.

## Where the bytes are

- **The last commit holding them:** `a121d3c8d156d62ab294b209c9222dc78d7fe38f`.
- **The durable backup:** `origin` (`refs/heads/main`). It was verified on 2026-11-28 by an independent clone of
  origin and a comparison of each blob's SHA-256 and mode.

## Restore

From the repository root:

```sh
git restore --source=a121d3c8d156d62ab294b209c9222dc78d7fe38f --worktree -- work/records/2026/10/finding-v12-authoring-expiry-enforcement/candidate-333743/verification-source.tar.gz work/records/2026/10/finding-v12-authoring-expiry-enforcement/candidate-333964/verification-source.tar.gz work/records/2026/10/finding-v12-authoring-expiry-enforcement/candidate-333964-final/verification-source.tar.gz
```

- **The restored files are untracked** at their original paths. To track them again, revert the retirement commit.
- **To check them:** `sha256sum` each file against the table above, or against the packet's own `MANIFEST.json`.
- **To extract elsewhere, without touching the working tree:**
  `git archive a121d3c8d156d62ab294b209c9222dc78d7fe38f -- <path> | tar -x -C <dir>`.
