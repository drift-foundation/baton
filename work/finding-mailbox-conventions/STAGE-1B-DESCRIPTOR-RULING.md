# Stage 1B part descriptor — ruled

Slawomir ruled: use URL-query-style named fields with URL percent encoding.
Do not use positional colon suffixes. Do not base64-wrap JSON.

The flat Stage 1B spelling is one query descriptor per repeated part:

```text
--part 'source=report.pdf&type=application/pdf&disposition=attachment&name=Q3-report.pdf'
--part 'source=notes.md&type=text/markdown;%20charset=utf-8'
```

Contract:

- known keys are `source`, `type`, `disposition`, and `name`;
- `source` and `type` are required and non-empty;
- `disposition` defaults to `inline`; `name` is optional;
- reject duplicate keys, unknown keys, missing required keys, malformed `%`
  escapes, and empty values where not permitted;
- split a pair at its first `=` and preserve decoded values exactly;
- field order inside one descriptor has no meaning;
- repeated `--part` occurrences, interleaved with `--attach` and
  `--references`, define total leaf order;
- use RFC 3986 percent encoding: spaces are `%20`; `+` remains a literal plus
  rather than HTML-form space, so `application/ld+json` is not corrupted;
- diagnostics identify the offending part occurrence and field without
  echoing arbitrary payload bytes.

The CLI flag already establishes that this is a part descriptor, so no
`file:` or invented URI scheme is implied. The query fields describe a local
source to read and the metadata of the resulting inline leaf; they are not a
network locator.

Implementation constraints, pinned because the obvious standard-library
shortcuts have lossy defaults:

- do **not** use `urllib.parse.parse_qsl` or `unquote_plus`; both apply HTML
  form semantics and turn literal `+` into a space;
- split the raw descriptor on `&`, then each non-empty field at its first
  `=`; percent-decode keys and values only after that structural split;
- validate every `%` escape before decoding, then decode percent bytes as
  strict UTF-8 (no replacement characters);
- detect duplicates after key decoding, so `type` and `%74ype` cannot evade
  the duplicate check;
- an omitted optional key differs from a present empty value; empty values are
  refused rather than silently dropped.

Common media types remain readable. RFC 3986 does not require `/`, `;`, `=`,
or literal `+` in these query values to be percent encoded; the space in a
parameter is `%20`. Characters with structural meaning here, especially `&`
and `%`, remain percent-encodable in source paths and names.

JSON may be reconsidered later only for an explicit descriptor/spec-file
surface if nested multipart authoring gains a concrete CLI use case. Base64
adds no value to argv transport and is not part of this surface.
