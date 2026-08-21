# Progress

**State — 2026-08-21:** round-two review finding corrected; awaiting
independent review.

## Response to `review-2026-08-21T06-42-58Z.md`

Confirmed and fixed. The reviewer is right that this is not an incidental
count: it is the in-source explanation of a security boundary, and it said the
policy file is "deliberately dedicated to the four managed mutations" while
the module generates thirty rules. Someone maintaining this later could
reasonably have read that as evidence the other twenty-six were unintended.

The rationale now names the approved `managed-work-workflow` profile and its
thirty verbs, and keeps both points the review asked to retain: read-only
commands need no allow rule here, and rules for other participants are
unaffected.

## One thing I did not remove

The round-6 W415 note above it still says "four". That sentence explains why a
broad rule is reported even when the exact rules are present, and it is an
account of a defect found when the ruled set genuinely WAS four verbs.
Rewriting it would erase the history that explains why the check has its
current shape, so it is dated instead — "Round-6 review (of W415, when the
ruled set was four verbs)" — which removes the ambiguity without removing the
record.

## What changed

- `tools/codex-event-bridge/src/exec_policy.mjs` — two comment blocks. Nothing
  else.

**This round is comment-only.** Both edits replaced blocks whose every line was
a `//` comment; no executable line moved. The refusal TEXT the auditor emits is
asserted by the focused tests and is unchanged, which is the mechanical check
on that claim.

## Verification

- `npm test` in `tools/codex-event-bridge`: **172 pass, 0 fail**.
- `tests/work/test_deploy_v11.py` and
  `tests/work/test_w220_managed_workflow_policy.py`: **23 passed**.
- The complete v11 gate: **2807 passed** (non-serial) and **52 passed**
  (serial).
- `git diff --check`: clean.
- The live effective-policy matrix was NOT re-run this round, and that is
  deliberate: nothing it measures changed. The retained
  `effective-policy-matrix-2026-08-21-r2.txt` (13/13, with the runtime and
  incident cases executing as the nominated participant) remains the current
  evidence for the effective boundary.

## Boundaries held

- The confirmed 30-verb profile, its recorded exclusions, and every refusal
  are unchanged.
- Deployment-owned generation, exact binary/config/participant matching,
  broad-rule refusal and the raw-store prohibition are unchanged.
- No schema, authority, config-grammar or runtime-dispatch change.

## Not done here, deliberately

- **The deployment still runs the four-rule policy.** After this is committed
  and a release deployed, the operator must regenerate the policy file for
  every configured participant; until then the dispatcher fails closed and its
  refusal names the missing verbs.
- The durable approval incident is the action owner's; I did not touch
  incident state.
- Nothing was staged or recorded in history; the working tree carries the
  diff for Slawomir.
