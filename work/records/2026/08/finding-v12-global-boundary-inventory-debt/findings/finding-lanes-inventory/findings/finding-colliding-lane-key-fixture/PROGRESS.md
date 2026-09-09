# Progress

## 2026-09-08 — baton.tuner claim119384

Claimed the separate fixture result after the parent released its claim on the
explicit dependency. Revalidated the real insert, collision SELECT and
`_adopted` validator against the pinned scope. Retained exact base.py and
runtime/schema hashes in evidence. Implemented only the returned-lane-key
branch and six additive controls; other column updates and labels remain.

Pre-execution question: does the malformed identity reach the real collision
lookup and validator while the stored row remains valid, valid returned rows
produce ordinary contention, earlier/wrong refusals fail the existing guard,
and the exact previous row factory is restored? Prior evidence only contains
the broken stored-key probe, so it cannot answer this question for the fix.
Run `PYTHONPATH=src python3 -m unittest -v
tests.manager.test_boundary_inventory.TheCollidingLaneKeyProbeReachesAdoption`
from v12/python (six focused controls), then a fresh-fixture sweep of
`EveryProbeProvesItArrived.lane_probes()` once. Cumulative budget 15 seconds.
That sweep checks all unchanged lane-column stimuli alongside the corrected
key; no whole aggregate, daemon or ordinary suite is needed for this leaf.

Initial focused run took 1.34 seconds: five controls passed; the new positive
control expected an unquoted attempt name, but real `name_value` quotes it.
Preserved the complete output and execution data in evidence/initial. Corrected
only that newly authored assertion from `held by attempt attempt-1` to
`held by attempt 'attempt-1'`, retaining the required exact holder. The fixture
itself already passed the malformed-key and real-query controls. Re-run the
focused class for these corrected bytes, then the not-yet-run lanes sweep;
remaining cumulative verification budget exceeds 13 seconds.

Completed: six focused controls green; all 17 lane probes green, each with a
fresh reclaimed fixture. Final execution 3.059 seconds; cumulative runs below
5 seconds within the 15-second budget. Exact outputs: evidence/focused.txt,
lanes.txt, verification.json and retained initial failure. `git diff --check`
passes. Candidate SHA256 is
162f527e3476dcffcc937996df6c36d2d26505dfd7ea156eee6657e7433b30d5.
evidence/audit.json verifies only the existing `spoiling_colliding_lane` AST
and new control class differ from accepted base830496b4; lanes runtime and
schema hashes remain exact. No scanner, aggregate assertion, catalog, label or
other existing-test change occurred.

Awaiting independent fixture review. The parent retains seven unowned entries,
four orphan calls and joined module acceptance. This is one complete bounded
fixture result; those other outcomes remain separately scheduled. No whole
inventory or ordinary-suite completion is claimed. Concurrent unrelated
dossier edits seen in final status are outside this candidate and untouched.

Handoff correction: the first pass named `baton.rview`, which is a route/role
handle rather than a registered endpoint and was correctly refused. This was
my operand error, not a Baton defect. Read the supplied config's exact kinds
and routes; `baton.bug` resolves through rview to baton.codex and is the
independent review destination. The refused pass changed no Work state.
