# Finding — first-class decisions, reactions, and voting

**Status:** direction and non-dismissible decision obligation confirmed by
Slawomir on 2026-08-09. On 2026-08-10 he also ruled the universal TUI actions:
`+` means thumbs-up/upvote and `-` means thumbs-down/downvote. For an ordinary
directed message, either is a lightweight response that finishes the
recipient's obligation without requiring a ceremonial text reply. Storage/API
details still require implementer/reviewer design review as part of protocol
10. He subsequently ruled that `pin` is another meaningful reaction and
that the protocol must not freeze reactions to a closed LIKE/DISLIKE list.

## User need

When a message asks for a yes/no decision, the recipient should be able to
answer with a universal LIKE/DISLIKE action. The Messages list should show the
answer at the right edge so an old decision can be judged without opening the
thread. With team and multi-recipient audiences, the same primitive naturally
extends to voting.

## Recommended boundary

Do not encode this only as an arbitrary `outcome` string on an ordinary reply.
That works for one reviewer and loses the properties needed by a shared
inbox: one answer per participant, aggregation, timestamp, replacement, and a
stable query surface.

Protocol 10 should introduce a first-class message-linked reaction/decision
record with at least:

- target message ID;
- reacting participant;
- an extensible validated reaction token; initial conventional values include
  `like`, `dislike`, and `pin`, but the schema has no closed value CHECK;
- creation/update timestamp;
- immutable audit evidence when a participant changes their answer;
- uniqueness of the current answer per message and participant.

An explicit decision request creates the stronger durable obligation described
below. Ordinary directed messages may also receive `+` or `-`: the reaction is
a real minimal response, not merely social metadata, and atomically completes
the matching active claim just as a text reply would. The sender can therefore
see that the recipient picked a side without forcing the recipient to compose
"approved" or "disapproved" as a new body. The authority must expose this as a
reaction response rather than pretend that text was delivered.

This lightweight ordinary-message response must stay distinct from a declared
decision request. On a decision request, the same `+`/`-` action records the
durable LIKE/DISLIKE answer and satisfies that participant's decision
obligation. A text reply alone still cannot do so. For an ordinary message
there is no separate decision obligation to preserve after the reaction.

## Extensible reaction vocabulary — ruled

Reactions are protocol data, not transport lifecycle states. `pending`,
`claimed`, `completed`, and the other message states continue to describe
delivery/disposition. `like`, `dislike`, `pin`, and later meanings describe
what a participant says about the message.

The protocol validates a bounded portable token shape and length, ownership,
target, audience authorization, and retry identity. It does **not** enumerate
the only allowed semantic values in schema text. Unknown-but-valid tokens are
stored, audited, returned exactly, and may be rendered generically by an older
client; this lets the vocabulary evolve without another protocol bump merely
to add a reaction word. The initial TUI gives `like` and `dislike` the ruled
`+` and `-` shortcuts. Do not consume direct keys for every later value. The
generic TUI spelling is `:reaction_name`; the initial pin reaction is entered
as `:pin`. Thus common voting remains one keystroke while the vocabulary can
grow without growing a conflicting shortcut table.

The colon spelling is a TUI command surface, not part of the stored value.
`:pin` stores the normalized token `pin`; a delivery/scan exposes `pin`, not
the leading colon. Completion, validation feedback, and discovery for reaction
names should be designed with the protocol-10 TUI rather than accepting typos
silently.

The rendered reaction notation is `{pin}`. Slawomir chose braces to distinguish
the message reaction visibly from Baton's existing “hash-pinned” external-part
guarantee without giving up the familiar reaction name. The three layers are
deliberately distinct and pinned: type `:pin`, display `{pin}`, store `pin`.
Braces and colon are TUI presentation/entry syntax; neither is protocol data.

Extensibility does not mean any token satisfies any obligation. A declared
decision mode names the answer values it accepts. The initial Yes/No mode
accepts only `like` or `dislike`; `pin` or a future reaction may acknowledge
the message socially but cannot clear that decision. This rule must be checked
by the authority, not inferred by the TUI.

