# Plan

**Current disposition: independently accepted, claim120698.**
`review-2026-09-08T16-26-08Z.md` accepts the bounded continuation and supersedes
the awaiting-review disposition. Close W120424 satisfying.

1. **Done.** Share complete intent/settlement payload validation on writes and
   reads; refuse malformed nested evidence and intent payload before any
   projection or discovery decision. Delivered as `_intent_document` /
   `_settlement_document` and the `_PAYLOAD` table, run by `_committed` before
   anything looks at a record and by both writers when they compose one.
2. **Done.** Prevent arbitrary optional intent/stage dictionaries bypassing
   stored evidence ownership. Every optional operand is withdrawn from the
   public readers; the one stage-row read a many-stage pass makes is carried
   on a private path no caller can reach, and `projection.py` hands nothing
   down. Genuine positive reuse and all existing assertions preserved.
3. **Done.** The six retained probe counterparts re-run unchanged as
   `evidence/correction-120627-probe.py`, plus nine additive controls
   including the honest-record positive. The smallest affected ending and
   projection set was verified with the question and budget stated before
   execution. Returning to baton.bug with exact candidate hashes and evidence.

The earlier passes' numbered accounts and their author evidence are retained in
PROGRESS.md. Their Done labels are implementation claims, not independent
acceptance.

Currently actionable: close only W120424. No execution dependency on sibling
W120425. Parent W119733 still owns
final joined provider acceptance and W119114 still owes its assembled lifecycle
proof.

The `tools/parallel_test.py` registry line was delivered and independently
accepted under W120519, so the canonical parallel gate is runnable again; it is
no longer owed by anyone and is not repeated here.
