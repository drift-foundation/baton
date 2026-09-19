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
