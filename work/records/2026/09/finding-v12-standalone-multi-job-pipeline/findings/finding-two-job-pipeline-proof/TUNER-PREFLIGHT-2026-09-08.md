# Concrete demonstration preflight — 2026-09-08

Author: baton.tuner, role tuner, lightweight W115572; successful claim seq115580.
This is preparation for W71879/W71830, not the final freeze or independent
acceptance. Only this report was written. No test, reproduction, container,
model, credential operation, submission, recovery or Git mutation was executed.

## Result and decisions needed

**Confirmed:** the approved demonstration now submits A and B to completion
and a third small fault Job C together. Both implementation overlap and review
versus unrelated coding overlap, two serialized imports, same-line correction,
planned existing-test work, the companion refusal and zero ordinary operator
transitions remain required. The dated approval in FINDING.md supersedes the
old exact-two-document wording, not these assertions.

**Observed:** the current deployment factory still configures exactly one
worker per role and one development line. Merely filling in its configuration
cannot demonstrate A/B concurrency. Logged as lightweight limitation **W115599**
for owner placement; no workaround or new dependency was installed.

**Open:** no complete automatic companion-refusal path has been established
that preserves honest independent approval and both successful imports. The
accepted integration workload's semantic test-scope refusal ends conservatively
`held` after provider exposure. Its existing negative fixture is not the
end-to-end submission. Logged as lightweight decision **W115604**; section 4
identifies exactly what still needs placement rather than inventing success.

Recommended owner decisions:

1. Choose the small operator-prepared fixture repository below and retain its
   immutable baseline; confirm the bounded test scope and deliberate correction.
2. Place multi-Job factory capacity and per-Job binding explicitly, preserving
   current serial file ownership and the one-Job assembly/custody acceptance.
3. Resolve the companion's negative-fixture provenance, automatic trigger,
   observation boundary and terminal semantics before freezing any run.
4. Obtain accepted port/assembly inputs, then perform the targeted delta review
   in section 8. No current proof gate is removed by this report.

## 1. Evidence and source identity

Read AGENTS.md, docs/AGENTS-MAILBOX-PROTO.md and docs/EFFECTIVE-BATON.md, then
the assigned FINDING.md, PLAN.md, PREPARATION-2026-09-08.md and
review-2026-09-04T14-10-08Z.md in this record. Also read the port's
`../finding-standalone-stage-composition/findings/finding-integration-runtime-port/HANDOFF-CONTRACT-2026-09-08.md`
and the shared assembly PLAN.md. These records and current source are the
basis for the distinctions below; test bodies were read, never executed.

Canonical read of W103083 at snapshot115593 found its integration-port provider
still open and independently under review. Its verdict-channel and joined
custody/ordinary-test providers were satisfying. This is dated evidence, not
a replacement for reading live dependencies at freeze.

Observed checkout HEAD was `e213de76102cbf35c96a39544738f74e0f4f00fb`.
The working tree contains numerous modified and untracked provider files;
HEAD therefore does not identify the implementation inspected here. These
SHA-256 values identify source observed during this preparation, not accepted
deployment bytes or a new immutable candidate. Re-read any file that changes.

