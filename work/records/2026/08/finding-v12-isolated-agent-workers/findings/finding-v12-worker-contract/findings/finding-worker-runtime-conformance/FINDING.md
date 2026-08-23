# Finding: specify runtime-neutral v12 worker conformance

Canonical Baton Work: `W1441` (`43c55d4b-W1441`).

Child of `work/records/2026/08/finding-v12-isolated-agent-workers/findings/finding-v12-worker-contract/`.

## Assignment boundary

Define the black-box, runtime-neutral conformance suite for the frozen outer
worker-control and ACP boundary contracts. The suite must certify observable
behavior rather than provider claims or Docker/SSH implementation details. Do
not implement a production runtime, manager, protocol or adapter.

## Required design output

The contract must define fixture manifests, driver/observer interfaces,
machine-readable observations, pass/fail rules and retained evidence for:

- typed source materialization and digest verification, read-only inputs,
  private writable workspaces, declared-output containment, freeze, validation
  and collection;
- canonical repository, Git metadata, other-worker workspace, mount, network,
  resource and tool isolation;
- pre-claim execution denial, token expiry/replay/binding failures, claim
  ambiguity and current-generation-gated activity/result/proposal publication;
- graceful cancellation, forced stop, positive quiescence, explicit uncertain
  quiescence, replacement gating and every late stale publication attempt;
- manager and adapter restart, duplicate operations/events, transport
  partition, proof-bound remote reattachment and safe replacement;
- assignment-scoped credential delivery, exact-canary non-retention scans,
  leakage-triggered publication refusal and explicit residual-risk reporting;
- policy/mode refusal, untrusted output, result/proposal integrity, runtime
  profile probation/disablement signals and route-policy consequences; and
- at least one local OCI and one genuinely non-local adapter profile using the
  same normative vectors and no model-provider dependency for the core gate.

## Acceptance boundary

Every normative assertion must identify the observable evidence that decides
it and distinguish `passed`, `failed` and `unable`. Counts or elapsed time do
not certify a runtime. Runtime-specific supplemental cases are allowed but
cannot compensate for a failed portable core case.

## 2026-08-21 design record

### Revalidated baseline

Both dependencies closed `satisfying` before this Work became ready, and both
were re-read at their current state before anything was written.

- **Confirmed.** W1439 closed after one review round; its `SPEC.md`, schema
  and evidence are unchanged since approval. Its error taxonomy remains CLOSED
  at 7 categories and 31 code pairs, its control surface at 17 kinds, and its
  manifest family at 10 schemas.
- **Confirmed.** W1440 closed after four review rounds
  (`review-2026-08-21T23-42-10Z.md`, signed off). Its turn-outcome, session-state
  and event vocabularies are closed at 8, 9 and 10 members; its approval
  families at 4.
- **Confirmed.** W151 remains the normative owner of the three typed gates
  this suite observes: `runtime-quiescence`, `contract-runtime` and
  `plan-revision`.
- **Confirmed.** Nothing in either approved contract changed after its
  approval, so no supersession was needed and this child imports rather than
  restates.

### Decisions proposed for approval

`SPEC.md` §13 states the eight decisions as one compatible set. In summary:
the suite adds no rule to the contracts it tests and every obligation cites
its source clause; coverage of the frozen vocabularies is mechanically checked
against the approved schemas rather than claimed; the observable surface is
closed and excludes runtime internals, with isolation observed through an
ordinary in-runtime probe; the core gate is deterministic and model-free;
faults are ordered and an uninjectable fault yields `unable`, which denies
certification; a negative case passes only on its exact expected refusal;
the verdict is recomputed and counts, elapsed time, a declared verdict and
supplemental passes decide nothing; and both profiles run the same core, with
`remote` required to be demonstrably remote.

### Acceptance boundary, met

The assignment required that every normative assertion identify the observable
evidence that decides it and distinguish `passed`, `failed` and `unable`.
`evidence/obligations.json` carries `observable` and a three-valued `verdict`
on all 64 obligations, and
`test_every_obligation_names_its_evidence_and_all_three_verdicts` fails if any
is missing either. The assignment also required that counts and elapsed time
not certify a runtime, and that a runtime-specific case not compensate for a
failed portable core case: `SPEC.md` §6.2–§6.4 states both and
`test_counts_and_the_declared_verdict_decide_nothing` and
`test_a_supplemental_pass_cannot_offset_a_core_failure` demonstrate them
against a run that declares itself certified while failing a core case.

