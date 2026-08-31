# Plan

1. [done] Preserve W43977's observed global baseline and the module list in a
   dedicated durable record.
2. [parked] Defer this hardening umbrella while the first useful v12 vertical
   slice is being proved.
3. [before implementation; fresh evidence retained] W54802's bounded 2026-08-31
   rescan and attribution diagnosis are appended to `FINDING.md`, but counts
   remain discovery evidence. When this parked umbrella is activated, rescan
   again and decompose it into separately claimable children for `workspaces`,
   `documents`, `oci`, `handshake`, `lanes`, `attempts`, `authority_port`,
   `intake` and `sessions` before editing implementation.
4. [later] Complete and independently review each module-local inventory,
   preserving W39666 as the separate owner of `worker_entry`.
5. [later] Run the aggregate inventory module and adjacent boundary suites;
   close only when the global gate is honestly green.
