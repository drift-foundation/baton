# Reaction/decision design review

The implementer's audience-authorization conclusion is correct and is the
reviewer's recommendation for Slawomir's ruling.

## Recommended authorization rule

The right to answer comes from the immutable audience snapshot expanded and
stored when the decision request is published—not from current config/group
membership and not from an active claim.

An active claim cannot be the gate because the confirmed workflow permits a
clarification/follow-up first. Protocol-9 `reply` terminally completes that
claim, while the decision remains owed. Requiring the now-gone claim would
make the only lawful decision-maker permanently unable to answer.

Therefore:

- an addressed participant may answer whether or not a claim is still active;
- if that participant holds the matching active claim, answering also
  completes it in the same transaction;
- a former/terminal claim is neither required nor revived;
- no current or future member outside the publication-time audience may
  answer or learn that the request/aggregate exists;
- refusals for nonexistent and unauthorized decision IDs are
  indistinguishable to avoid enumeration.

This leaves claims as short-lived delivery/work ownership. The durable
per-recipient decision obligation is the thing that survives discussion.

## Accepted design points

- one durable request/obligation per message and addressed participant;
- one current answer per message and participant, enforced by schema key;
- explicit change operation for LIKE -> DISLIKE or reverse; a changed value is
  never accepted as an ordinary retry;
- same-value retry reports already committed;
- author answers only when included in the stored audience snapshot;
- author-only audited withdrawal;
- aggregate and individual answers visible only within the audience;
- aggregate never replaces the auditable individual answers.

## Audit caveat requiring protocol-10 proof

The current `transitions` table is not already sufficient without change. Its
schema accepts only `entity IN ('message','claim')` and stores state edges but
no arbitrary answer payload. Protocol 10 may extend it for decision/request
and answer entities if LIKE/DISLIKE are represented as explicit states, or may
use an append-only answer-event record with a derived/current answer.

Either is viable. Do not claim the existing ledger preserves changed answer
values until the proposed schema and triggers demonstrate it. The review
criterion is one authoritative history, schema-guarded mutation, and a doctor
check that can reconcile current answer with audit—not allegiance to a table
name.

## Ruling requested

Approve authorization by immutable publication-time audience membership,
with a matching active claim completed atomically when present but never
required to answer.
