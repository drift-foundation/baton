# S4 — probes for already-owned entries (owner M384898)

Author: K (interactive copilot under the owner-held claim E384883), 2026-10-30.
Edits: `v12/python/tests/manager/test_boundary_inventory.py` only. No product edit.
Every probe drives the REAL public entry (or adopted read) with exactly one
operand or column spoiled and requires the owner's own refusal label through
`refusing`; a probe that met an earlier precondition was withdrawn or composed
the deployment fact the entry legitimately demands, never weakened.

## What was done

1. **Probe-key matching** (`_probe_covers`, `_unprobed`, `_unowned_probes`).
   The owners' labels are resolved through the caller's context (`the claim
   answer's identity`), while 40 existing probes were keyed by the fragment
   the code says (`'s identity`) — the same relation `test_every_declared_
   probe_reaches_its_named_boundary` asserts of every probe (`fragment in
   full`). The three wanted-versus-declared comparisons now use that relation
   (and the placeholder form `{what}, when it is given,` → its literal
   fragment); the probes themselves are unchanged and still drive the same
   owners. This is a harness key-spelling correction, not a new claim.
2. **Probes authored** (`w384870_probes`, extended `intake_probes` and the
   interrogation derivation): intake public doors (cleanup_of,
   abandonment_cleanup_of, gate_discharge_of, abandoned_gate_discharge_of, the
   two discharge gates incl. `port`, fence_pre_attach_abandonment,
   abandon_attempt, inaccessible_output, reclaim_expired_resource,
   settle_revoked_resource, reclaim_operation_id) and the collect/intake
   operation members; interrogation columns at both reading sites; tokens
   (Governance, acquire envelope and members, admit/settle activation,
   renew execution/operation, unresolved, release cessation and members);
   workspaces (identities, container, storage place, line id); maintenance
   (all six public functions, `prepare` with its configured group, store and
   custody root composed at run time); exchange and attempt_logs deliveries
   and documents; store.open_readonly; custody.clear_custody_hold operands;
   source_boundary marker/document; provider_context run_id; review_cycles
   release_writer and restoration retention digest; agent-session row
   columns; the three intake destroy endings' provider members (full closed
   envelope, non-text spoiled state); the retained profile's postures; oci
   command documents/members and vectors.
3. **Exemptions added to NO_PROBE, each justified by the file's own rules**:
   `count` columns SQLite will not let a writer spoil (attempts.activity_bytes,
   assignment_generation at three readers, agent_sessions.generation,
   interrogations.assignment_generation ×2, interrogations.session_epoch);
   columns a read SELECTS BY (interrogations.operation_id at `_row`,
   runtime_attempt_id and posture at `interrogations_of`, `_row`
   runtime_attempt_id; agent_sessions.posture and runtime_attempt_id at
   `_session_row`); exchange.command_document `attempt_id` (owned twice by one
   text rule: `_value` refuses first under its own label, so the identity
   label is unreachable; `_value`'s probe stands).

## Measured effect

| list | before S4 | after S4 |
|---|---|---|
| owned entries with no probe | 266 | 47 |
| declared probes not reaching their owner | 0 | 0 |
| receiving entries with no owning validator | 597 (after S1) | 597 |
| boundary calls attributed to no entry | 182 (after S1) | 182 |

`just test-group scans 32` after S4: collected 445 = executed 445, passed 435,
optional skipped 2, failed 8 — the six remaining boundary-inventory ids plus
the two pre-existing singletons (test_source_boundary scratch bound,
test_text_sweep exported-callable table); identical to before S4.

## The 47 remaining, classified (per-case; none papered over)

| entries | why no probe yet | classification |
|---|---|---|
| review_cycles `_one_by_attempt` `WHERE.*` (15) | the read is `f"SELECT * FROM {table} WHERE …"`; the inventory's `_read_table` drops the formatted table and takes `WHERE` as the table name, so these subjects are not real columns | inventory attribution defect (S1-type); fix is in `_read_table` (resolve the literal table bound by each caller) |
| review_cycles `_verdict_row` JSON members (6), `checkpoint_of` fence.intent (2) | members inside JSON columns; need a world holding a verdict / checkpoint row to corrupt | probes to author with a composed review world |
| intake `_destroyed_abandoned` members (8) | no abandonment destroy driver exists (the other three endings have `destroying*` helpers) | probes to author with an abandonment world |
| intake `retentions_of` retentions.retain_operation_id (1) | column probe for the retention row | probe to author |
| workspaces `_configured_gid` meta, meta.value (2) | adopted configuration record read | probe to author (spoil the recorded group document) |
| workspaces release_preparation `why` (1), prepared_workspace_governance `permission` (1) | reachable only with a PreparationOwnership / a governance state | probes to author with that state, or per-case decision |
| attempts request_runtime_start adapter.mounts.* (3), govern (1) | composed start world with a real adapter mount list | probes to author |
| tokens renew seconds, token, token.domain (3) | the token document is typed after store reads | probes to author with a held token |
| authority_port satisfy_gate, satisfy_gate.kind (2) | needs a fenced, observed-absent attempt and a spoiled discharge answer | probes to author with the fence world |
| oci start request.labels.{participant, runtime_attempt_id} (2) | refused by the labels rule (`a runtime's labels needs …`), which the inventory covers under the request label | inventory covering limitation; per-case |
