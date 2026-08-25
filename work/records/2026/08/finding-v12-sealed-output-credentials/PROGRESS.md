# Implementer progress — sealed output and assignment credentials

Created 2026-08-24 by `baton.claude` on claiming W6634, as the record requires.

## The dependency edges are installed

The assignment asked the route handler to add them before implementation, and
they are in: **W6634 → W6628** (seq 6902) and **W6634 → W6630** (seq 6903), each
with the rationale recorded on the edge itself.

## This Job is blocked, and that is the finding rather than a delay

The brief is explicit twice over: *"Consume the manager-owned output and
section-13 contracts"* and *"Do not invent manager envelopes or infer sealing
from engine prose."*

I revalidated against the current tree rather than taking the dependency
Works' status as the answer:

- **W6628** (manager output freeze and artifact receiver) — `open`, `queued`,
  **no dossier binding**.
- **W6630** (worker-control section 13 security surfaces) — `open`, `queued`,
  **no dossier binding**.
- In the Python distribution, `artifactOutput`, `freeze_operation` and the
  durable-secret rule occur **only in
  `contracts/schema/worker-control-1.0.schema.json`**. The manager package
  exports nothing that accepts an output observation, freezes, retains or
  authorizes cleanup; `seal_refusal` is the control store's refusal sealing and
  is a different thing wearing a similar word. `ARTIFACT_REF_MEMBERS` is a
  member list in the contracts layer, not a receiver.

So both contracts this Job is required to consume **do not exist yet**.

**What implementing now would mean.** Every deliverable in the assignment
terminates in one of them:

- quiescence-gated staging and manifest/count/bytes/digest observations have to
  be *accepted by the manager*, and the envelope that accepts them is W6628's;
- the exhaustive credential leak refusal has to apply *section 13's*
  durable-secret rule, which is W6630's.

I could write both. They would be **my invention of two other Works' contracts**
— the single thing this brief forbids — and W6628 and W6630 would then either
adopt my guesses or force this component to be rewritten. That is worse than
waiting, and it is worse in a way that is expensive to undo, because by then
tests would encode the guess.

**What I did not do:** start the parts that look independent. Bounded regular-
file collection reads a great deal like W6631's directory materializer and I
have just written that one, so it would have been easy to produce something
plausible. But *what may be collected* is decided by the declared outputs in the
manager's envelope, and *what must never be collected* is decided by §13 — so
the two rules that give collection its meaning are exactly the two that are
missing. A collector built without them would be a file walker with a Baton name
on it.

## Recommendation, not a decision

Route W6628 and W6630 first. When either lands, this Job can start against a
real contract; if the reviewer would rather I proceed against a **written,
reviewed provisional contract** stated in this record and explicitly owned by
W6628/W6630 to accept or replace, say so and I will — that is a different thing
from inventing one silently, and I would want it on the record before writing a
line of it.

## State

**Claimed, edges installed, no implementation.** Returned for the route
handler's decision.
