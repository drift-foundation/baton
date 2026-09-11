# Progress

Implementation entries belong to the assigned change author.

## 2026-09-09 — baton.claude, claim 129811

**Claimed first**, at seq129811, before any edit. The baseline revalidation,
the enumerated singleton consumers, the exact new variant, the held worker and
pool shape, the role-to-workers seam, the question, the 200s budget and the
selectors are all recorded in PLAN.md before editing, as this Work's plan
requires.

### Delivered

**The variant.** `MULTI_CONFIG_SCHEMA = "baton.v12.stage-execution-deployment/2"`,
selected by the document's own `schema`. `/1` is closed and stays closed — it
still refuses two workers for one role with the same sentence, and the role
rule is checked BEFORE the new identity rule so that refusal is the one it
always was. All 160 pre-existing cases in the module pass unchanged.

**The pool.** `_pool` needed no change: it already emits one eligible entry per
configured worker, with the lane derived by the scheduler's own rule. Every
existing per-worker rule still applies to every worker — the Authority
comparison first, `single_worker`'s own launch validation, launch-role
agreement, the outside-the-checkout paths, every role served, and
participant/principal independence. One rule is added, which `/1` got for free
from its roles: **worker identities are unique across the pool.**

**The seam the next cut selects on.** `workers_for(role)` answers every
configured worker in order and never reduces a role to a singleton;
`sole_worker(role)` answers the one, refusing when there are several with a
sentence naming the per-Job binding cut. `line()` asks `sole_worker`, so `/1`
behaves exactly as it does now and `/2` refuses the per-Job question rather
than choosing the first producer. `publishers` maps each producer participant
to its own publisher session — `Authority.publish` takes the *producer's* live
assignment and a session refuses to act on an assignment naming somebody else —
and `published_proposal` selects by the accepted checkpoint's writer's own
recorded participant, which under `/1` is the single session it has always
used. `publications` is the same mapping for the publication seam, with a
`_PerJobPublication` that refuses under several producers.

**What this cut does not claim:** per-Job source, task, line, checkpoint or
target binding. Pool acceptance alone is not multi-Job execution.

### Test delta, recorded under the standing authority

`tests/tools/test_stage_execution.py` —
`test_another_generation_of_the_schema_is_refused` named `.../2` as its foreign
value, and that is now a variant this deployment serves. The rule it is about
has not moved, so it names a value that is actually foreign and additionally
asserts the refusal names both served variants. Added
`TheMultiWorkerPoolComposesWithoutASecondAllocator`, 13 cases.

`Integration.required_tests`' one-producer refusal is **deliberately left
exactly as it was**: it already gives the same answer `sole_worker` would, and
it is reached through a deployment DOUBLE in the accepted integration cases,
which holds the configuration and not this composition's readers. Routing it
through the new seam broke ten accepted cases for no behavioural gain.

### Runs

160 with 15 failures (20.618s, the `required_tests` routing) → 160 with 4
(20.625s) → **160 OK** (20.688s, the one-Job variant untouched) → four
iterations of the new class (1.840s: the single-publisher session name, then
the single publication seam, then one encoded column, then OK) → **173 OK**
(20.877s) → **189 OK** across `test_single_worker`, `test_scheduling` and
`test_sweep` (4.101s). **89.7s of the declared 200s, 110.3s left.** No live OCI
or model campaign and no whole-suite pass. Detail:
`evidence/provider-129811.json`.

Passing back to `baton.bug`. The per-Job binding cut consumes this seam only
after independent acceptance; the two paths transfer to it then.
