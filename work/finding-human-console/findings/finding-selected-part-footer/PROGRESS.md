# Progress

Owner: `baton.implementer` only.

## 2026-08-10 — implemented

State: **complete, pending review**.

Implementation: `part_footer` plus `PART_FOOTER_ROWS` in
`baton_tui/render.py`; `_detail_pane` reserves the last row; `layout_for`
subtracts it from the model's scrollable height.

Against the contract:

- body content begins where the leading part header was; a single-part text
  message shows its text first;
- one fixed footer row, format as specified, including `(N/TOTAL parts)`;
- it survives vertical and horizontal scrolling and focus changes;
- `[address]` is the address; a `part_name`, when present, is shown separately
  and labelled `name:` — the address is never called a name;
- `[`/`]` update the footer and bring the part's CONTENT into view;
- multipart bodies keep a quiet blank-line boundary, with no repeated media
  line; container labels stay, because they say where in the message you are;
- a contentless message shows `0 parts` and fabricates no address;
- one DETAIL row consumed, accounted for in layout, paging, overflow and
  resize; the global status bar is untouched;
- narrow terminals truncate by display cells, asserted at 40, 60 and 100.

ONE CHANGE BEYOND PRESENTATION, and it should be visible in review rather than
buried: bringing a part's content into view used to scroll to that part's
HEADER row, which text parts no longer have. Scroll targets and style marks
are now separate signals through the renderer. Conflating them would either
style body text or stop `[`/`]` scrolling at all. No core, protocol, schema,
manifest, delivery, receipt, claim or materialize behaviour changed.

Evidence 1-7 covered, including a packaged PTY test asserting the footer is
the last pane row and has not displaced the status bar.

Break-checked: the footer row, the reserved row, and body-before-metadata each
fail named tests when removed.

Deleted during implementation: a separate zero-parts branch that printed what
the no-selection path already printed. No break check could tell them apart,
which is how a redundant branch announces itself.

## Migrated tests

Nine tests pinned the leading-header design this finding replaces, and were
rewritten against the footer contract with the supersession stated in each
docstring: five mark/styling tests, one container-panning test, two
part-navigation tests, one state test. Two PTY fixtures changed for the same
reason.

## 2026-08-10 — corrected after review R1, R2, R3 and the cleanup

State: **corrected, pending re-review**.

**R1, stale state.** `_detail_lines` hides the message behind a fresh
composition; `_shows_part_footer` did not, so a new compose or notice got the
previous message's address, media type, disposition and NAME attached to it —
attributing unrelated content to the draft the human was about to send. It now
applies the same `_fresh_composition` rule. A REPLY deliberately keeps its
original and its footer, and that distinction is pinned so the fix cannot
erase reply context.

**R2, truthfulness.** `_detail_parts` was a SECOND traversal that recognised
fewer detail shapes than `state.visible_parts()`, so an unopened two-part
preview said `(0 parts)` — "not loaded here" stated as "contentless". Deleted.
The footer counts through the model's own traversal, and is shown only for
shapes whose part set is authoritative, so a lightweight outbound listing row
shows no footer rather than an invented zero. The approved `0 parts` for an
actually opened contentless message is unchanged and still pinned.

**R3, truncation.** The count was built at the far right and handed to
ordinary right-edge truncation, so a long advisory name removed it at every
width — the one field the footer exists for. The count is reserved now and the
optional fields are dropped from the right until the address and count fit.
The narrow regression asserted only display width, which is why it passed
while the suffix was absent; it asserts the INFORMATION now.

**Cleanup.** `part_header_line_index` is `part_start_line_index`, with the
driver local and the surrounding comments corrected. Text parts have no header
row, and leaving the name would have future navigation work infer one.

Break-checked: the fresh-compose rule, the authoritative-shape rule and the
reserved count each fail named tests when removed.
