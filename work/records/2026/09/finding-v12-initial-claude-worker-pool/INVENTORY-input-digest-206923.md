# Which `input_digest` is which — the producer/consumer inventory

W202663, claim206923, answering review206898 [R1]: "Build an explicit
producer/consumer inventory distinguishing Job submission, Job-derived offer,
standalone offer, runtime attempt, result, provider-context and recovery
identities. Migrate actual Job composers only."

Every row is **traced in the current tree**, not inferred from a member called
`input_digest`. That inference is exactly what my claim206704 handoff got wrong,
and the review caught it: I called `dogfood_operator` lines 1210 and 1221 "Job
composers" because of the field name, and neither is one.

## The six identities

| # | identity | produced at | consumed at | axis | migrated? |
| --- | --- | --- | --- | --- | --- |
| 1 | **Job submission** | the operator's submission document; stored by `job_manager/submission.py:123` | `single_worker._matches`, `stage_execution` worker compatibility, `stage_execution._correspondent`, `integration/admission` | **JOB** | **yes** — these are the actual Job comparisons |
| 2 | **Job-derived offer** | `job_manager/delegation.py:824`, `issue_offer(input_digest=job["input_digest"])` — its own docstring calls this "the Job's immutable input and policy identities" | `single_worker._claim` | **JOB** | **yes** — this is the site that actually blocked heterogeneous pools, since an offer is minted per stage |
| 3 | **standalone offer** | `dogfood_operator.py:1210`, inside `run_dogfood_task` | `offers.accept_offer`, then `offers.py:713` folds it into the claim **intent digest**, which is self-consistent and compared only against itself; `authority/core.py` stores it on the proposal row | neither — **there is no Job** | **no, deliberately** |
| 4 | **runtime attempt** | `dogfood_operator.py:1218` and `single_worker.py:1722`, both `record_attempt(input_digest=<the delivered manifest's own digest>)` | `attempts.authorize_input_root` compares it to the manifest actually found in the input root (`given["manifest_digest"]`); `output.py:394` and `provider_context.py:587` load the manifest BY it | **RUNTIME** | **no, and it must not be** |
| 5 | **result / proposal** | `integration/driver.py:439`, from the frozen result's `input_manifest_digest` | `integration/admission` — which now projects it before comparing to the Job | **RUNTIME at the producer, JOB at the consumer** | **consumer only** |
| 6 | **provider context / recovery** | `provider_context.py:313` from `runtime["input_digest"]`; `review_cycles.py:1429` against `attempt["input_digest"]` | their own receipts and re-entry checks | **RUNTIME** | **no** |

## Why rows 3 and 4 are left alone — the review's correction, verified

**Row 4 is the one that would have broken.** `attempts.py` (around 1386):

```python
if given["manifest_digest"] != attempt["input_digest"]:
    raise ContractRefusal(
        "integrity", "digest",
        f"the input root at {name_value(inputs)} carries an input "
        f"manifest this attempt was not claimed against")
```

`given` there is the manifest **read back out of the delivered input root**. Its
`manifest_digest` is the whole document's digest and always will be. Replacing
`record_attempt`'s `input_digest` with a Job projection would make that
comparison compare a projection against a whole digest, refuse every runtime
start, and destroy the exact per-attempt runtime attribution owner ruling
206702 requires preserved. The reviewer was right and my handoff was wrong.

**Row 3 has no Job to be about.** `run_dogfood_task` is the standalone operator
launch: it composes a manifest, issues an offer, accepts it, records the attempt
and claims — all without a Job store, a submission, a stage or `_SingleWorker`.
Traced: `tools/dogfood_operator.py` imports neither `single_worker` nor
`claimed_offers_for`, so a standalone offer can never reach the
Job-scoped comparison in `_claim`. Its digest is consumed by the claim intent
digest, which is a hash over the offer's own members and is compared only
against itself. A projection there would change an opaque self-consistent value
for no reader.

## What this leaves

Row 1 and row 2 are the only Job composers, and both are corrected. Row 5's
consumer is corrected while its producer stays runtime-local, which is what lets
an imported candidate keep naming the exact manifest its attempt ran.

**No product composer remains to migrate.** My claim206704 handoff listed
`dogfood_operator.py:1210` and `:1221` as remaining product work; that item is
**withdrawn** — it was a misreading, and the correct action at both lines is to
change nothing.
