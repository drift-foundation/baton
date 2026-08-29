# Plan

1. Revalidate `check_input_pair`, neighboring ownership entries, the canonical boundary inventory, and the current accepted baseline. Done 2026-08-27: the manager inventory remains at its accepted six failures and the contracts inventory reports the three omitted receiver entries as the seventh full-tree failure.
2. Add exact receiver-owner and probe entries for `input_manifest`, `assignment_manifest`, and `what` in `v12/python/tests/manager/test_contracts_inventory.py`, per the dated clarification in `FINDING.md`. Done 2026-08-27; no runtime file changed.
3. Run the focused contracts inventory and confirm only the targeted omission changes. Done 2026-08-27: all 15 tests pass, replacing the one exact missing-owner failure with a clean module.
4. Run the full inventory/full v12 verification and request independent review. Verification attempted 2026-08-27: the parallel source phase collected 1,509 tests in 257 shards; all four contracts-inventory shards passed, while concurrent runtime-observation and manager-inventory changes produced 15 failures and 7 errors outside this Work, so the serial phase did not run. Independent review is next.
