# Correction and restart proof (slice C) — preparation packet

Prepared by baton.claude, W177938 claim 178730, after owner poke 178688 lifted
the stop hold and in the owner's stated order (W177937 first, then this).
**Preparation only.** No product or test file edited, no test run, no engine,
live model or rerun, no architecture-review cycle. All writes are inside this
dossier.

All five required inputs in `FINDING.md` were present and readable, and are
hashed in `BASELINE-177938.json`.

## 1. Headline

**C is not "more coverage". It is the one proof this campaign does not have,
and the existing schedule says so in its own words.**

`tests/tools/test_scheduler_trace.py:test_the_composed_deployment_reopens_and_continues`
already performs a genuine manager recomposition over the same durable files,
already compares engine starts by input identity before and after the boundary,
and already injects a synthetic duplicate container to prove the comparison can
fail. It then records, in the artifact it publishes:

> "THE ENGINE COUNT IS THE ONLY DUPLICATE COUNT THIS SCHEDULE CAN MAKE. …
> The PROVIDER side cannot be counted here: `agent_sessions_of` answers EMPTY
> for both attempts at this boundary, because neither has reached the turn that
> records a session, so a provider-duplicate comparison here could not fail."

**That is the gap, stated by the predecessor rather than inferred by me.** C's
job is to reach a boundary where both counts are positive and both duplicates
are rejectable. Everything else in C exists to get a real turn in front of that
boundary.

The second half is the same shape. `test_a_correction_opens_a_second_episode_on_the_same_line`
obtains a real verdict, settlement and routed attempt — **and stops at revised
preparation.** No useful revised code crosses it, and nothing carries the
correction through managed import to a target receipt.

## 2. What is already accepted, and must not be re-proved

| Already established | Where | C's use |
| --- | --- | --- |
| Managed preparation / judgment / apply / import and target receipts | W161230, closed satisfying; `tests/tools/test_managed_apply.py`, `test_managed_integration.py`, `test_managed_preparation.py` | **consumed, not rebuilt.** C drives the accepted path; it does not re-assert placement, authorization or receipt-transaction rules |
| A real correction episode on one line | `test_scheduler_trace.py:test_a_correction_opens_a_second_episode_on_the_same_line` | **extended past revised preparation**, preserving its evidence |
| A real manager recomposition with engine-side duplicate rejection | `test_the_composed_deployment_reopens_and_continues` | **the pattern is reused**; C adds the provider stream the predecessor could not count |
| A real provider process seam | `test_stage_execution.py:2652 provider` / `:2678 turn`, driving `baton_worker.serve_exchange` over `claude_agent.ClaudeAgent` | **the counter attaches here**, not to session rows |
| The trace harness, its schema and its validator | `tests/tools/scheduler_trace.py` (`SCENARIO_SCHEMA`, `TRACE_SCHEMA`, `validate`) | **the companion validator extends this**, and does not fork it |
| Eighteen valid terminal traces, four import orders | W103525 `CONSOLIDATION-2026-09-13T14-10-03Z.md` | **not rerun.** Those traces contain zero corrections and no reopen, which is precisely why C exists |

**No broad suite, no predecessor rerun, no baseline repair, no historical
reconstruction.** DESIGN §9's "without rerunning all 18 predecessor schedules"
is a constraint on C, not an aspiration.

## 3. The two scenarios, and what makes each non-vacuous

### 3.1 `UsefulCorrection`

An initial deterministic provider writes a **meaningful function with the wrong
requirement** — DESIGN's multiply-by-2. A **genuine** verifier runs over those
bytes. A **real** independent changes-requested review produces the next
same-line episode. A fresh attempt then writes **multiply-by-3**, a separately
pinned verifier executes the revised bytes, independent review finishes, and the
accepted managed preparation / judgment / apply / target-receipt / final-outcome
path runs to completion.

**What makes it non-vacuous:** the old and revised code digests differ, the
verifier really executed both, the verdict and routing are the owners' own, and
the target receipt names the revised bytes. **A correction that only changes a
disposition row proves nothing** — the point is that useful, different, working
code crossed the whole pipeline.

**Isolation is asserted, not assumed:** reviewer mounts and identities exclude
producer context and the writable line.

### 3.2 `CountedReopen`

After a real deterministic provider call and a durable result, close the manager
handles and recompose over the same stores and protected state. **Engine
observations and counters live outside those handles**, or the reopen destroys
its own evidence.

**Two independent counter streams, and both baselines must be positive before
the boundary:**

| Stream | Counted at | Keyed by |
| --- | --- | --- |
| provider | the real `_ran_provider` / provider process seam | use, invocation, attempt, and the exact open/`--resume` operands |
| engine | engine `run` invocations | their own **input** attempt/operation identity, as `launches_naming` already does |

**Neither count may be inferred from `agent_sessions_of`, allocated tokens or
unique operation ids.** DESIGN says this and the predecessor schedule proves why:
session rows were empty exactly where the count was needed.

**The reopen must not increment the old use or restart its runtime; a legitimate
new correction increments its own distinct use exactly once.**

**Duplicate injection on both streams, separately**, each rejected by the same
companion validator — following the predecessor's own discipline that "an
assertion nothing can break is not an assertion". Also rejected: missing positive
baselines, an absent actual reopen, changed verdict/checkpoint/attempt
attribution, and a forged context receipt. **These are labelled synthetic invalid
evidence and are never owner receipts.**

