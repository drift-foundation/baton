# W156162 — candidate provenance, 27 paths

Gathered read-only at claim 158092 by `/tmp/w156162_prov.py` (retained below as
`provenance-158092.json`). Base bytes and digests are `HEAD`'s; candidate bytes
and digests are the working tree's. **No Git mutation was performed**, and no
foreign edit was removed, imported or absorbed to make this packet look clean.

## What each path is

**Seven new files, wholly W156162's** — no base to compare, nothing foreign in
them:

| Path | Bytes |
| --- | ---: |
| `src/baton_v12/job_manager/execution_limits.py` | the owner's table, generations and resolver |
| `tests/job_manager/test_execution_limits.py` | added tests |
| `tests/manager/test_execution_limits.py` | added tests |
| `tests/tools/test_execution_limits.py` | added tests |
| `tests/job_manager/execution_limits_fixtures/golden-schema4.sqlite3` | fixture; provenance beside it |
| `tests/job_manager/execution_limits_fixtures/PROVENANCE.md` | that fixture's own record |

**Twelve modified source and document paths, all W156162's own scope:**
`DEPLOYMENT.md`, the five `job_manager` sources (`documents`, `projection`,
`schema`, `store`, `submission`), `worker_manager/launch.py`,
`tools/integration_bundle.py`, `tools/integration_worker.py`,
`tools/single_worker.py`, and the three worker files (`baton_worker.py`,
`claude_agent.py`, `integration_workload.py`).

**Five existing Job tests whose EXPECTATIONS changed**, and this is the standing
gate: `tests/job_manager/test_documents.py`, `test_exchange.py`,
`test_scheduling.py`, `test_store.py`, `test_tool.py`. Each moved because the
submission schema went `/1`→`/2` and the status schema `/4`→`/5`. **They carry no
owner disposition yet** and are part of the pending `M157653` request.

**Two existing test files changed under PLAN-scheduled setup-only authority:**
`tests/tools/test_single_worker.py` (18 added lines, no assertion changed) and
`tests/tools/test_stage_execution.py` (see below).

## The two `stage_execution` files, hunk by hunk

### `tools/stage_execution.py` — 18 hunks, all W156162's

Eight carry the marker in their own text. The other ten are the same change's
mechanical halves and are **not** foreign; each is named here so that claim is
checkable rather than asserted:

- the `execution_limits` import;
- three constructor signatures gaining `seconds=` / `retention=` / `scope=`
  (`_ConfiguredExecution`, `_CausalObserver`, `_ImportedVerifier`);
- two call sites passing those operands (`_CausalObserver`, `_ImportedVerifier`);
- the retained-failure check moved ahead of materialization;
- `_integration_operations` gaining `job_store` and passing it on.

**One hunk is FOREIGN and is reported rather than removed.** At the read-only
integration observation:

```
-        A generic or not-yet-activated stage needs neither owner opened.
+        A generic stage needs neither owner opened. Integration.account selects
+        reconciled completion before checking direct-runtime prerequisites.
-        row = attempt_runtime_of(self.control, stage["attempt_id"])
-        if row is None or row["assignment"] is None:
-            return None
```

That deletes a runtime precondition so a reconciled completion with no runtime
reaches the outer observer. It belongs to the read-only reconciled-completion
Work, not to per-Job budgets.

### `tests/tools/test_stage_execution.py` — 7 hunks

Six are W156162's, all additive or setup-only under the authority the PLAN
scheduled: `job_execution_for`, two `integration_job_execution` helpers, the
`turn` helper's adopt operand, the `TwoBoundJobs` `integration_turn` operand, and
its comment. **No existing assertion in this file was changed by this Work.**

**One hunk is FOREIGN**: the added test
`test_readonly_reconciled_completion_without_runtime_reaches_outer_observer`
(61 lines), which is the test for the source hunk above.

## Separability

The two foreign hunks are **one change and its test**, in two files, and they are
**textually separable** from W156162's: they touch a different method
(`observe_integration`'s precondition) and add a whole test function, with no
overlapping lines. Nothing in W156162's hunks depends on them.

**What I cannot certify** is that removing them leaves a passing tree: the
foreign test would fail without its source hunk, and this Work's 13 long-standing
`test_stage_execution` errors have only ever been compared against an earlier
W156162 candidate, never against a tree with the foreign change excised. That is
a measurement nobody has taken, and I am not claiming it.

## Expectation changes and their authority

| Change | Authority |
| --- | --- |
| Five Job tests moved for the schema transition | **pending**, part of `M157653` |
| `test_single_worker.py`, `test_stage_execution.py` setup operands | PLAN-scheduled setup-only authority, review 2026-09-13T02:19:56Z |
| Every other changed path | this Work's own finite scope |
| Durable no-status host outcome, and the failed scratch's disposition | **pending**, `M157653` / `HOST-FAILURE-PROPOSAL-2026-09-13.md` |
