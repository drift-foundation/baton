# Plan

**Status — configuration generation 2 accepted 2026-08-18.**

1. [done] Add the new role, participant, route, and endpoint kind to
   the editable v11 `baton.json`; increment its generation.
2. [done] Validate and accept the complete configuration with `regen` as
   the config-capable participant.
3. [done] Confirm `baton.tuner` is accepted and can read the unchanged
   authority; use `baton.tune` for bounded
   polish work that does not overlap implementation-owned files.

Accepted config event: generation 2, sequence 90, digest
`03d5b1486193a57fc0324ca97999ea31b496c7ea8810cf2564e1b4e7409ffe3c`.
The authority UUID remained `bec445ce436b17fc66ab5634833a3fbf`; existing
W26 remained queued at `baton.impl` with its planned return to `baton.feat`.

## Durable role instructions

**Status — implementation signed off 2026-08-18; deployment step 10 handed to
the approver.** The required repository policy now carries the v11 model and
the universal explicit-role launch contract is independently verified. See
`review-2026-08-18T19-41-52Z.md`.

**Status — bootstrap-policy audit complete; returned to `baton.feat` on
2026-08-18. See PROGRESS.md.** The required repository policy now describes the
v11 Work/claim/pass/obligation model throughout, and the guard sweeps the whole
file in both directions rather than pinning the strings a review named.

**Prior status — operator-surface repair complete; returned to `baton.feat` on
2026-08-18.** The reviewed P1 was already fixed; sweeping the
adjacent wording the review also asked for found two further surfaces, and the
guard against this recurring is now a sweep across all six shipped surfaces
rather than per-file assertions.

**Prior status — steps 7-9 implemented by `baton.claude` and returned to
`baton.feat` on 2026-08-18.** Universal role instructions,
explicit launch-role selection, the shipped example, the docs, and the pinned
Baton role texts are done. Step 10 (deploy, accept the next generation,
restart each launcher) remains the approver's act and is gated on this review.

**Prior status — scope expanded by the operator on 2026-08-18 after the clean
generation-3 implementation review. Deployment is blocked pending universal
role bootstrap instructions, explicit launch-role selection, and renewed
independent review.**

1. [done] Extend the strict role configuration with validated durable operating
   instructions; an unknown field must continue to refuse.
2. [done] Expose the effective participant instructions through a stable projection
   suitable for external launchers without reading the authority directly.
3. [done] Make the Codex/ACP launch path use those instructions when creating or
   resuming the participant session; eliminate operator-maintained one-off
   prompts from the normal path.
4. [done] Cover init, regen, participant/role resolution, session creation/resume,
   multiple roles, and refusal of ambiguous or missing instruction selection.
5. [done] Preserve existing Work and topology across the configuration generation
   change and document the bootstrap compatibility path for already-created
   sessions.
6. [done] Make the launcher instruction/readiness consumers agree
   with the candidate's projection-10 contract, restore unique participant
   assignment across Codex targets, and return the focused Codex plus ACP
   launch gates green before another review.
7. [done] Supersede optional instructions: require a non-empty instruction
   contract on every configured role, and make every agent launcher name one
   explicit role held by its participant.
8. [done] Populate the shipped example and next Baton coordination
   generation with complete `rview`, `impl`, `approv`, and `tuner` scope plus
   required bootstrap/read material. Keep the text role-owned rather than
   duplicating it per member.
9. [done] Add positive and refusal coverage for all-role completeness,
   explicit single- and multi-role launch selection, accepted-generation
   binding, required read directives, Codex start/resume, and ACP new/loaded
   sessions; then obtain a new independent review.
10. [pending] Deploy the reviewed immutable candidate, accept the next config
    generation, and restart each role launcher so no manually prompted or
    uninstructed session remains.

Implementation must preserve the already-reviewed transport and stay within
steps 7–9. The exact minimum Baton role/read contracts are pinned in
`FINDING.md`; generic protocol validation must not encode those Baton-specific
handles or paths.

The earlier tuner-only deployment paragraph is superseded by steps 7–10. Do
not edit the live generation-2 config yet: its deployed binary correctly
refuses the new field, and W101's expanded complete-role contract is not yet
implemented or reviewed.
