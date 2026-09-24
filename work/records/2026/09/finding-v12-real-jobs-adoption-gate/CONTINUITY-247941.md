# G2 — what accepted evidence covers, and what the witness had to add

ASSESSMENT-249338.md G2: "compare the relevant older accepted concurrency seams
against the selected snapshot ... Reuse unchanged or independently accepted
successor behavior. For any remaining configuration-specific gap, use a single
deterministic two-Job witness through the selected composition."

## The seam comparison

The accepted two-Job evidence (W130224, review-2026-09-11T00-52-04Z.md) was
taken against `tools/stage_execution.py` at
`9cf2927f4057a68beec61cfd56abeca709509d7770cd577412f750bce4ae1223`. The
selected snapshot carries
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`, and
`verify_247941.py --pins` re-verifies that digest, the 106-file manager-source
count and the runtime executable independently — all three agree with the
assessment's pins.

**The seams are not compared by reading two digests.** They are compared by
RUNNING the accepted fixture's own two-Job traversal against the selected bytes
with this arrangement's document substituted. That is what `test_two_jobs.py`
does, and a seam that had drifted would fail there rather than be argued about
here.

| Concurrency seam | Accepted evidence | How it is joined to this arrangement |
| --- | --- | --- |
| Per-Job binding: one Work, base, target and source worker per Job | W119405, and `_held_bindings` in the selected snapshot | `two_jobs.bindings` composes exactly what that validator accepts; the witness holds it through `held_configuration` |
| Per-Job allocation: each Job's stage reserves its OWN worker | W130216; `EveryJobRoleIsValidatedBeforeAllocation` | Witnessed on this document: `job-a/implementation` → `implementation-worker`, `job-b/implementation` → `implementation-worker-b` |
| Simultaneous distinct producers and lines | W130224 `test_both_jobs_code_at_once_on_their_own_workers_and_lines` | Re-driven on THIS document; both `waiting` at one observed instant, two distinct `line_id`s, two distinct mounted workspaces |
| Each Job reaches its OWN reviewer | W130224 `test_the_second_job_reaches_its_own_reviewer_and_verdict` | Re-driven on THIS document for Job B's reviewer attempt |
| A participant serving both sides of one review is refused | `TheMultiWorkerPoolComposesWithoutASecondAllocator` | Unchanged product rule; this arrangement additionally refuses ONE reviewer across two Jobs, which is this gate's limit rather than the product's |
| Correction isolation | W130224 `test_a_correction_reopens_only_its_own_jobs_line` | Not exercised: this arrangement sets `correction_policy: "decline"` (W239533's accepted product boundary), so no round opens at all |
| Live implementation, retained proposal, positive cleanup | W239528, `live-success-244216` | One Job, live. Not re-proved; the limit is that it is ONE |
| Live independent attributed review, positive cleanup, destroyed runtime | W239533, `live-review-248377` and `ATTRIBUTION-248565.json` | One review, live, verdict re-derived from the retained store through supported readers |
| Historical live A/B execution of two Jobs | W130224 / `live-success-nup4nltc`, seven retained hashes re-verified by the assessment | Older configuration and a managed-integration path; carried as feasibility, NOT relabelled as this arrangement's certification |

## What the witness had to add, and why

Everything above except the last three rows is machinery. What none of it
covered is **this arrangement's own document**: a `/2` deployment whose pool
and bindings are composed by `two_jobs.arrangement` from per-Job facts, with no
integration stage and corrections declined. That is the configuration-specific
gap, and it is the only thing `test_two_jobs.py` adds.

A guard case asserts the document that actually served is this arrangement's
and not the fixture's own, by worker order. Without it these cases would be
W130224's accepted evidence re-presented under this Work's name.

## What remains uncovered, named rather than bridged

1. **Positive stop and cleanup for FOUR admitted attempts.** Accepted cleanup
   evidence is per-Job and live (W239528, W239533); the witness runs no
   containers, and no two-Job bounded supervisor exists yet. This is the gap
   ADOPTION-247941.md names as the smallest remaining implementation step.
2. **The container and live-provider boundary under concurrency.** Two
   runtimes on one host at one instant is not established by any evidence in
   this map. The historical A/B run is the closest, on an older configuration.
3. **`changes-requested` under this arrangement.** Settled only
   deterministically, as in W239533.
