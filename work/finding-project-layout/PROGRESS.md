# Progress

Owner: `baton.implementer` only.

## 2026-08-10 — steps 3 and 4

State: **placement choices revalidated with evidence; baseline captured.
No file moved yet.**

Baseline: commit `8444d12`, working tree clean apart from this finding's own
documents.

## Step 3 — the three open placement choices

### The CLI adapter stays `baton_core/cli.py`

Not a preference. `src/baton_cli/` would change the ZIPAPP MEMBER NAME, and
this finding's own invariant says a pure move must leave the artifacts
byte-identical:

    bin/baton members today
        __main__.py
        baton_core/__init__.py
        baton_core/_impl.py
        baton_core/authoring.py
        baton_core/cli.py          <- would become baton_cli/...
        baton_core/references.py

So the choice is between the layout name and the artifact-parity evidence, and
parity is the stronger claim: it is what proves the refactor changed nothing.

The module is already the narrow adapter the option describes. Its docstring
says so: it implements nothing, it exists so that importing `baton_core` gets
a library with no `main` on it while the executable has exactly one documented
door. A `baton_cli` package would be a second door with the same view.

Revisit only if a future front end needs core WITHOUT that door, which is a
product change and not this refactor.

### Frozen evidence goes to `compat/`, not `tests/fixtures/`

`baton_v6.py` is imported by NOTHING. Every reference reads its BYTES for a
hash pin or `ast`-parses it to assert nothing imports it. It is not test
input; it is a record of what protocol 9 did, and the assertions about it are
"unchanged" and "unreferenced".

A fixture is something a test consumes. Filing a record as a fixture invites
the next reader to consume it, which is the one thing the retirement forbids.

The retired root `baton` shim (243 bytes, "protocol 6") joins it: same
category, and grouping them stops the shim looking like the current
`bin/baton`, which the finding names as a goal.

### Test configuration: `tests/conftest.py`, and no root file

`tests/conftest.py` inserting `src/` on `sys.path` satisfies every constraint
at once:

- no root clutter and no root exception to request;
- no packaging dependency; Baton stays stdlib-only;
- works for bare `pytest`, `just test`, and an IDE runner alike, where a
  `PYTHONPATH` in the justfile only works for `just`;
- cannot silently omit a new test file, because discovery stays pytest's
  ordinary recursive scan rather than an enumerated list.

The justfile's `PYTHONPATH=.` becomes unnecessary rather than moving.

## Step 4 — pre-move baseline captured

Recorded before touching anything, so post-move parity is a comparison rather
than an assertion:

    bin/baton      341270 bytes  15873a37099ee36b7bac8ef459cf401ecd3825889e7e1f56d1cb7fd226e462e4
    bin/baton-tui  641520 bytes  9189f1cd2ef62d46b23f29f5a1d9399b6d92ede2fc72b6d7ae9a090ff77430c6
    baton_v6.py     hash pinned by test_retired_oracle.py, unchanged
    baton (shim)    243 bytes

Every zip member's name, size, CRC and timestamp is recorded. Member
timestamps are fixed at 2020-01-01, so a pure move must not move a single
byte — the builders have no wall-clock input to drift on.

THE PARITY CONSTRAINT, stated plainly: members are named `baton_core/...` and
`baton_tui/...`. After the move the builders read from `src/` and must still
emit exactly those names. If a member name changes, the artifact changes, and
the refactor stops being provably behaviour-free.

Also recorded: a sha256 for every `.py` file that will move, and for the six
non-Python movers.

## Next

Step 5, mechanical moves only, once the reviewer has seen the three decisions
above. No product or protocol edits in the same step.

## 2026-08-10 — baseline corrected after review

State: **baseline corrected; still nothing moved.**

Two omissions, both fair.

### `.gitignore` was missing from the inventory

92 bytes,
`3ac405b185f163dd49fc18bbbab14162e33db44dd3bdddef58769c15c47331c0`.
Tracked, at the root, and NOT in Slawomir's four-file allowlist.

Its disposition is a genuine product choice the root rule does not settle, so
it is escalated rather than decided here. What the evidence says:

    __pycache__/                     repo-wide
    *.py[cod]                        repo-wide
    .pytest_cache/                   root artifact
    .venv/                           root artifact
    .coverage                        root artifact
    htmlcov/                         root artifact
    .claude/settings.local.json      root-anchored

Five of the seven patterns are root-anchored and the other two are repo-wide.
The options, with what each costs:

1. **Root exception**, alongside `AGENTS.md` and `justfile`. Git reads
   `.gitignore` from the root and nowhere else, so this is the same argument
   already accepted for those two: moving it means giving up
   zero-configuration discovery.
