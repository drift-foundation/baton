# Plan

**Status — revalidated 2026-08-17:** implementation-ready as W202, queued after
W235. The old vocabulary is authority-wide rather than cosmetic: schema table
and columns, event kinds/payloads, transition names, CLI grammar, JSON/detail
projection, due-action keys, TUI labels, both readiness bridges, documentation,
and source/packaged workflow stories all carry `round`. This is an honest
breaking schema/projection change under the already approved fresh-authority,
no-alias/no-migration boundary; bump those versions rather than accepting old
names.

1. Revalidate every authority table/event/payload, transition, projection,
   grammar, TUI, documentation and workflow use of `round`.
2. Rename the creation command to `try` and the durable concept to `trial`
   without leaving a compatibility alias.
3. Keep the object subordinate to Work and preserve report, assessment,
   deadline, replacement, abandonment and close-time audit semantics.
4. Update source and packaged workflows, negative grammar coverage and JSON/
   TUI parity.
5. Run the complete v11 gate and return for independent review.

Do not mechanically replace unrelated English uses such as “review round” or
test iteration. The closed vocabulary is the candidate-verification domain:
`try`, `trial`, `trials`, trial number/summary, and `due_trial` readiness.
