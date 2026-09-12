# Combined read-only judge observation and accounting candidate 152563

Owner152560, claim152563, 2026-09-12T13:03:18.877320+00:00. Return directly to baton.feat, Next baton.ops, for independent review of the combined bytes. This supersedes the unresolved product capability gap in ACCOUNTING-150501.md for this new candidate only. Partial and historical records remain evidence.

## Exact product scope and behavior

Changed `v12/python/src/baton_v12/worker_manager/store.py`: public ControlStore.open_readonly acquires only an existing recognized manager in SQLite mode=ro, adopts the existing complete ownership/schema checks in one snapshot, validates the clock and closes failed acquisitions. It does not initialize a database, request WAL mode, repair state, use immutable mode or fall back to a serving handle. SQLite remains responsible for its WAL/SHM coordination under the established read-only contract. Public snapshot keeps related reads coherent and nests without committing the caller's transaction. Any transact on a read-only handle or inside a snapshot refuses before callback execution, including replayable operations. Ordinary serving outside this boundary is unchanged.

Existing tests changed additively: `v12/python/tests/manager/test_store.py` adds six acquisition/action/snapshot/cleanup/URI/serving cases; `v12/python/tests/manager/test_workspaces.py` adds two real configured-capability consistency and no-repair cases. These three paths were explicitly assigned by owner152560; W71830 standing test-change authority applies. No old assertion was weakened. Base bytes, exact base hashes, candidate copies and a unified product delta are in evidence/accounting-152563. No other product, protocol, worker or image source was edited.

## Reader and runner

prepared-152563/accounting.py validates immutable result subject, exact Job/stage/attempt/Authority assignment, participant/principal, generation, current policy, configured group, launch/exchange and public frozen-output/intake/report custody. A committed imported result uses its journal-bound recorded approval generation: ordinary import/lease release can advance current policy. Unfinished results still require current generation. This observes an existing terminal act; it grants no new authorization. Required owner failures propagate. Pre-activation claims earn no exclusion until the manager binds their exact attempt; foreign or ended-unbound claims refuse.

Judge claims stay separate from allocated Job stages. Public Authority event reads bracket assignment reads; a changed history causes a fresh observation. The manager snapshot joins its configuration, runtime and custody reads. A live unable/lost/fault or retained rejection is a primary required-attempt failure; frozen findings/report identities are checked against accepted intake. No raw store access, private capability mint, serving factory or provider stream parser appears in this reader.

Integration is charged cumulative120 seconds minus only the clipped union of its three exactly bound judge claim intervals. Each judge180, implementation240, original review180 and whole1200 limits remain. Completed intervals between polls cannot erase overruns. The timer records its chosen clock before arming; stale attempt alarms refresh owners, with at most three consecutive unstable reads, while the whole deadline stays fatal. Known required failures are handled before optional Docker stats and later reader work. Both-terminal acceptance also requires all three observed accepted reports. The whole deadline remains through final target tests, identity and cleanliness checks; no positive remainder means no test launch. Operational required-read refusal is never a budget exclusion or success.

## Validation and limitations

Final product modules:166 tests, zero failures/errors, 0.706456483s. Final proof package:89 tests, zero failures/errors, 5.480484759s. Joined cases drive real disposable component owners and worker report/intake paths with simulated engine/provider answers: pending judges, all three accepted frozen reports, ordinary coordinator import, four Authority receipts and both completed Jobs, plus rejected report and live-failure/refusal paths. Runner checks cover missing judgments, primary failure precedence and expiry during final checks. Pure accounting checks retain overlap/gap/history/whole-deadline coverage.

All attempts are retained: first product166 had two new fixture timestamp errors (missing milliseconds), fixed without changing accepted behavior; first proof84 had one post-import policy mismatch, corrected to the committed terminal contract; intermediate86 passed but three appended runner methods were outside discovery, then moved into their test class; final89 includes them. No model/Docker run was launched. These checks do not prove the live standalone two-Job pipeline.

Preservation verified198 actual run9 input files,19 reconciliation files,75 prior partial candidate files, and five unassigned source contracts. Prior genuine image/review markers remain covered by that custody; the new package has no execution markers. Nine historical failed runtime walls stay2002.0388815780316s. This claim measured checks total16.988649009029s; cumulative67.939754715930s, with previous untimed/host/provider billing uncertainty retained in spending.json.

## Operational finding and exact host command

The new manager reader and existing IntegrationStore.open_readonly both refuse the retained external run9 stores in this managed context: ContractRefusal(refused,precondition), underlying OperationalError; coordinator specifically reports unable to open database file. A sidecar-access boundary is plausible, not proven. The supported probe is evidence/accounting-152563/inspect_readers.py; it prints only selected owner metadata/refusals, never credentials or provider streams. It does not copy databases, change permissions, create sidecars manually, checkpoint or repair. Historical coordinator final state remains unverified here.

Run this same command in the already authorized host operational context and retain stdout with the Work evidence:

```sh
/usr/bin/python3 /home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/evidence/accounting-152563/inspect_readers.py
```

The script establishes its own source import path and uses only the public read-only openers and configured-group/result readers. SQLite may maintain its own sidecars as documented by those APIs. If the host also refuses, preserve the exact refusal and return that operational boundary; do not bypass it. Independent code review can proceed on this complete candidate while host access remains an explicit execution prerequisite.

## Remaining Work

Review combined manifest/product base/delta and all changed expectations against owner152560 and approved accounting150498. Then baton.ops resolves supported host access and any separately authorized fresh proof preparation. Real verification, review and approval, scoped receipts/current policy, ordinary import/lease/causal verification and both-terminal final checks remain mandatory. No retry or historical state repair is requested here. Existing W144335/W144813/W136578/W129838, fault-C/H7 and resilience deferrals, run5 writer/run6 root-cause uncertainty and separate queued OAuth recovery procedure are unchanged.
