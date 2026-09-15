# W103525 scheduling evidence — disposition matrix

Advisory Work W174052, claim 174115, baton.claude via baton.impl.
**Read-only pass. Nothing was executed:** no test, probe, provider, model,
engine, build, Git mutation or worker. No product, test or original dossier was
edited, and no original was closed, reclassified, rerouted or re-gated.
Advice for the owner; **not acceptance**.

Baseline: live tree, 2026-09-15, under claim 174115. Provisional.

**Not reopened here:** no new stress campaign, no priority/shared-slot/random/TUI
expansion, no duplicate implementation, no new prerequisite.

## 1. The retained evidence is intact and still hashes equal

`CONSOLIDATION-2026-09-13T14-10-03Z.md` pins the trace foundation by hash.
Re-measured now:

| Artifact | Pinned hash still current |
| --- | --- |
| `v12/python/tests/tools/scheduler_trace.py` | **same** (`fa9e69f2…`) |
| `v12/python/tests/tools/test_scheduler_trace.py` | **same** (`a57c0a71…`) |

The dossier still holds **88** `trace-*`/`review-161114-*` artifacts. So the
independently accepted foundation — fresh traces of 97 records, 12 stage
completions and four authorized imports each, plus the audited 18-schedule
export — is reusable **as it stands**, with no re-run needed to cite it.

**Its own qualification, carried forward verbatim in spirit:**
`review-2026-09-13T14-10-03Z.md:27` — *"This does not claim fresh execution of
every exported method."* The acceptance is of the oracle, the traces and the
audit, not of every method they touch. Any closure text must repeat that limit
rather than round it up.

## 2. Canonical state has moved since the plan — one item is already resolved

`SELECTED-PLAN-161345.md` recorded: *"W161234 detail161363 is queued at
baton.feat; M161246 reports prompt's dependency attempt was correctly refused by
endpoint authority, so no edge exists yet. Do not say the documentary dependency
is a recorded scheduler gate."*

**That edge now exists.** Measured:

| Work | Phase | `blocked_by` | Next |
| --- | --- | --- | --- |
| W103525 | **parked** | `W71830` | `baton.feat` (rview) |
| W161230 | block | `W170387` | `baton.ops` (approv) |
| W161234 | block | **`W161230`** | — |
| W156162 | block | `W161230` | — |

So the delegation the plan describes **is** recorded canonically for both
consumers. The plan's caution is satisfied and should not be repeated as an open
item.

**And W103525's own blocker is already discharged:** `W71830` ("Run a standalone
multi-job v12 pipeline") is **closed satisfying** at seq 153656. W103525 is
therefore parked behind a closed dependency, with `next` already pointing at
`baton.feat` for the reviewer disposition the plan asked for.

## 3. Disposition matrix

Each row: what the evidence supports, where the outcome now lives, and what is
genuinely undecided. Locators are exact.

| Selected outcome | Disposition | Evidence locator |
| --- | --- | --- |
| Trace/oracle foundation, replay, reservation-before-offer, effective-principal exclusion | **Reusable for closure now.** Independently accepted; artifacts hash equal today | `CONSOLIDATION-2026-09-13T14-10-03Z.md` matrix; `review-2026-09-13T14-10-03Z.md` |
| A→B dependency with C/D progressing; alternate terminal orders | **Reusable**, at its measured boundary: two-team, **one-target**, four-producer/four-reviewer. The combined two-repository / two-effective-slot / reopen / correction contract is *not* supplied by these traces | consolidation matrix row 61 |
| Managed integration isolation and custody | **Delegated to W161230.** Historical host-path traces do not certify the managed lifecycle | plan §"Evidence and certification boundaries" |
| Actual revised-code correction | **Delegated to W161234.** Configuration-label fixes and revised-attempt preparation alone are insufficient | same |
| Context continuity and counted reopen | **Delegated to W161234**, required not optional. Reuse W106673 capability evidence | same |
| Per-Job limits reaching every selected phase | **Delegated to W156162** | checklist row 34 |
| Dedicated worker capacity and repository bindings | **Reusable** at its measured boundary; no combined shared-slot or repository certification claimed | plan table |
| Shared slots; priority / randomized stress / TUI | **Deferred.** No gate, no certification claim, and explicitly no backlog to create | plan table |
| Final pinned environment | **Delegated** into each selected Job's completion checks | plan table |
| **Operator-designated replacement** | **The one concrete remaining decision.** See §4 | §4 below |

