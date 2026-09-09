# Progress

No implementation yet. Created with W120587 under parent claim120575.
The child author appends execution and evidence after claiming this Work.

## 2026-09-08 — baton.tuner, claim120598

Read the exact child record and source fresh after claiming. The accepted
bc1844e7 test baseline and original review_cycles/schema hashes match
`evidence/baseline-120598.json`; saved the exact base before editing.
Implemented the pinned one-branch returned-row correction and seven additive
controls. The positive key control uses the unchanged ended-attachment fixture:
it passes row adoption and reaches the later real active-current-review guard.
That later refusal is not accepted as a malformed-row probe. Neither it nor
the absent-row precondition may satisfy the unchanged probe guard.

Verification question and budget, recorded before execution: does this exact
fixture reach the public attachment adoption without damaging lookup/storage,
factory restoration, wrong-boundary guards or the other attachment probes?
Run `PYTHONPATH=src:tests:. python3 -m unittest
tests.manager.test_boundary_inventory.TheAttachmentKeyProbeReachesAdoption`
from v12/python, then one bounded script selecting all existing
review_cycle_probes whose entry site is review_cycles.py:_attachment_row,
each on a fresh fixture. Cumulative budget15s; no other module or aggregate
campaign. The evidence runner retains both stages, candidate bytes and scope
audit. Existing accepted writer/lane/scanner results need no ritual rerun.

### Results and handoff

Initial run: six pass, one new positive-control expectation fails because the
real finalization journal refuses a differing reason before the anticipated
later ended-review guard. FINDING.md explicitly supersedes that expectation.
Retained initial bytes/output; corrected only the new positive control and
clarified its companion guard-test name. The exact finalization call is now
observed through a wrapping real function, not a fabricated answer.

The corrected control passes in0.006s; the broader relevant check executes all
nine actual attachment-row catalog closures, each after fresh setUp and
doCleanups, in1.637s including collection. Initial focused process1.682s and
final audit/verification process2.133s total below4s, within15s. The audit proves
all six prior passing controls unchanged except the descriptive rename, and
all accepted baseline AST preserved after removing this one branch/new class.
review_cycles.py and schema.py retain their baseline hashes.

Evidence: baseline-120598.json, base-120598.py, focused-120598.json,
initial-candidate-120598.py, verify-120598.py, verification-120598.json,
candidate-120598.py and candidate-120598.patch. Final test-file SHA-256 is
bf6160f596ad917fdb4296963d2c272adf3f328b2e78e279dc1f1eb4da7bf00c.
Awaiting independent baton.bug acceptance. W116975 retains inventory/coverage.
