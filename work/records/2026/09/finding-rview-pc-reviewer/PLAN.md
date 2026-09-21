# Current action — exclusive rvpc review routing

Complete: owner activated the exclusive-route packet; fresh canonical teams confirms rvpc alone handles baton rview, codex has no routes or claims, and rvpc has a non-stale idle runtime lease. No further activation command is needed. Previous pool selection and preparation-only status below are historical and superseded.

# Current plan

1. Prepare generation10 config adding baton.rvpc to rview, a separate lifecycle manifest/dispatcher, minimal Codex-home config and exact permission rules. Bind changes to generation9 file digest and refuse drift.
2. Validate config structure, lifecycle manifest and dispatcher/policy structure locally without launching models or consuming readiness.
3. Owner applies the prepared files and accepts config via regen, then starts only the new supervised stack. Refuse duplicate deployment or occupied endpoint; retain backups.
4. Verify new runtime/readiness health. Keep existing reviewers and claims intact. Record installed state after owner execution.

Prompt owns only setup records and configuration preparation. No managed Work execution or review claim is taken.

## Prepared, not activated

Generation10 candidate, isolated port4501 lifecycle and dedicated workflow/inspection rules validated locally. Packet: /tmp/baton-rview-pc-setup. Owner runs bash /tmp/baton-rview-pc-setup/activate.sh. Installer refuses config drift, existing setup files and occupied port; retains generation9 backup. Existing infra manifest/services and auth.json are unchanged. Only baton.slaw config capability can accept regen; prompt has not installed external files or launched the reviewer.


## Current owner-selected restart — 2026-09-21

Pending owner execution of /tmp/baton-restart-codex-home.sh for reviewer/tuner .codex selection per newest FINDING ruling. Verify both app-server health and effective home, then explicitly resume dispatch. Earlier .codex-pushcoin home selection is superseded; no role/route change.


## Current repair — 2026-09-21

Earlier pending-restart status is superseded: owner performed restart and resumed dispatch. In progress: copy exact reviewer rules into the selected .codex home, update dispatcher template, restart only rview-pc with fresh context, and verify W202663 pickup. Record final outcome here.

Repair installation and static verification complete. Pending owner restart of the rview-pc service set (full stop/start to mint a fresh context); then verify rendered policy path and canonical W202663 claim pickup. No additional policy installation is needed.
