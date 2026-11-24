# Accepted import and human checkpoint — W385853 instruction delivery

## 2026-11-24 — exact-byte host import of candidate 6580545d verified

By baton.prompt (K), on the owner's selection; no claim, no Git mutation.

- Accepted by independent delta review M386046,
  `review-2026-11-24T22-43-47Z.md` (`261ef905…`), for the selected
  implementation/review delivery scope only.
- Candidate `sha256:6580545d6cb0c9673e9baf4dce3699b41813024654da1af5386e85dcbe59d440`,
  12 paths, archive `5abb5d90…`, from `evidence/correction-prompt-386042/`.
- **Preflight** (`preflight.json`), whole path set before any write: identity
  recomputed; accepting review digest and candidate name checked; HEAD equals
  the reviewed base `317351e73c92749e201f536ba115c9fdf213077d`; index empty;
  each of the 11 existing targets is an owner-writable regular file whose
  bytes equal the base blob (no target drift); the one new target was absent;
  no symlinked parent. Zero refusals. `v12/DESIGN.md` equals the candidate's
  context copy; it is not an imported path.
- **Import** (`import-reviewed.py`): 12 exact reviewed files written; existing
  modes preserved; the new file `provider_policy/worker_instructions.md` is
  0644. **Postflight** (`postflight.json`): final bytes and modes verified; no
  other path under `v12/` changed.
- **Host validation** on the imported bytes: prepared interpreter,
  `just test-one`, eight modules, **503 collected / executed / passed**, zero
  failures, errors, skips, duplicates or unaccounted ids, 68.8 s, source
  identity stable (`integration.*`). Groups manager-pure, tools-pure. No
  group, packaged or full-suite run. No build, image, engine, credential or
  provider.

## Not covered by this acceptance

- F1 and F2 (provider-selected integration turn refused; `invoke_provider`
  prepares the home before binding the launch) are open and tracked as
  **W386048**. Not fixed, not waived.
- No vendor-loading, model-visibility, image or native qualification claim.
- Codex credential path, N4b, conversation resume: untouched and gated.

## Human checkpoint

`owner-checkpoint.py` (copy at `/tmp/baton-w385853-checkpoint.py`) verifies
HEAD, an empty index and every byte it names, then stages exactly the 12
reviewed paths and this dossier and commits. `--check` verifies only.
The unrelated working-tree change to `v12/DESIGN.md` and every other dossier
stay unstaged. No push.

Commit message:
`Deliver native worker instructions and execution-context label under provider selection`

After the commit: record its identity here in PLAN, then give codexpc that
commit as the base of the N4a shared-file join.
