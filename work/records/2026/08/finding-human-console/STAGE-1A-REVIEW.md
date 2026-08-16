# Stage 1A review — changes requested

The implementation boundary is sound and the focused evidence passes, but
three current descriptions still state the superseded pre-adoption contract.
They now contradict the artifact being proposed for release:

- `baton_core/__init__.py` says the released CLI does **not** use the package,
  is still built from `baton_v6.py`, and that adoption is not scheduled.
- `README.md` says the existing CLI remains frozen on its original
  implementation until a later adoption stage.
- `test_core_parity.py::test_divergence_is_additive_only` says adoption is a
  separate, unscheduled decision and calls the oracle the released behavior.

Update those present-tense descriptions to the Stage 1A reality: `bin/baton`
uses `baton_core`; `baton_v6.py` remains frozen only as the differential
oracle and is not shipped. Historical trial/final-gate records should remain
historical and need no rewrite.

Independent checks completed by the reviewer:

- `test_core_parity.py test_packaging_isolation.py`: 19 passed;
- packaged executable reports `baton 5.1.0 (protocol 9)`;
- archive membership and submitted hashes match the handoff;
- `git diff --check` is clean;
- no unrelated Git state was touched.

Once the three live descriptions agree with the artifact, rerun only the
focused parity/packaging checks and return the updated hashes. A full suite is
not needed for this documentation-only correction.

## Revision review

The three descriptions are corrected and the focused checks pass. One final
release pin remains stale: the Stage 1A evidence block in `PLAN.md` still
records artifact `4d5eeeff…`, while packaging the corrected
`baton_core/__init__.py` necessarily produced `f309d6d3…`. Update that evidence
line to the submitted final hash. No code change or additional test run is
needed.
