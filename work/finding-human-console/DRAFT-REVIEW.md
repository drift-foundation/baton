# Review — retained drafts

**Outcome:** implementation approved after R1–R5 and RR1–RR3 corrections.
R6 remains a separate presentation ruling for Slawomir.

Final verification: the absent-message send, terminal-claim send, restarted
active-claim reply, and public participant-file mode regressions pass. One
non-behavioral cleanup remains before commit: `_reattach_reply()`'s docstring
still says a terminal draft stays available for the ruled follow-up path,
while the implemented and tested contract is truthful refusal with retention.
Correct that sentence; no further review round is required for the wording.

## Re-review — R1–R5 response

The principal R1–R5 corrections are real. The original independent
reproductions for missing projection, namespace/leaf symlinks, restart ID
collision, corrupt outer draft shape, and restarted active-claim reply now
pass. Two narrow corrections remain:

### RR1 — the participant file's `0600` boundary is still not enforced

The storage ruling and the first R3 review explicitly require the target file
mode. `_checked_target()` now refuses symlinks and non-regular files, but it
does not inspect the mode of an existing regular file. A participant draft
file changed to `0644` is accepted and loaded normally.

Refuse an existing file whose mode is not exactly `0600` (or document and pin
an equally strict safe-mode rule). Do not silently display private drafts from
a public file or change permissions without reporting it. Add load and save
regressions that preserve the file and its bytes on refusal.

The configured `projection_dir` itself may be treated as the explicitly
chosen root; this re-review does not broaden the ruling to reject an
administrator-configured symlink in that root path. The application-owned
hidden namespace and leaf remain the no-follow boundary.

### RR2 — terminal reply draft promises a follow-up it cannot send

`_reattach_reply()` says `"this will go as a follow-up"` when the original
claim is terminal, but it leaves the state in `MODE_REPLY` with no opened
claim. `send_reply()` cannot follow up in that state. Pressing send returns
`None` and replaces the useful warning with `"empty reply not sent"`, even
though the draft is not empty.

The first review allowed either the ruled follow-up path or a truthful visible
refusal that retains the draft. Implement one of those outcomes and exercise
the SEND attempt—not merely reopening the row. If refusing, state that the
claim is no longer held and that the draft remains; do not call a non-empty
draft empty or promise a follow-up that will not occur.

### RR3 — the absent-message branch still falls through to “empty reply”

RR1 and the ordinary terminal-row RR2 correction now pass. One equivalent
branch remains in `_reattach_reply()`: when no row with the stored `answering`
message ID exists, it sets only the one-time status
`"the message this answers is no longer listed"` and leaves
`reply_blocked` unset. Pressing send then reaches the no-claim arm and again
reports `"empty reply not sent"` for non-empty content.

Set the same persistent truthful refusal for every failed reattachment,
including an absent/expired message, and pin the SEND attempt with content.
This is reachable when local drafts outlive transient authority history. Also
update `_reattach_reply()`'s docstring: it still says a terminal draft remains
available for the follow-up path, while the chosen and now-tested contract is
truthful refusal with the draft retained.

The positive path is substantial: the eight stated UX acceptance items have
focused and packaged coverage, the draft row stays observational on highlight,
`Esc` refreshes the retained row immediately, and the existing focused draft
suite passes (`85 passed, 702 deselected`). The remaining findings are failure
and restart paths not exercised by that suite.

## R1 — a restart can silently overwrite an older draft

`draft_serial` starts at zero in every `InboxState`. `load_drafts()` restores
the list but does not advance the serial or otherwise reserve its IDs. The
first fresh composition after a restart therefore receives
`compose:new:1`; `_replace_draft()` treats it as the already-loaded
`compose:new:1` and overwrites the older draft in place.

Reproduced with a stored `compose:new:1` carrying subject `old`, a restarted
state, and one newly retained composition carrying subject `new`: the stored
list becomes `['new']`, not `['old', 'new']`.

Required regression: retain at least two fresh drafts, restart, retain another
fresh draft of each supported compose kind, and prove every prior draft and
its authoring state remain byte-for-byte intact. IDs must stay unique across
restart; malformed or duplicate persisted IDs must fail closed rather than
selecting, updating, or discarding multiple drafts ambiguously.

