# Header simplification review — cleanup requested

The implementation is accepted. Focused review passed:

- source render: simplified count header, identity rule, full-width divider,
  and 40/44/52/60/80/133-column degradation — 9 tests passed;
- packaged zipapp: 80- and 44-column PTY cases — 2 tests passed;
- the one-cell terminal shield preserves the complete participant address;
- SENT adopting the same quiet `Sent:` shape is consistent and approved;
- `git diff --check` is clean.

Before this phase is committed, clean the stale contract record:

1. `work/finding-human-console/FINDING.md` still says the focused labels are
   `> MESSAGES` / `> SENT` / `> DETAIL` and says both labels are always drawn.
   Mark that presentation superseded and state the new count header,
   label-free detail rule, and one leading focus marker.
2. `work/finding-human-console/PLAN.md` repeats the old label contract as
   done/pinned. Update the row and explanatory paragraph.
3. `work/finding-human-console/TRIAL.md` says the screenshot is current and
   describes the old header, old detail label, and older status glyphs. The
   checked-in screenshot is now stale again after this ruled change. Record
   that a new human terminal capture is outstanding; do not claim the old
   image depicts the current UI.
4. Remove the duplicated consecutive `MIN_RULE_CELLS` comment in
   `baton_tui/render.py`.
5. Refresh stale test comments/docstrings that still explain locators in terms
   of a `DETAIL` label or `> MESSAGES`; the assertions are already corrected,
   but the surrounding explanation must not teach the retired surface.

Do not rerun `just test` for this documentation/comment-only cleanup. Focused
text checks and `git diff --check` are sufficient; the full suite runs once at
the final Stage 1B gate.
