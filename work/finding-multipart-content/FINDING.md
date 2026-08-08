# Message content needs a multipart-capable envelope

Folder: `work/finding-multipart-content/`
Status: **superseded and implemented** by `work/finding-typed-content-envelope/`
at protocol 8 / tool 4.0.0.
Raised by: Slawomir during `work/finding-wait-notice-wakeup/`.

> This finding is kept as the origin of the requirement. The reviewer/team
> restated it in `work/finding-typed-content-envelope/FINDING.md` with the
> RFC references, the exactly-one-representation rule, and the demand that
> multipart readiness be real in storage as well as delivery. That folder
> carries the implementation and the handoff.
>
> Every acceptance criterion below is met, with one deliberate exception noted
> under "Not done yet".

## Problem

The current body representation models exactly one blob and can expose the
same text twice, as both UTF-8 and base64. That is awkward for humans and is
not a sufficient long-term content model for text, HTML, PDF, images, or other
media.

This is separate, versioned protocol work. It was explicitly excluded from
the `wait`/notice fix and must not be folded into that patch.

## Required direction

Start with the smallest forward-compatible example: represent an ordinary
text body as a multipart message containing exactly one inline UTF-8 text
part.

The model must then be able to carry additional text and binary media without
Baton having to interpret or render every type. Each part needs enough
metadata to identify and verify it, including:

- media type;
- content disposition;
- transfer encoding;
- integrity metadata;
- either inline content or a pinned attachment reference.

Text should be carried once as UTF-8. Binary content may use base64 or a
pinned attachment reference.

## Protocol constraints

This changes the delivery envelope and therefore requires a protocol version
bump rather than a patch release.

Directed messages and broadcast notices must migrate together. Today,
`_delivery` and `_notice_delivery` share the body representation, and the
notice shape shipped in 1.0.1 is
`{"notice": {..., "body": {...}}}`. Changing only one delivery path would
make `wait` and `see` disagree again—the same class of divergence fixed by
`work/finding-wait-notice-wakeup/`.

## Acceptance criteria

- The protocol defines a multipart-capable body envelope.
- The first supported example is one inline UTF-8 text part, without a
  duplicate base64 copy.
- Every part has explicit media type, disposition, encoding, and integrity
  metadata.
- Binary and externally stored parts have an unambiguous representation.
- Directed delivery, notice delivery, `wait`, and `see` expose the same body
  model where applicable.
- Compatibility and migration behavior are documented and regression-tested.
- The standalone distribution is rebuilt and contains no host-project or
  Drift-specific assumptions.

## Not done yet

**All criteria are now met.** The last outstanding one -- *"Binary and
externally stored parts have an unambiguous representation"* -- was closed at
protocol 9 by `work/finding-attachment-part-convergence/`: an externally
stored part is a `parts` row with a declared media type, disposition,
filename, order and hash, covered by the same manifest as inline content.

Compatibility policy was decided rather than deferred: there is no migration
and no compatibility shim. Protocol 8 had never existed on disk when this
landed, so the typed envelope defines the released protocol-8 schema and the
deployment takes one teardown rather than two.
