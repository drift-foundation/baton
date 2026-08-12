# Progress — editor exit enters send confirmation

Owner: `baton.implementer` only.

State: **SIGNED OFF 2026-08-11 after six review passes.**

## Revalidation, before editing

The finding's "Observed" section still describes the tree exactly: `K.EDIT_BODY`
imports the body and stops, and the human presses Enter to reach `arm_send()`.
Both branches — `R`/`r` from browse and Ctrl-E inside a composition — ended in
the draft mode.

One thing the finding did not say, found by reading `edit_body_externally`:
**it returns True for an emptied body.** An editor that deletes everything is a
successful, changed import. Routing "returned true" straight to the
confirmation would therefore ask the human to approve a message the send is
about to refuse.

## Implemented

`state.arm_send_after_import()` — one named helper, called from both driver
branches:

- refuses when the imported body is empty, which is the case above;
- otherwise delegates to the existing `arm_send()`, so preflight is NOT
  duplicated. An attachment or root problem still refuses and focuses the bad
  field with the imported body intact.

The driver arms on a successful import in both branches. `abandon_fresh_reply()`
is still called only when the editor produced nothing, exactly as before.

## Existing tests adapted — each one flagged

Every edit below is a case-specific assertion whose ruled transition changed.
No assertion was weakened, and no test lost its subject.

1. `_send()` helper — skips its arming Enter when the confirmation is already
   armed. Without this, callers that had just returned from the editor would
   have pressed Enter ONTO the question and answered it. It still asserts the
   confirmation exists before `y`.
2. `test_editing_keys_do_not_disturb_the_other_bindings` — dropped the now
   superseded Enter between the editor and the confirmation.
3. `test_ctrl_e_edits_the_reply_body_and_publishes_nothing` — the mode after a
   successful import is `MODE_CONFIRM_SEND` with `send_return_mode ==
   MODE_REPLY`, which says what the old assertion meant plus the new
   transition.
4. `test_an_existing_draft_is_opened_exactly_and_never_re_seeded` — declines
   back to the draft between the two edits, because a second edit now starts
   from the confirmation.
5. `test_an_editor_failure_leaves_the_draft_untouched` — same decline before
   the failing edit.
6. `test_the_editor_key_opens_the_editor_from_browse`,
   `test_a_fresh_editor_reply_that_succeeds_is_unaffected`,
   `test_lowercase_r_goes_straight_to_the_editor` — mode assertions updated the
   same way as (3).
7. `test_an_edited_body_wins_over_the_subject_line` — its trailing "the
   ordinary confirmation still stands" Enter would now answer the question, so
   it asserts instead that nothing has been published while the confirmation is
   up. That is what the line was there to protect.
8. Two legend tests and `test_the_body_state_is_shown_rather_than_typed` —
   decline back to the draft before asserting the DRAFT's legend.
9. `test_lowercase_r_reaches_the_editor_path_on_a_real_terminal` (PTY) — one
   extra Esc to decline the send the editor now arms, and its status assertion
   changed from "draft imported" to the confirmation itself. The import status
   is genuinely replaced by the question; the body size is still on screen.

## Two mistakes of mine while writing the new tests

- I used `R` for the editor path. `R` is the quick subject-only reply; `r` is
  the full editor reply. The keys were swapped by an earlier ruling and I
  reached for the old one.
- I wrote `_press(state, store, ord("n"), _pick(state, "acme.reviewer"))`.
  Python evaluates both arguments before `_press` runs, so it asked which
  picker page a recipient was on while the console was still browsing.

## And a hollow case I caught by re-breaking

My first "emptied body" parametrization started from an EMPTY body, so the
editor handed back the seed unchanged and the import was refused one step
earlier — the non-empty guard was never reached. Removing the guard left the
test green. `test_emptying_the_body_in_the_editor_never_arms` now starts from a
body that exists, and removing the guard fails it by name.

## Evidence

New, in `tests/tui/test_tui_driver.py`: a full reply editor exit arms with
nothing written; compose and notice Ctrl-E arm identically; one affirmative key
publishes exactly once; declining restores draft, body, subject and the
original on screen, and a second edit re-arms; cancelled and unchanged imports
never arm; emptying an existing body never arms; and an attachment problem
refuses before the question with the imported body and the bad field focused.

Deliberate breaks, each failing named tests: the transition reverted to
requiring the extra Enter → 3 tests; the non-empty guard removed → the emptying
test.

**Packaged candidate over a real PTY** (built to a throwaway root): `r` opened
the editor, the console came back at `Send now? [Y/n]` with no intervening
keystroke, and a single `y` produced exactly one reply and one disposition.

`tests/tui`: 1663 passed. Released artifacts untouched.

## Response to review pass 1 — three body-boundary blockers

All three correct, and R2 is the one that mattered.

**R1 — `strip()` refused lawful content.** Whitespace-only bodies are exact
protocol content; the protocol refuses zero BYTES, not spaces. My guard decided
on the sender's behalf that their content was not content. It now tests exact
zero length.

