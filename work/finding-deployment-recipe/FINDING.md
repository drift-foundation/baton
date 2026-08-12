# Baton has no deployment; the repository IS the deployment

Status: **deployment source signed off in
`review-2026-08-11T19-35-31Z.md`; actual 1.1 candidate publication, deployed
verification, and human soak remain release gates. No deployment or activation
has occurred. Production activation/permanent destination remain next-major
work.**

Captured by `baton.implementer` because no finding existed to pin the ruling
against. `baton.reviewer` owns this file from here; amend rather than defer to
it.

## Independent re-review — 2026-08-11

`review-2026-08-11T19-27-39Z.md` accepts the ruled command/payload and complete
manifest certification, but finds four remaining publication-integrity gaps:
the final operation is still replacing `rename` rather than atomic no-replace;
PID staging can delete an unexpected tree and cannot clean itself after 0555
hardening; `verify` ignores modes and follows a symlinked version root; and
only the staging root, not nested directory entries/final metadata, is fsynced.
The 1.1 candidate publish remains blocked pending correction and re-review.

## Independent re-review 3 — 2026-08-11

Deployment source is **signed off** in
`review-2026-08-11T19-35-31Z.md`. True atomic no-replace publication, uniquely
owned hardened-staging cleanup, exact mode/root verification, and recursive
post-hardening fsync all pass official and independent boundary tests. This is
source approval only: the current mixed next-generation/frozen-1.0 tree is
correctly undeployable, and no candidate may be published until coherent 1.1
artifacts/manifests/docs exist and the release umbrella authorizes the soak.

## Observed

There is no install, publish or deploy step anywhere in the project. `just`
offers `venv`, `test`, `build` and `build-tui` and nothing else, and neither
the README's Distribution section nor the protocol document describes copying a
release anywhere. Consequently every consumer today points into a working
git checkout:

    executable: /home/sl/src/baton/bin/baton
    human TUI:  /home/sl/src/baton/bin/baton-tui

That path is the 1.0.0 team announcement's own answer to "where is Baton", so
it is not a local habit — it is what the release told people to use.

## Why that is a problem now, and not before

While the repository only ever held released bytes, pointing at it was
harmless. Next-generation work ends that: the moment source moves ahead of the
released artifacts, the checkout contains one version's documentation, another
version's source, and possibly a rebuilt executable — and every team pointing
at `bin/baton` is pointing at whatever state a developer's tree happens to be
in. A checkout is a workspace; it changes under people who are not watching it.

This is the same class of hazard the release gate protects against inside the
repository, arriving from outside it.

## Confirmed direction

- There must be a real deployment recipe that installs or publishes the
  production tool tree (`bin/`, `docs/`, and whatever else a consumer needs)
  to a destination OUTSIDE the repository.
- The current `/home/sl/src/baton` release is the production deployment
  BASELINE: whatever the recipe produces must be equivalent to what teams use
  today, so nobody is broken by the transition.
- Next-generation builds deploy separately, under their own VERSIONED
  destination, with their own executable name and their own development
  authority and config.
- Teams keep pointing at a stable deployed path while next-gen is beta-tested
  elsewhere. Stability of the production path is the requirement; everything
  else is mechanism.
- Do not alter the current production deployment yet.

## Open questions, none of them mine to settle alone

1. **Destination layout.** A versioned directory plus a stable pointer is the
   conventional shape — `<root>/v1.0.0/…` with `<root>/current` resolving to
   it — because it makes "the stable path" and "which version am I running"
   two separate, answerable questions. Whether the stable pointer is a symlink,
   a copy, or simply what the team writes in its own policy is undecided.
2. **What a deployment contains.** `bin/` and the protocol document are
   certain. `docs/EFFECTIVE-BATON.md`, the README, `dist/` manifests, LICENSE
   and `examples/` are each defensible and none is obvious. The manifests
   argue strongly for inclusion: they are how a deployed tree can be verified
   after the fact.
3. **Verification.** A deployment that cannot be checked is a copy with
   ambitions. The manifests already pin `artifact_sha256`, so verifying a
   destination against them is nearly free, and a `verify` mode is worth as
   much as the install itself.
4. **Immutability.** A version directory should never be rewritten in place;
   a new release is a new directory. Whether the recipe REFUSES to overwrite,
   or requires an explicit force, is a real decision — refusing is what makes
   a deployed version trustworthy.