| Repository-relative path | Observed SHA-256 |
| --- | --- |
| v12/python/tools/stage_execution.py | 95271d77edc044653eef59f79169c82394c5e2b30d1b5ffb1edb48b16d88da47 |
| v12/python/tools/integration_worker.py | d34a289148cf87e3be750d14905d432819c750d806f0fd63e0758df379b0fe08 |
| v12/python/tools/job_manager.py | a745e36ac192044e53a5ea640244c77149b1fdd334e75da0e7043c511f6cbb14 |
| v12/python/tools/single_worker.py | 5dfd0df1b393f87e6a48e75f0845b266c73d2929e5cd6ad53509e1c02ef9dc27 |
| v12/python/src/baton_v12/job_manager/documents.py | e00d5804311e08826d289ac74063f64b13645be7607691ae3359a6380b8c9987 |
| v12/python/src/baton_v12/job_manager/scheduler.py | fe6d8f33204d1ecb0647eefd11cf6ca781abc22a3841f9310ed32bb1e1f36457 |
| v12/python/src/baton_v12/job_manager/review_driver.py | 0ba2b2bb7adb9c6181cb843a4b90ddf5da6bd8dadd43ed9e6e5a5952020c2262 |
| v12/python/src/baton_v12/integration/driver.py | c1f55d7b8416ce29bd3024ead709852145c1d885af4bba3e5c47a498abcfd887 |
| v12/worker/integration_workload.py | b2dfbafb6cc6c01b4bb88edd6e2a226eb088f99da32b50fe7e6cb6aa9d264394 |
| v12/worker/claude_agent.py | 9a16f57c516660f2ccb2ad56fc404c91bc2c575bf3dd52970f64017b1ee29955 |
| v12/python/tests/manager/test_integration_worker.py | a35013a2ad37f9079c8c653776bf1c7d76bdb7628a673268c3f0d5b3318b4f15 |
| v12/python/tests/tools/test_stage_execution.py | 16ac448aafef3a29fc7a7778613dc32281ff4b1bbe0e9a38e4cf946f23e5f8d5 |

Handoff recheck: `tools/integration_worker.py` changed during this turn to
SHA-256 `0fb9abe758a07923a11ef1f964b9f8a415b9b100957ce6e22a8b5f24a478841b`.
Its constructor and the four public method signatures cited below were re-read
and remain the same. This is a source-drift observation, not review of the new
implementation. The factory and driver hashes above were unchanged at that
recheck. Consume the eventual accepted provider, not either observed port hash.

## 2. Proposed baseline and concrete contracts

**Proposed:** use a tiny independent Git-backed Python fixture repository,
prepared and committed by Slawomir before the run. It avoids making the proof
depend on pending Baton application edits. All three Jobs nominate the same
retained immutable Git source and full base object id. They receive distinct
manager-custodied writable lines. A/B target one disposable canonical checkout
registered with the accepted Authority. Neither the live Baton checkout nor its
Git index is the demonstration target.

No repository, file or baseline described in this section was created.
`<BASE_OID>`, source nomination, target registration and accepted profile digests
remain freeze inputs. The baseline should contain exactly the following useful
fixture surface, ordinary owner-writable non-executable files, and its Git
metadata. Empty package initializers make the verification argv unambiguous.

| Path | Baseline contract |
| --- | --- |
| demo/__init__.py | Empty package initializer |
| demo/greeting.py | `greet(name)` returns `"Hello, " + name + "!"` |
| demo/units.py | `minutes_to_seconds(n)` returns `n * 60` |
| tests/__init__.py | Empty package initializer |
| tests/test_greeting.py | unittest cases for `Ada` and preserved spaces around ` Ada ` |
| tests/test_units.py | unittest cases for 0 and 2 minutes |
| tests/test_guard.py | Independent unittest assertion that a fixed sentinel equals `"retained"` |
| README.md | Fixture purpose and Python unittest invocation |

Keep this baseline small (under 1 MiB including retained Git objects is a
proposed budget), dependency-free and readable through the chosen source
profile. Freeze complete baseline file contents, modes, tree/base ids and
source nomination before deriving any task or policy digest. Git preparation
and final Git action remain Slawomir's; this report supplies no Git mutation
commands.

### A — normalize a greeting, then complete one bounded correction

**Draft final contract:** edit only `demo/greeting.py` and the EXISTING
`tests/test_greeting.py`. Strip surrounding whitespace from a name and raise
`ValueError("name is empty")` when the stripped name is empty. Preserve the
`Ada` result and punctuation. Explicitly replace the baseline preserved-space
expectation with `greet(" Ada ") == "Hello, Ada!"`; add empty/whitespace-only
rejection cases. This schedules that specific expected-behavior change and
adds assertions; it grants no deletion, general weakening or other test edit.
`test_scope` is exactly `["tests/test_greeting.py"]`.

**Draft forced-correction policy:** the first implementation checkpoint n
deliberately delivers normalization plus its passing updated test, leaving
empty-name rejection incomplete. The independent reviewer sees the full final
contract and truthfully requests that exact missing behavior and regression.
A fresh implementation assignment completes them on the existing line; its
later checkpoint n+1 receives a fresh independent review. Encode both rounds
and the final requirement in the original task, with the already-normalizing
line as the bounded round distinction, so no operator edits the task or feeds
a manual stage transition between rounds. Final review must check that this
distinction is unambiguous against the actual frozen fixture bytes.

