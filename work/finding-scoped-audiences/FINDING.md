# Scoped audiences and multi-recipient delivery

Folder: `work/finding-scoped-audiences/`
Status: protocol-10 core/CLI behavior released in 1.0.0; next-generation TUI
scope-picker child implemented and reviewer-signed-off for 1.1. Parent record
reconciled 2026-08-11; folder remains until the child lands and cleanup is
performed deliberately.

Raised by Slawomir during the `baton-tui` trial on 2026-08-08.

Decision recorded 2026-08-10: global notices freeze the configured recipient
set at publication, just like scoped notices. A participant added later does
not receive an older global notice.

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
- Every directed message belongs to an immutable publication record, including
  a single-recipient send and a response message created by `reply`. There is
  no private-message storage special case for later audience authorization.
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
- Publication is at-least-once. Baton does not correlate a repeated send with
  an earlier publication whose success result may have been lost.
- A sender repeating after an ambiguous result marks the new publication with
  an immutable `possible_duplicate` warning. The warning is advisory and
  sender-supplied; Baton must not imply that it proved a duplicate exists.
- The warning is available on at-least-once `send` and `send-notice` paths.
  Claim-bound `reply` and `close` retain their existing effectively-once
  claim-ID semantics.
- The warning is visible to every recipient and in inspection/history surfaces
  so recipients can decide how to disposition the repeated request.
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
- **Superseded for scoped-notice authoring on 2026-08-11:** the TUI audience
  picker was to offer global, configured team scopes, and explicit participants
  without free-form typo paths. Multi-selection remains visible before send
  and cancellation still publishes nothing, but scoped-notice entry is now an
  editable, filtering combobox rather than a closed choice list.
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
- An ambiguous retry may create a second frozen publication; when the sender
  marks it `possible_duplicate`, every recipient sees that warning.
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

## TUI audience-entry supersession — 2026-08-11

Slawomir ruled that the closed selector above would pollute the drop-box and
prevent manually addressing a team not represented by a precomputed choice.
For notice authoring, the control is text-first:

- typing filters/searches registry-derived suggestions live (`web` narrows the
  visible configured addresses/scopes);
- a complete manually typed selector such as `web.*` means a scoped broadcast
  and remains publishable without first choosing a drop-box row;
- the core still validates and freezes expansion at publication; the TUI does
  not expand a typed wildcard or fall back to global after refusal;
- explicit global remains visible rather than being inferred from an empty
  string.

## Exact notice-audience ruling — 2026-08-11

The semantic edge above is **resolved**. Notices are team-oriented; the only
TUI audience values are `*` for every team and a dotted team wildcard such as
`team-a.*`. Exact participants are not offered and no new one-person notice
lifecycle is added. A normal directed send remains the exact-participant path.

The drop-down/filter therefore presents only `*` plus valid configured team
scopes (`team-a.*`, `team-b.*`, …), never individual participant addresses.
Typing `team` narrows those scope options by prefix. In the TUI, `*` maps to the
core's existing global notice call (`scope=None`); it does not widen the core
scope grammar, where a bare `*` is not a selector.

## Current-state reconciliation — 2026-08-11

The opening sequencing status is historical and superseded: protocol 10 and
the scoped/global plus multi-recipient core/CLI work shipped in Baton 1.0.0.
The `PLAN.md` section titled “Not built at the WIP checkpoint” remains as
chronological evidence, not current truth. Reply publication linkage,
non-null fresh-schema enforcement, doctor coverage, public return shapes, and
recipient mappings were subsequently implemented and tested; the released
1.0.0 commit is `f64431d`.

The remaining TUI authoring child is no longer open implementation work. Its
editable `*`/team-scope combobox, retained-audience behavior, and safe local
draft versioning are approved in
`findings/finding-tui-notice-scope-picker/review-2026-08-11T15-55-03Z.md`.
The parent cannot be removed until that 1.1 work lands and Slawomir performs
the deliberate finding cleanup pass.
