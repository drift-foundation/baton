# Public contract — provider C, owner128669

Current test authority is AGENTS.md#w71830-standing-test-change-authority.
It supersedes older additive-only and assertion-preservation permission limits
below for accepted campaign scope. Record affected test paths and reasons;
independent review evaluates required behavior. Source scope and20s cumulative
verification remain unchanged; no per-test approval gate applies.

Pinned by baton.codex under W119114 claim128673 before implementation. Revalidate
A/B accepted schemas and current episodes/document semantics before dispatch;
no path or behavior outside the four approved files may be changed.

`restart_abandoned_correction(store, custody, *, job_id, attempt_id, generation)`

This public job_manager.episodes operation prepares one fresh episode from an
explicitly abandoned correction after A/B's accepted owners have proved and
recorded exclusion, exact gate discharge and checkpoint restoration. It takes
identity selectors, not a caller-supplied absence/receipt/checkpoint assertion.
It is an explicit recovery act, not a timeout or a new ordinary scheduling rule.

Derive the Job's implementation stage and its exact live correction episode;
re-read B.abandoned_correction_of and A.abandoned_gate_discharge_of plus owning
Job, attempt and line/checkpoint/verdict records through existing public
interfaces. Bind full Authority/Work/participant/generation, stage/episode/
attempt, old writer, retained checkpoint, cleanup signature and discharge
operation. Prove this checkpoint is the one selected by the last committed
changes-requested handoff and that another accepted review/integration or
unknown external effect has not superseded this correction. Require the line
still be prepared for this replacement, with the old writer excluded. A
historical receipt alone never ends a different or later live episode.

Placement clarification accepted in review-2026-09-09T17-07-35Z.md: the original
instruction to add the new reason to EPISODE_ENDINGS is superseded. That set is
specifically the terminal-offer vocabulary. Add the closed episode ending
`abandoned-after-exclusion` to documents' own EXCLUSION_ENDINGS and to
REPLACEABLE_ENDINGS, distinct from abandoned-after-restart and correction
endings. Preserve the existing offer-state import assertions.
Under one stable operation identity for the original episode/attempt, journal
and end exactly that live implementation episode with the accepted reason.
Do not create a replacement itself or modify manager/projection/scheduler;
existing ordinary replacement behavior then creates one successor. Reuse
existing transactional uniqueness and stable episode identities. Preserve the
review/integration stage history and all committed effect identities.

Return a plain closed document:
- schema: `baton.v12.abandoned-episode-restart/1`;
- operation_id, job_id, stage_id, episode, attempt_id, assignment;
- line_id, checkpoint_id;
- preparation_operation_id (B's receipt) and discharge_operation_id (A's);
- ended_state: `abandoned-after-exclusion`.

Exact replay returns the committed original result before mutable current-stage
checks, including after the ordinary successor has started; mismatched operands
collide. A partial failure cannot falsely authorize a new episode. Retain
foreign/uncertain/incomplete-evidence refusal and prior claimed-offer recovery
semantics. Never turn failed/declined/held arbitrary endings into replaceable
ones. If the existing replacement path requires another file, report that exact
boundary rather than changing the scheduler outside approved scope.

Add focused real-store proof: A/B-owned completed restoration permits exactly
one successor through ordinary sweep; repeated/concurrent replay creates no
second live episode; successor starts only after exclusion/restoration; wrong
Job/attempt/generation/checkpoint/receipt and running/uncertain evidence refuse;
committed route/publication/checkpoint remain unchanged. Tests remain additive,
including additive exhaustive-vocabulary registry cases; preserve all existing
assertions. Enforce20s cumulative across all selectors and iterations, retaining
commands/logs/wall times. W119114 owns the final full fixture and custody proof.