**R2 — an emptied compose/notice body could later send a different message.**
`edit_body_externally` replaced the body with `""` and reported a successful
import; `arm_send_after_import` then refused silently, leaving a compose or
notice in its ordinary mode with a subject and no body — where the next Enter
publishes the subject-only shorthand. The human chose the full-body editor,
deleted the body, and could be sent a message they never wrote.

Fixed at the boundary rather than downstream: an exact-empty editor result is
now an immediate, visible refusal that imports nothing and preserves the prior
body. The refusal is ordered AFTER the unchanged check, so a fresh reply whose
seed was empty still reports "no changes", which is the more accurate reason.

**R3** — the docstring's superseded extra Enter is rewritten.

### My test positively accepted the danger

`test_emptying_the_body_in_the_editor_never_arms` asserted the empty buffer and
zero writes — precisely the state that makes the later wrong-message send
possible. It now asserts the body SURVIVES, that the refusal is visible, and
that a later ordinary send publishes the original body rather than falling
through to the subject alone.

That is the second time in this finding that a test of mine described the
implementation instead of the requirement.

## Existing test adapted — flagged

`test_an_empty_body_from_the_editor_refuses_rather_than_sending_the_subject`
pressed Enter twice to reach the warning at send time. Under the ruling the
refusal is visible when the editor returns, so it asserts that immediately,
then still presses Enter twice to prove nothing publishes and the claim stays
owed. Nothing was weakened.

## Evidence

New: whitespace-only bodies arm and publish their exact bytes, for reply,
compose and notice.

Deliberate breaks, each failing named tests: `strip()` restored → the three
whitespace cases; the exact-empty refusal removed → both empty-body tests.

`tests/tui`: 1669 passed.

## Response to review pass 2 — a boolean cannot say three things

All three findings correct.

**The root cause is one shape.** `edit_body_externally` returned a boolean, so
"the human explicitly emptied the body" was indistinguishable from "the editor
was cancelled". Every downstream defect followed: a quick reply that never set
`reply_body_requested` could publish its subject as the message, and a fresh
browse reply was thrown away by `abandon_fresh_reply()` along with its
inherited draft.

Fixed by making the outcome three-way — `EDIT_IMPORTED`, `EDIT_NONE`,
`EDIT_EMPTY` — and giving each its own consequence:

- IMPORTED arms the confirmation;
- NONE abandons a fresh reply, exactly as before;
- EMPTY keeps the draft and, in reply mode, sets `reply_body_requested` so the
  full-body intent survives and the later send refuses instead of publishing
  the subject line.

**Tests that measured the wrong thing.** My later-send checks compared row
counts and subjects — which a subject-only fallback also satisfies. They now
open the published message or notice through the public read path and compare
EXACT BYTES.

**The removed assertion is restored.** `test_an_empty_body_from_the_editor_...`
asserts again that the inherited `Deploy` draft survives, which the ruling
requires and which I dropped when adapting it.

## New coverage

Emptying a quick reply keeps the full-body intent and the later confirmation
refuses; a fresh browse reply emptied in the editor keeps its draft and subject;
a CANCELLED fresh reply is still abandoned (the other half of the three-way
distinction, so neither outcome can be merged into the other); emptying a
compose or notice preserves the prior body and publishes those exact bytes.

Deliberate break: `EDIT_EMPTY` collapsed back into `EDIT_NONE` →
`test_a_fresh_reply_emptied_in_the_editor_keeps_its_draft` fails by name.

## A process note on my own editing

Two of my scripted edits this round went wrong in ways worth recording: one
aborted midway and left `state.py` and `driver.py` disagreeing (57 failures),
and a two-range `sed` display made me believe a block sat inside a guard it did
not. Both were self-inflicted by editing with pattern scripts instead of
reading the region first. The method was ultimately rewritten as a whole unit,
which is what I should have done at the start.

`tests/tui`: 1674 passed.

## Response to review pass 3 — the follow-up path

Correct: a fresh browse follow-up is `MODE_COMPOSE` with `compose_is_reply`
true, so protecting only `MODE_REPLY` left it publishing the subject shorthand
after the human deliberately emptied the body.

- `compose_body_requested` mirrors `reply_body_requested` for compose and
  notice. It is set by an import AND by an explicit empty, reset by
  `begin_compose`, and persisted with the draft as `body_requested` so a
  restart cannot turn an emptied follow-up back into a quick one.
- Both subject-only fallbacks in `send_compose` refuse when it is set.
- It is NOT inferred from `compose_is_reply`, because a quick subject-only
  follow-up remains valid — pinned by its own test.

`assert state.draft == "Deploy"` is genuinely restored this time. I said it was
in the previous round and it was not.

### Another test that could not fail

My first follow-up test performed a successful edit before emptying, which set
the marker by the IMPORT path — so removing the explicit-empty assignment left
it green. The notice branch now deletes a QUOTE seed with no prior import,
which is the only way to reach the empty path cleanly, and the break fails it
by name.

That is the fourth time today a test of mine passed against broken code. Every
one had the same cause: the fixture already satisfied the condition under test.
Watching a deliberate break do nothing is the signal, and the first place to
look is the fixture, not the assertions.

