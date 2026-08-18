# Plan

**Status — implementation signed off 2026-08-18 by `baton.codex`; operator
smoke remains.** The non-session-leader guard test no longer depends on the
runner's incidental session topology and no longer merely reads process ids:
it builds its own leader/child session and proves the guard by which process
survives `_terminate`. Focused file 45 passed; both removal and inversion
sweeps now red it. See the `R4` section of `PROGRESS.md` and
`review-2026-08-18T20-57-35Z.md`. The operator-owned live four-service smoke
remains and is not claimed as done.

**Prior status — changes requested 2026-08-18.** The process-group repair passes
its behavioral descendant cases, but its new non-session-leader guard test is
environment-dependent and does not call the function it claims to cover. See
`review-2026-08-18T19-59-53Z.md`.

**Prior status — changes requested 2026-08-18.** The containment and readiness
repairs are clean, but stop signals only each service's group leader and can
leave its spawned ACP agent alive while reporting success. See
`review-2026-08-18T19-46-35Z.md`; the live smoke remains blocked.

**Status — process-group termination repair complete; returned to
`baton.bug` on 2026-08-18. See PROGRESS.md.** Stop now terminates the session
the controller created, waits boundedly for it to drain, and keeps truthful
state when a member survives.

**Prior status — lock-containment repair complete; returned to `baton.bug` on
2026-08-18.** The lifecycle lock, the logs and the state read
now share one stated containment rule rather than three copies of four flags.

**Prior status — socket-readiness repair complete; returned to `baton.bug` on
2026-08-18.** Unix readiness is a bounded connection rather
than an inode check, expected refusals are distinguished from being unable to
probe, and both startup and status are covered. Both health-truth regressions
and the full gate are green, so the operator-owned live smoke is unblocked —
but it remains a human step: stopping that set would terminate the session this
participant runs inside.

**Prior status — second review changes requested on 2026-08-18.** The
log-containment repair is clean, but Unix-socket readiness accepts an inert
socket pathname as healthy. See `review-2026-08-18T17-03-46Z.md`.

**Prior status — 2026-08-18:** changes requested by independent review; the
operator-owned live smoke remains gated on the log-containment repair.

1. [done] Inventory the current manually launched v11 backend set and its
   deployment-owned inputs.
2. [done] Pin the `just start|stop|status MAILBOX` UX, mailbox-local log/state
   layout, explicit manifest boundary, and fail-closed ownership semantics.
3. [done] Revalidate the surviving Codex bridge entry points,
   configuration schema, and Justfile after retired runtime removal lands.
4. [done] Add the lifecycle controller, Just wrappers, generic
   example manifest, and focused fake-service test battery.
5. [done] Break-sweep stale/tampered process ownership, partial startup,
   duplicate readiness, rollback, interruption, bounded termination, and
   log/status truthfulness. The successive review findings are repaired and
   independently signed off.
6. [blocked on W101 deployment] After the candidate is deployed and the
   universal explicit-role configuration is accepted, update the dispatcher
   and Claude launch configs, configure the mailbox manifest, stop the
   manually launched set, and prove start/status/stop/restart with no v10
   fallback. Never stop the current set while its restart inputs still use the
   superseded participant-only shape.
