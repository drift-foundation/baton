# Evidence packs

Each pack is produced end to end by `scripts/run-proof.sh <label>` and is
never hand-edited. Packs are grouped by review round, and **earlier packs
are kept rather than replaced**: they are the evidence for observations
recorded in `PROGRESS.md`, and deleting them would leave those claims
unsupported.

A run WRITES its pack under the external `state_root` in `poc.json`,
together with the rest of its disposable state. A pack becomes retained
evidence when somebody copies it into this directory — which is what
makes retention a decision rather than a side effect. Packs from before
the in-repository migration name the retired external prototype root in
their recorded paths; that is history and is left exactly as it was
produced.

Read `proof-r12-standalone` for the current state of the prototype.

## Standalone — after the external root was removed

`proof-r12-standalone`

The first pack produced with only ONE prototype tree on the host. Round
five accepted the migration, and the external root
`/home/sl/src/baton-v12-poc` was then removed as the final recorded step.
This run is the verification that the in-repository copy needs nothing
from it: fresh disposable authority, 78 unit tests, the happy path, both
token fences, the post-claim compensation, credential disposal, and the
whole-checkout walk — all from `v12/` alone.

Packs before this one name the retired external root in their recorded
paths. That is history, and it is left exactly as it was produced.

## Placement round 5 — after `review-2026-08-21T06-33-08Z.md`

`proof-r11-fixture`

No production behaviour changed between this pack and `proof-r10-absent-root`.
What changed is the regression that guards it: the absent-root case used
to establish its precondition by recursively removing a FIXED path, which
is the hazard it exists to prevent. Its candidate is now a child of a
parent the test creates and that has never been created, so the absence
is a fact rather than something deleted into being, and the only thing
removed is that parent.

## Placement round 4 — after `review-2026-08-21T06-08-14Z.md`

`proof-r10-absent-root`

Produced after the deletion path stopped answering for a root that does
not exist. The run itself is the round-nine run again — the correction
is a refusal, not a behaviour change — and what this pack adds is that
the whole cycle was exercised against it: `just state-clean` removed the
owned root, a second `state-clean` refused the now-absent one and
printed no path, and this run re-established ownership from nothing.

## Placement round 3 — after `review-2026-08-21T05-34-21Z.md`

`proof-r9-ownership`

The first pack produced after root deletion started requiring positive
ownership evidence. What this pack shows that `proof-r8-placement` does
not:

- the run established the state root's `.v12-poc-state-root` marker
  before writing anything under it. An existing root without that marker
  is refused rather than adopted, which is what now stands between a
  mistyped `state_root` and `rm -rf`;
- `new-authority.sh` acts on the authority and record-base values the
  configured plan RETURNS, not on the operands it was handed. A
  descendant of the state root is no longer automatically a legal
  target — the retained evidence and the attempt state are descendants
  too.

## Placement round 2 — after `review-2026-08-21T05-09-14Z.md`

`proof-r8-placement`

The first pack produced with every state-creating and state-deleting
entry point going through one fail-closed placement authority
(`src/placement.mjs`), which creates and deletes nothing itself. What
this pack shows that `proof-r7-migration` does not:

- the runner's disposable paths come from a VALIDATED plan, computed
  before its first `rm -rf`. A traversal evidence label, a
  filesystem-wide state root, an out-of-root authority or record base
  now refuse the run before anything is created or removed;
- externality is asserted against the WHOLE Baton checkout rather than
  the `v12/` subtree, so a sibling of `v12/` inside the checkout is
  refused too;
- the closing stray-state walk covers the whole checkout, not just the
  prototype subtree — "the state root is external" is a claim about the
  repository, and this pack is the first to check it as one.

## Migration — after the move into this repository

`proof-r7-migration`

The first pack produced with the prototype living inside the Baton
checkout as `v12/`. Nothing about the assignment lifecycle changed, and
the round-6 corrections are all still in force. What this pack shows that
the round-6 packs do not:

- every disposable path is EXTERNAL. `prerequisites.txt` records the
  state root, and the run's authority, Job records, attempt directories,
  staged credentials and this pack itself were written under it;
- the capability fence was not relaxed to accommodate the move. Its
  forbidden set still names the whole Baton checkout, which now contains
  the prototype, and the per-container mount assertions are checked
  against that checkout path rather than a hard-coded literal;
- the runner asserts, after the fact, that the prototype subtree holds no
  authority, Job record, attempt state or credential — a check the
  repository-status comparison cannot make, because an untracked subtree
  looks identical before and after whatever is written inside it.

## Round 6 — after `review-2026-08-21T00-38-29Z.md`

`proof-r6-1`, `proof-r6-2`

Two ambiguity paths in the authoritative return/compensation boundary:

