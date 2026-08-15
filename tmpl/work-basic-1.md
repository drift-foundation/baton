# work-basic-1 — turning an accepted report into a managed dossier

This is a numbered instruction pattern, edition 1. A materially changed
instruction becomes `work-basic-2.md`; this file is never rewritten in
place. It teaches an implementer how to turn an accepted report or
research result into a permanent Baton dossier. It is not a directory
copied verbatim, not a protocol object, and nothing in Baton validates
the shape it describes.

## Where the record lives

Choose the canonical permanent location at creation and never move it:

    work/records/YYYY/MM/<stable-record-name>/

The year and month are when the record is created; the stable name is a
short kebab-case identity for the finding (for example
`finding-parser-recovery`). Optionally add a human convenience symlink:

    work/open/<friendly-name> -> ../records/YYYY/MM/<stable-record-name>

The symlink is sweep-friendly courtesy, never protocol state; remove it
at close as ordinary housekeeping.

## What goes inside

Every dossier starts with three files:

- `REPORT.md` — the accepted report or research result, complete and
  self-contained: what was observed, why it matters, and the evidence
  as received. Do not thin it down to a summary of a conversation; a
  reader must not need the discussion history.
- `PLAN.md` — how the work will be delivered: scope, slices or steps,
  what is explicitly out of scope, and where each review stop lands.
- `PROGRESS.md` — the append-only step log. One entry per meaningful
  step, newest last, with exact evidence (test counts, commands,
  decisions). Never rewrite an earlier entry.

Add context-appropriate structure when the work needs it — `reviews/`
for append-only review journals, `repro/` for reproductions, `tests/`
or `scripts/` for executable evidence, `fixtures/` and `data/` for
supporting material. Do not manufacture empty directories for shape's
sake; the pattern describes responsibilities, not a fixed tree.

## How Baton relates to the record

Bind the Work to the record's canonical path
(`ROOT_ID:work/records/YYYY/MM/<stable-record-name>`) at creation or as
the Current handler afterwards. Reference evidence in messages as
paths relative to the dossier. Git owns the file history; Baton owns
only the binding and the self-contained Work and discussion record.
Terminal Work freezes its binding; later corrections are follow-up
work and new evidence, never a rewrite of the closed record.
