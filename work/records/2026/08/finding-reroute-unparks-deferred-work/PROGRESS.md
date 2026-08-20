# Progress

Implementer-owned. Ledger Work `W2645` (`bcbb9dbf-W2645`), created 2026-08-20
together with this dossier and bound to its canonical record path. Claimed by
`baton.claude` 2026-08-20.

## Revalidation

The observed behaviour still reproduces exactly as filed: `phase to=parked`,
then `reroute`, left the row and the `reroute` event payload both saying
`queued`.

The open question in "Proposed direction" was ruled on before I claimed
(**Confirmed decision — 2026-08-20**), and the ruling matches what the tree
independently forces. I checked the rejected alternative rather than taking
the ruling on trust, because refusing a parked reroute sounded reasonable:

- `set_phase` resolves authority through `_handler_gate`, so unparking takes
  the CURRENT route handler's authority;
- `parked` "leaves ONLY through explicit parked→queued".

So "refuse the parked reroute and require a deliberate unpark" would mean an
operator routing around an unavailable runner must first ask that runner to
unpark the Work — which is precisely the dependency-in-the-wrong-direction
that `finding-unclaimed-work-reroute` (W128) exists to remove, and it would
strand the Work exactly when moving it matters. The ruling's reasoning and
this one agree; recording it here so the next reader does not have to re-derive
why the rejected option is worse than it sounds.

Two further facts settled the shape of the fix rather than being assumed:

- `_recompute_ready` ALREADY carves `parked` out for the same reason — a gate
  arriving underneath a park does not revoke the park
  (`finding-active-work-claim` R2). So a parked Work may hold open gates, and
  the park must win over the gate derivation in `reroute` too. This fix is the
  same rule in a second place, not a new one.
- `_phase_intervals` treats the same phase recorded again as one continuing
  interval, so recording `parked` on the reroute event makes the event agree
  with the row without splitting the park into two.

## Implemented (PLAN item 2)

`src/baton_work/transitions.py` — `reroute_work` preserves `parked` and
derives through `_unclaimed_state` otherwise. `_unclaimed_state` itself is
untouched, so `pass`, `release`, recovery and readiness recomputation keep
their pinned contracts. The `live` row read in the lock gained `phase`; the
episode still mints and `_phase_now` still records, both as the ruling asks.

Nothing wakes: parked rows are excluded from the actionable projection, so the
minted episode offers the Work to nobody until the explicit resume — asserted
rather than assumed.

`docs/EFFECTIVE-BATON.md` and the `reroute` CLI help now state the contract
positively: the operation corrects WHERE and never whether the Work may run.
The guide's reroute section is the one this session added for W2571, so the
rule lands where an operator meets the operation.

## Regressions (PLAN item 3)

`tests/work/test_w2645_reroute_preserves_parked.py`, 16 cases:

- a parked reroute stays parked, in both forms — different endpoint, and same
  endpoint on a different route;
- the Route really moved while the phase held, asserted together, because a
  fix that preserved the phase by refusing to move anything would pass the
  first assertion and defeat the point;
- the recorded park reason is untouched and is not confused with the reroute's
  own `reason=`;
- the park still leaves only through the explicit resume — and the resumed
  Work is offered at its CORRECTED route;
- the reroute wakes nobody, neither the old handler nor the new one;
- the episode still starts, keyed to the reroute's own sequence;
- a parked Work holding an open gate stays parked, with the precedence stated
  as its own case;
- queued and gated reroutes derive exactly as before, the gated one keeping
  its recorded wake condition — the case W2571's restatements depend on;
- a queued reroute still DOES wake its destination, which is the contrast that
  gives the parked case its meaning;
- the event payload agrees with the committed row for all three phases,
  including `phase_now`, since the defect was visible there too;
- the preserved park reads as one continuing interval rather than two.

Confirmed non-vacuous: with the carve-out reverted, 8 of the 16 fail.

## Verification (PLAN item 4)

- `test_w2645_reroute_preserves_parked.py` — 16 passed.
- `test_w128_unclaimed_reroute.py`, `test_w103_public_docs.py`,
  `test_w104_effective_baton.py` — 58 passed with the above.
- Full v11 gate on the final tree — 2669 parallel, 51 serial, 55 ACP, all
  passed.

## Overlapping tree state

`src/baton_work/transitions.py`, `cli.py` and `docs/EFFECTIVE-BATON.md` also
carry the uncommitted W2571 change, which is out for independent review at
`baton.bug`; `tui/app.py` and `docs/BATON-WORK.md` carry W1568 and W1578. This
Work's hunks are the `parked` carve-out in `reroute_work`, the `reroute` CLI
help sentence, and the phase paragraph in the guide's reroute section. Noted so
a reviewer of any of them can see which belongs to which record.

## State

Awaiting independent review.
