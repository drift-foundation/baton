# Progress

No implementation had started when the ruling was routed; W33937's explicit
one-candidate approval may proceed independently.

## 2026-09-02 — baton.tuner

Implemented the bounded policy and deployment-polish change under W71459. The
repository policy and proposal-integrator guide now require whole-path-set
authority preflight before mutation, all three case-specific approval facts,
refusal for insufficient or stale authority, candidate-bounded scope, and no
interactive approval request from a managed turn. Preserved generation 5 and
prepared the generation-6 candidate by changing only its generation number and
`teams.baton.roles.integ.instructions`. Added an independent W71459 static
guard; verification results and candidate digest follow after the focused and
broader gates complete.

Verification is complete:

- `./.venv/bin/python3 -m pytest -q tests/work/test_w71459_integrator_test_change_preapproval.py tests/work/test_w65212_proposal_integrator_deployment.py`
  — 6 passed;
- `./.venv/bin/python3 -m pytest -q tests/work/test_w101_role_instructions.py tests/work/test_config.py tests/work/test_deploy_v11.py`
  — 82 passed;
- `git diff --check` — clean, with separate no-index whitespace checks for all
  new untracked evidence and test files also producing no diagnostics; and
- generation-6 `baton.json` SHA-256:
  `4869e1a9271c0119ec8d3074ba54d9195994e9dea7c0a2aa5490d23abc7c9114`.

The existing unrelated worker-manager and finding edits reported by
`git status --short` were left untouched. W71459 is awaiting independent
review of the repository correction and immutable generation-6 candidate.

## 2026-09-02 — baton.tuner, changes-requested response

Revalidated the review against canonical W33937 detail: it remains `active`
under failed `baton.merge`, assignment episode 71379, so that claim is the live
blocker that prevents a drain from reaching `paused`. Corrected the rollout
checklist to record W33937's explicit approval first, begin the drain, recover
the exact claim under that fence, verify `paused`, and only then stop, install,
accept generation 6, restart, and allow the fresh integrator to claim W33937.
Added an ordering guard that fails unless approval, drain, recovery, pause,
stop, restart, and fresh claim remain in that sequence. The accepted role text
and generation-6 `baton.json` were not changed, so its reviewed digest remains
`4869e1a9271c0119ec8d3074ba54d9195994e9dea7c0a2aa5490d23abc7c9114`.

Focused correction verification passed all 7 W71459/W65212 tests.
`git diff --check` is clean, and separate no-index whitespace checks for the
changed untracked test, checklist, and progress files produced no diagnostics.
The correction is ready for focused independent re-review.

## 2026-09-02 — baton.tuner, live-gate root-cause trace

Traced the lower live failure through retained managed session evidence. The
W61984 integrator imported eleven paths with `cp --preserve=mode --parents`
from frozen custody at `2026-09-02T04:09:28Z`; W64268 repeated the same
operation for three paths at `2026-09-02T04:34:47Z`. The affected surviving
test paths are mode `0444` with matching change times. Custody deliberately
sets every file to `0444`, so these operations copied custody protection
metadata into the ordinary checkout. W33937's later FileChange approval request
was the consequence when it reached one of those leaked modes.

Recorded a bounded correction proposal in `FINDING.md`: import reviewed bytes
without custody modes; for an existing regular target, retain its preflight
mode plus owner-write; explicitly refuse before mutation when semantic
authority is absent; and verify final bytes and modes. A `/tmp` probe confirmed
`install -m 0644` can replace an owner-owned `0444` target with byte-identical
content and a writable checkout mode without a FileChange request. The exact
replacement/default-mode rule is now routed for independent review and
approver decision before changing the durable role or preparing another
deployment generation. No protocol, application, execution-policy generator,
or infrastructure file was changed.

## 2026-09-02 — baton.tuner, approved fail-closed correction

Pinned Slawomir's approver handoff and implemented its bounded documentation
and deployment-role correction. The earlier `install` proposal is explicitly
superseded: existing targets must already be owner-writable non-symlink regular
files matching reviewed base bytes, or the whole import refuses before content
or mode mutation and returns to `baton.ops`. Passing imports transfer reviewed
content without custody modes and verify final bytes and modes. Planned new
regular files use ordinary non-executable repository mode; executable mode
requires explicit accepted scope. No privileged replacement capability was
added.

Also incorporated the confirmed test-authority clarification: an accepted Work
description or plan that schedules bounded test changes is the case-specific
authority, while independent review still enumerates actual paths and binds the
candidate. Out-of-scope mutations refuse; scheduled and reviewed test work does
not prompt redundantly.

Prepared immutable generation-7 evidence by changing only `generation` and
`teams.baton.roles.integ.instructions` from generation 6. Candidate SHA-256:

```text
e7fac15abbcb33a09df3a5c650b2e7a9127515ecbba5ce9ff222953b1b4b6b55  baton.json
```

Added `tests/work/test_w71459_integrator_checkout_modes.py` without weakening
the prior guard. Verification:

- focused W71459/W65212 slice — 10 passed;
- role/config/deployment slice — 82 passed.

Generation 6 remains unchanged. W33937 remains closed and is not reused; the
generation-7 checklist requires separately accountable positive and negative
managed gates after independent review and approver rollout.
