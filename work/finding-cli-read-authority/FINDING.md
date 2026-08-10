# Reading a message back through the CLI

Raised after a process failure of mine, recorded here rather than worked
around: verifying that a message I had just published carried the body I
intended, I read `mailbox.sqlite3` directly with `sqlite3` and compared a
`sha256` I computed myself.

That is the abuse of privileged access. Every other team that uses Baton has
the CLI and nothing else. If a question can only be answered by opening the
store, the product cannot answer it, and an agent sitting in Baton's own source
tree is the last participant who will notice — it will reach past the gap and
report success. The store is the coordination authority; reading it by hand to
answer a question the tool should answer is how a second, informal way of
knowing the mailbox's state gets established.

## What was actually a gap, and what was my error

Separating these matters, because only one of them is Baton's to fix.

**My error, twice over.** `materialize <message_id> --dir DIR --part 0`
projects a stored part to a file, and answers the question exactly: the
projection of the message diffs identical to the file I published from. And
`dump` does carry the content — the top-level `parts` and `contents` tables
hold every part row and every body. I concluded it did not because the
per-message record shows `"parts": null` and I looked no further. So the
detour was not even filling a gap. Two CLI paths already answered it.

**The gap that is real: `materialize` performs no authorization.** It takes a
bare `message_id` and has no `--participant` option at all. I projected the
body of a message addressed to `baton.reviewer`, from this participant, and
the tool did not ask who I was. Nothing else in the CLI behaves this way —
`claim`, `wait`, `see`, `reply`, `close` and `scan` are all
participant-scoped, and delivery of content is the one thing the protocol is
most careful about elsewhere.

This mailbox holds ten teams' agents in one file. Any of them can project any
other's message content, including messages neither sent nor received by
them. It requires no elevated access, no SQL, and leaves the reader's identity
unrecorded: with no participant on the command there is nothing to write into
`op_context` or the transition log, so a read that crosses a boundary is not
distinguishable afterwards from one that did not.

## A secondary point, minor but it is what misled me

`dump`'s message records carry `"parts": null` while the part rows live in a
sibling top-level table. That is a faithful rendering of the schema and a
misleading rendering of a message. It invites precisely the conclusion I drew.
Nothing about it is incorrect, so it is a clarity item, not a defect.

## Direction, not a decision

Three things are worth deciding, in this order:

1. **Should `materialize` require `--participant`, and refuse a message that
   participant is not party to?** The conservative answer is yes, and it is a
   behaviour change to a shipped verb, so it is a protocol-10 item rather than
   something to slip in. It also needs an answer for `human.slawomir`, who
   holds `recovery` and plausibly should be able to project anything.
2. **Is there a legitimate sender-side read?** Confirming what you published
   is a reasonable thing to want, and today it is served only by the
   unscoped verb. A participant-scoped read that covers messages you sent as
   well as messages you hold would remove the reason to reach for the
   unscoped one.
3. **Should the unscoped projection survive at all** as an operator tool, and
   if so should it record who ran it?

None of this is started, and none of it belongs in the current protocol-9
commit. It is filed for the protocol-10 umbrella.

## A second gap, found the same way

A NOTICE cannot be re-read after delivery. `wait` hands its body over once,
`see` then reports nothing because the receipt exists and at-most-once means
what it says, `dump` elides part bodies as `<125 bytes>`, and `materialize`
takes a MESSAGE id and refuses a notice id:

    baton materialize f667134b… --dir …
    baton: unknown message 'f667134b11a4270a52b8b0b1bf726e43'

So a participant who lets the delivered text scroll past — or, as here, prints
it through a formatter that truncates — has no way back to it. The subject
survives in `dump`; the body does not.

At-most-once is a deliberate protocol property and this is not a request to
weaken it. The recipient already HAS the bytes at delivery; what is missing is
any local record of them. That is a console and CLI question — offer to write
the delivered notice somewhere, or let `materialize` address a notice the
participant has already seen — not a protocol one.

Filed rather than worked around: the temptation was to read the body out of
`mailbox.sqlite3`, and that is the exact move this finding exists to forbid.

## Live recurrence — truncation made the missing reread path operational

On 2026-08-10 Slawomir published the status notice “I need status before we
consider this round ready for commit.” The implementer's `wait` correctly
recorded the at-most-once receipt, but her agent/terminal presentation
truncated the delivered text. A second `see` could not return it because the
receipt already existed. She recovered the body through `dump` plus an ad-hoc
formatter.

That recovery is exactly the privileged workaround this finding says must not
become normal operation. Nothing was corrupt and the receipt rule worked as
implemented; the product gap is that receipt-at-most-once is still conflated
with party-authorized reread.

This recurrence sharpens the required contract:

- delivery/receipt remains at most once and retry-idempotent;
- a participant in the immutable publication-time audience may read retained
  notice content again without creating another receipt, claim, disposition,
  or delivery event;
- the author may read their own retained outbound notice;
- a non-party learns nothing from the read surface;
- the read is an ordinary supported CLI/core operation, not `dump`, raw SQL,
  or a reconstruction script;
- scan/history may say content is available for reread without embedding all
  bytes in every listing.

Merely offering to save the first delivery is not sufficient: process output
can truncate before a human or agent has a chance to choose a destination, and
a crash can erase an in-memory copy. The authority already retains the bytes;
the missing piece is a correctly authorized reread.

Authorization must be designed after protocol 10's scoped and multi-recipient
audiences, because that immutable audience snapshot defines who is a party.
Therefore this recurrence raises the priority and acceptance evidence but does
not belong in the current protocol-9 commit.

## The convention, which does not need any of the above

Verifying what you published is right; how it was verified was not. The
verification a participant should reach for is `materialize` and a `diff`
against the source file — an assertion about bytes, made with the tool, not
about a hash computed beside it. Reading `mailbox.sqlite3` is not a fallback
when the CLI seems not to offer something. If the CLI cannot answer a
question, that fact is the finding.
