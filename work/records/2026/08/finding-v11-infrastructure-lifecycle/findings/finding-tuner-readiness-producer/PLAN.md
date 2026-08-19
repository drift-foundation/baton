# Plan

**Status — 2026-08-19:** independently reviewed and signed off. The existing
five processes remain unsignalled; status is deliberately partial/stale
because the live manifest now declares the sixth service. The parent
infrastructure Work owns the operator stop/start smoke.

1. [done] Revalidate the manifest and dispatcher target mapping.
2. [done] Add one uniquely owned `baton.tuner` readiness producer.
3. [done] Test duplicate-participant refusal and reviewer/tuner isolation.
4. [done] Run the live tuner poke canary and the full v11 gate. Focused and
   packaging tests pass; the full shared-tree gate is red on concurrent W17
   projection/TUI changes, recorded in `FINDING.md`.
5. [done] Independent review signed off before the next lifecycle restart.