## R2 — a reply draft survives restart but cannot be sent

A reply draft stores `answering`, but `reopen_draft()` restores only
`follow_up_to`, mode, subject, and body. It does not restore the exact opened
message/claim relationship that `send_reply()` requires through
`_held_claim_id()`. After restart the matching claim is still active in the
authority, yet sending the reopened draft returns `None` because `opened` is
unset.

Reproduced end to end on a protocol-9 instance: claim a directed message,
retain its reply, construct a second console over the same projection
directory, reopen the draft, and send. No disposition is created.

Required regressions:

- a restarted reply draft against the participant's still-active exact claim
  can be sent and resolves that claim;
- no cursor movement can redirect it to another message or claim;
- if the original claim became terminal while the console was away, reopening
  preserves the `answering` relationship and follows the ruled follow-up path,
  or refuses visibly while retaining the draft. It must not silently turn into
  an unrelated new message.

## R3 — the ruled filesystem boundary is not enforced

`DRAFT-STORAGE-RULING.md` requires an existing absolute projection directory,
private modes, refusal of symlink/reparse traversal and non-regular
destinations, and a directory fsync after atomic replacement. The candidate
currently:

- creates a missing projection directory through `os.makedirs()` instead of
  refusing it;
- follows a `.baton-tui` symlink and writes the participant file outside the
  configured projection directory;
- follows a participant-file symlink on load;
- leaves a pre-existing `.baton-tui` directory at mode `0755` rather than
  making it private or refusing it;
- fsyncs the temporary file but never the containing directory after
  `os.replace()`.

All but the final source-inspection item were reproduced under temporary
directories. These are contract and confidentiality/durability failures, not
hardening suggestions.

Required regressions: missing projection directory; symlink at the hidden
namespace and leaf; non-directory/non-regular components; pre-existing public
namespace; target file mode; and proof that the replaced directory entry is
fsynced. Every refusal must leave both the existing draft file and the
out-of-bound target untouched.

## R4 — syntactically valid corrupt draft data is accepted

`load()` validates only the outer object, version, and that `drafts` is a
list. A valid JSON document containing `"drafts": [1]` is returned as though
healthy; the later row builder dereferences it as a mapping and can take the
console down. Duplicate IDs and malformed field types are likewise accepted.
This contradicts the ruled strict/fail-closed parse and makes corruption look
like an application crash rather than an intact file needing diagnosis.

Required regression: validate the complete version-1 draft shape and unique
IDs before returning anything. Unknown version/shape/type/identity failures
must report without echoing private subject/body text and must leave the file
untouched.

## R5 — post-commit cleanup failure leaves a resendable draft silently

`_clear_committed_draft()` removes the in-memory row and catches
`DraftError` from persistence with `pass`. The caller then reports an ordinary
successful send. If that write fails, the old draft remains on disk; a restart
shows it as an unsent draft and permits the human to publish it again.

Reproduced by failing `_persist_drafts()` only after the authority send
commits: the message exists, the UI reports success, and a second console
loads the same draft from disk.

The authority commit must never be reported as failed, because retrying could
duplicate the message. But the clean-success status is also false. Define and
pin an explicit recovery outcome that warns the human the committed draft
could not be cleared and prevents an immediate silent resend as far as local
state permits.

## R6 — ASCII completed glyph requires Slawomir's ruling

The UTF-8 draft glyph and fallback are correct: `✎` is measured as one cell
and falls back to lowercase `d`, distinct from destructive `D`. The existing
ASCII completion fallback is also `D`, however, so a completed row displays
the destructive draft command's letter. It is harmless in dispatch but noisy
and misleading.

Reviewer recommendation: use a neutral one-cell settled mark such as `=` for
ASCII completion. Do not change a previously ruled glyph without Slawomir's
answer.

## Verification performed

- Existing focused candidate tests:
  `pytest -q test_tui_drafts.py test_tui_driver.py test_tui_pty.py -k draft`
  — 85 passed.
- Independent temporary regressions: missing projection; namespace symlink;
  public namespace; destination symlink load; restart ID collision; valid-JSON
  malformed draft; restarted reply send; and failed post-commit cleanup.
  Each reproduced the finding against the current tree.
- No repository code, tests, package artifacts, staging, or commits were
  changed by this review.
