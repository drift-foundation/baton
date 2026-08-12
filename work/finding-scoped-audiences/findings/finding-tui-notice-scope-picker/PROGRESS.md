# Progress — TUI scoped-notice audience picker

Owner: `baton.implementer` only.

State: **APPROVED 2026-08-11 after three review passes. No changes outstanding.**

## Revalidation, before editing

The finding's "Observed" section is still exactly true of the tree today:

- `NOTICE_FIELDS = ("subject",)` — no audience field anywhere.
- `begin_compose(notice=True)` enters `MODE_NOTICE` directly; `N` never asks
  who the notice is for.
- `send_compose` calls `store.send_notice(self.participant, kind=…,
  subject=…, body=…)` with **no `scope`**, so every console-authored notice is
  global.

The core side is likewise unchanged and needs nothing: `SCOPE_RE` is
`^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*\.\*$` with a 64-byte bound, and
`validate_scope` returns the literal segments before the `*` so matching
compares whole segments (`baton.*` cannot match `baton_extra.reviewer`).
`Store.list_participants` is the registry the suggestions derive from.

## Decisions pinned before editing

1. **A dedicated mode, `MODE_PICK_SCOPE`.** Not a flag on the recipient
   picker. The finding requires the picker's purpose be explicit so a wildcard
   can never enter directed compose and a recipient can never be a wildcard;
   two modes make that structural instead of a guard someone can forget.
2. **Typing is text; Tab completes; Enter submits the typed text.** The
   recipient picker selects by letter, which cannot work here — in a combobox
   every printable key belongs to the query. So selection is Tab cycling
   through the matching suggestions into the text, and Enter submits whatever
   is typed. That satisfies "the typed text remains submit-capable" without a
   second, hidden way to choose.
3. **`*` is a value, not a mode.** It is offered as an explicit row and is a
   legal thing to type. It maps to `scope=None` at the boundary and nowhere
   else, so nothing downstream has to know the TUI spelling.
4. **Suggestions are every proper team prefix of every configured address.**
   For `a.b.c` that is `a.*` and `a.b.*` — never `a.b.c.*`, which would be an
   exact participant wearing a wildcard. Deduplicated, sorted, deterministic.
5. **The chosen audience lives outside `compose`,** beside the same boundary
   `to` uses. Compose fields are editable text; the audience was chosen and
   must survive field changes, external editing, a declined confirmation, and
   draft retention without ever being typed into a text field.
6. **The TUI validates NOTHING about the scope's meaning.** It checks the
   shape only far enough to refuse an obvious typo before the human writes a
   whole message; expansion, authorization and freezing stay in the core's
   publication transaction, and a core refusal preserves the draft and never
   falls back to global.

## Not in this item

The editor-exit-to-Send-confirmation child is separately filed and queued.
`tools/deploy.py` and any actual deployment are deferred to the next major
release by ruling. Released 1.0.0 binaries, manifests and the production
authority stay untouched.

## Implemented

`N` now asks who a notice is for, then composes.

- `MODE_PICK_SCOPE` with its own key table: printable keys type, Tab completes,
  Enter accepts what is typed, Esc cancels, Ctrl-U clears. No letter selects a
  row — there is no spare letter when the alphabet is the input, which is why
  this is not the recipient picker with a flag.
- `team_scopes()` derives suggestions from `list_participants`: every PROPER
  prefix of every address, deduplicated and sorted. `lang.deep.owner` yields
  `lang.*` and `lang.deep.*`, never `lang.deep.owner.*`.
- `submit_scope()` calls the core's own `validate_scope` — already exported, so
  no core change was needed — rather than copying the grammar into the console.
- `self.notice_scope` holds the audience outside `compose`, like `to`.
- `send_compose` maps `*` to `scope=None` at the publication boundary and
  passes a team scope through unchanged.
- The audience is drawn in the compose pane, so it is on screen while typing
  AND behind the `Send? Y/n` confirmation.

## Three defects found while building it

