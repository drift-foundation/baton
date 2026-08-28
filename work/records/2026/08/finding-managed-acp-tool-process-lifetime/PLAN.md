# Plan

1. [done 2026-08-28] Revalidate the live process tree and preserve exact
   PID/PPID/PGID/SID evidence plus the self-matching watcher and runaway-test
   mechanisms. Evidence:
   `evidence/reviewer-research-2026-08-28.md`.
2. [done 2026-08-28] Map the current outer-owner gap. The bridge has a setup
   deadline but no turn deadline; its direct-child stop and infrastructure
   process-group stop cannot reach tool-created sessions. ACP session ids can
   already survive an agent-process replacement.
3. [awaiting ruling] Confirm the proposed v11 boundary: mandatory explicit
   `turnTimeoutMs`; one PID-namespace process domain per delivered turn;
   bubblewrap `--unshare-pid --die-with-parent` for the Claude deployment;
   positive domain exit before settlement/retry; terminal timeout reported as
   correlated `failed/cause=internal`; no separate runtime state.
4. [queued after ruling] Implement bridge configuration/deadline supervision,
   process-per-turn teardown and session reload; update the Claude launcher,
   supported templates, README, and installed-deployment preflight. Failure to
   establish or drain the domain fails closed.
5. [queued after ruling] Add the focused matrix from the research evidence:
   success/failure/timeout/cancel/shutdown/replacement teardown, `setsid`,
   self-matching watcher, runaway descendant, settlement race, session-id
   continuity, retry, and unrelated-process isolation.
6. [coordination] Make W28681 a live prerequisite of W6636 and carry the
   attempt-domain invariant into W6636's owned destroy/settlement crossing:
   force-remove the exact container and observe positive absence before clean
   settlement or replacement.
7. [pending implementation] Run focused ACP, deployment, and infrastructure
   gates; preflight the PID namespace from the actual service launch context;
   then run the full gate and obtain independent review.
