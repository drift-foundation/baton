# Plan: Codex system-error target stays healthy and never drains

1. [done 2026-08-30] Record the failed W36540 turn, `systemError` thread,
   false-idle runtime publication, healthy lifecycle report, and retained
   W36540/W39357 deliveries.
2. [done 2026-08-30] Bound high-priority tuner Work W43539 before using the
   managed-restart workaround.
3. [done 2026-08-30] Revalidate the app-server terminal-status model and pin
   fail-closed v11 recovery through a full managed-stack restart; automatic
   live replacement remains v12 worker-supervisor scope.
4. [done 2026-08-30] Correct runtime/health publication and bounded target
   recovery without dropping or duplicating retained readiness.
5. [done 2026-08-30; independently signed off] Focused races and lifecycle
   regressions pass, as do the complete bridge and v11 gates. Deployment
   remains required before relying on recovery.

## 2026-08-30 — first independent review

1. [confirmed] An observed `systemError` is sticky, unhealthy and
   non-deliverable; queued readiness and its in-flight identity are retained,
   reconnect restores the diagnosis, and an authoritative `idle` remains
   reusable.
2. [done 2026-08-30] Fail health and delivery closed when the
   post-terminal `readThread()` status refresh itself fails. The transient
   retry fence replaces stale-idle publication, and focused regressions cover
   retention, recovery, deferred completion, and retry/status races.
3. [done 2026-08-30] Rerun the focused bridge test, the complete bridge suite
   and v11 gates, then return for independent review before deployment.

## 2026-08-30 — second independent review

1. [confirmed] The transient status-refresh fence prevents stale cached
   `idle` from publishing or draining, preserves queued/in-flight identities,
   and reports unknown/retrying health until an authoritative status arrives.
2. [confirmed] Retry identity fencing, deferred completion, reconnect, and
   terminal promotion preserve the newer authoritative observation and do not
   reopen a sticky failed context.
3. [done 2026-08-30] Independent focused, complete bridge, v11, adversarial,
   PTY, and ACP verification passed. The correction is signed off for the
   managed deployment path.
