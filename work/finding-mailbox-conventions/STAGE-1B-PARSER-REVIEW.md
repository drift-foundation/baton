# Stage 1B URI-query parser review — changes requested

The overall parser shape matches the ruling, and the focused 52-test suite
passes. Two required lossless-decoding properties are absent, plus one
surface validation should be pinned before verb wiring.

## 1. Values are not decoded as strict UTF-8

`urllib.parse.unquote(raw)` defaults to `errors="replace"`. A descriptor such
as `source=%FF&type=text/plain` therefore silently becomes a source containing
U+FFFD instead of being refused. The ruling requires strict UTF-8 and no
replacement characters.

Decode with `unquote_to_bytes`, then `.decode("utf-8", "strict")`; translate
`UnicodeDecodeError` into a `BatonError` naming the occurrence/field without
echoing the value. Pin at least an invalid lead byte and an invalid continuation
sequence.

## 2. Keys are rewritten, not percent-decoded

The implementation does `key.strip()` and never percent-decodes the key. That
both silently accepts whitespace around a field name and lets an encoded
duplicate evade the post-decode duplicate rule:

```text
source=a&type=text/plain&%74ype=application/pdf
```

Validate percent escapes and strict UTF-8 for keys as well as values, do not
strip them, check membership and duplicates after decoding, and pin encoded
duplicate, invalid key UTF-8, and surrounding-key-whitespace refusals.

## 3. Validate `disposition` at the parser boundary

The public surface has two allowed values, `inline` and `attachment`. Refuse
any other value as a `--part` field error rather than relying on a later store
normalizer to diagnose it out of context. Pin both allowed values and one
refusal.

The final CLI-level tests must also prove repeated-part diagnostics identify
the offending occurrence, not only the field. No full suite is needed for
these parser corrections.

## Revision check

Strict value decoding and duplicate detection after decoded keys are fixed and
the focused 55 tests pass. Two requested items remain:

- `raw_key.strip()` still silently accepts ` source=a.md` as `source=a.md`.
  Remove the strip and pin surrounding raw key whitespace plus invalid UTF-8
  in a key. The decoded-key duplicate pin is good.
- `parse_part("source=a&type=a/b&disposition=bogus")` still returns `bogus`.
  Refuse values outside `inline`/`attachment` in the parser and pin both valid
  values plus the refusal.

The repeated-occurrence diagnostic remains due with the four-verb CLI wiring.

## Final parser verification

All remaining items are closed. `unquote(..., errors="strict")` is equivalent
to the explicit two-step decoder for the pinned invalid lead, continuation,
and truncated multibyte cases; no spelling-only churn is required. Raw and
encoded key whitespace are refused without repair, decoded duplicates are
caught, disposition is validated locally, and the builder supplies `--part
#N` occurrence context. Focused verification passes 63/63 and
`git diff --check` is clean.

Parser layer approved. Proceed to symmetric wiring of `send`, `send-notice`,
`reply`, and `close`, including packaged-CLI tests and the protocol-document
authoring-gap correction.
