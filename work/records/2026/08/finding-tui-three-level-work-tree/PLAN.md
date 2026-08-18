# Plan

**Status — signed off by `baton.codex` on 2026-08-18.** Level reads are batched
one statement per level, the window change is published as projection 11.0,
both launcher consumers are widened, JSON/TUI parity is proved through depth
2, and live descriptions are corrected. See
`review-2026-08-18T19-38-52Z.md`.

**Prior status — implemented by `baton.claude` and returned to `baton.feat` on
2026-08-18.** All three steps done; projection 10.1.

**Original status — queued 2026-08-18.** This is a post-W71 design follow-up,
not a reopening of closed Work.

1. [done] Expand the canonical/TUI containment window from two to three
   visible levels while preserving one-parent containment semantics.
2. [done] Render a fixed `▸` more-levels cue on the deepest visible row when
   additional containment exists; share the reserved structural cue contract
   with `finding-tui-deeper-child-cue-visibility`.
3. [done] Extend projection, virtual-screen, and real-PTY coverage for the
   full acceptance matrix and return for independent review.
