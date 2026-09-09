# Execution — claim120897

Owner120878 approves the exact proposal at Normal priority. Revalidated the
two receiver/helper/column ASTs against the retained source; implementation
binds normalized fingerprints and recomputes call spans. Existing probe bytes
and runtime remain unchanged. Reporting guidance reread and adopted.

Question: do exactly the two approved entries select their real row occurrence,
with explicit repeated-call links, while missing/stale/unclaimed witnesses
refuse and other contexts/nested rules remain visible? Retained public probes
already prove the runtime path; new controls prove the changed accounting.

Commands from v12/python, with PYTHONPATH=src:tests:.: run the new
DuplicateColumnChecksRequireOwnedWitnesses class, then the existing
HelperDeclarationsHaveExactAccounting class; run one retained verification
script for the complete pair/occurrence census and AST preservation audit.
Cumulative test/census budget15s; no broad suite or additional module coverage.
Exact invocations and outputs will be retained in evidence. Any correction
reruns only the newly unanswered control before the final census.

Final census/audit command from repository root: `PYTHONPATH=v12/python/src:v12/python python3 work/records/2026/09/finding-v12-adopted-column-owner-precedence/evidence/verify-120897.py`. Compare every entry selection and expected pair against the accepted baseline functions over one current source snapshot; retain explicit row/repeat links and all residual deltas.

## Result and exact evidence

Final candidate918f8d9a9b8d342c6ed276c49f5c84c2326312d70ecb650a63d7f961480f2e7d
is retained in final-candidate-120897.py/.patch. Base is base-120897.py.
Only three existing helpers change: _owned_here, _boundary_claims and
_account_boundary_calls. Declarations, witness helpers and11 new controls are
additive; prior tests, discovery, catalogs, stimuli and exception maps remain
exact AST. Runtime/schema/boundary implementation hashes remain unchanged.

Initial focused output/candidate are retained in focused-120897.json and
initial-candidate-120897.py: three staleness subcases encountered an earlier
span mismatch. The final helper validates all semantic fingerprints before
any source positions, so source-drift reporting is deterministic. Joined new
controls and existing declaration accounting pass21 tests in3.003s; command
and exact candidate hash are in joined-120897.json.

verification-120897.json retains the single census:1382 independent entries,
731 occurrences, exactly two entry/pair selections changed, two explicit
repeat-to-claimed-row links,92 residual occurrences unchanged. Module missing
pairs7→5 and orphan pairs2→0; nested/member debt remains visible. No blanket
row preference or source-call exemption is introduced.

Final delegate preservation adds only a covering=True condition and one control:
exact delegate queries keep baseline selection, while the two adopted entries
use covering=True. delegate-120897.json records the passing control and exact
AST comparison supporting reuse of the prior census/21 results. There are22
passing controls in total, with cumulative process execution about12.3s including
the retained initial failure, within15s. No repeated census or broad suite.
