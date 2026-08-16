# Ruling — completion glyph is direction-independent

The human-facing status column describes both ownership while work is live and
the item outcome once it is terminal.

This is deliberate progressive disclosure for a human interface. The list
spends its visual budget on only two questions: who owns the next action, and
is the item done? Exact protocol state, disposition, and outcome remain in the
detail pane and help instead of competing for attention on every row.

- `•` means an inbound item has not been opened by me.
- `○` means I opened it and still owe a reply or close.
- `▷` means an outbound item is queued for the remote party.
- `▶` means the remote party picked it up and is working.
- `✓` means the item is ordinarily finished: replied/completed, closed without
  reply, or a notice seen. Direction does not change it.
- Direction matters while an obligation is live, because the human must know
  who owns the next action. Direction does not matter after completion: the
  party/direction column already shows who acted, and the terminal glyph must
  not duplicate that information.
- Protocol/store states are unchanged. This is presentation only.

Consequently, both `R` and `C` are removed from the human-facing status vocabulary,
including the message list, SENT view, help, README, trial guide, tests, and
packaged zipapp. A completed inbound and completed outbound row with otherwise
equivalent state must render the same `✓` glyph; a normally closed row and a
seen notice use it too. The detail pane retains the exact protocol state and
outcome for anyone who needs to distinguish reply from close. `Q/P` may remain only as the
non-UTF fallback for `▷/▶`; they are not the normal UTF-8 presentation. The
fallback must likewise use one direction-independent completed marker.

The final packaged PTY gate must exercise inbound and outbound live states,
both terminal directions, and prove that the UTF-8 UI shows `•/○`, `▷/▶`, and
`✓` with no human-facing `R replied` or `C closed` legend.

## References

- `baton_tui/render.py`
- `test_tui_render.py`
- `test_tui_driver.py`
- `README.md`
- `work/finding-human-console/PLAN.md`
- `work/finding-human-console/TRIAL.md`
- `work/finding-human-console/FINAL-GATE.md`
