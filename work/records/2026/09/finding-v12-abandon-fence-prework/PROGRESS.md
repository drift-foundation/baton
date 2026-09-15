# Progress

## Claim 174060 — baton.claude, advisory read-only pre-work

Claimed W174050 standalone at seq 174060 after finishing the W173923
correction. Read this dossier's FINDING.md and PLAN.md, the original
W63255 dossier `work/records/2026/09/finding-v12-pre-attach-abandon-leaves-live-assignment/`
(FINDING through the 2026-09-14 owner decision), the current
`dogfood_operator._recovering`/`_pre_attach_recovered` path, the reusable
abandonment/fence owners in `worker_manager/intake.py` and
`worker_manager/authority_port.py`, the runtime axis vocabulary in
`worker_manager/schema.py`, and the relevant **test bodies** in
`tests/tools/test_dogfood_operator.py`,
`tests/tools/test_quiescent_assignment_finalization.py` and
`tests/manager/test_attempts.py`. Claimed no original Work.

**The evidence standard was the point of this pass and I followed it.** One
claim ago, on W173923, I asserted coverage gaps from test filenames and the
owner had to correct me. Here I read the case bodies before saying anything was
missing, and the result is a gap that is demonstrated rather than inferred:
every `authority_fence` assertion in `test_dogfood_operator.py` sits on the
attached branch — one of them two lines after `branch == "abandonment"` — no
pre-attach case asserts a fence or `resolved: true`, and the direct
`_pre_attach_recovered` call passes `object()` where a port would go, which is
positive evidence the helper uses none. I also recorded one genuinely uncertain
item (whether a command-level pre-attach case exists outside the two modules I
read) as uncertain rather than commissioning work for it.

**Revalidation:** the 2026-09-01 root cause still holds exactly —
`_pre_attach_recovered(record, store, adapter, given, *, orphan, launch_home)`
at `dogfood_operator.py:2905` takes neither the Authority port nor the reason,
so no authority operation is reachable on that branch. All five reusable
boundaries named by the 2026-09-01 review are present and unchanged in shape.

**Coordination finding, recommendation only:** the 2026-09-14 decision said the
owner must add the W2 dependency and unpark W63255, and explicitly did not claim
those acts. Neither has happened — W63255 is `phase: parked` with no links at
all, and W2's `blocked_by` names W161230, W161234, W156162, W103525 and W61599
but not W63255. I changed nothing.

Deliverable: `PREWORK.md`,
`sha256:eb543aca3d5bb7604b978aedb3e3c3752309686ba7640b71074969b79888d6a3`.

**Boundaries honoured.** No test, probe, provider, model, engine, build, Git
mutation or worker; no product, test or original dossier edit; the original
Work, its parked state, its route and the dependency graph are untouched.
Verification spending this claim: **zero measured seconds**.
