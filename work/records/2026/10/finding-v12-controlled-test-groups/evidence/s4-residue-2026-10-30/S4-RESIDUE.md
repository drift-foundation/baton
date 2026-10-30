# S4 residue, first pass (2026-10-30)

Author: K under owner claim E384905 (`baton.slaw`); HEAD `84f66f43`. File:
`tests/manager/test_boundary_inventory.py` (digest in CANDIDATE-SHA256.txt).
No product change; no full suite, engine, live model, Git mutation or agents.

## Done

1. Both debt lists at once: `test_every_owned_entry_has_exactly_one_probe`
   asserts a two-key dict, so "probed, never owned" is no longer hidden
   behind "owned, never probed" (review 2026-10-30T08:20:12Z).
2. Dynamic-table misparse: `_read_table(node, origins)` resolves a formatted
   FROM operand through the bindings and treats an unresolvable one as "not a
   read". The fifteen `WHERE.*` entries of `_one_by_attempt` are gone (they
   named columns of a table that does not exist). LIMITATION, recorded
   honestly: the caller's literal (`"line_writers"`, `"review_attachments"`)
   does not resolve through the helper's bindings today, so that read is now
   not inventoried at all rather than misattributed; its columns are owned by
   `boundaries.row` with caller-supplied columns by contract.
3. Four of the nine unmatched declarations attributed: `OciAdapter.stop`
   `request.runtime_id` / `request.operation_id` → `_stopped`;
   `line_assignment_workspace` `place` → `_composed_line_roots` (DELEGATED).
4. Latent defect fixed: `_probe_covers` used `re` without importing it; the
   placeholder branch had never been reached before the stop delegation.

## Measured

`just test-group scans 32`: collected 447 (445 + the two S1 witnesses),
executed 447, passed 436, optional skipped 2, failed 9 — the same eight
pre-existing ids plus `test_every_declared_probe_reaches_its_named_boundary`
during the ONE iteration in which the stop-request probe was keyed `{what}`;
that key was reverted (reaches-boundary-after-revert.log: 115 OK), so the
failing set is the known eight again. Debt lists (script, same as the
reviewer's audit): wanted 1118, declared 1091; owned-never-probed 47 → 33;
probed-never-owned 9 → 6. Unowned receiving entries 593.

## Remaining, classified

| item | why | classification |
|---|---|---|
| `inquire`/`probe` `agent`, `deadline_seconds` (4 probed-never-owned) | validated inside the `act` closure of `_ask`; `_scope_nodes` never enters a nested function body, so no owner exists anywhere for "an interrogation deadline" and the capability check is credited only to sessions.py | INVENTORY LIMITATION: closure bodies invisible to ownership. Fix is in `_calls_in`/`_origins` (scan nested defs as the enclosing site); blast radius unmeasured, not attempted here |
| `_committed_record` `committed` (1) | the replayed journal document is owned (`boundaries.document`, subject `committed`) but `store.replay(...)` results are not modelled as crossings, so no entry exists for the probe | INVENTORY LIMITATION: replay results (20 sites) unmodelled |
| `OciAdapter.stop` `request` (1 in each list) | delegated label resolves to the placeholder `{what}`; the probe fragment is the caller's literal | INVENTORY LIMITATION: delegated labels are read at the helper's site, not resolved through the delegating call's literal |
| 32 owned-never-probed | as classified in S4-PROBES.md (composed worlds: `_destroyed_abandoned` 8, `_verdict_row` 6, `request_runtime_start` 4, `tokens.renew` 3, `checkpoint_of` 2, `_configured_gid` 2, `oci start` 2, `satisfy_gate` 2, `retentions_of`, `prepared_workspace_governance`, `release_preparation`) | probes still to author |

## Second pass — review 2026-10-30T09:29:47Z P2 (dynamic reads must stay visible)

Corrected: `_read_table(node, origins)` keeps an unresolvable formatted piece
as a PLACEHOLDER in the SQL text instead of answering None. So a static FROM
with a dynamic predicate still names its table; a dynamic FROM resolves when a
binding carries the literal; and `_one_by_attempt`'s caller-named read answers
`{table}` -- a recognised read, unresolved, visible. The real tree now shows
sixteen entries at that helper: the row read `{table}` and the fifteen columns
its callers take from the returned row (`{table}.state`, `{table}.writer_id`,
...), each owned by `boundaries.row`'s `{what}` label and each listed as
"owned, never probed" debt until the table resolves through its callers.

Regressions (`DynamicTableReadsStayVisible`, 5 OK, dynamic-table-reads.log):
static FROM under a dynamic predicate; dynamic FROM resolved through a literal
binding (both real tables); unresolved FROM is `{table}`; non-SELECT is None;
and the real `_one_by_attempt` family is PINNED (the `{table}` row entry must
exist, every entry at the site is in the placeholder family, no `WHERE`
table), so removing or hiding that read fails the inventory.

Measured after this pass: wanted 1133, declared 1091; owned-never-probed 48
(33 + the 15 placeholder-column entries now counted honestly), probed-never-
owned 6, unowned 593, entries 2302. The dynamic table's resolution through
the callers' literals (`writer_for_attempt` → line_writers,
`review_for_attempt` → review_attachments) is the next step; it needs owner
lookup to see owners that `owning_validators` records under the CALLER's site
for a helper's resolved read, which `layer_labels` (site-bound) does not today.
