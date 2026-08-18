# Finding: show three Work containment levels before unfolding

## Context — 2026-08-18

The closed W71 design intentionally limited the main Work window to a root and
its immediate children. In live use, that hid active W6 beneath visible W5;
the operator saw the parent waiting with no Handler and had no visible reason
to re-root it. Even a repaired disclosure cue would still make a common
root/child/grandchild shape require an extra navigation step.

## Superseding decision — 2026-08-18

The main Work window shows up to three containment levels: root, child, and
grandchild. This supersedes only W71's two-level visual cap. Containment still
has one parent, indentation still represents containment only, `Enter` still
opens Work details, and `u` still re-roots/unfolds the selected Work.

A visible row at the third level that contains still-deeper Work carries a
fixed `▸` more-levels icon in reserved structural space before its title. The
icon is not a dependency arrow and does not aggregate hidden Handler, Phase,
or message state onto the ancestor. Re-rooting that row reveals the next
three-level window, with the existing breadcrumb and Esc/Back behavior.

## Acceptance

- Root, child, and grandchild rows render together with unambiguous fixed
  indentation and no dependency edge masquerading as containment.
- Fourth-level-or-deeper containment never paints in the current window; its
  visible ancestor carries the unclippable `▸` continuation icon.
- `u`, breadcrumb, Esc/Back, selection, filters, closed-row hiding, narrow
  fallback, and resize remain coherent at the new cap.
- Canonical `tree` JSON and the TUI consume the same bounded window and expose
  enough progress data to render the cue without filesystem inference.
- Tests cover leaf, exactly-three-level, four-level, long-title, filtered, and
  re-rooted cases. SQLite schema does not change.

