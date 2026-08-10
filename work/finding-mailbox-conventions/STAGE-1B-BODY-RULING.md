# Ruling — body composition with multipart authoring

**Decision (Slawomir, 2026-08-09): approved as recommended.**

Stage 1B currently accepts `--body` together with `--references`, reports
success, and silently drops the body. The packaged reproduction delivered
only the references part. We need to pin the intended composition contract
before K corrects the integration.

## Reviewer recommendation

Keep the useful historical composition while making general parts explicit:

- `--body` may accompany `--references` and legacy `--attach`;
- the body is the first leaf, preserving the historical body-plus-attachment
  order;
- `--content-type`, `--disposition`, and the legacy advisory-name option apply
  to that body;
- `--body` is mutually exclusive with general `--part`, because every
  `--part` already carries its own source and metadata;
- if any explicit content source is supplied, an omitted `--body` must not
  implicitly consume stdin;
- at most one source across body, parts, and references may consume stdin;
- every invalid combination fails before any input is read.

This makes the common message-plus-references case concise without creating
two ways to describe a fully general ordered multipart message.

## Simpler alternative

Make `--body` mutually exclusive with `--part`, `--references`, and
`--attach`. This is safe and easier to explain, but makes the common
body-plus-references case needlessly verbose and breaks the existing
body-plus-attachment authoring surface.

The recommended contract above is authoritative for Stage 1B. Silently
discarding authored content is forbidden.
