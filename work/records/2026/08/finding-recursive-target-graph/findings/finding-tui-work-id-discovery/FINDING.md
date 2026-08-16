# Finding: the v11 TUI hides Work IDs required by its command bar

## Observed

During the second v11 trial, Slawomir created `Cut next v11 trial release`
through the TUI command bar and missed the transient `work_id` returned by
`create`. The Work table renders only title and workflow columns. Entering the
focused Work view also omits the stable Work id.

The same TUI asks operators to use public commands such as `block`, `detail`,
`phase`, and `say`, all of which require a Work id. Once the creation result is
gone, there is no visible TUI path to recover the identifier. The operator had
to leave the TUI surface and query JSON `home` by title; titles are not unique,
so that is not a sound identity mechanism.

## Confirmed problem boundary

A stable identifier required by the TUI's own command surface must remain
discoverable from the TUI. Transient creation output and title matching are
not sufficient. This is a usability defect, not a request to make titles
unique or to infer identity from cursor position inside the authority.

The exact compact interaction remains for implementation review: the focused
view may expose the full selected Work id, the command bar may offer an
unambiguous selected-Work reference, or both. Any solution must preserve exact
identity, work at narrow widths, and never let a stale or hidden selection aim
a mutation at different Work.

The current trial Work is `8b92cb10-W11`. This finding is queued for the next
revision; the deployed immutable trial is not modified in place.

## Superseding interaction and pre-cutover audit — 2026-08-16

The later short-selector ruling in
`../finding-local-work-selectors/FINDING.md` resolves the open interaction
choice above: Work details expose canonical `id` and authority-local
`local_id`; the Work list exposes the compact local selector. At minimum this
Work owns making the canonical selected Work id visible in its detail view;
the short-selector Work owns the broader parser/list/JSON surface.

**Confirmed by source inspection.** The current detail projection contains
the canonical `id`, but `_detail_header()` and `_facts()` render neither it nor
a local selector. This Work remains genuinely open. Showing the existing
canonical value is a TUI presentation/test correction, needs no authority
schema change, and must be completed before the fresh cutover rather than
recreated afterward.
