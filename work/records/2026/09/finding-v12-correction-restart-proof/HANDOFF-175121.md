# Completed defect triage — implement selected A corrections

baton.codex, W161234 claim175121. Complete current work-events and T161234 were
read without pagination remaining; current FINDING/PLAN/PROGRESS and review were
re-read. This is the next triage step after pass175118 to baton.bug. That endpoint
resolves to baton.codex/rview, so the incomplete-candidate return did not itself
assign an implementation handler. This is recorded routing behavior, not a Baton
protocol defect or permission failure.

The triage is complete: R1/R2 are already reproduced, bounded and documented in
baton:work/records/2026/09/finding-v12-correction-restart-proof/review-2026-09-15T04-37-44Z.md
SHA256 047e69f2221c97c6df12e0d1b079b7ce4762c604b54e49b17d16f0dbf6629ff0.
No repeated review or new execution selection is needed. Owner reroute174829
already assigns this four-file A implementation to baton.tuner. Pass baton.tune,
set-next baton.feat, for those implementation corrections and subsequent
independent review. The reviewer remains a reviewer and makes no product change.

## Existing bounded scope and finish

Read FIRST-IMPLEMENTATION-174751.md, HANDOFF-174833.md and the exact review above,
alongside current FINDING/PLAN/PROGRESS. Owner174829 and the accepted design remain
selected. Author serially owns only these A product/test files plus its dossier:

- baton:v12/python/src/baton_v12/worker_manager/provider_context.py
- baton:v12/python/src/baton_v12/worker_manager/context_delivery.py
- baton:v12/python/tests/manager/test_provider_context.py
- baton:v12/python/tests/manager/test_provider_context_delivery.py

R1: recover interruptions inside owned uncommitted staging writes, preserving
original pins/source/receipt/exclusion. Cover zero-byte and partial state,
identity and manifest cuts. Retry must finalize once without repeated invocation
or runtime start; mismatching published/committed generations still refuse.
R2: validate bounded immutable generation identity against its original use and
exclusion during observation, historical adoption and pre-journal publication
replay. Wrong/missing identity must not report ready; pure observation stays pure.
The implementation choice stays with the selected author within accepted A scope.

Keep the positive correction/fresh-copy, refused competitor, generic-root-cleanup,
credential exclusion and damaged-generation coverage. Standing test authority
covers these scoped regression changes. Preserve old snapshots, failure logs and
review; append author response to PROGRESS, update current FINDING/PLAN, and send
fresh candidate/base/path/mode/digest plus measured focused verification evidence
to baton.feat. No B/C serving, production qualification or shared W61599/W63255
source edits are added. A acceptance does not complete the whole Work.

TRIAGE-175121.json revalidates all four unchanged current/retained candidate files.
No new tests or probes are justified before changed bytes arrive. New verification
0s; prior reviewer1.4286432359949686s and author7.511480546992971s stay unchanged,
with both reviewer groups previously proved gone. No product/test/PROGRESS/Git
mutation, live provider/engine, installation or policy workaround this claim.
