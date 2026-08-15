# R95–R98 corrected — evidence

In reply to review message `46a4ff35ebd1021b3e056cc5266a4dd5`
(review-2026-08-15T18-58-12Z.md, claim
`08b983bc05c34ad77729c9eb59cea38a`). All five regressions (the
extended resolve case plus the four new tests) were reproduced red as
observed, then corrected to green — and this time the COMPLETE gate
was rerun after the focused set.

## R95 — the independent locator requires a contained suffix

`resolve pushcoin` and `resolve pushcoin:` now refuse: "not a
canonical independent locator: the form is ROOT_ID:<contained
relative path> with a non-empty contained suffix; a bare WORK id
resolves its dossier root". The bare-Work-id dossier form is kept.

## R96 — no-follow governs directory creation itself

For every managed directory the parent is opened component-by-
component with `O_RDONLY|O_DIRECTORY|O_NOFOLLOW` BEFORE creation, and
the created-or-existing child is then validated through that same
parent fd. A parent swapped for a symlink during the mkdir is
detected by the fd-relative validation (the held parent fd no longer
contains the child); the invocation's own misplaced empty directory —
created milliseconds earlier through the swapped path, never user
data — is withdrawn, and the operation refuses with the changed-
while/symlink message. The reviewer's nested-race regression ends
with the outside directory empty. File creation was already
fd-chain-bound (R93) and remains so.

## R97 — the resolver document is strict

`load_resolver` parses with the shared duplicate-key boundary
(`config._no_duplicates`) — `{"roots": {"pushcoin": A, "pushcoin":
B}}` refuses at parse instead of silently redirecting the root — and
the top-level field set is exactly `{"roots"}`: unknown fields
refuse, naming them. Root-id and absolute-path validation retained.

## R98 — a short write is a reported partial failure

Both writers check the `os.write` return count. A short write
refuses with the same structured exact-partial report as a raised
failure — init: "init managed only a short write of <file> (N of M
bytes). Created so far, including the partial <file>: [...]";
bootstrap: "bootstrap failed at <target>: short write (N of M
bytes)... Created so far: [...]". Success is never reported until
every expected byte was written; bootstrap byte parity stays part of
the success contract.

## Public workflow forms

WF-14 (source+packaged) gained the CLI-visible cases: bare and
empty-suffix resolve refusals (R95); duplicate-key resolver refusal
through `resolve` and unknown-field resolver refusal through
`bootstrap` (R97). R96/R98 need monkeypatched fault injection and
live in the focused suite.

## Break-sweeps for the new guards

Defect in → red → restore → green, no residue: R95 gate dropped
(focused + WF-14 red); R96 creation trusted blind (nested escape red
on the outside-directory check); R97 laxity restored (focused +
WF-14 red); R98 counts ignored (both short-write regressions red).

## Gate

Focused `test_ws6_project.py`: 16 passed under
`-W error::ResourceWarning` (12 prior + the 4 new regressions, with
the extended resolve case). All 56 workflow runs green
source+packaged. `just test-v11`: 511 parallel + 3 serial green.
Dossier: PROGRESS.md Step 47. STOPPED for re-review. Production
deployment, mailbox migration, shutdown, and cutover remain held for
Slawomir's manual operation.