- the recap `say` is now **effectively-once**. It carried an operation
  id that nobody replayed, so a recap that committed and lost its result
  threw before the pass, compensated an already-complete assignment, and
  put the Job back on the queue for a second execution with a duplicate
  recap to follow. It is now replayed and, failing that, settled from
  the thread itself;
- `pass` and `release` reconciliation now asks whether **this manager's
  claim** is gone, not whether nobody has claimed since. A legitimate
  successor claiming immediately after the mutation committed used to
  look like evidence the mutation had not happened.

## Round 5 — after `review-2026-08-20T23-56-14Z.md`

`proof-r5-1`, `proof-r5-2`

Three further corrections. What these packs show that round 4's do not:

- **cleanup happens before the handoff.** Disposal is now part of the
  success boundary, asserted as `credential.disposed` preceding
  `baton.pass`. Round 4 disposed *after* the Job reached review, so an
  attempt could return cleanly with the operator's credential still on
  disk;
- a retained credential produces the distinct terminal state
  `returned-unclean`, surfaced in the CLI result and exiting non-zero,
  rather than a trace line under a clean success;
- the compensating `release` carries an operation identity and
  reconciles an ambiguous result, as `claim` and `pass` already did;
- the capability fence names the live Baton checkout and the
  `/home/sl/baton-v11` alias, so a mount into either is refused *before*
  launch instead of being noticed afterwards.

## Round 4 — after `review-2026-08-20T23-30-47Z.md`

`proof-r4-1`, `proof-r4-2`

Four further corrections. What these packs show that round 3's do not:

- **no staged credential survives.** Round 3's packs left a complete
  mode-0600 copy of the operator's OAuth credential — refresh token
  included — under `run/attempts/*/claude-config/` on every path. The
  runner now asserts the RUNTIME state, not just the sanitized evidence
  pack, which is where the secrets actually were;
- disposal happens only once every container that mounts the credential
  is proven absent, and an unprovable reap retains it *loudly* rather
  than claiming cleanup;
- the production-authority guard compares real paths, so the live
  `/home/sl/baton-v11` symlink and any link resolving into a production
  home are refused;
- an ambiguous `claim` or `pass` — committed, result lost — is
  reconciled through the public projection instead of being reported
  under the wrong state;
- containers launch with the canonical mount source that was validated,
  not the mutable alias.

## Round 3 — after `review-2026-08-20T21-07-20Z.md`

`proof-r3-1`, `proof-r3-2`

Four further corrections. What these packs show that round 2's do not:

- the declared result is the **directory** the finding pinned (`/out`,
  declaring exactly `index.json`), not a file;
- every container is removed **and proven gone**, recorded as
  `containers.reaped`, and the post-claim case asserts that proof
  happens *before* the claim is released;
- both agent turns carry an explicit manager deadline, so a live but
  silent agent can no longer hold the canonical Handler;
- container mount sources are canonicalized before the
  no-Baton-capability check.

The final repository check also changed shape. It used to assert the
whole Baton tree was clean; this checkout now carries unrelated
in-flight Work, and a status listing records that a path changed, never
who changed it. So the runner proves what it can — that the run mutates
nothing — and reports the rest verbatim rather than asserting authorship
it cannot establish.

## Round 2 — after `review-2026-08-20T19-57-54Z.md`

`proof-r2-1`, `proof-r2-2`

The five trust-boundary corrections are in force. What these packs show
that round 1's do not:

- the consent turn runs in the non-executing `plan` posture on a
  read-only root filesystem with all capabilities dropped, and performs
  **zero tool calls**, while the worker performs ~20;
- both fences are *established* rather than recorded — a quiescence that
  cannot be proven now ends the attempt;
- the typed input is materialized without following any link;
- the worker's `job.out` declaration is bound to its assignment and to
  the offered outputs;
- a third negative case: an injected **post-claim** fault releases the
  claim and returns the Job to `queued`/unclaimed/ready, instead of
  stranding the canonical Handler.

## Round 1 — as first submitted for review

`proof-1`, `proof-2`, `proof-3`, `proof-4`

These four runs established that the happy lifecycle completes and that
the expired/replayed token fences hold. Independent review then found
five trust-boundary gaps that these packs do **not** establish — see the
review and the responses in `PROGRESS.md`. Read them as history, not as
a description of the current prototype: in particular their consent
turns ran in `bypassPermissions` with full tool access, which is exactly
what round 2 corrects.

`proof-1` through `proof-3` also span the claim-token contract change:
`proof-1` and `proof-2` used the 402-character signed-payload token, and
`proof-2`'s first attempt is the run in which a model miscopied one and
the attempt was refused as `forged`. `proof-3` onward use the
39-character opaque handle.
