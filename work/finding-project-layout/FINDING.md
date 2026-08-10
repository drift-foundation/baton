# Repository layout obscures Baton's product boundaries

Status: **confirmed; queued behind the current human-console freeze**.

## Observed

The repository root currently contains all of these different classes of
file together:

- reusable source packages: `baton_core/` and `baton_tui/`;
- fourteen `test_*.py` modules;
- distribution builders: `build_zipapp.py` and `build_tui.py`;
- generated artifacts and manifests: `bin/`, `DISTRIBUTION.json`, and
  `DISTRIBUTION-TUI.json`;
- current user/configuration documentation;
- a retired executable shim (`baton`) and frozen protocol-9 oracle
  (`baton_v6.py`).

There is no `pyproject.toml` or other package-layout declaration. The test
recipe compensates with `PYTHONPATH=.`, and both builders discover packages
by assuming that their own directory is also the repository root and source
root.

## Confirmed problem

The layout no longer communicates the architecture that the implementation
now has:

1. `baton_core` is the reusable protocol/storage/client library.
2. The agent CLI and human TUI are independent front ends.
3. Each front end has a separate deterministic standalone distribution.
4. Tests, build tooling, frozen compatibility evidence, checked-in release
   artifacts, and product source have different ownership and lifecycles.

Keeping all of those at one level makes ordinary navigation noisy, makes
retired code look current, and encourages build/test code to depend on the
working directory rather than an explicit source layout. The problem will
worsen as the core API and TUI grow.

## Slawomir's root rule

Slawomir clarified the intended outcome after the initial audit: source code
belongs under `src/` (or an equivalently explicit source directory), tests and
tooling belong under their own top-level directories, and the repository root
must not remain a mixed list of code, tests, generated metadata, examples,
and documentation. The desired visual rule is **top-level directories plus
`README.md` and `LICENSE`**.

That ruling supersedes the initial proposal to leave protocol/config/schema/
manifest/development files loose at the root merely because they are release
entry points. Give those files named directories instead.

## Proposed boundary

This is a repository-layout refactor, not a protocol or behavior change.
Revalidate the exact names before implementation, but preserve these
boundaries:

```text
src/
  baton_core/
  baton_tui/
  baton_cli/          # CLI-only adapter/bootstrap, if still needed
tests/
  core/
  tui/
  packaging/
  fixtures/           # frozen protocol evidence, not active source
tools/
  build_zipapp.py
  build_tui.py
  requirements-dev.txt
docs/
  AGENTS-MAILBOX-PROTO.md
examples/
  baton.json
schema/
  config-schema.json
dist/
  DISTRIBUTION.json
  DISTRIBUTION-TUI.json
bin/                  # checked-in standalone release artifacts
work/                 # ephemeral findings only
assets/
```

`README.md` and `LICENSE` remain at root. Two discovery entry points also
remain as explicit functional exceptions:

- agents discover repository policy through root `AGENTS.md`;
- bare `just` discovers root `justfile`.

Moving either is possible only by giving up the normal zero-configuration
discovery path or by leaving a root shim/symlink, which would violate the
literal files-only rule in a different form. Slawomir approved the reviewer's
recommendation on 2026-08-10. The complete root-file allowlist is therefore:

```text
README.md
LICENSE
AGENTS.md
justfile
```

Everything else at root must be a directory. This allowlist is a required
regression boundary, not merely a documentation example.

The frozen `baton_v6.py` evidence must move out of the apparent executable
surface and retain its exact byte hash. The retired root `baton` shim should
either be removed or moved to explicit compatibility evidence; it must not
look like the current `bin/baton` release.

An ordinary `src/` layout may use a small project/test configuration file
without adding a runtime packaging dependency, but the strict root rule means
that configuration must either live under a tooling directory and be passed
explicitly or receive a separately approved root exception. Baton remains
stdlib-only and the zipapps remain the released interface.

## Important invariant: distribution independence

Moving a source file does not require changing its archived zipapp member
name. If source bytes and bootstrap bytes are unchanged, the deterministic
builders should still emit `baton_core/...` and `baton_tui/...` members with
the same timestamps and ordering. Aim for byte-identical `bin/baton` and
`bin/baton-tui` across the pure move. Any artifact drift must be explained
member-by-member and must not be hidden inside the layout change.

The CLI artifact must still exclude curses/TUI code. The TUI may include core
and TUI packages. Neither artifact may import from the repository, tests,
tools, or a host project at runtime.

## Interactions

- Do not begin while K's current source/test/artifact candidate is moving.
  Start from a committed, reviewed baseline so renames do not obscure product
  changes.
- Preserve Slawomir-only Git mutation: the implementer prepares filesystem
  moves and reports them; Slawomir stages/commits.
- Update `justfile`, builders, test discovery, documentation paths, hash pins,
  and packaging-isolation tests together.
- No permanent source or test may depend on this ephemeral finding path.

## Required regressions and evidence

1. All existing tests are discovered from the new layout without enumerating
   a stale hand-maintained subset.
2. `just venv`, focused tests, `just test`, `just build`, and
   `just build-tui` work from a fresh checkout.
3. Both zipapps execute from outside the repository with no `PYTHONPATH` and
   no repository imports.
4. CLI artifact contains no TUI/curses members; TUI contains exactly its
   declared core/TUI packages.
5. Deterministic double builds match byte-for-byte.
6. Compare pre/post artifact hashes and zip member manifests. Pure moves are
   byte-identical or every changed byte has a reviewed reason.
7. The frozen protocol-9 oracle hash is unchanged and active source imports
   none of the compatibility evidence.
8. Root contains only intentional repository/release entry points; a test or
   documented check pins that boundary so flat-root drift does not return.
9. `git diff --check` is clean and the final handoff lists every moved path.

## Open decisions to revalidate before implementation

- Whether the CLI adapter deserves `src/baton_cli/` or remains a deliberately
  narrow module adjacent to core without making core itself executable.
- Whether frozen protocol evidence belongs under `tests/fixtures/` or a
  separately named `compat/` directory.
- Where test configuration lives without reintroducing root clutter. It must
  not silently omit a new test file.