2. **`.git/info/exclude`** — untracked and local, so every clone loses the
   hygiene. Fails the tracked requirement outright.
3. **`core.excludesFile`** pointing into a tooling directory — per-clone git
   config, so a fresh clone has no ignore rules until someone runs a setup
   step. Fails zero-configuration in a way that shows up as noise in
   `git status` rather than an error.
4. **Per-directory `.gitignore` files** — works for the two repo-wide
   patterns, but multiplies the file and SILENTLY MISSES a new directory.
   That is the same failure mode the test-configuration decision was chosen
   to avoid.

Recommendation: option 1, for the reason already ruled twice. Not implemented
without a ruling.

**RULED 2026-08-10: `.gitignore` stays at the repository root.** The exact
root allowlist is therefore FIVE files, not four:

    README.md
    LICENSE
    AGENTS.md
    justfile
    .gitignore

The root-boundary regression pins five, and the reviewer's earlier pre-move
objection is superseded.

### Per-source hashes were 16-hex prefixes

Corrected. Full 64-hex SHA-256 for all 44 tracked movers, with byte sizes,
sent with this entry. A prefix is fine for reading and useless for the parity
comparison this baseline exists to enable, which is the whole point of taking
it.

## 2026-08-10 — step 5: mechanical moves complete

State: **moved; nothing else touched. Discovery and builds are expected to be
broken until step 6.**

    src/baton_core/          src/baton_tui/
    tests/core/              4 modules
    tests/tui/               7 modules
    tests/packaging/         3 modules (packaging, docs, retired oracle)
    tools/                   build_zipapp.py, build_tui.py, requirements-dev.txt
    docs/                    AGENTS-MAILBOX-PROTO.md
    examples/                baton.json          (was example-baton.json)
    schema/                  config-schema.json
    dist/                    DISTRIBUTION.json, DISTRIBUTION-TUI.json
    compat/                  baton_v6.py, baton-protocol6-shim

Root is now exactly the five allowed files: `README.md`, `LICENSE`,
`AGENTS.md`, `justfile`, `.gitignore`.

`bin/`, `work/` and `assets/` are unchanged.

**All 44 movers verified byte-identical** against the pre-move baseline: same
size, same full SHA-256, at the new paths. That is what makes this a move
rather than an edit, and it is checked rather than asserted.

Two naming decisions inside the move, both minor and both reversible:

- `example-baton.json` became `examples/baton.json`. The `example-` prefix was
  compensating for a flat root; inside `examples/` it says the same thing
  twice.
- the retired shim became `compat/baton-protocol6-shim`, dropping the bare
  name `baton`. Its own docstring says protocol 6, and a file called `baton`
  sitting anywhere still reads as the current executable, which is what the
  finding asked to end. It has no extension because it never had one and this
  step does not edit content.

`test_retired_oracle.py` went to `tests/packaging/` rather than `tests/core/`:
what it asserts is that the frozen evidence stays out of the shipped surface
and is imported by nothing, which is an isolation property.

Next: step 6, discovery and paths.

## 2026-08-10 — steps 6 and 7

State: **complete; ready for review.**

    2278 passed  (2276 before the move, plus the two root-boundary tests)
    git diff --check                   clean
    bin/baton      15873a37...  BYTE-IDENTICAL to the pre-move baseline
    bin/baton-tui  9189f1cd...  BYTE-IDENTICAL to the pre-move baseline

### Discovery

`tests/conftest.py` puts `src/` on the path; the justfile stops enumerating
test files and runs `pytest tests`. The enumerated list was itself a defect:
adding a test module and forgetting that line meant the suite silently stopped
covering it, which is regression 1 of this finding.

### Builders

Both now name their layout explicitly -- `ROOT`, `SRC`, `DOCS` -- instead of
assuming their own directory is the repository. Manifests are written to
`dist/`.

ONE BEHAVIOUR CHANGE, and it needs to be visible rather than buried: the CLI
builder no longer COPIES the protocol document into the distribution root. It
records and hash-pins `docs/AGENTS-MAILBOX-PROTO.md` instead. The copy existed
because the flat root made source and distribution root the same directory, so
it was a no-op; with the document under `docs/` a copy would be a real
duplicate, a second file claiming to be the protocol and diverging the first
time someone edits one. Writing it to the repository root would also break the
root rule. `protocol_doc` in the manifest is therefore a path from the
repository root rather than a bare filename. Artifact bytes are unaffected.

### Tests re-anchored, not rewritten

Every test that reached for a repository file used its own directory, which
was the root by coincidence. They now name the root explicitly. The PTY tests
needed more than a path constant: they SPAWN a console, and a child process
does not inherit `conftest.py`'s `sys.path` edit, so `src/` travels in the
child's environment.

