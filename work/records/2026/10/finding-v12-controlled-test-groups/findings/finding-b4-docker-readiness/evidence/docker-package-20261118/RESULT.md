# M385071 Docker/package follow-on —22 passed,8 prerequisite-blocked

Claim E385073; baton.codxpc / impl. Authority: parent review-2026-11-18T02-15-55Z.md, child FINDING/PLAN, M385071. Exact isolated committed438eefa68f592e159f42cf1d190c7d7de4afde12 plus declared consumed inputs. No K bytes, shared product/test edits, Git mutations or Docker builds. Prior242 accepted results remain unchanged and distinct.

## Exact current collection and outcomes

| Module | Collected | Passed | Not started | Seconds |
|---|---:|---:|---:|---:|
| tests.manager.test_refused_session_engine |8|0|8|—|
| tests.manager.test_oci_engine |9|9|0|1.265|
| tests.tools.test_packaged_creation |13|13|0|12.375|

Historical25 is superseded by current30-ID collection, not used to omit cases: OCI includes four additional gate/accounting cases and packaged creation includes13 current IDs. `collected-all.json` is the complete list. Every ID partitions into22 passed or8 explicitly prerequisite-blocked in `accounted-summary.json`; zero failures/errors/skips/fixture events/duplicate or unaccounted IDs. No refused-session fixture was invoked. Runner summary's all_passed refers only to the22 executable selections, not the whole assignment.

## Missing prerequisite reported before dependent execution

`image-prerequisites.json` records failed inspect for both previously built current-context worker IDs:
- sha256:358141000ac06aa4719d4721ac9cfb258c66159896587e9776828f753c3c5934
- sha256:4da24074d73c8bdeb7ad676ca646287f356f84fbccf517f1f6052686b020ef83

Both were removed by their prior task-tag cleanup. `test_refused_session_engine` inherits Lifecycle, whose setUpClass at test_lifecycle_composition.py:146 requires a selected reference-worker image or implicitly builds one at169. M385071 allows installed images only, so dependent execution was withheld, not skipped. M385074 reports this exact prerequisite before execution. Historical images exist but none was substituted as an unproved current-context reference. Required next step: select an installed image with matching reference-worker provenance or release one bounded offline build from the same snapshot/base, then run the8 exact blocked IDs. No product repair is indicated.

OCI uses its installed pinned base python@sha256:8fef26df932191825664e4957ff488c96dfe64918327634a357a55facbc994d3, local ID sha256:9351a9a0a697a69e156f8bd067dd5ef3f9fa9b110abbdbbda1f343c622c7adc0. Corrected streaming wrapper retained; build/pull forbidden, runs use --pull=never and unique task label/cidfiles. Four created containers all absent; pre-existing containers/images preserved; all test roots removed, no emergency cleanup.

## One local distribution build

`build-distribution.py` compared all installed runtime/build dependency versions to both exact snapshot locks, then invoked prepared Python's PyInstaller6.16.0 directly with the unmodified packaging/stack.spec, isolated output/cache/work paths,1800s timeout. No dependency installation or download. Build6.220s. See dependencies.json, distribution-build-plan/result/log for exact arguments and provenance.

The materialized snapshot has no Git metadata. GIT_CEILING_DIRECTORIES prevents the build stamp from accidentally attributing the enclosing mutable repository; embedded commit/dirty are honestly null, and source provenance is the external exact commit/content manifest. `artifact-identity.json` proves frozen executable, Python3.13.7, native validator and both schema assets. Generated untracked build stamp preserved then removed from snapshot; original1134 source-file hashes before/after match. No source bytes modified.

Required flag BATON_V12_STACK_PACKAGING_REQUIRED=1 and explicit BATON_V12_STACK_DISTRO name the built artifact; absent bundle cannot skip. Cases invoke actual frozen command in a stripped environment. No Job/provider execution or live models. `distribution.tar.gz` durably retains the entire tested bundle; `artifact-manifest.json` hashes each file, `artifact-archive.json` names archive SHA256/size. Artifact bytes reverified unchanged after tests; exact disposable build output removed after archival. No required evidence exists only in scratch.

## Handoff

New evidence is child-only. Both selection invocations/logs/ledgers/results preserve600s timeouts, measured durations, environment and exact cleanup. Accounted22 passes are ready for independent acceptance;8 blocked cases require the image prerequisite selection above. No full/group/supervised run, repair or pull occurred. Pass W384944 to baton.decide with this finite remaining list.
