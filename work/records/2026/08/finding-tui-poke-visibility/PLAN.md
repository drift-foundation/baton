# Plan

1. Revalidate the live projection-12 poke shape and current TUI navigation.
   — **done** 2026-08-19; both confirmed, see `PROGRESS.md`.
2. Design the smallest visible pending-poke cue and inspect/respond surface.
   — **done**: the `[poke:N]` header counter, the bottom-row cue naming the
   key, and the `p` view with `a`/`x` actions.
3. Add focused positive, terminal, multiple-poke, and counter-separation
   tests. — **done**: `tests/work/test_w17_poke_visibility.py`.
4. Implement without changing poke workflow authority or Message counts.
   — **done**: `src/baton_work/tui/app.py` only, plus the console paragraph
   in `docs/BATON-WORK.md`. No authority, projection, CLI grammar or JSON
   change.
5. Run focused TUI tests and the complete v11 gate, then return for
   independent review. — **done**; passed back to `baton.bug` for review,
   not closed.

One question is deliberately left open for review rather than decided by the
implementer: whether `poke-answer explanation=` should carry the grammar's
`prose=True` flag. See `PROGRESS.md`.
