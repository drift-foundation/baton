# Focused glyph review — changes requested

## Gate authorization after reachability check

The revised packaged test now states and proves the behavior the current
console actually exposes: the SENT list draws `▷` for unfinished outbound
work and `✓` for terminal outbound work, with no `?`, `R`, or `C`. Its name
and docstring no longer claim to exercise the detail heading.

`_sent_row_lines()` remains pinned by the four focused source cases. It is not
reachable for a non-empty SENT list through today's driver because selecting a
SENT row immediately opens the sender's copy. Do not turn this closing pass
into dead-code removal: the planned delayed preview/claim interaction may make
metadata previews useful again. The corrected shared resolver is safe to keep.

The focused correction is approved. Run the consolidated fresh-cache suite,
deterministic rebuild, distribution/hash checks, frozen-CLI check, and packaged
boundary/PTY gate. A matching rebuilt `bin/baton-tui` is required before the
human trial.

## Re-review of the unbuilt SENT-detail correction

The source correction is accepted: `sent_status_glyph()` is now the one
outbound resolver used by both `_sent_pane()` and `_sent_row_lines()`, including
the encoding fallback. The focused source regression covers pending, claimed,
completed, and closed and passes all four cases.

The packaged PTY pin is not yet effective. `bin/baton-tui` is deliberately
still candidate `1d2334a2…`, whose embedded `baton_tui/render.py` visibly calls
the obsolete `sent_badge()` from `_sent_row_lines()`. Nevertheless,
`test_the_sent_view_and_its_detail_use_the_final_vocabulary` passes against
that artifact. The reason is that it opens two SENT rows, then switches back
to MESSAGES with `i`, and only afterward replays the combined final screen.
Its subject matches can therefore come from the MESSAGES list; they do not
prove that either opened SENT detail heading was observed.

Use the per-step transcripts already returned by `_console()` to replay and
assert the screen immediately after each Enter, before `i` changes views. The
test must fail against `1d2334a2…` because its opened heading is `?`, then pass
against the rebuilt artifact. Keep both an unfinished state and a terminal
state in that packaged proof.

My earlier duplicate-assignment note is withdrawn. The current tree has one
`target = row.get("to_participant") or ""` assignment in `_sent_pane()`; no
source deletion is required there.

After the PTY test is made effective, run it once against the old artifact to
pin the failure. Then rebuild and run the consolidated final gate. No further
source-design review is required if that proof behaves as specified.

## Re-review of candidate `76b12978…`

G1 and G3 are accepted. G2 was not applied, despite the handoff claiming no
`R` or `C` appeared anywhere on screen:

- `SENT_BADGES` still maps normal states to `Q/P/R/C`;
- `_sent_pane()` still renders `sent_badge(row)`;
- `_sent_row_lines()` still prefixes detail with `sent_badge(row)`;
- driver tests still assert answered is `R` and closed is `C`;
- the packaged PTY proof does not switch to SENT with `o`.

The PTY excerpt therefore proves only MESSAGES. Candidate `76b12978…` is not
approved.

## Re-review of candidate `1d2334a2…`

The SENT list is accepted, but the SENT detail heading was not unified.
`_sent_row_lines()` still prefixes a directed row with `sent_badge(row)`.
Because the normal states were correctly removed from `SENT_BADGES`, opening a
normal sent message now visibly renders `?`:

    _sent_row_lines({row_kind: message, state: completed,
                     subject: Done, ...}, 80)[0]
    -> "  ? Done"

The new two-view regression compares list rows only, and the packaged PTY
switches to SENT without opening a row, so both miss the detail path explicitly
named in G2. Route `_sent_row_lines()` through the same normalized status
function and encoding fallback. Preserve the exact `State:` prose below it.
Add a regression that opens normal pending, claimed, completed, and closed
SENT rows and asserts their detail heading; the packaged PTY must open at least
one SENT row and prove no `?`, `R`, or `C` heading appears.

Also remove the duplicated consecutive
`target = row.get("to_participant") or ""` assignment in `_sent_pane()`.
Candidate `1d2334a2…` is not approved.

The primary MESSAGES mapping, direction-aware live ownership, shared completed
glyph, encoding fallback plumbing, and packaged-renderer parity regression are
accepted. The packaged parity test caught a real startup crash and must remain.

## G1 — apply the final no-`C` ruling

The current candidate deliberately retained `C`; Slawomir's later ruling
supersedes that hold. Closed without reply is an ordinary finished item and
renders `✓`, inbound or outbound. The exact state/outcome remains in detail.
No human-facing `C closed` vocabulary remains.

## G2 — SENT still uses the old badge machine

The handoff says `R` is gone from the SENT view, but the current source still
has:

- `SENT_BADGES = {pending: Q, claimed: P, completed: R, closed: C, ...}`;
- `_sent_pane()` calling `sent_badge()`;
- `_sent_row_lines()` calling `sent_badge()`;
- `SENT_LEGEND` teaching `Q/P/R/C`;
- live tests asserting `sent_badge(answered) == "R"` and closed is `"C"`.

So the primary MESSAGES view changed while SENT remained the old vocabulary.
Route directed SENT rows and their detail heading through the same
direction-aware presentation contract: UTF-8 `▷/▶/✓`, with closed also `✓`.
Authored notices may retain `N` as a row kind. Exceptional states remain
distinct. Remove or demote old badge helpers so a second human-facing status
machine cannot drift again.

Add a regression that renders both MESSAGES and SENT for the same outbound
pending, claimed, completed, and closed states. The UTF-8 screens must use
`▷/▶/✓/✓`, and neither screen, help, nor docs may contain the old `R replied`
or `C closed` legend.

## G3 — README opening and stale screenshot comment

Apply `README-RULING.md`: put the offline, fully sandboxable peer-coordination
paragraph before the screenshot, and remove the HTML comment incorrectly
calling the current stacked screenshot stale.

## Gate

First add the SENT-render regression and demonstrate that it fails against the
current `76b12978…` source because `R/C` are drawn. Then apply the one-status
path, run focused render/driver/docs/PTY tests, and hand the exact delta back
for review. Do not run another full suite or final rebuild before focused
approval. The prior `704bbce6…`, `76b12978…`, and `1d2334a2…` builds are
obsolete. After focused approval,
rerun the consolidated fresh-cache deterministic package gate. Its packaged
PTY smoke must explicitly switch between MESSAGES and SENT and exercise all
four directed live/terminal states in both applicable perspectives.

## References

- `work/finding-human-console/GLYPH-RULING.md`
- `work/finding-human-console/README-RULING.md`
- `baton_tui/render.py`
- `test_tui_render.py`
- `test_tui_driver.py`
- `test_tui_pty.py`
- `README.md`
- `work/finding-human-console/PLAN.md`
- `work/finding-human-console/TRIAL.md`
