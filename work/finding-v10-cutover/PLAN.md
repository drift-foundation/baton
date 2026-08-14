# Plan

1. Confirm no active legacy claim is held.
2. Tell `baton.implementer` the v10 cutover gate is open.
3. Stop the shared bridge stack without deleting either mailbox.
4. Repoint its runtime config to exact 10.2.0 and `mailbox/v10/baton.json`.
5. Restart the stack and verify all ten monitors use the v10 paths.
6. Prove directed communication and scoped notice receipt on v10.
7. Give Slawomir the exact v10 TUI command.
