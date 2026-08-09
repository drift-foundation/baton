# R10 fixed — and the reported symptom was not the defect

Reproduced immediately against the exact shape: an inline Markdown leaf beside
an external LICENSE leaf. **Both part headers were already reachable and
`[`/`]` did move the mark.** What Slawomir saw on the external row was this:

    [1] text/plain; charset=utf-8  attachment  LICENSE  (no retained bytes)

The console told him the part was empty. "I can only view part[0]" was the
only conclusion available from that screen, and it was correct.

`(no retained bytes)` belongs to a SCRUBBED transient body, where the manifest
outlives the payload. An external leaf has bytes — in a configured root,
hash-pinned, verified at claim time — it simply does not carry them in the
envelope. `storage` is what tells the two apart, and the renderer was not
looking at it.

And he was half right: there was no way to READ it. `m` refuses on an external
part, deliberately and correctly — it is already a file, and copying it into a
projection would duplicate the thing the pin exists to avoid. So the console
offered a header, a false statement that it was empty, and no key at all for
the one thing a person wants to do with a licence.

## Three fixes, together

- **The header says what an external part is**: size, the pinned `root:path`,
  and that the pin verified.
- **`v` reads a text part into the pane.** New read-only core call,
  `read_claimed_external_part`: owner-checked and gated on an active claim,
  like every other path that returns content; the pin is REVALIDATED before a
  byte is read, so bytes edited after publication fail closed rather than
  being shown as what the sender sent; bounded to 1 MiB for display and
  explicit when it truncates; resolved by the pinned root id and relative path
  through the same component-wise no-follow walk that pinned it, never the
  advisory `filename`. Non-text media and non-UTF-8 bytes are refused with the
  location rather than wrapped into the terminal. `v` was verified unbound.
- **The bytes are cached for DISPLAY only**, keyed by manifest address and
  dropped whenever the detail pane changes — otherwise message A's licence
  would redraw under message B's part 1.

## Your regression, and one clause I did not implement as written

"both part headers are reachable using `[`/`]`, the selected header visibly
changes" — pinned, and it already held; the pin now proves it rather than
assuming it.

"materialize targets the selected external part" — it already does, and I did
not change the core rule to make `m` copy the file. The refusal names part
`1`, the part the human selected, rather than silently writing part 0. Copying
an external part into a projection is exactly what the pin exists to prevent,
and TRIAL has recorded that rule since round three. Pinned as "the refusal
names the selected part". If you meant `m` should start copying external
parts, that is a core rule change and I would want it ruled explicitly.

## One thing found while fixing it

A wrapped part header repeated the selection marker on every continuation row,
so a header long enough to wrap looked like several selected parts. The new
external header is long enough to wrap at 100 columns, which is how it
surfaced. The mark is applied to the first row only now; the indents are the
same display width, so continuations still line up.

## Deliberate-break checks

| Break | What fails |
|---|---|
| an external part described as empty again | the not-empty pin and the read pin |
| `v` unbound | three read pins |
| pin revalidation skipped before reading | the broken-pin pin |
| the display cache kept across a move | the never-under-another-message pin |

## Verification

    just test          1596 passed   (was 1589)
    git diff --check   clean
    bin/baton-tui      742159a98d03d50008e4c827fcdbc3e8475fa4e74934013312ce789978a52541
                       deterministic: rebuilt twice, byte-identical
    frozen             bin/baton a23461ae7577422f5c4ade86eae370926b2dc41bc93ecd7732c29b2785374566,
                       DISTRIBUTION.json, baton_v6.py, build_zipapp.py unchanged
    docs               test_docs_consistency.py green

The frozen agent CLI and the protocol authority are untouched: protocol 9, no
schema change, and the only core change is an additive read-only method.

**Relaunch the console to pick this up** — a running one keeps the old code.

## Changed paths

    baton_core/_impl.py
    baton_tui/state.py
    baton_tui/render.py
    baton_tui/keys.py
    baton_tui/driver.py
    bin/baton-tui
    DISTRIBUTION-TUI.json
    test_tui_state.py
    work/finding-human-console/FINDING.md
    work/finding-human-console/PLAN.md
    work/finding-human-console/TRIAL.md

New tests, all in `test_tui_state.py`:
`test_both_part_headers_are_reachable_and_the_mark_moves` (the regression you
specified), `test_an_external_part_is_not_described_as_empty`,
`test_v_reads_the_external_part_into_the_pane`,
`test_reading_an_external_part_writes_nothing`,
`test_reading_an_external_part_fails_closed_on_a_broken_pin`,
`test_materialize_still_targets_the_selected_external_part`,
`test_bytes_read_for_one_message_are_never_drawn_under_another`, plus
`_licensed` and `_opened_licensed` helpers.

No existing test was rewritten this round.

FINDING gains the external-part contract in "Pinned TUI interaction"; PLAN
gains the status row; TRIAL records the trial, the fix and the break table.

## Still outstanding

`assets/artwork/baton-tui.png` — stale in three ways (columns, oldest-first,
flat replies) and needing a real-terminal capture from the trial. It and the
Git operations are the only items left in PLAN's "Remaining before this stage
is committed".

References:
- baton_core/_impl.py
- baton_tui/state.py
- baton_tui/render.py
- baton_tui/keys.py
- baton_tui/driver.py
- test_tui_state.py
- work/finding-human-console/FINDING.md
- work/finding-human-console/PLAN.md
- work/finding-human-console/TRIAL.md
- assets/artwork/baton-tui.png
- DISTRIBUTION-TUI.json
