# Progress — public release version

Implementer journal. The reviewer owns FINDING.md and PLAN.md; this file is
the record of what was actually done, including what was decided against.

## What shipped

`baton_core._impl.RELEASE_VERSION = "1.0.0"` is the single declaration.
Everything else derives from it:

- `baton_core.RELEASE_VERSION` re-exports it (never re-declares).
- `baton --version` -> `baton 1.0.0 (protocol 10)`.
- `baton-tui --version` -> `baton-tui 1.0.0 (protocol 10)`.
- Both `dist/` manifests carry the SAME key, `release_version`.
- README documents both lines and says the number is shared.

Retired: `TOOL_VERSION = "6.0.0"` and `TUI_VERSION = "0.2.0"`. Those were the
two independently drifting product versions the ruling closed, so a test
asserts their ABSENCE rather than trusting that nothing re-adds them.

## Decisions

**One declaration, not two aliases.** `TOOL_VERSION` was deleted rather than
kept pointing at `RELEASE_VERSION`. An alias cannot drift, but two names for
one release invite a future author to "update the tool version" and leave the
release version behind. There is nothing to update but the one constant.

**`core_versions()` keeps its `tool_version` KEY.** Renaming it to
`release_version` would change the shape of the public core API, which is a
declared contract (`CORE_API_VERSION = 2`) that an existing test pins at 2 --
and editing an existing test to accommodate my own change is not mine to do.
The VALUE now comes from `RELEASE_VERSION`, so nothing drifts; only the name
is legacy, and it is commented as such at the definition. The rename belongs
with the next core API bump, not with a version-string release. FLAGGED to
the reviewer rather than done quietly, and RULED on 2026-08-11: the key stays
for this release candidate, its value keeps deriving from the shared
declaration, and renaming the public key waits for an intentional Core API 3
change. So the legacy name below is a decision, not an oversight.

**The console parser was split out of `main`.** `main` is `pragma: no cover`
and built its parser inline, so "source-level parser tests cover `--version`
and generated help" was not testable without a terminal. `build_parser()` is
now importable, and `main` parses FIRST -- before `import curses` and before
the core compatibility check -- so the offline claim is structural rather
than incidental.

**The compatibility error dropped its version prefix.** It read
`baton-tui {TUI_VERSION} requires core API ...`. With no console-specific
version left, quoting the shared release number there would say nothing about
compatibility; the message now names only the API numbers, which are what the
check is about.

## Mistake made and caught

Break-checking the drift guard, I edited `RELEASE_VERSION` to `1.0.1`, ran the
tests, and restored it. All three writes were the same byte length and landed
inside one mtime second, so Python reused a stale `__pycache__` entry: the
test process imported `1.0.1` from bytecode while the source said `1.0.0`.
Worse, the REBUILD I ran next imported the same stale value and wrote `1.0.1`
into both `dist/` manifests while the packaged artifacts (which package source
text, not bytecode) correctly said `1.0.0`.

So the tree briefly held exactly the defect this finding exists to prevent --
manifests disagreeing with the executables -- introduced by my own verification
step. Cleared the bytecode, rebuilt, and confirmed. Recorded because the trap
is not specific to this change: any same-size edit to a constant can produce a
build whose manifest disagrees with its own artifact, and the only reason it
was caught is that `test_both_manifests_and_the_readme_agree_with_the_source`
compares the manifest against the source rather than against the build's own
idea of the source.

## Evidence

`tests/packaging/test_release_version.py`, seven tests, one per contract item:

1. Single semantic declaration; the retired constants are gone.
2. Both source parsers print the exact line and advertise `--version` in help.
3. The console answers `--version`/`--help` before its `required=True`
   arguments, and still refuses a bare run.
4. Both packaged executables print exactly one line, exit zero, with `TERM`
   removed, `HOME` redirected, every `BATON_*` variable dropped, and an empty
   temporary directory as the whole world.
5. Tripwire: nothing is written to that directory, and a `--config` path that
   does not exist is not even looked at.
6. Both manifests and the README agree with the source constant; the retired
   keys are absent.
7. Rebuilding into a scratch root reproduces the checked-in artifacts byte for
   byte and the published manifests exactly.

Deliberate breaks, each failing a NAMED test:

- Dropped `(protocol N)` from the console version ->
  `test_both_source_parsers_answer_version_and_advertise_it_in_help`,
  `test_rebuilding_reproduces_the_checked_in_artifacts_and_manifests`.
- Removed the CLI `--version` help text -> the same two.
- Changed the source constant to `1.0.1` without rebuilding -> five of the
  seven, including both manifests, the README, and both packaged executables.

Focused suites after the final rebuild: `tests/core` 688 passed,
`tests/packaging` + `tests/core/test_core_api.py` + `tests/tui` 1644 passed.
The complete release gate was NOT run -- the reviewer reruns it once on the
final bytes after independent approval.

Protocol 10 untouched: no schema, wire, authority, message, claim, retention,
or delivery behavior changed. `PROTOCOL_VERSION` is still 10 and
`CORE_API_VERSION` is still 2.
