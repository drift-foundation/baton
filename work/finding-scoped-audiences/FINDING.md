# Scoped audiences and multi-recipient delivery

Folder: `work/finding-scoped-audiences/`
Status: pinned for the next protocol stage after CLI-to-core adoption; not part
of the current protocol-9 TUI+core commit.

Raised by Slawomir during the `baton-tui` trial on 2026-08-08.

## Problem

Baton currently has two audience shapes: one exact recipient for a directed
message, or every configured participant for a notice. That is too coarse for
a multi-team deployment. A Baton-team announcement should be addressable to
`baton.*` without waking every participant in every unrelated team, and one
directed publication should be able to require independent action from several
explicit recipients.

These are related audience features but they do not share lifecycle semantics.
A scoped notice is still a notice; a multi-recipient directed publication is
still claimable work for every recipient.

## Pinned model

### Scoped notices

- A notice may target all configured participants, preserving today's global
  broadcast, or a team scope such as `baton.*`.
- A team scope is a dotted participant-prefix selector ending in a literal
  `.*`. It matches complete dotted segments only: `baton.*` matches
  `baton.reviewer` and `baton.implementer`, never `baton_extra.reviewer`.
- The selector expands against the validated participant registry in the SAME
  transaction that publishes the notice. The resulting explicit audience is
  stored immutably; later config additions/removals never rewrite history or
  acquire a previously published notice.
- Every audience member has an independent at-most-once seen receipt. Delivery
  through `see`/`wait` creates no claim, exactly as for a global notice.
- Existing author-delivery parity remains: a matching author is in the
  audience unless a future, explicit exclusion feature is separately approved.

### Multi-recipient directed messages

- One logical publication may name two or more exact configured participants.
  Duplicate recipients are rejected rather than silently changing the request.
- Publication is atomic: either every recipient delivery is created against
  the same immutable content manifest and subject, or none is.
- Each recipient gets a distinct pending delivery, claim, retry lifecycle, and
  terminal disposition. Claiming, replying to, closing, recovering, damaging,
  or quarantining one delivery cannot resolve or mutate another recipient's
  delivery.
- A reply goes to the original sender by default. It does not implicitly copy
  the other recipients or disclose their replies as a group conversation.
- Delivery identifies the original audience so a human can distinguish a
  private message from work deliberately assigned to several participants.

## Safety and retry identity

- Stored audience membership, not a live glob re-evaluation, governs delivery.
- Retry identity includes the audience kind, selector where applicable, and
  the canonical explicit recipient set. A retry that would address a different
  set fails closed rather than silently widening or narrowing delivery.
- Participant existence and capabilities are validated before any publication
  row commits.
- Content may be stored once and referenced by per-recipient delivery rows,
  but this is an implementation choice only if retention, damage, audit, GC,
  and disposition invariants remain independent and exact.
- No raw SQL, filesystem mailbox, or host-project participant assumptions are
  introduced.

## CLI and TUI direction

- CLI syntax must keep global notice, scoped notice, one-recipient directed,
  and multi-recipient directed requests unambiguous. Exact flag spelling is a
  design task; a wildcard must never be accepted where an exact participant is
  required by accident.
- The TUI audience picker must offer global, configured team scopes, and
  explicit participants without free-form typo paths. Multi-selection must be
  visible before send and cancellation must publish nothing.
- Inbox rows and detail headers show enough audience information to distinguish
  global, team-scoped, private, and multi-recipient traffic without claiming
  or marking anything seen.

## Sequencing

This requires new persisted audience/delivery relationships and changes wire
delivery, dump, scan, retry, GC, doctor, and UI behavior. It is protocol work.
Do not widen the current protocol-9 TUI+core commit or the subsequent
protocol-9 CLI-to-core adoption with it.

After CLI adoption lands, review this together with
`work/finding-part-name-semantics/` for one protocol-10 implementation and one
communications-first cutover rather than consecutive mailbox teardowns.

## Acceptance evidence

- `baton.*` reaches every and only configured `baton.` participant, including
  independent delivery to reviewer and implementer.
- A global notice retains current delivery and author-parity behavior.
- Scope membership is frozen at publication across config changes and retry.
- A multi-recipient directed publication creates independent claim/disposition
  lifecycles; resolving one recipient leaves every other copy actionable.
- Publication failure cannot leave a partial audience.
- Duplicate, unknown, malformed, empty, and mixed wildcard/exact audiences
  fail closed with no authority writes.
- Observation in scan/TUI creates no claims or notice receipts for any member.
- Polling fallback and the query-to-arm race wake every eligible recipient
  without waking unrelated teams.
- Dump, doctor, retention, GC, attachment damage, quarantine, and recovery
  preserve per-recipient and shared-publication invariants.
- Standalone builds and documentation contain no Drift-specific team list.
