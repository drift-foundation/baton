# W325959 — the source-pinned bundle, and the update gap it cannot close

Preparation under `review-2026-10-24T02-09-29Z.md`, claim361217. **Nothing was
installed, deployed, started, stopped, submitted or retried.** The retained
instance was read only as the ordinary JSON documents it publishes about
itself; no store under its `db/` was opened, copied, traversed or hashed, and
no supported command was run against it.

## 1. The bundle, and exactly what it was built from

Built with the repository's own `packaging/stack.spec` and the locked
toolchain, to a path **outside the checkout** so the stale September build
under `v12/python/build/out` was left alone.

| | |
| --- | --- |
| built from | `614668e0831e8c87cdae11ca43620e0d544a84d5` |
| built at | `/home/sl/w325959-bundle/out/distro` |
| whole-folder digest | `1b014603aec40e9f6d9c03a8b21ae74a02d9f1fef1ff95fc0f3e8a851a229c07` |
| files | 81 |
| executable sha256 | `f4e9cecf0ccb7211b5c36691a35d8499cff94c7e64f1aff18c36bb50b13206d3` |
| version | `12.0.0`, Python 3.13.7, Linux-6.17.0-41-generic x86_64 |
| native validator | `_internal/rpds/rpds.cpython-313-x86_64-linux-gnu.so` |
| frozen schema assets | `worker-control-1.0` 51419, `agent-session-1.0` 48212 |

The folder digest is computed by the product's own `tools.instance.manifest`
— the same reader `instance.verify` uses — rather than by a hash this packet
invented.

**The build stamp says `dirty: true`, and that needs saying plainly.** It
records 383 changed entries. **None of them is under `v12/`**:
`git status --porcelain --untracked-files=normal` lists zero paths there, so
the v12 subtree this bundle was built from is byte-identical to the commit.
The dirty flag comes from `AGENTS.md` and the `work/records` dossiers — the
records this very turn is writing. An installed build reporting `dirty` is a
true statement about the tree it came from and should not be explained away;
if the owner wants a clean stamp, the bundle must be rebuilt from a clean
checkout, and that is a separate selectable act.

**Toolchain provenance.** `pyinstaller==6.16.0`,
`pyinstaller-hooks-contrib==2026.7`, `altgraph==0.17.5`, `packaging==26.3`,
`setuptools==84.0.0` — each matching `requirements.build.lock` exactly. The
locked install step was **not** re-run (it needs the network); the already
prepared interpreter was used and its versions compared against the lock
instead. If the owner wants the hash-checked install performed as part of the
build, that is a separately selectable command on a host with network access.

## 2. The six extra committed paths

The commit carries 21 paths. Six are outside the retry signoff, and they are
W321776's declared-verification-context work:

- `v12/python/src/baton_v12/verification_context.py` — **imported by nothing
  in `src/` or `tools/`.** It travels inside the bundle as part of the
  package and changes no stack behaviour.
- `v12/worker/Dockerfile.claude` and `v12/.dockerignore` — a new `COPY` of
  that module into the **worker image**, and the allowlist entry the build
  context needs for it. These are not part of the stack bundle at all; they
  describe a worker image that **has not been built here**.
- `v12/python/tests/manager/test_verification_context.py` and
  `test_claude_agent.py` — 337 cases, run once this claim: **OK**. That is an
  accounting of their state, not an acceptance of W321776, which is not this
  Work's to give.
- `v12/DESIGN.md` — REC-7 itself, already the authority for this work.

**What this means for the retained pilot:** the retained task
`w321608-native-operator-quickstart-3.json` is a `baton.dogfood-task/2`
document. The verification-context layer is a `/3` concern, so the retained
image and profile remain compatible with the unchanged task, and **no new
worker image is required to re-attempt it**. A `/3` task would be a different
question and is not this pilot's.

## 3. Compatibility with the retained instance

`compatibility.py`, 27 checks, zero failures, 0.6s — `evidence/COMPATIBILITY.json`.

**Its published documents still parse under this build.** `deployment.json`
is accepted by `stage_execution.held_configuration`; `install-inputs.json` is
accepted by `bootstrap.held`. Both were read as files; neither store beside
them was touched.

**The Job store format.** This build is schema 8 and the retained store is 7,
so an updated deployment would migrate it on first write-open. A **disposable**
schema-7 store carrying a quickstart-shaped failed two-stage Job — built from
this build's own `SCHEMA` minus exactly what the 7→8 step creates, which is
how `test_store` and `test_execution_limits` impersonate older stores — was
migrated and compared row by row: `submissions`, `jobs`,
`job_execution_limits`, `stages` and `episodes` are **byte-identical across
the migration**, every prior `operations` row survives, and `fresh_attempts`
exists afterwards and is empty. This is a **format fixture and not the
retained store**, which was never opened.

## 4. The update gap, measured

No supported procedure updates a retained instance's runtime. Three facts,
each driven against a disposable destination rather than read off the source:

1. `bootstrap.custody` refuses a destination that already holds a runtime —
   *"nothing here upgrades a deployment in place. Stop that instance and
   prepare a new destination if you mean a different runtime."*
2. `instance.verify` refuses when the folder's recomputed digest is not the
   one the selector records. Driven against **this real bundle**: it holds 81
   files digesting `1b014603…` and the probe's record named another.
3. **`instance.verify` ACCEPTS this bundle the moment the record names it.**
   So the obstacle is the *recorded selector*, not the runtime.

The retained instance records runtime digest
`3dbc610e0c2a0e1165367871097bd2a5bb590e271fee729b94b436a04045e7ac` (81 files)
and command
`/home/sl/baton-instances/native-coordination-pilot-w321608-3/distro/baton-v12-stack`.

**Where the capability stops.** `tools/instance.py` already has `publish`,
documented as *"how an instance's own selector is rewritten in place"* — and
**nothing calls it**. `bootstrap.install` uses `instance.create`, which
refuses to replace. The `instance` CLI exposes only read questions. So the
supported surface is one unused function short of being able to retire a
runtime and name a new one, and DEP-1 forbids rewriting an old deployment in
place by any other means.

### The smallest concrete owner decision

**Not implemented here, and this packet does not authorize implementing it.**

> Authorize a bounded `instance update-runtime` operation: given a stopped
> instance and a new bundle, verify the new folder through
> `instance.manifest`, require the recorded authority, stores, state root,
> deployment configuration and every other selector member to be carried
> forward unchanged, and republish **only** `runtime` and `command` through
> the existing `instance.publish`. It installs nothing, copies no store,
> mints no authority and touches no Job.

That keeps DEP-1's prohibition on rewriting a deployment in place honest by
making the runtime swap an explicit, bounded, reviewed operation rather than
a side effect, and it satisfies DEP-3 because the store migration is the
product's own and is evidenced above.

**The alternative, if the owner prefers not to add a capability:** prepare a
fresh destination with this bundle and carry nothing over. That abandons
`quickstart-c`, its Work, its evidence and its bindings — which is the thing
this pilot exists to preserve — so it is recorded as the option it is rather
than recommended.

## What remains unavailable or unproved

- **No worker image was built.** The Dockerfile change is accounted for and
  shown not to be required by the retained `/2` task; building an image is a
  separate selectable act needing an engine.
- **No deployment, no live retry, no credential check.** Whether the retained
  instance can actually run the bounded retry with refreshed authentication is
  still a live-provider question this packet does not answer.
- **The bundle is host-specific** and reports itself so; it is built for this
  host's platform and claims no portability.
- **The dirty build stamp** stands as recorded above.
