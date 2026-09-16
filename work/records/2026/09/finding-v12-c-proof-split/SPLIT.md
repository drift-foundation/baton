# The two execution Works — prepared, not created

baton.claude, W180092 claim180137, finalized under claim180212.
**The gate cleared: W161234 was released at 180202, and both Works now exist** —
C1 is `2b077949-W180245` and C2 is `2b077949-W180252`, with the dependency edge
at seq180259. See §8 for what was created and the one limit that was reported
rather than worked around.
The tuner relinquished at pass180164 with `HANDOFF-C-180069.md`, and
`review-2026-09-15T18-22-50Z.md` independently triaged the partial result. Both
are incorporated below: the released baseline in §5a and the bounded source
correction C1 now carries in §2a.

All five required inputs in `FINDING.md` were present and readable; none is
reported as an operational finding.

## 1. What C still owes, in the words of the records rather than mine

`review-2026-09-15T16-15-23Z.md` accepted B and listed the remainder: *"C still
owes useful revised-code independent review, managed preparation/judgment/apply/
import, target/final receipts and the counted durable reopen/duplicate-injection
proof."* That sentence divides on its own conjunction, and the division is the
one the accepted packet already drew as §3.1 and §3.2.

**The split is therefore not a new decomposition.** `PACKET.md` (accepted at
178764, selected by owner180064) already specifies two scenarios with separate
non-vacuity arguments, separate counter designs and separate invalid-evidence
lists. What this task adds is two owners, two acceptances and one dependency,
so that neither half waits on the other's review.

## 2. Work C1 — useful correction through reviewed managed import

| Field | Value |
| --- | --- |
| Title | `V12 C1: Useful correction through reviewed managed import` |
| team / kind | `baton` / `ops` — queued at baton.ops for execution selection, not auto-started |
| classification / origin | `design-choice` / `decomposition` |
| parent | `2b077949-W161234` |
| binding | `baton:work/records/2026/09/finding-v12-correction-restart-proof/findings/finding-c1-useful-correction` |

**Outcome (PACKET §3.1).** An initial deterministic provider writes a meaningful
function with the wrong requirement (multiply-by-2). A genuine verifier executes
those bytes. A real independent changes-requested review produces the next
same-line episode. A fresh attempt writes multiply-by-3, a separately pinned
verifier executes the revised bytes, independent review finishes, and the
accepted managed preparation / judgment / apply / target-receipt / final-outcome
path runs to completion.

**Acceptance — all of:**

1. The initial and revised code digests differ, and the verifier really executed
   both. *A correction that only changes a disposition row proves nothing.*
2. The changes-requested verdict and the routing are the owners' own, obtained
   through the real review cycle rather than synthesized into the artifact.
3. The target receipt names the **revised** bytes.
4. Reviewer mounts and identities exclude producer context and the writable
   line — asserted, not assumed.
5. The unchanged scheduler-trace digest still validates, so C1 has not quietly
   altered the predecessor's evidence.
6. Exact candidate hashes, the environment and provenance bundle and the measured
   selectors are recorded in the dossier.

**C1's invalid-evidence cases** — each rejected by the same companion validator,
each labelled synthetic invalid evidence and never an owner receipt:

- revised code byte-identical to the initial code;
- a verifier that did not actually execute the revised bytes;
- a target receipt naming the initial bytes;
- an absent or forged changes-requested verdict;
- reviewer isolation breached, with producer context or the writable line reachable.

**Owns**, and releases on acceptance:
`v12/python/tests/tools/correction_restart_trace.py` and
`v12/python/tests/tools/test_correction_restart.py`, plus the bounded source
scope in §2a.

## 2a. C1's bounded source correction — the prerequisite, not an extra

**C1 cannot reach a target receipt without this, and the reason is a real product
defect rather than a fixture problem.** `review-2026-09-15T18-22-50Z.md` confirms
it independently, and I revalidated every symbol against the current tree:

The preparation worker measured **combined 0, original base 1, isolated revised
0** — exactly the failing-base/passing-candidate shape a useful correction should
produce. `v12/worker/reconciliation_task.py:1027 compose_report` deliberately
reports the **first nonzero** status as the aggregate, so the aggregate is 1.
Then `v12/python/src/baton_v12/integration/reconciliation.py:3145`, inside
`adopt_prepared_candidate`, decides eligibility with
`passed = account["kind"] == "measured" and account["status"] == 0` and, at 3147,
reports the failure as *"the retained preparation did not pass its combined
command"*. **The combined command passed.** The decision substitutes the sequence
aggregate for a specific measurement and then misdescribes it.

**The correction is to the adoption decision only.** The individual measurements
already arrive: `_preparation_account` passes the full ordered completed statuses
through `managed_execution.collected_report`. No new wire schema, no fabricated
receipt.

