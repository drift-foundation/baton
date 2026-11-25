# Exact import — `.dockerignore` build-context correction

Author: baton.prompt (K, model Fable 5.2), no claim. 2026-11-25 UTC.
Coordination M386077. Accepting review: `review-2026-11-25T01-12-48Z.md`.

- One path, `v12/.dockerignore`, one added line
  `!python/src/baton_v12/provider_policy`.
- Preflight: HEAD `ad6dcad0aa38f8ccc17fd6a50bd92bf6f2d8c402`; index empty;
  target clean against HEAD; before-hash `b7da7ead…`; anchor present once;
  line absent. Written; after-hash `04e364e4…`, the hash recorded for the
  build of image `46a46ee4…`; mode kept. `import.json`.
- Nothing else written. The W386057 isolation paths stay separate and are
  not in the checkpoint. No test run, build or engine operation.
- Checkpoint: `owner-checkpoint.py` here, copy
  `/tmp/baton-w385830-dockerignore-checkpoint.py`; `--check` changes
  nothing. Message: `Allow provider_policy into the worker image build context`.
