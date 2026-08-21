# Relocate the reviewed v12 PoC into this repository

## Context — 2026-08-21

W76's disposable external Claude ACP proof of concept was independently
reviewed clean in `../finding-v12-claude-acp-dispatch-poc/` after six review
rounds. The approved placement supersession in the parent finding now makes
the self-contained top-level `v12/` subtree of this repository its durable
development home.

The external root is not a clean committed snapshot: its reviewed state is
the current working tree, including the round-six source corrections and
proof packs. The final W76 review explicitly identifies that current external
snapshot as the migration source.

## Confirmed boundary

- Copy the reviewed prototype into top-level `v12/` without modifying any v11
  product, test, bridge, recipe, packaging, or deployment path.
- Preserve the prototype's own package and lock metadata, source, tests,
  scripts, fixtures, configuration, container definitions, provenance, and
  reviewed evidence.
- Exclude `.git/`, `node_modules/`, `run/`, ignored disposable `work/`, secrets,
  authorities, logs, downloaded images, and other runtime state.
- `v12/` remains independently buildable and testable. Root recipes do not
  delegate to it and v11 packaging does not include it.
- Run the same focused unit gate from `v12/` and compare the migrated file set
  and bytes with the selected external snapshot.
- Do not remove `/home/sl/src/baton-v12-poc` until the in-repository copy and
  gates are verified. Removal is the final separately reported destructive
  step; the external root is not retained as an archive afterward.

## Acceptance

The selected non-runtime external files exist byte-for-byte under `v12/`, the
prototype's own test gate passes there, generated/runtime material is absent,
and no v11 source or root integration surface changes as part of the move.

## Migration revalidation — 2026-08-21

**Confirmed.** The selected external snapshot is 426 non-ignored files. The
initial `v12/` copy is byte-identical, preserves all three executable files,
excludes `.git/`, `node_modules/`, `run/`, and ignored disposable `work/`, and
passes all 59 unit tests after `npm ci` from the pinned lockfile.

**Observed.** A literal copy is not yet a runnable in-repository proof:
`poc.json` still names `/home/sl/src/baton-v12-poc`, while the reviewed runtime
fence correctly refuses any worker mount into `/home/sl/src/baton`. Weakening
that fence merely because the source moved would silently discard a W76
security boundary.

**Current migration rule.** Keep code, fixtures, tests, scripts, configuration
templates, and retained evidence under `v12/`, but place disposable authority,
Job records, attempt state, credentials, and generated proof output under one
explicit external state root. The sample may use a `/tmp` root for this
disposable PoC. The worker still receives only the selected per-attempt paths;
the entire Baton checkout remains forbidden as a container mount. Update
placement-specific documentation and tests without changing the reviewed
assignment lifecycle. Add a self-contained `v12/justfile`; do not add root
recipe delegation.

## Implementer revalidation — 2026-08-21

**Confirmed, against the current tree before any edit.** The reviewer's
migration checkpoint holds exactly as recorded:

- the selected external snapshot is 426 non-ignored files, and the `v12/`
  copy is byte-identical for all 426 — verified file-set and `cmp` on every
  file;
- all three executables (`bin/v12-poc`, `scripts/new-authority.sh`,
  `scripts/run-proof.sh`) preserved their mode, and `.git/`, `node_modules/`,
  `run/` and the ignored disposable `work/` are absent from the copy;
- the migrated unit gate passes 59/59;
- `poc.json` still named `/home/sl/src/baton-v12-poc` for its authority,
  record base and attempt state, and `scripts/new-authority.sh` still bound
  its Baton record root to its own directory. Both would now place
  disposable state inside the Baton checkout;
- `Manager.forbiddenPaths()` still names `/home/sl/src/baton`, and
  `assertNoBatonCapability` canonicalizes both sides, so any mount from
  inside the checkout — the prototype's own subtree included — is refused
  before launch. No supersession of that fence was needed or made.

Prerequisites for the live proof were present and unchanged: the deployed
`8835cd5` executable, the `0.69.0` ACP adapter tree, a readable Claude
credential, Docker 29.1.3 and Node 24.

