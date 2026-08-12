# Progress — save any message body

Owner: `baton.implementer` only.

State: **both halves SIGNED OFF IN SOURCE. The prerequisite `m` boundary
repair on 2026-08-11; whole-message save (`M`) in
`review-2026-08-11T23-26-58Z.md`. Slawomir's deployed-candidate trial is the
only gate left, and it is his to open.**

(Superseded, and left standing because it was true for most of this finding's
life: "prerequisite signed off; the finding's actual subject — whole-message
save — is not started". The paragraph below is written from inside that
period and should be read as history.)

The sequence matters and is easy to lose: `m` reaching everything viewable was
the PREREQUISITE. Saving a whole multipart message in one action, to a chosen
path, is the feature this finding is named for and it has not begun.

This file should have existed from the first pass. I wrote my implementation
record into the review journal instead — which is the reviewer's artifact, on a
boundary I had described correctly in another finding earlier the same day and
then ignored here. The reviewer cannot write this file on my behalf, and a
record kept in someone else's document is not a record I own.

## The finding, corrected before implementation

The original premise was inverted: it said `materialize` was "limited to
materializable external content". The opposite is true — `_project_part` writes
INLINE bytes and refuses external ones ("it is already a file"). I ran it rather
than reading it, and a claimed message with an inline body materialized to a
chosen directory on the first try.

The real gaps were: no whole-message save, no chosen filename, and — the one
that actually bit a human — `m` demanded an ACTIVE claim, which ends the moment
you reply or close, and which never exists for a sent message or a seen notice.
The agent CLI could save all three; the human console could not.

## Response to review pass 1 (2026-08-11T06:22Z, my own)

Recorded the inverted premise, the retention hazard in the word "any", and the
external-parts recommendation. Slawomir ruled: external parts stay references,
retention is unchanged, and anything viewable in full must be saveable.

## Response to review pass 2 (R1, dispatch)

The reviewer measured through the real `m` key and found the model widened but
dispatch still gating on an active claim — so `m` refused on an answered row
while every model test passed. Correct, and the failure is mine twice over: I
tested the method rather than the key, which is the same mistake as the packaged
Enter defect I had already been through.

Fixed by making `affordances()["materialize"]` ask the SAME predicate the model
asks, rewriting `unavailable_reason`, and correcting the stale docstring.

Two further defects surfaced in that fix, both found by the agreement sweep I
added rather than by me:

1. The affordance over-promised on an UNSEEN notice — advertised, then failed
   with "unknown id" from the core. The predicate became
   `_is_unreceived_content`: an inbound message still pending, OR a notice not
   yet seen.
2. The rule was reading `self.opened`, which is an identity (row type, id,
   claim) and carries no `state` — so "has this notice been seen" answered no
   forever. `_action_row()` resolves the actual list row.

And a third, self-inflicted: my first edit was line-spanning and missed the
affordance, so it kept reading the identity dict after every other call site had
moved to the row. `test_the_affordance_and_the_model_agree` caught that too.
Three defects in one small change, all from the same root — one question asked
in more than one place.

## Response to review pass 3

PROGRESS.md created (this file). Implementation returned unchanged, as
instructed.

## Known follow-up, deliberately not done yet

The reviewer's non-blocking note: the direct state-method refusal for an unseen
notice still uses the MESSAGE wording, while real key dispatch reports the
notice-specific wording through `unavailable_reason`. It is the same
two-places-one-question shape as everything else in this finding, so it should
be unified — but the instruction was to return the implementation unchanged for
sign-off, and quietly editing source after "no change is requested" would make
the thing being signed off different from the thing that was reviewed. Queued
for immediately after sign-off.

## Evidence

Core: `tests/core/test_core_api.py::TestAuthorizedMaterialize`, 4 tests —
messages and seen notices reachable, unseen refused; no claim required and none
created (full `dump()`); authorization unchanged with the two refusals identical
apart from the id each names; retention unchanged with nothing written.

Console model: `tests/tui/test_tui_materialize_boundary.py`, 7 tests.

Console dispatch: `tests/tui/test_tui_driver.py` — answered message saved
through the key, seen notice saved through the key, unclaimed pending refused
with no file and no claim, and the affordance/model agreement sweep across every
row shape.

Deliberate breaks, each failing a named test: the notice branch removed from the
core resolution walk; the affordance restored to demanding a claim while the
model stays widened.

`tests/tui` + `tests/core/test_core_api.py`: 1652 passed.

## Outside this finding, and unchanged by it

Three tests remain red on one cause — the core source is ahead of the frozen
1.0.0 artifacts, and the CLI manifest pins `source_sha256`, so this finding's
core addition desynchronized `bin/baton`. Not repaired here: rebuilding would
modify a released artifact in the released tree, which the isolation ruling
forbids and the branch exists to make unnecessary.

