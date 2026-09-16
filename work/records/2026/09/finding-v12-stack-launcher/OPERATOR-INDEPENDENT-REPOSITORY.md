# The repositories a real deployment needs — the owner packet

W183883. Rewritten under claim187223 after review 2026-09-16T14-40-22Z found the
previous version **mandated roots outside the destination** — an external
target, an external workspace, `workspace_storage` outside the instance — which
contradicts OWNER-INSTANCE-DESTINATION-20260916.md and
OWNER-PYINSTALLER-20260916.md: *"it should literally produce a self contained
distro/db/repo so we can continue work in the repo while running jobs."* It also
carried a check block that **returned 0 when a read failed**, which is the worst
possible property for a check.

**Nothing here was run by the implementer.** Creating or cloning a repository is
a version-control mutation and this Work performs none. Every command is yours;
the reads are marked.

## Where each role lives — all under the destination

`<D>` is the destination you gave `just bootstrap`, e.g. `/srv/baton-v12`.

| Role | Path | Prepared by |
| --- | --- | --- |
| **target** — `integration_target`, the repository a reconciled result is imported into | `<D>/repo/target.git` | **you**, once |
| **workspace** — `integration_workspace`, integration's private preparation area | `<D>/repo/workspace` | **you**, once |
| **source** — each worker's `nominated_source` | `<D>/repo/source-<worker_id>` | **you**, once per worker |
| each worker's `workspace_storage` | `<D>/workers/<worker_id>/storage` | created by you, no repository |
| stores, logs, process records, the runtime | `<D>/db`, `<D>/logs`, `<D>/state`, `<D>/distro` | **derived** by `just bootstrap` |

`_prove_isolation` refuses if any two of target, workspace and a producer's
source/line turn out to be **one** repository. It compares the **repository**
identity (the resolved common directory, so a linked worktree or a symlink is
caught) and the **directory** identity (resolved device and inode, so an aliased
path is caught even where a repository tool cannot be asked). Three separate
clones under one destination satisfy that; a worktree of the target does not.

`just bootstrap` derives `integration_workspace = <D>/repo` when you do not name
one. **Name it explicitly as `<D>/repo/workspace`** — an explicit workspace is
supported, and it must be inside the destination or the bootstrap refuses. That
leaves `<D>/repo` as the folder holding all three repositories.

**What stays a parameter, not a fixture choice.** `<SOURCE>` (where your code
comes from) and `<BASE>` (the immutable base each Job declares) are production
selections. Nothing here picks them, and nothing here says a particular
repository is the right one.

## The order — every path exists BEFORE `just bootstrap`

**Not "either order".** The previous version said cloning afterwards was
simpler; review 2026-09-16T14-54-21Z showed it is not possible. `just bootstrap`
validates the configuration through `held_configuration` →
`single_worker._held` → `nominate_source`, which proves each worker's
`nominated_source` with an `lstat` and one `O_DIRECTORY | O_NOFOLLOW` open. A
source that does not exist yet is refused there, before an Authority is
composed — so the repositories come first.

Two further things `nominate_source` requires, because they are easy to get
wrong: the final component **must not be a symlink**, and the spelling you give
must already be the path the kernel resolves to — a symlinked *ancestor* looks
ordinary and is refused on the resolved path. Use real directories.

```sh
D=/srv/baton-v12

# 1. Everything the configuration names has to exist first.
mkdir -p "$D/repo" "$D/workers/impl-a/storage"

#    ONE clone creates the target from your source.
git clone --no-local --mirror <SOURCE> "$D/repo/target.git"

#    TWO further clones, each a SEPARATE repository -- not worktrees, not
#    hardlinked: --no-local forces an object-by-object copy, so each has its
#    own object store and its own common directory.
git clone --no-local "$D/repo/target.git" "$D/repo/workspace"
git clone --no-local "$D/repo/target.git" "$D/repo/source-impl-a"

# 2. The fail-closed check below, which only reads. Do not go on if it refuses.

# 3. THEN install the deployment. `just bootstrap` refuses a destination that
#    already holds a runtime or a selector; the repositories and worker roots
#    you just made are neither, and it leaves them alone.
cd /path/to/checkout/v12
just build
just bootstrap /path/to/inputs.json "$D" python/build/out/distro
```

Three clone commands create repositories and one `mkdir -p` creates the worker
root. Everything else in this file only reads.

## The check — fail-closed, and it exits non-zero when a read fails

The previous version compared the *output* of commands without checking they
succeeded, so a workspace that could not be stat-ed compared equal to nothing
and passed. Every read here is checked before it is used.

