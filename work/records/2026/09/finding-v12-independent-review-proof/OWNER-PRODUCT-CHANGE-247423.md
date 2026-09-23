# The selected product change, and the file ownership it takes

Recorded under claim 247423, **before any product byte was edited**, because
owner reroute 247421 requires exactly that: "Record decision and exact file
ownership before edits."

## What the owner selected

> "Owner selects the smallest supported product change needed for review-only
> completion without opening a correction round; preserve existing correction
> behavior for other Jobs."

This supersedes the position claim 247318 took. Review 2026-09-23T11:56:42Z R4
was right that detecting a round AFTER `open_correction` has run is
retrospective: "returning held does not undo that store effect", and the owner
had asked for the limitation to be reported BEFORE it is enabled. The
limitation was reported; the owner has now selected the change.

## The exact limitation this closes

`StageComposition.routed` calls `review_driver.open_correction` unconditionally
whenever a recorded verdict answers `correction`. There is no configuration,
bound or operand on the composed deployment that declines it, so a review-only
deployment cannot end a `changes-requested` review without a correction round
being opened in its Job store.

## The change, and why it is the smallest one

ONE OPTIONAL DEPLOYMENT MEMBER AND ONE CONDITION.

    correction_policy: "open" | "decline"        (optional; default "open")

  * ABSENT OR `"open"` means exactly today's behaviour, byte for byte. Every
    existing deployment document -- W239528's, W236087's, the product's own
    fixtures -- carries no such member and is unchanged. That is the
    "preserve existing correction behavior for other Jobs" half, and it is
    preserved by DEFAULT rather than by a migration.
  * `"decline"` makes `routed` NOT call `open_correction`, and answer the
    verdict with `correction_declined` recorded instead. It fails closed
    BEFORE the effect: the act is never reached, rather than reached and
    reported afterwards.

WHAT IT IS NOT. It is not a way to suppress a verdict, and it changes nothing
about what a reviewer may answer: `accepted`, `changes-requested` and
`rejected` all remain valid and the review is free to return any of them. What
it declines is the Job-store ROUND that would follow, which is the next Job's
work and not this one's.

WHY NOT A NEW SCHEMA VERSION. The member is optional and additive, so a
document that omits it is valid under the existing schema and means what it
means today. Introducing `/3` would require every existing document and
validator path to move for a member almost none of them will ever carry.

## Exact file ownership taken

    v12/python/tools/stage_execution.py

and nothing else under `v12/`. Its digest BEFORE this claim's first edit:

    ebc9be29d2bd23cf129afe33943f5336832df2ef24256c724708004220032896

That is the byte-identical value W239528's `PRODUCT-CHANGE-242687.json`
records as its accepted `after` for the same path, re-read at the start of this
claim. The `after` digest of this claim's edit is recorded in
`PRODUCT-CHANGE-247423.json` beside it.

Product tests covering `routed` and `held_configuration` are this change's own
and are edited if the change requires it; none is weakened to accommodate it.

## What stays untouched

`v12/python/src/baton_v12/job_manager/review_driver.py` -- `open_correction`
is unchanged. The decision to call it moves; the act does not.

W239528's `baseline.py`, both worker images, the retained run directories and
the other two dossiers are untouched, as under every previous claim.

## The packet stays non-runnable until this is accepted

Owner reroute 247421: "Keep the packet non-runnable until the no-correction
boundary is implemented and independently accepted." `OPERATOR-239533.md`
carries that statement, and `review_supervisor.held_packet` refuses a packet
whose deployment does not carry `correction_policy: "decline"` -- so the
boundary is a precondition of running at all rather than a promise in prose.