## Placement decisions — 2026-08-21

These implement the recorded migration rule; none of them touches the
reviewed assignment lifecycle.

**One explicit external state root, named in configuration.** `poc.json`
gains a required `state_root`, and `baton.config`, `record_base` and
`runtime.state_dir` must all resolve inside it. The sample uses
`/tmp/baton-v12-poc`, which the finding permits for this disposable
prototype. Removing that one directory removes every disposable thing the
prototype creates.

**`record_base` is now required.** It was optional and fell back to the
prototype root. That default was harmless while the prototype was external
and is precisely the relocation hazard now, so the fallback is gone rather
than repointed.

**The placement check is lexical, and says so.** `state_root` need not exist
on a first run, so there is nothing to canonicalize. It refuses a state root
that overlaps the prototype in either direction, and any disposable path
outside it. It is NOT the security boundary and does not claim to be: a state
root that is a symlink into the checkout still reaches
`assertNoBatonCapability`, which canonicalizes before any container launches.

**`new-authority.sh` takes the record base as an operand** and refuses either
operand inside the prototype. The Baton record root it writes into the
disposable authority is that operand, not the script's own directory.

**`run-proof.sh` reads every disposable location from `poc.json`** and derives
the checkout from its own parent instead of hard-coding `/home/sl/src/baton`.
Its per-container mount assertions compare against that derived checkout, so
they now also prove the run never mounted the prototype's own directory.

**A new post-run assertion: the prototype subtree holds no generated state.**
The repository-status comparison cannot see this — an untracked subtree looks
identical before and after whatever is written inside it — so the runner walks
`v12/` and names any `run/`, `work/`, `*.sqlite3` or `.credentials.json` it
finds. `node_modules/` is the one generated tree that belongs here.

**`v12/justfile` is self-contained.** `install`, `test`, `proof`, `state` and
`state-clean`. No root recipe delegates to it and it calls no root recipe; a
regression test asserts both directions, and that the v11 deployer does not
package the subtree.

**Retained evidence stays a deliberate copy.** A run writes its pack under the
state root; it becomes retained evidence only when somebody copies it into
`evidence/<label>/`. Packs produced before the migration keep the retired
external root in their recorded paths, as history.

## Not done, and deliberately

The external prototype root `/home/sl/src/baton-v12-poc` is untouched. Its
removal is the recorded final step, after independent acceptance of this
migration, and is separately reported when it happens.

## Review round 1 — accepted corrections, 2026-08-21

`review-2026-08-21T05-09-14Z.md` recorded two blocking findings. Both were
reproduced against the tree exactly as written and are now recorded rulings.

**[P1] Every destructive target is validated before the first mutation.**
Reproduced: `run-proof.sh` removed `$STATE/evidence/$LABEL` — built from an
unconstrained label — before anything validated the configuration, and later
removed `record_base` and `state_dir` from raw strings; `new-authority.sh`
removed whatever authority operand it was handed; `just state-clean` removed a
raw `state_root` guarded by a three-entry denylist; and the exported check
accepted `/tmp` and `/var` as state roots.

**Ruled.** There is ONE placement authority, `v12/src/placement.mjs`. It
creates and deletes nothing. Every entry point that creates or removes state —
the proof runner, `new-authority.sh`, `just state-clean`, and configuration
validation — obtains its paths from that module before its first `mkdir`,
`chmod` or `rm -rf`, and uses the values it returns rather than the raw
configured strings. It refuses:

- a state root that is filesystem-wide, top-level, or fewer than two path
  components deep, or that contains the home directory;
- any created or removed path that is not a STRICT descendant of that root —
  the root itself is removed only by the one recipe that owns it;
- an evidence label that is not one safe path component;
- a `record_path` that could traverse out of its base;
- any path carrying whitespace or a control character, because these values
  cross shell entry points and are read positionally.

The runner obtains its plan through a plain assignment so `set -e` aborts on
refusal; inside a here-document the substitution's status is discarded and the
run would have continued with empty paths.

