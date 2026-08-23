# Baton worker runtime conformance contract

Version: `1.0-design`
Suite family: `baton.worker-conformance`
Status: proposed normative design for W1441; not an implementation and not a
certification of any runtime until approved and run.

**Amended 2026-08-22 by the W4487 decline ruling.** W151 §7 required a
declining worker to echo the claim bearer while worker-control 1.0 and its
frozen schema require `claim_token: null`; the approver kept the non-secret
envelope and superseded W151. The register gained obligation `C-08` and
three cases so the rule the two frozen contracts had to be re-ruled over is
covered here too. The matrix is 110 cases, up from 107, and the register 69
obligations, up from 68. Nothing else in this contract changed. See
`work/records/2026/08/finding-worker-control-decline-token-conflict/`.

**Amended again 2026-08-22 by the W4487 review.** The decline the amendment
above made tokenless is effectively-once only if a receiver RECOMPUTES the
operation signature, and §12 rule 9 of worker-control 1.0 required that
without any obligation certifying it — so a document could change its durable
reason, recompute its body digest, keep the previous signature and replay the
first decline. The register gained obligation `E-11` and two cases. The
matrix is 112 cases, up from 110, and the register 70 obligations, up from 69.
Nothing else in this contract changed.

## 0. Scope and precedence

This contract specifies how a runtime is CERTIFIED against the two approved
M1 contracts: what must be observed, what the observation is allowed to
decide, and what makes a profile certified or not.

It specifies nothing about how a runtime is built. There is no Docker command,
no SSH invocation, no orchestration recipe and no vendor API in this document,
because a suite that named one would certify that implementation rather than
the contract.

Precedence is strict and one-directional:

1. `../../finding-v12-assignment-state-machine/SPEC.md` (W151) owns assignment
   identity, generations, fencing, typed gates, effectively-once settlement,
   runtime observation axes and receipt authority.
2. `../finding-worker-control-api-manifests/SPEC.md` (W1439, approved) owns
   the outer protocol, the manifest family, canonicalization, digests, limits
   and the CLOSED portable error taxonomy.
3. `../finding-acp-agent-boundary/SPEC.md` (W1440, approved) owns the inner
   agent-session boundary.
4. This document owns only how conformance to 1–3 is decided.

If this document conflicts with any of them, that one wins and this design
must be revised. **This suite adds no rule to the contracts it tests.** Every
obligation in §2 cites the clause it comes from; an obligation with no source
clause would be this document quietly legislating, which is exactly the defect
a conformance suite is worst placed to introduce, because it would arrive
wearing the authority of a test result.

### 0.1 The shared definitions are reproduced, not re-derived

`schema/conformance-1.0.schema.json` reproduces W1439's `digest`, `opaqueId`,
`timestamp`, `participant`, `workRef`, `artifactRef` and `evidenceRef`
VERBATIM, and `evidence/test_conformance_model.py` asserts they stay
byte-identical — the same rule W1440 §0.3 adopted, for the same reason. A
suite whose evidence references were shaped slightly differently from the
contract's would be unable to quote the artifact it just examined.

### 0.2 Sealed documents

Fixtures, cases, observations and runs are sealed documents carrying
`document_digest`, computed exactly as W1439 §3.2 defines. A consumer verifies
the seal BEFORE reading any other field and takes its own copy; "unchanged"
means byte equality, not object identity. This is W1440 §0.2 unchanged, and it
matters more here than anywhere: a certification whose evidence could be
edited after acceptance is not evidence of anything.

## 1. What conformance certifies, and what it cannot

A conformance run certifies exactly this:

> On this fixture, against this obligation register, a runtime under this
> profile exhibited the observable behaviour every portable core case
> requires.

It does not certify that the runtime is secure, that it will behave the same
tomorrow, that a different build of it behaves the same, or that behaviour the
suite did not attempt is correct. It is a floor, and it is stated as one.

Three things in particular are outside it, and naming them is not modesty —
each is something an implementer would otherwise be entitled to read into a
green result:

| Not certified | Why |
| --- | --- |
| absence of secrets | canary scans prove the scan RAN and found what was planted. They cannot prove nothing else is present, so §7.F requires a residual-risk statement rather than a claim of absence |
| behaviour under unattempted faults | a case whose fault could not be injected is `unable` and denies certification; it is never quietly passed |
| a different build | a profile certifies the exact adapter build and runtime profile digests the fixture bound. A new build is a new run |

