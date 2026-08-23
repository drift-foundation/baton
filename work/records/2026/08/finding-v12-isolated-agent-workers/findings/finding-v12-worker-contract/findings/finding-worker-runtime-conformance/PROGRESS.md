# Progress: v12 worker runtime conformance

Implementer-owned. One writer: `baton.claude`.

## 2026-08-21 — W1441 claimed and specified

Claimed W1441 at authority sequence 2415 after reading `AGENTS.md`,
`docs/EFFECTIVE-BATON.md`, the campaign record, the parent
`finding-v12-worker-contract` record, this child's `FINDING.md`, and both
approved dependencies in full.

### Revalidation performed before writing anything

| Pinned claim | Source re-read | Outcome |
| --- | --- | --- |
| outer worker-control contract | `../finding-worker-control-api-manifests/` SPEC, schema, evidence, review | closed satisfying, unchanged since approval; 17 control kinds, 31 error pairs, 10 manifest schemas |
| ACP agent-session boundary | `../finding-acp-agent-boundary/` SPEC, schema, evidence, four reviews | closed satisfying after a fourth-pass sign-off; 8 turn outcomes, 9 session states, 10 event kinds, 4 approval families |
| W151 assignment contract | `../../finding-v12-assignment-state-machine/SPEC.md` | unchanged; three typed gates observed by this suite |

No pinned decision had changed, so nothing needed superseding. Both contracts
are imported here, never restated.

### Delivered

- `SPEC.md` — the conformance contract, §0-§13.
- `schema/conformance-1.0.schema.json` — fixture, case, observation and run
  documents, Draft 2020-12.
- `evidence/obligations.json` — 64 obligations across eight families, plus the
  two profile definitions.
- `evidence/cases.json` — 101 sealed portable core cases, 43 positive and 58
  negative.
- `evidence/conformance_model.py`, `evidence/test_conformance_model.py` — the
  executable model and 38 tests.

### Verification

From `evidence/`:

```text
python3 -B -m unittest -q test_conformance_model
----------------------------------------------------------------------
Ran 38 tests in 0.668s

OK
```

Both JSON files parse; Draft 2020-12 self-validation and the W1439 shared-
definition equality are test assertions. The model imports no Baton or `v12/`
product code, reaches no model provider, and starts no container.

### Design decisions and why

Three earlier rounds on W1440 established a pattern I applied here from the
start rather than after a review found it missing:

- **Composition over restatement.** The register does not carry its own copy
  of the frozen vocabularies. It carries `covers` metadata, and the tests load
  the two approved schemas and the approved agent-session model and assert
  the register accounts for every member. When an upstream contract adds a
  member, a test here fails. A hand-maintained coverage claim decays exactly
  when the contract moves, which is exactly when it matters.
- **Composed acceptance.** `accept_document` is shape, then seal, then a
  private copy, before any field is read — W1440 §12.7a's ordering, adopted
  rather than rediscovered.
- **Byte equality, not object identity.** Every accepted document is copied in
  and out, so a caller that keeps a reference cannot edit what the suite went
  on to trust.

Four decisions are specific to this contract:

1. **The observable surface is closed at six kinds** (`SPEC.md` §3.1). It
   excludes the container runtime API, the host process table and adapter
   internals, because certifying against those certifies one implementation.
   The consequence is that isolation cannot be observed from the manager's
   side at all, which forces decision 2.
2. **Isolation is probed from inside the runtime by ordinary worker code**
   holding no capability a real worker would not have (§7.1). Because such a
   probe cannot be trusted to self-report success, family B is predominantly
   NEGATIVE: the manager observing a refusal is the strong evidence; the probe
   saying it could not reach something is the weak one.
3. **A negative case passes only on its exact refusal pair** (§5.2). "The
   request was refused with `stale-assignment.generation`" and "the request
   was dropped, ignored or crashed the adapter" are the same observation to a
   suite that only checks for absence of success — and the second family is a
   broken runtime. 58 of 101 cases are negative, so this rule decides most of
   the suite.
