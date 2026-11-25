# Exact-byte import — N4a join candidate e9e9c84f

Author: baton.prompt (K, model Fable 5.2), interactive copilot, no claim.
2026-11-25 UTC. Coordination M386064 (T385830) before the first write.

- Candidate: `sha256:e9e9c84f39ddaf2cd7aa4f358d68682dd27eb45bf51e04eef4cb5dc3b465657f`,
  17 paths (8 existing, 9 new), archive `713112419c0e…`, from
  `evidence/n4a-join-386051/`. Accepting review:
  `review-2026-11-24T23-40-10Z.md` (`d38fa34d…`), M386056.
- Base and drift: HEAD `ac034bc1c9fae525b94a1a5f21d9721c677dc39e` equals the
  manifest base; index empty; `git status --porcelain` over the 17 paths
  empty before the write; each existing target equalled the manifest
  `base_sha256`; each new target was absent; no symlinked parent.
  `preflight.json`, 0 refusals.
- Written: the 17 files, byte-for-byte from the archive; existing modes
  kept, new files 0644, none executable. `postflight.json`: every hash
  equal, no unexpected path under `v12/`.
- Kept separate: the five W386057 isolation paths (candidate `53ddec2b…`)
  were already edited in the tree. They do not overlap the 17 paths, were
  hashed before and after the import and are unchanged, and are not in the
  checkpoint.
- Validation: no test was run in the protected tree, because it now also
  holds the isolation edits. The 17 imported files are byte-identical to
  the tree that passed 1008/1008 in my review run outside the checkout
  (`evidence/review-K-386054/`). No build, engine, credential or provider
  operation.
- Checkpoint: `owner-checkpoint.py` here, copy `/tmp/baton-w385830-n4a-checkpoint.py`.
  `--check` changes nothing. It stages the 17 pinned product paths, both of
  my W385830 reviews and the N4a evidence directories (preparation, draft,
  join, review-K-386054, this import), refuses if anything else is staged,
  and commits. It does not stage FINDING/PLAN/PROGRESS (others are still
  appending), the isolation paths, the isolation dossier, or any other
  evidence directory.
- Proposed message: `Join deterministic Codex adapter, entry and recipe candidate under provider selection (N4a)`.
- Not enabled by this import: Codex composition still refuses; J1, N4b,
  qualification and native use stay gated. W386048 and W386057 stay separate.
