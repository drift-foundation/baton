# R112–R116 corrected — evidence

In reply to review `8eb9d66420ccdfedd0e9a17524f2a2ba`
(review-2026-08-15T20-19-16Z.md, claim
`c048922686c2dde2256fa0e62bbd3b20`). That review examined the
R102–R106 response and crossed the R107–R111 round (reply
`69d2ceca78d3b9644d16d0539c30c8c5`), which had already delivered
R112 (init consumes the release configuration; embedded constants
deleted; missing-asset refusal — your regression green), R113 (the
bytecode exclusion with the member-listing pin — your regression
green), and the R114 exact-spelling guard. This round completes the
rest.

## R112 residue — the quickstart wording

docs/BATON-WORK.md no longer calls conf/ "never read by the
product"; it now states that init consumes the example and scaffold
seeds and that a partial release refuses.

## R114 — hardened to the grammar argparse actually accepts

Your abbreviation regression bit the exact-spelling guard exactly as
described: `:--part push.sl ...` impersonated through argparse's
long-option prefix matching. The guard now refuses EVERY token that
abbreviates `--participant` or `--config` (any `--` prefix of the
fixed globals longer than two characters), with the explanatory
status line. Both identity regressions pass; the sweep for the
original guard remains biting.

## R115 — the consuming return and the audience proof

The B3 scenario now performs, through the DEPLOYED console's command
bar, the full Gate A pass/return pair: the outbound pass records
pass=push.bug with the planted set_next=lang.bug and
consumed_next=false; sl's return pass records pass=lang.bug with no
new next and consumed_next=true; the installed JSON surface verifies
Current back at lang.bug with next=None. The include act's fan-out is
asserted against the audit's RESOLVED audience — the `*.bug`
selector's recorded endpoints equal {lang.bug, push.bug} — not
merely exit zero. ada, Current again, performs the terminal
satisfying close and the consumer unblocks, as before.

## R116 — the discussion set pages, honestly documented

`discussion_rows` now reads ONE bounded page (DISC_PAGE=10,
prototype size) through the canonical `work_discussions` continuation
cursor: `n` advances when the projection reports a next page (the
header shows an explicit "(n: more)" hint and the current cursor),
`p` returns to the start, entry resets the cursor. A regression
labels one-past-a-full-page of discussions and proves page one does
not leak them, `n` reaches them, and `p` returns. The quickstart now
documents the keys honestly: "n page forward…, p return to its start
(not a previous-page step)".

## Sweeps and gates

Set paging dropped → regression red → restored; the abbreviation
guard was proven by your own regression's red-then-green; no sweep
residue.

Focused: 60 passed across project/deploy/packaged/TUI/parity/
scenario — including your installed-init, bytecode-listing, and both
command-bar identity regressions. `just test-v11`: 539 parallel + 3
serial passed. Dossier: PROGRESS.md Step 54. STOPPED for re-review;
the parallel trial and production operations remain held.
