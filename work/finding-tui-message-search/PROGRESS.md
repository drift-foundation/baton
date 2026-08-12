# Progress — TUI message search

Owner: `baton.implementer` only.

State: **SIGNED OFF IN SOURCE 2026-08-11**
(`review-2026-08-11T17-33-45Z.md`), for MESSAGES and Sent. That sign-off also
named Archived-view integration as a remaining gate; bulk archive was withdrawn
from 1.1 on 2026-08-12 and deferred to protocol 11, so the only gate left is
Slawomir's deployed-candidate trial.

(Superseded: "decisions pinned; implementation starting". Everything below was
written at that point and is history.)

Ruled by Slawomir on 2026-08-11, relayed through `baton.reviewer`: v1 is
metadata-only search over **author and subject**. Body search is out of scope
for v1. Bulk selection and trashing follow after search is reviewed and landed.

The evidence behind that ruling, from this finding's plan step 2:
`Store.preview_message` returns headers only and says why — "reading the full
text is the separate, explicit `claim and open` action, which is the only thing
that takes ownership and starts the reply/close obligation." Body text does not
exist to a reader who has not claimed the message, so a body search could only
ever have covered already-opened rows. Metadata-only is not a simplification;
it is the only scope that is honest about what it searched.

## Decisions pinned before editing

The ruling settled scope. These are the rest, decided here so they are on
record before any test hardens them. Each says whether it is mechanical or
taste — the reviewer can promote any into `FINDING.md` as ruled, and the two
marked TASTE should reach Slawomir rather than stand on my judgement.

1. **Literal substring, case-insensitive. No regex.** (mechanical) A regex
   engine in a search box turns a typo into an error state or a wrong result
   set, and every character a human types in a mailbox — `.`, `*`, `?`, `(` —
   is a literal they meant literally. Addresses are dotted: `payments.` as a
   regex matches `paymentsX`.
2. **Case folding via `str.casefold()`, matching on the composed string.**
   (mechanical) `casefold` over `lower` because it handles non-ASCII pairs a
   mailbox will genuinely contain. No normalization beyond that in v1: NFC/NFD
   folding is a real question but it is not one a v1 needs to answer, and
   pretending otherwise would put an untested claim in the help text.
3. **Filter the list in place; do not jump between matches.** (TASTE — my
   recommendation) A filtered list answers "what is there" at a glance, which
   is the question a growing retained list actually poses. Jump-to-next answers
   "take me to the next one", which is better when the list is short enough to
   already see. The alternative is defensible and cheap to switch, so it is
   flagged rather than assumed.
4. **Search applies to the active view, including Sent.** (TASTE — my
   recommendation) Both lists are the same widget over rows carrying the same
   two fields, and a search that silently stopped working when the human
   pressed the Sent key would read as a bug, not a boundary. "Author" in Sent
   means the row's other party, which is what that column already shows.
5. **`/` enters a search mode; Esc cancels and restores the unfiltered list;
   Enter accepts the filter and returns to browsing.** (mechanical) A dedicated
   mode is what makes the `n` collision moot — the finding notes `n` is compose
   in normal navigation — because typing goes to the query while the mode is
   active and no navigation key is consumed.
6. **The filter survives accepting the mode.** (mechanical) Enter leaves the
   list filtered so the human can act on a result; the status surface says a
   filter is active and how to clear it, because a filtered list that does not
   announce itself is indistinguishable from a mailbox that lost messages.
7. **Selection is preserved by row identity across refresh and across
   filtering.** (mechanical) Already how the list behaves; search must not
   reintroduce index-based selection. If the selected row stops matching, the
   selection moves to the nearest remaining match rather than jumping to the
   top.
8. **Read-only, absolutely.** (ruled, restated) Entering, typing, filtering,
   navigating and cancelling perform no claim, no seen receipt, and no other
   authority write. Search reads rows the model already loaded, exactly like
   the owed-row emphasis does.

## Isolation

Console surfaces only: `keys.py`, `state.py`, `render.py`, `tests/tui/`. No
core, protocol, schema or CLI change; the released `bin/baton`,
`bin/baton-tui` and the live authority are not rebuilt, migrated or touched.

## Implemented

`/` opens a one-line filter box; typing narrows the list on every keystroke;
Enter keeps the filter and returns to browsing; Esc clears it. Matching is
case-insensitive literal substring over author and subject, per the ruling.

- `keys.py` — `/` bound in browse (verified unbound first, like `v` and `?`);
  `MODE_SEARCH` gets its OWN small table rather than joining `_TEXT_MODES`,
  because the text modes bind Ctrl-E to an external editor, Tab to the next
  compose field and Enter to `send`. A filter box that inherited those would
  open vim on the query.
- `state.py` — `row_matches`/`row_author` as pure module functions;
  `MODE_SEARCH`; `rows`/`sent_rows` became filtered PROPERTIES over
  `_all_rows`/`_all_sent_rows`, so every display path filters without being
  told to and the setters keep all existing assignments working.
- `render.py` — the header announces the filter: `N of M matching 'q'`.
- Help lists the binding, including that it reads nothing.

### The split that matters

Filtering is a VIEW. Seven call sites needed the FULL set and now say so:
detail-metadata lookup, action-target revalidation, held-claim lookup, the
answering-row lookup, the owed count in the header, and the FIFO warning. Each
would otherwise have been a real defect — a filter that appeared to reduce
what you owe, or that made the console forget a claim it was holding.