### Judgement calls a reviewer should check

1. **The observable surface is closed at six kinds** (`SPEC.md` §3.1), which
   excludes the container runtime API, the host process table and adapter
   internals. That is what makes the suite runtime-neutral, and it is also
   what makes family B need an in-runtime probe.
2. **The probe holds no special capability** (§7.1), so family B is
   predominantly negative: the manager observing a refusal is strong evidence,
   while the probe self-reporting failure is weak.
3. **`unable` denies certification** (§6.1) rather than being skipped. The
   alternative makes "we could not test it" indistinguishable from "it works".
4. **A negative case passes only on its exact refusal pair** (§5.2), never on
   absence of success, because a dropped or ignored request would otherwise
   certify as a correct refusal.
5. **The register is machine-checked against the upstream contracts** (§2.1)
   rather than maintained by hand, so an upstream addition fails a test here.

This child changes design records only. No protocol, authority, application,
runtime or adapter implementation was added or modified, and no container was
started.

## 2026-08-22 corrections after review `review-2026-08-22T03-28-18Z.md`

First review; four P1 findings. All four counterexamples reproduced against
the submitted artifacts before anything changed, and all four were real.

### Decisions changed by this round

1. **An observation carries facts and no verdict; the assessor derives every
   assessment.** **Superseded:** the previous `observed` member and the
   aggregation of it in `certify`. A case document carried a sentence, evidence
   purpose names and an error pair but no machine-readable expectation, and an
   observation carried a chosen verdict but no observed facts — so the suite
   aggregated the observer's declaration and never applied the register's
   verdict rules. It certified 101 observations that had declared themselves
   passing without a runtime being driven.

   Cases now carry a machine-readable `stimulus` and an executable
   `expectation` of predicates over named facts, plus the `required_facts` that
   expectation reads. Observations carry a `facts` map and a `status` of
   `observed` or `blocked`, and the schema gives them nowhere to record a
   conclusion. `assess` derives `passed`, `failed` or `unable`. An observation
   whose evidence purposes are not exactly the case's `deciding_evidence`, or
   which is missing a required fact, is inadmissible rather than failing: the
   suite could not decide, so it does not.

2. **Certification composes fixture acceptance and binds the profile.**
   **Superseded:** `certify` reading `fixture["document_digest"]` without
   accepting the fixture, and never comparing the run's profile with it. A
   fixture with an invalid seal certified, and a run could claim a different
   profile than the fixture it ran against.

3. **Remoteness is decided from facts.** **Superseded:** the `locality: remote`
   label plus a partition capability as the only enforced remote facts. The
   fixture now carries a `host_identity` block, and a remote fixture is refused
   unless the runtime host differs from the manager host and the workspace does
   not resolve on the manager; it must also be able to inject both a partition
   and a host restart, each of which now has a case.

4. **An `invariant` is not a refused control operation** (`SPEC.md` §5.2.1).
   **Superseded:** the rule that every negative case pass only on an exact
   `control.error` pair. W1439 §6.5 and §11 define `control.error` for
   control-protocol errors; nothing in W151, W1439 or W1440 requires a
   filesystem denial inside a runtime, an absent mount, or a negative reading of
   gate-clearance evidence to synthesize a control frame. Demanding one was
   this suite inventing a runtime interface rule — precisely what §0 forbids.
   Expectations now have three kinds, 44 of the 107 cases are `invariant`
   decided from probe or authority facts, and a test asserts that no case whose
   stimulus is an in-runtime probe or an authority read is a `control-refusal`.

5. **The missing mandatory vectors exist** and the completeness test names them
   rather than checking a subset relation. Added: `E-adapter-restart-reconciles`,
   `E-remote-host-restart`, `F-credential-scoped-to-assignment`,
   `F-credential-not-reusable-cross-assignment`, `F-credential-expiry-mid-run`
   and `G-profile-failure-signal`, with obligations `E-09`, `E-10`, `F-06` and
   `G-14`.

6. **The suite emits a profile signal and chooses no policy** (§6.5).
   **Superseded:** obligation `G-09`, which cited §6.4 — a clause about counts
   and elapsed time — and proved only that the suite mutates nothing. A report
   whose portable core did not pass now emits a `profile_signal` bound to the
   runtime-profile and adapter build digests, naming the failed and undecided
   cases, addressed to a `route-policy` consumer. Emitting nothing would leave
   that consumer with no input; deciding here would put the suite in charge of
   routing.

