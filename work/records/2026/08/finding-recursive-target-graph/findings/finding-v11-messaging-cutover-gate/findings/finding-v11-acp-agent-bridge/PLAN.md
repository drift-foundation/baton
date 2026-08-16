# Plan

**Status — 2026-08-16:** queued behind W148. The transport and product boundary
are decided; exact installed-agent schemas, session continuity and supervision
shape require a focused implementation plan and independent review before code.

1. Inventory the installed Claude and Gemini ACP entry points and generate or
   obtain their authoritative ACP schema/capability definitions.
2. Specify a small external ACP client boundary that consumes canonical v11
   readiness without importing model behavior into Baton.
3. Define explicit configuration for agent command, participant, workspace and
   persistent session selection.
4. Build a fake ACP agent harness and cover initialization, prompt streaming,
   permissions, busy serialization, restart and isolation failures.
5. Prove Claude continuity first, then repeat the same acceptance flow against
   Gemini by configuration only.
6. Independently review the adapter and live evidence before treating v11 as a
   replacement wake path for either participant.
