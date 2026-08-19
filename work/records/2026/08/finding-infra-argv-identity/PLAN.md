# Plan

1. [done] Compare the manifest argv, lifecycle state, `/proc` argv, and logs for all four freshly spawned services.
2. [done] Identify the single violated identity assumption and pin the correction before implementation.
3. [done] Add focused real-shebang positive and later-substitution/PID-reuse regressions.
4. [done] Replaced the disproved quiet-window mechanism with provisional launch identity finalized atomically at configured readiness. Exact final-argv refusal and bounded provisional rollback are covered, and Slawomir approved version-1-as-provisional recovery on 2026-08-19.
5. [ready — operator] Recover the live partial set and repeat the W20 operator smoke. The `claude-acp` and Codex app-server processes belong to that set, so the restart must be run by the operator from outside those sessions.

## Combined W10/W6 phased cutover — approved 2026-08-18

Minimize the final outage by preparing the next immutable release and Gemini
configuration before stopping any participant:

1. Let K finish and release current Work; independently review the frozen tree,
   run the gate, and let Slawomir commit it.
2. Deploy that exact commit to a new immutable application directory.
3. Stage a new commit-named coordination home whose Baton and infrastructure
   configuration includes the approved Gemini `impl2` route and bridge, but do
   not start it or move the live home symlink yet.
4. At the cutover gate, freeze participants and stop the OLD home while
   `/home/sl/baton-v11` still resolves to it. Its version-1 lifecycle state is
   the ownership evidence required for bounded provisional recovery.
5. Recreate the final unfinished Work snapshot in the staged authority, move
   the live symlink to that home, start the complete service set, and run
   status plus Codex/Claude/Gemini canaries.

Moving the live symlink before stopping the old set is forbidden: the
controller would open the new home's state and strand the old processes it was
supposed to recover.
