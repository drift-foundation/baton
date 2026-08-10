# Explicit subject-only authoring with `--tweet`

Status: **ruled; implementation ready for final review**.

Parent: `work/finding-nonempty-message-bodies/`.

Discovery context: review proved the Store's new contentless representation
was unreachable through `bin/baton`, because omitted body still selected
implicit stdin and empty stdin became a refused zero-byte body.

## Why this is a separate finding

The parent finding rejects explicitly supplied zero-byte bodies. People also
intentionally send short directed messages whose subject is the entire
message. Before the correction, those messages reached the store only by
presenting an empty body, so closing the defect without a deliberate authoring
surface would remove a relied-on flow.

This finding is the CLI contract that selects the Store's contentless
representation intentionally. It changes authoring only; it is not a protocol
kind, schema change, or lifecycle change.

## Decision history

1. Omitted `--body` meaning “no body” was proposed and not accepted because
   ordinary `send` and `reply` already default to stdin.
2. `--subject-only --subject TEXT` was rejected as too much ceremony.
3. Slawomir chose `--tweet TEXT`.
4. `--tweet -` was chosen over `--tweet ""` for stdin. `-` is Baton's existing
   explicit convention and keeps the empty string invalid.

## Required contract

    baton send ... --tweet "Still testing; give me more time"
    baton reply CLAIM ... --tweet "Approved"
    baton send ... --tweet -

- The tweet value is the publication subject. The publication contains no
  parts and uses the parent's pinned contentless representation.
- The caller's kind, outcome, retention, audience, claim, reply, close, retry,
  and thread semantics remain ordinary directed-message semantics. `tweet` is
  authoring vocabulary, never a stored protocol kind.
- `--tweet -` reads stdin as UTF-8, removes exactly one terminal LF or CRLF,
  and passes the result through the ordinary subject validator.
- Empty input/value, more than one line, embedded controls, invalid UTF-8,
  excessive length, and existing edge-whitespace violations fail before
  publication.
- `--tweet` is mutually exclusive in both directions with `--subject`,
  `--body`, `--part`, `--references`, `--attach`, `--content-type`,
  `--disposition`, and `--part-name`. No input is silently ignored.
- Send/reply without `--tweet` preserve implicit stdin. Explicit body stdin or
  file input still requires at least one byte.
- Notices do not gain `--tweet`; the TUI may select the same Store
  representation automatically for a non-empty subject with no body.

## Required evidence

1. Direct and packaged CLI tests for inline tweet send/reply.
2. Packaged stdin tests ending in LF and CRLF.
3. Every validation refusal with no publication.
4. Every mutual exclusion in both argument orders.
5. Preserved ordinary implicit stdin and unchanged notice refusal.
6. Dump/delivery evidence that subject/kind/empty parts are correct.
7. Help/README examples, deterministic standalone builds, and no host-project
   assumptions.