The first candidate's narrow command can pass while review still identifies
the intentionally missing behavior. It is not accepted for integration and
its passing tests are not claimed to prove the final contract. The final
command remains `python3 -m unittest tests.test_greeting`; the correction adds
the missing cases within the already scheduled path. The integration driver
must verify the final producer's actual ordinary-test observation against the
held task bytes, not reuse checkpoint n's command result.

**Source-supported automatic route, once assembly wires it:**
`prepare_implementation` → `end_implementation` → independent
`prepare_review` → `end_review_from_result` → `open_correction` → fresh
implementation/review episodes. `open_correction` validates the recorded
verdict through `episodes.advance_correction`; correction is distinct from the
scheduler's replaceable failure endings. No call to `record_verdict` or
`open_correction` is an operator step in the run. Current StageComposition.end
still calls the old `end_review(... verdict=deployment.verdict(...))`; its
default `_no_verdict` is not the accepted frozen-verdict channel. That wiring
is existing assembly work, not a reason to supply a canned callback here.

### B — independent unit conversion

**Draft contract:** edit only `demo/units.py` to add
`hours_to_seconds(n) = n * 3600`. Add `tests/test_hours.py` covering 0, 1 and 2
hours. Preserve `minutes_to_seconds` and its existing tests. `test_scope` is
`[]`: no existing-test edit is scheduled. The new test is explicitly part of
the planned path set; all files remain ordinary non-executable files.
Verification argv is `python3 -m unittest tests.test_units tests.test_hours`.

There is no A/B source-path overlap and no implementation dependency. The
reviewer independently accepts the exact B checkpoint and the integrator
imports it on the same registered target as A. B's verification touches no
A path, so both orders are viable PROVIDED the accepted integrator supports
serial disjoint imports from the common baseline without an intervening Git
commit. Freeze the target observation policy; do not silently retarget or
rebase B after A imports.

**Overlap proposal:** make A's first round short and B's independently useful
coding/verification longer. If deterministic timing is needed, use a reviewed,
bounded provider-fixture wait INSIDE B's real implementation runtime, defined
before submission (for example 120 seconds, maximum 180). It is a timing
fixture, not evidence of 120 seconds of useful coding. No manager sleeps,
fabricated runtime timestamps or operator barrier releases qualify. Such a
fixture/image is not currently supplied by the factory and needs explicit
freeze/delta review. With live providers, latency alone cannot guarantee
overlap: accept only the observed positive interval intersection, never an
assumption that B will take longer.

### C — contained start failure

**Draft contract:** a separate implementation-only Job, same immutable base,
no changed paths, `test_scope: []`, `terminal_policy: "report-and-hold"`.
Its task may ask to inspect the fixture without editing it, but the selected
failure happens before that task runs. C is not expected to produce a
successful proposal or count toward either import.
The proposed task's required verification argv is
`python3 -m unittest tests.test_guard`; retain it as unrun under this failure,
never as passing evidence.

**Preferred bounded injection proposal:** after configuration/image preflight
and a real C claim, inject one start error at the `engine_run` boundary of
`operations_from`, selected by C's exact derived attempt/start labels and only
for its OCI `run` call, before forwarding that call to the real engine. Other
engine operations, especially runtime identification, must execute normally.
No fake runtime id, successful inspect answer or lifecycle receipt is returned.
The injector must retain its exact predicate and observed one-shot invocation.

This proves a failed runtime START, not containment of an already-running
process crash. Confirm that choice in the delta review. An invalid global
image or credential is a poor substitute: preflight may reject the whole
factory before there is a C allocation. Do not inject a generic programming
exception at the serving-loop boundary.