4. **`unable` denies certification** (§6.1) and must name its cause. Combined
   with §5.3 — a case whose faults the fixture cannot inject may not be
   observed `passed` — this closes the incentive that would otherwise make the
   cheapest clean run a fixture that can inject nothing.

### Judgement calls a reviewer should check

1. **The register is the deliverable, and prose does not duplicate it.**
   `SPEC.md` §7 gives per-family summaries and points at `evidence/cases.json`
   for detail, because a matrix duplicated in prose is one that will disagree
   with itself. §12.2 requires the two to agree in both directions and a test
   enforces it.
2. **The suite legislates nothing.** Every obligation cites a clause of W151,
   W1439 or W1440. If any reads as a new requirement rather than a restatement
   with observable evidence attached, that is a defect — a conformance suite
   is the worst place to introduce a rule, because it arrives wearing the
   authority of a test result.
3. **`remote` is asserted, not declared.** The profile requires an injected
   partition that changes what the manager observes. An elaborate local setup
   can satisfy the first two assertions; only the partition demonstrates a
   network. Without it family E certifies nothing.
4. **Verdict recomputation** (§6.2). The run document's own `verdict` and
   `counts` are ignored; the test demonstrates a run declaring itself
   certified while failing an isolation case, and recomputing to
   `not-certified`.
5. **One vocabulary I did not add.** `unable` is W151's word for a verifier
   observation, reused unchanged rather than renamed to something like
   `skipped`, because a skipped case sounds harmless and an unable one does
   not.

### State

Specification complete; awaiting independent review.

## 2026-08-22 — response to review-2026-08-22T03-28-18Z.md

State: **changes requested, all applied**. Reclaimed W1441 at authority
sequence 2483.

All four counterexamples reproduced against the submitted artifacts before
anything changed:

```text
wrong-evidence-purpose accepted     fabricated-core certified
fixture-seal INVALID                invalid-fixture-certifies certified
run-profile-mismatch certified      unused faults: adapter-restart, host-restart
A-input-readonly requires integrity.path from a filesystem write attempt
```

The first finding is the one that mattered, and it was correct in the way that
stings: what I had built was a sealed collection of self-declared results. The
case carried a sentence and an error pair but no machine-readable expectation;
the observation carried a chosen verdict but no observed facts; `certify`
aggregated the verdict. My own `clean_run` helper demonstrated the gap by
declaring 101 observations passing without driving anything, and the model
certified it.

### P1 — the assessor now derives from facts

I did not add a check; I moved the boundary. Cases carry a machine-readable
`stimulus` and an executable `expectation` — predicates over named facts, in
three kinds — plus the `required_facts` that expectation reads. Observations
carry a `facts` map and a `status` of `observed` or `blocked`, and **the schema
gives an observation nowhere to record a conclusion**. That is the enforcement:
an observer that could write `passed` is a component that both causes an
outcome and declares it, and such a component can arrange to see what it
expected.

Two admissibility rules follow, and both refuse rather than fail, because a
suite that could not decide does not get to: an observation whose evidence
purposes are not EXACTLY the case's `deciding_evidence`, and one missing any
required fact.

The tests now synthesize observations from each case's expectation, so a
passing run is one whose facts satisfy the contract. The old fabricated run is
kept as a negative test: 107 declared passes, 107 failures.

### P1 — fixture acceptance and profile binding

`certify` now calls `validate_fixture` first and compares the run's profile
with the accepted fixture's. Remoteness moved from a label to facts: the
fixture carries `host_identity`, and a remote fixture is refused unless the
runtime host differs from the manager host and the workspace does not resolve
on the manager. It must also inject both a partition and a host restart, each
of which now has a case, so §8.2's assertions are enforced rather than listed.

### P1 — the missing vectors

Added `E-adapter-restart-reconciles`, `E-remote-host-restart`,
`F-credential-scoped-to-assignment`,
`F-credential-not-reusable-cross-assignment`, `F-credential-expiry-mid-run`
and `G-profile-failure-signal`, with obligations E-09, E-10, F-06 and G-14.
The completeness test now names the required faults instead of checking a
subset relation, which is what let two mandatory ones sit unused.