7. **There is no verdict to read.** **Superseded:** the run document's own
   `verdict` and `counts` fields, which the previous revision carried and
   merely promised to recompute. A document that carries a conclusion invites
   being trusted for it. The verdict now lives only in a separate derived
   `report`.

## 2026-08-22 corrections after review `review-2026-08-22T03-45-41Z.md`

Second review; three contract-composition gaps. All three counterexamples
reproduced before anything changed. The reviewer accepted the first-round
corrections.

### Decisions changed by this round

1. **A case declares the profiles it applies to, and may exclude one only when
   the fault it requires cannot exist there** (`SPEC.md` §8.3).
   **Superseded:** `E-remote-host-restart` being universal core while
   `MANDATORY_FAULTS_BY_PROFILE` exempted `local-oci` from `host-restart`. A
   local fixture was therefore ADMITTED and then necessarily failed
   certification as `unable` — the suite's admission rules contradicting its
   assessment rules, which would have read to an operator as a runtime defect.

   Cases now carry `applies_to`. Exactly one case is profile-scoped, and the
   justification is definitional rather than convenient: a local runtime's host
   IS the manager's host, so restarting it is `manager-restart`, which is in the
   common core. Fixture admission derives its mandatory faults from the core
   each profile actually runs, and the model refuses both a case that excludes a
   profile without a profile-only fault and a run that observes a case outside
   its profile's core. `local-oci` runs 106 cases and `remote` runs 107; that
   one-case difference is the only one the contract permits.

2. **Residual risk is derived from accepted facts** (§10.1).
   **Superseded:** `build_report` accepting a caller-supplied `residual_risk`
   and sealing it unexamined. A fully certified report over a run whose own
   facts said all ten surfaces were scanned could state that none were, and the
   two surface sets could omit or overlap surfaces. `build_report` now takes no
   residual-risk argument at all; `surfaces_scanned` comes from the
   `F-canary-each-surface` facts and only when that case passed, and the
   complement is computed, so the sets are disjoint and partition the closed
   vocabulary by construction. A derived document with one caller-supplied
   member is a document trusted for the one thing nobody derived.

3. **A run carries its own supplemental case definitions** (§9).
   **Superseded:** the `runtime-supplemental` scope value with no way to bind a
   definition. `CASE_BY_ID` held only the fixed core, so a schema-valid sealed
   supplemental case and its bound observation were refused at the advertised
   entry point — the extension point rejected every use of itself. A run now
   carries `supplemental_cases`, accepted and assessed under the same shape,
   seal and fact rules, reported in the report's separate `supplemental` list
   and never in the verdict. A supplemental case may not reuse a core
   identifier and a run may not present one declaring `portable-core`, because
   either would let a run redefine the contract it is being measured against.

## 2026-08-22 corrections after review `review-2026-08-22T03-53-55Z.md`

Third review; one P1 finding with four parts, all reproduced before anything
changed. The reviewer accepted the second-round corrections.

### Decisions changed by this round

1. **A supplemental case names no register obligation and declares its own
   source** (`SPEC.md` §9). **Superseded:** the requirement that every case
   carry a non-empty `obligations` array. An additional runtime property need
   not implement one of this contract's obligations, and the register — being
   fixed — cannot backlink a case it has never seen, so a citation there could
   only ever be a claim nobody checks.

   The worked example proved the point against itself: `G-vendor-extra` is a
   vendor attestation citing `G-04`, whose obligation is proposal-digest
   integrity. The citation was false and was the only way the example could
   validate. Cases now carry `supplemental_source`, a reverse-DNS namespace
   with an explicit version whose pattern cannot be mistaken for an obligation
   identifier. A portable core case carries obligations and no source; a
   supplemental case carries a source and no obligations; the schema enforces
   both directions.

2. **A bound supplemental definition is always accounted for** (§9).
   **Superseded:** `certify` silently dropping a definition the run bound but
   never observed. A run could advertise an extension and suppress its failed
   or blocked execution from the report, which is reporting in name only. A
   bound definition now yields exactly one applicable observation or an
   explicit `unable` naming that it was declared and never observed.

3. **A supplemental definition must apply to the fixture's profile** (§9).
   **Superseded:** `applies_to` being enforced for portable core cases only, so
   a local run could assess a supplement declaring itself remote-only.
