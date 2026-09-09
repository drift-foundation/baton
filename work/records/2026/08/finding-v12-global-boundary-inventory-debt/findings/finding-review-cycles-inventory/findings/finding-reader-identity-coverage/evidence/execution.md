# Execution — W121031, claim121055

Question: do exactly the two new reader entries forward to their real identity
owners and public probes, preserving all existing inventory semantics? The
new six-control class covers exact source forwarding, ownership, actual
catalog closures before SQL, valid lookup/absence, wrong-boundary rejection,
and successful reads of a genuinely committed lifecycle.

Run the retained verify-121055.py from the repository root with
`PYTHONPATH=v12/python/src:v12/python BATON_V12_DISK_ROOT=/home/sl/src/baton/v12/python python3 work/records/2026/08/finding-v12-global-boundary-inventory-debt/findings/finding-review-cycles-inventory/findings/finding-reader-identity-coverage/evidence/verify-121055.py`.

It runs only the six new controls and one before/after global census over the
same accepted source snapshot, proves exactly two additive owners/probe pairs,
unchanged residual occurrences and all prior AST, and saves candidate/patch
and output once. Combined process budget15s; no daemon or broad suite. Reuse
accepted fixture/scanner tests. If a new control fails, retain its output and
candidate and rerun only what the correction makes necessary.

Initial six-control run passed five and found only a list/set expectation error in the new ownership control; preserved in verification-121055.json. Correct that one assertion, reuse the five unchanged passes, and run the same command with verify-final-121055.py for the corrected control and the first census. The final runner proves the exact single-line difference from the initial candidate and combines elapsed budgets.

The corrected ownership control passed, then verify-final-121055.py stopped at line106 (`assert before_resolved == after_resolved`). The unchanged accounting omits already-claimed lexical occurrences from its resolution map; two new direct delegated claims can replace prior declaration links without changing residuals. This was an overstrict new audit expectation, not a runtime/scanner change. Preserve the failed runner/candidate; run only audit-121055.py to enumerate and require exactly that transition, retaining every other link. No tests or product changes are repeated. The failed audit exited before recording elapsed time, so exact cumulative timing is unavailable; final follow-up is bounded to5s and the timing limitation is reported.

## Final result

Candidate912cce9a3fcd6b26c8cab3b36418ff35b0db3f2d6a91d3d6e895aef80dbb9532
is retained as final-candidate-121055.py/.patch. audit-121055.json proves every
existing AST node is preserved after removing exactly two added mappings,
two added probe entries and the new six-control class. Runtime/schema/boundary
hashes match accepted evidence. Initial five passes are retained; the corrected
sixth passed before the first follow-up reached its audit assertion. Its runner
and failure are retained, though that follow-up did not save its test log or
elapsed time before exiting. This is an evidence/timing limitation, not an
exact cumulative-budget success claim.

The final audit command was the documented environment/script invocation with
`timeout 5s env` and audit-121055.py. It passed in3.616s; initial recorded time
was2.935s. It finds exactly ONE declaration-resolution replacement, clarifying
the possibility described above: `_verdict_row` identity at source211 is now
directly claimed by verdict_of, so its old link to integration_checkpoint is
no longer necessary. Every remaining resolution and all92 residual occurrences
are unchanged. No scanner behavior changed.

The152 module entries now have two unowned instead of four; expected pairs
103→105 and declared98→100 grow by exactly the two reader pairs. The same five
missing/no orphan pairs remain. Global1382 entries/731 occurrences and all
other ownership/pair selections are preserved. Independent review of this
reader result is next; parent coverage and joined acceptance remain open.
