# Required-attempt failure correction — W71879 claim147109

Owner147106 and campaign FINDING/PLAN20:23:14Z assign the bounded runner
correction and establishment of the supported nonsecret diagnostic boundary.
Prepared-147109 is a correction candidate for independent review. It retains
historical run6 operands and is not executable. Do not run copied operator-prepare,
deployment prepare/validate/render/provision or run.py. No fresh namespace,
review marker, model retry, live repair or deadline increase is authorized.
All six runs and prior packages remain preserved.

## Result and scope

The runner now detects definitive failure through the existing canonical STATUS
owner surface, before optional telemetry and the next sleep. The helper checks
current Job/submission/stage, attempt/episode/allocation, runtime assignment and
performed claim receipt, then the exchange owner's correlated terminal sequence.
Unable/cancelled and non-review plan-rejected answers, or supported faulted/lost
terminal answers, stop these required implementation/review attempts. No automatic
recovery is authorized for this proof. Review plan-rejected remains the existing
correction path. Pending result collection, absent artifacts, quiescence, missing
telemetry and successful answers do not mean failure.

The first observed failure gets its own first-failure.json, sample locator,
assignment/attempt/sequence/runtime correlation and wall time. The sample is
flushed with docker_stats:null and telemetry_skipped explicitly recorded. Counts
remain counts of performed telemetry, not fabricated measurements. The runner
then uses existing stop_serving and exact-Authority labelled-container containment,
retaining all state. It never clears a claim, creates a receipt or repairs a Job.
If multiple failures first appear in one poll, existing Job/stage order breaks
the tie; it does not claim to reconstruct which unobserved failure happened first.

A later deadline remains secondary to RequiredAttemptFailure in both the result
record and raised error. Serving containment/cleanup errors remain visible while
final evidence persists. Existing main-loop deadlines, all-stages-completed
criterion, final verification and source/target checks remain. Successful completion
with failed cleanup is still a failure, never accepted proof.

New failure_observation.py is the fourth execution helper. A future genuine
execution review must bind it alongside run.py, deployment.py and target_posture.py.
This package carries no copied markers. Deployment, full tasks/report/Git-read
instructions, STATUS observer/config, images, operator recipe, resources and
limits are unchanged. Twenty-five copied dependencies are byte-identical; only
run.py and two copied fixture/preservation tests differ. See correction-delta.patch.

The narrow correction handles a current claimed implementation/original-review
attempt's definitive exchange ending. Generic integration-held diagnostics,
uncertain launch/recovery and broad resilience are not added. Existing owner
projection and protocol behavior are not changed. Actual A/B acceptance is owed.

## Supported diagnostic boundary and unresolved scope

After containment, diagnostics read only a correlated published artifact's fixed
adapter result.json (implementation) or review.json (review). The artifact ID must
match the current attempt/output; its file URL must name a custody path under
this run's storage. Every component is opened with O_NOFOLLOW; only a regular
file and at most64KiB are read. Wrong schema/task, foreign/duplicate/missing artifact,
symlink, unavailable, oversized, duplicate-key, malformed or unclassified input
produces explicit unavailable/unknown. No arbitrary file glob, raw store, provider
stdout/stderr, credential source/home or log stream is opened.

Only the adapter's existing closed reason and bounded exit status are exposed;
report prose and parser/OS errors are never copied. The diagnostic is supplementary
published-report evidence, not a new attestation or the fact that decides failure.
Its directory content digest is supplied by the existing owner; the helper does
not remeasure the entire artifact or invent a new artifact-validation authority.
Changed/unavailable reports cannot turn an uncertain stage into a failed one.

The current adapter v12/worker/claude_agent.py maps only structured terminal_reason
api_error to api-error. Timeout, start-error and unclassified are its other fixed
reason words. It discards the provider record and keeps stderr on DEVNULL. There
is no supported authentication-specific reason in this accepted version. An
api-error may not be described as expired credentials, account restriction or
network failure. The actual run6 A and B-review published reports both yield
api-error/status1 and authentication_cause:unknown through the new safe reader.