1. **The registry key.** I wrote `entry.get("participant")`; it is `address`.
   The suggestion list came back empty, which looks exactly like "this registry
   has no teams" rather than like a bug. The recipient picker had the answer
   twenty lines away.
2. **Tab could not reach the second candidate.** Completing `lang` to `lang.*`
   narrowed the filter to that single row, so the next Tab had nothing to cycle
   to. Completion now cycles over the matches of the typed STEM, which is what
   shell completion does and why it works.
3. **A test-file edit at the wrong indentation.** Adapting the existing notice
   preconditions, my pattern matched an indented call site too and produced a
   comment at the wrong depth, breaking an `else:` block. Caught immediately by
   a syntax error; repaired line-aware.

## Existing tests adapted — flagged, not buried

`N` used to enter the composer directly, so 13 existing driver tests reached it
that way. Their PRECONDITION changed by ruling, not their subject: each now
presses `N` then Enter to accept the default `*`, which is the audience they
were written against. No assertion was weakened or removed. Sites: six direct
`_press(... ord("N"))` calls plus one parametrized branch.

## Evidence

`tests/tui/test_tui_notice_scope.py`, 20 tests: the prefix rule without a
screen; `N` asks first; options are `*` plus teams with exact participants
absent from both the model and the drawn screen; typing filters and backspace
widens; Tab cycles; a typed `brandnew.*` submits with no suggestion; an
incomplete `lang` is refused and keeps the text; empty means everyone; Esc
composes nothing; a scoped notice reaches exactly the core's expansion and a
deep scope only its own subtree; the audience is visible while composing and
confirming and survives a declined confirmation; opening/filtering/cancelling
and a declined send leave the authority dump byte-identical; a core refusal
keeps draft and audience and never falls back global; and the picker draws
safely at 100x24, 60x12 and 44x10 with every offered option actually drawn.

Deliberate breaks, each failing named tests: the scope dropped at the publish
boundary (the original defect) → 3 tests; exact participants leaked into
suggestions → 4 tests; a refused scope silently falling back to global → 1 test.

**Scratch candidate, driven over a real PTY** —
`scope-candidate/bin/baton-tui`, `ef4bc8e0…`, built to a throwaway root:
`N` → type `web` → Tab → Enter → subject → send published one notice with
subject "live scoped notice" to exactly `web.dev` and `web.lead`, with no exact
participant shown in the picker. The released console is untouched
(`24f08cb1…`).

Full suite: 2378 passed, 3 failed — the same three frozen-artifact currency
failures, unrelated to this item and unchanged by it.


## Response to review pass 1 — the wrong-audience defect

The reviewer found the defect that mattered, and my own PROGRESS had claimed
coverage I had not written: `_draft_from_state` omitted `notice_scope`, the
version-1 schema had no field for it, and `reopen_draft` did not restore it. A
retained `web.*` notice therefore reopened with no audience, and `send_compose`
reads no audience as global — so continuing yesterday's team draft would have
broadcast it to the whole mailbox, silently, at the moment of sending.

