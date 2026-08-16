# Finding: label the Work classification column `Cat`

## Observed

The v11 Work table labels its compact classification column `Cls`. During the
live trial Slawomir found that abbreviation opaque; readers do not naturally
connect it to the category of a finding.

## Confirmed correction — 2026-08-16

Render the Work-table header as `Cat`. People already think of the value as
the Work/finding category, and the abbreviation is easier to scan.

This is presentation only. Canonical JSON, schema, command grammar, and source
identifiers continue to use `classification`; compact values such as `defct`
are unchanged. The earlier header-case finding remains historically correct
for its release, but its recorded `Cls` display label is superseded by this
decision for the next distribution.

