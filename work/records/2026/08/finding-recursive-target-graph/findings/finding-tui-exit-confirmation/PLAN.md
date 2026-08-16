# Plan

Queued as independent feedback from the first human v11 trial.

1. Add the confirmed `Exit? y/N` state to normal TUI navigation.
2. Preserve text-entry handling and return to the exact prior view on cancel.
3. Add real-PTY coverage for confirm, cancel by each accepted key, irrelevant
   keys, one-row narrow rendering, and absence of authority/seen mutation.
4. Include the accepted correction in the next immutable v11 distribution.
