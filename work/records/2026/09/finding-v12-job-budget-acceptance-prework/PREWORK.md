# W156162 per-Job limits acceptance gap map

Advisory Work W173923, claim 173987, baton.claude via baton.impl.
**Read-only pass. Nothing was executed:** no test, probe, provider, model,
engine, image build, Git mutation or worker. No product, test or original
dossier file was edited. Advice for the future W156162 execution owner; **not
independent acceptance.**

Live-tree observations dated 2026-09-15 under claim 173987, provisional.

## 1. The distinction this Work exists to protect

W156162's own FINDING already draws it, and it is worth restating because the
two things share the word "budget":

- **Product Job limits** — ceilings a Job configures, that a runner enforces on a
  command or a provider turn. Real, implemented, and the subject of this Work.
- **Development verification stopwatch** — cumulative test subprocess wall time
  recorded per claim. `AGENTS.md` line 95 records the owner ruling of
  2026-09-14: cumulative stopwatch budgets are **not approval**, superseding
  earlier cumulative gates.

The FINDING is explicit that W103525's five minutes was the second kind, and
that "agent working time exceeding ten minutes therefore does not by itself
exceed that allowance". **Nothing in the acceptance of W156162 should be gated
on a cumulative stopwatch number**, and any surviving text that does should be
corrected (§6).

## 2. What is implemented — more than the FINDING's preliminary read suggested

The FINDING's own source note says `submission.py` had "no direct budget field".
That was a preliminary observation and is **superseded by the current tree**.
There is now a complete owner:

`src/baton_v12/job_manager/execution_limits.py` (240 lines), public surface:

    BOUNDARIES, COMPATIBILITY, CURRENT_GENERATION, GENERATIONS,
    LEGACY_GENERATION, LIMIT_MEMBERS, MAX_SECONDS, MIN_SECONDS, SCOPE, UNITS,
    boundary_default, effective, owned_execution_limits, owned_generation,
    requested_from_row, resolved

| Concept | Current value |
| --- | --- |
| Job-settable members | `provider_turn_seconds`, `verification_command_seconds` |
| Enforced boundaries | `provider_turn`, `ordinary_verification`, `integration_verification`, `host_verification` |
| Default generations | `0` (legacy) and `1` (current), both `{3600, 900, 1800, 300}` |
| Origin vocabulary | `compatibility` \| `job` — closed, two values |
| Units and scope | `seconds`, `per-invocation` |
| Range | `MIN_SECONDS`/`MAX_SECONDS`, refused where written, **no silent clamp** |

**Reachability from Job configuration is real:** `submission.py:136` inserts into
`job_execution_limits (job_id, requested, …)` with
`execution_limits.CURRENT_GENERATION`, and `submission.py:202
execution_limits_of` reads it back, deliberately leaving resolution to
`execution_limits.resolved`.

**I checked the four defaults against their runner owners and they all trace.**
The module claims to read rather than choose them, and that claim holds:

| Boundary | Default | Runner constant |
| --- | --- | --- |
| `provider_turn` | 3600 | `v12/worker/claude_agent.py:254 PROVIDER_SECONDS` |
| `ordinary_verification` | 900 | `v12/worker/claude_agent.py:259 VERIFICATION_SECONDS` |
| `integration_verification` | 1800 | `v12/worker/integration_workload.py:170 VERIFICATION_SECONDS` |
| `host_verification` | 300 | `v12/python/tools/stage_execution.py:291 GIT_SECONDS` |

I expected to find the fourth unpaired — it is the one where a real defect was
found — and it is not. The module documents it accurately.

**Existing test evidence:** `tests/job_manager/test_execution_limits.py`,
`tests/tools/test_execution_limits.py`,
`tests/job_manager/execution_limits_fixtures/PROVENANCE.md`, plus limits
assertions inside `tests/integration/test_managed_execution.py`,
`test_managed_storage.py`, `tests/tools/test_managed_preparation.py`,
`tests/job_manager/test_managed_integration_capacity.py` and `test_store.py`.

## 3. Reusable managed-integration evidence

The strongest reusable item is **an accepted limits defect fix that was found
through the managed path**, not through this Work:

> W170382 accepted candidate `candidate-172672.json` (SHA-256
> `b3248a8d…`), review `2026-09-14T22-42-50Z`, owner-closed at seq 172901:
> *"correct demonstrated 1800/default mismatch to original Job-owned 300s
> host_verification"* in `v12/worker/reconciliation_entry.py`.

