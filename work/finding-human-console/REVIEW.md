# Reviewer re-review — final UX residue

Status: changes requested.

The functional refresh correction and the strengthened rendered-surface
notation pin are good. The final gate remains held because current recovery
documentation and two live test comments still contradict the final key map.

## R1 — live test comments still invert `r` and `R`

In `test_tui_driver.py`, the cancelled-editor regression still calls this the
``R`` follow-up path and later says retry means pressing ``R``. This regression
executes lowercase ``r``. Both comments must say lowercase ``r`` so the test is
not a future instruction to restore the superseded mapping.

## R2 — the PLAN recovery contract still specifies the superseded key map

`work/finding-human-console/PLAN.md` still contains current, normative recovery
instructions that say:

- `r` is quick subject reply;
- `R` is full editor reply;
- manual refresh is `Ctrl-R` because `R` was taken;
- subject kill-left is `Ctrl-U`;
- the resolved directed-action decision includes browse `e`.

The final contract is lowercase `r` for editor reply/follow-up, uppercase `R`
for quick subject editing, `Ctrl+r` for refresh, `Ctrl+u` for kill-left, and
`Ctrl+e` for editor promotion from a typing mode. Browse `e` is absent. Update
the current key table, its explanatory prose, and any current resolved-decision
summary. Explicitly labelled historical records may remain historical; the
recovery contract may not contradict the shipped mapping.

## R3 — the PLAN says the screenshot is both done and stale

The active-item table correctly says Slawomir captured the replacement
screenshot. The paragraph immediately below still says the screenshot is stale,
must be recaptured, and blocks calling the stacked layout documented. Update or
remove that obsolete warning so the recovery state has one answer.

## R4 — the TRIAL front matter still teaches the superseded keys

The top-level `## Keys` section in `work/finding-human-console/TRIAL.md` is
presented as current instructions ("Everything Slawomir needs"), but still says
lowercase `r` is quick, uppercase `R` opens the editor, and `^R` is refresh
because `R` is the full reply. It also uses the superseded caret notation.
Either update this front matter to the shipped mapping and notation or label the
entire isolated-package section unmistakably as a historical snapshot and point
to the current instructions. A current-looking quick guide cannot contradict
the final contract recorded at the bottom of the same file.

## R5 — the PLAN still exposes an obsolete approval as current status

The PLAN's `### Review outcome` still says the old 1661-test snapshot is
approved, every review finding is closed, and the remaining acceptance item is
the terminal trial plus replacement screenshot. The screenshot is now complete
and the consolidated gate has not run. Recast that block as explicitly
historical or replace it with the current pending-gate state. Recovery must not
mistake an old package approval for the release candidate.

## R6 — current test prose still contains the inverse mapping

In the cancelled-editor regression, the paragraph now opens with lowercase
`r`, but still says "`R` from browse is ONE action" and "through Ctrl-E".
Those are lowercase `r` and `Ctrl+e`. The current refresh/focus docstring also
spells `Ctrl-R`; make it `Ctrl+r`. These are current explanations, not merely
quoted historical records.

## R7 — the Vi-mode discussion is not an approved finding

`work/finding-protocol-10-umbrella/FINDING.md` currently calls the proposed
Normal/Insert modes Slawomir's "after-commit finding" and refers to a
"ruling." Slawomir corrected that interpretation: this was loose discussion,
he is not sold on reassigning Esc, and Esc remains cancel unless a later
explicit ruling changes it. Remove the entry from the work queue or recast it
unambiguously as an unscheduled, unapproved question. It must not imply a
decision, scope, or acceptance criteria.

## R8 — one live test name still names the wrong key

`test_R_publishes_a_full_body_follow_up_from_a_handled_row` exercises the
lowercase editor key after the swap. Rename the test to lowercase `r`; unlike
explicitly labelled historical prose, a current regression name is an
instruction about the behavior it pins.

## R9 — lead the Vi-mode finding with its uncertainty

Keep the Vi-mode section as a finding, but its first substantive line must
state: **it is not a confirmed direction, is exploratory, and requires more
research and discussion.** The existing details about Esc and approval remain
useful after that lead.

## Delivery gate

After these corrections, run focused tests only and return the exact changed
paths. If this re-review clears, the reviewer will authorize the one consolidated
full-suite, deterministic-package, manifest, frozen-CLI, and packaged-PTY gate.
Every handoff requesting Slawomir's review must include a newly rebuilt
`bin/baton-tui` containing that exact candidate. Slawomir trials only the
zipapp; source-only behavior is not delivered behavior. The next rebuilt
artifact must therefore include the final obligation glyphs.

## References

- `test_tui_driver.py`
- `work/finding-human-console/PLAN.md`
- `work/finding-human-console/TRIAL.md`
- `README.md`