**Confirmed owner path:** `worker_manager.attempts.request_runtime_start`
journals before calling the adapter and owns start-failure settlement;
`single_worker._SingleWorker.launch` preserves the owner's failure record;
the Job sweep consumes the recorded ending and projects C `exceptional`.
`scheduler.reconcile_allocations` releases a positively failed-before-runtime
allocation, but keeps uncertain runtime/failed cleanup `recovery-required`.
`documents.REPLACEABLE_ENDINGS` contains only `abandoned-after-restart`, so
this chosen failure earns no automatic replacement. The read-only test
evidence is `tests/job_manager/test_launch.py::AFailedStartIsContainedAndExceptional`,
especially `test_a_recorded_adapter_fault_is_contained_and_the_sweep_continues`.
Its FakeOperations supplies observations; it supports the intended scheduler
behavior but is not the real run's proof of failed-start reconciliation.

**Still to supply:** the approved factory/fixture entry that installs this
one-attempt injector. `engine_run` is a callable Python seam, not a JSON field
or CLI flag. Run A/B through real independent containers and the actual
manager start/failure owners. If C becomes uncertain instead of positively
absent, preserve the hold and judge against the predeclared expected ending;
never repair it with retry, release or restart.

## 3. Submission and task document shapes

**Confirmed source:** `job_manager/documents.py` accepts closed
`baton.v12.job-submission/1` documents: `schema`, `submission_id`, `jobs`.
Each Job has exactly `job_id`, `input_digest`, `policy_digest`, `test_scope`,
`terminal_policy`, `stages`. Each stage has exactly `kind`, `work_id`,
`profile_name`, `profile_digest`, `depends_on`. No failure/delay/hook/command
field may be added to that schema. The task and deployment are separate
documents, not extra Job members.

Freeze one document with these seven stages:

| Job | Stage | Dependencies | Work binding |
| --- | --- | --- | --- |
| A | implementation | `[]` | `<A_WORK_ID>` |
| A | review | A implementation | `<A_WORK_ID>` |
| A | integration | A review | `<A_INTEGRATION_WORK_ID>` |
| B | implementation | `[]` | `<B_WORK_ID>` |
| B | review | B implementation | `<B_WORK_ID>` |
| B | integration | B review | `<B_INTEGRATION_WORK_ID>` |
| C | implementation | `[]` | `<C_WORK_ID>` |

For example, A review's dependency is
`{"job_id":"<A_JOB_ID>","kind":"implementation"}`. Each role's
profile name/digest must match its eligible pool workers. A and B implementation
Works differ; each review is over its own implementation Work, as the current
assembly requires. Have the accepted assembly supply integration Work and
Authority bindings rather than assuming they are the implementation Work.
All Work ids here are v12 deployment identities, not the v11 planning ids.

Use unique submission and Job ids for a fresh proof. Let `submit` and
`episodes.open_first` derive offer/attempt identities; retain the returned
identities and verify them against status rather than inventing an attempt
formula. A correction gets new episodes through its driver while retaining the
line. An exact resubmission is idempotent, not a new clean run.

**Confirmed task schema:** `claude_agent._read_task` reads exactly
`schema: "baton.dogfood-task/2"`, `task_id`, `instructions`, `verification`
(one non-empty argv list), `source_root: "/input/source"`, `source_profile`,
`declared_base`. Use the accepted persistent-line profile (currently
`git-line`) with `<BASE_OID>` after assembly confirms its nomination/mount
contract. Hash exact delivered task bytes. Job input/policy and stage-profile
digests come from their accepted owners; none is presumed to equal the task
hash or the source commit.

## 4. Companion refusal: precise supported boundary and unresolved path

**Proposed negative content:** edit only existing `tests/test_guard.py` so its
fixed-sentinel assertion is weakened to unconditional truth. It is outside
both successful Jobs' accepted existing-test scopes. The proof Work authorizes
constructing this negative fixture, not integrating it. Retain the exact
negative bytes/digest separately; do not edit an accepted candidate, checkpoint,
review or immutable bundle in place.

**Confirmed from current source:**

- `integration.admission.resolved_account` resolves the actual Job scope and
  accepted checkpoint/receipts. `driver.admit_accepted` requires bound
  accepted evidence and ordinary-test requirements. A rejected A checkpoint
  does not become an eligible integration by operator request.
