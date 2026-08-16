# Review: the orphan is real; the peer-build diagnosis is not

Outcome: **changes requested before the WIP boundary is described as reviewed**.

The live orphan is a genuine Stage 2.2 contract violation, but the finding and
proposed commit message attribute it to the wrong writer.

## Verified cause

The orphan K received is message `fac6d5a15122f6203123aec4516e765c`, a response
created by the current protocol-10 publication-aware executable through
`Store.reply`. It was not published by the preserved pre-publication cutover
artifact.

`Store.send` creates `publications` and `publication_audience` rows and passes
their id to `_insert_message`. `Store.reply` still calls `_insert_message`
directly without a `publication_id`. The resulting response therefore has a
NULL link and is delivered with `audience: []`.

That is exactly the acceptance path already pinned in
`work/finding-scoped-audiences/PLAN.md`: response messages created by `reply`
must receive their own single-recipient publication record while the claim
disposition remains the effectively-once retry key. No regression currently
exercises it.

## Why the older-peer inference is contradicted by evidence

The hash-pinned cutover executable was reconstructed byte-for-byte during the
incident (`9736b18d...`). Against the publication-aware live schema it refused
to open with schema-validation damage: extra `publications` and
`publication_audience` tables/triggers and changed `messages`/`notices` tables.
It published nothing. The schema check therefore did reject the older schema
understanding.

Remove the peer-build claim from the finding and proposed commit message. The
separate operational problem remains that the mutable `bin/baton` path and
live authority were advanced while both were called protocol 10, but it did
not create this orphan.

## Required correction

At minimum before this WIP checkpoint:

1. Correct `FINDING.md` and the proposed commit message to name the `reply`
   publication gap rather than an older peer passing validation.
2. Call the commit a WIP checkpoint. Stage 2.2 is not complete while a pinned
   directed-message path violates its publication invariant.

The implementation may remain deferred across this explicit WIP boundary if
Slawomir chooses. Before Stage 2.2 can be approved, it needs:

- one atomic single-recipient publication for each first committed reply;
- retry of that claim to reuse the committed response, never create another
  publication;
- a non-null schema invariant and doctor coverage for orphan links;
- a deliberate backfill/disposition plan for already-created orphan replies;
- break-checked core and packaged-CLI regressions.

## Other Stage 2.2 pins still absent at this boundary

This review is not a request to widen the WIP checkpoint, but the checkpoint
must not call Stage 2.2 complete:

- `PLAN.md` pins a multi-recipient return containing the `publication_id` and
  recipient-to-message mapping. `Store.send` and the CLI currently return only
  the publication id for several recipients. The mapping is therefore neither
  returned nor tested.
- The same plan pins a single-recipient compatibility shape "plus
  `publication_id`". The current public return remains only the message-id
  string; delivery adds the audience but omits the publication id.
- Slawomir has since ruled that a seen receipt is one-time notification
  metadata, not authorization to destroy rereadability of retained content.
  The current `mark_notice_seen` and `list_notice_activity` documentation and
  behavior still implement content-at-most-once. That decision belongs in its
  own pinned follow-up and is not approved by this WIP review.

Reviewer correction: the initially reported duplicate block in
`mark_notice_seen` was not in the file. The inspection command printed two
overlapping source ranges, making the shared lines appear twice in its combined
output. K's challenge was correct; no cleanup item remains for that block.
