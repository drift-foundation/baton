# Make dogfood retention a real operator decision

Work: W51473
Follow-up of: W39358
Discovered by: W39364 attempt `attempt-w39364-run2`

## Observed

The first live supervised dogfood attempt completed the entire manager arc but
could not leave its candidate available for independent review.
`tools/dogfood_operator.py::_custody` calls `decide_retention` with the literal
`disposition="discard-after-intake"`. The explicit
`retention_policy_digest` identifies a policy but no operand selects the
policy's disposition.

The manager froze and intook a 86,417-byte proposal, the operator independently
derived it, and then discard removed the proposal directory. Only
`sealed.json` survived. The lost files include `result.json`, the worker's
bounded explanation for its `unable` disposition, and the candidate tree the
review contract requires a human to inspect.

Evidence:
`work/records/2026/08/finding-v12-first-useful-dogfood-task/findings/finding-first-useful-task-acceptance/acceptance-2026-08-30T22-49Z.md`
and its `evidence/w39364-run1/` directory.

## Confirmed defect

This is not solved by replacing the literal with `retain` alone.
`_ended_however` currently treats every cleanup answer other than `complete`
as unresolved, while the manager deliberately reports `retained` when policy
keeps custody. An intended keep would therefore preserve the bytes but make
the documented command exit unresolved forever.

The deployment must carry one explicit retention disposition, use it for the
manager decision, and interpret the manager's matching terminal `retained`
ending as resolved when runtime absence and all provider endings are proven.
There is no ambient or digest-derived default.

## Required boundary

- Add a required, validated retention-disposition operator grant; consume one
  manager-owned vocabulary rather than spelling a second set.
- Pass that held disposition to `decide_retention` and retain the committed
  answer in evidence.
- Resolve an intentionally retained ending only when the requested/committed
  disposition keeps material, the manager reports terminal `retained`, the
  runtime is positively absent and no other unresolved fact remains.
- Preserve current discard semantics for an explicit discard choice.
- Keep retry/replay exact: evidence cannot choose a different disposition and
  an edited record cannot mint a retention decision.
- Prove the retained public custody locator exists after command completion and
  supports the documented independent diff and verification rerun.
- Regression-cover positive retain, explicit discard, mismatch/refusal,
  restart/retry and secret-free durable evidence. Run one real-Docker retained
  gate before another live provider attempt.

No workaround or second live provider turn is authorized under this Work.
