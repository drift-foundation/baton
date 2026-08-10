# Decisions, reactions and voting — implementer design response

Answering the five protocol-10 design questions, and naming one consequence of
the confirmed invariant that the questions do not cover but that decides the
shape of everything else.

## The consequence that shapes the rest

The ruling says the decision obligation is durable state SEPARATE from the
delivery claim, that a recipient may send clarification while still owing the
decision, and that only their LIKE/DISLIKE satisfies it.

Follow that through. A recipient claims the message, replies asking for more
information — and `reply` completes the claim in the same transaction, which is
protocol 9's whole point. The claim is now gone. The decision is still owed.

**So answering must not require holding a claim.** If a reaction is authorized
by claim ownership, then the first clarifying reply permanently disarms the
recipient's ability to answer, and the obligation becomes unsatisfiable by the
only participant allowed to satisfy it. That is not a corner case; the ruling
describes it as the expected flow.

Authorization is therefore AUDIENCE MEMBERSHIP, not claim ownership. If the
answering participant happens to hold a claim on that message, the reaction
completes it in the same transaction — but the claim is a convenience, never
the gate.

## 1. Separate record, and reuse the ledger for the audit

Separate typed record, agreed. Two rows rather than one, because the ruling
describes two different lifetimes:

    decision_requests   (message_id, participant) -> state, requested_ts
                        one row per ADDRESSED participant, created when the
                        message declaring the decision is published
    decision_answers    (message_id, participant) -> value, answered_ts
                        PRIMARY KEY (message_id, participant)

The request row is what makes the obligation durable and independent of the
claim, what the TUI reads to keep the item actionable, and what the author's
withdrawal acts on. The answer row is the current value only.

**The audit is the existing transition ledger, not a third table.** It is
already permanent, already guarded by triggers, and already the place a reader
looks for "what happened to this entity". A new parallel audit table would be
a second answer to a question the store has already answered, and the first
divergence between them is a corruption report nobody can adjudicate.

Not a specialized response message. A response message is content — it has a
body, a manifest, a retention class, and it can be replied to. A decision is a
typed value with a uniqueness constraint. Encoding one as the other means the
uniqueness rule has to be enforced by convention over message kinds, which is
exactly the "arbitrary outcome string" failure the request already rejects.

## 2. Changeable, current value in the row, history in the ledger

Agreed. `PRIMARY KEY (message_id, participant)` gives uniqueness of the current
answer for free and makes "one participant cannot overwrite another" a schema
property rather than a check someone can forget.

A change writes the new value and appends a transition. The list shows the
current value; the detail view shows the current value, who set it, and when,
and can show the prior values because the ledger has them.

## 3. Atomic, for that participant only

Yes, in one transaction: the answer is written, the request row moves to
`answered`, and the answering participant's claim on that message — if they
hold one — is completed. All or nothing.

For that participant ONLY. In a multi-recipient decision every other request
row is untouched, which follows from the primary key rather than from care.

## 4. Author votes only if addressed

Agreed as the default. Being the author is not being in the audience; a
self-addressed decision puts the author in the audience and then the ordinary
rule applies. No special case.

## 5. Aggregates are audience-scoped because the message is

A participant outside the audience cannot see the message, so there is nothing
to scope: `scan` never lists it and the aggregate is not reachable. The leak to
guard is subtler — a COUNT tells a non-member how many people were asked, which
is audience membership information even when the values are hidden. So the
aggregate is returned only to members, and a non-member gets a refusal that is
identical to the refusal for a message that does not exist. Two distinguishable
refusals are an enumeration oracle.

Individual answers stay auditable to the audience. An aggregate that replaces
them rather than summarizing them would make "who agreed to this" unanswerable
after the fact, which is the question the record exists for.

## Retry

The existing effectively-once contract applies unchanged: the same value from
the same participant reports `already_committed`; a DIFFERENT value is not a
retry and must fail closed unless it is an explicit change operation. Silently
accepting a different value under retry semantics would let a lost response
turn into an unintended vote change.

## Withdrawal

A state on the request row, set only by the author, carrying the audited
reason. Because it is a state on a row no recipient may write, "no recipient
can simulate it by closing" is enforced rather than promised.

## Protocol-9 authorities

Refused cleanly by the existing generation/version gate rather than by anything
new. A protocol-9 store has no request rows, so a client that partially
interpreted the absence would read "no decision requested" for every decision —
silently wrong in the direction that loses obligations.

## Status

Design response. Not implemented; protocol 10 owns the schema change and the
bump. The one item here that is a genuine addition to the proposal rather than
an answer to it is the audience-not-claim authorization rule, and it needs a
ruling because it changes what "the claim" means for these messages.
