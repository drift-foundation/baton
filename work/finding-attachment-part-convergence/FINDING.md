# Attachments and parts are two models for one idea

Folder: `work/finding-attachment-part-convergence/`
Status: **implemented** at protocol 9 / tool 5.1.0; see `IMPLEMENTATION.md`
in this folder. **Deployed 2026-08-07**: the protocol-8 authority was retired
intact and protocol 9 is live.
Raised by the implementer while closing
`work/finding-typed-content-envelope/`, 2026-08-07.

## Why this exists

`work/finding-typed-content-envelope/FINDING.md` listed as an open question:

> How this interacts with the existing pinned-attachment mechanism: an
> attachment is already a typed, external, hash-pinned part, and the two
> concepts should converge rather than coexist unexplained.

The typed-content-envelope implementation **explained** the relationship but
did **not** converge the two. This finding records the remaining gap, so the
explanation does not quietly become the permanent answer.

## The two models today

Protocol 8 has two ways to attach bytes to a message, and they share nothing:

**Inline parts** live in the `parts` table. They are an ordered tree, each leaf
carrying `content_type`, `disposition`, optional `filename`, `size` and
`sha256`, with the bytes in `contents`. A message may have any number, nested
to any depth. Their collective identity is `messages.manifest_sha256`.

**Pinned attachments** live in five columns on `messages` — `attach_root_id`,
`attach_path`, `attach_sha256`, `attach_size`, `attach_generation`. The bytes
stay in the filesystem under a configured root. A message may have **exactly
one**, and a `CHECK` constraint makes content and attachment mutually
exclusive. An attachment has no declared media type, no disposition, and no
filename field distinct from its path.

So a message may carry N typed inline parts, or one untyped external one, and
never both.

## Why that is wrong

An attachment already *is* a part: external storage, hash-pinned, with size and
integrity metadata. The only real differences are where the bytes live and that
the pin is verified at claim time. Everything else — ordering, typing,
disposition, count, and the manifest that gives retries their identity — was
built once for inline parts and simply does not exist for attachments.

The costs are concrete, not aesthetic:

- **An attachment carries no media type.** The whole point of the typed
  envelope is that a consumer can dispatch on a declared type. An attached PDF
  and an attached PNG are indistinguishable to a consumer without sniffing the
  bytes, which is exactly what the envelope was built to stop.
- **A message cannot carry a note beside its evidence.** The mutual-exclusion
  `CHECK` forces a choice between "here is the file" and "here is what it
  means". The documented workaround — send the explanation as a separate
  message — puts two halves of one statement on a queue that may interleave
  them.
- **Only one attachment per message**, for no reason that survives the parts
  table existing.
- **Attachments are outside the manifest.** `manifest_sha256` covers the
  ordered inline manifest; the attachment tuple is checked separately. Retry
  identity therefore has two mechanisms where it should have one.
- **Two damage paths.** `verify_attachment`, the skip-and-continue logic in
  `_first_deliverable`, and the whole `quarantine-attachment` ceremony exist
  for external bytes. Inline parts have `_read_parts` and the manifest check.
  Both are correct; neither knows about the other.

## Required direction

An attachment becomes a **part with external storage**: a `parts` row whose
bytes are referenced rather than embedded, carrying the same `content_type`,
`disposition`, `filename`, `ordinal`, `size` and `sha256` as any other leaf,
plus the root binding and generation it needs to be re-verified.

That collapses two models to one and removes the mutual-exclusion `CHECK`: a
message becomes an ordered manifest of parts, each either inline or external.

## Acceptance criteria

- A `parts` row expresses external storage; `messages` carries no `attach_*`
  column.
- An external part declares a media type, disposition and filename like any
  other part.
- A message may carry inline and external parts together, in a defined order,
  and more than one of each.
- `manifest_sha256` covers external parts, so retry identity is ONE mechanism.
- Claim-time pin verification, `_first_deliverable` skip-and-continue,
  `scan --damaged`, `doctor`, and `quarantine-attachment` all operate on parts
  and keep their current behaviour. **Damaged content is still never
  delivered, and one damaged message still must not block the queue behind
  it** — that was `work/finding-damaged-attachment-queue/` and it must not
  regress.
- Quarantine records the damaged part, not the message's single attachment
  tuple.
- Regressions for each of the above, plus one proving a message can carry an
  inline explanation and an external evidence file at once.

## Protocol constraints

This changes `messages`, `parts`, and `quarantines`, so it is a **protocol
bump** and — under `work/finding-live-first-mailbox-upgrade/` — another
fresh-authority release with another teardown.

**That is the reason it was deferred rather than folded into the typed content
envelope.** The envelope had to ship inside protocol 8 because protocol 8 had
not yet been deployed; riding along was free. This work does not have that
window: by the time it starts, the protocol-8 authority is live. It should
therefore be batched with whatever other protocol-breaking work is pending, and
not taken alone.

## Not decided here

Whether an external part's bytes may be *copied* into `contents` at
publication (making the pin an integrity check rather than a storage
strategy), and whether `--attach` keeps its current spelling once a message
can hold several.
