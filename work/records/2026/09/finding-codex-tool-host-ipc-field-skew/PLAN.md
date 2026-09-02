# Plan

1. [done 2026-09-01] Preserve the managed-turn transcript, dispatcher timing,
   canonical W61984 claim state, and clean proposal path evidence.
2. [done 2026-09-01; W66012] Register the external runtime defect on the
   authoritative Baton ledger and gate W61984 on it.
3. [done 2026-09-01] Restart the managed stack on installed Codex CLI 0.152.1
   so fresh contexts use a decoder compatible with the emitted timing field.
4. [done 2026-09-01; M66087, snapshot 66088] Prove one standalone canonical
   mutation followed by one read in the fresh `baton.merge` context. Close
   W66012, return W61984 to `baton.merge`, and use a fresh assignment episode.
