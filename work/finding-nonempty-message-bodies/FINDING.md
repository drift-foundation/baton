# Explicit message bodies may be empty

Status: **confirmed; not started**.

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

