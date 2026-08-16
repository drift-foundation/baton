# Reviewer authorization — consolidated release-candidate gate

Status: passed; candidate released for Slawomir's human trial.

Accepted candidate:

    bin/baton-tui  3ef94453c3d7f64827f02b837413a33dce3960d447df3cdcf46aa94e8792b292
    bin/baton      a23461ae7577422f5c4ade86eae370926b2dc41bc93ecd7732c29b2785374566

K's fresh-cache gate reported 1882 passing tests, 50 packaging/core-boundary
tests, 24 packaged PTY/boundary tests, clean diff checking, two identical TUI
builds, and matching distribution metadata. Independent review verified both
artifact hashes, the distribution pins, the shared SENT list/detail resolver,
five focused glyph cases, the packaged SENT-list PTY case, and 18 core-parity
and packaging-isolation cases.

R1 through R9 in `REVIEW.md` are accepted. The current recovery contract,
front-matter key guide, obligation glyphs, `r`/`R` mapping, notation, and
exploratory-only Vi-mode record agree.

Run the final gate once against a fresh cache:

1. the complete test suite;
2. `git diff --check`;
3. packaging-isolation and shared-core boundary checks;
4. two deterministic `bin/baton-tui` builds with identical bytes;
5. distribution-manifest verification against the rebuilt artifact;
6. confirmation that frozen `bin/baton` is byte-identical to its pinned hash;
7. a packaged PTY smoke test using the rebuilt `bin/baton-tui`, including the
   final `•`, `○`, `▷`, `▶`, and shared `✓` obligation glyphs and the final
   `r`/`R` map.

The resulting handoff must name the test count, artifact and manifest hashes,
exact changed paths, and any remaining commit-scope decisions. Do not stage or
commit. Any handoff asking Slawomir to review must include this newly rebuilt
zipapp; no source-only candidate may be presented to him.

## References

- `work/finding-human-console/REVIEW.md`
- `work/finding-human-console/GLYPH-RULING.md`
- `work/finding-human-console/PLAN.md`
- `work/finding-human-console/TRIAL.md`
- `work/finding-protocol-10-umbrella/FINDING.md`
- `test_tui_driver.py`
- `bin/baton-tui`
- `DISTRIBUTION-TUI.json`
- `DISTRIBUTION.json`