Acceptance boundary 4 required exactly this ("survives ... draft retention,
restart/reopen") and I did not implement it. Worse, the handoff I wrote listed
"confirmation/draft/reopen/failure" as covered. It was not. That is the second
time today I have described evidence I had not produced, and it is the specific
habit to break: the claim of coverage has to be written from the test list, not
from the intent.

Fixed:

- `notice_scope` is part of the notice draft snapshot, defaulting to `*`.
- `drafts._validate` accepts it as optional text, refuses an empty string as
  damage (an empty audience is a field that lost its value, and guessing which
  audience it meant is precisely the guess that broadcasts to everyone), and
  leaves scope-less version-1 drafts loadable.
- `reopen_draft` restores it, treats a legacy scope-less notice draft as an
  explicit `*`, and — for a stored audience that no longer parses — reopens
  with that audience and says why it is unusable rather than downgrading it to
  global.
- The success status names the real audience; it said "to everyone"
  unconditionally, which was true of every notice until the audience became a
  choice.
- `notice_scope`/`scope_query`/`scope_stem` are cleared explicitly at send and
  at cancel, so an audience cannot be inherited by the next notice.

Seven further tests, bringing the suite to 27: retained-restart-reopen-SEND
verifying only the team audience at the authority; a legacy scope-less draft
reopening and sending global; an unparseable stored audience not downgraded; an
empty stored audience refused as damage; external-editor survival; the success
status naming the real audience for both scoped and global; and no inheritance
by the next notice.

Deliberate break: persistence removed →
`test_a_retained_scoped_draft_survives_restart_and_sends_to_its_team` fails.

**Live proof on the rebuilt candidate** (`776ecb49…`, throwaway root): session
one chose `web.*`, typed a subject and pressed Esc; the draft file on disk
carries `"notice_scope": "web.*"`; a second, fresh console reopened it showing
`web.*` and sent it; the authority recorded the audience as exactly
`web.dev, web.lead`.

Full suite: 2385 passed, 3 failed — the same three frozen-artifact currency
failures, unrelated to this item.

## Response to review pass 2 — the cross-version blocker

The reviewer imported the FROZEN `bin/baton-tui` directly and showed that my
version-1 file carrying `notice_scope` reopened there with the subject and no
audience — and frozen `send_compose` has no scope argument, so it publishes
globally. The first defect reached from the other side: same wrong audience,
different reader.

The lesson is the one I keep meeting: a version-1 file with an extra field is
still a version-1 file to every reader that already exists. Adding a field is
not a compatible change when the field's absence has a dangerous default.

Fixed:

- `VERSION = 2` is what this console WRITES; `READABLE = (1, 2)`.
- Version-1 notice drafts are migrated on read to an explicit `*`.
- A notice draft in the new format MUST carry a nonempty audience; without one
  its reach would be decided by whatever the reader defaults to, and that
  default is everyone.
- An experimental version-1 file that already carries an audience keeps it,
  validated like any other and never downgraded.
- The frozen console now REFUSES the newer file, which costs a human a reopen
  instead of a broadcast.

### A defect in my own migration, caught by a test I had just written

`_migrated_from_v1` tested `if draft.get("notice_scope")` — truthy — so an
EMPTY stored audience was migrated to `*`: silently turning a damaged team
notice into a mailbox-wide broadcast, precisely the downgrade the version bump
exists to prevent. It now tests for the KEY's presence. Absence means "written
before audiences existed" and has a safe answer; an empty string means "this
field lost its value" and does not.

### And a hollow pass of mine, found the same way

`test_an_empty_stored_audience_is_refused_as_damage` was green for the wrong
reason: my raw fixture created the draft directory with default permissions, so
`load` refused on the privacy check and never reached the audience rule. Both
raw fixtures now create the namespace 0700 and the file 0600 as the console
does, and the test asserts WHICH refusal it got.

## Evidence

30 tests. New: the frozen console refuses a file this one writes (imported from
`bin/baton-tui` itself, so it measures the artifact people run); the writer
advanced and still reads the old format; the storage and screen spellings of
`*` agree; an experimental version-1 audience is preserved.

Deliberate break: `VERSION` back to 1 → the frozen-refusal test and the
format test fail by name.

Full suite: 2388 passed, 3 failed — the same three frozen-artifact currency
failures. `bin/baton-tui` untouched at `24f08cb1…`.


## Approved — 2026-08-11

Both wrong-audience paths are closed: the audience survives retention, restart
and reopen, and an older console refuses a newer draft file instead of
misreading it.

What this item cost, recorded because the pattern is the point: three review
passes, and the reviewer found the two defects that would have reached a human.
Both were the same shape — a value with a dangerous DEFAULT. A notice draft with
no audience defaults to everyone, so omitting the field from the snapshot, and
later leaving the file version unchanged so an older reader saw no field, both
ended in the same broadcast. My tests covered the paths I had thought about;
his covered the readers I had not.

The habit to carry forward: when a missing value has a default, the test is not
"does the value round-trip" but "what happens to a reader that never sees it".
