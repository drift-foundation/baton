# Stage 1B re-review — changes requested

The R1–R8 corrections are substantially sound, and the focused correction
tests pass. Two release blockers remain. The first is another confirmed
successful-command data loss path.

## R9 — `reply --attach` silently discards the attachment

`authoring_opts()` newly exposes `--attach` on `reply`, but
`_authored_parts()` returns `None` whenever there is no `--part` or
`--references`. That fallback is valid only for `send`, whose historical
store call has an `attach=` parameter. `reply` has no corresponding legacy
parameter, and its dispatch never consults `_legacy_attach()`.

Confirmed through the packaged executable on a fresh protocol-9 instance:

```text
baton reply CLAIM --participant team.implementer --kind answer \
  --attach src:evidence.txt
```

The command returned success. The recipient claimed a response containing
one zero-byte inline `text/markdown` leaf. The external evidence part was
absent. The same defect drops `--attach` beside `--body` unless some
`--part` or `--references` option happens to force part mode.

Make every `reply` attachment enter the ordered parts plan, including when it
is the only authored source and when it accompanies `--body`. An omitted body
must not implicitly consume stdin when an attachment is explicit. Preserve
the true legacy `send --attach` path; this distinction is verb-specific.

Pin through the packaged executable at minimum:

- attachment-only reply delivers one external leaf and no invented body;
- body plus attachment reply delivers body first, external leaf second;
- attachment-only reply does not consume or publish available stdin;
- retry preserves the same manifest and refuses changed attachment identity
  under the existing retry contract.

This is the same class as R1: success while silently discarding a source the
caller explicitly named.

## R10 — R4's packaged regression still omits two verbs

`test_packaged_cli_diagnoses_an_unreadable_references_file` loops over only
`send` and `send-notice`. The review explicitly required the stable
no-traceback diagnostic to be pinned for all four authoring verbs, and the
handoff says it was pinned per verb. Add real claimed-message setup for
`reply` and `close`, then exercise invalid-UTF-8 `--references` through the
packaged executable for both. Assert refusal, the stable diagnostic, no
traceback, and no committed disposition.

## Documentation correction

The module header in `test_core_references.py` still says "The references
convention, enforced rather than described." That contradicts the implemented
and recommended split: the convention is optional; the `--references`
convenience validates its own input. Correct the header when Slawomir's
pending convention ruling is recorded.

## Raw-space question

Do not widen the descriptor grammar. Slawomir chose URL-query encoding, and
the pinned ruling explicitly says spaces are `%20`. The strict implementation
is correct; ergonomics do not override the chosen unambiguous grammar.

## Verification completed in this round

- `test_core_authoring.py` + `test_core_references.py`: 84 passed;
- eight focused packaged correction tests: passed;
- artifact, source, and protocol-document hashes match `DISTRIBUTION.json`;
- packaged version is tool 5.2.0 / protocol 9;
- `git diff --check`: clean;
- attachment-only reply data-loss reproduction: confirmed.

Correct R9 and R10 before another handoff. The full suite need not run again
until those focused regressions are green and the convention ruling is pinned.
