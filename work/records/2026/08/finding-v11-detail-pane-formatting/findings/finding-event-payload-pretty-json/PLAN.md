# Plan

**Status — signed off and closed satisfying on 2026-08-18.** See
`review-2026-08-18T17-14-12Z.md`. The wrap no longer trims serialized content,
the property is verified over a broad losslessness sweep, and the progress
guarantee for pathological widths is structural rather than arithmetic.

**Prior status — 2026-08-18: changes requested by independent review.** The
serializer is correct, but terminal soft wrapping deletes spaces within JSON
strings. See `review-2026-08-18T16-00-17Z.md` and its additive regression.

**Prior status — 2026-08-18:** reviewer revalidation complete;
implementation-ready for `baton.impl`. W47 is independently signed off, so the
Event-reader boundary is stable.

1. [done] Revalidate the reader and its generic wrapping boundary after the
   Event index child landed.
2. [done] Emit deterministic `json.dumps(..., indent=2, sort_keys=True,
   ensure_ascii=False)` logical lines beneath a standalone `payload:` label;
   distinguish an absent payload from every present falsy JSON value.
3. [done] Preserve each logical line's structural indentation across terminal
   soft wraps, adding two cells only to continuations and dropping no content.
4. [done] Add focused Event-reader tests for absent/empty/falsy scalar, nested
   object/array, Unicode, escaped and long strings, narrow/wide, resize,
   clipped-tail, scrolling, purity, and JSON/projection parity.
5. [done] Run focused TUI tests and `just test-v11`, then return for
   independent review.
6. [changes requested] Preserve every serialized character across visual
   wraps, including repeated spaces inside quoted JSON strings; rerun the
   focused and complete gates and return for review.