Actionable boundary: preserve the exact attempt and reason, then use the owner
route for an approved structured diagnostic before another run. Start-error points
to executable/runtime launch checks; timeout retains the existing deadline;
unclassified requires scoped diagnostic work. No automatic login/retry or broader
classifier is introduced. Authentication-specific diagnosis is unresolved product
scope: the adapter's _failure_reason/PROVIDER_FAILURE_REASONS and published result/
review contract would need a separately assigned, independently reviewed change
based on observed structured provider vocabulary, with updated image provenance.
W55360's closed-map decision requires its own observed case for another entry.
Raw provider prose or credential-bearing output is not an acceptable substitute.
No such observation is available in the retained run6 reports; this tuner claim
does not modify product/image code or claim recurring provider errors are fixed.

## Verification and evidence

From repository root, the offline suite is:

```text
python3 -B work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-147109/verify_offline.py
```

All49 tests pass:13 new early-failure/diagnostic cases and36 inherited cases.
Actual retained run6 status replay detects A at sample5/8.731681402990944s and
B review at sample21/41.547954526991816s. The main-loop tests use labelled mocked
owner/process/clock answers; they prove immediate failure before stats/deadline,
primary persistence despite a later alarm and containment timeout, and existing
watchdog/final-verification/telemetry guards. They are not a newly executed run.

Diagnostic tests use temporary synthetic reports and TOKEN-SENTINEL values. They
verify closed output, unknown auth spelling, malformed/oversized/duplicate reports,
foreign artifacts and actual no-follow symlink refusal. No real credential is
read. Separate run6-diagnostic-replay.json records actual retained status plus
published adapter reports through the same safe reader, with no store/runtime call.

Affected test paths in this package:
- test_early_failure.py is new and supplies13 focused cases.
- test_stats_observation.py adds the fourth helper to its synthetic review binding
  and optional serving-stop error injection; all17 existing assertions remain.
- test_run6_preparation.py keeps deployment/task/policy/operator preservation,
  compares the former runner to its accepted source, and accounts explicitly for
  the new runner delta and three stats-fixture lines. Its former equality of the
  changed runner is replaced by focused behavior/guard tests and exact diff review.
Other report/timestamp/observer tests remain byte-identical. W71830 standing
scope grants authority; prior package files/tests were not changed.

The first49-case suite passed48 and failed B review: the new detector mistakenly
compared configuration generation1 to Authority assignment generation2. Corrected
by matching the actual current claim receipt, retaining foreign-generation refusal.
The intermediate49-case suite passed. The final small change ensures a later
TimeoutError is re-raised as the recorded primary RequiredAttemptFailure; final49
cases pass. All three suites and costs are retained, not hidden or counted twice.

Final suite: /tmp/w71879-146897-offline-verification-br5_u37h
Intermediate: /tmp/w71879-146897-offline-verification-lrl545au
Failed: /tmp/w71879-146897-offline-verification-1ek72we9
Final synthetic diagnostic fixtures: /tmp/w71879-147109-diagnostic-fixtures-yevpgbwk
All other retained paths are in each full verification.txt. Historical fixture
prefixes are unchanged and are not run identities. No temporary evidence is removed.
The run6-status-facts.json file contains selected retained canonical status fields
and the original samples-file hash; it is not reconstructed protocol state.

Verified prior37-file preparation and568-file final freeze,45 provider entries,
four source requirements and three observer source bindings. Two extra read
bindings cover claude_agent.py and worker_manager/exchange.py. Git diff --check
passes. No new model turn, host/Git mutation, live repair, source/image patch,
provider output exposure or execution marker. Historical run6 helpers remain held.

Six failed runtime walls total1341.1107609820174s. Listed preparation/diagnosis
now7.531655556995641s: prior6.558265653970405 + provenance0.014020125003298745 +
failed suite0.3226501370081678 + intermediate0.3156040370085975 + final suite
0.31302173700532876 + retained diagnostic replay0.008093866999843158. Untimed
reads/edits/CLI/static/manifest checks, null-terminal summary error, locator errors,
prior failures, host/operator and billing uncertainty remain additional.
No enclosing tool-time double counting, reserve transfer or increased allocation.

Preserve1200/240/180/120s,2CPU/2GiB/512PIDs and all capacity/storage/custody guards.
Run5 writer/coordinator-entry uncertainty, exact run6 provider causes and actual
A settlement/B derived judgments/import/causal/terminal proof remain unresolved.
General tracing, recovery/resilience, W144335/W144813/W136578/W129838 and fault-C/H7
remain deferred; the specific first-failure/diagnostic boundary is now immediate
scope. Direct independent review next, with unresolved adapter diagnostic scope
explicit for disposition before another run. No fresh-run packaging is provided.
