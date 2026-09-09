# W124782 execution — baton.tuner claim124831

Question: does the concrete Authority's evidence-kind answer become a durable,
correlated local discharge receipt, including exact remote replay after a lost
local write, reopened stores and later Work movement? Negative controls must
retain wrong-kind/generation/authority and unreachable-runtime refusals.

Before execution: cumulative wall-clock budget20s for verification subprocesses.
From `v12/python`, with `PYTHONPATH=src:.`, run `python3 -m unittest -v
tests.manager.test_intake.ConcreteAuthorityDischargeReceipts`, then the affected
`tests.manager.test_intake` module if the remaining budget permits. The retained
runner records exact arguments, elapsed time and output and limits each process
to the remaining budget. No inventory, broader suite, daemon or live Authority.

The new concrete-session controls reuse the existing manager cleanup fixture;
offer/intake preparation still uses its fake. The discharge itself, original
and later claims/fences, Authority evidence and operation replay are concrete
public acts over disposable stores. This is provider acceptance evidence,
not the deferred consumer's joined lifecycle proof.

## Results

Final affected module: **156 tests pass**, including all six new concrete
controls. `verification.json` binds commands, timing and all three logs:

- Run1: five new controls pass; the new unreachable-runtime case expected
  `refused` instead of the existing `integrity/schema` refusal for an
  uncommitted cleanup. Corrected the expectation and additionally require the
  exact missing-operation diagnostic. Initial bytes: `initial-*.py`.
- Run2: the module exposed a fixture setup added to the wrong class by an
  insufficiently specific patch context (34 errors). Moved that added setup
  into the discharge class; no unrelated assertion was changed. Intermediate
  bytes and AST summary: `candidate-*.py`, `candidate.json`.
- Run3: the full module passes in2.933s wall time. Total test execution6.135s;
  scope audit0.064s, approximately6.20s combined, within20s.

`python3 <this-directory>/audit.py` passes. It compares the entire prior test
AST after allowing exactly two wrong-kind literal corrections, two additive
wrong-kind counterexamples, the discharge-only setup and six new controls.
All other prior test structure is identical. Source changes are confined to
the fresh-response and persisted-receipt functions. Modes remain0664.
Scoped `git diff --check` passes. Final hashes, bytes and base-relative patches
are in `final.json`, `final-*.py`, and `final-*.py.patch`.

Provider acceptance remains independent. No Authority/schema/shared fake,
registry, consumer, concurrent cleanup-provider or Git-state changes were made.
The consumer bypass and joined lifecycle proof remain with W122060/W119114.
