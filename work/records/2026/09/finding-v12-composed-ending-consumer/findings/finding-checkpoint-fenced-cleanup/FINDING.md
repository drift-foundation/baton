# Resume cleanup after the checkpoint fence

W124784, parent W122060, follow-up to closed W119733. Created124784 during
reviewer claim124772. Owner124767 approves item2 of
`baton:work/records/2026/09/finding-v12-composed-ending-consumer/PROVIDER-ALLOCATION-PROPOSAL-2026-09-09.md`.
Read that complete item and parent `review-2026-09-09T03-44-04Z.md`.

**Confirmed:** end_implementation freezes a checkpoint, revokes its writer and
then calls authorize_cleanup. If cleanup refuses once, the next ordinary
driver entry requires the already revoked writer to be active. The historical
branch only handles destroyed runtimes. The parent serving probe retains the
actual quiescent/pending cut plus a separate consumer mount refusal; this Work
fixes the shared driver, while W122060 fixes the serving entry.

**Approved ownership:** baton.impl, High, returning baton.bug. Exactly
`v12/python/src/baton_v12/job_manager/review_driver.py` and
`v12/python/tests/job_manager/test_review_driver.py`, additive tests only.
Owner124767 permits concurrency with W124782's disjoint tune paths; ownership
remains reserved through independent acceptance. No schema, registry, consumer,
intake or other provider changes. Report missing capability before expansion.

**Acceptance:** existing public end_implementation resumes its own committed
checkpoint with revoked writer and cleanup pending. Validate exact original
assignment/generation and committed frozen, intake, retention, publication and
checkpoint evidence before continuing cleanup. No re-grant, repeated
publication, fabricated active writer, foreign checkpoint or destruction
without positive absence. Reopen actual owner stores at the cut and compare
the final ordinary answer. Preserve active-writer and destroyed-runtime paths.
Cumulative20s focused verification; preserve all existing assertions.

## Scope disposition and review — 2026-09-09

Campaign owner04:13Z/M124896 supersedes this intermediate continuation as an
independent milestone requirement. The already delivered candidate is accepted
for reuse in `review-2026-09-09T04-24-46Z.md`, with its exact bytes and budget
violation preserved. This does not revive stronger consumer proof obligations;
the parent `RESTART-ACCEPTANCE-2026-09-09.md` owns current acceptance.