**This is a manager recomposition in one process, not a host or power loss.** The
predecessor labelled its boundary that way and C inherits the limit; no
exactly-once claim across host failure is made.

## 4. Proposed paths

**New, C's own:**

| Path | Contents |
| --- | --- |
| `v12/python/tests/tools/correction_restart_trace.py` | the scenario/trace harness for C, extending `scheduler_trace`'s schema and validator rather than forking them; the two counter streams and the companion validator live here |
| `v12/python/tests/tools/test_correction_restart.py` | `UsefulCorrection`, `CountedReopen`, `InvalidEvidence` |

**Dossier evidence** in `work/records/2026/09/finding-v12-correction-restart-proof/`:
the C candidate, its measured results and the exact selectors run.

**Owner-routed after independent review:** `v12/python/DEPLOYMENT.md`. **Not
edited during implementation** — a product-documentation claim before acceptance
is the thing DESIGN §8 and EXECUTION-B §6 both forbid.

**Explicitly not edited by C:** the six W61599 producer paths (accepted at
correction 178427, released at 178644), the fourteen paths EXECUTION-B selects
for slice B, `schema.py`, `store.py`, `documents.py`, frozen contracts,
`review_cycles.py`, `job_manager/review_driver.py`, the scheduler, the Authority,
and the accepted integration code. **If C demonstrably needs another source
boundary, report the exact required change for scope disposition — do not hide it
in a test helper.** That sentence is DESIGN's and it is the one most likely to be
tested in practice.

## 5. Sequencing — C cannot start yet, and the packet says so plainly

**C consumes B's output.** EXECUTION-B-177536.md is owner-selected (reroute
178645) and assigned to `baton.tune`; B delivers the context-required serving
path, the receipt and the historical ending order that C then drives end to end.
**C's `UsefulCorrection` cannot reach a real provider turn with a context receipt
until B exists.**

**So the concrete precondition list is:**

1. B implemented, independently reviewed at `baton.feat`, and owner-accepted.
2. The viewer connection (W177937, now with `baton.ops`) — **not a blocker for C**,
   but it shares the tuner and `test_stage_execution.py` sits in both change sets.
3. Production qualification (W177936, with `baton.tune`) — **explicitly not a
   precondition.** C's default provider is the deterministic fake/replay seam, and
   that separation is what keeps C runnable without a live model.

**The deterministic default is a decision, not a shortcut.** A fake can prove
contract enforcement, counting and ordering; it cannot establish third-party CLI
persistence. C therefore labels its provider evidence simulated and makes no
production-restoration claim — production qualification stays W177936's.

## 6. Finish criteria

C is ready for independent candidate review when **all** of:

1. `UsefulCorrection` shows different, working, verifier-passing revised code
   carried through a real changes-requested verdict and the accepted managed
   path to a target receipt naming the revised bytes.
2. `CountedReopen` shows **both** baselines positive before the boundary, the
   reopen incrementing neither, and a legitimate new correction incrementing its
   own use exactly once.
3. The companion validator **rejects** each injected duplicate on each stream
   separately, plus the four other invalid-evidence cases of §3.2.
4. The unchanged scheduler-trace digest still validates, so C has not quietly
   altered the predecessor's evidence.
5. Exact candidate hashes, the environment and provenance bundle, and the
   measured selectors are recorded in the dossier.

## 7. Finite run and cleanup plan

**Proposed, not run.** From `v12/python`, the repository-pinned interpreter with
`PYTHONPATH=src:tools:.`, each selected run in its **own process group under an
owning supervisor**, **180 s per C scenario**, TERM 5 s then KILL 5 s, with
**positive proof of group absence** after each — the discipline the W61599
correction review applied and found missing the first time.

```text
-m unittest tests.tools.test_correction_restart.UsefulCorrection
-m unittest tests.tools.test_correction_restart.CountedReopen
-m unittest tests.tools.test_correction_restart.InvalidEvidence
```

Each scenario stays under **100 logical ticks**. Record actual interpreter and
dependency versions and source/config hashes. **Cumulative historical seconds are
not an admission gate**; a tuned ceiling per fixture is.

**No live model, no actual OCI engine, no image build or pull, no broad
discovery run, no predecessor 18-schedule rerun.**

## 8. Recommended tuner execution scope

`baton.tuner` implements C **after B is accepted**: build the two new files,
extend the existing trace schema and validator rather than forking them, attach
the provider counter at the real process seam and the engine counter at input
identity, produce the companion validator with its duplicate injections, run the
three selectors under the supervisor above, and record the candidate and measured
evidence in the W161234 dossier. Then `baton.feat` for independent review, then
`baton.ops`.

**The tuner may not**: certify production restoration, claim host-failure
exactly-once, edit the producer or B path sets outside its own claims, rerun
predecessor schedules, repair the pre-existing baseline failures, or route a
`DEPLOYMENT.md` change before acceptance.

## 9. What this preparation did not do

No product or test file edited. No test, probe, provider, engine, build,
installation or version-control operation. **New measured verification: 0 s.**
Source reads and hash comparisons are preparation evidence, not executed
acceptance. Nothing protected was opened. All writes are inside this dossier.

Preparation acceptance is not implementation, experiment or release acceptance.