---

# Whole-message save — implementation

State: **implemented, tested, handed off for review 2026-08-11.** Claim
`b566e6c28180ae12352b41aa37c3b8af`.

## Revalidation before editing

Re-read the finding, the plan and all four review journals, then checked every
primitive the ruling names against the current tree rather than trusting the
recorded line numbers. All present and unchanged in shape: `_content_repr`,
`_publish_bytes_at`, `_open_dir_no_follow`, `authorize_read`, `_read_parts`,
`verify_attachment`, `publication_of`, `Store.materialize_authorized_part`.
Nothing in the approved contract had to be renegotiated.

## What shipped

**Core.** `Store.save_whole_message(owner_id, participant, output_path)`, and
the module-level `save_message(config, id, output, *, participant)` over it.
Every refusal it makes is made by machinery that already existed and is already
tested — `authorize_read` for who may read, retention for transient,
`verify_attachment` for external pins, `_publish_bytes_at` for no-clobber
publication through a directory opened without following symlinks. Reproducing
any of those here would have been a second answer to a settled question.

**CLI.** `baton save ID --participant WHO --output ABSOLUTE_PATH`. A separate
verb, not a flag on `materialize`: one command with two output shapes and two
naming rules is how a human ends up with a file they did not ask for.

**Console.** Uppercase `M`, its own `MODE_SAVE_PATH` one-line editor, seeded
from `projection_dir` when one is configured and empty when none is. Lowercase
`m` is untouched.

## Decisions the ruling did not cover

Four, each recorded because a reviewer should be able to overrule them without
reading the diff to find them.

**An empty container saves as `content: null`.** Removed in the pass-1
correction and REINSTATED in the pass-2 correction; the chronology is below.
The contract carries both a general rule (`_content_repr()` without
translation) and a specific one (subject-only saves as `content: null`), and
the specific one is the deliberate exception. Only a top-level container with
no parts folds; an owner with parts is emitted exactly as delivery emits it.

**A saved notice carries `audience_kind` and `selector`, not an audience list.**
The contract's field list says so and I kept it. My stated REASON was wrong and
is corrected here: I claimed a notice's recipients are derived at read time from
whoever is configured. They are not — `notice_audience` is expanded and frozen
transactionally at publication, exactly as a directed message's `publications`
audience is, so a saved list would have been accurate. The actual reason the v1
export omits it is the ruling: the selector is what the sender wrote and what
identifies the broadcast, and the export carries what was authored.

**~~The seeded filename is sanitized to `[A-Za-z0-9.-]`.~~ WITHDRAWN — see
review pass 1 below.** The transformation was a policy nobody ruled; it did not
even implement the alphabet it claimed (`str.isalnum()` accepts non-ASCII
letters); and it made the seeded name disagree with the id it names. The seed is
now the ruled `<kind>-<created>-<id>.baton.json` with both fields exactly as the
authority holds them.

**The status line is the box.** Same as `/`. The path being typed is shown
there and updated on every keystroke, and the row is tail-anchored while the
editor is open.

## Two defects the PACKAGED console found, that no source test could

Both came from running `M` on a real terminal through a real zipapp.

**The box was invisible.** `M` opened, the prompt said "Enter writes it", and
the path being typed appeared nowhere on screen — the only way to learn where
the file would land was to press Enter and find out. The model was correct
throughout; there was simply no way to read it. Fixed by putting the draft in
the status line, as `/` does.

**The last character was dropped.** With the path visible and tail-anchored,
`.baton.json` drew as `.baton.jso`. The driver writes at most `columns - 1`
cells — the standard curses bottom-right-wrap workaround — so a row filled to
the full width loses its final cell, which on a tail-anchored row is the
character just typed. The footer now truncates to `columns - 1` to match.

This is the third time the packaged artifact has disagreed with the source
tree about whether a feature exists.

## Two of my own tests were hollow

Both passed against deliberately broken code, and both are now repaired and
re-broken:

- The wrong-row test moved the cursor while `state.opened` still pinned the
  target, so re-resolving the row at Enter changed nothing. Rewritten in the
  SENT view, where a row is readable without being opened and the selection is
  the only thing naming it. Its docstring now says plainly that the cursor is
  moved directly, and why that is the only honest way to write it.
- The preview-boundary tests were satisfied by the dispatch gate alone, so
  removing the model's own check was invisible. A second test now reaches past
  the gate to the model, and a fourth break confirms the gate is load-bearing
  too. One rule, asked in two places — which is the arrangement, not an
  accident.

## Evidence