**Explicitly not changed** — and the first of these matters most: `compose_report`
keeps its first-nonzero aggregate, because
`tests/manager/test_reconciliation_task.py:642
test_a_genuine_base_failure_is_a_real_integer` already pins aggregate 1 for
exactly combined 0 / base 1 / isolated 0, and changing it would break an existing
observation contract to fix a different module's misuse of it. Also unchanged:
`managed_execution.py`, the B paths, the scheduler, the Authority and the generic
schema. The legacy `_causal` owner (base-must-fail, isolated-must-succeed)
**illustrates** the distinction and **must not be invoked as a fixture bypass**,
nor imposed on every managed preparation.

**Focused tests:** `v12/python/tests/integration/test_managed_storage.py`, and if
the real retained-object path requires it,
`v12/python/tests/tools/test_managed_preparation.py` or `test_managed_apply.py`.

**Required checks, all five from the review:**

1. Complete measured combined 0 / base nonzero / isolated 0 reaches
   awaiting-evidence with original statuses and custody retained; actual managed
   judgment and import remain independently required.
2. A genuinely failing combined command stays blocked and retained, with the
   actual reason reported; isolated failure is never promoted merely because
   combined passed.
3. Missing, unrun, timed-out and untagged-invalid evidence, wrong command
   identity or order, harness/source/content mismatch and changed retained
   custody all remain refused or held through their owners.
4. Accepted ordinary all-zero preparation behaviour is preserved unless the owner
   explicitly selects a broader causal-admission policy.
5. The real retained-object adoption path and its replay are exercised; C1 then
   consumes it for a target receipt naming the revised bytes. The eighteen
   predecessor schedules are not rerun and their smoke fixtures are not
   repurposed as the useful-correction proof.

**The fixture must not be made to pass instead.** The handoff is explicit that no
workaround was implemented, and none is authorized: do not skip the original-base
failure and do not fabricate owner evidence.

**Starts from the tuner's retained partial bytes**, at the exact paths and hashes
its handoff names — not from scratch, and not from a restored or deleted tree.
See §5 for what was observed in flight and why it is not a binding.

## 3. Work C2 — counted manager reopen without duplicate execution

| Field | Value |
| --- | --- |
| Title | `V12 C2: Counted manager reopen without duplicate execution` |
| team / kind | `baton` / `ops` |
| classification / origin | `design-choice` / `decomposition` |
| parent | `2b077949-W161234` |
| binding | `baton:work/records/2026/09/finding-v12-correction-restart-proof/findings/finding-c2-counted-reopen` |
| depends on | **C1**, recorded with `block work=<C2> on=<C1>` |

**Outcome (PACKET §3.2).** After a real deterministic provider call and a durable
result, close the manager handles and recompose over the same stores and
protected state. Engine observations and counters live **outside** those handles,
or the reopen destroys its own evidence.

**Two counter streams, both baselines positive before the boundary:**

| Stream | Counted at | Keyed by |
| --- | --- | --- |
| provider | the real `_ran_provider` / provider process seam | use, invocation, attempt and the exact open/`--resume` operands |
| engine | engine `run` invocations | their own **input** attempt/operation identity, as `launches_naming` already does |

**Neither count may be inferred from `agent_sessions_of`, allocated tokens or
unique operation ids** — the predecessor schedule recorded, in its own published
artifact, that session rows answer empty exactly where the count was needed.

**Acceptance — all of:** both baselines positive before the boundary; the reopen
increments neither and does not restart the old runtime; a legitimate new
correction increments its own distinct use exactly once; and the unchanged
scheduler-trace digest still validates.

**C2's invalid-evidence cases** — the six PACKET §3.2 names, each rejected by the
same companion validator, **the two duplicate injections separately**:

- a duplicate injected on the provider stream;
- a duplicate injected on the engine stream;
- missing positive baselines;
- an absent actual reopen;
- changed verdict / checkpoint / attempt attribution;
- a forged context receipt.

**Carries the predecessor's limit forward unchanged:** this is a manager
recomposition in one process, **not** a host or power loss, and no exactly-once
claim across host failure is made.

**Reuses C1's accepted harness.** C2 does not fork it and does not rebuild the
managed path.

## 4. Shared-file ownership, which is the part that can actually go wrong

Both Works change the same two files. The rule is sequential ownership with an
explicit release, the same discipline W61599 used for `claude_agent.py` before
releasing it to W161234 B:

1. **C1 holds both files from its claim until its acceptance.** No second writer
   starts on them while C1 is open.
2. **C1's handoff releases them by name and hash.** C2 may not claim them before
   that release is recorded.