## 2. The obligation register

`evidence/obligations.json` is the register: **70 obligations** across eight
families, each carrying

- `source` — the exact clause of W151, W1439 or W1440 it comes from;
- `statement` — the normative requirement in one sentence;
- `observable` — **what the harness can see that bears on it**;
- `verdict` — what makes it `passed`, what makes it `failed`, and what makes
  it `unable`; and
- `cases` — the concrete vectors that decide it.

The `observable` and `verdict` fields are the assignment's acceptance
boundary, and they are mandatory rather than conventional: a test asserts that
no obligation is missing either. An assertion that does not say what would be
seen if it were violated is prose, and prose in a conformance suite reads as
coverage while providing none.

### 2.1 The register covers the frozen vocabularies mechanically

The register does not claim completeness; it is checked for it. The tests load
the two approved schemas and the approved agent-session model and assert that
the register's `covers` metadata accounts for:

| Vocabulary | Owner | Count |
| --- | --- | --- |
| control message kinds | W1439 | 17 of 17 |
| error category/code pairs | W1439 §11 | 31 of 31 |
| manifest and receipt schemas | W1439 §8 | 10 of 10 |
| turn outcomes | W1440 §5.2 | 8 of 8 |
| agent-session states | W1440 §7.3 | 9 of 9 |
| normalized event kinds | W1440 §6.1 | 10 of 10 |
| approval families | W1440 §10.5 | 4 of 4 |
| typed scheduler gates | W151 | 3 of 3 |

If either upstream contract adds a member, this suite fails a test rather than
silently ceasing to cover it. That is the whole reason the check is mechanical:
a coverage claim maintained by hand decays exactly when the contract moves,
which is exactly when coverage matters.

## 3. The harness and the black-box rule

Three roles, and the boundary between them is the point:

| Role | Does | Never |
| --- | --- | --- |
| Driver | orders the case's `stimulus`: control operations, in-runtime probes, authority reads, agent scripts, and the faults the case requires | inspects runtime internals |
| Observer | reads the observable surfaces of §3.1 and files one observation of machine-readable FACTS per case | judges — **an observation carries no verdict at all** |
| Assessor | applies each case's executable `expectation` to those facts, derives `passed`/`failed`/`unable`, and produces the report | re-runs anything |

**The observation document has no verdict field.** This is structural rather
than procedural: an observer that could write `passed` would be a component
that both causes an outcome and declares it, and such a component can arrange
to see what it expected. The schema gives it nowhere to record a conclusion,
so the only thing it can contribute is what it saw.

This mirrors W151's split between a verifier's raw `report` and a reviewer's
separate `assess`, and it is the same reason.

### 3.0 Stimulus and expectation

Every case carries two machine-readable halves:

- **`stimulus`** — what the driver orders: a kind (`control-operation`,
  `in-runtime-probe`, `authority-read`, `agent-script`, `workflow-receipt`),
  the control kinds involved, the faults required, and a portable description.
  No host command, no vendor API.
- **`expectation`** — how the assessor decides, as predicates over named facts:

  | Kind | Decided by |
  | --- | --- |
  | `control-refusal` | the observed `refusal` fact equals the exact expected pair, plus any further predicates |
  | `control-success` | all predicates hold and no refusal was observed |
  | `invariant` | all predicates hold over probe or authority facts |

Each case also declares `required_facts`, which must be exactly the facts its
expectation reads — a fact nobody reads is not required, and a fact read but
not required could be absent when the assessor went looking. An observation
missing any of them is INADMISSIBLE rather than failing: the suite could not
decide, so it does not get to.

### 3.1 The observable surfaces, exhaustively

An observation may be founded ONLY on:

1. control-protocol frames at the manager boundary, including error frames;
2. durable manifests and workflow receipts;
3. artifact bytes and their recomputed digests;
4. the authority's read-only projections;
5. adapter-reported runtime observations, treated as reports rather than facts
   (W1439 §6.2); and
6. what the runtime itself can reach, probed from inside it by fixture-planted
   probes whose results cross back as ordinary declared output.