`tests/core/test_core_save.py`, 29 tests: the document shape and everything
deliberately absent from it; byte-identical saves across a lifecycle change;
canonical serialization; contentless and multipart; notices; external parts as
references with a damaged pin failing closed and writing nothing;
authorization indistinguishable from an unknown id, for messages and unseen
notices alike; the sender's own mail; transient refused before the destination
is opened; nothing written to the authority; envelope agreement with `dump()`;
path safety — relative, non-canonical, missing parent, symlinked parent,
symlinked destination, existing file, FIFO, no scratch left behind; large and
binary bodies; the CLI; and a CANDIDATE PACKAGED CLI built to a throwaway root,
run with no `PYTHONPATH` and no repository on the path.

`tests/tui/test_tui_save_message.py`, 22 tests, every one driven through the
real key: the editor opens and only from browse; the preview boundary in both
places; no selected part needed; no projection directory needed; command
letters are text inside the box; backspace and Ctrl-U; Esc; the empty-path
refusal, distinguishable from the box's own prompt; writing; a refusal keeping
the box and the target; the target being the row `M` was pressed on; resume;
no clobber; seen and unseen notices; the seeded name; sent mail; the help
entry; and the two rendering tests the packaged console forced.

`tests/tui/test_tui_pty.py::test_M_saves_a_whole_message_on_a_candidate_console`
— a real PTY, a real zipapp, a real file on disk.

Deliberate breaks, each failing named tests: the transient refusal removed; the
external-pin revalidation removed; mutable `state` added to the exported
envelope; the canonical-path check removed; the target re-resolved at accept
time; a refusal dropping back to the list; the model's boundary removed; the
affordance's boundary removed; the seeded name left unsanitized; the
`MODE_SAVE_PATH` key table removed.

## Two existing tests changed, and why

Against the standing rule, so flagged for a ruling rather than buried.

`tests/tui/test_tui_driver.py::test_the_effectful_events_are_exactly_these` and
`::test_nothing_advertised_refuses_for_want_of_state` are exhaustive REGISTRIES
— one asserts the complete set of destructive events, the other maps every
affordance to its legend label and fails on a `KeyError` for any name it does
not know. Neither can accept a new writing key without being extended. The
first one's own docstring says so: "If a new key is wired to something that
takes ownership or writes, it has to be added here deliberately — and this test
is the thing that forces the decision to be made rather than skipped."

Each gained exactly one member (`SAVE_PATH_ACCEPT`, `save_message`). No existing
assertion was weakened or removed. If the preference is that even this needs
case-specific authorization, say so and I will revert both and carry the
addition some other way.

## Not done, by instruction

Nothing deployed or activated. `bin/baton`, `bin/baton-tui`, their 1.0
manifests, the live authority and config, and Git state are untouched;
verification used candidate artifacts built to throwaway roots. No bulk
archive/restore work was begun.

## Response to review pass 1 — all seven corrections

**R1 — Enter now writes the EXACT path typed.** `accept_save_path()` applied
`.strip()`, so a lawful filename ending in a space wrote a different name than
the one on screen — in the one box whose entire purpose is that those two agree.
The draft goes to the core unchanged; empty, relative and noncanonical are all
the core's to refuse, and a whitespace-only path now reaches that refusal rather
than being rewritten into the empty-box message, which is true of a different
situation.

**R2 — `//x` is refused.** POSIX reserves exactly two leading slashes as
implementation-defined, so `normpath` preserves that spelling and my
normpath-only check called it canonical. Fixed in `save_whole_message` AND in
`_open_dir_no_follow`, which is where the rule belongs: it is the canonical
path-walking primitive, and leaving it there would have let every other caller
keep two canonical names for one directory. Tightening it broke no existing
test.

**R3 — the content representation is no longer translated.** I folded an empty
container to `null`. The contract says `_content_repr()` without translation,
and the branch was unreachable anyway: `content_type` is NOT NULL on both owner
tables, so no stored owner has null content. A subject-only message now exports
its empty container, and a new test asserts the saved content equals the
DELIVERED content exactly — nested containers, dispositions, part names and all
— so one representation serves both paths.

**R4 — the notice-audience rationale was false and is corrected** in the source
comment, the test docstring, and the decisions section above. `notice_audience`
is frozen transactionally at publication; the omission is the ruling, not a
limitation. A test now asserts the frozen rows EXIST in the authority while the
export deliberately omits them, so the distinction is recorded rather than
implied.

**R5 — the model guard now uses the same words dispatch does.** It called an
unseen notice an unopened message. It asks `unavailable_reason("save_message")`
now — one source for the wording, not two — and the direct-guard sweep asserts
both unreceived shapes and their row-kind-correct text.

**R6 — the README says "no save timestamp"** and states plainly that the
message's own immutable `created_ts` is present and required.

**R7 — the seeded name is the ruled spelling, untransformed.** `str.isalnum()`
does not implement `[A-Za-z0-9.-]`, so the code never matched its own claim; and
the transformation was speculation about a future id scheme rather than anything
ruled. The test now asserts the exact ruled name and that the id is readable in
it.

