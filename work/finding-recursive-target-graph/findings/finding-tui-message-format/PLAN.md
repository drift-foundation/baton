# Plan

Queued as non-blocking feedback from the first human v11 trial.

1. Inventory the useful v10 message-reader treatments without importing its
   outbox, delivery, or ownership model.
2. Implement the confirmed stacked Work/messages split and a borderless compact
   message block with metadata, wrapping, references, and personal new/seen
   cues at wide and narrow widths.
3. Keep distinct Threads switchable, select one with personal `New` first,
   and preserve bounded paging plus explicit `s` seen behavior.
4. Prove parity with the canonical JSON Thread projection on a real
   PTY before the next immutable v11 distribution.
