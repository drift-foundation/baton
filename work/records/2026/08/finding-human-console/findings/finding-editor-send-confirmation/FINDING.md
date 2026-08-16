# Successful body edit should enter send confirmation

Parent: `work/records/2026/08/finding-human-console/`

Status: **required for 1.1 by Slawomir on 2026-08-11; source implementation
signed off on 2026-08-11.**

Reported and ruled by Slawomir on 2026-08-11:

> when exiting body edit from editor, we should already enter Send Y/n, not
> require another ENTER and then prompt to send. After email body is edited, we
> want shortest path to send.

## Observed

The external editor currently imports a successful body and returns to
`MODE_REPLY`, `MODE_COMPOSE`, or `MODE_NOTICE`. The human must then press Enter
to call `arm_send()`, see `Send now? [Y/n]`, and press Enter/`y` again to
publish. A full-body path therefore requires an editor exit plus two console
keystrokes even though exiting the editor already completes the edit step.

The split lives in `src/baton_tui/driver.py` under `K.EDIT_BODY`:
`edit_body_externally(edit_fn)` imports only, while `arm_send()` is reached by a
later Enter event. Existing driver tests explicitly assert the old intermediate
compose mode and extra Enter.

## Confirmed contract

- A **successful, non-empty** external body import immediately arms the existing
  send confirmation. The first console state visible after editor exit is
  `Send now? [Y/n]`.
- Editor exit still never publishes by itself. The human must affirm with
  Enter/`y`; save-and-quit muscle memory remains separated from network send by
  one explicit confirmation.
- `n`/`N`/Esc from that confirmation returns to the same draft, mode, field,
  body, recipient, attachment, reply/follow-up context, and original-message
  display exactly as the existing confirmation contract requires.
- Editor cancellation, nonzero exit, signal, unreadable/replaced temp file,
  empty-body refusal, or unavailable editor does **not** arm send. The draft and
  visible failure remain unchanged.
- `arm_send()` preflight remains authoritative before the question. If an
  attachment/root problem exists after the body import, the console reports it
  and focuses the bad field instead of asking a confirmation it cannot honor.
- The transition applies to every lawful external-body entry path: full
  reply/follow-up from browse, Ctrl-E inside reply/compose, and notice body
  editing. It does not change subject-only quick compose, direct publish
  semantics, retention, claims, or the core.

## Superseded parent text

The parent finding's external-editor section says: “The ordinary Enter and
`Send now? [Y/n]` still stand.” The **extra Enter after a successful editor
return is superseded** by this ruling. The confirmation itself and the rule
that editor exit never publishes remain current.

## Recommended patch boundary

Keep this in the TUI transition layer. After `edit_body_externally(edit_fn)`
returns true, route through the existing `arm_send()` rather than duplicating
its preflight or constructing confirmation state directly. The browse full
reply path must still call `abandon_fresh_reply()` only when the editor did not
produce a successful body.

Expected code/test surface:

- `src/baton_tui/driver.py`: successful `K.EDIT_BODY` transitions;
- `src/baton_tui/state.py`: only if a small named transition helper prevents
  branch drift; do not duplicate send preflight;
- driver and packaged PTY tests for reply, new compose, notice, decline,
  cancel/error/empty, and attachment-preflight refusal.

## Acceptance boundaries

1. Full reply: successful editor exit shows the send confirmation without an
   intervening Enter and writes no disposition/message yet.
2. Compose and notice Ctrl-E behave identically.
3. One affirmative key then publishes exactly once through the existing path.
4. Decline restores the full draft/context and allows another edit or later
   send.
5. Cancel/error/empty editor results never enter confirmation and never write.
6. Invalid attachment/root preflight refuses before confirmation and preserves
   the imported body.
7. Released 1.0.0 artifacts/manifests and the production authority/config stay
   untouched; verification uses a next-generation candidate artifact.

## 1.1 inclusion ruling — 2026-08-11

Slawomir explicitly required this behavior in 1.1 and asked to be contacted
only if an unresolved product decision appears. The contract above is complete;
no current product answer blocks implementation.

## Independent review — 2026-08-11

Changes requested in
`review-2026-08-11T17-19-48Z.md`. The ordinary confirmation transition is
correct, but the import boundary currently strips lawful whitespace-only
content and permits an emptied compose/notice body to fall back to a later
subject-only send. Empty editor output must warn immediately, preserve the
draft/full-body intent, never arm, and remain unable to publish a different
message through a later ordinary send. The implementation docstring also
retains the superseded extra-Enter statement.

## Independent re-review — 2026-08-11

`review-2026-08-11T17-31-16Z.md` accepts exact-whitespace handling and the
docstring correction but requests further empty-refusal work. An explicit
empty result inside a quick reply still leaves full-body intent unprotected and
can later publish the subject shorthand. A fresh browse empty refusal is
collapsed with cancellation and abandons the provisional draft; the existing
draft-preservation assertion was removed rather than satisfied. The new later-
send and whitespace tests also count rows/subjects without verifying published
body bytes. Distinguish the edit outcomes, preserve draft/context and intent,
restore the old assertion, and prove exact published content across every
ruled path.

## Independent re-review 3 — 2026-08-11

`review-2026-08-11T17-46-30Z.md` accepts the three-way edit result and exact
published-byte checks but finds the omitted fresh follow-up path still unsafe.
An emptied handled-message/notice follow-up is compose-mode, so it receives no
`reply_body_requested` protection and a later send can publish its inherited
subject shorthand. Add a distinct compose full-body-intent marker, preserve it
through retain/reopen, keep quick follow-up valid, cover both browse follow-up
sources, and restore the still-deleted assertion in the original empty-reply
test.

## Independent re-review 4 — 2026-08-11

`review-2026-08-11T17-57-46Z.md` accepts the in-session compose follow-up marker
and restored assertion but requests storage and attachment corrections. The
safety-critical field was added to draft version 2 without a bump, reply drafts
still lose it on restart, the restart test retains a non-empty body and cannot
expose fallback, and an attachment bypasses the marker. Move to required
version-3 records with v1/v2 migration, persist reply and compose intent, prove
the genuinely empty follow-up/reply restart cases, and keep ordinary
attachment-only compose valid while refusing attachment-only fallback after an
explicit empty body.

## Independent re-review 5 — 2026-08-11

`review-2026-08-11T18-16-29Z.md` accepts the corrected version-3 source,
reply/compose persistence, genuinely empty restart refusal, and attachment
guard, but requests the migration/validation regression matrix required by the
previous review. The existing frozen-reader case exercises version 1 rather
than the version-2 reader this bump must exclude. The attachment negative case
must also reach its empty requested-body state through a real quoted follow-up
rather than direct state mutation, and stale version-2/optional-marker comments
must match the current contract.

## Independent re-review 6 — 2026-08-11

Source implementation is **signed off** in
`review-2026-08-11T18-25-02Z.md`. Version-3 migration/validation, persisted
reply and compose intent, genuinely empty restart refusal, the reachable
attachment refusal, ordinary attachment-only compose, and the immediate
post-editor confirmation transition are covered and green. Final candidate
build and human soak remain release-umbrella gates.
