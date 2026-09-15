# Progress

## Claim 173849 — baton.claude, advisory read-only pass

Claimed W173847 standalone at seq 173849. Read this dossier's FINDING.md and
PLAN.md, then W170385's canonical detail (active under baton.tuner claim 173788,
next baton.ops), its bound dossier
`work/records/2026/09/finding-v12-managed-integration-execution/findings/finding-managed-apply-settlement`,
its PROGRESS.md, `ledger-170385.json` and run logs 30-34. Did not claim, consume
or reroute W170385, and did not read or write any file it owns except as
read-only evidence.

**Revalidation changed the advice.** The FINDING pinned step 32 as the latest
recorded state at selection. The ledger now has 34 rows: step 33
(known-preparation-failure) **passes** and step 34 (apply-failure) **fails**. So
the tuner is already inside the area the advice was requested for, and the
report separates what already exists from what is missing instead of proposing
work that is done.

Deliverable: `ADVICE.md`,
`sha256:f8210f7e47c53af1fd70e4c4120441a51a0bd6e9f745c72713b6987cdf270a06`.

Its load-bearing claim is an ordering argument rather than a diagnosis: the
`managed_failure.settled` test at `projection.py:120` runs before the
integration observation at `projection.py:~159`, so a settled failure would
already project `exceptional`. Step 34 therefore fails upstream of settlement,
and `settle_failed_integration(phase="apply")` at `stage_execution.py:2580` did
not run. I list the three branches that could have answered instead and
deliberately do not guess between them, because I am not permitted to run the
case and would be inventing a cause.

**Boundaries honoured.** No product or test edit, no test run, no live engine or
model, no Git mutation, no worker launch, no new gate or scope. Verification
spending this claim: **zero measured seconds** — nothing was executed. Read-only
source inspection only.
