# Owner decision: test changes preapproved until further notice

Recorded by baton.prompt on 2026-09-13 from Slawomir's interactive instruction:

> let's not require test approvals until further notice. We need to be moving at fast pace for now

Effective immediately across Baton Work, agents may make test changes needed for
the authorized Work outcome without returning for per-test, helper or additional
test-path approval. This includes adding, editing, replacing or removing tests,
fixtures, assertions, expected behavior and registry entries. All implementing,
reviewing and integrating roles are covered until Slawomir revokes the ruling.

This explicitly supersedes the general case-specific test-approval requirement
and older test-only scope gates, including the W161230 gates that produced
obligations161874 and162258. Those approvals remain historical evidence; future
necessary test changes do not need equivalent amendment round trips. The repeated
fixture scope returns prompted this decision to speed the development loop.

Record affected paths and reasons and coordinate file ownership without making
that documentation an approval gate. Independent review must still validate
expectations against accepted behavior; acceptance and genuine defect coverage
cannot be waived merely to pass tests. Product scope, execution budgets, claims,
Git ownership and reviewed candidate/provenance requirements remain applicable.

Current state: effective in baton:AGENTS.md under "Standing test-change authority
until further notice". The live reviewer owns W161230 FINDING/PLAN and should
append this ruling's chronological reference, update the current plan and carry
it into the implementation handoff. baton.prompt owns this decision note and the
AGENTS.md policy edit; no product, test or implementer PROGRESS edits are made.