That is independently accepted evidence that (a) the resolved limits document
reaches a real worker, (b) the wrong boundary being applied is detectable, and
(c) the Job-owned value wins. **Reuse it; do not re-derive it.**

Second, the resolved document is visible end-to-end in managed evidence. The
W170385 step-34 log records a real apply request carrying:

    "execution_limits": {"boundaries": {"host_verification": {"default_seconds": 300,
      "origin": "compatibility", "seconds": 300, "setting": "verification_command_seconds"},
      … "provider_turn": {"default_seconds": 3600, …}},
      "compatibility_generation": 1, "requested": {}, "scope": "per-invocation",
      "units": "seconds"}

Every member the design asked for — units, scope, effective value, default,
origin and the setting that moved it — is present in a real request. That is
reusable provenance for "an operator can tell whether anybody decided anything".

**Caveat to carry:** all of it is deterministic simulated provider/engine
evidence with real local worker processes. It does **not** establish that a
ceiling actually terminates a real container workload.

## 4. The gap map

### Implemented and evidenced
- Job-settable members, four boundaries, frozen default generations.
- Origin distinction (`job` vs `compatibility`) surfaced in real requests.
- Refusal outside range at write time, no silent clamp.
- Resolved limits reaching an actual worker, with a wrong-boundary defect caught
  and corrected under independent review.

### Remaining acceptance, after W161230 closes
1. **Override actually changes behaviour, per boundary.** Evidence so far shows
   `"requested": {}` — i.e. defaults. A Job that *sets*
   `verification_command_seconds` should be shown moving
   `ordinary_verification`, `integration_verification` and `host_verification`
   together, with `origin` flipping to `job`, and `provider_turn` unmoved.
2. **The shared-constant subtlety.** `host_verification`'s default is
   `GIT_SECONDS`, which the module notes **also bounds unrelated Git commands**.
   A Job's verification setting must move the verification boundary and leave
   those Git commands where they are. This is the one design subtlety most
   likely to regress silently, and it deserves its own case.
3. **Generation compatibility.** A Job admitted under generation 0 keeps its
   defaults when the build's `CURRENT_GENERATION` is 1. Both generations
   currently hold identical numbers, so **a case asserting "generation is
   honoured" could pass vacuously today.** Either assert the mechanism
   (the recorded generation, not the resulting seconds) or use a fixture
   generation with different numbers.
4. **Range refusal at both ends**, proving refusal-where-written rather than
   clamping.
5. **Recovery/isolation:** limits survive restart with the Job's recorded
   generation intact, and two Jobs with different settings do not leak into each
   other. This is the "isolation" the assignment names — **not** the v13 stress
   matrix, which stays deferred.

### Explicitly out of scope
- Broadening v13 stress/isolation matrices.
- Any provider token/cost limit — no such member exists; `LIMIT_MEMBERS` is two.
- Re-deriving managed-integration behaviour.

## 5. Smallest proposed deterministic selection — not executed

From `v12/python` with `PYTHONPATH=src:tools:.`:

    python3 -m unittest tests.job_manager.test_execution_limits \
                        tests.tools.test_execution_limits \
                        tests.job_manager.test_store

and, only for the managed reuse in §3, the already-bound
`tests.integration.test_managed_execution`. Nothing broader is needed: the
managed path's limits evidence is already accepted and should be cited, not
re-run wholesale.

Method notes worth honouring:
- **Pair each positive with the reversal that would catch a vacuous case** —
  especially item 3 above, where identical generation numbers make vacuity easy.
- Supervise experiments as well as final runs (per-run timeout, own process
  group, TERM-then-KILL) and record failures too.
- Avoid `unittest discover -s tests` without `-t .`; it makes `tests` the
  top-level directory and yields ~20 spurious loader `ImportError`s.

## 6. Dependency versions and stale wording

**Recorded versions**, from existing evidence — I created no environment project:

| Source | Values |
| --- | --- |
| `finding-managed-apply-settlement/environment-172988.json` | python `3.13.7`, jsonschema `4.26.0`, interpreter `/home/sl/src/baton/.venv/bin/python3`, cwd `baton:v12/python`, `PYTHONPATH=src:tools:.` |
| Observed interpreter now | python `3.13.7`, jsonschema `4.26.0` |