### One flagged default

`body_requested` is absent from draft files written earlier in this unreleased
cycle, and its absence defaults to `False` — the permissive direction. Those
files exist only in scratch directories on this machine; the frozen console
already refuses version 2 entirely. Flagged rather than silently accepted,
because a missing value with a dangerous default is the shape that cost two
review rounds here already.

## Evidence

New: handled-message and seen-notice follow-ups emptied in the editor refuse
and preserve what was there; the quick subject-only follow-up still sends; the
intent survives retention and reopen.

Deliberate break: the compose-side assignment removed → the notice follow-up
test fails by name.

`tests/tui`: 1678 passed.

## Response to review pass 4 — persisted intent and the attachment bypass

Four findings, all correct, and the first one is a lesson I had literally just
written down and then failed to apply.

**1. Version 3.** I added `body_requested` as an OPTIONAL version-2 field and
"flagged" the permissive default in this file — one round after learning that
an optional field leaves every existing reader accepting the file and silently
dropping the protection. Flagging is not a mitigation. Writes are now version
3; version 1 and 2 are read and migrated (`body_requested` derived from whether
a body is present, which is exactly what the console did before the marker);
version 3 requires the boolean; an experimental value already present is kept
rather than recomputed.

**2. Reply snapshots** carry the marker now, and reopen restores the STORED
value instead of deriving it from `bool(body)` — which turned an explicitly
emptied reply back into a quick one across a restart.

**3. My restart test could not fail.** It kept a non-empty body, so losing the
marker had nothing to fall through to. The new test deletes a quoted seed,
leaving a genuinely empty draft, then reopens and attempts a send; breaking
serialization and restoration INDEPENDENTLY each fails it.

**4. The attachment bypass.** The refusal sat under `not body and not attach`,
so attaching a file let an attachment-only message go out in place of the
deleted body. It now refuses on an empty body whenever the intent is set,
BEFORE the attachment question — and an ordinary attachment-only compose, which
never asked for a body, still sends.

### Existing tests adapted — flagged

`tests/tui/test_tui_drafts.py`'s `_draft()` factory gained `body_requested`,
which the current format requires. One edit, fourteen tests, no assertion
touched. Two fixtures of mine in `test_tui_notice_scope.py` likewise, plus its
version assertion moving to 3 / (1, 2, 3).

## Evidence

`tests/tui`: 1682 passed. Deliberate breaks, each failing named tests: the
marker not serialized; the marker not restored; the compose-side assignment
removed; the attachment guard removed.

## Response to review pass 5 — the matrix, the reachable state, the comments

**R2 is the one worth keeping.** My attachment test reached the dangerous state
by assigning `state.compose["body"] = ""` — asserting the postcondition under
test instead of producing it. It now uses a seen-notice follow-up, whose stored
body is empty and whose quote can be deleted, so the state arrives through the
transition a human actually makes. Same fixture discipline the last three
passes needed, and I applied it to the fixture data and not to how the state
was reached.

**R1 — the migration matrix.** Seven cases in `test_tui_drafts.py`: version-1
intent derived from the body both ways; version-2 migrated the same way with
its audience intact; an experimental version-2 marker preserved rather than
recomputed (recomputing would overwrite a TRUE intent on an empty body, which
is the case the marker exists for); version-3 refusing a missing marker and a
mistyped one; an older reader refusing what this console writes; and reading an
old file then saving rewriting it as version 3.

The older-reader test patches `READABLE` on the module rather than reloading
it — a reloaded module has a different `DraftError`, so the raise it makes is
not the one the test catches. It also does NOT use the frozen 1.0 console,
which stopped at version 1 and would refuse version 2 as well: what has to be
shown is that a reader which ACCEPTED the optional-field file now refuses.

**R3 — the comments.** `_migrated_from_v1`, `_validate`, the field table, and
`reopen_draft` now describe the version-3 contract instead of the format they
replaced.

## Evidence

`tests/tui`: 1688 passed. The attachment guard break still fails the rewritten
reachable test by name.


## Signed off — 2026-08-11

Six passes. The one-line behaviour change — a successful editor exit arms the
confirmation — took four rounds of body-boundary work around it, and the
reviewer found every defect that would have reached a human.

What they all shared: the shortest path to send is only safe if "I deleted the
body" is distinguishable from "I never wrote one", everywhere that distinction
can be lost. It could be lost in five places, and I fixed them one at a time
because I kept treating each as the last:

1. `strip()` deciding whitespace was not content;
2. an empty import replacing the body and leaving a subject-only fallback;
3. a boolean return collapsing "emptied" into "cancelled";
4. reply-only protection, missing the compose-mode follow-up;
5. an optional storage field an older reader ignores.

And four of my tests passed against broken code, each because the fixture
already satisfied what the test was for — including one where I produced the
dangerous state by assigning it rather than reaching it.

The habit I am taking out of this finding: when a break does not fail a test,
the fault is in the fixture, not the assertion. And a value whose absence has a
dangerous default cannot be introduced as optional — not in a struct, not in a
file format, not anywhere a reader that predates it can still run.