## 4. The one concrete remaining decision — operator-designated substitution

The plan's four source claims re-verify today:

- `src/baton_v12/job_manager/scheduler.py:158 activate_pool` — configuration
  generations.
- `:316 reserve(store, stage, *, excluded=None)` — **the only operand besides
  the stage is `excluded`. There is no designated-replacement operand.**
- `:137 _required_workers` — retains providers needed by live allocations.
- `tools/stage_execution.py:4516 _job_workers`, `:4581 _job_eligibility`,
  `:5629 _pool_generation` — per-Job Work/input compatibility, actor exclusion
  and activation-generation checks.

**I read the test body the plan cites**, rather than trusting its name:
`tests/job_manager/test_scheduling.py:201
test_affinity_is_soft_and_fallback_does_not_rewrite_it` reserves for a line,
releases, lets a blocker occupy the preferred worker, then reserves again and
asserts `selection_outcome == "fallback"`, `preferred_worker_id ==` the original,
and — reading the `worker_affinity` row directly — that the stored affinity is
**still the original worker**. That is automatic soft fallback that does not
rewrite the preference. It pins present behaviour precisely and confirms the
plan's reading.

**So the gap is real and unchanged:** there is no scoped, durable substitution
relationship with an authorizer, revocation and admission provenance.
"Jane covers Chris until further notice" is not expressible today.

**What is undecided, stated as the owner's choice and not as new work:** whether
an explicit authorized configuration revision suffices, or whether a separate
durable substitution record is required. The plan is emphatic that this must not
be folded silently into W161230/W161234 or reinterpreted as optional, and I make
no recommendation between the two options — it is a product-shape decision, not
a research finding.

## 5. Proposed owner commands — where justified only

I am proposing two coordination acts and **have performed neither**:

1. **Route W103525 for its reviewer disposition.** It is parked behind a closed
   blocker with `next` already set to `baton.feat`. The plan asks for exactly
   this: *"Return this small Job plan and the explicit residual
   substitution-design boundary for owner review."* An unpark is the owner's act.
2. **Decide the substitution question in §4**, or record it as a separate
   selected Work. The plan explicitly declines to create a third Job for it; it
   remains unowned until the owner places it.

**No closure command is justified yet.** W103525 should not be closed as fully
certified — the plan says so directly, and §1's qualification means the retained
evidence supports a *staged* disposition, not full historical certification.

## 6. Reconciled wording, no new decisions requested

- **The jsonschema question is settled.** The plan requires
  *"resolving/revalidating jsonschema 4.19.2 versus 4.26.0"*. The recorded
  environment (`finding-managed-apply-settlement/environment-172988.json`) and
  the observed interpreter both read **4.26.0** with python **3.13.7**. I
  verified this while preparing the W156162 report. Earlier exports remain
  nonconformant evidence with their recorded limitation.
- **Spending wording.** The plan carries W103525 author "289 runs
  1063.5077970099796/1200s … remaining 136.49…" and a preserved historical
  overrun. Under `AGENTS.md` line 95 (owner ruling 2026-09-14) cumulative
  stopwatch budgets are **not approval**, so the *remaining* figures should be
  read as history rather than as an allowance governing any successor. The
  measured numbers and the unwaived overrun stay recorded. Proposed for the
  owning dossier; I edited nothing.

## 7. Assumptions and limits

- I ran nothing. Behavioural claims come from reading source, the cited test
  body, recorded reviews and canonical state; structural claims are citations.
- I re-verified the two pinned artifact hashes and the artifact count, **not**
  the 88 individual trace exports or the 18-schedule audit. Those remain
  accepted on their original review, with its stated limitation.
- I did not read `CONSOLIDATION.md`, `BUDGET-DISPOSITION-…`,
  `CONTINUATION-…` or the per-run ledgers in full; the disposition above follows
  `SELECTED-PLAN-161345.md`, which supersedes the consolidation's
  recommendations by its own terms.
- Nothing here closes, reclassifies, reroutes or re-gates any original, and none
  of it is a new release prerequisite.