- `integration_workload._authorized_scope` validates the authority account,
  frozen accepted review, Job/scope correlation and review material. It does
  not classify every test by filename. The account enumerates grants; an
  empty account is not permission for every other changed path.
- The provider prompt requires whole-candidate semantic evaluation against
  scheduled scope and frozen review documents, and instructs refusal of an
  unscheduled existing-test change. The actual callable workload boundary is
  `integration_workload.integrate(...)` and the typed runtime entry supplies
  its assignment, launch, bundle and isolated target.
- `test_an_unscheduled_existing_test_change_is_the_providers_to_refuse` in
  `tests/manager/test_integration_worker.py` uses `WorldCase.derived` to
  build a negative bundle and a deterministic provider behavior `refuse`.
  It expects `held` / `import-incomplete`; it checks the selected file and
  prompt. It does not exercise an automatically submitted, genuinely
  independently reviewed negative proposal or observe the complete target.
- `test_a_clean_provider_refusal_after_writable_work_is_still_held` pins the
  reason: unchanged ending bytes do not prove that no write occurred between
  observations. `refused` is reserved for a turn that exposed no provider.

**Conclusion:** a callback returning an accepted verdict, rewriting a review
disposition, deriving an allegedly accepted bundle from another candidate, or
calling `admit_accepted` manually would substitute for required proof. Those
fixtures are useful component tests; they are not a zero-transition live
companion. Corrupting bundle bytes after acceptance instead exercises digest
or correlation refusal, not the semantic out-of-scope-test requirement.

**Decision recorded in W115604:** the owner must specify either a reviewed
automatic negative-fixture boundary with genuine retained provenance that
fulfils the existing assertion, or the missing composition needed to reach
it. This report establishes no such complete path. In particular, allowing a
deliberately policy-invalid proposal to pass an independent review cannot be
silently called ordinary acceptance. Any changed proof interpretation needs
an explicit ruling and targeted independent review.

Preserve one successful A/B target. A companion that ends held on that target
before both imports finish may retain their exclusion and invalidate the
demonstration. A separate disposable target or an automatic trigger after both
imports is a placement proposal, not a currently supplied factory capability
or approval to add another submission. C must still remain the deliberately
failed Job; it cannot be retried into the companion. Do not add an unapproved
fourth Job while claiming the three-Job plan is frozen.

Freeze complete target observations around the eventual negative attempt:
every regular file's bytes/hash and mode, directories/modes, symlink or other
entry type, and the protected Git metadata, using no-follow observation.
Compare the full set including absence/addition/deletion, not just the changed
path. Also retain evidence at the writable-exposure boundary sufficient to
exclude intermediate writes: provider non-invocation for a pre-provider
refusal, or an explicitly reviewed stronger observation method for a semantic
hold. Before/after equality alone cannot turn the latter into the former.

## 5. Capacity, identities and serialized imports

**Proposal after the factory limitation is placed:** three independently
identified implementation workers I-A, I-B, I-C; two independently scheduled
review workers R-1, R-2; one integration worker G serving the one successful
target. These are symbolic slots, not minted participants. Use six distinct
participants and canonical principals, worker ids and role-correct sessions.
Each attempt/incarnation has separately retained runtime id, output and log
sink; A and B have separate persistent line ids and disk-backed roots. Bind
C to a distinct fault profile/eligible worker so its retained capacity cannot
take either success slot. Reviewer principals must differ from every producer
they assess, including earlier correction episodes; an alias is insufficient.

`scheduler.reserve` selects by lane, kind and profile, excludes occupied
worker/principal capacities, and applies review independence. Three available
implementation slots keep both success slots usable even if C is quarantined.
Two review slots preserve independent review capacity without making a long
review serialize the whole campaign. G is a distinct integration-capable
allocation even though integration belongs to the scheduler's implementation
lane. Do not count one principal twice or infer capacity from container count.

**Observed limitation, W115599:** `_held_workers` refuses repeated roles;
`StageDeployment._roles` and `line()` select one configured implementation
source/Work; `_prepare` reaches that same line. `_pool` therefore supplies only
one implementation worker. A valid one-Job factory and a general scheduler
are insufficient together to freeze the six-slot arrangement. Separate
factories sharing stores or a custom multiplexer would be a new composition,
not an authorized stopgap supplied by this report.

