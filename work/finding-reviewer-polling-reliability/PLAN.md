# Plan

Scheduling: **deferred from 1.1 by Slawomir on 2026-08-11**. Retain this plan
for a future runner/monitor integration window.

1. Reproduce the timeout and ready-result exit statuses with a focused harness.
2. Specify a monitor contract: read-only readiness only; never claim, see, reply,
   or close; explicit handling for every exit status; observable liveness.
3. Add regression coverage for repeated timeout, ready result, process restart,
   no duplicate active waiters, runner-visible blocked-versus-stopped state,
   and prevention/detection of a turn ending with an active claim.
4. Choose and document a deployment/supervision method that survives the end of
   an agent turn.
5. Implement only after the contract is approved; preserve production mailbox
   semantics and the single active consumer rule.
6. Include the 2026-08-11 implementer recurrence from `FINDING.md` in any
   future runner acceptance test: a queued claim must keep/resume the owning
   turn until reply/close, or fail before claiming; it must never be left
   active merely because the model turn stopped.
