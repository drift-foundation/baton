# Stage 1B part-descriptor alternatives — exploratory, not ruled

Slawomir asked that two standard encodings be evaluated before freezing the
repeatable `--part` parser.

## A. URI-query descriptor

One argument per part, using `&`/`=` fields and RFC 3986 percent encoding:

```text
--part 'source=report.pdf&type=application/pdf&disposition=attachment&name=Q3-report.pdf'
--part 'source=notes.md&type=text/markdown%3B%20charset%3Dutf-8'
```

The repeated `--part` occurrence still defines leaf order; field order inside
one descriptor does not. Parse only known keys, reject duplicates and unknown
keys, require `source` and `type`, and split pairs at the first `=`. Specify
that `+` is literal and spaces use `%20` (URI query semantics, not HTML form
`+`-as-space semantics), so media types such as `application/ld+json` are not
a footgun.

Advantages: one shell token per part, standard escaping for `&`, `=`, `%`,
spaces and other delimiters, self-describing fields, extensible without empty
positional placeholders.

Costs: hand-authored percent encoding is less readable; URI query key/value
conventions still require an exact local contract for duplicate keys, unknown
keys, blank values and `+`; the descriptor names a local source rather than a
network resource, so no `file:` URI semantics should be implied.

## B. JSON descriptor

JSON can carry the same object directly:

```text
--part '{"source":"report.pdf","type":"application/pdf","disposition":"attachment","name":"Q3-report.pdf"}'
```

This is typed, self-describing, extensible, and could eventually describe
nested multipart trees. Reject duplicate keys and unknown fields rather than
letting a generic JSON decoder silently overwrite them.

Raw JSON requires shell quoting, but the shell already transports it safely
as one argument. A descriptor-file form could cover large or generated
structures later.

### JSON wrapped in base64

Not recommended unless a concrete transport limitation is demonstrated. CLI
argv already carries quoted UTF-8 text, so base64 hides the command from the
human, prevents useful completion/inspection, requires a separate encoding
step, introduces standard-vs-URL-safe and padding choices, and makes mistakes
harder to diagnose. It protects neither secrecy nor integrity.

## Reviewer’s current preference

For the flat Stage 1B surface, URI-query form is the strongest single-token
candidate. JSON is better reserved for a future explicit descriptor/spec-file
surface if nested trees acquire a real CLI use case. Do not implement either
until K has checked parsing, diagnostics, compatibility, and test implications
and Slawomir rules.
