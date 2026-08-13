# Same-second messages and notices lack insertion ordering

## Observed

On 2026-08-13, protocol-10 successor testing published three broadcasts inside
one timestamp second. Sent history returned them in digest-ID order rather than
publication order (observed `third, first, second`). Directed queue selection
uses the same `(created_ts, id)` tie-break, so an unqualified `claim` also has no
insertion-order promise inside one second.

## Confirmed

- `created_ts` has one-second resolution.
- Message and notice IDs are random 128-bit hex values.
- `list_sent`, `list_messages`, readiness and unqualified claim selection use
  `(created_ts, id)` ordering. The result is deterministic but not chronological
  within one second.
- `transitions.seq` is monotonic but records only messages and claims; notices
  have no row in that ledger. It cannot define one total message/notice order.
- Standing Baton policy uses `wait` followed by explicit
  `claim --message-id`, and the TUI acts on a selected ID. The defect therefore
  does not substitute another delivery in normal coordinated use. All items
  remain present.

## 2026-08-13 ruling

Defer the correction to protocol 11. A truthful fix needs a shared persisted
publication sequence that orders messages and notices; that is a mailbox-schema
decision and must not be slipped into the supported protocol-10 interim release.
Protocol 10 retains its deterministic `(created_ts, id)` rule and documents the
same-second limitation. This is not a blocker for the 1.2.0 cutover.

## Protocol-11 acceptance boundary

- Assign a monotonic authority-local sequence transactionally at publication.
- Define whether a multi-recipient directed publication has one publication
  sequence or one delivery sequence; do not let recipient count change author
  history ordering accidentally.
- Use the same authoritative order for readiness, unqualified claim, combined
  message history and Sent history, including notices.
- Preserve explicit-ID claim behavior and damaged-head semantics.
- Test same-transaction/multi-recipient, same-second, deletion/GC, restart,
  rollback, concurrency and maximum-sequence behavior.

