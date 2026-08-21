# baton-v12-poc — disposable Claude ACP natural-dispatch proof

**Disposable** proof of concept for Baton Work `W76`
(`baton:work/records/2026/08/finding-v12-isolated-agent-workers/findings/finding-v12-claude-acp-dispatch-poc`),
living in this repository as the self-contained `v12/` subtree
(`.../findings/finding-v12-in-repository-migration`).

This is **not Baton product source** and carries no compatibility promise.
Nothing here is adopted Baton code, nothing in the v11 product imports
it, no v11 recipe delegates to it, and the v11 distribution does not
package it. It exists to answer one question:

> Can an operator submit an ordinary Baton Job and have a trusted Worker
> Manager naturally dispatch it to one isolated Claude ACP worker —
> obtaining explicit consent, committing the canonical claim before any
> writable execution, materializing typed input, collecting a declared
> output, and returning the Job for review — without launching or
> prompting Claude for that individual Job?

The answer, with evidence, is in the bound dossier's `PROGRESS.md`.

## Running it

    just install          # or: npm ci
    just test             # the fail-closed unit and placement gate
    just proof <label>    # the whole live proof

`v12/` has its own `justfile` and its own `package.json`; nothing here is
reachable from the root gate and nothing here reaches into it.

The proof is the whole thing: fresh disposable authority, unit tests,
happy path, both negative fencing cases, the post-claim compensation
case, and every assertion. It exits nonzero the moment an assertion
fails.

Prerequisites are printed at the top of every run: Docker, Node ≥ 20, the
deployed v11 Baton executable, and the `claude-agent-acp` adapter tree
with a readable Claude OAuth credential.

## Where state lives

Everything disposable — the authority and its SQLite file, the Job
records, per-attempt directories, staged credentials, and the evidence
pack a run generates — is written under the ONE external
`state_root` named in `poc.json`, and `just state-clean` removes all of
it. Nothing disposable is written inside this checkout.

That is not tidiness. This prototype lives inside the Baton source tree,
and its runtime fence refuses to mount any path inside that tree into a
worker container — a W76 boundary, not something to relax because the
source moved. So the state moved instead.

`src/placement.mjs` is the one authority for that, and every entry point
that creates or removes state — the proof runner, `new-authority.sh`,
`just state-clean`, and configuration validation — asks it BEFORE its
first mutation, and then acts on the paths it RETURNS rather than on the
ones it was handed. It refuses a `state_root` that overlaps the Baton
checkout in either direction, that is a filesystem-wide or top-level
directory, or that contains the home directory; it refuses any created
or removed path that is not a strict descendant of that root; and it
refuses an evidence label that is not one safe path component. It
creates and deletes nothing itself, and it is not the security
boundary — `assertNoBatonCapability` remains the canonicalized
launch-time fence for what a container may mount.

**Deleting the root needs proof that the root is ours.** Path shape
cannot supply that: `/var/log` and `/usr/local` satisfy any denylist and
any depth rule, and a typo can reach either. So the state root carries a
`.v12-poc-state-root` marker naming *itself*, written by the recipe that
creates the root, and `just state-clean` removes an existing directory
only when that marker is there and names that exact path. A directory
that predates the marker, or one a marker was copied into, refuses and
stays exactly as it is — remove it yourself, deliberately, or point
`state_root` somewhere that does not exist yet.

An ABSENT root refuses cleanup too, and prints no path. "Nothing is
there right now" is a fact about this instant, not about ownership:
the value would go straight to `rm -rf`, and anything could create an
unrelated directory at that path in between. Setup still accepts an
absent root — creating it is how ownership is established.

A generated evidence pack becomes *retained* evidence only when somebody
copies it into `evidence/<label>/`. The packs already there are the
reviewed history and are never regenerated in place.

## Shape

| Path | What it is |
| --- | --- |
| `bin/v12-poc` | `submit` (operator), `manage` (Worker Manager), `snapshot` |
| `src/manager.mjs` | the orchestrator — the only thing that touches Baton |
| `src/baton_cli.mjs` | black-box CLI/JSON client for the deployed executable |
| `src/claim_token.mjs` | the claim fence: short-lived, single-use, bound |
| `src/acp_session.mjs` | one ACP session against one container |
| `src/container.mjs` | explicit mounts, identity and termination evidence |
| `src/runtime.mjs` | per-attempt isolation, credential staging, container specs |
| `src/envelopes.mjs` | the draft `0-spike` JSON contracts |
| `src/fixture_check.mjs` | the transformation rule and its independent checker |
| `src/input_source.mjs` | containment of the untrusted input descriptor |
| `src/manifest.mjs` | digests, manifests and containment |
| `src/placement.mjs` | where disposable state may be created and removed |
| `src/trace.mjs` | the append-only chronological trace, with secret scrubbing |
| `scripts/new-authority.sh` | a disposable authority; its operands must BE the configured plan |
| `scripts/run-proof.sh` | the whole proof, with assertions |
| `justfile` | this subtree's own recipes; the root gate does not call them |
| `PROVENANCE.md` | what was copied from Baton v11, and how it was changed |

Everything in this directory is reviewed source, fixtures or retained
evidence. Disposable state lives under the external `state_root`, and
`node_modules/` is resolved from the pinned lockfile and ignored.

## Boundaries this prototype keeps

- This prototype is in the Baton repository, and is still not part of
  it: it imports no v11 product module, modifies no v11 source, adds no
  root recipe, and is not packaged by the v11 deployer. Its own gate
  runs from this directory alone.
- No worker ever receives a path inside the Baton checkout — this
  subtree included. The fence canonicalizes both sides and refuses
  before launch, and a proof run asserts afterwards that no disposable
  state was written into the checkout either.
- The deployed v11 executable is used only as a documented CLI/JSON
  client. No SQLite file is ever opened, by this code or by any model.
- Only the manager holds Baton access. No container receives the Baton
  executable, config or database, so no worker has any coordination
  capability at all.
- Consent runs in a **non-executing** `plan` ACP posture, on a read-only
  root filesystem with all capabilities dropped, with no copy of the
  Job's input and nowhere to write a result. It performs zero tool
  calls. Two residuals are not claimed away: the credential bind is
  writable because the Claude SDK requires it, and network egress to the
  model provider exists because a model turn needs it. So the property
  is: **a consent turn holds no Baton capability, touches no Job input
  or output, and cannot produce an accepted result or an assignment.**
- Nothing writable starts until the canonical claim has committed.
- Every agent turn carries an explicit manager deadline. Setup
  supervision is not turn supervision: a live but silent agent would
  otherwise hold the canonical Handler for as long as it stayed quiet.
- A container is *proven* stopped before its output is read; a fence
  that cannot be established ends the attempt rather than being recorded
  and stepped over.
- Before a claim is released, every execution container is *proven gone*.
  If that cannot be established the claim is deliberately kept and the
  attempt reports `stranded` — advertising Work whose old worker may
  still be running is the overlap the claim boundary exists to prevent.
- A Job's typed input descriptor is contained inside its bound record —
  lexically and by real path — and copied without following links.
- Container mount sources are canonicalized before the no-Baton-capability
  check, so a source that is merely a symlink to Baton state is refused
  rather than passing a string comparison.
- If anything fails *after* the claim, the manager releases it, so the
  Job returns to being offerable instead of stranding the Handler.
