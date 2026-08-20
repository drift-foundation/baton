# Plan

1. [done 2026-08-20] The mandatory real-PTY gate did not reproduce the pause;
   its probe and evidence are retained.
2. [dropped by approver 2026-08-20] Leave existing `Ctrl-W` navigation
   unchanged. A later pursuit requires a new finding with live evidence.
3. [done 2026-08-20] Remove the superseded top-level Tab aliases and add view-mode
   `Tab`/`Shift-Tab` focus cycling while preserving
   context-specific text-entry behavior and `[`/`]` tab navigation.
4. [done 2026-08-20] Cover forward/reverse cycling and wrapping in wide/narrow layouts,
   refresh/resize stability, text-entry isolation, and read-only authority
   behavior.
5. [done 2026-08-20] Independently review focused PTY tests and live behavior.