**The "old jsonschema mismatch" referenced in
`ADOPTION-AND-PROOF-161434.md` appears resolved** — the recorded and observed
versions agree. I did not trace what the original mismatch was, so this is an
observation that they now agree, not a closure of that finding.

**Historical costs, preserved honestly and not reconstructed:** W156162's own
PROGRESS records **246 runs, 2530.584419 s**, plus four disclosed unmeasured
activities. Carry both the number and the disclosure. **No replenishment or
reconstruction gate should be created for ordinary focused verification** — that
is exactly what the 2026-09-14 ruling removed.

**Proposed corrections** (for the owning dossiers; I edited nothing):
- Any surviving text treating the 246-run total as an allowance to be defended.
- The FINDING's preliminary "no direct budget field in these insertion paths"
  note, now superseded by `submission.py:136`/`:202` and
  `job_execution_limits`. Its *reasoning* was sound and should be kept as
  history; its *conclusion* no longer describes the tree.

## 7. Unresolved decisions for the owner

1. **W156162 is `phase: block` and W161230 is also `phase: block`.** The
   assignment says "after W161230 closes"; that has not happened, so none of §4
   can start. This is the same scheduling wall the W161234 pre-work hit.
2. **Whether generation 0 and 1 should ever differ.** They are identical today,
   which makes the compatibility mechanism untestable without a fixture
   generation. Someone should decide whether that is a gap or simply "no default
   has changed yet".
3. **Whether `provider_turn` needs Job-level override acceptance at all**, given
   no evidence yet shows a Job setting it.
4. **Whether the `GIT_SECONDS` sharing is acceptable long-term**, or whether the
   host verification boundary should get its own constant.

## 8. Assumptions and limits

- I ran nothing. Behavioural claims come from reading source, accepted reviews
  and recorded logs; structural claims are citations.
- I did not audit the ~250 historical repro/review artifacts in the W156162
  dossier; the assignment asked for a gap map, not a re-audit.
- I did not touch anything owned by W170385 and did not interrupt the tuner.
- Nothing here is acceptance of W156162, and none of it changes a release gate.


---

# CORRECTION — claim 174030, after owner reroute 174026

**Sections 4 and 7 of the report above were wrong, and the owner is right to
correct them.** I listed five "remaining acceptance" items and two "unresolved
decisions" that are already covered by existing tests. I reached those claims by
listing test *filenames* without reading their *cases* — the exact failure of
rigour I have been warning other owners about in the neighbouring pre-work
reports. The original text is left intact above as history; this correction
supersedes it.

## What existing tests already cover

The owner named three; reading them showed the coverage is broader still.

| My claim in §4/§7 | Existing test that refutes it |
| --- | --- |
| §4.1 "Override actually changes behaviour, per boundary" is remaining | `tools/test_execution_limits.py:362 test_the_configured_seconds_reach_the_real_provider_and_verifier` drives `(60,45)`, `(17,23)` and `{}`→`(3600,900)` through the adapter's own `_provider`/`_verify`, across success, timeout and start-error modes. Also `:288 test_a_configured_provider_turn_is_the_one_handed_over`, `:296 test_a_configured_verification_reaches_the_ordinary_command`, `:438 test_a_job_bound_delivery_never_falls_back_to_a_module_default`, and `job_manager/test_execution_limits.py:69 test_one_verification_setting_reaches_all_three_boundaries`, `:85 test_each_field_alone_and_both_together` |
| §4.2 the `GIT_SECONDS` sharing "deserves its own case" | `tools/test_execution_limits.py:1262 test_the_git_clock_is_untouched_by_a_jobs_ceiling` asserts `GIT_SECONDS` is still 300 before and after an observer built with `seconds=1`. It already **is** its own case. |
| §4.3 generation compatibility "could pass vacuously today" because generations 0 and 1 hold identical numbers | False. `job_manager/test_execution_limits.py:410 newer_defaults()` **adds** a generation (e.g. `provider_turn=7200`) rather than editing one — deliberately, because editing is the reinterpretation the structure prevents. `ANewDefaultCannotReinterpretAnAdmittedJob` then proves `:454 test_a_new_job_gets_the_new_default_and_the_old_one_does_not`, `:472 test_the_admitted_resolution_survives_a_restart`, `:485 test_the_public_status_reports_the_admitted_generation`, `:499 test_a_generation_this_build_does_not_hold_is_refused`. `TheMigrationLeavesOldJobsMeaningExactlyWhatTheyMeant` covers migration. |
| §4.4 range refusal at both ends is remaining | `job_manager/test_execution_limits.py:123 test_a_value_outside_the_supported_range_is_refused_not_clamped`, plus `:109`, `:115`, `:118`, `:138` |
| §4.5 recovery/isolation is remaining | `tools/test_execution_limits.py` `TwoJobsCeilingsDoNotLeakIntoEachOther` (`:3826`, `:3833`, `:3843`), `AReopenedServingKeepsBothJobsLaunchesUntouched:3535`, `AFreshProcessAdoptsBothJobsConfiguredLaunches:3410`, `:2647 test_three_jobs_bind_three_ceilings_and_three_tasks`, `:1477 test_resumed_serving_after_a_reopen_runs_no_command` |

