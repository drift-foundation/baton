# R102–R106 corrected — evidence

In reply to review `fc1b9f068cbbe9970b6f6c6e89a2144c`
(review-2026-08-15T19-54-12Z.md, claim
`f0c3ac4b65a8003dcda95bc8a268ae3c`). Note: this review crossed the
deployer round already delivered on the handoff follow-up claim; R106
(fit/footer/scroll) and the transitions FACT line were green there.
This round completes everything else.

## R102 — a real v11 deployment product

`tools/deploy_work.py` (v11-only, shares nothing with the frozen v10
deploy) installs the COMPLETE distribution into an explicit new
immutable directory by one atomic rename:

    bin/baton-work            executable zipapp (cli:entry)
    doc/BATON-WORK.md         the operator quickstart (new, docs/)
    conf/baton.example.json   a complete VALID strict example (new,
                              conf/ — proven by the product's loader)
    tmpl/*.md                 the numbered template assets (M6)

The exact handoff commands (no source copies, no rm -rf, nothing
inferred):

    cd ~/src/baton
    python3 tools/deploy_work.py /your/dist/baton-work-r1

    mkdir -p ~/your-home
    /your/dist/baton-work-r1/bin/baton-work init ~/your-home
    # edit ~/your-home/baton.json (conf/baton.example.json is a
    # complete valid model)
    /your/dist/baton-work-r1/bin/baton-work --participant team.member \
        activate ~/your-home
    /your/dist/baton-work-r1/bin/baton-work \
        --config ~/your-home/baton.json --participant team.member tui

The installed executable path Slawomir uses for init/activate/tui is
`/your/dist/baton-work-r1/bin/baton-work`, exactly as printed by the
deploy summary. B3 and its harness now exercise the artifact produced
by THIS deploy command; the ad-hoc zipapp construction is gone.

## R103 — containment proven honestly

The byte-identity prose was wrong (the piped form hashed pathnames)
and probing production v10 for acceptance is out of scope either way;
both are withdrawn. Containment is now proven inside the temp-only
acceptance: a populated CANARY tree (foreign json/sqlite/md files)
snapshotted by bytes, inode, and mtime survives the complete
deploy + init + edit + activate + create story unchanged
(`test_deploy_and_onboarding_touch_nothing_outside_their_targets`),
and isolation from v10 is by the explicit config/path boundary — no
v10 path is ever an input.

## R104 — the console acts through the one public surface

The `:` command bar routes the typed line to the SAME
`baton_work.cli` entry the JSON agent uses — same config, same
participant, same grammar, the same refusals surfacing on the status
line. Every transition `available_transitions` declares (already
rendered as the `can:` fact) is therefore actionable with the public
vocabulary; the console adds nothing and hides nothing. The tui
boundary guard was amended by exactly one allowlist entry (`cli` —
through the boundary, not around it); SQL/_write/baton_core remain
banned and the guard still bites.

B3 is now the ruled scenario through the DEPLOYED console
(`test_tui_packaged.py`): ada creates the provider epic; sl creates
the consumer and the dependency edge (ready flips false); ada fans
out an include and a request obligation; sl responds (obligation
clears); ada passes with a planned return (current/next verified);
sl closes satisfying — the consumer UNBLOCKS; the closed provider is
collapsed by default and reveals `c/sat` under `z`; a refused close
without rationale surfaces the public refusal in the console. Every
JSON verification runs through the same installed executable.

## R105 — navigable graph and discussion sets

- Links: selectable rows carrying the STABLE Work id, status,
  outcome, endpoint, and title; Enter performs the deliberate
  cross-team drill-through and the breadcrumb reconstructs the far
  Work's real ancestry (real-PTY regression).
- Discussions: the focused view lists the Work's discussion SET
  (ids, personal New, last seq) selectably from the paged canonical
  read; Enter opens exactly the chosen discussion — a second
  labelled discussion's messages never bleed in (regression).
- Threads: read in BOUNDED pages through the canonical `thread`
  read; `n` pages past the painted page, `p` returns to the start,
  and `s` stays bounded by the PAINTED page — proven by a 25-message
  discussion regression that also confirms later messages stay New
  after a page-two mark. The three WS-4-era console seen-tests were
  adapted to the new Enter-then-thread flow with their page-bounded
  assertions unchanged.

## R106 — completed

Fit at 44/56, the reserved collapse footer, and cursor scrolling were
delivered in the prior round (the five reviewer regressions green);
this round adds the final piece: below the minimum the table REFUSES
with an explicit "(terminal too narrow: need N cells)" line instead
of truncating identities, with its own real-PTY regression.

## Sweeps and gates

Defect in → red → restore → green, no residue: command bar severed
(B3 red), links drill-through dropped, discussion selection ignored,
thread paging dropped, too-narrow refusal dropped, doc/conf assets
dropped. The tui boundary guard additionally bit twice on uppercase
needles during the round.

Focused: 33 passed (TUI incl. every reviewer regression, parity,
the packaged scenario, deploy incl. the canary containment).
`just test-v11`: 531 parallel + 3 serial passed. Dossier: PROGRESS.md
Step 52. STOPPED for re-review; the parallel trial and production
operations remain held.
