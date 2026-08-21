# Plan: interactive prompt participant

1. [done] Pin the confirmed `baton.prompt`/`baton.codex` identity split and its
   migration boundary.
2. [done 2026-08-21] Update repository identity policy and reusable deployment guidance
   without changing protocol or application code.
3. [done 2026-08-21] Replace the superseded in-place generation-3
   checklist with a schema-27 fresh-authority rollout: add the prompt
   role/member before initial activation, preserve all existing routes, and
   derive every absolute path and policy from the new release/home.
4. [ready-for-approver 2026-08-21] Update the retained W459 deployment tests for prompt, reviewer,
   and tuner contexts; assert the prompt dispatcher target and the absence of
   a prompt readiness service. Then move the interactive launch to
   `baton.prompt`, give each identity
   one runtime publisher, leave Work readiness only on managed `baton.codex`,
   and verify the participant/context bijection plus Handler/Run agreement.
   The retained tests and candidate are complete. The approver still owns the
   fresh-authority deployment, runtime bijection check, and Handler/Run
   acceptance described in `CUTOVER.md`.
5. [done 2026-08-21] The retained prompt-context failure is
   corrected and the complete gate passes. Round-two review found that the
   fresh runtime template drops the deployed `gemini-acp` service and its
   agent-specific template while the accepted boundary preserves existing
   participants. Restore both Claude and Gemini ACP services/templates in the
   parameterized fresh rollout and cover their preservation; see
   `review-2026-08-21T14-47-50Z.md`.
