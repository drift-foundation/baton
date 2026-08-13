# Successor verification — the scenario, run

Owner: `baton.implementer`. `FINDING.md` and `PLAN.md` are the reviewer's; this
file is mine.

## What was asked

PLAN step 2: run the send-scoped-broadcast / observe-in-Sent scenario on the
next-generation client, without restarting the TUI. Pass → record legacy-only
closure. Fail → correct the successor before cutover.

## Result: the successor passes

Two levels, one session each, and in both the checks run against the console
that published the notice — no second state object, no reopened store, no
refresh performed on the console's behalf.

`tests/tui/test_tui_sent_broadcast.py` (7 tests), driving `InboxState` through
the real key handler:

* the scoped broadcast is in the sender's Sent view immediately, and the list
  reports itself fresh rather than cached;
* the row is accurate — subject, `kind=announcement`, no borrowed directed-message
  vocabulary, `to_participant` absent, receipts at 0 — and the receipt count
  moves to 1 when a recipient `see`s it;
* it is drawn on the rendered Sent screen with the notice glyph, not merely
  present in the model;
* a GLOBAL broadcast behaves the same (it takes the other branch where the TUI
  spelling becomes `scope=None`, so a scope-dependent implementation would pass
  the reported case and fail here);
* the sender's own copy does not land in the inbox instead;
* ordering and completeness, with the caveat below.

`tests/tui/test_tui_pty.py::test_a_published_broadcast_appears_in_sent_on_a_real_terminal`,
in front of curses on a real pty: `N`, `acme.*`, Enter, subject, Enter, `y`,
`o` — and the row is read off the reconstructed screen after `o`, not out of
the raw transcript (which would have found the composer keystrokes).

### Break sweep

`list_sent`'s notice query was made to return nothing
(`... WHERE from_participant=? AND 0=1`). All 8 tests failed, including the
PTY one — so none of them is matching leftover paint. Restored: 8 pass.

## What the pass does NOT prove, and the reviewer should not read into it

**Legacy's core is not missing notices from `list_sent`.** Reading the deployed
`/home/sl/baton/app/baton-cli/legacy/v1.1.0/bin/baton`, its `list_sent` selects
`FROM notices WHERE from_participant=?` exactly as the successor does. So the
successor passing is NOT evidence that a legacy core defect was fixed; whatever
Slawomir saw at 15:42Z has another explanation — the console layer, the
projection-directory reading of "folder", or timing. Per PLAN step 1 I did not
diagnose legacy further, and I am not claiming a repair that did not happen.

The honest closure this supports is: **the successor meets the acceptance
boundary**, so no correction is owed before its cutover. Whether the legacy
observation is closed as legacy-only is the reviewer's call, and it rests on
the ruling, not on a demonstrated difference between the two cores.

**Source, not the packaged candidate.** These run the checkout's console. The
shared `build/` candidate is stale against this source and rebuilding it is not
mine to do, so a packaged run would have reported on last build's bytes. If the
cutover wants deployed-artifact evidence, that is a candidate rebuild and a
separate act.

## Two things found on the way

**Sent ordering is only newest-first across a second boundary.** `created_ts`
has one-second resolution and `list_sent` orders by `(created_ts, id)`, where
`id` is `token_hex`. Three broadcasts published inside one second came back
`third, first, second`. My first ordering test asserted the intuitive order and
failed; rather than weaken it I split it: one test waits past a second boundary
and measures the ordering rule, another measures what the same-second case
actually guarantees (all present, none collapsed). Small, but "the one you just
sent is at the top" is exactly what a human relies on after publishing.

**`tests/tui/test_tui_pty.py::test_the_packaged_harness_executes_the_candidate_when_they_differ`
now fails, caused by Checkpoint A.** It reads `/home/sl/src/baton/bin/baton-tui`
as a historical input, and the relocation moved that file out of the checkout
(`git status` shows `D bin/baton` and `D bin/baton-tui`; both are Git-tracked).
The suite was green here this morning before the move. Not fixed by me: the
choice between restoring the files from Git, rewriting the test now that the
checkout artifact cannot exist, and untracking built artifacts altogether is a
ruling, not a cleanup.

## Evidence

    ./.venv/bin/python3 -m pytest tests/tui/test_tui_sent_broadcast.py -q
    7 passed

    ./.venv/bin/python3 -m pytest tests/tui/test_tui_pty.py -k broadcast -q
    1 passed

    ./.venv/bin/python3 -m pytest tests/tui -q
    1732 passed, 1 failed   (the Checkpoint A casualty above)