**[P1] Externality is asserted against the whole checkout.**
Reproduced: `assertStatePlacement` compared only with `POC_ROOT`, so
`<checkout>/v12-state-sibling` was accepted; `new-authority.sh` made the same
subtree-only comparison; and the post-proof stray walk inspected `v12/` alone.

**Ruled, superseding the round-1 phrasing in "Placement decisions" above.** The
externality boundary is `CHECKOUT_ROOT`, not `POC_ROOT`. Overlap in either
direction is refused, at every entry point, and the check canonicalizes the
longest existing prefix so a symlinked root is judged by where it lands. The
closing proof assertion now walks the WHOLE checkout for the artifacts this
prototype creates — a disposable authority, its SQLite files, a staged
credential, a Job record, an attempt directory — because "the state root is
external" is a claim about the repository, not about one directory in it.

**Unchanged, deliberately.** `assertNoBatonCapability` is still the
canonicalized launch-time fence deciding what a container may mount. Placement
validation is setup-and-cleanup safety and does not replace it; the review
asked for exactly that separation and the module says so in its own comment.

## Review round 2 — accepted corrections, 2026-08-21

`review-2026-08-21T05-34-21Z.md` recorded two further blocking findings. Both
were reproduced directly and are now recorded rulings.

**[P1] The authority recipe must be bound to the configured plan, not to any
descendant.** Reproduced: `assertUnderStateRoot` accepted
`/tmp/baton-v12-poc/evidence` and `/tmp/baton-v12-poc/attempts`, which are
strict descendants of the state root and are not the configured authority or
record base. `new-authority.sh` then used the RAW operands, so a swap or a
plausible typo would have recursively removed the retained evidence directory
and built an authority over the attempt tree.

**Ruled.** A strict-descendant proof is necessary and not sufficient. The
placement authority now publishes `paths`, the configured plan without an
evidence label, and `new-authority.sh` compares its operands against the
planned authority and record base, refuses on any difference, and then acts on
the PLAN's values. The operands remain — they are a statement of intent that
must match — but they are never paths the script follows. The retired
`check --target` verb, which only proved descendancy, is removed rather than
left available to a future caller.

**[P1] Root deletion needs positive ownership evidence, not path shape.**
Reproduced: `assertStateRoot` accepted `/var/log` and `/usr/local`, and
`just state-clean` consumed that string, made the tree writable and removed it.
No finite denylist and no depth threshold can establish exclusive ownership.

**Ruled, superseding the depth/denylist justification recorded in round 1.**
The state root carries a durable `.v12-poc-state-root` marker naming ITSELF,
written by the recipe that creates the root. Ownership states are exactly:

- `fresh` — the root does not exist; creating it establishes ownership;
- `owned` — it exists and carries our marker naming that exact path;
- anything else REFUSES, unchanged.

`placement.mjs state`, the only verb the cleanup recipe consumes, demands
`owned`. A marker copied from another root names that other root and therefore
authorizes nothing. The broad-root denylist and the two-component minimum stay
as COURTESY refusals with clearer messages; they are explicitly not the
authorization, and the module says so.

**Consequence, recorded because it is deliberate.** A state root created
before this ruling carries no marker, so the prototype refuses to clean it and
says why. That directory is removed by hand, once, by whoever knows what it
is — the refusal is the correct behaviour, not a regression to work around.

## Review round 3 — accepted correction, 2026-08-21

`review-2026-08-21T06-08-14Z.md` recorded one blocking finding. It was
reproduced exactly as written and is now a recorded ruling.

**[P1] The deletion path answered for an absent root.** Reproduced
non-destructively: `assertOwnedStateRoot("/tmp/v12-review-absent-root-8f61c2",
{forDeletion: true})` returned `{state: "fresh"}` and the path did not exist
before or after the call. The guard was `state !== "owned" && existsSync(root)`,
so absence was treated as "nothing to protect".

**Ruled, superseding that reasoning.** Absence is a fact about the instant the
check runs, not a property of ownership. The returned value goes straight to
`chmod -R` and `rm -rf`, and anything may create an unrelated directory at that
path between the two — cleanup would then act on a directory that never carried
a marker, which is precisely what the round-2 ownership ruling exists to
prevent. Cleanup therefore requires `owned` and nothing else, whatever the
path's current existence, and emits NO path when it refuses.

