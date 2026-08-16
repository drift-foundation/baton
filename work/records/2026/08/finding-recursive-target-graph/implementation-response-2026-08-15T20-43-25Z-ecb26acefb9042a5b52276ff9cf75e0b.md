# R117–R119 closed — evidence

In reply to review `ecb26acefb9042a5b52276ff9cf75e0b`
(review-2026-08-15T20-32-06Z.md, claim
`2a4fa0a4638dd0975208b304e4ee12b4`). That review examined the
R107–R111 response and crossed the R112–R116 round (reply
`cf05c885b53c06790607d2617869dda5`), which had already delivered two
of its three items.

## R117 — the ruled grammar fix

The public CLI parser now sets `allow_abbrev=False`: the public
grammar accepts FULL SPELLINGS only, so no abbreviation of any
global — identity, configuration, or otherwise — can be accepted
anywhere on the surface. The parser grammar and the console guard
therefore agree by construction; the console's check over the two
fixed session globals remains only as the human-readable explanation
("--part … names the session's fixed global participant/
configuration"), no longer a compensating denylist. A new
public-grammar regression proves `--part` refuses as unrecognized
through the CLI itself, and the sweep (re-enabling abbreviation)
bites it. Your abbreviation regression passes.

## R118 — delivered in the crossed round

B3 performs the consuming return through the installed console
before the terminal close: outbound pass audited as
(pass=push.bug, set_next=lang.bug, consumed_next=false); sl's return
audited as (pass=lang.bug, no new next, consumed_next=true); the
installed JSON surface verifies Current back at lang.bug with
next=None; the include act is asserted against the audit's RESOLVED
audience ({lang.bug, push.bug}); ada — Current again — closes
satisfying and the consumer unblocks.

## R119 — delivered in the crossed round

`discussion_rows` reads one DISC_PAGE-bounded page with the
`after` cursor and carries the projection's `next_after`; `n`
advances (with an explicit "(n: more)" hint and the cursor shown),
`p` returns to the start, entry resets. Your
beyond-the-first-fifty regression passes, as does my
one-past-a-full-page regression. The quickstart documents `p`
honestly as return-to-start.

## Gates

Focused: 68 passed across project/deploy/packaged/cli-boundary/TUI/
parity/scenario — including your abbreviation, >50-discussion, and
installed-init/bytecode/identity regressions. `just test-v11`: 540
parallel + 3 serial passed. Dossier: PROGRESS.md Step 55. STOPPED
for re-review; the parallel trial and production operations remain
held.
