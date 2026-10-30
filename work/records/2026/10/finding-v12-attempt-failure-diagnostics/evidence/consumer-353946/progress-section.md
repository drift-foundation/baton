
## 2026-10-22 — baton.claude, claim353946 — THE REPORT NOW CARRIES ITS JOB'S LIMITS AND ITS SNAPSHOT'S TIME

Successful canonical claim353946 after reading current state (queued,
unclaimed, routed `baton.impl`, `last_change_seq 353940`, zero open blockers),
the complete handoff through `work-events` (79 events, `next_after` null) and
thread T333486 in full (6 messages, `last_seq 353098`, unchanged). Read
`review-2026-10-22T18-18-00Z.md`, the current `PLAN.md` and the reviewer's
`evidence/review-353910/` — `CANDIDATE.json`, `report-omission.json`,
`packaged-report.json` and both joined logs.

**The blocker, confirmed by reading it rather than taking it.**
`rows_of` discarded the Job object when it called `_row(stage)`, so no row
carried its Job's execution limits; `report` discarded `status.observed_at`.
The reviewer's packaged reproduction — my own binary `88c737e0…`, hash-checked,
over a product-composed status document — proved `provider_turn` 3600 and
ordinary verification 900 with their units, scope and compatibility origins
present **upstream** and absent **downstream**, and input `observed_at`
`2026-09-02T00:00:00.000Z` likewise absent. The reviewer is right that the
token axis is no substitute: a token lifetime and a renewal limit are a
different mechanism from the per-invocation ceilings a command is handed, and a
report about an unknown historical cause particularly needs its snapshot's age
and the limits actually observed.

### The correction, bounded to this one outcome

- **`rows_of` threads the Job with its stage.** A row can no longer answer with
  a sibling Job's ceiling, and that is asserted directly rather than assumed:
  the multi-Job case submits one Job that *selected* 120/45 and one that
  selected nothing, and checks each row against its own Job.
- **`_execution_limits` projects positively and typed**: envelope (`units`,
  `scope`, `compatibility_generation`), `requested` per owned setting, and per
  owned boundary `seconds`, `default_seconds`, `origin`, `setting`. Requested
  stays separate from effective on purpose — an empty `requested` beside an
  effective 3600 says the default applied, which is a different fact from a Job
  that asked for 3600, and a Job that asked for 120 still reports the runner
  default beside it rather than overwriting it.
- **`report` emits `source_observed_at`** plus `source_time_why`, which names
  the three instants this report carries and keeps them distinct:
  `source_observed_at` is when the document was composed, a row's
  `execution.observed_at` is when its runtime was looked at, and a cause's `at`
  is when the cessation was ordered.
- **The vocabulary is mirrored by value**, the way `SOURCE_DIAGNOSTIC_SCHEMA`
  already is, so the projection still imports no `job_manager` module — with a
  drift test holding every name against `execution_limits.BOUNDARIES`,
  `LIMIT_MEMBERS`, `UNITS` and `SCOPE`.

Preserved, each with a case: explicit unknown on absent *and* malformed limits
and times, with **no default invented and no value coerced**; the **positive**
allowlist, so an unowned boundary name or member is reported by name only under
`unrecognised` and never forwarded; **no freshness verdict** and no
cumulative-budget policy, so an old snapshot reports its own instant unjudged;
read-only — `opens_no_store` true, `is_acceptance` false, store changes zero;
and the cause, degradation, correlation and cessation-versus-acceptance
semantics untouched, including claim353758's absent-record recognition.

### Verification

- **Focused: 39 tests OK** in `tests.tools.test_attempt_diagnostics` — 13 new
  cases on top of 27, covering real multi-Job composition with distinct
  selected and defaulted limits, correct row association, every owned boundary
  per row, the snapshot instant, an old snapshot, absent and malformed times,
  absent and malformed limits, a malformed boundary member, an unowned boundary
  and member, a secret canary nested in the limits, read-only invariants, and
  the vocabulary drift guard.
- **Red before green:** the reviewed reader `7b832216…` beside the new cases
  gives **39 tests, 1 failure and 15 errors** — every new limits/time case
  fails. `test_the_report_still_OPENS_NOTHING_and_accepts_nothing` passes in
  both arms, which is correct: it is an invariant, not a new behaviour.
- **Joined 12-module gate: 1256 tests, 14.313s, OK, exit 0, zero skips**
  against the previous arm's 1244.
- **Packaged:** rebuilt bundle `a1ec84af…`; the designed proof
  (`test_packaging` bound to it with `BATON_V12_STACK_PACKAGING_REQUIRED=1` so
  a skip cannot pass) gives 11 tests, 10 ok, **zero skips**, 1 failure — the
  `--version` source-commit case, which the reviewer already classified as an
  isolated-build-root artifact and not this blocker. No workaround and no
  waiver requested; final release provenance remains owed to the
  human-integrated build. The command itself: exit 0 in 0.301s.
- **The reviewer's reproduction, closed member for member** in
  `omission-closed.json`: over the same composed input and through a rebuilt
  bundle, `output_has_execution_limits` and
  `output_has_snapshot_observed_at` are both **true**, with
  `provider_turn` 3600 and its `compatibility` origin, ordinary verification
  900, units `seconds`, scope `per-invocation`, and
  `2026-09-02T00:00:00.000Z` in the envelope.

### Candidate and cost

Changed by this claim, isolated root only:
`v12/python/tools/attempt_diagnostics.py` `7b832216…` →
`b3932d126dcb20a79c3fcb21ef2b77caf553f453172b2251cba2021287ed8227` and
`v12/python/tests/tools/test_attempt_diagnostics.py` `e7a7b929…` →
`faea822ae6e49a28b5fcb39bf3b15dcfbe0c2d4e996d2da920c8ac47cfe129f9`. **The
accepted child producer is untouched** — `failure_cause` `776f5932…`, `intake`
`71f0ef60…`, `attempts` `f48c5519…`, `worker_manager/documents` `376e62ab…`,
all equal to `INPUT.json`'s accepted hashes; no producer change was needed or
made. Every other consumer file is byte-unchanged since the review. Evidence
with digests in `evidence/consumer-353946/INDEX.json`
(`fc56816a9d6db7086093f93aad77e9ede597d0d6bf48530b37e99d62fb765f6c`).

No shared product import or edit, no Git mutation, no live provider or engine,
no deployment, no installed-root edit, no recovery, no new split. W339626's
candidate untouched. Measured this claim: focused 0.095s, red arm 0.126s,
joined gate 14.313s once, packaging 2.221s, one bundle build ≈5.9s, the
packaged command 0.301s, plus unmeasured reading and hashing. Prior parent
≈2253s and child ≈5726.14s plus unknowns stay separately attributed; no live
provider or engine call this claim.
