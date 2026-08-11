# Public release version

Status: **implemented, independently approved, and final release gate passed; awaiting RC commit**.

Discovery context: immediately after the final human TUI trial, Slawomir
ruled that both public executables need a conventional version query and that
the first public release is `1.0.0`.

## Confirmed contract

- The Baton project release version is semantic `major.minor.patch`; this
  release is exactly `1.0.0`.
- `bin/baton --version` succeeds and reports the Baton release version.
- `bin/baton-tui --version` succeeds and reports the same Baton release
  version. CLI and TUI must not expose independently drifting product
  versions for this release.
- Version output identifies the executable and retains the protocol version,
  so a human can distinguish product compatibility from the release number:

      baton 1.0.0 (protocol 10)
      baton-tui 1.0.0 (protocol 10)

- `--version` is an offline metadata operation. It must not require a config,
  terminal, participant, authority, or project directory; it must not open or
  mutate the store; and it exits zero after one output line.
- Each executable's generated help advertises `--version`.
- Source metadata, both distribution manifests, packaged executables, README
  examples, and tests must agree on `1.0.0`. There must be one authoritative
  release-version declaration used by both applications, not copied constants
  that can drift.

This is a tool/package surface change only. Protocol 10 remains frozen; no
schema, wire, authority, message, claim, or retention behavior changes.

## Resolution

Approved by `baton.reviewer` on 2026-08-11. Both packaged artifacts report the
shared 1.0.0 identity offline and rebuild deterministically. The Core API 2
`tool_version` response key is retained as a compatibility name whose value is
the shared release version; any rename waits for an intentional Core API bump.
The final gate passed 2318 tests, deterministic rebuild, packaged workflow
smoke, and live doctor. The reviewed RC commit remains.

## Required evidence

1. Source-level CLI and TUI parser tests cover `--version` and generated help.
2. Both packaged zipapps produce the exact ruled one-line output without
   config or terminal setup and exit zero.
3. A tripwire proves the query performs no store/config/project access.
4. Both distribution manifests and public documentation agree with the
   shared source version.
5. Deterministic rebuilds match the checked-in executables and manifests.
6. The complete suite, packaged release smoke, and live protocol-10 doctor
   pass on the final bytes after Slawomir's zipapp trial.