On the profile signal: you were right that G-09 cited a clause about counts and
proved only that the suite mutates nothing. A report whose core did not pass
now emits a `profile_signal` bound to the runtime-profile and adapter build
digests, naming failed and undecided cases, addressed to a `route-policy`
consumer. Emitting nothing leaves that consumer with no input; deciding here
would put the suite in charge of routing.

### P1 — invariants synthesize no control frame

This was the finding I most needed. Demanding an exact `control.error` pair
from a filesystem denial or a negative authority read was this suite inventing
a runtime interface rule, which is what §0 forbids and what a conformance suite
is worst placed to do — it arrives wearing the authority of a test result.

Expectations now have three kinds. 41 cases are `control-refusal` and still
require the exact pair; 44 are `invariant`, decided from probe or authority
facts with no error pair at all; 22 are `control-success`. All eight of family B
became invariants, as did `A-input-readonly`, `D-agent-quiescence-not-runtime`
and `F-credential-not-reusable-cross-assignment`. A test asserts no case whose
stimulus is an in-runtime probe or authority read is a `control-refusal`.

Coverage of the closed taxonomy did not suffer — it never depended on attaching
an error to every negative assertion, which was the mistake.

### One thing I changed beyond the findings

The run document no longer has `verdict` or `counts` at all. The previous
revision carried them and promised to recompute; that promise held in the model
and told an implementer nothing, because a document carrying a conclusion
invites being trusted for it. The verdict now exists only in a separate derived
`report`.

### Verification

From `evidence/`:

```text
python3 -B -m unittest -q test_conformance_model
----------------------------------------------------------------------
Ran 53 tests in 1.896s

OK
```

53 tests, up from 38; 68 obligations, 107 cases (22 control-success, 41
control-refusal, 44 invariant). Every counterexample now refuses:

```text
fabricated-core                 not-certified (107 failed)
wrong-evidence-purpose          ConformanceError (not the deciding evidence)
invalid-fixture-certifies       ConformanceError (document digest mismatch)
run-profile-mismatch            ConformanceError (profile is not the fixture's)
local-fixture-calling-remote    ConformanceError (same host)
adapter-restart / host-restart  both exercised
profile signal on failure       probation, naming the failed case
probe invariants                expectation invariant, refusal None
```

Both JSON files parse; Draft 2020-12 self-validation and the W1439
shared-definition equality remain test assertions. Only dossier records
changed.

### State

Corrections complete; awaiting the second independent review.

## 2026-08-22 — response to review-2026-08-22T03-45-41Z.md

State: **changes requested, all applied**. Reclaimed W1441 at authority
sequence 2542.

All three counterexamples reproduced against the submitted artifacts before
anything changed:

```text
local-without-host-restart-valid local-oci
local-verdict not-certified   local-unable ['E-remote-host-restart']
contradictory-report certified   residual_risk surfaces_scanned []
supplemental-run ConformanceError run observes unknown case 'G-vendor-extra'
```

Each is a gap I introduced, and each is the same shape: two parts of this
contract disagreeing with each other rather than a runtime misbehaving.

### P1 — the admitted local fixture could not certify

This is the one I most want on the record, because it would have read to an
operator as a runtime defect. A local fixture was admitted and then necessarily
assessed `unable` on a case it was structurally unable to attempt: the
admission rule exempted `local-oci` from `host-restart` while the case
requiring it stayed universal core.

Cases now carry `applies_to`, and fixture admission derives its mandatory
faults from the core each profile actually runs — so an admitted fixture can
always attempt every case it will be assessed on. Exactly one case is
profile-scoped, and I wanted the justification to be definitional rather than
convenient: a local runtime's host IS the manager's host, so restarting it is
`manager-restart`, which is already in the common core as
`E-manager-restart-reconciles`. There is no separate host to restart.

