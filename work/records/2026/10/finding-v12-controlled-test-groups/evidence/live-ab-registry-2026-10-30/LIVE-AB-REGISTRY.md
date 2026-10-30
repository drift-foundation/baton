# Live A/B credential registry as an explicit run input (2026-10-30)

K (Claude, interactive copilot as baton.prompt) under the owner-held claim
E384905 (arrangement B); K holds no claim. Answers M384918 / review
2026-10-30T08-51-30Z: replace the live A/B composer's personal-home registry
default with an explicit supported input, prove fake-path propagation and
missing/invalid refusal, no live execution.

## Change (CANDIDATE-SHA256.txt)

- `v12/testing/live_ab/deployment.py`: `REGISTRY` is no longer the constant
  `/home/sl/.baton/credential-sources.json`; it is
  `credential_registry(SETTINGS)`, which takes `settings.credential_registry`
  and refuses (RuntimeError naming the setting and the operand) a missing,
  empty, non-string, relative or non-normalized value. The composer only
  checks the SHAPE: nothing here reads the registry, which remains read only
  by the execution owner when delivering attempts (README unchanged on that).
- `v12/testing/live_ab/scenario.py`: new REQUIRED operand
  `--credential-registry PATH`; refused unless absolute, normalized and an
  existing file (operator preflight, a stat, no read); carried into
  `settings.json` as `credential_registry` before `deployment` is imported.
- `v12/testing/live_ab/README.md`: names the operand instead of the personal
  path.
- `v12/python/tests/tools/test_live_ab.py`: the render test's settings carry a
  FAKE registry path under the temporary root that does not exist; every one
  of the eight composed worker deployments carries exactly that path as
  `credential_sources`, the path is never created or touched, and no
  `/home/sl/` prefix survives in the composed configuration. New:
  `test_the_registry_is_an_explicit_run_input_and_a_bad_one_refuses_composition`
  (missing, relative, unnormalized, empty: importing the composer fails with
  the setting named and renders nothing) and
  `test_the_scenario_requires_the_registry_operand_before_any_preparation`
  (argparse exit 2 naming `--credential-registry`, the given root is not
  created).

## Verification

`just test-one tests.tools.test_live_ab` (test-live-ab.log): 4 OK in 0.84 s.
No live run, provider, engine, image, Docker or Git mutation; the module is a
PARALLEL_MODULES entry (tools package group), no registry change.
Portability: the module and the package now carry no operator home path; the
earlier portability proof (evidence/portability-2026-10-30) did not relocate
this package, so the fake-path proof here is the portability evidence.