The isolated-checkout test now mirrors the layout instead of flattening it.
That is the honest shape: the layout is part of what makes a checkout usable,
and a flat copy would prove something nobody ships.

### The root boundary, as a regression

`test_the_repository_root_holds_only_the_allowed_files` pins the five, and a
sibling proves no source or test escaped its directory -- the allowlist alone
would still pass with an empty `src/`.

Measured on the WORKING TREE rather than `git ls-files`. The index belongs to
Slawomir and agents never stage, so an index-based check would report his
staging rather than the repository's shape, and would fail for the whole
window between the moves and his commit. My first version made exactly that
mistake and failed listing the old paths.

Break-checked: a stray file at the root fails both.

### Evidence

- deterministic double builds, both artifacts, identical bytes;
- both artifacts byte-identical to the pre-move baseline;
- both execute from outside the repository with no `PYTHONPATH`;
- frozen oracle hash unchanged in `compat/`, imported by nothing;
- CLI artifact still carries no TUI member.

The extraction-purity gate caught my own README layout section naming the
agent-policy file, which is a banned host reference in a reusable asset. That
gate has now caught me six times, and every time it was right.

## 2026-08-10 — corrected after layout review

State: **corrected, pending re-review.** 2279 passed.

**R2 was a real defect and my test hid it.** The builder recorded the protocol
document's path without copying it, so an alternate distribution root got a
manifest naming a file that root did not contain. My regression resolved the
built manifest's path against the SOURCE repository, where it always exists --
so the check passed while the contract was broken.

That is the second time in this session I have written an assertion that
resolved the easy way. The contract is "every path the manifest records
resolves from the root the manifest sits in", and the test now resolves from
`root` and hashes the file it finds. Break-checked: removing the copy fails
it by name. An alternate root now contains bin/, dist/ and docs/.

The copy is skipped when building in place, where the target IS the canonical
file, so there is still no duplicate in the repository.

**R1.** Root policy pointed at `AGENTS-MAILBOX-PROTO.md`, which the move had
relocated. Repaired to `docs/`, and pinned:
`test_every_repository_path_named_by_agent_policy_resolves` RESOLVES every
repository path the policy names rather than checking a known list, so the
next move breaks it instead of it ageing quietly. Placeholders like
`work/finding-<slug>` are excluded -- they describe a shape, not a file.

Break-checked: pointing the policy back at the old path fails it.

**R3.** ".gitignore is the only place git looks" was simply wrong -- git reads
one in any directory. Corrected in the README and the test docstring to the
accurate reason: the root file is the tracked, zero-configuration
repository-wide ignore policy, which is what makes moving it costly.

**Handoff convention.** The previous handoff attached the changed-path list as
an ordinary part rather than a references leaf. Corrected.

## 2026-08-10 — cleanup residues, final gate

State: **complete, pending final review.**

    2279 passed
    git diff --check                   clean
    bin/baton      15873a37...  byte-identical to the pre-move baseline
    bin/baton-tui  9189f1cd...  byte-identical to the pre-move baseline

Both were docstrings and dead weight left behind by my own edits:

- the builder's module and `build()` docstrings still said the manifest sits
  "beside" the artifact at the root top, describing the layout the refactor
  replaced. They now state the actual contract: executable at `bin/`, manifest
  at `dist/`, protocol document at `docs/`, every recorded path relative to
  the root -- which is the property that broke when the document was recorded
  without being copied;
- the unused `DOCS` constant is gone. I added it while re-anchoring the
  builder and then never used it;
- `test_distribution_root_contract` asserted the built protocol hash twice on
  consecutive lines. One remains.

Verified after: an alternate root still contains `bin/`, `dist/` and `docs/`.

No product, protocol, package-source or artifact change in this step, and the
hashes confirm it.

## 2026-08-10 — commit message reviewed and forwarded

Approved with one precision edit, and the edit is worth recording because the
overclaim was mine.

I wrote "a pure relocation: no product, protocol, schema or package-source
change". The second half is true and evidenced. The first two words are not:
test discovery, builder paths, the agent-policy link and manifest placement
all changed. What is unchanged is product and protocol behaviour, the packaged
source bytes, and both artifacts.

"Pure relocation" is the kind of summary that reads well and quietly widens a
claim past its evidence -- exactly what a commit message should not do, since
it is what the next reader trusts instead of re-deriving. The reviewer
replaced it with the supported statement and forwarded that to Slawomir.

State: approved pre-commit. Cross-team onboarding stays closed until the
reviewer verifies the committed bytes under the separate post-commit gate.
