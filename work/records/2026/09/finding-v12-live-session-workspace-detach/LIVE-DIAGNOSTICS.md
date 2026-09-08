# Runtime diagnostic candidate — W106673

Prepared by baton.tuner, claim 110238, under owner reroute 110236 and
review-2026-09-07T06-25-36Z.md. This candidate is preparation only. The accepted
retained actual-Claude process/session/workspace correction remains valid; its
11.936325138-second observation is not a restoration comparison. Earlier source,
manifests and export bytes remain unchanged. The restored-first failure cause is
still unknown; no credential, provider or restoration failure is inferred.

The separate sources are `evidence/live_controller_diagnostic.py` and
`evidence/live_supervisor_diagnostic.py`. The manifest binds both and the prior
90 inputs. The controller stages the new supervisor bytes at the same reviewed
container target, so it needs no new worker mount. Image/model/CLI argv, source
selection, private credential delivery, process/mount/receipt checks, resources,
work/ending deadlines and teardown authority remain unchanged.

## Observation contract

Host records have closed arm, outer operation, command operation, turn number,
stage and refusal fields. Outer operations distinguish start/turn/detach/attach/
consume/shutdown; command operations distinguish start/turn/identity/probe.

| Observation | What it establishes |
| --- | --- |
| turn-intent | Host began this turn attempt; no successful dispatch implied. |
| command-write-intent | Host is about to write the supervisor command. |
| command-write-completed | Full host command write and flush returned successfully. |
| provider-write-intent | Supervisor is about to write the provider user frame. |
| provider-write-completed | Full provider user-frame write and flush returned successfully. |
| provider-response-observed | Supervisor parsed a provider **result** frame, before success/identity checks. |
| response-observed | Host parsed a supervisor response, before response-shape and post-turn checks. |
| turn-complete | The existing response/identity/time and post-turn quiescence checks all passed. |

Provider assistant text and other intermediate frames remain discarded. A parsed
result observation is distinct from its validation; an invalid/incomplete byte
stream need not produce such an observation. A short or failed write may have
had effects, so absence of write-completed never claims no dispatch occurred.
Neither a host write nor a provider write proves provider acceptance/completion.

Supervisor diagnostic frames carry only allowlisted labels, bounded turn/time/
errno values and fixed refusal codes. Host verifies arm/operation/turn context,
rejects unknown fields, and accepts at most 32 frames within the original
per-command deadline. A pre-increment refusal can identify the previous completed
turn count; it cannot become a completed write for the next turn. Refusal codes
come from explicit source literals. Unknown exception arguments/types become
`unclassified`/`other`; no arbitrary exception string conversion occurs.

Normal supervisor responses now have an exact allowed field set and bounded
typed values. Unexpected fields fail closed before their contents can enter the
event log. No prompts, provider text, tool arguments, transcripts, private paths,
credential data, raw exception strings or custom exception class names are
added to diagnostics. Only reviewed identity/model fields remain in ordinary
validated response records.

Provider milestones must arrive once in their fixed order. Supervisor timestamps
are retained as supervisor_monotonic_ns beside the host observation timestamp,
so emission time is not confused with receipt time.

## Truthful result summaries and unchanged custody

Result milestones count observed container creation, initialization, host/provider
writes, provider results, validated completions and verified consumptions. They
separately report retained correction, restored initialization/correction and a
verified matched pair. They derive from this invocation's controller events;
missing observations are explicitly inconclusive about side effects.

The copied preparation-only limitation and blanket historical-consumption denial
are removed from future results. Results instead state that future work is not
admitted after ending and preserve observed prior consumptions/corrections.
Actual-model observations do not claim resume support or hard billing limits.
Failure in a later arm cannot erase an earlier verified correction or turn it
into a completed comparison. Existing historical result files are not rewritten.

Instrumentation wrappers retain original detach/consume/shutdown method bodies.
Receipt consumption still precedes any artifact read; an unconfirmed stop still
retains credential delivery. No diagnostic event grants a receipt, admits work,
widens the idle process set or changes the verifier. The source snapshot, setup
accounting and fixed export policy from the setup correction remain in force.

## Verification and next decision

Offline commands:

```sh
/usr/bin/python3 -B /home/sl/src/baton/work/records/2026/09/finding-v12-live-session-workspace-detach/evidence/live_controller_diagnostic.py --audit
/usr/bin/python3 -B /home/sl/src/baton/work/records/2026/09/finding-v12-live-session-workspace-detach/evidence/test_live_diagnostics.py
```

Focused fault tests cover before-write, partial-write, after-write, parsed-response,
post-response identity and post-turn quiescence failures; provider failed-result
observation; arm/turn correlation; unknown-field/code redaction; and unchanged
receipt/ending refusal. A read-only check against the accepted retained export
confirms truthful partial-result summarization without rerunning that arm.

The public `--run` entry is disabled and returns `execution-scope-not-selected`
after its offline package audit. No operator invocation is proposed or authorized
by this candidate. The existing pair orchestration remains as a source reference,
not a decision to repeat the retained arm. After independent diagnostic review,
baton.ops chooses restored-only continuation versus a new matched pair and binds
any resulting invocation separately. Separate timing evidence must never be
presented as the original matched run. No live/provider/credential operation,
production change, stronger cleanup or adoption follows from this preparation.