To keep §8.3's protection I made the rule enforceable rather than documented:
a case that excludes a profile without requiring a fault from that profile's
`PROFILE_ONLY_FAULTS` is refused, and a run that observes a case outside its
profile's core is refused. `local-oci` runs 106 and `remote` runs 107, and a
test asserts the difference is exactly the host-restart case. Also corrected
the stale count in §8.3.

### P1 — a derived report could contradict its own facts

Correct, and the cause was structural: one caller-supplied member on a document
whose whole point is being derived. `build_report` now takes no residual-risk
argument. `surfaces_scanned` comes from the `F-canary-each-surface` facts and
only when that case passed; the complement is computed, so the sets are
disjoint and partition the ten surfaces by construction rather than by
promise. `unproven` always carries the standing sentence about redaction, plus
a line naming unscanned surfaces and a line for a failing or undecided core.

New vectors cover a blocked canary case (every surface reported unscanned), a
partial scan (the case fails and nothing is credited), and the absence of the
parameter itself.

### P1 — supplemental cases were unassessable

Also correct, and slightly embarrassing: the advertised extension point
rejected every use of itself. `SPEC.md` §9 and the `scope` value permitted a
supplemental case while nothing could bind its definition, and my own
"supplemental cannot compensate" test contained no supplemental case — it only
re-asserted that a core failure stays a failure, which is why the gap survived.

A run now carries `supplemental_cases`, accepted and assessed under the same
shape, seal and fact rules, reported in the report's separate `supplemental`
list and never in the verdict. Two identifier rules keep the boundary honest:
a supplemental case may not reuse a core identifier, and a run may not present
one declaring `portable-core`. Either would let a run redefine the contract it
is being measured against. There are now four supplemental vectors, including
a failed supplemental over a clean core (still certified) and a passing
supplemental over a failed core (still not certified).

### Verification

From `evidence/`:

```text
python3 -B -m unittest -q test_conformance_model
----------------------------------------------------------------------
Ran 67 tests in 3.254s

OK
```

67 tests, up from 53. Every counterexample now refuses or resolves:

```text
local minimal fixture       certified, unable []
local core / remote core    106 / 107, difference exactly E-remote-host-restart
build_report parameters     run, fixture, report_id, created_at
residual risk               10 scanned / 0 unscanned, disjoint and partitioning
supplemental-run            certified, reported separately, core untouched
```

Both JSON files parse; Draft 2020-12 self-validation and the W1439
shared-definition equality remain test assertions. Only dossier records
changed.

### State

Corrections complete; awaiting the third independent review.

## 2026-08-22 — response to review-2026-08-22T03-53-55Z.md

State: **changes requested, all applied**. Reclaimed W1441 at authority
sequence 2574.

All four parts reproduced against the submitted artifacts before anything
changed:

```text
G-vendor-extra cites G-04, whose obligation is proposal-digest integrity
no-obligation variant schema-valid: False
supplement-observed certified [('G-vendor-extra', 'passed')]
supplement-omitted  certified []
local run assessing a remote-only supplement: certified, passed
```

### The false citation

This is the part worth dwelling on, because the evidence was sitting in my own
worked example. `G-vendor-extra` is described as a vendor attestation and cites
`G-04`, which is about proposal-digest integrity. The two have nothing to do
with each other. That citation was not carelessness in the example — it was the
only way the example could validate, because the schema required every case to
name an obligation.

So the rule was generating false claims, and the first thing it falsified was
its own demonstration. An additional runtime property need not implement one of
this contract's obligations, and the register cannot backlink a case it has
never seen, so a citation there could only ever be a claim nobody checks.

Cases now carry `supplemental_source` — a reverse-DNS namespace with an
explicit version, whose pattern deliberately cannot look like an obligation
identifier. A portable core case carries obligations and no source; a
supplemental case carries a source and no obligations; the schema enforces both
directions, and tests confirm that `G-04` is rejected both as a supplemental
obligation and as a supplemental source.

### The disappearing definition

Also correct. A run could bind a definition and simply not observe it, and
`certify` dropped it — so a producer could advertise an extension and suppress
its failed or blocked execution. A bound definition now yields exactly one
applicable observation or an explicit `unable` with the rationale that it was
declared and never observed. Reporting that omits what it does not like is
reporting in name only.

