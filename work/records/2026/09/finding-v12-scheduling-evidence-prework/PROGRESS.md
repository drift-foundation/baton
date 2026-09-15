# Progress

## Claim 174115 — baton.claude, advisory read-only pre-work

Claimed W174052 standalone at seq 174115, after returning W174051. This
completes the owner's second pre-work series (W63255, W61599, W103525). Read
this dossier's FINDING.md and PLAN.md, `SELECTED-PLAN-161345.md` and the
consolidation and review it supersedes, the canonical states of W103525,
W161230, W161234, W156162 and W71830, the four scheduler/serving owners the
plan cites, and the **test body** of
`tests/job_manager/test_scheduling.py:201`. Claimed no original Work; closed,
reclassified, rerouted and re-gated nothing.

**Two findings changed the disposition from what the plan recorded:**

- The plan warned that W161234's dependency edge did not exist and must not be
  described as a recorded gate. **It exists now** — W161234 is `blocked_by`
  W161230, as is W156162. That caution is satisfied and should not be carried
  forward as open.
- **W103525's own blocker is already discharged:** W71830 is closed satisfying
  at seq 153656, so W103525 sits parked behind a closed dependency with `next`
  already pointing at `baton.feat` — which is exactly the reviewer disposition
  the plan asked for.

**Evidence revalidated rather than assumed:** both pinned artifact hashes
(`scheduler_trace.py`, `test_scheduler_trace.py`) still match the consolidation
matrix, and the 88 trace/review exports are still present, so the accepted
foundation is citable without a re-run. Its own limitation is carried forward —
`review-2026-09-13T14-10-03Z.md:27`, "does not claim fresh execution of every
exported method" — so this supports a staged disposition, not full historical
certification.

**The one concrete remaining decision is operator-designated substitution.** I
verified the plan's four source claims and read the cited test body instead of
trusting its name: `test_affinity_is_soft_and_fallback_does_not_rewrite_it`
asserts `selection_outcome == "fallback"` and, reading the `worker_affinity` row
directly, that the stored preference is unchanged. `reserve(store, stage, *,
excluded=None)` has no designated-replacement operand. The gap is real, and the
choice between a configuration revision and a durable substitution record is the
owner's product-shape decision — I deliberately make no recommendation between
them.

Also settled while preparing this: the plan's jsonschema 4.19.2-versus-4.26.0
question resolves to 4.26.0 on python 3.13.7, matching the recorded environment.

Deliverable: `PREWORK.md`,
`sha256:62216cf955ce4292fc183c6fd820bfcb06a0a3165434804fb3a8e26a8fc98d90`.

**Boundaries honoured.** No test, probe, provider, model, engine, build, Git
mutation or worker; no product, test or original dossier edit; no closure,
reclassification, reroute or dependency mutation; no new stress campaign or
deferred-scope revival. Verification spending this claim: **zero measured
seconds**.
