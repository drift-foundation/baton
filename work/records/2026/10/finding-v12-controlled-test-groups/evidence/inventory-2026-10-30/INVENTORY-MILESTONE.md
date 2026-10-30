# Inventory milestone: caller-resolved reads, closure owners, replay results (2026-10-30)

K (Claude, interactive copilot as baton.prompt) under the owner-held claim
E384905 (arrangement B); K holds no claim. Answers review-2026-10-30T17-25-53Z
("dynamic-table caller resolution, closure/replay discovery and remaining S4
probes; preserve unresolved reads as visible debt"). One file:
`v12/python/tests/manager/test_boundary_inventory.py` (CANDIDATE-SHA256.txt).
No product change, no full suite, engine, live model, Git mutation or agents.

## The three mechanisms

1. **A dynamic read is named by its callers.** `_one_by_attempt` reads
   `f"SELECT * FROM {table} ..."` and hands the row back; its return origin
   is `read:<helper>|{table}`. Now `_resolved_placeholders` fills a
   placeholder in a helper's returned read from the CALL's literal bindings,
   so `writer_for_attempt`'s member reads are reads of `line_writers` and
   `review_for_attempt`'s of `review_attachments`, both adopted rows at the
   helper's site. `_through_helpers` adds the resolved row entry through each
   delegation and records, per placeholder read, which delegations named the
   table and which did not; `receiving_entries` retires the placeholder
   family ONLY when every delegation reaching the read named it, otherwise
   `{table}` and its members stay (visible debt). The owner of a resolved
   read is recorded at the caller (`boundaries.row(found[0], what, columns)`
   seen through the delegation), so `_owned_here` falls back, for a `read:`
   stem only and only when the read's own site owns nothing for it, to
   owners recorded elsewhere for exactly that read site. Labels composed
   from a formatted string (`what = f"the line writer for attempt
   {name_value(attempt_id)} generation {generation}"`) now resolve through a
   `("label", name)` binding, at the site and through delegation, so the
   owner's label is `the line writer for attempt {name_value(attempt_id)}
   generation {generation}` rather than `{what}`.
2. **An owner inside a closure is the enclosing function's.** `_ask` owns
   the agent adapter and the interrogation deadline inside the `act` closure
   it hands to `transact`; `_scope_nodes` never enters a nested body, so the
   four interrogation entries were "probed, never owned". `_closure_pieces`
   walks nested function/lambda bodies with the enclosing bindings as they
   stood where the closure was defined, minus the names the closure binds
   itself; `_calls_in` yields their boundary calls in that context. The
   DELEGATED entries for `inquire`/`probe` `agent` and `deadline_seconds`
   resolve at `_ask`'s own site as before, now non-empty.
3. **A replayed journal document is an adopted read.** `_, committed =
   store.replay(operation_id, signature, kind=...)` decodes one of this
   manager's own committed records and hands the document back; the result
   bytes are NOT signature-bound (`ControlStore.replay` returns
   `json.loads(row["result"])`; the signature covers operands), so a corrupted
   result reaches the reader and the reader's owner is a real boundary
   (`spoiling_preparation_record` already proves it for `_committed_record`).
   `_read_table` answers the pseudo-table `replay` for a `.replay(a, b, ...)`
   call, tuple unpacking binds the document (second element) to that read,
   and every member read of it is a column entry. The `_committed_record`
   probe is re-keyed from the caller operand `committed` to the adopted
   `replay` entry.

## Measured (audit/audit-*.txt; audit/audit.py is the inventory's own
computation: `expected()` versus `all_probes()`, plus unowned entries)

| stage | wanted | declared | entries | owned, never probed | probed, never owned | unowned |
|---|---|---|---|---|---|---|
| before | 1133 | 1091 | 2302 | 48 | 6 | 759 |
| A caller-resolved reads (+composed labels, cross-site fallback) | 1137 | 1091 | 2306 | 52 | 6 | 759 |
| B closure owners | 1141 | 1091 | 2306 | 52 | 2 | 759 |
| C replay results | 1348 | 1091 | 2545 | 259 | 2 | 833 |
| D probes for the resolved rows, probe re-key | 1344 | 1106 | 2545 | 239 | 1 | 833 |

("unowned" here = receiving entries with no layer label, not in
STATED_OWNERS/DELEGATED, as the audit script counts it; the 593 quoted in
S4-RESIDUE.md used a different cut. Same script before and after, so the
deltas are exact: +74 from replay sites.)

Stage A's first cut used cross-site owners for every read stem and changed two
verdicts (`intake.py:_attempt_of` `attempts.runtime_id` and `_verdict_row`
`review_fence` lost their covering row owner to exact owners at other
sites, which the probes show is not what refuses first); narrowed to a
fallback used only when the read's own site owns nothing (audit-stageA2:
identical to before except the resolved family). Stage C's 207 newly owned
replay entries and 74 unowned ones are REAL debt, listed per site in
audit-stageD.txt and audit/replay-unowned.txt (57 replay sites; 41 own
nothing: `tokens.py:_document` 13, `_admitted_cleanup_document` 6,
`settle_restoration_execution` 4, …). The 206 owned-unprobed replay pairs
sit at 18 sites (`intake.py:_committed` 66, `admit_context_use` 34,
`abandoned_correction_of` 27, `deadlines.py:_record` 21, `_fixed_intent`
15, …): each would be a corrupted-result probe in the pattern of
`spoiling_preparation_record`. Not authored in this milestone; visible.

## Probes authored (`dynamic_table_probes`, 15)

`line_writers` row + 9 columns, `review_attachments` row + 4 columns, keyed
by the composed label's literal head (`the line writer for attempt`, `the
review attachment for attempt`); each builds `review_cycle_world` (which
already holds the revoked writer `writer-probe` and the ended attachment
`attachment-probe`), spoils ONE column of that real row behind the build's
back and drives `writer_for_attempt` / `review_for_attempt`; the reader owns
the row first (`boundaries.row` inside `_one_by_attempt`), before binding it
to its act, so the refusal carries the composed label. A first cut that
granted/attached through the public acts refused at earlier preconditions
(no configured workspace group; checkpoint not review-ready) -- a vacuous
probe `refusing` rejects, which is how it was caught (scans-group.log, first
run). NO_PROBE, by name: `runtime_attempt_id` (the read SELECTS BY it; a
spoiled value answers absence) and `assignment_generation` (strict count)
of both tables.

W375444's slice test (`StoppedSettlementInventory`) pinned an exact site set
and full ownership; replay discovery adds `stopped_settlement.py:_read` and
four UNOWNED replay entries (`_read` `replay`, `replay.operation_id`;
`status` `replay`; `settle_stopped` `replay`: the intent/outcome/receipt/
selection documents are handed on without a boundary owner). They are pinned
by name in `REPLAY_DEBT` with an assertion that they are the only unowned
replay entries in the slice and that each is still unowned, so the slice
test keeps failing on any NEW unowned entry and on silent retirement.

## Regressions (`CallerResolvedReadsClosuresAndReplays`, 7; `DynamicTableReadsStayVisible` pin updated)

Synthetic sources through the patched `_sources`: every caller names the
table → resolved rows and labels, placeholder retired; one unnamed caller →
`{table}` kept beside the named resolutions; the resolver fills only from
literals; a closure owner is the helper's owner for the caller's parameter;
a closure that rebinds the name owns its own parameter and not the
caller's; a replayed document is an adopted read its reader owns, and an
unowned reader's read is visible with no owner; plus the real-tree pins
(interrogation DELEGATED labels non-empty, `_committed_record` `replay`
owned, ≥40 replay sites, `line_writers` resolved). The S4 pin now requires
exactly `{line_writers, review_attachments}` at the helper with one
composed label each and no placeholder.

## Verification

- `just test-one` on the three discovery classes (discovery-regressions.log):
  23 OK in 5.4 s.
- `EveryProbeProvesItArrived.test_every_declared_probe_reaches_its_named_boundary`
  (focused-after-fix.log): every declared probe, the 15 new ones included,
  reaches its named boundary. `StoppedSettlementInventory` + the two
  discovery classes (settlement-slice.log): 13 OK in 13.8 s.
- `just test-group scans 32` (scans-group-final.log): see the line below.
- Remaining non-replay "owned, never probed" (33): the S4 composed-world
  list unchanged (`_destroyed_abandoned` 8, `_verdict_row` 6,
  `request_runtime_start` 4, `tokens.renew` 3, `checkpoint_of` 2,
  `_configured_gid` 2, `oci start` 2, `satisfy_gate` 2, `retentions_of`,
  `prepared_workspace_governance`, `release_preparation`, stop request).
  "Probed, never owned" is down to the one stop-request placeholder
  (delegated label read at the helper's site).

Scans group (scans-group-final.log): collected 459 = executed 459, passed
449, optional skipped 2, failed 8 — exactly the pre-existing eight ids (the
two aggregate debt tests and `test_the_missing_probe_check_can_actually_fail`,
`test_every_boundary_call_belongs_to_an_entry_or_is_declared`,
`test_every_receiving_entry_has_an_owning_validator`, `test_no_entry_is_owned_twice`,
the lanes coverage, source_boundary scratch bound, text_sweep exported-callable
table); the stop-request `{what}` reaches-boundary failure of the previous
scans run is gone. The first run of this milestone (scans-group-first-run.log,
10 failing ids) caught the vacuous probe worlds and the W375444 slice pin,
both corrected above. CANDIDATE-SHA256.txt binds the one changed file.

## Correction — review 2026-10-30T18:07:52Z (P2 false ownership in closures)

Confirmed: `_closure_pieces` walked a closure body with `ast.walk`, queued a
nested definition with its own filtered context and `continue`d -- but
`ast.walk` does not prune, so the nested body's calls were ALSO yielded under
the enclosing bindings, and an inner `agent` parameter was credited to the
outer `caller:agent` (the reviewer's nested-closure-repro.py: labels
`['inner only']`, owners holding both `?` and `caller:agent`). False coverage.

Corrected: each nested lexical scope is visited ONCE, with the bindings as
they stand at its definition minus the names it binds; the body walk is an
explicit stack that stops at nested function/lambda nodes instead of
`ast.walk`. New witness
`test_a_twice_nested_closure_is_visited_once_with_its_own_bindings`: a
twice-nested `inner(agent)` owns subject `?` only and `caller:agent` has no
owner, while a sibling `captured(connection)` still owns the enclosing
`caller:deadline_seconds` (captured-argument positive preserved). The
reviewer's reproduction passes unchanged (nested-closure-repro-after-fix.log:
labels `[]`, owners `{('capability', 'inner only', '?')}`).

Real-tree effect: NONE. audit/audit-stageE-after-closure-fix.txt is identical
to audit-stageD.txt (owned-never-probed 239, probed-never-owned 1, unowned
833, entries 2545): no package closure happened to shadow an enclosing name
with a boundary call inside, so the earlier counts stand, now on corrected
discovery. Focused: discovery + settlement slice 14 OK in 8.4 s
(closure-fix-discovery.log). Scans group rerun: see below.

Scans group after the correction (scans-group-after-closure-fix.log):
collected 460 = executed 460 (the new witness), passed 450, optional skipped
2, failed 8 — the same pre-existing eight ids, nothing new.
CANDIDATE-SHA256.txt refreshed for the one changed file.
