# Instance 4 — the exact owner commands, in order (revision 4, corrected)

Prepared under owner **M361302**, which selects a **new revision destination
and a fresh workload** rather than an updated retained instance: no updater,
no migration gate, and instances 1, 2 and 3 preserved untouched. This
supersedes `../fresh4-361320/COMMANDS.md`, which is preserved, and answers
`review-2026-10-24T02-35-41Z.md`.

**What changed from the previous commands, and why.**

- **Selection 2b was wrong and would have failed.** It indexed
  `["preparation"]["workspace_storage"][0]` on
  `generated/preparation-readback.json`. That file is the preparation's own
  answer; `workspace_storage` is **top-level** and there is no `preparation`
  member. The corrected command is below, and `prove5.py` now runs **both**
  against the actually emitted document: the corrected one extracts the path,
  the previous one raises.
- **The declared base is now `614668e0…`**, matching the cloned revision.
  The previous documents declared `30245386…` while claiming `614668e0…` as
  the source. `30245386` is an ancestor so nothing would have failed, but it
  was two statements about one selection.
- **The source revision is now read, not labelled.** `fresh5.py` runs
  `git -C <source> rev-parse HEAD` — a read — and refuses a directory that is
  not a repository or is at another commit, before anything is minted.
- **The bundle that is verified is the bundle that is used.** Selecting a
  different bundle now requires stating the digest it must have.

**Nothing here was executed.** Instance 4 did not exist at this authoring and
does not exist now. Every check below is repeated by `fresh5.py` at the
eventual operation, and **each mutating step is a separate owner selection**.
All `sh` blocks pass `bash -n`; `evidence/SHELL-SYNTAX.txt` is the output.

## The operands

```sh
PKT=/home/sl/src/baton/work/records/2026/10/finding-v12-native-pilot-instance-packet/fresh5-361402
SRC=/home/sl/src/baton/v12/python
PY=/home/sl/.local/state/baton-v12-venv/bin/python
D=/home/sl/baton-instances/native-coordination-pilot-w321608-4
DISTRO=/home/sl/w325959-bundle/out/distro
RSRC=/home/sl/src/baton
```

`DISTRO` is the bundle pinned by `../bundle-361217/`: built from
`614668e0831e8c87cdae11ca43620e0d544a84d5`, **81 files**, folder digest
`1b014603aec40e9f6d9c03a8b21ae74a02d9f1fef1ff95fc0f3e8a851a229c07`,
executable `f4e9cecf0ccb7211b5c36691a35d8499cff94c7e64f1aff18c36bb50b13206d3`.
Confirm it before selection 2 — these are reads:

```sh
test -x "$DISTRO/baton-v12-stack" || echo "NOT THE BUNDLE: $DISTRO"
"$DISTRO/baton-v12-stack" identity
```

It must answer `frozen: true`, both frozen schema assets, a `native_rpds`
inside the bundle's own `_internal`, and `build_stamp.commit`
`614668e0…`. **It answers `dirty: true`**, and that is expected and
disclosed: the v12 subtree is byte-identical to the commit and the dirt is
records outside `v12/`. `fresh5.py` recomputes the digest of **whichever
bundle is selected** through the product's own `instance.manifest` and
refuses anything but the pin above, so a different bundle cannot be installed
by accident — and selecting one deliberately requires `--bundle-digest`.

`RSRC` must be at `614668e0…`. This is a read; confirm it yourself if you
like, and `fresh5.py` does it again before minting anything:

```sh
git -C "$RSRC" rev-parse HEAD
```

## Selection 1 — preparation preflight (writes nothing)

```sh
cd "$SRC" && PYTHONPATH=src:. "$PY" "$PKT/fresh5.py" \
    --destination "$D" --packet "$PKT" \
    --bundle "$DISTRO" --repository-source "$RSRC"
```

Read-only. It checks everything knowable before anything is minted: the four
packet documents hash to the **literal** digests reviewed with `fresh5.py`,
so an edit made after review refuses here; the imported
`fresh3-358443/fresh.py`, its own imported `post-install-357462/configure.py`
and the inherited documents hash to their pins; the selected bundle
recomputes to the expected digest; the selected source **is** a repository
and **is** at `614668e0…`; **no consumed path lies inside instance 1, 2 or
3**; the destination is free; and the whole manifest/submission
cross-binding is rehearsed against a deliberately provisional authority so a
sealing fault refuses here rather than after a destination exists.

It answers `source.commit`, and `bundle.digest` for the bundle it would
actually install. Both are worth reading before selection 2.

## Selection 2 — mint, compose and install

```sh
cd "$SRC" && PYTHONPATH=src:. "$PY" "$PKT/fresh5.py" \
    --destination "$D" --packet "$PKT" \
    --bundle "$DISTRO" --repository-source "$RSRC" --owner-selected
```

