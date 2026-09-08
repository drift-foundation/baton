# W71879 proof preparation — 2026-09-08

Prepared by baton.prompt under Slawomir's critical-path preparation instruction.
Owning Work W71879; parent W71830. This is planning while providers are gated,
not a frozen run plan, independent sign-off or execution permission.

## Already settled

The demonstration contract was independently approved in
review-2026-09-04T14-10-08Z.md. PLAN item 1's old pending label is superseded by
that review. Re-review only material deltas when freezing the real deployment.
Existing provider acceptance gates still constrain freeze and execution.

One submission must prove concurrent independent implementation, independent
review, one same-private-line correction, scoped test work, serialized imports,
refusal before target mutation, observability and failure containment.
Ordinary operator lifecycle transitions after submission must number zero.
No worker retry, manager restart or manual integration may repair the run.

## Approved demonstration shape; concrete Job inputs await freeze

These are contract roles to instantiate against the chosen immutable baseline;
they are not invented executable submission JSON or permission to modify files.

| Contract | Bounded work | Required ending and evidence |
| --- | --- | --- |
| A: correction and planned test work | One small behavior change with an explicitly scheduled existing-test edit; exact source/test paths named at freeze | Independent reviewer requests one bounded correction at revision n; fresh assignment reuses the same private line; later revision accepted and integrated |
| B: independent work | One similarly small change on disjoint paths from A, using the same immutable baseline and one canonical target | Implementation overlaps A; B's coding overlaps an independent review; accepted proposal integrates serially with A |
| Companion refusal | One specifically named existing-test change outside the relevant accepted scope | Real admission/import boundary refuses with complete target bytes/modes unchanged; never counted as either successful integration |
| C: fault containment | A minimal independent Job with one predeclared worker/runtime fault | Remains exceptional or recovery-required according to accepted scheduler evidence; A/B continue without retry or stack restart |

Why C is required for this selected scenario: W71877's accepted 2026-09-03 policy automatically replaces
only abandoned-after-restart episodes. A deliberate failure normally leaves its
Job exceptional until explicit operator retry, while this proof forbids that
retry. Making one of exactly two intended successful Jobs fail would prevent
showing both accepted imports. The umbrella says at least two Jobs, but the
older proof review refers to exact two documents. Slawomir explicitly approved
this demonstration plan on 2026-09-08: A and B complete, C carries the deliberate
failure, all in one submission. This supersedes that exact-two-document scenario
while preserving the original overlap, two accepted imports, independent review,
refusal and zero-ordinary-transition requirements. No automatic retry is added.

At freeze choose the exact companion-refusal injection point and trigger using
accepted component capabilities. It must reach the actual refusal boundary
without fabricating independent approval or issuing an ordinary manual workflow
transition. If the chosen composition cannot supply that path, report the exact
gap before submission; do not improvise inside the demonstration.

## Freeze checklist and responsible supplier

| Required frozen value | Supplier |
| --- | --- |
| Immutable baseline and readable retained identity; exact A/B paths, designated test path and disallowed path; full baseline target observation | W71879 author with operator Git ownership |
| Valid Job documents, unique submission/Job/Work/attempt identity derivation, input/policy digests and per-stage dependency lists | W71879 using accepted submission schema; no cross-Job dependency between A/B implementations |
| Factory constructor, serving/observation entry points, configuration schema, engine/image/profile selections and allowed identities | Accepted W103083 handoff consuming W110774 |
| Exact integration evidence/target bindings and public continuation inputs | Accepted W110774 handoff |
| Role/participant/principal/session separation and pool capacity sufficient for required overlaps despite the fault allocation | W71879 against accepted pool configuration |
| Bound correction revision/trigger; failure injection point, expected ending and automatic containment observations | W71879 freeze, within accepted component behavior |
| Absolute external state/output/log roots, persistent private lines, target baseline, disposable refusal observation locations | Approved deployment inputs at freeze |
| Exact focused verification commands, test-change scope, selected restart cutpoint if reused, and immutable evidence hashes | Accepted assembly evidence plus W71879 delta plan |
| Wall/per-stage budget, sampling interval, CPU unit, storage ceilings and retention size calculation | W71879 freeze with operator resource limits |

No placeholder is a ready-to-run command. The existing CLI spelling, confirmed
from tools/job_manager.py, is: global --store, --incarnation, --authority-uuid;
submit --document; serve --control --operations [--interval]; status --control
--observe. The final handoff must instantiate these with actual approved values.
Status observation must stay read-only; serving owns runtime reconciliation.

## Evidence to collect once

- The accepted submission and configuration with credential-free references,
  baseline/profile/image identities and candidate hashes.
- Durable runtime intervals for two distinct implementation assignments:
  overlap = min(end times) - max(start times), strictly greater than zero.
  Apply the same calculation to review versus unrelated coding.
- Every integration lease interval on the target, with zero overlap; corresponding
  worker result, positive quiescence, Authority receipt and release evidence.
- Original checkpoint n remains immutable/resolvable; correction assignment is
  fresh while private line identity persists; checkpoint n+1 is independently
  accepted. Reuse assembly's custody proof where bytes/interfaces are unchanged,
  and capture the real two-Job run's own line/mount observations.
- Complete canonical-target before/after byte/mode observations around refusal.
  A reported refusal or a single unchanged file is insufficient.
- Failed allocation ending and unaffected Job progress; no inference from silence.
- Status at required states. Polls alone can miss brief states: correlate retained
  canonical event history and observations, rather than fabricating snapshots.
- Wall and per-stage duration, process/container CPU counters with units and
  measurement interval, peak private workspace/scratch use, retained artifact
  sizes and every operator act. Freeze methods and limits before submission.
- All missing evidence, injected versus unexpected failures, and final assessment.

## Stop and handoff rules

Before running, independently assess material deltas from the already approved
proof contract, including the approved C fault scenario. Preserve no ordinary transitions.
A real component failure stops the proof; return it to its owner and perform a
fresh submission only after correction. Keep nonblocking hardening separate.

After the one clean proof, independent assessment binds the exact retained
evidence and recommends satisfying or non-satisfying disposition. Include the
exact W71879 owner closure command and, after its satisfying closure and checking
all remaining children/gates, the W71830 command. Never batch a parent close
ahead of its prerequisites or replace independent assessment with this checklist.
