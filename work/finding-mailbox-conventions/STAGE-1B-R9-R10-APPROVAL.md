# Stage 1B R9/R10 re-review — approved

The `reply --attach` correction and four-verb invalid-references regression
are approved.

Independent checks:

- `reply` explicitly enters part mode for a lone attachment while only
  `send` retains its genuine legacy `attach=` path;
- attachment-only reply creates one external leaf and does not invent or
  consume an implicit body;
- body-plus-attachment order is body first, external leaf second;
- exact retry is effectively once and changed attachment bytes fail closed;
- invalid-UTF-8 references are exercised through all four packaged authoring
  verbs, with `reply` and `close` using a real active claim;
- both refused dispositions leave the claim active and create no disposition;
- three focused packaged regressions pass independently;
- `git diff --check` is clean.

The two rulings K listed as pending have since been resolved:

1. References remain an optional mailbox convention exposed through a strict
   convenience. Each checked reference is now root-qualified as
   `ROOT_ID:RELATIVE/POSIX/PATH`; the generic `--part` escape remains
   unchecked. See `STAGE-1B-REFERENCE-ADDRESS-RULING.md`.
2. After reply/close, TUI pane focus returns to Messages while selected-row
   identity is preserved. The focus correction was separately approved.

Proceed with the root-qualified references correction and its focused tests.
Do not rerun the full suite until that last contract change is ready.
