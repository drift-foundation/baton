# Owner direction — short correction loops

2026-09-17, recorded by baton.prompt from Slawomir's explicit instruction.

The owner rejected describing 743 checks across six suites as focused
verification: it is a sweep. Run short tests first so this bounded change does
not consume hours in repeated broad verification and handoffs.

For each correction, select the specific failing reproduction and the smallest
adjacent regression set that can answer whether the correction works. Reuse
unchanged evidence. Broaden only when changed behavior or unresolved interactions
justify it, normally when the complete candidate is ready. Do not repeat hundreds
of tests merely because another implementation/review turn started. Report test
selection and elapsed time honestly; raw counts are not evidence of focus.

This supersedes any reading of the current PLAN or prior handoffs as requiring
suite sweeps on each correction. It preserves required acceptance, independent
review and genuine defect coverage. It adds no stopwatch approval gate. Finish
the bounded shared-identity change without unrelated redesign or a broad stress
campaign. Author and reviewer should reflect this cadence in the current PLAN
at their next owned update; no product or test files are changed by this ruling.

## Previously confirmed deployment clarification

After independent acceptance, build a fresh standalone instance at
`/home/sl/baton-v12-instance-<UTC-ISO-timestamp>` (filesystem-friendly example:
`2026-09-17T14-30-00Z`, use actual deployment time). Preserve the old instance as
diagnostic evidence. Owner reports having run `just stop` there. The first Job
failed before provider execution; submit its task afresh to the new instance.
This explicitly supersedes the dossier's requirement to prepare in-place
upgrade/failed-attempt recovery instructions for the old instance. Do not expand
this Work to build recovery tooling. No deployment or new submission is executed
by this record.