## Confirmed invariant — a requested decision cannot be dismissed

When the author explicitly requests Yes/No, the addressed participant cannot
`close` the item without choosing LIKE or DISLIKE. An ordinary reply does not
satisfy it either. The recipient may need more information first, so they can
send clarification/follow-up messages, but the original decision obligation
remains outstanding and must be revisited after the discussion.

This means the decision obligation is durable state separate from the
delivery claim and from any one reply message:

- requesting more data does not terminally erase the decision;
- follow-ups can continue in the same thread while the original remains owed;
- the TUI keeps or returns the original decision to the actionable list;
- only the recipient's LIKE/DISLIKE answer atomically satisfies their
  obligation;
- the author may explicitly withdraw/cancel the decision request, with an
  audited reason; no recipient can simulate that by closing it;
- in a multi-recipient decision, each participant's obligation is independent.

The protocol-10 follow-up/progress surface is the natural way to request more
information without abusing terminal reply semantics. If the implementation
retains claims as short-lived delivery ownership, claims may reach a terminal
transport disposition while the separate decision obligation remains open;
the public API and TUI must never present that as "decision complete."

For a directed decision, one recipient produces one answer. For scoped/team
or multi-recipient decisions, each addressed participant produces their own
answer and the authority exposes an aggregate. This is the first useful voting
surface without prematurely designing arbitrary polls.

## TUI presentation

- `+` records thumbs-up/LIKE and `-` records thumbs-down/DISLIKE. On an
  ordinary directed message this is the complete lightweight response; on a
  declared decision it is the required durable answer.
- Show the current answer or aggregate at the right edge of the list row;
  preserve subject space first and omit/compact the answer on narrow screens.
- Do not reuse the left status glyph: it answers whether work is owed, while
  the right-side mark answers how the decision went.
- Avoid assuming emoji display width. The ruled input and ASCII-safe display
  vocabulary is `+` / `-`; a richer terminal may additionally render a
  thumbs-up/down presentation only if width and fallback stay deterministic.
- Detail view shows who answered, their value, and timestamp; aggregates must
  never hide individual auditable votes.

## Questions for protocol-10 design review

1. Is a reaction a separate event/table or a specialized response message?
   Reviewer recommends a separate typed record while keeping an audit trail.
2. May an answer be changed, and if so does the list show only the current
   answer while audit retains prior values? Reviewer recommends yes.
3. How does a short-lived delivery claim interact with the durable decision
   obligation? The invariant is fixed: transport completion cannot make an
   unanswered decision disappear, and LIKE/DISLIKE satisfies that
   participant's obligation atomically.
4. Can an author vote on their own request? Default recommendation: only if
   explicitly included in the decision audience.
5. How are aggregate counts exposed without leaking answers outside the
   message audience?

## Acceptance properties

- reacting and satisfying a decision obligation are one transaction;
- reacting to an ordinary directed message records the typed response and
  completes the matching active claim in one transaction, with no invented
  text body;
- `close` and ordinary reply are refused as substitutes for LIKE/DISLIKE, or
  leave the decision obligation visibly outstanding if transport claims are
  modeled separately;
- clarification/follow-up messages do not clear the original decision;
- retry is idempotent for the same value and explicit for a changed value;
- one participant cannot overwrite another participant's answer;
- multi-recipient aggregation is deterministic and audience-scoped;
- list/detail/scan expose the same current answer;
- an unknown-but-valid reaction token round-trips and is audited without a
  schema/protocol edit;
- malformed, oversized, or unauthorized tokens are refused;
- `pin` is recorded as a reaction but cannot satisfy a Yes/No obligation;
- `+`/`-` dispatch the conventional values and `:pin` dispatches `pin`, with
  the colon absent from stored protocol data;
- the `pin` reaction renders as `{pin}`, while hash-pinned continues to name
  external-content verification;
- ordinary directed-message claim/reply/close semantics stay unchanged;
- older protocol-9 authorities are refused cleanly rather than partially
  interpreting reaction metadata.