**Nothing else.** Not the container runtime's API, not the host process table,
not the adapter's private state, not provider telemetry. Those would certify
one implementation's internals, and the next runtime would have different ones
— which is precisely how a "runtime-neutral" suite stops being one.

Surface 6 deserves its own sentence, because it is the only way to observe
isolation at all. The probe is part of the fixture, it runs as ordinary worker
code under the ordinary policy, and its findings return through the declared
output path like any other result. It receives no special capability; if it
did, it would be measuring a runtime that does not exist.

### 3.2 The core gate runs no model

The scripted agent endpoint speaks the profile's protocol deterministically
from a digest-bound script. `scripted_agent.model_provider_required` is pinned
to `false` and the schema permits no other value.

This is a correctness requirement, not a cost one. A case whose outcome
depends on what a model chose to say has no stable expected result, so it
cannot fail in a way anyone can act on. A suite built from such cases reports
weather.

### 3.3 Faults are ordered, not awaited

The matrix requires races, restarts, partitions and expiries. These do not
happen reliably by waiting, so the harness ORDERS them: the fixture declares
its `fault_capabilities` from the closed set of 20, and a case declares the
`required_faults` it needs.

**A case whose required faults the fixture cannot inject is `unable`.** Not
skipped, not passed, not "not applicable". §6 makes `unable` deny
certification, which is the only arrangement in which "we could not test the
partition behaviour" and "the partition behaviour is correct" stay
distinguishable.

## 4. Fixtures

A fixture is a sealed document binding one certification run's inputs:
profile and locality, `work_ref`, the input/policy/runtime-profile and
agent-session-profile digests, the scripted agent, the fault capabilities, and
a canary plan.

Three rules are enforced rather than described:

- **Remoteness is decided from facts, not from the label.** The fixture
  carries a `host_identity` block, and a `remote` fixture is refused unless
  `runtime_host_id` differs from `manager_host_id` and
  `workspace_path_resolves_on_manager` is false. It must also declare both
  `transport-partition` and `host-restart` among its capabilities. A profile
  that cannot be partitioned or restarted out from under the manager is a
  local one wearing a different label, and `locality: remote` is a string
  anyone can type.
- **A fixture must be able to inject every fault the portable core IT RUNS
  needs.** The mandatory set is derived from that profile's core (§8.3), so an
  admitted fixture can always attempt every case it will be assessed on. One
  that cannot is refused at validation rather than discovered case by case as a
  run full of `unable`.
- **The canary plan covers every surface** W1439 §9 names — all ten. A
  fixture that plants canaries in some surfaces certifies a scan of some
  surfaces, and §7.F's obligation is that each named surface was actually
  reached.

## 5. Observations

One observation per case, sealed, bound to the exact case digest and the exact
fixture digest. Binding by digest rather than by identifier is what stops an
observation of one revision of a case from being counted for another.

An observation has exactly two shapes:

- `status: "observed"` — it carries a non-empty `facts` map and no
  `blocked_by`.
- `status: "blocked"` — it carries `blocked_by` and no facts.

It does not carry a conclusion in either shape.

**The evidence purposes must equal the case's `deciding_evidence`.** Not
intersect — equal. A sealed claim that some artifact exists is not an
observation of the property under test, and an observation supported by
material of a kind the case never said would decide it is unsupported in
exactly the way that is hardest to notice.

### 5.1 The three assessments are W151's, unchanged

`passed`, `failed`, `unable` — the same vocabulary a verifier reports under
W151 §7, deliberately not a new one. They are DERIVED by the assessor:

- `passed` — every clause of the case's expectation held over the facts.
- `failed` — some clause did not.
- `unable` — the observation was blocked, or the case required a fault the
  fixture could not inject. **It is not a pass.**

A blocked observation MUST name what was missing, in `blocked_by`. One with no
named cause is an untested case wearing a result, and the schema refuses it
rather than merely discouraging it.

### 5.2 A negative case passes only on its exact refusal

This is the single most important rule in the document, so it is stated
flatly.

**43 of the 110 cases are `control-refusal`.** Such a case passes when the
implementation REFUSED, with the exact category/code pair from W1439's closed
taxonomy that the case names. It does not pass because the operation "did not
succeed".

