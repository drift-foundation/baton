# Part identity is a name, not a filename

Folder: `work/finding-part-name-semantics/`
Status: approved for protocol 10, but parked until `baton` has first adopted
`baton-core` and that protocol-9 consolidation has been reviewed and landed.

Raised by Slawomir during the `baton-tui` trial on 2026-08-08.

## Problem

Protocol 9 calls a leaf's optional human label `filename`. That gives a MIME
part filesystem semantics it does not have. The sender names a part; the
recipient decides whether it is displayed, transformed, ignored, or saved,
and if saved, under which filename and path.

An image named `architecture diagram` is still a named image part when it is
never materialized. Conversely, materializing it does not authorize the
sender to choose a path in the recipient's filesystem.

## Pinned direction

- The protocol concept and wire field are **part name** and `part_name`, not
  filename and not `filename`.
- `part_name` is optional advisory metadata on a leaf. It is immutable,
  delivered losslessly, and participates in the manifest/retry identity just
  as the current label does.
- A part name has no path semantics. It is never interpreted as absolute or
  relative path syntax, never selects a directory, and never authorizes a
  write.
- The recipient owns materialization. A console may offer the part name as a
  naming suggestion, but the eventual output path is chosen or safely
  generated on the recipient side. Unsafe or unusable suggestions are
  replaced; the original part name remains visible as message metadata.
- The TUI says **part name** and displays it on the part header. It does not
  expose the old protocol term as user-facing vocabulary while protocol 9 is
  still live.
- MIME serialization, if added later, may map a part name to a format-specific
  filename parameter at that boundary. That does not make the Baton protocol
  field a filename.

## Version and sequencing

This changes the schema, delivery JSON, manifest identity, CLI/API vocabulary,
documentation, dumps, and retry comparison. It therefore requires a protocol
bump; it is not a tool-only rename.

Slawomir approved the rename but pinned three separate landed stages. First,
finish, review, and commit the current protocol-9 TUI plus `baton-core` work
with the existing CLI untouched. Second, start a NEW work folder and branch,
move the CLI onto `baton-core` while remaining on protocol 9, prove parity
against the frozen implementation, and land that consolidation separately.
For now every executable and authority remains protocol 9 and the rename is
parked. Only after the shared core is the landed CLI implementation does a
third stage replace `filename` once in protocol 10.

Protocol 10 must contain `part_name` only; do not accept, emit, or retain a
compatibility `filename` field in its live schema or public surface.

Keep the existing protocol-9 executable and authority running solely as the
coordination channel while protocol 10 is implemented and reviewed. Do not
mutate or cut over the live instance during development. After approval,
retire it intact and initialize a fresh protocol-10 authority first so
communications return before any optional history work.

## Acceptance evidence

- Schema, public API, CLI flags, delivery JSON, dumps, documentation, and
  examples contain `part_name` and no live `filename` field or option.
- Inline, external, text, binary, nested multipart, and unnamed leaves round
  trip their names without acquiring path semantics.
- Retry identity rejects a changed part name and accepts an unchanged one.
- Hostile names cannot escape a projection directory or become terminal
  control sequences.
- Materializing an unnamed part and a maliciously named part uses safe
  recipient-controlled output naming; the original metadata is not rewritten.
- Standalone distribution and protocol documentation remain free of
  host-project assumptions.
