# Review — protocol-10 read-only wait and cutover docs

Outcome: **approved** (fresh protocol-10 authority remains live).

The implementation and cutover are operationally sound: the fresh authority
opens cleanly, `wait` observed a message published while it was blocked, the
reviewer then claimed it explicitly, and the focused readiness/publication
suite passes. The documentation correction found and resolved the stale public
flow claims below.

## R1 — the README walkthrough must claim the message `wait` named

`wait` reports a specific FIFO-head `message_id`, including when that head is
damaged. The walkthrough then runs bare `claim --participant`, which is a
different operation: it may skip damaged work and may select a different
message if the queue changes. Capture/copy the readiness `message_id` and use
`claim --message-id` in both the reviewer and implementer receive examples.

This is the central safety contract of the split, not presentation polish.

## R2 — the core-command summary still promises delivery from `wait`

README's `Core commands` section still describes `wait` as “the same directed
delivery, or a broadcast notice.” It now returns readiness metadata only.
Update that summary to point at explicit `claim`/`see` consumption.

## R3 — protocol wording still says notices are received through `wait`

The notice bullet begins “Consume with `see`, or receive them on the blocking
`wait` path,” immediately before correctly explaining that `wait` only reports
notice presence. Say instead that `wait` reports their presence and `see`
receives them. In the live-turn convention, “Delivery returns to the LIVE
turn” should likewise distinguish readiness returning from the subsequent
claim delivery.

## R4 — pin the documented timeout status at the public CLI boundary

The runner-loop documentation now promises exit `0` for readiness and exit `3`
for an idle timeout. `test_blocking_readiness_times_out_like_wait` pins the
internal helper's `BatonError.exit_code`, while the existing CLI notice test
pins the public success status. Add the missing public CLI timeout assertion
(through `main`, alongside the other CLI wait tests) so a future dispatch or
error-handling change cannot silently break runner loops while the helper test
stays green.

After these edits, rebuild both packaged artifacts because the pinned protocol
document changes, run `git diff --check`, and report the final hashes and test
result. Do not disturb the live protocol-10 authority.

## Evidence checked

- fresh authority: protocol 10, maintenance off, doctor `ok: true`;
- blocked `wait` returned a newly published directed message without claiming;
- explicit `claim --message-id` and reply completed it;
- focused readiness/publication suite: 24 passed;
- current artifact and protocol-document hashes match both distribution
  manifests before these requested edits.

## Final verification

R1–R4 are resolved. The second receive example uses its own `RESPONSE_ID`; the
core-command and notice/live-turn wording distinguish readiness from delivery;
README and protocol policy document exit `0`/`3`; and public CLI regressions
pin both statuses. The deliberate break check proved the new timeout test fails
when only the public error mapping changes while the helper test remains green.

- implementer full suite: 2170 passed, 0 failed;
- independent focused readiness/CLI suite: 13 passed;
- `git diff --check`: clean;
- both packaged artifact hashes and source/protocol hashes match their
  distribution manifests;
- live protocol-10 authority remains healthy and ungated.
