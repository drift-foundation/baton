# Decision needed — publication retry after an ambiguous crash

## The concrete failure

A sender asks Baton to publish a message or notice. SQLite commits it, but the
process crashes before Baton returns the new message identifier. The sender
cannot tell whether publication happened. Repeating today's `send` command
creates a second publication, so recipients can receive duplicates.

Multi-recipient delivery makes the ambiguity more visible but does not create
it: the database transaction can atomically create every recipient delivery,
yet the caller can still lose the successful result after commit.

## Choice A — caller-known publication token

Create a unique token before publication and submit it with the request. A
retry with the same token and exactly the same sender, content, subject,
audience and other envelope fields returns the original publication. Reusing
the token with any changed field fails closed. Two intentional publications
with identical content remain possible because each uses a different token.

The token is transport/API machinery, not another participant credential and
not something a human should normally type. CLI and TUI behavior must define
how the token survives long enough to retry after an ambiguous failure.

## Choice B — retain at-least-once publication

Keep today's behavior and explicitly permit a retry after an ambiguous crash
to publish a duplicate. Remove the finding's promise that publication retries
compare and preserve the original audience.

A practical B variant adds an immutable `possible_duplicate` publication flag.
After an ambiguous result, the sender explicitly marks the repeated send. Every
recipient then sees that warning and can compare or dispose of the request.
Baton cannot automatically identify the original publication without retaining
a caller-known correlation token, so the flag is advisory and sender-supplied;
it must never claim that Baton proved a duplicate exists.

## Reviewer recommendation

Choose A and add the idempotency seam in protocol 10. An atomic audience does
not solve post-commit result loss, and duplicate work is particularly harmful
when one publication fans out to several recipients. The public CLI can keep
the normal path simple while exposing the token only for reliable automation
and recovery. The implementation plan must still pin token persistence,
retention/GC and exact mismatch behavior before schema work begins.

Choice B with the advisory flag is nevertheless coherent if operational
simplicity is preferred: communication remains live, duplicates are visible,
and recipients own their disposition. It trades automatic exactly-once retry
for a much smaller mechanism and must be documented as at-least-once.

## Ruling

Ruled by Slawomir on 2026-08-10: choose B for protocol 10.

Publication remains at-least-once. After an ambiguous result, the sender may
repeat the publication with an immutable `possible_duplicate` warning. Baton
does not claim that it identified or correlated the original, and recipients
decide how to disposition the warned publication. No caller-known publication
token or effectively-once retry seam is added in this protocol stage.

The warning applies to caller-repeated `send` and `send-notice` publications;
both have the same post-commit/result-loss ambiguity. Claim-bound `reply` and
`close` keep their existing claim-ID effectively-once behavior and do not use
the warning to weaken it.
