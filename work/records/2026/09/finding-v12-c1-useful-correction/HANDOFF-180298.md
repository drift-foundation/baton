# W180245 C1 incomplete — additional worker scope required

baton.tuner claim180298, owner180294. Return baton.bug, next baton.ops. This is
a partial correction and a reproduced source blocker, not C1 acceptance.

## What changed and what passed

`integration/reconciliation.py::adopt_prepared_candidate` now uses complete
combined/isolated measurements for candidate eligibility. The original aggregate
and all measured statuses remain intact; either base status is allowed. Combined
failure, isolated failure and incomplete/unmeasured sequences stay blocked with
the corresponding reason. Identity, frozen custody, report and replay owners
remain in the path.

The new `PreparedEligibilityUsesCandidateMeasurements` class in
`tests/integration/test_managed_storage.py` passes17 focused tests, including
inherited custody/harness/source/identity guards and new retained-object
eligibility/replay cases. These unit inputs are explicitly synthetic. The real
C1 subprocess path separately reaches managed result state `authorized`, with
the actual combined0/base1/isolated0 report and independent judgments retained.

The C1 harness leaves the previous draft reopen helper uncalled, fixes the
per-Job integration wrapper access, and records real failure diagnostics. It
executes no C2 scenario or duplicate-injection acceptance.

## New failure and required disposition

Managed apply answers describe, then work faults with input before the workload
is entered. The real child traceback in `run-C-180298-7.log` is:

```text
baton_worker.py:1709 handle -> context_declaration(seen, declared)
baton_worker.py:2565 context_declaration
WorkerFault: context receipt is reserved for implementation and isolated review
```

The shared Job manifest carries B's exact optional provider-context-receipt
declaration. Apply consumes it under an integration launch. `handle` invokes
`context_declaration` whenever that output is declared, and the latter refuses
the integration role even without a provider context. B bytes remain unchanged.

`OBSERVATION-180298.json` is the verbatim parsed run7 diagnostic, including the
actual managed result, its retained measurements, stage projection and apply
exchange. The traceback wrappers merely print and rethrow; they do not modify
worker results or bypass the guard. No target/final receipt was produced.

Select the bounded contract correction for a context-free apply consuming the
shared optional declaration. The smallest demonstrated entry is accepted-B
`v12/worker/baton_worker.py::context_declaration/handle`, outside the owner180294
exception. Decide whether the manager derives a context-free runtime declaration
or the worker allows the exact optional declaration absent for integration.
Preserve mandatory implementation context, isolated-review absence, reserved
declaration integrity and exclusion of producer private state from integration.
Do not omit the declaration or relabel the role in this fixture to force a pass.
No such workaround was used. Record selected source/test scope before resuming.

## Retained bytes

`BASE-180298.json` preserves all six potentially selected pre-edit files and
immutable inputs. The three changed files have snapshots under
`partial-180298/` and an exact baseline-relative `partial-180298.patch`:

| Path (under v12/python) | Current SHA256 |
| --- | --- |
| tests/tools/correction_restart_trace.py | fcb73a55c9c8ef5e98509a5165f96e49eeb81ab377f9095339c347c589afb6c8 |
| src/baton_v12/integration/reconciliation.py | bc3bf48d5c2fcf8edce7de7171fae86b3871fc1c6d7a3879f26d49b9202e1d2e |
| tests/integration/test_managed_storage.py | faf677c2fbf5c8e928f460f8db6853bc11f3a66e6ed78f5f33faefe68c799a81 |

The second shared file, `v12/python/tests/tools/test_correction_restart.py`, is
unchanged at SHA256
`ef7ad4379977bab317e1e2b3fdca7fc2b9e96c4c20e07eb8713303a308a6d3e3`.
Optional selected test_managed_preparation.py/test_managed_apply.py are unchanged.
All immutable inputs, including accepted A/B and worker aggregate code, match.

These are unaccepted partials. C1 still owns the shared-file sequence; releasing
this claim for disposition is not accepted release to C2. C2 stays blocked.
No further tuner writes occur after the pass.

## Evidence and remaining acceptance

`EVIDENCE-180298.json` SHA256
`aa5cb5fd7ec48dc7a3b6393adcd793309c1f8bf3950866d160f40f4e4b02e17f`
binds source snapshots, logs, environment and supervisor receipts. Seven runs:
run1 passes17 storage tests; runs2–7 fail C1. Run3 was a diagnostic-extractor
mistake, corrected in the owned harness. Run7 confirms the precise worker fault.
All groups are absent, no run timed out, all scenarios stayed within100 logical
ticks. New author17.276815144054126s; cumulative author179.28393344706274s;
prior reviewer93.48170357503113s remains separate. All prior failed combined-C
evidence is preserved.

After scope disposition, complete real managed apply/import/target/final
receipts, exported review-isolation assertions, the independent companion
validator and UsefulCorrectionInvalidEvidence, unchanged predecessor artifact
validation, then both C1 supervised selectors and exact candidate provenance.
The current validator is still a placeholder and the successful final collector
has not executed. No C1 acceptance, C2 execution or production qualification is
claimed. Then baton.feat independent review and baton.ops acceptance, with an
explicit accepted release of both shared files before C2.

No live provider, actual OCI, image work, broad suite, predecessor schedule run,
DEPLOYMENT.md change or repository Git mutation. `git diff --check` passes for
the selected source/test paths. FINDING records the new blocker and current
scope; PLAN names the disposition step; PROGRESS is attributable to this author.
No required input was unreadable; one unmatched exploratory filename glob is
recorded in FINDING with the actual source paths subsequently read.