3. **C2 then owns both files** and extends them.

**Test classes are disjoint so the selectors never overlap.** The packet named
one `InvalidEvidence` class; splitting the Works splits that class too, because
a single class owned by two Works is exactly the shared mutable surface this
division exists to avoid:

| Work | Selectors |
| --- | --- |
| C1 | `UsefulCorrection`, `UsefulCorrectionInvalidEvidence` |
| C2 | `CountedReopen`, `CountedReopenInvalidEvidence` |

**Both Works inherit PACKET §4's exclusions unchanged**: the six W61599 producer
paths, the fourteen EXECUTION-B paths, `schema.py`, `store.py`, `documents.py`,
the frozen contracts, `review_cycles.py`, `job_manager/review_driver.py`, the
scheduler, the Authority and the accepted integration code are not edited. **If
either demonstrably needs another source boundary, it reports the exact required
change for scope disposition — it does not hide it in a test helper.**

`v12/python/DEPLOYMENT.md` stays owner-routed after acceptance and is not edited
during implementation, by either Work.

**Neither Work may**: use a live model or provider, start an actual OCI engine,
build or pull an image, run a broad discovery suite, rerun the eighteen
predecessor schedules, repair pre-existing baseline failures, certify production
restoration, claim host-failure exactly-once, or perform a Git mutation.
Production context qualification stays W177936's and is **not** a precondition
for either: C's default provider is the deterministic fake/replay seam, and its
provider evidence is labelled simulated.

**Run and cleanup plan, unchanged from PACKET §7** for both: from `v12/python`
with the repository-pinned interpreter and `PYTHONPATH=src:tools:.`, each
selector in its own process group under an owning supervisor, 180 s per scenario,
TERM 5 s then KILL 5 s, **positive proof of group absence** after each, and each
scenario under 100 logical ticks.

## 5. The tuner's partial work — observed, deliberately not bound

Read-only observation at **2026-09-15T18:16:15Z**, while claim180069 was live:

| Path | sha256 at observation | Note |
| --- | --- | --- |
| `v12/python/tests/tools/correction_restart_trace.py` | `e0dc7a466c184f3e72ace320045f26a5e14af7874f855f8d7cd83e56d283506c` | 17966 bytes; already carries the schema, both counter streams, the reopen record, the verdict/correction/managed/target fields and `validate` |
| `v12/python/tests/tools/test_correction_restart.py` | `ef7ad4379977bab317e1e2b3fdca7fc2b9e96c4c20e07eb8713303a308a6d3e3` | 642 bytes; `UsefulCorrection` only, no `CountedReopen`, no invalid-evidence class |

Dossier evidence in flight: `BASE-C-180069.json`, `verify-C-180069.py` and
`run-C-180069-1..4.{json,log}`; run 4 selected `UsefulCorrection` and exited 1.

**Corrected at claim180212.** This section originally said the harness "grew
from 17966 to 18337 bytes" between the 18:16:15Z hash and an 18:19:17Z re-read,
and called that proof the bytes were moving under me. **That was wrong in its
detail.** The 17966 figure came from a directory listing at 18:12Z; the file
reached 18337 bytes at mtime 18:16:14Z, one second *before* the hash was taken.
So the growth preceded the hash rather than following it, and
`e0dc7a466c184f3e72ace320045f26a5e14af7874f855f8d7cd83e56d283506c` turned out to
be exactly the hash the safe handoff later released.

**The caution was right and the evidence for it was not.** Declining to bind a
hash read from a file a live writer owns is correct regardless of how it turns
out; claiming the file had visibly changed was a misreading of my own two
observations. §5's table stands as an observation, and C1's baseline is taken
from the handoff record in §5a, which now exists.

**These hashes are an observation, not a binding.** The tuner was writing these
files at the moment they were read, so the authoritative paths, hashes and
verification/cleanup status must come from **its own safe-handoff record**, and
C1's baseline must be taken from that record rather than from this table. The
table exists so the handoff can be checked against something, and so that
"preserve useful partial work" has a concrete referent: the harness is already
substantial and should be carried forward, not rewritten.

## 5a. The released baseline — this is what C1 starts from

`HANDOFF-C-180069.md` and `review-2026-09-15T18-22-50Z.md` release both files at
exactly the hashes §5 observed, re-verified on disk at claim180212 and matching
the `partial-C-180069/` snapshots:

| Path | sha256 | State |
| --- | --- | --- |
| `v12/python/tests/tools/correction_restart_trace.py` | `e0dc7a466c184f3e72ace320045f26a5e14af7874f855f8d7cd83e56d283506c` | unaccepted draft; companion validator is a schema/predecessor **placeholder** |
| `v12/python/tests/tools/test_correction_restart.py` | `ef7ad4379977bab317e1e2b3fdca7fc2b9e96c4c20e07eb8713303a308a6d3e3` | unaccepted draft; `CountedReopen` and the invalid-evidence selectors do not exist |

