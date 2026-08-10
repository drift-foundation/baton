# Stage 1B convention ruling requested

**Refined by Slawomir on 2026-08-09:** references are root-qualified logical
addresses, `ROOT_ID:RELATIVE/POSIX/PATH`, rather than paths relative to an
unspecified repository. See `STAGE-1B-REFERENCE-ADDRESS-RULING.md`.

The mailbox document deliberately calls file-reference paths a recommended,
optional convention. The new `--references` convenience currently refuses
absolute paths, `..`, home expansion, host-specific roots, malformed POSIX
paths, and empty content.

Recommended ruling: keep the convention optional, but state that the
`--references` convenience validates and enforces the recommended portable
shape. A sender who deliberately wants an unchecked references-typed leaf can
still use the general `--part` authoring surface. This keeps a convention from
becoming wire protocol while making the convenience useful rather than merely
an alias.

Also replace the `Current authoring gap` paragraph when Stage 1B lands; it will
otherwise immediately become false.

Alternative: make the path restrictions normative. This is not recommended
because it would make the generic mailbox-use document define behavior of one
CLI convenience and blur the document's explicit convention/protocol
boundary.

Decision requested from Slawomir: approve the recommended optional-convention,
strict-convenience model, or direct that the path rules become normative.
