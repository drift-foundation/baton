# Progress

Implementer-owned.

## Revalidation against the current tree — 2026-08-20

`_event_lines` rendered `f"  roles: {', '.join(entry['roles'])}"`
unconditionally, and `_event_roles` in the projection guarantees the
array is never empty — it falls back to `["subject"]`. So every direct
Event spent a line saying it was the subject of the view it was already
in.

The relationship itself is genuinely informative elsewhere.
`_event_roles` derives `consumer`/`blocker` from paired kinds, `parent`
and `predecessor` from a creation seen from the other end,
`duplicate_target` from a close, and `parent` again from an `accept`
that created a provider. Those explain why an Event primarily about
another Work is in this history, which is not inferable from the row.

## What changed

Only the reader, and only what it says:

- `subject` alone → no row at all;
- one meaningful value → `relation: <value>`;
- several → `relations: <comma-separated>`, in the projection's own
  order rather than re-sorted;
- `subject` never appears beside a meaningful value — it is the
  implicit baseline, and `close_work` on a duplicate target is the case
  that carries both.

The canonical `roles` array is untouched. This is the reader deciding
what to SAY, not the projection deciding what to HOLD, and the suite
asserts that distinction rather than assuming it: every direct Event
still projects `["subject"]` in JSON while showing nothing.

## Superseded assertion edited

W123's `test_the_reader_shows_roles_related_and_the_whole_payload`
asserted `"roles: consumer"`. `consumer` is exactly the meaningful case
this ruling keeps, so the assertion moved to `relation: consumer` with
the reason recorded at the site. W123's point was that the typed
relationship is READABLE, not that it was spelled `roles:` — and the
rest of that case (the related row, the rationale, the whole payload)
is untouched.

## Verification

- `tests/work/test_w1217_event_relations.py` — new, **16 passed**: a
  direct Event saying nothing; create/claim/pass/close all quiet, with
  the kinds asserted so the case cannot pass by testing three Events
  that happen to be the same; the word `roles:` gone from the reader
  entirely; a dependency naming `consumer` from one end and `blocker`
  from the other, reading differently from each side with `subject`
  nowhere; a parent seeing its child's creation; a predecessor seeing
  its follow-up; the plural label keeping every value in the
  projection's order; `subject` suppressed beside both a single and a
  multiple meaningful value; the canonical array unchanged in JSON;
  the reader writing nothing; the label and every value surviving
  wrapping at four widths; and W123's `related:` rows untouched.
- Restoring the old line fails **13** of those 16, which I checked
  rather than assumed.
- The complete v11 gate, `just test-v11`, exits 0 on this tree:
  **2589 passed** (parallel), **40 passed** (serial), both bridge
  suites green.

## Two cases I built rather than found

`relations:` (plural) and `subject` beside a meaningful value are
asserted on the reader's own formatter with a constructed `roles`
array, not on an Event this authority happened to produce. Both
combinations are reachable — `close_work` with `duplicate_of` yields
`["subject", "duplicate_target"]`, and an `accept` beneath a parent can
add a second — but arranging them through the public verbs would have
made the case about the arrangement rather than about the rule. The
rule is what the finding states, so the rule is what is pinned; the
end-to-end cases beside them cover the shapes the authority produces
on its own.