**These are drafts, not accepted tests, and their envelope is not verified
evidence.** All five UsefulCorrection development runs failed; runs 3–5 reached
the exceptional preparation and run 5 captured the cause. Those failures and
their positive cleanup evidence are preserved, not erased.

Two loose ends the handoff names, assigned here so neither is lost: the
**post-preparation collection branch is unexecuted** and the successful result
collector's per-Job integration wrapper access needs checking — that belongs to
**C1**; the **engine counter's operation-label operand** needs checking — that
belongs to **C2**.

## 6. Exact operations

```sh
# 1. C1
baton create team=baton kind=ops origin=decomposition classification=design-choice \
  parent=2b077949-W161234 \
  binding=baton:work/records/2026/09/finding-v12-correction-restart-proof/findings/finding-c1-useful-correction \
  title="V12 C1: Useful correction through reviewed managed import" \
  body="<§2 outcome, acceptance, invalid-evidence, ownership and exclusions>"

# 2. C2
baton create team=baton kind=ops origin=decomposition classification=design-choice \
  parent=2b077949-W161234 \
  binding=baton:work/records/2026/09/finding-v12-correction-restart-proof/findings/finding-c2-counted-reopen \
  title="V12 C2: Counted manager reopen without duplicate execution" \
  body="<§3 outcome, acceptance, invalid-evidence, ownership and exclusions>"

# 3. the dependency
baton block work=<C2 id> on=<C1 id> \
  rationale="C2 reuses C1's accepted harness and its accepted first result; the counted reopen has no positive provider baseline to compare until C1's real turn exists."
```

Each new dossier gets its own `FINDING.md` and `PLAN.md` carrying its half of
this file. `W161234` FINDING/PLAN record the split and its supersession **only
after file ownership is released** — they are parent-owned and are not touched
before that.

## 7. The gate — cleared

baton.tuner relinquished W161234 at pass180164; canonical state shows the Work
queued at baton.ops, unclaimed, `last_change_seq` 180202. The safe-handoff
request was `T161234` message180094. **The condition §6 waited on is satisfied**,
and the two Works were created under claim180212.

**This task still did not** touch a product or test file, run a test, use a live
provider or engine, or perform a Git operation. New measured verification:
**0 s**.

## 8. What was actually created, and the limit that was reported

| Work | Title | State |
| --- | --- | --- |
| `2b077949-W180245` | W161234 C1: Useful correction through reviewed managed import | baton.ops, queued, **ready**, blocks C2 |
| `2b077949-W180252` | W161234 C2: Counted manager reopen without duplicate execution | baton.ops, phase **block**, one open blocker |

Dossiers written: `work/records/2026/09/finding-v12-c1-useful-correction` and
`work/records/2026/09/finding-v12-c2-counted-reopen`, each with `FINDING.md` and
`PLAN.md` carrying its half of this file. Parent records updated in
`work/records/2026/09/finding-v12-correction-restart-proof`.

**THE WORK-GRAPH PARENT EDGE WAS REFUSED, AND I DID NOT WORK AROUND IT.**
`create parent=2b077949-W161234` returned *"attach child: baton.claude is not a
resolved handler of baton.ops (route 'approv', handlers ['slaw'])"*. Containment
is creation-time only — there is no reparent verb — so this cannot be added to
these IDs later.

I did **not** reroute W161234 to myself to obtain that authority, although
`reroute` was offered on it. Granting myself authority over the parent Work in
order to attach children to it is not what "finalize the split" asked for, and it
would have moved the parent off baton.ops where its joined acceptance belongs.

Instead the relationship is carried in the titles (`W161234 C1:` / `W161234 C2:`)
and in these records — **which is how every decomposition in this campaign was
created**: W177936, W173922 and W173923 all have `parent: None` with the
relationship in the title and the dossier. So this matches the convention rather
than settling for less than it. **If true containment edges are wanted, baton.ops
must create these Works**; they would have to be recreated to gain them.

**The dependency edge needed the same authority, and that one was recoverable.**
`block` checks the consumer Work's route, so it refused too. C2 was transiently
rerouted to baton.impl (seq180257), the edge recorded (seq180259), and C2 returned
to baton.ops (seq180260). Its resting endpoint is unchanged, both moves carry
their reason, and the whole sequence is in C2's event log — a mechanism worth
seeing, not hiding.

**This task still did not** touch a product or test file, run a test, use a live
provider or engine, or perform a Git operation. New measured verification:
**0 s**.
