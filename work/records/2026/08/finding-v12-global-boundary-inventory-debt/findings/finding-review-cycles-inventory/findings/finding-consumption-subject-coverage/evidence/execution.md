# Execution — W121034, claim121130

Question: do the two consumption ownership entries and three public probes
reach the source's real cardinality, caller and delegated identity rules,
with genuine positive/zero-match/schema controls and no changed old coverage?

From repository root:
`PYTHONPATH=v12/python/src:v12/python BATON_V12_DISK_ROOT=/home/sl/src/baton/v12/python python3 work/records/2026/08/finding-v12-global-boundary-inventory-debt/findings/finding-review-cycles-inventory/findings/finding-consumption-subject-coverage/evidence/verify-121130.py`.

Run only the six new ConsumptionEntriesReachTheirOwners controls and the new
StatedRules.test_consumption_requires_one_live_writer_before_delegating witness,
then one before/after census over the same cached source snapshot and an exact
AST/runtime preservation audit. Cumulative budget15s; the runner has a deadline
and saves logs/elapsed time in finally, including failures. Reuse accepted
reader/scanner results; no daemon, full suite or generic lifecycle-suite witness.
Retain the initial candidate/output if a correction is needed and rerun only
the newly unanswered part.

Initial run took3.043s: three controls pass, four fail on the new fixture/stimulus assumptions recorded in FINDING.md. Run the same command with verify-final-121130.py; it proves exactly the two recorded source corrections, reuses three unchanged passes, runs only the four affected controls and the first census, and subtracts initial elapsed time from its remaining deadline. All initial evidence is preserved.

## Final result

Candidatee92579485bc5074b26a83d953fc08f428723c84c459fc5750f20278b81b1d401
is retained as final-candidate-121130.py/.patch, against base-121130.py.
final-verification-121130.json retains four corrected-control passes plus the
census/audit; verification-121130.json retains the three unchanged passes and
initial failures. The exact two-line correction is audited. Combined elapsed
time6.765s is within15s, including the initial run; every log/time is retained.

The public projected-key probe performs exactly the intended attempt/generation/
active SELECT, returns empty writer_id from real SQLite and refuses at the
delegated identity validator before any full-row lookup. The stated witness
answers a genuine live subject/path/pin/custody sibling, then refuses wrong
attempt, stale generation and revoked writer before delegation. A distinct
genuine second line cannot admit a duplicate attempt/generation writer: the
real SQLite uniqueness diagnostic identifies that pair, isolating this from
the per-line active-writer index. Both malformed caller probes refuse before SQL.

Exactly two formerly unowned entries gain owners, one expected delegated pair
and three declared public pairs are added. Module unowned2→0, expected105→106,
declared100→103, missing5→3, orphan0. The remaining three pairs are nested
fence coverage; helper accounting remains separate. Global1382 entries,
731 occurrences,92 residual occurrences and all other ownership/pairs/links
are unchanged. Removing only the scheduled additive nodes reproduces the
entire accepted baseline AST. Runtime/schema/boundary hashes are unchanged.
Independent acceptance is next; this is not parent module completion.
