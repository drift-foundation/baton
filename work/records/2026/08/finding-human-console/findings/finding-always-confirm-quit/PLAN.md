# Plan — always confirm quit

1. Revalidate the current conditional request and special two-row renderer — completed.
2. Make browse `q` always enter one confirmation mode with `Exit? y/N` — completed.
3. Preserve all modal/help meanings and prove the path makes no store call — completed.
4. Replace obsolete immediate-exit/two-row tests with state, render, help, and
   packaged PTY regressions for the ruled contract — completed.
5. Rebuild only the TUI artifact and submit a referenced focused handoff — completed and approved.
6. Slawomir tests the fresh zipapp — completed.
7. After human confirmation, rerun the full frozen release gate because this
   decision arrived after the previous 2289-test gate completed — superseded by
   the later `work/finding-release-version/` candidate; its diagnostic run
   passed 2302 tests, but final certification must use the versioned successor.