5. **The authority is not part of a deployment.** Config and SQLite live
   outside product trees and are supplied explicitly; the recipe must not
   create, carry, migrate or discover one. Next-gen's development authority is
   created separately by whoever runs the beta.
6. **The version number for next-gen.** The direction names `v1.0.1` as an
   example. Under the ruled `major.minor.patch`, console search is a FEATURE,
   which is a minor bump — `1.1.0` — and `1.0.1` would say "patch" about work
   that adds a key binding, a mode and a rendering change. Flagged rather than
   assumed: the number is Slawomir's to choose, and if he wants `1.0.1` the
   recipe does not care.

## Boundary

No protocol, schema, authority, message, claim or retention change. This is
packaging and operations only. The released 1.0.0 artifacts are inputs to the
recipe, never outputs of it: a deployment copies bytes that were already
certified, and never rebuilds them at the destination.

## Required evidence, when scheduled

1. Deploying into a fresh destination produces a tree a consumer can run with
   no repository present and no `PYTHONPATH`.
2. The deployed executables report the expected version and pass the packaged
   workflow smoke against a temporary authority.
3. Verification detects a tampered or truncated file in a deployed tree.
4. Deploying the same release twice is either refused or byte-identical, and
   which one it is, is a stated decision rather than an accident.
5. A next-gen deployment coexists with the production deployment: distinct
   versioned destination, the same product executable names, distinct
   authority, and neither observable from the other.
6. The repository's own `bin/` and `dist/` are untouched by deploying.

## Supersession — binary names in versioned deployments, 2026-08-11

The earlier confirmed-direction bullet saying a next-generation deployment has
“its own executable name” is **superseded**. Slawomir ruled that executables
keep the same product names in every versioned tree:

    <deploy-root>/v<version>/bin/baton
    <deploy-root>/v<version>/bin/baton-tui

The versioned path, reported version, separate development authority/config,
and absence of a stable `current` pointer to the beta provide isolation. Do not
rename either binary. This ruling changes no implemented deploy-tool behavior:
the recipe already copies the certified payload names as-is.

## Release payload ruling — 2026-08-11

The two open choices above are resolved: the next version is **1.1.0** and
`examples/baton.json` **does belong in the deployed payload**. The earlier
proposal excluding it because it looked like an authority is **superseded**.
It ships as an inert example/template; the deployment still creates, carries,
discovers, or activates no SQLite authority, and all real operations still
require an explicit external `--config` path.

The implemented `PAYLOAD` and packaging regressions still encode the old
exclusion and must be corrected before independent approval.

## Scheduling and destination supersession — 2026-08-11

This deployment is **not a 1.1.0 release gate**. Slawomir deferred installing
Baton outside its repository until the next major release. Preserve the recipe
and its evidence, but perform no publish or activation for 1.1.

The earlier `<deploy-root>/v<version>/` layout remains an implemented proposal,
not a ruled destination. The destination is open; the leading idea is:

    <mailbox-root>/bin/baton
    <mailbox-root>/bin/baton-tui

so an operational mailbox root contains the database/config and compatible
tools. These are co-located sibling responsibilities, not one payload. The
future deployer must still never copy, initialize, discover, or mutate the live
config/SQLite authority. Do not hard-code `/home/sl/src/mailbox` or discard the
versioned/immutable design until the next-major destination and upgrade model
are explicitly ruled.

## Candidate-soak scheduling supersession — 2026-08-11

Slawomir subsequently required a human-run 1.1 pre-release install in the
shape `just deploy DEST 1.1.0`, followed by a period of real use and separate
release clearance. This **supersedes only the blanket prohibition on a 1.1
external install**. It does not authorize `deploy-activate`, replacement of the
frozen repository artifacts, or selection of the permanent production root.

The existing immutable version-directory proposal is appropriate for this
candidate soak and must be independently reviewed, with the ruled
`examples/baton.json` payload correction, before Slawomir runs it. The candidate
may use the existing mailbox because both releases speak protocol 10; its
operations are real. The deployer still never carries, discovers, initializes,
or mutates that authority.

## Independent review state — 2026-08-11

`review-2026-08-11T16-55-31Z.md` requests changes before candidate use. The
implementation still lacks the ruled `just deploy DEST VERSION` interface and
example payload, hardcodes the 1.0 release note, ignores the manifest-pinned
protocol-document digest and cross-manifest protocol agreement, publishes
directly into the final version directory, leaves writable/followable paths,
and may remove unrelated activation staging/current entries. The existing
seven tests pass but encode the superseded example exclusion and omit these
failure boundaries.