No cross-Job dependency delays A/B implementation. Their own stage dependencies
order implementation → review → integration; correction is driver-owned.
Use the one coordinator/target identity for both successful imports, with a
single G runtime at a time. Retain lease acquisition through positive
quiescence, Authority receipt/read-back and release. Verify disjoint path
imports preserve the other's bytes without an intermediate commit or manual
target update. If that common-base target policy is incompatible with the
accepted assembly, return the precise mismatch before submission.

## 6. Resource and evidence budget proposals

These are proposals for the freeze owner to accept against actual host limits,
not measured capacity or installed quotas. No current resource probe was run.

| Item | Proposed limit/method |
| --- | --- |
| Whole proof | 20-minute wall deadline from initial submit receipt to final A/B completion plus C/companion observations; missing required result at deadline is non-satisfying, no retry |
| Stages | 4 minutes per implementation attempt, 3 minutes per review, 2 minutes per integration; C injected at its first eligible start; tune once before freeze to the accepted provider budget |
| Sampling | 1-second manager status/CPU cadence, 2-second storage cadence; retain actual timestamps and overhead |
| Runtime resource posture | Current OCI owner specifies 2 CPUs, 2 GiB memory, 512 PIDs per runtime; `/tmp` 64 MiB and `/dev/shm` 16 MiB, private bounded scratch |
| Host reservation | Conservatively budget up to 12 CPU shares and 12 GiB runtime memory for six slots plus explicit manager/OS headroom; reduce simultaneous active slots only if both overlaps remain possible |
| Disk need | Propose 1 GiB declared workspace need per active slot and at least 12 GiB free external disk for persistent lines, checkpoints, attempts and evidence; refine with accepted custody layout |
| Run storage thresholds | Propose 1 GiB per private line/attempt and 2 GiB retained outputs/logs total as observed abort thresholds; count retained prior A checkpoint and correction output explicitly |

`single_worker.workspace_capacity` declares a preflight free-space NEED; it
is not an enforced quota. Neither the disk proposal nor sampled thresholds
may be reported as a kernel ceiling. Scratch has its actual mount limits;
all source checkout/build/test artifacts, output and logs remain disk-backed.
Keep state/output/custody/credential roots outside the participating checkout,
on a filesystem proven non-tmpfs by the accepted owner.

Freeze these calculations and collection surfaces:

- Wall/per-stage latency uses one monotonic measurement domain with UTC
  correlation to retained manager and OCI start/end events. Implementation
  overlap is `min(end_A, end_B) - max(start_A, start_B) > 0`. Apply the same
  calculation to an A review and B implementation. Status `running` alone
  is not a runtime interval; independently bind process identities and events.
- Integration lease intervals are half-open; assert every pair on the target
  has empty intersection and every later start follows prior positive shutdown
  and release. A result file while the writer lives does not end the interval.
- CPU: retain cgroup/process CPU nanosecond counters and elapsed seconds;
  report CPU-seconds and average cores (`delta_cpu_ns / 1e9 / elapsed_s`).
  State whether percent means one core or the assigned two-core quota. Include
  manager CPU separately and preserve counters before runtimes disappear.
- Workspace/output: record both logical byte size and allocated disk blocks,
  avoiding double-counting hard links or overlapping roots. Report per-attempt
  and per-line values plus the complete retained evidence total. A sampled
  maximum is a lower bound on true peak, not an exact high-water mark. Freeze
  an accepted peak-accounting method if exact peak is required.
- Scratch: observe both tmpfs mounts from the runtime namespace before normal
  cleanup and retain samples/limits. Missing samples cannot be reconstructed
  from the absence of a destroyed container. Provider/kernel high-water
  telemetry, if available and accepted, should supplement samples.
- Status: retain queued, offered, claimed, starting/waiting/running, reviewing,
  changes-requested, integrating, completed and exceptional evidence. Short
  states need the actual canonical event history or transition-time observer;
  never label a reconstructed state a captured status snapshot. Confirm the
  accepted assembly supplies those public locators; do not read a store raw.