### Applicability

`applies_to` was enforced for portable core cases and not for supplemental
ones, so a local run could assess a supplement declaring itself remote-only.
A bound definition whose `applies_to` excludes the fixture profile is now
refused. Duplicate supplemental observations were already refused by the
one-observation-per-case rule, and there is now a vector for it.

### Verification

From `evidence/`:

```text
python3 -B -m unittest -q test_conformance_model
----------------------------------------------------------------------
Ran 73 tests in 3.754s

OK
```

73 tests, up from 67. Every part now refuses or resolves:

```text
example obligations []          example source com.example.runtime/1
citing G-04 schema-valid False  source 'G-04' schema-valid False
core case with a source False
supplement-omitted certified [('G-vendor-extra', 'unable')]
local run with a remote-only supplement: ConformanceError
```

Both JSON files parse; Draft 2020-12 self-validation and the W1439
shared-definition equality remain test assertions. Only dossier records
changed.

## Amendment for W4487 — 2026-08-22

Not a review response: an amendment carried in from the W4487 decline ruling
(`work/records/2026/08/finding-worker-control-decline-token-conflict/`). W151
§7 required a declining worker to echo the claim bearer while worker-control
1.0 and its frozen schema require `claim_token: null`; the approver kept the
non-secret envelope and superseded W151. Without this the one rule the two
frozen contracts had to be re-ruled over would be the one the conformance
register does not cover.

Added obligation `C-08` — a decline carries no bearer, is authorized by its
exact offer binding, consumes the verifier and terminates only the offer it
names — with three cases: `C-decline-without-bearer` (success),
`C-decline-carrying-bearer-refused` (`integrity/schema`) and
`C-decline-wrong-binding-refused` (`refused/precondition`, asserting that
NEITHER the named offer nor the bound one is terminated).

**Current counts, superseding the earlier ones in this file:** 69 obligations
and 110 sealed cases (23 `control-success`, 43 `control-refusal`, 44
`invariant`); family C is 16, up from 13; `local-oci` runs 109 and `remote`
runs 110, and the one-case difference is still exactly
`E-remote-host-restart`. `python3 -m unittest test_conformance_model.py` — 73
tests, unchanged in number and all passing; the register/matrix two-way
agreement test is what proves the addition is complete rather than partial.
Only dossier records changed.

## Amendment — 2026-08-22, W4487 review [P1]

`work/records/2026/08/finding-worker-control-decline-token-conflict/review-2026-08-22T14-39-32Z.md`
found that the tokenless decline the amendment above certifies is
effectively-once only if a receiver RECOMPUTES the operation signature — and
worker-control §12 rule 9 required exactly that with no obligation covering
it. A decline could change its durable reason, recompute its body digest,
retain the previous operation signature, and be journalled as an exact replay
of the first decline.

Added obligation `E-11` — a mutating command's signature recomputes over the
operation kind and every durable operand — with two cases:
`E-operation-signature-mismatch-refused` (`integrity/digest`, nothing
durable written) and `E-operation-signature-covers-kind`
(`refused/operation-collision` when one operation id is reused across
`output.freeze` and `output.collect`, whose bodies are byte-identical; an
implementation that signed the body alone would REPLAY the freeze as a
collect instead of colliding).

`E-02` does not cover either: it starts from two signatures that already
differ, so it says nothing about whether a signature describes its own
request.

**Current counts, superseding every earlier one in this file:** 70
obligations and 112 sealed cases (23 `control-success`, 45 `control-refusal`,
44 `invariant`); `local-oci` runs 111 and `remote` runs 112, and the one-case
difference is still exactly `E-remote-host-restart`. `python3 -m unittest
test_conformance_model.py` — 73 tests, all passing; the pinned case count in
`test_every_case_document_validates_and_reseals` moved 110 -> 112 with the
register. Only dossier records changed.

### State

Corrections complete; the fourth independent review signed off. Amended
2026-08-22 for W4487, and again for that Work's review, which returns for
re-review under W4487.
