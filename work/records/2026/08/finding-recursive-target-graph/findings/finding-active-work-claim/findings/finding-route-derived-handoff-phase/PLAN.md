# Plan

**Status — 2026-08-17:** confirmed; implementation must follow W49 because
both change the pass authority path and its episode tests.

1. Revalidate the stage-role vocabulary and every current explicit-phase pass
   call against the latest W49 authority changes.
2. Remove the public and internal pass phase operand and derive the phase from
   the live resolved destination route under lock.
3. Cover all mapped roles, approver mapping, unmapped refusal, explicit-key
   refusal, retry/race identity, claim release, Next consumption, and episode
   generation.
4. Mechanically update workflows, docs, and packaged parity to the phase-free
   handoff grammar without changing same-route phase mutation.
5. Run focused transition/workflow tests and `just test-v11`; return for
   independent review.