- File/custody: baseline and final source observations plus read-only mount
  facts; distinct disk-backed writable roots; same A line across new attempts;
  retained immutable n/n+1; actual intake/retention/cleanup receipts and
  post-cleanup reopen/digest verification. Reuse the assembly's unchanged
  custody method but capture this run's own identities and mounts.
- Interventions: timestamp every human act, distinguish initial submission,
  predeclared forced-review/policy decision, read-only exceptional observation
  and final Git action. Ordinary manual transitions must total zero. Any
  emergency stop is recorded as such, never hidden as normal completion.

The eventual proof run needs its question, exact scope and budget recorded
BEFORE execution under docs/EFFECTIVE-BATON.md. Reuse unchanged accepted
provider evidence; the new question is whether this one submitted multi-Job
composition demonstrates the required joined behavior. Do not repeat provider
suites as a substitute for that missing evidence.

## 7. Minimal accepted inputs and command templates

### W110774 port/driver handoff

Supply accepted hashes/review and final public constructor signature for
`tools.integration_worker.IntegrationRuntimePort`, plus `prepare(stage, job)`,
`run(delivery, assignment)`, `refresh(attempt_id)`,
`observed(attempt_id, assignment)` and `continue_accepted`. Names/signatures
here are observed source, not independent acceptance.

The constructor currently requires resolved coordinator/manager/Job stores,
Authority and assignment port; integration/checkpoint profiles and object
runner; line/proposal/target identities and target directory; delivery,
bundle, launch, storage and credential homes; instruction bytes; runtime
identity, adapter/toolchain/input manifest; engine/run capability, workspace
group/capacity; launch session/contract, network and credential resolution/provider.
Each value must come from its named owner rather than from an opaque target id
or the proof writer's guess. In particular target id AND directory are inputs.

Observed continuation signature:

```text
continue_accepted(store, manager, jobs, authority, verification, reviewer,
                  approver, integrator, *, canonical_target_id, line_id,
                  proposal_id, policy_generation, profile, attempt_id,
                  launch_root, workspace_group, required_tests)
```

No runtime port is supplied to continuation, so it cannot start another writer.
The handoff must identify valid initial preparation/start, refresh and normal
continuation ordering, the live-process marker owner, lost-marker restart hold,
typed observation, Authority receipt/read-back and completion/release evidence.
Return focused acceptance and required-gate evidence, including real retained
target observations, rather than only API declarations.

### W103083 assembly handoff

Supply the accepted factory and read-only observation entry points, final
closed configuration schema/example, exact role/profile/image/engine/network
bindings and isolated credential REFERENCES. Include per-Job task/source/line
mapping and the placed multi-Job pool capability from W115599. Return target
binding/observation policy for two disjoint imports, all external state and
artifact roots, and shared-file candidate identities after port registration.

Derive `required_tests` from the held implementation task and manifest for the
actual accepted writer, including correction: the current closed members are
`argv`, `input_manifest_digest`, `task_digest`, `task_id`. Supply the real
`end_review_from_result` wiring, integration preparation/start/refresh/continuation
call sites and typed read-only status (ordinary worker exchange is insufficient
for an integration result). Retain the required one-Job lifecycle/custody and
selected restart/held-uncertainty acceptance, with exact reusable evidence.

### Proof-owner inputs beyond the two providers

Supply the operator-created base and full fixture bytes; frozen A/B/C Job and
task documents; accepted test scope/correction policy; all v12 Work/participant/
principal identities and resource limits; the installed one-C failure selector;
the W115604 companion decision/trigger; precise timing/peak/target observers.
Neither provider's mere acceptance fills in these demonstration choices.

### Existing CLI templates — NOT READY TO RUN

Every `<...>` is an unresolved required freeze value. Paths below refer to the
accepted v12 Python deployment; these are not invocations of the v11 Baton
coordination authority. Execute no template until provider acceptance,
configuration placement and final delta review are complete. The source
currently names `tools.stage_execution:factory` and
`tools.stage_execution:observing_factory`; their present one-Job composition
is the limitation above, so no working replacement name is invented here.

```sh
cd '<ACCEPTED_V12_PYTHON_ROOT>'
export BATON_V12_STAGE_EXECUTION_CONFIG='<APPROVED_EXTERNAL_CONFIG_JSON>'
```

