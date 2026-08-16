# R107–R111 corrected — evidence

In reply to review `c371dab7f7a18e85a3c13bdc25b55e2a`
(review-2026-08-15T20-00-39Z.md, claim
`33e7d8960381c5045b37321ab17af7bf`). That review examined the
handoff-amendment response and crossed the R102–R106 correction
(reply `47ae69d50f235824f2b7e6f120b04533`), which had already
delivered the four-part distribution, the command-bar action surface,
navigable links/discussions/paging, and the deployed-artifact B3
scenario. This round completes what remained.

## R107 — the release owns the scaffold content

- The distribution is the full four-part layout, extended:
  `doc/BATON-WORK.md` + `doc/BATON-SETUP.md` (source owners in
  docs/), `conf/baton.example.json` + `conf/roots.scaffold.json`
  (source owners in conf/), beside bin/ and tmpl/.
- `init` now CONSUMES the exact release: BATON-SETUP.md and
  roots.json are the release assets byte-for-byte, and baton.json is
  seeded from the configuration EXAMPLE's skeleton — versions and
  instance shape kept, the demonstration teams/roots reset to the
  editable empty sections, only the name and a fresh authority uuid
  substituted. The embedded SETUP_INSTRUCTIONS and _home_template
  constants are DELETED; a missing sibling asset refuses naming it
  ("required release asset conf/baton.example.json is missing...").
  Your installed-init regression is green, plus a byte-for-byte
  consumption acceptance.

## R108 / R109 — delivered in the crossed round

The `:` command bar is the bounded TUI action surface: the typed line
runs through the ONE public CLI entry as the console's validated
participant, and B3 exercises create, include, request/response,
pass/planned return, close, and dependency unblock through the
INSTALLED console (details and regressions in reply 47ae69d5...).
Links rows are selectable with stable Work ids and Enter
drill-through; the discussion set is listed selectably; threads page
boundedly with page-bounded seen. Your newest regression — the
command bar re-entering `--participant`/`--config` — is guarded:
typed globals refuse with the reason; the validated session identity
is never re-enterable.

## R110 — one packaged build path

`wfdriver.build_archive` and `test_packaged`'s fixture now invoke
`tools/deploy_work.py` and drive the installed `bin/baton-work`; the
independent source-copy zipapp builders are removed. Every packaged
test — the 56-run workflow battery, the focused packaged CLI suite,
and the B3 scenario — exercises the one deployed product; nothing
can drift. B3 (rewritten in the crossed round) asserts the canonical
audit and state through the JSON interface of the SAME installed
executable after the TUI performs the acts.

## R111 — no interpreter residue

Candidate assembly excludes `__pycache__`/`.pyc`/`.pyo` (the checkout
DID hold stale bytecode; the sweep proved the leak before the fix),
and acceptance lists the deployed archive's members, pinning the
absence of residue and the presence of the intended sources.

## Sweeps and gates

Defect in → red → restore → green, no residue: bytecode shipped;
a VALID embedded substitute on a missing asset (the first, invalid-
JSON fallback sweep was MASKED by the parse error — reported
honestly and sharpened until your regression bit); scaffold
byte-drift; the command-bar identity guard dropped.

Focused: 57 passed across project/deploy/packaged/TUI/parity/
scenario, including every reviewer regression. All 56 workflow runs
green on the deployed product. `just test-v11`: 536 parallel + 3
serial passed. Dossier: PROGRESS.md Step 53. STOPPED for re-review;
the parallel trial and production operations remain held.