This performs the four supported steps in the resolved order: mint the
authority from a document carrying no workers and no jobs; read the minted
uuid back from `authority-identity.json`; compose the Work as
`<uuid[:8]>-W1` and seal the manifest and task against it; then one supported
`bootstrap` call that creates the four repositories, the Work, the
configuration and the selector.

**Expected readbacks.** `authority_uuid` is 32 hex characters and is *this*
instance's — never `5a8fa4b4…`, which is instance 3's. `work` is
`<uuid[:8]>-W1`. `installed_workers` is `["implementation", "review"]`,
`installed_job_bindings` is 1, `repositories` has four entries, and
`task_digest` describes the emitted task bytes. The run writes
`generated/preparation-readback.json`; **preserve it**.

A second run of this command against the same destination **refuses** and
changes nothing. Report a mismatch rather than re-running.

## Selection 2b — the workspace storage prerequisite

The preparation derives and bounds `workspace_storage` but does not create
it, and the consumer refuses a place it cannot see. Create it as the owning
user after selection 2, reading the path from the readback rather than
assuming it. **`workspace_storage` is top-level in that document** — this is
the command the previous packet got wrong:

```sh
WS=$("$PY" -c 'import json,sys;print(json.load(open(sys.argv[1]))["workspace_storage"][0])' "$D/generated/preparation-readback.json")
mkdir -p "$WS" && ls -ld "$WS"
```

`$WS` is inside `$D` — expect `.../state/workspaces`. If it prints a path
outside the destination, stop and report rather than creating it.

## Selection 3 — submission (a separate decision)

```sh
A=$("$PY" -c 'import json,sys;print(json.load(open(sys.argv[1]))["authority_uuid"])' "$D/authority-identity.json")
"$D/distro/baton-v12-stack" manager --store "$D/db/jobs.sqlite3" \
    --incarnation w325959-owner-submit-4 --authority-uuid "$A" \
    submit --document "$D/generated/submission.json"
```

One submission, `sub-w321608-quickstart-4`, carrying Job `quickstart-d` with
an implementation stage and a review stage gated on it, at **3600s provider /
900s verification per invocation**. There is no second submit.

## Selection 4 — serving, observation and stop (separate decisions)

```sh
"$D/distro/baton-v12-stack" start --instance "$D/instance.json"
"$D/distro/baton-v12-stack" monitor --instance "$D/instance.json"
"$D/distro/baton-v12-stack" manager --store "$D/db/jobs.sqlite3" \
    --incarnation w325959-owner-observe-4 --authority-uuid "$A" \
    status --control "$D/db/control.sqlite3"
"$D/distro/baton-v12-stack" stop --instance "$D/instance.json"
```

`monitor` blocks; invoke `stop` separately rather than treating the block as
an unattended script. **This is the point at which a live provider turn
happens**, and nothing in this packet proves it will succeed — see below.

## Restart checkpoints

- **Interrupted during selection 2.** Do not delete the destination and do not
  re-run blindly. Inspect it and report: the preparation refuses an occupied
  destination by design, and an interrupted install is state to be looked at,
  not cleaned up by an agent.
- **Interrupted after selection 3.** The submission is journalled by its own
  identity, so an exact re-run replays rather than submitting twice.
- **If `quickstart-d`'s implementation fails** — the credential expiry that
  ended `quickstart-c`, or anything else — this build has the supported retry
  that `quickstart-c` did not:

```sh
"$D/distro/baton-v12-stack" manager --store "$D/db/jobs.sqlite3" \
    --incarnation w325959-owner-retry-4 --authority-uuid "$A" \
    fresh-attempt --prior-job quickstart-d --control "$D/db/control.sqlite3" \
    --authority "$D/db/authority.sqlite3" --instance "$D"
```

It derives `quickstart-d-retry-2`, reuses this instance's Work, performs the
admission and the additive binding itself, and refuses unless the prior
runtime ceased and its resource returned. An exact re-run is the replay path;
keep the incarnation if it is interrupted while incomplete.

## What this packet does not establish

- **No live provider or credential result.** Selection 4 is where
  authentication is actually exercised; deterministic proof covers
  composition and admission, not a provider response.
- **The proof's apply is disposable**, with a simulated repository runner and
  a stub bundle. Real clones, the real runtime and a real turn are the
  owner's selections above.
- **The bundle's build stamp is `dirty`**, as disclosed in
  `../bundle-361217/BUNDLE.md`.
- **Selections 3 and 4 were not re-proved by this revision.** They are
  unchanged from `fresh4-361320` apart from the packet path; the corrections
  here are to the preparation, its pins and selection 2b.