```sh
#!/usr/bin/env bash
set -euo pipefail                      # any unchecked failure ends the script
D=/srv/baton-v12
TARGET="$D/repo/target.git"
WORKSPACE="$D/repo/workspace"
SOURCES=("$D/repo/source-impl-a")      # every worker's nominated_source
BASE=<BASE>
REFERENCE=refs/heads/<REFERENCE>

fail () { echo "REFUSED: $*" >&2; exit 2; }

identity () {                          # the repository identity, CHECKED
  local answer
  answer="$(git -C "$1" rev-parse --path-format=absolute --git-common-dir)" \
    || fail "not a repository this profile can identify: $1"
  [ -n "$answer" ] || fail "empty common directory: $1"
  local resolved
  resolved="$(realpath -e "$answer")" || fail "common directory is absent: $1"
  [ -d "$resolved" ] || fail "common directory is not a directory: $1"
  printf '%s\n' "$resolved"
}

place () {                             # the directory identity, CHECKED
  local resolved
  resolved="$(realpath -e "$1")" || fail "path does not resolve: $1"
  stat -c '%d:%i' "$resolved" || fail "cannot stat: $1"
}

alternates () {                        # borrowed objects, in ANY of the three
  local common="$1"
  if [ -s "$common/objects/info/alternates" ]; then
    fail "borrows objects from elsewhere: $common"
  fi
}

TARGET_ID="$(identity "$TARGET")";        TARGET_PLACE="$(place "$TARGET")"
WORK_ID="$(identity "$WORKSPACE")";       WORK_PLACE="$(place "$WORKSPACE")"
alternates "$TARGET_ID"; alternates "$WORK_ID"

[ "$WORK_ID" != "$TARGET_ID" ] || fail "the workspace IS the target repository"
[ "$WORK_PLACE" != "$TARGET_PLACE" ] || fail "the workspace IS the target directory"

for one in "${SOURCES[@]}"; do
  ONE_ID="$(identity "$one")"; ONE_PLACE="$(place "$one")"
  alternates "$ONE_ID"
  [ "$ONE_ID" != "$TARGET_ID" ] || fail "a source shares the target repository: $one"
  [ "$ONE_ID" != "$WORK_ID" ]   || fail "a source shares the workspace repository: $one"
  [ "$ONE_PLACE" != "$TARGET_PLACE" ] || fail "a source IS the target directory: $one"
  [ "$ONE_PLACE" != "$WORK_PLACE" ]   || fail "a source IS the workspace directory: $one"
done

# The base you declare must be a commit IN the target, and the reference you
# import at must exist there.
git -C "$TARGET" cat-file -e "${BASE}^{commit}" \
  || fail "the declared base is not a commit in the target"
git -C "$TARGET" rev-parse --verify --quiet "$REFERENCE" >/dev/null \
  || fail "the import reference does not exist in the target"

# REPORTING, NOT A GUARANTEE: remotes are shown so you can see what the target
# is wired to. Having no remote is not the same as being unable to push, and
# nothing here claims it is -- push capability is your host's and your
# credentials', not a property this can check.
echo "-- target remotes (reporting only):"; git -C "$TARGET" remote -v
echo "-- target objects:"; git -C "$TARGET" count-objects -v

echo "OK: three distinct repositories under $D, base and reference present"
```

It exits 0 only when every read succeeded and every comparison held.

## What to put in the input document

```json
{
  "integration_target": "/srv/baton-v12/repo/target.git",
  "integration_workspace": "/srv/baton-v12/repo/workspace",
  "integration_target_reference": "refs/heads/<REFERENCE>",
  "integration_observer": "baton.<observer-participant>",
  "workers": [
    {"worker_id": "impl-a", "role": "implementation",
     "participant": "baton.impl-a",
     "deployment": {"nominated_source": "/srv/baton-v12/repo/source-impl-a",
                    "workspace_storage": "/srv/baton-v12/workers/impl-a/storage",
                    "credential_sources": "/home/<you>/.baton/credential-sources.json",
                    "…": "the rest of DEPLOYMENT.md's launch document"}}
  ],
  "jobs": [
    {"job_id": "…", "work_id": "…", "source_worker_id": "impl-a",
     "canonical_target_id": "<the target id this Job integrates into>",
     "line_declared_base": "<BASE>"}
  ]
}
```

`credential_sources` must be an absolute path to your own
`baton.user-credential-sources/1` registry: the bundled manager refuses to serve
without one, which is how this Work found that requirement. It is the one path
here that is deliberately **not** under the destination — it is yours, not the
deployment's.

## Checking it from the deployment itself

```sh
/srv/baton-v12/distro/baton-v12-stack repository --instance /srv/baton-v12/instance.json
```

Read-only; runs no repository tool. It prints the workspace and the target —
inside or outside this instance, present or absent, whether each carries a
repository layout, and the `HEAD` it holds — plus the configured reference and
every declared base, and says explicitly when a workspace is not a repository
yet and what that costs.

## What is still true of the retained instances

The two instances this Work installed and ran carry no `integration_target`,
reference or observer, and their `<D>/repo` is bound and **empty**. With any of
the three absent the deployment schedules and never reconciles: a valid state,
and not a prepared integration. Nothing in the retained evidence claims it is.

## Later owner interface ruling — 2026-09-16

OWNER-STANDALONE-INTERFACE-20260916.md supersedes public lifecycle JSON arguments
and manual pre-clone steps as the normal user workflow: bootstrap INPUTS
DESTINATION creates the complete deployment, including repositories and its
own justfile; deployed just start/status/monitor/stop resolve local instance.json.
Git mutation remains owner-only through the finished operator-run command.
Earlier technical isolation requirements and evidence remain applicable.