The reason is concrete. "The request was refused with `stale-assignment.
generation`" and "the request was dropped, timed out, crashed the adapter, or
was silently ignored" are the same observation to a suite that only checks for
absence of success — and the second family of behaviours is a broken runtime.
A suite that accepted them would certify exactly the implementations most in
need of failing.

The assessor enforces the same rule in the other direction: a
`control-success` or `invariant` case whose facts include a refusal FAILS,
because something was refused that should not have been.

### 5.2.1 An invariant is not a refused control operation

A further 44 cases are `invariant`, and they are decided from probe or
authority facts with **no error pair at all**.

This distinction is load-bearing. W1439 §6.5 and §11 define `control.error`
for control-protocol errors. Nothing in W151, W1439 or W1440 requires a
filesystem denial inside a runtime, an absent mount, or a negative reading of
gate-clearance evidence to synthesize a control frame. Requiring one would be
this suite inventing a runtime interface rule — the precise thing §0 forbids,
and the precise thing a conformance suite is worst placed to do.

So a probe that could not write into an input path reports
`input_write_succeeded: false`, and that is what decides the case. A test
asserts that no case whose stimulus is an in-runtime probe or an authority read
carries a `control-refusal` expectation.

### 5.3 A pass requires that the case could be attempted

Facts satisfying an expectation do not yield `passed` when the case's
`required_faults` exceed the fixture's `fault_capabilities`; the assessment
becomes `unable`. And `validate_fixture` refuses outright a fixture that
cannot inject every fault the portable core needs, so the condition should
never arise in a real run.

Without this the incentive runs the wrong way: the cheapest path to a clean
run would be a fixture that can inject nothing.

## 6. The verdict

### 6.1 The rule

A profile is `certified` for a fixture when, for that run:

- every portable core case FOR THAT PROFILE (§8.3) has exactly one
  observation, and
- every one of those cases is assessed `passed`.

Any `failed`, any `unable`, any unobserved core case, or any case observed
twice, yields `not-certified` with the reason named.

### 6.2 There is no verdict to read

The run document has no `verdict` field and no `counts`, and neither does an
observation. The assessor DERIVES every case assessment from facts and the
verdict from those assessments, and publishes both in a separate sealed
`report`.

The earlier revision of this contract let a run carry its own verdict and
merely promised to recompute it. That promise held in the model and told an
implementer nothing: a document that carries a conclusion invites being
trusted for it. Removing the field is the enforcement.

### 6.3 Supplemental cases cannot compensate

Runtime-specific supplemental cases are welcome (§9) and are reported
separately. They never enter the verdict. A portable core failure with twenty
supplemental passes beside it is a portable core failure, because the core is
what the contract says and the supplement is what one runtime happens to also
do.

### 6.4 Counts and elapsed time certify nothing

"107 of 110 passed" is not a partial certification; it is `not-certified` with
three named cases. Elapsed time is not evidence at all: a runtime that
finished quickly and a runtime that finished quickly because it did nothing
produce the same duration.

This is W151's rule for trials, restated because it is the most tempting one
to soften: counts and elapsed time never decide anything.

### 6.5 The suite emits a signal; route policy is not its decision

A report whose portable core did not pass carries a `profile_signal` bound to
the fixture's `runtime_profile_digest` and `adapter_build_digest`, naming the
failed and undecided cases, addressed to the `route-policy` consumer:

| Report | Signal |
| --- | --- |
| certified | `none`, with empty case lists |
| one core case failed | `probation` |
| more than one core case failed | `disablement` |
| core undecided but nothing failed | `probation` |

The split of responsibility is deliberate in both directions. Emitting nothing
would leave a route-policy consumer with no input and make "this profile keeps
failing" a thing only a human reading reports could notice. Deciding here would
put the suite in charge of routing, which is policy — and W151 §7 keeps policy
with the endpoints that own it. So the suite states what it observed about a
profile, and something else decides what to do about it.

The suite mutating route policy or profile certification directly is itself a
portable core case (`G-verdict-is-not-policy`).

## 7. The portable case matrix

**110 portable core cases** in eight families: 23 `control-success`,
43 `control-refusal` and 44 `invariant`. All 110 apply to `remote`; 109 apply
to `local-oci` (§8.3). Every one is a sealed document in
`evidence/cases.json` naming its obligations, its machine-readable stimulus
and expectation, the facts that expectation reads, its required faults, and
the evidence purposes that decide it.

| Family | Cases | Covers |
| --- | --- | --- |
| **A** source and output | 15 (7 success, 5 refusal, 3 invariant) | exact base revision, moved-ref refusal, exact directory tree, read-only inputs, traversal/symlink/overlap refusal, freeze after quiescence, digest recomputation, exact replay and changed-byte refusal, undeclared paths uncollected, missing required output, proposal is not a push, ambiguous collection |
| **B** isolation | 8 (8 invariant) | no authority capability, no Baton executable, no canonical repository, private Git metadata, cross-worker isolation, network, resource and tool policy |
| **C** claim and authority | 16 (2 success, 8 refusal, 6 invariant) | pre-claim metadata only, no pre-claim execution, token expiry/replay/binding, **decline carries no bearer**, **a bearer-carrying decline refused**, **a differently bound decline terminates nothing**, ambiguous claim grants nothing, settlement by exact operation, nothing writable before activation, assignment manifest after claim, stale-generation activity/result/proposal, activity changes no state |
| **D** cancellation and quiescence | 12 (4 success, 4 refusal, 4 invariant) | fence before stop, cancel reply is not death, quiescent is not destroyed, destroyed clears the gate, uncertain quiescence, replacement gated, late publication refused, output sealed, discard needs policy, slot freed immediately, agent quiescence is not runtime quiescence, retention policy |
| **E** restart, retry and partition | 13 (8 success, 4 refusal, 1 invariant) | manager restart reconciliation, **adapter restart**, **remote host restart**, exact replay, operation collision, duplicate observation, observation regression, duplicate frame, partition reattachment proof, reachability is not identity, duplicate runtime start, agent transport loss, cleanup blocked on intake |
| **F** credentials and leakage | 9 (1 success, 2 refusal, 6 invariant) | no credential in manifests or events, a canary in every named surface, leak refuses publication, credential lifetime, **assignment-scoped delivery**, **no cross-assignment reuse**, **expiry mid-run**, residual risk reported |
| **G** policy and integrity | 22 (1 success, 15 refusal, 6 invariant) | mode unavailable, policy drift, approval refusal and race, provider-valid denial payloads, untrusted output, prose decides nothing, proposal integrity, receipt immutability, version/capability/extension refusal, uncertified profile, plan rejection, typed error frames, three unavailable dependencies, stale contract, stale target, verdict is not policy, **profile failure signal** |
| **H** agent session | 15 (5 refusal, 10 invariant) | capability withheld, unadvertised method refused, fresh sessions, history methods refused, consent then execution, all eight turn outcomes, disposition gating, event normalization, event integrity, overflow counted, cancellation observed, drain unknown, monotonic axis, provider id is not identity, agent holds no capability |

The per-case detail lives in `evidence/cases.json` rather than here, because a
matrix duplicated in prose is a matrix that will disagree with itself. §12.2
requires the two to agree in both directions, and a test enforces it.

### 7.1 The isolation family needs a probe, and the probe is ordinary

Family B is the only family that cannot be decided from the manager's side.
"Can this runtime reach the canonical repository?" is a question only something
inside the runtime can answer.

So the fixture ships a probe that runs as ordinary worker code, under the
ordinary pinned policy, with no capability a real worker would not have, and
reports through the declared output path. Its report is untrusted worker
output like any other (W1439 §13).

All eight of family B's cases are therefore `invariant`, decided from probe
facts such as `authority_home_reachable` and `canonical_repository_reachable`.
None of them expects a control frame, because none of them IS a control
operation: a filesystem denial inside a runtime is not a protocol error, and
requiring the runtime to manufacture one would be this suite inventing an
interface (§5.2.1).

The facts are stated in the negative — "the probe could not reach it" — and
that is the honest shape. A probe reporting that it DID reach something is
strong evidence of a failure; a probe reporting that it did not is what a
correct runtime produces, and the case is decided on both the reachability
fact and the accompanying denial fact rather than on the probe's word alone.

## 8. Profiles

Two profiles, running the SAME normative core. The profile says where the
vectors run, never which vectors run.

### 8.1 `local-oci`

An OCI runtime on the manager's host, asserted by `runtime_host_id` equalling
`manager_host_id`. It must be able to inject every fault the portable core it
runs requires, plus the scripted agent endpoint.

### 8.2 `remote`

A runtime host that is **not** the manager host. This is asserted from
machine-readable facts, not declared:

| Assertion | Where it is enforced |
| --- | --- |
| `host_identity.runtime_host_id` differs from `manager_host_id` | `validate_fixture` |
| `host_identity.workspace_path_resolves_on_manager` is false | the schema, and `validate_fixture` |
| an injected partition changes the manager's observations | case `E-partition-reattach-proof` |
| an injected host restart leaves the runtime uncertain | case `E-remote-host-restart` |

The last two are the ones that matter. The first two can both be arranged in
an elaborate local setup, and `locality: remote` is a string anyone can type.
Only a partition and a host restart that actually change what the manager
observes demonstrate that there is a network between them — and family E,
which exists almost entirely to test partition and restart behaviour, would
otherwise be certifying local behaviour under a remote name.

### 8.3 A profile may not narrow its own core

`local-oci` runs 109 portable core cases and `remote` runs all 110. That is
not an exemption, and the one-case difference is the only one the contract
permits.

A case carries `applies_to`, and it may exclude a profile ONLY when the fault
it requires cannot exist on that profile. Exactly one case does:
`E-remote-host-restart` requires `host-restart`, and a local runtime's host IS
the manager's host — restarting it is `manager-restart`, which is in the common
core as `E-manager-restart-reconciles`. There is no separate host to restart,
so this is a fault that does not exist locally rather than one a local profile
is let off.

The model enforces the rule rather than trusting the data: a case that excludes
a profile without requiring a fault from that profile's `PROFILE_ONLY_FAULTS`
is refused, and a run that observes a case outside its profile's core is
refused too.

The earlier revision of this contract got this wrong in a way worth recording,
because it is the failure mode `applies_to` exists to prevent. It made
`E-remote-host-restart` universal while exempting `local-oci` from
`host-restart` in fixture validation — so a local fixture was ADMITTED and then
necessarily failed certification as `unable`. That is not a runtime failing a
test; it is the suite's admission rules contradicting its assessment rules, and
it would have read as a runtime defect to whoever ran it. Fixture validation
now derives its mandatory faults from the core each profile actually runs, so
an admitted fixture can always attempt every case it will be assessed on.

## 9. Runtime-specific extensions

A runtime may add supplemental cases with `scope: runtime-supplemental`: extra
isolation properties, vendor attestations, performance floors.

**A run carries its own supplemental case definitions**, in
`supplemental_cases`, sealed and shaped exactly like a portable core case. It
has to: the register fixes the portable core, so a runtime-specific case has
nowhere else to come from. The earlier revision permitted the `scope` value and
provided no way to bind a definition, which made such a case a valid document
that no run could assess — the advertised extension point refused every use.

They are accepted, assessed and reported under the same rules as core cases —
same shape and seal, same fact admissibility, same derived assessment — with
three differences.

**A supplemental case names no register obligation, and declares its own
source instead.** It carries `supplemental_source`: a reverse-DNS namespace
with an explicit version, such as `com.example.runtime/1`, whose pattern
deliberately cannot look like an obligation identifier. A portable core case
carries at least one obligation and no source; a supplemental case carries a
source and no obligations, and the schema enforces both directions.

The earlier revision required every case to cite an obligation, which forced a
supplemental case to claim one it does not implement. Its own worked example
demonstrated the problem: a vendor attestation citing `G-04`, whose obligation
is proposal-digest integrity. That citation was false, and it was the only way
the example could validate. An additional property need not implement one of
this contract's obligations, and the register cannot backlink a case it has
never seen — so a citation there could only ever be a claim nobody checks.

**Its assessment appears in the report's `supplemental` list**, never in
`assessed`, and never in the verdict.

**Once a run binds a definition, that definition is accounted for.** Exactly
one applicable observation, or an explicit `unable` naming that it was declared
and never observed. It is never simply absent from the report — otherwise a
producer could advertise an extension and quietly suppress its failed or
blocked execution, which is reporting in name only.

Three further rules keep the boundary honest: a supplemental case may not reuse
a portable core case identifier; a run may not present a case declaring
`scope: portable-core`; and a bound definition must apply to the fixture's
profile, so a local run cannot assess a supplement that declares itself
remote-only. Without the first two a run could redefine the contract it is
being measured against.

They cannot enter the verdict (§6.3), and they cannot replace a core case. The
asymmetry is deliberate: a runtime is free to prove more than the contract
requires and is never free to prove something else instead.

## 10. Evidence retention

Every observation carries at least one evidence reference, using W1439 §9's
artifact reference and its closed purpose set. Each case names the evidence
purposes that DECIDE it, so an observation supported only by material of some
other kind is visibly unsupported.

Evidence is retained under W1439's rules: credential-free locators, no
userinfo, no query, no fragment; redaction at the trust boundary before
anything is durable. The suite generates no exception to those rules for its
own convenience — a conformance harness that leaked a credential while proving
a runtime does not would be a memorable way to fail.

### 10.1 Residual risk is derived, not supplied

The report's `residual_risk` is computed from the accepted facts of
`F-canary-each-surface` and from the verdict. `surfaces_scanned` is what that
case's facts say was scanned, and only when the case PASSED;
`surfaces_not_scanned` is the complement over the closed vocabulary. The two
are disjoint and partition the ten surfaces by construction, because they are
computed rather than stated.

`build_report` takes no residual-risk argument at all. The earlier revision
accepted one from the caller and sealed it unexamined, which let a fully
certified report — over a run whose own facts said all ten surfaces were
scanned — state that none were. A derived document with one caller-supplied
member is a document trusted for something it never established, and the member
it is trusted for is the one nobody derived.

The `unproven` statement always carries the standing sentence that redaction is
not proof of absence, and gains a line naming any unscanned surface and a line
noting that nothing above a failing or undecided case is established.

## 11. What does not certify

Collected in one place, because each is something a reader might otherwise
take a green run to mean:

- **A count.** 107 of 110 is `not-certified` with three named cases.
- **Elapsed time.** It distinguishes nothing, least of all a runtime that did
  nothing quickly.
- **A provider's claim.** A vendor attestation is supplemental evidence, never
  a case result.
- **A previous run.** Certification binds the fixture, the register digest and
  the adapter and profile digests. Any of them changing requires a new run.
- **A run's own verdict field.** There is none: a run carries observations, and the verdict lives in a separate derived report (§6.2).
- **A declared observation.** An observer records facts; it has nowhere to record a conclusion (§3).
- **Absence of a failure.** Only an observation of the required behaviour
  passes a case; nothing observed is `unable`.
- **A supplemental pass.** It never offsets a core failure.
- **This suite passing.** It certifies the observable floor in §1 and nothing
  above it.

## 12. Required semantic validation beyond JSON Schema

A conforming harness proves all of these:

1. Every definition reproduced from W1439 is byte-identical to the frozen one.
2. The register and the case matrix agree in BOTH directions: every case a
   register entry cites exists, and every case names exactly the obligations
   that cite it.
3. Every obligation names its source clause, its observable evidence, and what
   makes it each of `passed`, `failed` and `unable`.
4. The register's coverage accounts for every member of every closed
   vocabulary listed in §2.1.
5. Every `control-refusal` case names a category/code pair that exists in
   W1439 §11, and no other kind of case names one. No case whose stimulus is
   an in-runtime probe or an authority read is a `control-refusal`.
5a. Every case carries an executable expectation, and its `required_facts` are
   exactly the facts that expectation reads.
6. Every fixture, case, observation and run is shape-valid and seal-valid, and
   is accepted before any of its fields is read.
7. An observation is bound to the exact case digest and fixture digest it was
   made against, and its evidence purposes EQUAL the case's deciding evidence.
8. An observation carries facts and no conclusion; every assessment is derived
   by applying the case's expectation to those facts.
9. An observation missing any of the case's `required_facts` is inadmissible —
   the suite could not decide, so it does not.
10. A `control-refusal` case is assessed `passed` only on its exact expected
    refusal, and a `control-success` or `invariant` case that observed a
    refusal fails.
11. A case is assessed `passed` only when the fixture could inject every fault
    it requires, and a fixture that cannot inject every fault the portable
    core needs is refused outright.
12. A blocked observation names its cause.
13. A case is observed at most once per run.
14. Supplemental cases never enter the verdict.
15. A run is refused if it names a different obligation register, a different
    fixture, or a different profile than the fixture being assessed.
16. Remote locality is decided from `host_identity`, never from the `locality`
    label, and a remote fixture can inject both a partition and a host restart.
16a. A case excludes a profile only when it requires a fault that profile
    cannot have, and a run never observes a case outside its profile's core.
16b. A run's supplemental case definitions are accepted, assessed and reported
    separately; none reuses a core identifier, declares `portable-core`, cites a
    register obligation, or applies to a profile other than the fixture's. Each
    declares a namespaced `supplemental_source` that cannot be mistaken for an
    obligation identifier, and each is accounted for in the report by exactly
    one observation or an explicit `unable`.
16c. The report's residual risk is derived from accepted facts; its two surface
    sets are disjoint and partition the closed surface vocabulary.
17. The core gate declares no model-provider dependency.
18. The canary plan covers every surface W1439 §9 names.
19. A report whose portable core did not pass emits a profile signal bound to
    the runtime-profile and adapter build digests, naming its failed and
    undecided cases.

## 13. Design evidence and approval boundary

- `schema/conformance-1.0.schema.json` — the shape contract for the fixture,
  case, observation and run documents.
- `evidence/obligations.json` — the 69-obligation register and the two profile
  definitions.
- `evidence/cases.json` — the 110 sealed portable core cases, each with its
  machine-readable stimulus, executable expectation and profile applicability.
- `evidence/build_cases.py` — the one place the matrix is authored, so no prose
  copy of it can disagree with it.
- `evidence/conformance_model.py`, `evidence/test_conformance_model.py` — the
  executable design model and its 73 tests, composing with both approved
  upstream contracts.

All of it is design evidence. It imports no Baton or `v12/` product code, runs
without a model provider, certifies no runtime, and starts no container.

Approval is requested for these decisions as one compatible set:

1. **The suite adds no rule to the contracts it tests**; every obligation
   cites its source clause (§0).
2. **Coverage of the frozen vocabularies is mechanical, not claimed** — the
   register is checked against the approved schemas and model, so an upstream
   addition fails a test rather than silently escaping coverage (§2.1).
3. **The observable surface is closed and excludes runtime internals**, with
   isolation observed through an ordinary in-runtime probe holding no special
   capability (§3.1, §7.1).
4. **The core gate is deterministic and model-free** (§3.2).
4a. **The observer records facts and holds no verdict; the assessor derives
   every assessment from those facts and a case's executable expectation**, and
   neither an observation nor a run has a field in which to declare a result
   (§3, §5, §6.2).
5. **Faults are ordered, and an uninjectable fault yields `unable`, which
   denies certification** (§3.3, §5.3, §6.1).
6. **A `control-refusal` case passes only on its exact expected refusal**;
   absence of success is not a refusal (§5.2). **An `invariant` case is decided
   from probe or authority facts and synthesizes no control frame**, because no
   upstream contract requires one (§5.2.1).
7. **The verdict is recomputed from observations; counts, elapsed time, a
   declared verdict and supplemental passes decide nothing** (§6.2–§6.4).
8. **Both profiles run the same core, and `remote` must be demonstrably
   remote** — from host-identity facts, an injected partition, and an injected
   host restart that each change what the manager observes (§8.2).
9. **The suite emits a profile signal for a route-policy consumer and chooses
   no policy itself** (§6.5).
10. **A profile may not narrow its own core**: a case excludes a profile only
   when it requires a fault that profile cannot have, and fixture admission is
   derived from the core each profile runs, so an admitted fixture can always
   attempt every case it is assessed on (§8.3).
11. **A run carries its own supplemental case definitions**, accepted and
   assessed under the same rules and reported separately from the verdict. Each
   names no register obligation and declares a namespaced source instead, must
   apply to the fixture's profile, and is accounted for by exactly one
   observation or an explicit `unable` (§9).
12. **Residual risk is derived from accepted facts, never supplied**, so a
   report cannot contradict the run it certified (§10.1).

Approval freezes this conformance vocabulary for M1. It does not certify any
runtime, authorize any implementation, or make a passing run mean more than
§1 says it means.
