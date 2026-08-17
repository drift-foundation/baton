# Plan

**Status:** approved as W310 and queued after v10 retirement; authority
scheduling is blocked by W24. No implementation begins before that gate
closes. W309 records the current child-dossier binding rejection; until it is
fixed, W310 uses the canonical umbrella binding and its born message names this
exact child record as the explicit stopgap.

1. Revalidate every discussion-grouping schema field, event/payload,
   transition, CLI operand, JSON projection, TUI label/key, readiness client,
   document, and workflow story against the then-current tree.
2. Rename the durable and public contract coherently to Topic vocabulary,
   retaining `Tn` identities and the existing behavioral guarantees.
3. Refuse old command/operand spellings; bump schema and projection versions
   honestly and use a fresh authority rather than migration or aliases.
4. Add focused positive, negative, paging, cursor, race, replay, JSON/TUI
   parity, packaged, and end-to-end workflow coverage.
5. Run the complete v11 gate and return for independent review.
