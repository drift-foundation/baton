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

## The interrogation split — implemented and verified — 2026-08-25

The review's blocking finding is addressed. `probe` and `inquire` are two
operations over one journalled lifecycle, and the required re-review evidence
is in `tests/manager/test_interrogation.py` (51 cases): positive and negative
shapes for both, replay and operation collision, restart between enqueue,
delivery, answer, journal and Baton publication, manager deadline expiry
without cancellation, the `adapter-unreachable`/`runtime-absent` distinction,
answer correlation and safe-turn delivery, and the proof that no worker
receives a Baton or SQLite capability.

Four gates were re-derived rather than asserted, and two of them found real
defects — a dead `_kind` validator and a doubled capability check on the
authority port. Both are deleted; neither was exempted.

    cd v12/python && PYTHONPATH=src python3 -m unittest discover -s tests -t .
    # Ran 1053 tests -- FAILED (failures=16, skipped=1)

    cd v12/python && just build
    # the same 16 from the INSTALLED layout, outside the source tree

The delta against the recorded baseline is in
`evidence/gate-after-interrogation-2026-08-25.txt`. **Nothing was added to the
red baseline by this claim.** One baseline failure went away because commit
0b7b8ac landed mid-claim and declared an operand this slice also needed; four
new failures are reviewer-authored cases on W6630 and W6633, Work this
participant has already passed back, and they are reported rather than fixed.

## State

**Awaiting independent re-review.** The claim is not released and no Git
operation was performed.

## Second re-review correction — 2026-08-25

All three [P1]s are corrected and all three of the review's additive
regressions are green and kept as written.

**Wall time is not a caller operand.** `_ask` signed the derived absolute
deadline, so the same identity with the same operands collided with its own
journalled request whenever the manager's clock had moved — precisely the
ordinary restart the durable journal exists to survive. The signature carries
the duration the caller asked for; the absolute deadline stays the operation's
committed result, so the manager's first observation is what every later
caller sees and the second caller's clock decides nothing.

**The observation is durable.** It was an argument that reached the answer and
never the row, so an `observed` outcome survived a restart with nothing
observed in it — the whole content of the operation missing from the only copy
that lasts. There is a column now, written in the same statement as the
transition, with the pairing stated both ways as CHECKs and refused in this
build's own vocabulary first. `_view` takes no observation argument any more:
what a view says is what the row holds.

**The observation is typed.** `alternative` closes member names and
deliberately does not own their values, so a runtime-axis `running` crossed as
an agent-session state and collapsed two vocabularies this Work exists to keep
apart. Each member is owned before it is returned or written — and that
matters more now that the value is durable, because an unowned reading would
be read back by every later lookup as though this manager had established it.

## Verification

`evidence/gate-after-second-correction-2026-08-25.txt`. Focused
interrogation + session suites 136/136. Full suite 1077, reproduced byte for
byte from the locked installed layout. Nothing added to the pre-existing
failure set by this correction; the review's three are gone; four remaining
failures are reviewer-authored cases on W6630 and W6633, both in review,
reported rather than fixed.

## State

**Awaiting independent re-review and certification.** The claim is not
released and no Git operation was performed.

## Third re-review correction — 2026-08-25

All three [P1]s are corrected and all three additive regressions are green and
kept as written.

**No clock is read before the journal decides.** Taking `deadline_at` out of
the signature removed the ordinary collision but left the arithmetic in front
of `transact`, so an exact retry at a valid but late instant still refused —
a request whose durable answer already existed, rejected because a new
deadline would not fit. Both the instant and the deadline are computed inside
the transacted act now. The claim the previous correction made is true at this
boundary rather than nearly true, and the case asserts the property: on the
replay path the clock is read zero times.

**One observation owner, at every receiving door.** `probe` owned the
adapter's reading and the exported settlement took its caller's straight to
the column, so the vocabulary collapse the previous review found survived at
the door nobody had checked. The public door owns and compares; `_settle`
moves a reading somebody already owned — 4bz's split rather than owning twice,
and deliberately not a flag on a public signature. The idempotence re-audit
came with it: a second settlement carrying a different reading is refused,
because answering with the first would say the second was kept.

**A diagnostic name is bounded like its value.** A bound on half of an entry
is not a bound on the entry.

## Verification

`evidence/gate-after-third-correction-2026-08-25.txt`. Focused suites 144/144.
Full suite 1089, reproduced byte for byte from the locked installed layout.
Nothing added; the review's three removed. Three remaining failures belong to
W6633's and W6630's in-flight reviews and are reported rather than fixed.

## State

**Awaiting independent re-review and certification.** The claim is not
released and no Git operation was performed.

## Fourth re-review correction — 2026-08-25

Both [P1]s are fixed and both additive regressions are green and kept as
written.

**Nothing mutable is consulted before the journal decides.** The clock was the
first mutable input to move inside the fresh action; the live authority read
was the second, and it was still deciding historical operations — an exact
retry refused once the assignment ended. The durable binding stays before the
act, because the stable signature is built from it. My case now counts both
inputs and requires zero reads of each on the replay path, which is the
general property the two corrections were each half of.

**§13 at the observation's common receiving owner.** Ownership is not the
secret walk. `_diagnostics` proved shape, count, types and lengths and a
diagnostic named `claim_token` still reached the durable column. The raw
answer is walked in `_observation` — the one owner both doors reach — before
the members are composed, and the durable-writer reason names that path.

## Verification

`evidence/gate-after-fourth-correction-2026-08-25.txt`. Focused suites
150/150. Full suite 1100; the installed-layout list captured directly and
compared line by line against the source run's — identical, not merely equal
in count. Nothing added; the review's two removed. Two remaining failures
belong to W6633's and W6630's in-flight reviews.

## State

**Awaiting independent re-review and certification.** The claim is not
released and no Git operation was performed.
