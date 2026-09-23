# Preparing W239533's independent reviewer Job

Prepared by baton.tuner under W244180, claim244188, 2026-09-23 UTC.
**Preparation only: no executable reviewer packet is accepted or delivered here.**
Resolve every pending item in [INPUTS.md](INPUTS.md) before selecting execution.
W239528 must first deliver an independently accepted proposal and positive
cleanup. W236087's correction/resume remains a later, separate Job.

## 1. Recheck the prerequisite and select immutable inputs

Use the deployment-supplied v11 launcher, explicit config and your own participant
for each standalone coordination operation. For this preparation identity:

```sh
/home/sl/opt/baton/v11/0650c61/bin/baton --config /home/sl/baton-v11.14aecfb/baton.json --participant baton.tuner detail work=W239528
```

```sh
/home/sl/opt/baton/v11/0650c61/bin/baton --config /home/sl/baton-v11.14aecfb/baton.json --participant baton.tuner detail work=W239533
```

Read the latest handoff, discussion and independent review, not just status.
At preparation, W239528's custody source fix is accepted by
[review-2026-09-23T03-19-21Z.md](../finding-v12-single-implementation-proof/review-2026-09-23T03-19-21Z.md).
That accepts adapter SHA256
`18c34ff52faa150237df0c8d0206b805801ee71cb9e7a4ec6e84e4379d7f9d8d`;
it does **not** establish a corrected image, successful baseline or accepted
proposal. The old successor selections bind the old adapter. Do not run them.

Record the accepted proposal/result manifests, immutable artifact locators and
digests, producer assignment and checkpoint, base/head/tree, and stopped-runtime
and cleanup receipts. File existence or a prior provider's successful exit is
insufficient. Verify the retained bytes through their supported custody readers.
Preserve historical failures and consumed execution grants.

## 2. Prepare the separate review contract

The next executor must supply a distinct Job/run identity and a review task
whose criteria are independently delivered, digest-bound inputs. Its launch role
is `review`; no implementation, integration, correction or context restore is
selected. Worker, participant and principal must differ from the producer's.

The existing adapter consumes `baton.dogfood-task/2` with exactly `schema`,
`task_id`, `instructions`, `verification`, `source_root`, `source_profile` and
`declared_base`. `source_root` is `source` under `/input`; review requires the
Git-line profile. Criteria go in `instructions`; `verification` is a nonempty
argv list, not proof that those checks ran. Bind the actual accepted base and
checkpoint, not a mutable branch name or copied implementation task.

The reviewer must assess actual read-only proposal bytes and explain its own
decision. The provider writes `baton.review-report/1` with `schema`, `verdict`
and nonempty `findings`; the allowed verdicts are `accepted`,
`changes-requested`, and `rejected`. This is a report contract, **not a file for
the operator to prepopulate**. The adapter authors `findings` and `logs` outputs;
the manager reads `baton.checkpoint-review/1` from the frozen findings and
cross-checks base/head/tree and assignment provenance. Do not inject a verdict
through `end_review` or infer one from process exit status.

## 3. Preflight and bounded execution — command pending

There is no verified copyable start command for this separate Job yet. The
implementation-only `baseline.py` rejects review stages, and the older resume
`supervisor.py` requires at least one implementation invocation. Neither is a
review-only supervisor. Generic `manager serve` is not a substitute: it runs a
control loop without this Job's invocation limit and cleanup/outcome contract.

Before owner selection, the W239533 executor must deliver and independently
verify a packet/composer and one-run supervisor that:

1. Binds the accepted proposal to the exact checkpoint without creating a new
   implementation or weakening same-Work/Authority and independence checks.
2. Rejects incomplete/digest-mismatched inputs, consumed identity and store
   conflicts before side effects; pins actual manager, adapter and image bytes.
3. Admits one review invocation only, with retry disabled; names finite turn,
   total and reserved cleanup limits, plus an actionable no-progress rule.
4. Closes admission before cancellation, accounts for every discovered attempt,
   drives the ordinary ending/cleanup path, and publishes an outcome even on
   interruption or failure. It must not start correction on changes-requested.
5. Proves these boundaries through the real manager/adapter composition with a
   deterministic provider first, including missing/malformed/foreign verdicts,
   wrong checkpoint, self-review, repeated submission, interruption and cleanup
   uncertainty. Simulated verdict fixtures must be labelled as such.

