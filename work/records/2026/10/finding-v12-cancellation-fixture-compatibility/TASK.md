# Prepared input-only coding task

Proposed task: `cancellation-fixture-keyword-compatibility`.
Template: `baton.v12.job-template.implementation-review/1`.
Source: `installed`, after the selected installation/base is explicitly checked for this Job. This is preparation, not an installed task or create command with execution authority.

Statement: Repair the cancellation test-double keyword compatibility mismatch in CancellationFixture so the existing late-binding and before-attachment cancellation tests exercise the production composition. Preserve every existing assertion and expected cancellation, hold, stop and late-activation behavior. The adapter double must remain bound to the intended fixture adapter while accepting the production call shape, including attempt_id. Do not change production cancellation semantics or mask failures. Demonstrate the original failure and the corrected behavior using deterministic fake-engine tests, retain exact candidate evidence, and return independent review with report-and-hold.

Initial work/test scope: `v12/python/tests/manager/test_authoring_enforcement.py`. Read-only source evidence includes `v12/python/tools/single_worker.py`, `stage_execution.py`, `authoring_enforcement.py`, worker_manager/attempts.py and tokens.py. Implementation chooses necessary files within the bounded fixture outcome; any parallel overlap needs explicit ownership coordination.

Acceptance criteria:

1. The original keyword mismatch is demonstrated from the selected baseline; changing only fixture call compatibility permits the real cancellation composition to run. No product semantics or selected task policy changes.
2. Every existing assertion remains intact, including LateBindingCancellation and ALL BeforeAttachmentCancellation cases. Preserve expected outcomes rather than catching/ignoring TypeError or replacing failure assertions with success-shaped fixtures.
3. Authority cancellation precedes runtime stop; refused Authority fencing cannot stop a runtime. Stop failure/unknown observation retains the exact hold, and acknowledgement-only stop is retried when the writer is still observed running.
4. Deadline/operator/recovery cancellation before attempt attachment retains correct token/runtime identity; disagreement refuses. A late binding and later activation remain stopped under the original stable fence and stop identities without granting more time or releasing uncertain ownership.
5. Focused deterministic evidence passes the two requested classes through production routing and cancellation, using fake engine/workspace boundaries. Preserve source/base, exact diff/candidate digest, commands, results and any unrelated failures separately. Independent review confirms no assertions weakened and no production change concealed; report-and-hold pending human disposition.

Suggested verification (outcome controls; command is not exclusive): from v12/python with its normal src import path and disk-backed test root, run `python -m unittest -v tests.manager.test_authoring_enforcement.LateBindingCancellation tests.manager.test_authoring_enforcement.BeforeAttachmentCancellation`. Reuse discovery evidence, but revalidate source at actual assignment. Any additional focused test needed to expose the fixture contract is within the outcome. No real container/provider is needed for verification.

Candidate receipt is not owner acceptance. No automatic integration. Invocation limits, actual installation, task registration/admission and any live authoring-model allowance must be selected for this later Job; the documentation Job's live grant authorizes no second Job. Do not manufacture future UUIDs/receipts or copy its task manifest.
