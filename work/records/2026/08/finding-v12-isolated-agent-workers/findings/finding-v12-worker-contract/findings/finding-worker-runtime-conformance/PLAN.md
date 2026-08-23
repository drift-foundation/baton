# Plan: runtime-neutral v12 worker conformance

1. [done 2026-08-21] Revalidate the approved worker-control and ACP
   specifications and enumerate every normative MUST as an observable test
   obligation. Both closed `satisfying` and were unchanged; the result is the
   64-obligation register in `evidence/obligations.json`, whose coverage of
   the frozen vocabularies is asserted against the approved schemas and model
   rather than claimed. Extended to 68 obligations after the first review.
2. [done 2026-08-21] Define fixture, driver, observation, evidence and result
   schemas, including `passed`/`failed`/`unable` semantics.
   `schema/conformance-1.0.schema.json`; `SPEC.md` §3-§5.
3. [done 2026-08-21] Define the portable positive, negative, retry, race,
   crash, restart, cancellation, partition, credential and stale-generation
   matrix. 107 sealed cases across eight families in `evidence/cases.json`,
   each with a machine-readable stimulus and executable expectation:
   22 `control-success`, 41 `control-refusal`, 44 `invariant`; `SPEC.md` §7.
4. [done 2026-08-21] Define local OCI and genuinely remote profile
   requirements plus runtime-specific extension rules. `SPEC.md` §8-§9; the
   remote profile's locality is decided from host-identity facts plus an
   injected partition and host restart, never from the `locality` label.
5. [done 2026-08-21, extended 2026-08-22] Add a provider-free executable
   design harness model and vectors. `evidence/conformance_model.py`,
   `evidence/build_cases.py` and 73 tests in
   `evidence/test_conformance_model.py`.
6. [done 2026-08-22] First independent review requested changes in
   `review-2026-08-22T03-28-18Z.md`: the assessor trusts self-declared verdicts
   instead of deriving them from machine-readable facts; certification reads
   an unaccepted fixture and permits profile substitution; mandatory restart,
   credential-scope and profile-policy vectors are absent; and the matrix
   invents control errors for negative invariant probes.
7. [done 2026-08-22] Correct all four. Observations now carry machine-readable
   facts and no verdict, and the assessor derives every assessment from a
   case's executable expectation; certification accepts the fixture and binds
   the run's profile to it; remoteness is decided from host-identity facts; the
   missing restart, credential-scope and profile-signal vectors exist; and
   invariant cases are decided from probe or authority facts rather than
   synthesizing a control frame. See `PROGRESS.md`, "Response to
   review-2026-08-22T03-28-18Z".
8. [done 2026-08-22] Second independent review requested changes in
   `review-2026-08-22T03-45-41Z.md`: the admitted minimal local profile cannot
   certify because a remote-host fault remains in the common core; the derived
   report can contradict its accepted canary facts through caller-supplied
   residual risk; and schema-valid runtime-supplemental cases cannot be
   assessed by any run.
9. [done 2026-08-22] Correct all three. Cases declare the profiles they apply
   to and may exclude one only when it requires a fault that profile cannot
   have, with fixture admission derived from the core each profile runs; the
   report's residual risk is derived from accepted facts and `build_report`
   takes no residual-risk argument; and a run carries its own supplemental case
   definitions, assessed under the same rules and reported separately from the
   verdict. See `PROGRESS.md`, "Response to review-2026-08-22T03-45-41Z".
10. [done 2026-08-22] Third independent review requested changes in
    `review-2026-08-22T03-53-55Z.md`: a supplemental case must falsely cite a
    core obligation even when it proves an additional property, and a bound
    supplemental definition without an observation silently disappears from
    the report instead of being assessed missing or unable.
11. [done 2026-08-22] Correct all four parts. A supplemental case names no
    register obligation and declares a namespaced `supplemental_source`
    instead, which the schema keeps distinguishable from an obligation
    identifier; a bound definition is accounted for by exactly one observation
    or an explicit `unable`; and a bound definition must apply to the fixture
    profile. See `PROGRESS.md`, "Response to review-2026-08-22T03-53-55Z".
12. [done 2026-08-22] Fourth independent review signed off in
    `review-2026-08-22T03-59-52Z.md`; return the child for approval.
13. [amended 2026-08-22, W4487] The decline ruling
    (`work/records/2026/08/finding-worker-control-decline-token-conflict/`)
    superseded W151's requirement that a decline echo the claim bearer, so
    the register gained obligation `C-08` and three cases. Counts are now 69
    obligations and 110 cases; `local-oci` runs 109 and `remote` 110. The
    earlier counts in items 1, 2 and 8 above are superseded by these and are
    retained as the history of how the register grew. Reviewed under W4487.
14. [amended 2026-08-22, W4487 review] The independent review of that
    amendment found the tokenless decline's effectively-once property rests
    on an operation signature nothing recomputed, so the register gained
    obligation `E-11` and two cases. Counts are now 70 obligations and 112
    cases; `local-oci` runs 111 and `remote` 112. Item 13's counts are
    superseded by these.
