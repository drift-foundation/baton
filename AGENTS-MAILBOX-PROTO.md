# Baton agent mailbox protocol — v9

An agent coordination channel running **Baton protocol 9** has one SQLite
transactional authority per instance, no filename-state, and is defined
entirely by an explicit config. Consult the Baton distribution's `README.md`
for the command and storage contract.

## Instance selection

    BATON_BIN=/absolute/path/to/baton
    BATON_CONFIG=/absolute/path/to/instance/baton.json
    "$BATON_BIN" --config "$BATON_CONFIG" <command> ...

The config and SQLite authority live outside every participating product
tree. Never copy them into a repository, infer a config from the current
working directory, or omit `--config`. The local deployment supplies the
executable and explicit absolute config path; participating project policy
binds local roles to participant identities without hard-coding host paths.

Participant addresses are `<domain>.<role>`. A domain is a coordination
namespace, not necessarily a Git repository, and roles are open-ended. Each
project binds role-only instructions to concrete addresses in its own policy.

Never consume or claim through another domain's participant, even if a
message looks relevant. Cross-domain work must name the intended scoped
address.

Every identity-bearing invocation passes `--participant <address>`. The
participant address IS the identity: there is no actor and no seed. Filesystem
access to the instance is the trust boundary, so this is cooperative
coordination between trusted agents, not application-level authentication.

Run exactly ONE consumer path per participant — never two concurrent `wait`s
for the same address. If two consumers are genuinely needed, give them
distinct participant addresses rather than sharing one identity.

## Working the channel

- Give every substantive message a `--subject`: one line of plain text, at
  most 255 bytes, no control characters. It is what an inbox lists before
  anything is opened, and `scan` shows it. `reply` inherits the subject it
  answers unless you pass your own; retries must repeat the EFFECTIVE subject.
  Status pings may omit it and fall back to `kind`.
- Consume with `wait` (blocking) or `claim`; both return the lossless
  delivery (claim + envelope + body/attachment). Process a claim
  immediately: `reply` (publishes the response and completes the claim in
  one transaction) or `close` (terminal disposition). Retries are
  effectively-once: an exact retry reports `already_committed`, any
  mismatch fails closed.
- Durable review/response documents: bodies live IN the store; use
  `materialize --dir <finding folder> --prefix review|implementation-response`
  to emit the byte-exact projection for humans. Add `--part N` to address a
  specific part of a multipart message (default `0`). Projections are
  caches; the store is the authority.
- Content is TYPED. Every delivery carries `content` with a `content_type`
  and an ordered `parts` list, even for a single part. Each leaf states its
  media type, `disposition`, optional advisory `filename`, size and hash, and
  carries exactly one representation named by `encoding` — `text` for
  `text/...; charset=utf-8`, `base64` otherwise, never both. Declare
  `--content-type` when publishing anything that is not Markdown; the default
  is `text/markdown; charset=utf-8` and a `text/*` type must state its
  charset. Bytes that contradict the declared charset are refused at
  publication. Baton transports content and never renders it.
- Retries must repeat the WHOLE manifest: the same parts, in the same order,
  with the same media types, dispositions and filenames. Identical bytes under
  changed metadata are a different operation and fail closed.
- Evidence files already in the tree travel as EXTERNAL PARTS:
  `--attach ROOT:relative/path` (hash-pinned at publication; mutation fails
  the claim). An external part is an ordinary part — typed, ordered, covered
  by the retry manifest — so it may sit BESIDE an inline `--body` in the same
  message, and a message may carry several. Send the explanation and its
  evidence together rather than as two messages.
- Broadcasts: `send-notice` (finite TTL); consume with `see`, or receive
  them on the blocking `wait` path — a notice wakes a waiter and is
  delivered as `{"notice": ...}` rather than the directed
  `{"claim": ..., "message": ...}`. A directed message always wins when both
  are available. Notices are never claimed, so there is nothing to `reply`
  or `close`; the seen receipt commits with the read, which makes broadcast
  at-most-once per participant. Directed messages remain the durable
  channel for anything that must not be missed. Authors may `expire` early.
- Never mutate the database with raw SQL; every table is guarded and
  doctor treats bypasses as corruption. `doctor`/`scan`/`dump`/`inspect`
  are the read-only views.

## Retention

Transient messages lose their bytes when consumed (identity/hashes
remain); durable messages are permanent. `gc` (any participant) collects
aged transient metadata per `retention_days`; the transition ledger and
audit tables are permanent.

Config changes use Baton's audited `regen` ceremony and require a participant
with the `config` capability; direct config/database edits are forbidden.
Finding-folder workflow policy and concrete deployment identities belong in
the participating project's policy, not in this protocol.