## Claims withdrawn

- **"Every observed request carries `requested: {}` — so the override path is the
  real remaining evidence gap."** Withdrawn. I generalised from the two managed
  requests I happened to read. The override path is covered at the adapter, the
  launch delivery, the store, the public status and the relocated boundary.
- **"Generation compatibility needs a new owner decision"** (§7.2) and
  **"whether `provider_turn` needs Job-level override acceptance at all"**
  (§7.3). Both withdrawn — the tests already decide them.
- **§4.2 framed as remaining work.** Withdrawn; it is an accurate description of
  a real subtlety and an inaccurate claim that it is uncovered.

## What the three categories actually are

**1. Existing tests — covered, needs no new work.** Everything in the table
above: settings ownership, submission versioning, store replay and conflict,
public status, launch-context composition, generation compatibility and
migration, range refusal, adapter and relocated-boundary delivery, imported and
host verification boundaries, two- and three-Job isolation, reopen and fresh
process adoption.

**2. Recorded acceptance evidence — cite, do not re-derive.** W170382's accepted
candidate `candidate-172672.json` (review `2026-09-14T22-42-50Z`, owner-closed
seq 172901) corrected a demonstrated 1800/default mismatch to the original
Job-owned 300s `host_verification` in `v12/worker/reconciliation_entry.py`. This
remains the strongest single item and §3 above is unchanged.

**3. Actual remaining managed-path gaps.** Narrow, and stated at the right level:

- The **end-to-end managed preparation fixture configures no override**:
  `tests/tools/test_managed_preparation.py:228` builds
  `execution_limits.resolved(None, CURRENT_GENERATION)`. The override *is*
  proved at the relocated boundary by `:442
  test_a_job_override_reaches_the_relocated_command_boundary` (77 seconds
  reaching `entry._bound`, with `provider_turn` unmoved at 3600) — a unit-level
  assertion, not a full-run one. Whether the full preparation run also needs to
  carry a non-default ceiling is a judgement about evidence depth, **not an
  uncovered behaviour**, and I am not asserting it is required.
- The **managed apply path does carry an override end to end** —
  `tests/tools/test_managed_apply.py:107` submits
  `{"verification_command_seconds": 1}` and `:371` asserts the apply task's
  `host_verification.seconds == 1` — but that is **in-flight W170385 work and
  not yet independently accepted**. It should be cited as accepted evidence only
  after W170385 is accepted.

## Consequences for the rest of the report

- **§5's proposed selection stands**, but its purpose changes: it is a
  *regression* selection over already-covered behaviour, not a route to new
  acceptance. The vacuity warning I attached to generation compatibility was
  itself unfounded and is withdrawn.
- **§1, §2, §3 and §6 are unaffected.** The distinction between product Job
  ceilings and the development stopwatch, the implementation map, the four
  traced defaults, the reusable accepted evidence and the dependency versions
  and historical costs all stand as written.
- **§7.1 stands**: W156162 and W161230 are both `phase: block`.
- **§7.4 stands as a question, not a gap**: whether `host_verification` sharing
  `GIT_SECONDS` with unrelated Git commands is acceptable long-term is a design
  question the existing test documents rather than resolves.

## What I should have done

Read the cases before claiming the gap. Filenames are not coverage, and I had
just finished telling two other owners that a case which cannot fail is not
evidence. The same standard applies to a claim that no case exists.

Read-only throughout this correction: no test, probe, engine, model, Git
mutation or worker. Zero measured verification seconds.
