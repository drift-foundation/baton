# v11 deployment is not byte-reproducible

## Observed — 2026-08-17

The reviewed W104 candidate and the committed `137d7fc` deployment produced
different `archive_sha256` values from byte-identical application sources:

- reviewed candidate: `056c2ccb7668a131613fd77ec2d90974c1df21bd778cb89d4f1edf0e6256df7b`;
- deployed candidate: `00d6b0ea0b1aabd5bf3123a19832c5a6ac89cb2e46241f11dd08480f65e4f942`.

Both archives contain the same 14 member names in the same order. Every
member has the same CRC, compressed size, and uncompressed SHA-256. The sole
metadata difference is the `__main__.py` ZIP timestamp:

- reviewed candidate: `2026-08-17 19:57:46`;
- deployed candidate: `2026-08-17 21:38:48`.

`cmp` reports four differing bytes: the duplicated DOS time/date fields in
the member's local and central directory headers.

## Confirmed cause

`tools/deploy_work.py` copies sources into a temporary staging tree and calls
`zipapp.create_archive()`. The generated `__main__.py` inherits the staging
time, so identical inputs built at different times produce different archive
bytes. The repository already has deterministic ZIP writers in
`tools/build_zipapp.py` and `tools/build_tui.py`, but the v11 deployment path
does not use that property.

This is a release-gate defect, not a semantic payload difference. The
deployed `137d7fc` executable has the reviewed member contents, but its digest
cannot prove reproduction of the reviewed candidate.

## Decision

The v11 executable is a reproducible artifact. Its bytes depend only on its
intentional source inputs, never source or staging mtimes, build time, host
residue, or enumeration order.

**Superseded 2026-08-17 by the speed-priority cutover ruling below:** do not
use the `137d7fc` deployment for the authority cutover. Correct the builder,
pass the reproducibility regression and v11 gate, let Slawomir commit the
correction, and deploy the resulting commit to a new immutable release
directory.

## Cutover exception — 2026-08-17

Slawomir ruled that restoring forward progress takes priority over repairing
the packaging gate before cutover. Release `137d7fc` is accepted for this
cutover because the investigation proved that its application member names,
order, CRCs, sizes, and uncompressed bytes exactly match the reviewed W104
candidate. Only the duplicated ZIP timestamp fields for generated
`__main__.py` differ.

This exception does not redefine reproducibility or close the defect. W308
remains open for the next release, which must restore a stable digest and add
the mtime-perturbation regression. No later release may infer a general
timestamp-mismatch waiver from this one evidence-bound cutover exception.

## Acceptance

1. Two v11 deployments from identical source bytes produce byte-identical
   `bin/baton` archives and the same reported `archive_sha256`.
2. Changing source mtimes between those builds does not change the artifact.
3. Archive members have fixed metadata and deterministic ordering.
4. Generated `__main__.py` remains the ruled `baton_work.cli:entry` bootstrap,
   with the existing executable shebang and mode.
5. The installed onboarding, TUI, ACP bridge, and complete v11 gates remain
   green.
6. Existing immutable release directories are never overwritten or adopted.
