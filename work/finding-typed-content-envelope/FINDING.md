# Message content needs a typed, multipart-capable envelope

Folder: `work/finding-typed-content-envelope/`
Status: **implemented** at protocol 8 / tool 4.0.0 and shipped in the live
protocol-9 release; see `IMPLEMENTATION.md`
in this folder. Supersedes `work/finding-multipart-content/`. The one open
question left unclosed — attachment convergence — is recorded as
`work/finding-attachment-part-convergence/`.
Raised by the reviewer/team, relayed by Slawomir, 2026-08-07.

## Sequencing — the reason this is pinned now rather than later

This must land **after** `work/finding-seed-credential-boundary/` and
**before** the fresh authority is initialized, so both breaking changes ship in
**one** new protocol version.

That is the whole point of the timing. The seedless-identity work already
bumps the protocol and ends in a fresh-authority release. If the content
envelope followed the new mailbox, it would need a second protocol bump and a
second teardown within days. Riding along costs nothing extra; arriving late
costs another cutover.

It must not widen the seed-removal implementation in flight. Pin now,
implement immediately after that handoff, initialize the new authority only
once both are in.

## Problem

The current body representation models exactly one blob, carries no type
information, and duplicates the same bytes as both `utf8` and `base64`. A
consumer cannot tell Markdown from plain text from HTML, and a human-facing
console has nothing to dispatch rendering on.

## Envelope

Standard terminology, not invented vocabulary.

**`content_type`** — an IANA media type with parameters, e.g.
`text/markdown; charset=utf-8`, `text/plain; charset=utf-8`,
`text/html; charset=utf-8`. Markdown's registered type is `text/markdown` and
its `charset` parameter is **required** — RFC 7763,
<https://www.rfc-editor.org/rfc/rfc7763.html>.

**`disposition`** — `inline` or `attachment`, with an optional `filename` —
RFC 2183, <https://www.rfc-editor.org/rfc/rfc2183.html>.

The key rule:

    {
      "content_type": "text/markdown; charset=utf-8",
      "disposition": "inline",
      "size": 123,
      "sha256": "...",
      "text": "# Hello\n"
    }

For binary content, replace `text` with `base64`. **Never emit both.** Raw
bytes are stored and hashed exactly once.

Consequences:

- Markdown, plain text and HTML travel as ordinary JSON strings.
- PDFs and images use `base64` only when embedded in JSON.
- A future console may materialize binary parts to disk instead of displaying
  base64.
- **Baton core transports content and never renders it** — no HTML, no
  Markdown. Rendering is a consumer concern, and a transport that renders is a
  transport with an injection surface.
- Directed messages and notices use the **same** content representation. They
  diverged once already; see `work/finding-wait-notice-wakeup/`.

## Multipart readiness must be real, in storage as well as delivery

**Not merely wrapping today's single body in an array.** An envelope that
looks multipart over a storage layer that still assumes one blob buys nothing
— the second part is still a schema change, which is the cost this finding
exists to avoid paying twice.

Required:

- **Every message has an ordered parts collection from protocol inception.**
  Not optional, not added when a second part first appears.
- **Each leaf part carries** `content_type`, `disposition`, optional
  `filename`, `size`, the raw-byte hash, and **exactly one** delivery
  representation — `text` or `base64`, never both.
- **The database stores part order and metadata independently of the message
  row.** Parts are their own records with an explicit ordering, not columns on
  `messages` and not a serialized blob.
- **Retry identity covers the complete ordered part manifest, including
  metadata** — not only body bytes. Today `_verify_retry` compares a single
  content hash; under multipart, two retries that differ in part order,
  `content_type`, `disposition` or `filename` are different operations even
  when every byte matches, and must fail closed as mismatches.
- **`materialize` addresses a specific part**, e.g. `--part 0`.
- **The first implementation may require exactly one leaf part, but readers
  must accept the multipart envelope.** Writers may be restricted; readers may
  not assume the restriction.
- **Container semantics must accommodate `multipart/mixed`,
  `multipart/alternative`, and later nested multipart structures without a
  schema change.**

The shape:

    {
      "content_type": "multipart/mixed",
      "parts": [
        {
          "content_type": "text/markdown; charset=utf-8",
          "disposition": "inline",
          "size": 8,
          "sha256": "...",
          "text": "# Hello\n"
        }
      ]
    }

Adding `text/plain` and `text/html` alternatives, or PDF and image
attachments, then becomes a **capability extension rather than another
protocol redesign** — which is the entire test of whether this was done
properly.

## Open questions for the implementation

- Where multipart alternatives are expressed — a nested part list, or a
  sibling relationship with an explicit preference order.
- Whether `filename` is advisory only, and what a consumer is permitted to do
  with it (path traversal is the obvious hazard).
- How this interacts with the existing pinned-attachment mechanism: an
  attachment is already a typed, external, hash-pinned part, and the two
  concepts should converge rather than coexist unexplained.
- What `content_type` a body sent with no declared type defaults to, and
  whether an undeclared type is rejected instead.
- Size limits per part versus per message.

## Not decided here

No rendering, no content negotiation, no transformation. Baton moves bytes and
describes them accurately; everything else belongs to consumers.