One initial submission, its document already containing A/B/C:

```sh
python3 -m tools.job_manager --store '<JOB_STORE>' --incarnation '<SERVING_INCARNATION>' --authority-uuid '<V12_AUTHORITY_UUID>' submit --document '<FROZEN_ABC_SUBMISSION_JSON>'
```

Serving composition, installed/started according to the accepted deployment
before the operator submits (it owns all ordinary transitions):

```sh
python3 -m tools.job_manager --store '<JOB_STORE>' --incarnation '<SERVING_INCARNATION>' --authority-uuid '<V12_AUTHORITY_UUID>' serve --control '<CONTROL_STORE>' --operations '<ACCEPTED_FACTORY_MODULE:ATTRIBUTE>' --interval 1
```

Read-only observation using the accepted paired observation identity policy:

```sh
python3 -m tools.job_manager --store '<JOB_STORE>' --incarnation '<ACCEPTED_OBSERVER_INCARNATION>' --authority-uuid '<V12_AUTHORITY_UUID>' status --control '<CONTROL_STORE>' --observe '<ACCEPTED_OBSERVER_MODULE:ATTRIBUTE>'
```

Run logging/sampling must be configured before submission; ordinary terminal
output is not automatically a retained evidence bundle. No command to offer,
claim, set a verdict, advance correction, admit/import, retry, recover or restart
belongs in the demonstration recipe. Exact fixture-injection and resource
observer commands remain unsupplied; calling them ready would hide the open
inputs this preparation was tasked to expose.

## 8. Targeted material-delta review and handoff

Review only changes from the accepted 2026-09-04 proof plan plus the approved
2026-09-08 third-fault-Job ruling, binding the final concrete bytes:

1. **Three-Job document:** A/B both integrate, C fails once; no automatic retry
   or extra submission; seven stage bindings and no A/B implementation gate.
2. **Multi-Job composition:** actual distinct source/Work/task/line selections,
   six distinct capacity principals, two coding runtimes and independent
   reviewer capacity; current one-Job limitation actually resolved and accepted.
3. **Correction:** exact scheduled expectation change, truthful n refusal,
   sealed reviewer verdict, fresh n+1 assignments on the same line; no canned
   approval/correction callback, no second clone/candidate-tree copy.
4. **Failure:** exact one-attempt engine injection installed before submit,
   failed-start versus running-crash claim explicit, positive absence or held
   uncertainty accurately projected, unaffected slots and A/B completion proved.
5. **Companion:** actual automatic boundary/provenance and accepted semantics,
   exact unscheduled test bytes, no false approval, no target hold obstructing
   either success; complete target and intermediate-write evidence sufficient.
6. **Integration seam:** accepted port preparation before admission, normal
   refresh/continuation rather than restart adoption, receipt/read-back before
   release, one target and disjoint common-base import semantics.
7. **Custody and observation:** accepted one-Job custody evidence applies to
   these bytes/interfaces; real run identities retained; typed status remains
   read-only and short-lived states have a declared capture surface.
8. **Budgets:** fixed clocks/units/sampling, true versus sampled peak claims,
   workspace need versus quota distinction, accepted images/profiles/resources,
   retained evidence roots and zero ordinary intervention accounting.

Missing any required input keeps the run unfrozen. An unexpected component
failure is returned to its owner and a later proof starts with a fresh
submission; it is not repaired inline. Passing all these checks authorizes
the bounded demonstration only. The final independent assessment must bind
its actual retained evidence before calling the narrow design promising.

Preparation delivered to baton.ops for the concrete decisions above. W115599
and W115604 are lightweight owner-placement records without new dependency
edges or duplicate dossier bindings. They preserve the observed limitation
and unresolved proof boundary; they do not amend another Handler's live scope.

Document verification: checked CLI spellings against the argument parser,
rechecked the moving port's public signatures, and directly scanned this new
untracked Markdown file for trailing whitespace and unfinished TODO/FIXME
markers (none). `git diff --check` also returned clean, but it does not cover
untracked content, so it is not the basis of that content check. These are
read-only documentation checks, not proof execution or provider tests.
