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
5. [in progress; tuner delivery complete] Focused races and lifecycle
   regressions pass, as do the complete bridge and v11 gates. Independent
   review and deployment remain required before relying on recovery.
