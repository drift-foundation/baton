# W385623 test-only composition correction — E385665 / M385663

Ready for independent review. Candidate sha256:35de2ca2eff9f6daef003d3deee4fba1bb352c0daaa539d0ef56aa6e053e4a90. One changed file and one changed test method:
`v12/python/tests/job_manager/test_retained_failure_analysis.py` — TheFiniteProfileIsTheOwnersExactPublishedDefinition.test_the_implementation_jobs_own_control_profile_is_untouched.

The exhaustive profile list now includes the separately accepted native-handoff-heavy/1. The analysis-profile absence check and exact documentation/1 assertion are unchanged. Added exact native-handoff/1 values4800/9960/3600/900 and heavy values9000/21600/7200/900, both corrections0. No assertions removed, no product changes, no test IDs removed or renamed.

Base is the actual joined source: HEAD5d5e79a4317c8f067d1c79f21c331afbd9aef900 plus the ten hash-bound accepted7d686bf0 v12 paths from integration-20261122/import.json. joined-base.json binds those inputs; candidate-manifest.json binds the single before/after path and base/candidate-test.py preserve recoverable full bytes. candidate.patch is the narrow import delta, not the cumulative native implementation. Main imported source and all three accepted heavy-profile files were checked unchanged after verification; no host test/source edits or Git mutation. Scratch reconstruction used a read-only Git archive and exact imported-file copies, not a retained implementation restart.

Verification:201 tests passed,0 failures/errors/skips,6.383s unittest/6.993s measured subprocess wall. Full retained-analysis acceptance module140 cases, job-control module and focused worker-bound adapter class. Exact command/environment/exit in run.json; verbose per-test evidence in focused.log. The original388-case integration run remains the retained baseline finding; it was not rerun or relabelled. This run proportionately establishes the changed assertion, automatic analysis acceptance and heavy-profile coexistence. No full suite, build/package qualification, live model, instance changes or mainline import.

No remaining issue within this test-only delta. Independent review and coordinator import/reverification remain next; broader previously disclosed native coverage/environment limitations and package qualification are unchanged, not waived. Existing accepted native candidate/evidence were not rewritten.