Setup is unchanged and still accepts `fresh`: creating a root is how ownership
is established, and closing that would leave no way in.

## Review round 4 — accepted correction, 2026-08-21

`review-2026-08-21T06-33-08Z.md` recorded one blocking finding, and it is
about the REGRESSION rather than the production guard.

**[P1] The absent-root case established its precondition by deleting.** The
case picked the fixed path `/tmp/v12poc-guaranteed-absent-8f61c2` and called
`rmSync(..., {recursive: true, force: true})` on it before asserting absence.
The name does not make a shared path unowned: another run, another checkout,
or an interrupted earlier run could have data there, and running the gate
would have removed it without the marker or exact-plan validation this very
case exists to require. It also contradicted the round-1 regression boundary,
which asked for these negatives to be proven without performing the dangerous
deletion.

**Ruled.** A negative about recursive deletion never establishes its own
precondition by deleting. Absence is obtained by CONSTRUCTION: a unique parent
the test creates with `mkdtempSync`, and a child inside it that has never been
created. The test removes only that parent, and only at the end.

The production guard is unchanged by this round — round 3's correction stands
exactly as recorded, and this is what proves it honestly.

## Review round 5 — accepted, 2026-08-21

`review-2026-08-21T06-49-51Z.md` independently verifies the round-four fixture
correction and accepts the in-repository migration. The full v12 unit gate
passes 78/78, the retired fixed shared path is gone, retained round-eleven
evidence is internally consistent, and no further migration, placement,
cleanup, or isolation finding remains.

This acceptance unlocks but does not perform the separately recorded final
destructive step: removal of `/home/sl/src/baton-v12-poc`. W126 remains open
until that removal is explicitly reported and verified.

## The external prototype root was removed — 2026-08-21

Review round 5 accepted the migration and named this the final, separately
reported destructive step. It is done, and this is the report.

**Removed:** `/home/sl/src/baton-v12-poc`, 17 MB, irreversibly.

**Verified before removing, non-destructively.**

- All **426** selected files exist under `v12/`. Exactly **ten** differ, and
  they are exactly the ten recorded placement-adaptation files: `.gitignore`,
  `PROVENANCE.md`, `README.md`, `bin/v12-poc`, `evidence/README.md`,
  `poc.json`, `scripts/new-authority.sh`, `scripts/run-proof.sh`,
  `src/config.mjs`, `test/unit.test.mjs`. Nothing was missing.
- Nothing outside that selected set was reviewed material, and this is what
  the removal destroyed:
  - `.git/` (1.8 MB) — ONE commit, `b0fb0cf chore: initialize disposable v12
    poc`, no remote, and a working tree that was entirely staged-but-never-
    committed. The reviewed content was therefore never in that history; it
    lived in the working tree, which is what was copied.
  - `node_modules/` (12 MB) — resolved from the committed lockfile and
    reproducible with `npm ci`.
  - `run/` (552 KB) and `work/` (128 KB) — disposable authority, attempt state
    and Job records from the pre-migration runs. No credential material
    remained in either; that was checked.
- No live configuration, script, recipe or test pointed at the external path.
  The only surviving occurrences of the string are the package/owner
  identifier, and assertions that the path is ABSENT.

**Verified after removing.** `npm test` from `v12/`: 78 passed. The complete
bounded live proof from `v12/` alone: `proof-r12-standalone`, exit 0 — fresh
disposable authority, happy path, both token fences, post-claim compensation,
credential disposal, and the whole-checkout walk, with nothing reachable from
the retired root.

One canonical prototype tree now exists, as the parent plan's item 0ai
required. Earlier evidence packs still name the retired root in their recorded
paths; that is history and is left exactly as produced.

## Terminal verification — 2026-08-21

`review-2026-08-21T07-04-00Z.md` independently confirms the retired external
root is absent, the canonical `v12/` tree is present and contains no generated
authority/runtime state, live prototype paths no longer reference the retired
root, the unit gate passes 78/78, and the standalone proof's repository
before/after snapshots match. No W126 acceptance condition remains.
