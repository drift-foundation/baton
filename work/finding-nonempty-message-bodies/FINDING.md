# Explicit message bodies may be empty

Status: **implementation ready for final review**. The CLI authoring surface
is tracked in `findings/finding-tweet-authoring/{FINDING,PLAN,PROGRESS}.md`.

## Finding

Baton can publish a zero-byte content record when a body source resolves
successfully but contains no bytes. `_read_body("-")` returns an empty byte
string for empty stdin, and `_read_body(PATH)` does the same for a zero-byte
file. The send, reply, close-with-body, and notice publication paths accept
that value and persist the SHA-256 of the empty string as if content had been
supplied.

This is not a transport truncation: the stored size is zero and the stored
digest is `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

A missing or unreadable body path already fails in `_read_body`; that behavior
must remain fail-closed and be covered alongside the zero-byte case.

## Required contract

An operation that requires a body, or for which the caller explicitly supplies
`--body`, requires **at least one byte** of content.

- `send` without an attachment must reject empty file or stdin input.
- `reply` must reject empty file or stdin input and leave the claim active.
- `send-notice` must reject empty file or stdin input and create no notice or
  seen receipt.
- `close --body ...` must reject empty input and leave the claim active;
  `close` with no body remains a valid bodyless terminal disposition.
- A missing, unreadable, or non-regular body path must fail before any mailbox
  mutation.
- The invariant belongs at the publication boundary as well as the CLI
  boundary: programmatic Store calls must not create new zero-byte body
  content.
- Failure is validation (`EXIT_VALIDATION`) and occurs before a transaction
  can publish a message, disposition, notice, content row, transition, or
  receipt.

“Content” here means nonzero byte length. A one-byte body, arbitrary binary
bytes, and whitespace-only bytes are content; this finding does not invent
text semantics. Attachment behavior is unchanged and is outside this finding.

## Compatibility and retry

Existing zero-byte records remain valid historical data: they must remain
openable, diagnosable, and deliverable. No schema rewrite or protocol bump is
required merely to reject new publication.

An exact retry of a reply or close that committed a zero-byte body before this
fix must remain effectively-once and return `already_committed`; the fix must
not make an already-committed legacy disposition impossible to retry. A new
publication with the same empty input is rejected.

Multipart content is a separate protocol finding. When multipart is designed,
it must decide part-level emptiness explicitly rather than silently inheriting
or broadening this single-body rule.

## Required regression coverage

1. `send --body EMPTY_FILE` fails and publishes no row.
2. `send --body -` with empty stdin fails and publishes no row.
3. `reply` with empty file and empty stdin fails while its claim remains
   active and replyable.
4. `send-notice` with empty file and empty stdin fails without a notice or seen
   receipt.
5. `close --body` with empty input fails while bodyless `close` still succeeds.
6. Missing, unreadable, and non-regular body paths fail without mailbox
   mutation.
7. Store-level first-publication calls reject `b""` on every body-bearing
   path.
8. A one-byte body, binary content, and whitespace-only content remain valid.
9. Existing zero-byte messages remain deliverable and do not make `doctor`
   unhealthy.
10. Exact retries of legacy committed zero-byte reply/close dispositions remain
    idempotent.
11. Attachment publication and directed-message claim semantics are unchanged.
12. The standalone executable and distribution remain free of host-project
    assumptions.

## Clarification — ruled 2026-08-10, and it changes the shape of the fix

This finding was written as though rejecting a zero-byte body were purely a
subtraction. Measuring the protocol before implementing showed it is not:

    send        bodyless      REFUSED   "a message requires content"
    send        body=b""      ACCEPTED  -> 0-byte part, sha e3b0c442...
    send-notice bodyless      REFUSED   "a notice requires content"
    send-notice body=b""      ACCEPTED
    reply       bodyless      REFUSED   "reply requires content
                                         (a close is the contentless disposition)"
    close       bodyless      ACCEPTED  <- deliberate, unchanged
    close       body=b""      ACCEPTED  -> 0-byte part

So `close` is the ONLY contentless publication the protocol allows. Every
subject-only message on the live channel — including several carrying review
instructions — reached its recipient through the zero-byte loophole this
finding exists to close, because the deliberate path refuses a contentless
send. Rejecting empty bodies alone would therefore have removed a flow people
depend on, without anyone deciding to remove it.

The human-console decisions already require quick subject-only directed
messages and replies. Ruled: specify that honestly as a first-class
affordance rather than let it survive as a defect.

### The contract

- an explicitly supplied ZERO-BYTE body is refused on the body-bearing paths
  above; attachment behaviour is unchanged and outside this finding;
- a contentless directed `send` or `reply` is PERMITTED when, and only when,
  it carries a non-empty subject — the subject is then the message;
- `close` keeps its existing contentless disposition;
- notices are NOT included: subject-only notice publication stays refused. A
  broadcast has no recipient obligation to carry the meaning forward, and a
  TTL'd announcement whose whole content is a summary line is the case that
  most needs a body;
- the empty manifest/parts representation is pinned rather than left implicit,
  and `scan`, the console and `materialize` each state what a contentless
  directed publication looks like.

The distinction that makes this coherent: a zero-byte PART asserts that
content exists and is empty; a contentless message asserts that the subject is
the whole of it. The first is a lie the store told on the sender's behalf. The
second is something a sender can mean.

## Nested active finding

The complete decision history, CLI contract, compatibility rule, and evidence
for `--tweet` live in
`findings/finding-tweet-authoring/{FINDING,PLAN,PROGRESS}.md`. The parent owns the Store-level
empty-body/contentless distinction; the child owns how the CLI selects it.