### Acceptance regressions added

Nested multipart with mixed disposition and `part_name`, compared field for
field against the delivery envelope; every external reference field including
binding generation and size, compared against the delivery pin; transient
refused at pending, claimed, answered and scrubbed, for recipient and sender
alike, with durable saving at all four states as the control; complete `dump()`
equality before and after saving, not selected table counts; the publication
race at the chosen output path, including the honest finding that an
exact-bytes race is still a refusal because the resume check runs before the
scratch file exists — the refusal says "rerun to verify/resume" and the rerun is
what resolves it; and the console row shapes that were missing — answered and
closed inbound, an authored notice saved without a seen receipt, and a transient
row where `M` is offered and the CORE refuses, because the retention rule lives
where the contract lives and a second copy in the front end is one refactor from
disagreeing with the first.

### Evidence

`tests/core/test_core_save.py` 34 + `tests/tui/test_tui_save_message.py` 27:
**61 passed**. Candidate packaged-console PTY save: passed.

Deliberate breaks, each failing named tests: `strip()` restored; the
doubled-root refusal removed; the empty-container translation restored; the
stale unopened wording restored in the model guard; the seeded name transformed
again.

### Still open

The existing-test authorization for the two exhaustive registries in
`tests/tui/test_tui_driver.py`. Neither was touched further in this pass, and
both remain at their one-member additions pending Slawomir's ruling.

## Response to review pass 2 — the contentless representation, restored

One correction, and it reverses one I made in the previous pass at the
reviewer's instruction. Recorded in sequence rather than tidied away, because
the sequence is the useful part:

1. I shipped the empty-parts normalization as an unruled decision, flagged it
   as such, and gave a bad reason for it — that storage's distinction was
   meaningless to a reader.
2. Review pass 1 read the contract's general "without translation" rule as
   overriding, and asked me to remove it. I removed it, and wrote a
   confident-sounding rationale for the removal that was also wrong.
3. Review pass 2 withdrew that instruction: `FINDING.md` carries the specific
   rule "Subject-only/contentless messages save with `content: null`" as the
   deliberate exception to the general one, and it now says so explicitly.

So the code is back where it started and the reasoning is finally right. The
empty `multipart/mixed` container IS Baton's internal sentinel for "no
content" — `content_type` is NOT NULL on both owner tables, so there is
nowhere else for the absence to live — and the v1 export says the absence in
JSON's own vocabulary instead of passing the sentinel through.

The normalization is NARROW, and that is now pinned from both sides. Only a
top-level container with no parts folds. An owner with parts is emitted exactly
as the delivery path emits it, which the field-for-field delivery comparison
added in the previous pass proves.

### Evidence

`tests/core/test_core_save.py` 34 + `tests/tui/test_tui_save_message.py` 27:
**61 passed**.

Deliberate breaks, both directions, each failing named tests: the normalization
removed → `test_a_subject_only_message_saves_with_null_content` and
`test_M_needs_no_selected_part`; the normalization WIDENED to every owner → ten
tests including the delivery comparison, the lifecycle matrix, the binary
round-trip and the packaged CLI. A one-sided break would have left "narrow"
unmeasured.

### Still open

The existing-test authorization for the two exhaustive registries in
`tests/tui/test_tui_driver.py`. Untouched again this pass.

## Where this stands

**Functional implementation ACCEPTED by review 2026-08-11.** The reviewer
requests no further implementation, documentation, representation, path-safety,
authorization, retention, CLI, TUI or regression correction. Independent
verification: 62 tests — all 34 core save tests, all 27 console save tests, and
the real candidate-zipapp PTY save.

**Sign-off is withheld on one gate, and it is policy rather than behaviour:**
Slawomir's case-specific authorization for the two one-member additions to the
exhaustive registries in `tests/tui/test_tui_driver.py`. I made those edits
before asking, which was mine to raise first and I did not — I flagged them
only in the handoff, after the fact.

Both alternatives were examined and both trade the policy violation for a
correctness regression in the property the tests protect:

- omitting `SAVE_PATH_ACCEPT` from `keys.EFFECTFUL` classifies a key that
  writes a file to disk as non-destructive, which is the defect that test's own
  docstring records having been fixed for `DISCARD_DRAFT`;
- omitting `SAVE_MESSAGE` from the driver's `_AFFORDANCE` map restores separate
  model and dispatch predicates — the exact split that left lowercase `m`
  broken after a model-only fix, twice.

The reviewer found no technically honest workaround either, and recommends
authorizing exactly those two edits and no other existing-test change. If the
ruling goes the other way I will revert both and implement whichever
alternative is preferred, and record the resulting weakening here rather than
leave it to be rediscovered.

Nothing is deployed, activated or committed. `bin/baton` is `8798de0c…` and
`bin/baton-tui` is `24f08cb1…`, unchanged.