## Three defects I made, and what caught each

1. **`row_author` returned the recipient for every inbound row.** I tested
   `to_participant` before `direction`, and inbound rows carry one too — it is
   the local participant. Every inbound row would have matched the human's own
   address instead of the sender's. Caught by
   `test_author_is_the_party_the_row_displays`.
2. **`cancel_search` silently no-opped from BROWSE.** It guarded on
   `mode != MODE_SEARCH`, so the documented way to clear an accepted filter
   worked only by the key path and not by the method. Caught by
   `test_escape_clears_the_filter_entirely`; the guard is gone and clearing
   works from either mode.
3. **A hollow test of my own.** `test_an_open_claim_survives_being_filtered_
   out_of_sight` passed even after I deliberately broke revalidation to read
   the filtered list, because it never refreshed — and revalidation only runs
   on refresh. The test now polls under the filter, which is the ordinary case
   anyway: the console refreshes every two seconds. Verified by re-running the
   break and watching it fail this time.

## Evidence

`tests/tui/test_tui_search.py`, 20 tests covering the finding's required
boundary: entry only from browse, help lists the binding from the shared key
table, matching rules including literal-not-regex and non-ASCII case folding,
author semantics in both lists, no-match/cancel/empty/backspace/clear,
selection carried by identity, refresh under a filter admitting only matches,
Sent searched too, and rendering safe at 100x24, 60x12 and 44x10.

The safety property is asserted twice over: a full public `dump()` comparison
across an entire search session, and again in the finding's own terms (the
unread row is still pending, the unseen notice still unseen).

`tests/tui/test_tui_pty.py::test_search_filters_the_list_on_a_candidate_
console` drives a real zipapp over a PTY — built into a throwaway root, never
`bin/`.

Deliberate breaks, each failing a named test: obligations counted from the
filtered view; action-target revalidation reading the filtered list.

Suites: `tests/tui` 1613 passed before the PTY addition, 1650 with
`tests/packaging` — minus one expected failure recorded below.

## The one red test, not mine to fix

`tests/packaging/test_release_version.py::test_rebuilding_reproduces_the_
checked_in_artifacts_and_manifests` now fails on `bin/baton-tui`: the console
source has moved ahead of the released 1.0.0 artifact, which is precisely what
"develop next-generation work in isolation and do not rebuild production" asks
for. The CLI still matches exactly.

Both rules are right and they cannot both hold while source moves ahead of a
frozen artifact. I did not edit that test — it is an existing test and
changing it to accommodate my own change is not mine to do. Raised for a
ruling instead.

## Response to review pass 1 — the Sent cursor index space

The reviewer was exactly right, in both directions, and the diagnosis named the
mechanism better than my code did: `sent_cursor` indexes `sent_rows`, the
FILTERED view, and I read it out of `_all_sent_rows` in two places while
`_refresh_sent` wrote a full-list index back into it.

Fixed:

- `_selected_sent_row()` reads the cursor against the list it indexes, and is
  the single place `_set_draft` and `cancel_search` capture from.
- `_refresh_sent` restores the identity by enumerating the FILTERED
  `self.sent_rows` and leaves `sent_cursor` and `sent_top` legal for that view.

## What my three new regressions actually prove

Being precise, because "three regressions added" would overstate it:

- `test_clearing_a_sent_filter_does_not_jump_rows` FAILS when the capture
  defect is restored.
- `test_a_refresh_under_a_sent_filter_keeps_the_row_and_a_legal_cursor` FAILS
  when the refresh defect is restored.
- `test_a_filtered_sent_selection_stays_on_its_row_across_keystrokes`
  documents the reviewer's repro deterministically, from constructed rows, and
  asserts the cursor indexes the drawn row after every keystroke — but it does
  NOT fail under either break in isolation. I tried three formulations and it
  still passes, so I am recording that rather than implying it catches
  something.

The constructed rows are deliberate: rows created in the same second are not
ordered stably by the authority, and my first attempt at this test put the
target at index 0, where the filtered and full index spaces agree and the bug
cannot appear. That version passed against the broken code for the same reason
the reviewer's repro needed a nonzero cursor.

## Evidence

`tests/tui/test_tui_search.py`: 23 passed. `tests/tui`: 1666 passed. No frozen
artifact rebuilt and no existing test edited.

## Response to review pass 2 — the fixture that could not fail

The reviewer found what I could not, and the cause is worth recording exactly:
`_sent_row()` gave every synthetic row the recipient `acme.reviewer`, which
CONTAINS an `m`. Search matches the other party as well as the subject, so the
first keystroke matched all three rows, nothing was filtered, and the two index
spaces stayed identical — the defect had no way to appear.

I rewrote that test three times looking for the fault in its assertions. It was
in the fixture data, one field away from where I kept looking.

Fixed: the recipient is `ops.lead`, and the test now asserts the first
keystroke ACTUALLY removed the leading row before going on. With the capture
defect restored it fails; with the fix it passes. All three Sent regressions
now catch what they are named for.

The lesson is the same one as the notice-audience item, in a new costume: a
test whose data quietly satisfies the condition under test is a test that
cannot fail, and the way to find out is to break the code and watch — which I
did, three times, without ever asking whether the FIXTURE was the reason it
stayed green.
