# Progress — deployment recipe

Implementer journal.

State: **`tools/deploy.py` and its `just` targets implemented and tested. No
deployment performed.**

## What shipped

`tools/deploy.py` with three subcommands, and `just deploy`,
`just deploy-activate`, `just verify-deployment` over them. Built against the
layout pinned in `PLAN.md` and reviewed.

- `publish DEST` — copies a certified release into `DEST/v<version>/`, writes
  `DEPLOYMENT.json` recording every file with its digest, and makes everything
  read-only except the executables.
- `verify VERSION_DIR` — re-hashes every recorded file, and also reports files
  that are PRESENT BUT NOT RECORDED. An unrecorded file is as much a problem as
  a changed one: it is content in a deployed tree that no release put there.
- `activate DEST VERSION` — verifies first, then swaps `DEST/current` by
  rename. The symlink is relative, so a deployment root that is moved or
  mounted elsewhere still resolves.

Refusals, all exiting non-zero: an existing version directory (no force flag
exists), an artifact that disagrees with its manifest, manifests that disagree
with each other on the release version, activating a tree that does not verify,
and activating a version that was never deployed.

## A claim I made twice and had wrong

I told the reviewer, in the layout proposal and again in a status message, that
this working tree "could not be deployed right now" because the console source
is ahead of the certified console — and that the deployment refusal and the red
packaging test were the same fact.

They are not. Running it proved otherwise: `publish` succeeded from this tree.

The gate compares each ARTIFACT against its own MANIFEST, and those agree
perfectly — I never rebuilt `bin/baton-tui` or its manifest, so both still
describe certified 1.0.0. What has moved is the SOURCE, which the TUI manifest
does not record at all (the CLI manifest has `source_sha256`; the console
manifest has a member list instead).

And on reflection the tool is right and my claim was wrong in substance too:
the artifacts ARE the release. Deploying certified 1.0.0 bytes is correct
regardless of what the source beside them has moved on to. The packaging test
asks a different and also legitimate question — whether the checked-in artifact
is what this source builds — and conflating the two was my error, not a
property of either.

The residual gap is real but smaller than I said: nothing stops someone
deploying artifacts that correspond to no committed source state. Closing that
would need the console manifest to record a source digest, which is a manifest
change to a released distribution and therefore not this finding's to make.

## Evidence

`tests/packaging/test_deploy.py`, 7 tests: a deployed tree runs with no
repository and no `PYTHONPATH` and carries no authority; a version directory is
never rewritten; verification detects both tampering and unrecorded files;
activation is atomic, uses a relative link, leaves no staging artifact, and
refuses an unverifiable tree without disturbing the existing pointer;
publishing refuses an uncertified source and leaves nothing behind when it
does; the record is byte-reproducible across two publishes; and publishing does
not perturb the repository's own artifacts.

Deliberate breaks, each failing a named test: version directories made mutable
→ `test_a_version_directory_is_never_rewritten`; the certification comparison
disabled → `test_publishing_refuses_an_uncertified_tree`.

`tests/packaging`: 43 passed, 1 failed — the known release-currency test we
agreed to leave red until the branch exists. `bin/baton` and `bin/baton-tui`
still hash to their 1.0.0 values.

## Still open, and not mine

The next-gen version number, and whether `examples/baton.json` ships. Neither
blocked this: the version is an argument, and the exclusion is one line in
`PAYLOAD`.

## Response to review pass 1 — all four blockers

**R1 — the ruled command and payload.** `just deploy DEST VERSION` and
`deploy.py publish DEST VERSION`. The version is validated as
`major.minor.patch` and publish refuses unless BOTH manifests name exactly
that release, so an operator can state and verify what they are installing.
`examples/baton.json` ships — and publish proves it is inert first: no
`sqlite`/`database`/`authority` key, and no absolute root that exists on this
machine. The release announcement is selected from the version
(`docs/RELEASE-<VERSION>.md`) and its absence fails in preflight.

**R2 — certification now covers everything the manifests ADDRESS.** The
protocol document is hashed against `protocol_doc_sha256`, and both manifests
must agree on the protocol version (the old loop just overwrote it).

This immediately caught a real mixed-version condition in the working tree:
`docs/AGENTS-MAILBOX-PROTO.md` has moved on from the hash the frozen 1.0
manifest pins, so **this repository can no longer publish a 1.0.0 deployment**
— correctly, because it is no longer a coherent 1.0.0 release. That is the
exact scenario R2 describes, found in the wild rather than in a fixture.

