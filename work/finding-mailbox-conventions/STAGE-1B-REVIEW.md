# Stage 1B review — changes requested

The URL-query parser and ordered general-part builder are sound, but the
four-verb integration is not release-ready. The first item is data loss and
must be corrected before anything else.

## R1 — `--body` is silently discarded in part mode

`_authored_parts()` enters part mode whenever `--part` or `--references` is
present. Every verb then passes `body=None`, regardless of whether the caller
explicitly supplied `--body`.

Reproduced through the packaged executable:

```text
baton send ... --body body.md --references refs.txt
```

The command returned success. The claimed delivery contained only the
references leaf; the bytes `BODY MUST SURVIVE` were absent. This is a
successful command silently dropping authored content.

Do not merely add a test for the current behavior. The recommended contract
is: `--body` may accompany `--references` and legacy `--attach`, remains the
first leaf as it historically was with body+attachment, and its legacy
`--content-type`/`--disposition`/`--filename` metadata applies to that body.
`--body` remains mutually exclusive with general `--part`, which already has
its own per-leaf metadata and ordering.

If Slawomir instead chooses strict mutual exclusion, every mixed invocation
must fail before reading input. It must never succeed by ignoring a field.

Likewise, legacy content metadata must never be ignored in parts mode: apply
it to an accompanying body or refuse it when there is no body. Pin every verb
and stdin-collision behavior before any bytes are read.

## R2 — `close` advertises an unusable external attachment

`close` calls `authoring_opts(c)` and therefore exposes `--attach`, even though
external parts are forbidden on dispositions and never deliverable. Use
`attach=False` for `close`, just as for `send-notice`, and pin the packaged
help/parser refusal. Inline `--part ...&disposition=attachment` remains valid;
this finding concerns external storage.

## R3 — the parser is not enforcing the ruled RFC 3986 spelling

The ruling says spaces are `%20`, literal `+` stays plus, and percent-decoded
UTF-8 is strict. The parser and public examples currently accept raw spaces
and raw non-ASCII characters:

```text
type=text/markdown; charset=utf-8
source=notes-é.md
```

Those are not URL-encoded query values. Require the raw descriptor to use the
RFC 3986 query character set: no raw whitespace/control or non-ASCII bytes;
UTF-8 non-ASCII travels through percent encoding. Keep readable `/`, `;`,
`=`, and literal `+` where RFC 3986 permits them. Update examples to use
`text/markdown;%20charset=utf-8` and add packaged refusal/acceptance pins.

## R4 — invalid UTF-8 references produce a traceback

`_authored_parts()` decodes a references file with a bare
`.decode("utf-8")`; `main()` catches `BatonError`, not `UnicodeDecodeError`.
Translate invalid reference UTF-8 to a stable `BatonError` naming the
`--references` occurrence/file without echoing bytes, and pin the packaged
CLI diagnostic for all four verbs.

## R5 — the standard test recipe omits all 65 new focused tests

`just test` enumerates test files explicitly but does not include
`test_core_authoring.py` or `test_core_references.py`. The reported 1952-test
"full suite" therefore did not run the new focused regressions. Add both to
the `justfile`, run the standard recipe, and report its real total.

## R6 — this is tool 5.2.0, not 5.1.0

Four public CLI verbs gained new repeatable options and grammar. Bump the core
CLI tool version to 5.2.0 while protocol remains 9 and the frozen oracle stays
5.1.0. Update the parity/version assertion to record that intentional tool
version split without weakening protocol or behavioral parity. Rebuild all
affected CLI distribution pins deterministically.

## R7 — README and current contract text are stale

README still says the CLI can publish at most one inline plus one external
part. Replace that with the released `--part`/`--references` surface and one
practical multipart example. Keep the normative mailbox convention in
`AGENTS-MAILBOX-PROTO.md`; README documents how humans and agents invoke the
tool rather than duplicating the convention.

The protocol document's convention preamble currently says anything Baton
enforces is not a convention, while the new paragraph says the CLI enforces
the strict convenience. Resolve this with Slawomir's still-pending ruling and
make the preamble and section agree.

## R8 — record the discovered default-type defect in the protocol-10 bundle

The finding and explicit CLI stopgap are appropriate. Add the real
`normalize_parts` correction to the protocol-10 umbrella so it cannot be lost
during the planned bundle. Correct the finding's dangerous wording: the
frozen oracle must not be edited to make parity pass. Protocol 10 either
retires that oracle or records the deliberate core divergence; it never moves
the reference alongside the behavior being measured.

Also refuse Windows drive-root references such as `C:/repo/file` (and the
drive-relative spelling) while still allowing ordinary POSIX colons, because
the documented convention explicitly excludes host-specific roots.

## Verification already completed

- parser/reference focused suite before integration: 65 passed;
- packaged data-loss reproduction: confirmed;
- `close --help`: incorrectly exposes external `--attach`;
- raw-space and raw-non-ASCII descriptors: currently accepted;
- `git diff --check`: clean.

Continue with these corrections. A full suite is needed only after the
standard recipe includes the new tests and the candidate is otherwise ready.
