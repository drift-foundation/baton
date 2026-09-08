# Proposed exact owner seam — claim112312, awaiting ops assignment

Owner112288 authorized six paths. Review112223 explicitly requires identifying a
missing read-only owner seam before expanding custody/intake. This proposal adds
only the two paths needed to put historical receipt interpretation at its owner:

- v12/python/src/baton_v12/worker_manager/custody.py
- v12/python/tests/manager/test_custody.py

Proposed additive operation: historical_directory_custody(store, assignment_id,
which), with no adapter or caller image operand. The custody owner derives its
existing operation identity; requires the exact committed normalize kind; reads
and validates the recorded signature's attempt/root/verb/image/workspace-store
bindings against the requested subject and configured recorded store; validates
the result's closed receipt/account contract; returns the exact committed
receipt or a typed refusal. The historical image is evidence of the committed
act, not an assertion that the present deployment selects that image. No helper
execution, normalization, filesystem repair, new journal format or current
adapter capability is introduced. Existing adopted_directory_custody retains
its present deployment-image collision semantics.

The existing review_cycles scope consumes the new reader for result then
workspace and compares the full nested cleanup mapping with both returned
receipts. Reject malformed/missing/foreign nested receipts, missing/pending/wrong
normalization records, mismatched signature subject/store and result/account.
Preserve actual positive eligibility and ending replay without an adapter.

Schedule additive owner cases in test_custody.OneSignedReceiptPerRoot and the
existing actual-custody driver fixture. Preserve all old assertions, public
APIs and existing test behavior. Extend only exact new boundary attribution and
reaching probes in the already assigned test_boundary_inventory.py as required
by the final owner reader. Run focused custody/review suites and inventory gate;
return hashes and diagnostic deltas to independent review. No baseline backlog,
W112029 files or downstream/live scope is included.

Evidence: evidence/correction-112312/owner_seam_probe.py and .json show both
result/workspace adoption succeed with the genuine adapter and fail without its
image identity after an actual completed public custody ending, with no repeated
external actions or journal writes. No required file was unreadable.

## Accepted 2026-09-07, owner112383

The proposal and the exact two-path extension above are approved. This
supersedes the awaiting-ops heading/status for execution by tuner claim112385;
all bounds and scheduled additive tests remain in force.
