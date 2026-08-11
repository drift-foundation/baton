# Quitting always asks once

Status: **implemented, independently approved, and confirmed by human zipapp trial**.

Parent: `work/finding-human-console/`.

Discovery context: the final live zipapp trial showed that browse `q` exits
immediately when no claim is owed, but asks for confirmation when claims are
unresolved. Slawomir ruled one predictable path instead: quitting the app
always requires one confirmation, displayed as `Exit? y/N`.

## Confirmed interaction

- In BROWSE, `q` never exits immediately. It enters the quit-confirmation
  mode and displays exactly one status-bar row:

      Exit? y/N

- `y` or `Y` exits. `n`, `N`, Enter, Esc, and every other key decline and
  return to BROWSE. The capital `N` names the safe default.
- There is exactly one confirmation regardless of whether zero, one, or many
  claims are unresolved. Confirming does not lead to a second warning.
- Unresolved claims remain protected by the confirmation and visible through
  the existing list/header state. The quit prompt does not need a second row
  that restates their count.
- Declining sets a concise generic staying status; it must not tell a user
  with zero claims to finish or close a nonexistent claim.
- In HELP, `q` continues to close help rather than starting quit. In text and
  picker/modal modes, existing meanings remain unchanged.
- Requesting, declining, or confirming exit performs no store call and no
  protocol, filesystem, or authority write.

This supersedes the old contract that `q` exits immediately when nothing is
owed and that quit confirmation needs a special two-row footer.

## Required evidence

1. Zero-claim browse `q` enters confirmation and does not exit.
2. Unresolved-claim browse `q` uses the same one-line prompt and only one
   confirmation.
3. Only `y`/`Y` exits; Enter, `n`/`N`, Esc, and an unrelated key stay.
4. Declining with zero claims produces no false claim instruction.
5. Request/decline/confirm paths make no store call.
6. Help and every non-browse `q`/Esc behavior remain unchanged.
7. Footer geometry reserves one row in confirmation mode and never hides or
   duplicates the last pane row.
8. Generated help says `q` always asks rather than only when a claim is open.
9. Packaged PTY covers both zero-claim and unresolved-claim exit flows.
10. The human handoff carries a freshly rebuilt `bin/baton-tui`.

No protocol, schema, CLI, or core change is authorized by this finding.

## Resolution

Approved by `baton.reviewer` on 2026-08-10 after one correction pass removed
four stale descriptions of the superseded conditional/two-row behavior.
Focused state/key/help/render/PTY evidence and an independent deterministic
artifact rebuild passed. Slawomir confirmed the packaged interaction on
2026-08-10. The later public-version requirement reopens the release candidate,
so release certification now follows `work/finding-release-version/`.
