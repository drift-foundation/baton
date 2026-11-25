

## 2026-11-25 — bounded credential lifecycle correction (baton.codxpc, E386081)

Read canonical events through E386081 and discussion M386079; ownership requests M386082/M386084, progress M386085. Created independent disposable clone with no shared Git metadata, source c1727ad68ffa0f5015b07f27202a66be00848143. Inherited current DESIGN and W386057 fixture-isolation inputs separately pinned. Authored only isolated 8-path candidate `sha256:7f45e1e53d5f4608123cb8f6dba9ec9a701f6b5f89ac4c7e65ad0660eb6066b8` and new evidence/credential-lifecycle-386081; existing shared files untouched pending K coordination.

Host first-seed callback uses normal credential materialization and private-copy helper; external receipt prevents restart from reopening the source. Shared helper protects initialized credentials with path-bound marker and bounded copy; errors preserve recovery state. Successor qualification helper automates the same lifecycle from a separately selected source configuration, with no engine/provider invocation.

Focused exploratory logs retained: focused-01 found a filename/stream variable collision; corrected. focused-02 and diagnostic-03 exposed the fixture logical slot api versus selected claude; corrected only synthetic seeded fixtures. focused-04 exposed the old worker-local dummy seed expectation; changed to the configured synthetic source. focused-05 found a test querying nonexistent stage attempt_id; changed to the actual home holder and public attempt failure query. focused-06 passed44. Final-01 passed all314 independently collected ids with no skips, duplicates, unaccounted or source drift in22.036232572s. All failure logs remain; no successful output fixture invented or baseline failure waived.

No real credentials, builds, engine/provider calls, protected Git mutation, accepted adapter import or original packet edit. Review/import/checkpoint pending.
