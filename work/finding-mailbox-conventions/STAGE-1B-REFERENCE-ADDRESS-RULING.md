# Ruling — references use root-qualified logical addresses

**Decision (Slawomir, 2026-08-09):** a reference is not a bare path relative
to an unspecified repository. Each line uses the same logical address shape
as an external attachment:

```text
ROOT_ID:RELATIVE/POSIX/PATH
```

For example:

```text
source:baton_core/_impl.py
source:work/finding-mailbox-conventions/FINDING.md
```

This is necessary because one Baton authority may coordinate several
repositories. A bare `README.md` does not say which repository owns it.

Address alignment does not collapse the semantic distinction:

- an external attachment resolves the configured root, reads the file, pins
  its bytes and metadata, and may later fail verification;
- a reference carries navigational metadata only. It does not read, stat,
  hash, pin, or require the referenced path to exist.

The strict `--references` convenience validates the root identifier against
the authority's configured roots and validates only the relative POSIX path
shape. The general `--part` surface remains capable of publishing an
unchecked references-typed leaf; therefore using the convention remains
optional rather than becoming a wire-protocol requirement.

The root identifier is not a Windows drive letter. It follows Baton's root-ID
grammar and names the logical repository/root shared by participants. The
relative path retains the existing portability checks: no leading `/`, `..`,
`~`, backslash separators, empty components, or edge whitespace. File
existence is deliberately not checked.