**R3 — nothing partial ever appears.** The whole payload is preflighted, then
staged in a uniquely named sibling, verified, hardened, fsynced, and moved
with `os.rename`. The version path is reserved by an atomic `mkdir` lock and
checked for existence UNDER that lock, so an existing directory — including an
empty one somebody else made, which `rename` would have consumed — is never
replaced. Failure removes only the staging tree this process owns.

**R4 — the hardening claim is now true.** Directories and `bin/` entries are
`0555`, everything else `0444`, deepest-first so a directory is sealed after
its contents. Payload entries must be regular non-symlink files, with no
symlinked ancestor, at publish AND at verify — `verify` followed symlinks
before, so a deployed tree could describe bytes living elsewhere. Activation
uses a pid-unique staging link, refuses a non-symlink `current` instead of
replacing it, refuses an unexpected staging object instead of deleting it, and
fsyncs the destination after the swap.

The read-only claim is stated honestly in the code: it stops accident, not an
owner who changes a mode. `verify` is what answers deliberate change.

## Evidence

`tests/packaging/test_deploy.py`, 19 tests against a CONSTRUCTED release tree
— constructed because the repository is currently the mixed-version case
publish must refuse, so it cannot also be the fixture proving publish works.

Deliberate breaks, each failing a named test: protocol-doc certification
removed; staging removed; hardening removed; the activation guard removed.

Worth stating precisely: with staging removed, only the empty-directory test
failed. The late-payload and copy-failure guarantees are carried primarily by
the PREFLIGHT, which refuses before anything is written; staging is the second
line for failures preflight cannot see, such as a write error midway.

`tests/packaging`: 55 passed, 1 failed — the known frozen-artifact currency
failure, unrelated to this item.

## Not done, by instruction

Nothing deployed, nothing activated, no frozen executable, manifest, live
authority or config touched. `docs/AGENTS-MAILBOX-PROTO.md` and
`docs/EFFECTIVE-BATON.md` are the reviewer's for the config-regeneration
wording and were not edited here.

## Response to review pass 2 — true no-replace, owned staging, real verification

**R1 — the publication is atomic no-replace now.** My lock was cooperative: it
excluded another copy of this tool and nothing else, so any process could
create the final path between the check and the rename, and POSIX rename would
consume an empty directory and report success. Publication uses
`renameat2(RENAME_NOREPLACE)` through `ctypes` — the only primitive that
reserves the pathname at the moment it matters.

It FAILS CLOSED. If the syscall is unavailable or the filesystem cannot do it,
publish refuses and says so rather than degrading to a replacing rename, which
would be this defect hidden behind a successful exit code. The `lexists` check
survives only as an early, friendly refusal, and the code says that is all it
is.

**R2 — staging is created, therefore owned.** `tempfile.mkdtemp` makes it
atomically with a name nobody else holds, so there is no path where the tool
removes an object it did not create; a pid-derived name could collide after pid
reuse, and deleting whatever sat there was a cure worse than the disease.
`_remove_owned` restores write permission deepest-first before removing, so a
failure AFTER hardening no longer leaves the whole read-only tree behind — my
earlier copy-failure test failed before hardening and never reached that path.

**R3 — verify checks modes and the root.** Exact modes for leaves, `bin/`
entries, nested directories, the record, and the version root; and the root is
`lstat`ed and refused if it is a symlink or not a directory. A mode-only
change returned no problems at all before, and activation would have accepted
that writable tree.

**R4 — durability is deep.** Every file is fsynced, then every directory
deepest-first, AFTER hardening so the mode changes are durable too. Syncing
only the staging root said nothing about entries in `bin`, `docs`, `dist` or
`examples`.

### A test-suite consequence of hardening, fixed properly

A `0555` tree is exactly what stops accidental writes and also what stops
pytest's own `rm_rf` from clearing its temporary directory. An autouse teardown
restores the write bit, so the hardening stays honest in the product and tidy
in the suite. (The warnings I first saw came from directories left by runs
before that fixture existed.)

## Evidence

`tests/packaging/test_deploy.py`: 25 tests. New: a directory appearing AT the
rename boundary is not replaced; publication refuses when it cannot be atomic;
a failure after hardening removes only its own staging and leaves an unrelated
one untouched; every nested directory participates in the fsync; a mode-only
change is detected; a symlinked version root is refused; a pre-existing staging
object is never deleted.

Deliberate breaks, each failing named tests: replacing `rename` restored;
`_remove_owned` reverted to plain `rmtree`; leaf mode checks removed; only the
staging root fsynced.
