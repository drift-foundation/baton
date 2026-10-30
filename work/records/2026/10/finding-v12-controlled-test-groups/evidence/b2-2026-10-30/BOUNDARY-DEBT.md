# B2 — boundary-inventory debt as measured 2026-10-30 (before the B2 edits; HEAD carries the same numbers ±8)

## test_every_boundary_call_belongs_to_an_entry_or_is_declared: 190 entries

| domain / module | entries |
|---|---|
| intake.py (document validator calls) | 33 |
| review_cycles.py (identity validator calls) | 19 |
| review_cycles.py (document validator calls) | 17 |
| intake.py (identity validator calls) | 15 |
| review_cycles.py (text validator calls) | 13 |
| intake.py (text validator calls) | 12 |
| oci.py (text validator calls) | 9 |
| oci.py (identity validator calls) | 6 |
| review_cycles.py (generation validator calls) | 6 |
| launch.py (text validator calls) | 5 |
| oci.py (document validator calls) | 5 |
| attempts.py (document validator calls) | 4 |
| attempts.py (identity validator calls) | 4 |
| attempts.py (text validator calls) | 4 |
| workspaces.py (document validator calls) | 4 |
| posture_slots.py (instant validator calls) | 3 |
| workspaces.py (text validator calls) | 3 |
| launch.py (document validator calls) | 2 |
| launch.py (identity validator calls) | 2 |
| maintenance.py (identity validator calls) | 2 |
| provider_context.py (capability validator calls) | 2 |
| custody.py (identity validator calls) | 1 |
| exchange.py (instant validator calls) | 1 |
| exchange.py (text validator calls) | 1 |
| failure_cause.py (document validator calls) | 1 |
| failure_cause.py (identity validator calls) | 1 |
| intake.py (capability validator calls) | 1 |
| interrogation.py (text validator calls) | 1 |
| interrogation.py (injected validator calls) | 1 |
| oci.py (capability validator calls) | 1 |
| posture_slots.py (identity validator calls) | 1 |
| provider_context.py (document validator calls) | 1 |
| provider_context.py (identity validator calls) | 1 |
| review_cycles.py (capability validator calls) | 1 |
| review_cycles.py (instant validator calls) | 1 |
| sessions.py (identity validator calls) | 1 |
| source_boundary.py (text validator calls) | 1 |
| worker_entry.py (identity validator calls) | 1 |
| workspaces.py (identity validator calls) | 1 |
| workspaces.py (capability validator calls) | 1 |
| workspaces.py (deadline validator calls) | 1 |

## test_every_receiving_entry_has_an_owning_validator: 696 entries

| domain / module | entries |
|---|---|
| caller / provider_context.py | 118 |
| caller / workspaces.py | 110 |
| caller / failure_cause.py | 64 |
| caller / launch.py | 55 |
| caller / oci.py | 47 |
| caller / context_delivery.py | 37 |
| caller / documents.py | 30 |
| caller / attempts.py | 29 |
| caller / attempt_logs.py | 24 |
| caller / intake.py | 21 |
| caller / custody.py | 20 |
| caller / exchange.py | 20 |
| caller / review_cycles.py | 19 |
| injected / intake.py | 16 |
| caller / handshake.py | 14 |
| injected / authority_port.py | 13 |
| caller / source_boundary.py | 10 |
| adopted / review_cycles.py | 8 |
| caller / authority_port.py | 8 |
| caller / sessions.py | 8 |
| caller / store.py | 5 |
| adopted / provider_context.py | 4 |
| adopted / workspaces.py | 4 |
| caller / interrogation.py | 4 |
| caller / credentials.py | 3 |
| adopted / attempts.py | 2 |
| adopted / sessions.py | 1 |
| injected / attempts.py | 1 |
| injected / oci.py | 1 |

## test_every_owned_entry_has_exactly_one_probe: 266 entries

| domain / module | entries |
|---|---|
| injected / authority_port.py | 36 |
| caller / intake.py | 33 |
| caller / oci.py | 25 |
| adopted / interrogation.py | 23 |
| adopted / review_cycles.py | 23 |
| injected / intake.py | 20 |
| caller / tokens.py | 18 |
| caller / maintenance.py | 15 |
| caller / workspaces.py | 14 |
| caller / exchange.py | 10 |
| adopted / sessions.py | 9 |
| caller / attempts.py | 9 |
| caller / source_boundary.py | 6 |
| adopted / handshake.py | 4 |
| caller / attempt_logs.py | 4 |
| caller / custody.py | 3 |
| caller / review_cycles.py | 3 |
| caller / store.py | 3 |
| adopted / intake.py | 2 |
| adopted / workspaces.py | 2 |
| adopted / attempts.py | 1 |
| adopted / output.py | 1 |
| caller / provider_context.py | 1 |
| caller / sessions.py | 1 |

## test_the_missing_probe_check_can_actually_fail: 266 entries

| domain / module | entries |
|---|---|
| injected / authority_port.py | 36 |
| caller / intake.py | 33 |
| caller / oci.py | 25 |
| adopted / interrogation.py | 23 |
| adopted / review_cycles.py | 23 |
| injected / intake.py | 20 |
| caller / tokens.py | 18 |
| caller / maintenance.py | 15 |
| caller / workspaces.py | 14 |
| caller / exchange.py | 10 |
| adopted / sessions.py | 9 |
| caller / attempts.py | 9 |
| caller / source_boundary.py | 6 |
| adopted / handshake.py | 4 |
| caller / attempt_logs.py | 4 |
| caller / custody.py | 3 |
| caller / review_cycles.py | 3 |
| caller / store.py | 3 |
| adopted / intake.py | 2 |
| adopted / workspaces.py | 2 |
| adopted / attempts.py | 1 |
| adopted / output.py | 1 |
| caller / provider_context.py | 1 |
| caller / sessions.py | 1 |

Exact entries: boundary-inventory-lists.json (captured from the tests' own assertEqual operands).
HEAD (8876bf95) comparison, same tests run over `git archive HEAD`: unowned 688, unattributed 190, unprobed 266 — the debt is committed, not candidate drift.
