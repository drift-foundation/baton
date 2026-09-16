# Owner decision — application version and captured build identity

Work W183883, 2026-09-16. Recorded by baton.prompt.

## Confirmed conversation

Owner clarified that the bootstrap source is the repository containing the
development v12/justfile, not a source location to communicate in deployed JSON.
Owner then replaced the proposed arbitrary deployment label/commit version with
an application version file: "introduce a version.py or similar file so that
baton --version can show it".

Prompt proposed version.py as the authoritative version (example 12.0.0), with
commit identity as separate provenance. Owner added that deployment from a dirty
working tree is allowed. Prompt proposed output such as:

```text
baton 12.0.0 (3c0dd082, dirty)
```

Owner confirmed "yes". These values are captured at packaging time; the
deployed command never queries the original repository.

## Selected implementation boundary

- Introduce one authoritative v12 application version module and expose it through
  the deployed command's --version. Keep package metadata consistent with that
  authority instead of maintaining two unrelated version literals. The proposed
  initial application version is 12.0.0; do not infer broader release/tag actions.
- Capture full source commit and a clearly defined dirty flag when packaging,
  including staged/unstaged and ordinary untracked source changes reported by
  read-only Git status; ignored build outputs do not make a clean tree dirty.
  Display may abbreviate the commit while retaining full build provenance.
- Dirty builds are allowed. The commit identifies their base, not the exact
  built bytes; existing artifact/source manifests identify candidate content.
  Do not require commit/stage/clean operations or invent a Git revision for
  uncommitted content. No agent Git mutation.
- Embed the captured stamp in the distribution. --version must run with the
  development checkout and Git unavailable, without opening instance databases,
  checking credentials or starting a runtime. Later source changes cannot alter
  an installed build's reported identity. Missing development Git information is
  explicit unknown/unavailable, never falsely clean.
- Infer the build/bootstrap source from the repository containing v12/justfile,
  not the caller's arbitrary cwd. The original absolute checkout path is a build
  input only; deployed instance configuration must contain independent deployed
  paths and captured version/provenance, not require that checkout to exist.
  Preserve configured per-Job immutable base semantics; a version label is not
  a replacement for a Job's declared base. If repository-copy behavior for dirty
  content needs a separate decision, name it rather than silently changing it.

This supersedes the earlier idea that a user-supplied deployment label or commit
is the application's version. PyInstaller one-folder, independent external
distro/db/repo and destination-local justfile remain selected. All previous
reviewed work/evidence stays intact for unchanged paths. This is a bounded
version/stamp and source-selection adjustment, not a new installer framework.

## Verification

Pin exact version/entry/build/recipe/package metadata/test paths before edits.
Use focused deterministic checks for clean/dirty/unknown stamping and formatting,
plus actual packaged --version with source/Git unavailable. Reuse prior lifecycle
and bootstrap evidence; no broad suite or live model campaign. The final built
artifact must contain the same captured metadata the build records. Return
implementation to independent review and then owner operations; Work stays open
for the original usable deployment outcome.