The earlier 180/300/60-second implementation limits are historical inputs,
not approval of W239533's bounds. State the real-provider question if a live
run is selected: whether the actual reviewer receives the independent criteria
and retained bytes and returns its own valid report through the production
boundary. Deterministic checks cannot establish actual provider behavior.
Do not run any provider merely to prepare this document.

## 4. Inspect progress and logs using existing interfaces

The following are verified command **forms**, conditional on an accepted future
packet. Set the operands from that packet; none has an implicit default here.
`V12_STACK` is the accepted absolute bundle executable (not the v11 launcher).
`STATUS_JSON` is its published status snapshot; `JOB_ID` and `STAGE_ID` are v12
identities from that snapshot. `LOGS_ROOT` is the selected launch home's `logs`
directory, and `ATTEMPT_ID` is the manager-recorded attempt, never a guessed ID.

```sh
"${V12_STACK:?accepted v12 bundle required}" view --status "${STATUS_JSON:?published snapshot required}" --job "${JOB_ID:?v12 Job required}" --ticks 1
"${V12_STACK:?}" view --status "${STATUS_JSON:?}" --job "${JOB_ID:?}" --stage "${STAGE_ID:?}" --artifact findings
"${V12_STACK:?}" logs --logs "${LOGS_ROOT:?}" --attempt "${ATTEMPT_ID:?}" locators
"${V12_STACK:?}" logs --logs "${LOGS_ROOT:?}" --attempt "${ATTEMPT_ID:?}" read --stream provider.stderr --from-byte 0 --limit 65536
"${V12_STACK:?}" logs --logs "${LOGS_ROOT:?}" --attempt "${ATTEMPT_ID:?}" follow --stream provider.stdout --from-byte 0 --bound 65536 --once
```

`view` rereads a file, not the manager; `--ticks` does not publish fresh status.
Use only artifact names actually published for that stage. Retain observation
times, stale/disconnected indicators and raw log capture state. `absent`,
`inaccessible`, `partial`, `truncated` and `failed` are not complete evidence;
even a finished stream proves no verdict or cleanup. Resume log reads from the
returned byte offset. These bounded forms do not wait indefinitely.

If the selected packet permits a status producer, the existing form is:

```sh
BATON_V12_STAGE_EXECUTION_CONFIG="${DEPLOYMENT_JSON:?accepted deployment required}" "${V12_STACK:?}" manager --store "${JOB_STORE:?existing Job store required}" --incarnation "${READER_INCARNATION:?selected reader identity required}" --authority-uuid "${AUTHORITY_UUID:?v12 authority required}" status --control "${CONTROL_STORE:?existing control store required}" --observe tools.stage_execution:observing_factory
```

This emits JSON to stdout. Arrange publication through the selected packet;
never overwrite retained evidence. Omit `--control` and the projection is
uncanonical; omit `--observe` and exchange is unobserved. Runtime refresh
remains the serving loop's responsibility. **Do not execute this against
unselected or missing stores:** current CLI status uses ordinary store openers,
not the read-only opener. This preparation ran only parser help, no status or
store access. File-only view/log inspection is the available store-free path.

## 5. Stop, retain evidence, and hand off

The reviewer supervisor's exact stop command is pending along with its start
command. Require a tested Ctrl-C/SIGTERM path with a bounded cleanup window and
retained outcome locator. Stopping a log follower stops only that reader.
Generic manager `serve` handles SIGINT/SIGTERM by exiting after the current
tick; that alone does not prove all worker runtimes stopped or cleanup completed.
Do not substitute process-name kills, raw store edits or manual evidence deletion.

For the selected run, inspect the complete admitted/discovered attempt set,
exact runtime identities, terminal/quiescence observations, assignment fencing,
retention decisions and each committed cleanup record. Existing positive cleanup
vocabulary is `complete` or `retained`, with the latter's retained artifacts
identified by policy. A missing/failed/uncertain cleanup is outstanding, not
success. Preserve a held outcome and report its actionable missing evidence;
never spend a second invocation to improve the answer.

Accept the proof only with an attributed valid verdict **and** positive stop
and cleanup evidence. A changes-requested or rejected verdict can be a valid
review result; it is not acceptance of the proposal. Missing or invalid reports
are not rejection. Pass the immutable review result, criteria digest, attachment,
checkpoint, result/verdict IDs and digests, execution limits/timings and cleanup
evidence for independent acceptance under W239533. W236087 may then consume the
accepted evidence for separately selected correction/resume; this recipe does
not run it or close either Work.

Source and verification provenance: [PROGRESS.md](PROGRESS.md).
