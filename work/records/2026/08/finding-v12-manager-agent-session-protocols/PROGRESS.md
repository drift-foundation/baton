# Implementer progress — agent-session and runtime adapter protocols

Created 2026-08-24 by `baton.claude` on claiming W6627.

## First claim, 2026-08-24: dossier and revalidation, no implementation

The canonical dossier was created and the frozen contracts revalidated against
the current tree. The revalidation produced three findings rather than a
confirmation, and all three are in `FINDING.md`:

1. **Three vocabularies, not one** — the runtime axis, the agent-session
   `sessionState`, and `posture`. Collapsing any two is the two-live-sources-
   of-truth defect, and this Job's own title invites exactly that collapse.
2. **The two runtime enums are deliberately asymmetric** — `execution_runtime`
   admits `start-requested`, `cancel-requested` and `stopping`;
   `consent_runtime` does not, because a consent container is never asked to
   start work or cancelled mid-turn. That is the M6617 topology, and tidying
   them into one enum would erase it while looking like a simplification.
3. **The Job is narrower than its title** — W4 already ships the runtime axes,
   their transitions and their journalled observations.

Nothing was implemented: `W6627 → W6592` was installed as the handoff
required, and W6592 was open with changes requested. Building against a guess
at where its public seam would land is precisely the second public boundary
that dependency exists to prevent.

## Second claim, 2026-08-25: the implementation

W6592 closed satisfying, so the seam is the accepted one and these protocols
consume it rather than defining a second.

**`schema.py` — two tables, and the store version moved with them (6 → 7).**
`agent_sessions` keyed by `(attempt, posture, epoch)`, with the posture binding
as a CHECK rather than a convention: a consent session carrying somebody's
generation is refused by the store, not by a comment. `posture_slots` keyed by
`(attempt, posture)`, naming which epoch it is about so evidence about one
epoch can never move the epoch that replaced it.

**`posture_slots.py` — occupancy as a manager-owned axis.** Taken by a
compare-and-set against `available` inside the transaction that writes the
session row, so the database decides concurrency rather than a read. Three
kinds of positive absence, each PROVED against what the store already holds
rather than against the caller's account of it — a closed vocabulary of labels
is not evidence, it is a closed vocabulary of claims.

**`sessions.py` — the axis, the adapter protocol, the lifecycle.** The frozen
nine and their §7.3 successors; opening with a fresh per-posture epoch, the
posture bindings and a reprojected live assignment; the §3.1 reference bound in
all four components at every observation; transport loss recording `unknown`
and moving the slot to `recovery-required` in ONE transaction; the two §8.4
refusals that always refuse; and `reconcile_agent_session`, which asks the
adapter and records what it answers.

**`attempts.py` — one added announcement, nothing reordered.** The session's
`cancel-requested` is recorded where the runtime axis's own announcement
already is, before the agent is asked. `attempt.cancelled` gained a fourth
member because a cancellation touches four axes and the session's was the one
a reader had to infer from its absence.

## What the acceptance asked for, and where each line is

- *Consent and execution session axes distinct, no collapsing of runtime,
  session and posture* — three vocabularies in three places, and each axis
  REFUSES the others' values. `TheAxisIsNotTheRuntime` asserts that as a
  property rather than leaving it to prose.
- *Certified typed observations including positive absence of a session as
  distinct from an absent runtime* — `SESSION_OBSERVATIONS`, and the
  `session-absent` evidence kind. `SessionAbsenceIsNotRuntimeAbsence` proves
  the distinction: it recovers the posture, it moves no observation, and it
  satisfies no runtime gate.
- *Effectively-once operation identities and restart reconciliation* — the
  opening identity derived from `(attempt, posture, intent)`, journalled
  through W4's own store; `reconcile_agent_session` for the session half.
- *Cancellation ordering preserved: fence, then agent, then runtime* —
  `CancellationAnnouncesTheSession` drives all four axes and asserts the fence
  still precedes both boundaries.
- *Public composition hooks on W6592's boundary, not beside it* —
  `certified_agent_session_profile` is what a session reads its per-posture
  policy from, and an uncertified digest opens nothing.

## Verification

`tests/manager/test_sessions.py` — **73 cases, all passing.**

The gates this package makes a new module pay, all extended rather than
exempted:

- the **boundary inventory**: every new receiving entry owned exactly once —
  30 delegated to a shared owner, 11 stated with a rule that is not the
  boundary layer — with **56 probes** driving the real exported operation and
  **5 witness cases** exercising the stated rules. Three of my own owners were
  corrected by that machinery: two labels with no literal part, and a
  `boundaries.generation` call that was both the wrong rule and unreachable.
- the **text sweep**: a row for every new exported callable, 15 of them.
- the **declared operands**: the thirteen names this slice adds, and NOT
  `connection` or `at` — the composition helpers that take a caller's
  transaction are private, so neither is a public operand.

    cd v12/python && just build
    # the locked, hash-enforced install: resolves, builds, installs, imports
    # from site-packages, and runs the whole suite from outside the tree
    # Ran 846 tests -- FAILED (failures=12, skipped=1)

## The gate is red, and it was red before this claim

**Twelve failures, and none of them is this slice's.** The baseline captured
before any edit is 13, every one naming `oci.py` or `workspaces.py` — W6632's
and W6631's modules. The after-list is that list MINUS ONE: `oci.py:run_vector`
now has a declared operand for `posture`, because this slice needed the same
name. Both lists are filed, so the claim is diffable rather than remembered:

    evidence/gate-baseline-2026-08-25.txt
    evidence/gate-after-2026-08-25.txt

This is reported as an operational finding rather than worked around. It is
not this Job's to fix, and it means "the gate is green" is not a sentence this
slice can honestly say.

## Not done, and named rather than rounded up

- **Turns, event normalization, agent-origin routing and the provider
  binding.** Not in the brief and not in the acceptance. The package's own
  header says so rather than leaving their absence to be discovered.
- **The frozen Node host does not have `session-absent`.** This slice added
  it because the acceptance requires the distinction and two evidence kinds
  cannot express it. The divergence is recorded in FINDING as a divergence,
  with the direction the host should move; it is not this Job's to change the
  host.
- **The 12 pre-existing failures.** Untouched.

## State

**Awaiting independent review.**
