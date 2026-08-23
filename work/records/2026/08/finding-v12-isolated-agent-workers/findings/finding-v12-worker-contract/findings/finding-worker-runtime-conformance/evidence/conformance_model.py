"""Executable design model for baton.worker-conformance 1.0.

Provider-free evidence, not product code.  It models the rules a conformance
harness must obey that JSON Schema cannot express: what makes an observation
admissible, how the ASSESSOR derives a verdict from observed facts, and what
makes a profile certified.

The separation that matters is between the observer and the assessor.  An
observation carries FACTS and no verdict; `assess` applies the case's
executable expectation to those facts.  A component that both causes an
outcome and declares it can arrange to see what it expected, and a suite built
that way certifies its own claims.

It composes with the two approved upstream models rather than restating their
vocabularies, so a register that stops covering the frozen contracts fails a
test instead of drifting.

Nothing here imports Baton or v12/ product code, and nothing here reaches a
model provider.
"""

from __future__ import annotations

import copy
import hashlib
import json
import pathlib
from dataclasses import dataclass, field

from jsonschema import Draft202012Validator

HERE = pathlib.Path(__file__).resolve().parent
RECORD = HERE.parent
SIBLINGS = RECORD.parent
WORKER_CONTROL_SCHEMA_PATH = (SIBLINGS / "finding-worker-control-api-manifests"
                              / "schema" / "worker-control-1.0.schema.json")
AGENT_SESSION_SCHEMA_PATH = (SIBLINGS / "finding-acp-agent-boundary"
                             / "schema" / "agent-session-1.0.schema.json")
SCHEMA_PATH = RECORD / "schema" / "conformance-1.0.schema.json"
OBLIGATIONS_PATH = HERE / "obligations.json"
CASES_PATH = HERE / "cases.json"


class ConformanceError(ValueError):
    """A refusal by the suite contract itself, not a case result.

    Deliberately distinct from a case failing: a case that fails says the
    runtime is wrong, while this says the suite was not entitled to an opinion.
    """


# --------------------------------------------------------------------------
# Canonicalization, shared verbatim with the two upstream contracts.
# --------------------------------------------------------------------------

def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode()


def digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def seal_document(document: dict) -> dict:
    sealed = copy.deepcopy(document)
    sealed.pop("document_digest", None)
    sealed["document_digest"] = digest(sealed)
    return sealed


def verify_document_digest(document: dict) -> None:
    candidate = copy.deepcopy(document)
    recorded = candidate.pop("document_digest", None)
    if recorded != digest(candidate):
        raise ConformanceError("document digest mismatch")


SCHEMA = json.loads(SCHEMA_PATH.read_text())
_DOCUMENT_VALIDATOR = Draft202012Validator(SCHEMA)

SHARED_WORKER_CONTROL_DEFS = (
    "digest", "opaqueId", "timestamp", "participant",
    "workRef", "artifactRef", "evidenceRef",
)


def validate_document_shape(document: dict) -> None:
    error = next(_DOCUMENT_VALIDATOR.iter_errors(document), None)
    if error is not None:
        raise ConformanceError(
            "document does not satisfy worker-conformance 1.0: " + error.message)


def accept_document(document: dict, expected_kind: str) -> dict:
    """Shape, then seal, then a private copy — the W1440 ordering, unchanged.

    Nothing below may read a field of a document that has not been through
    here, because reading a field out of a document whose seal was never
    verified is reading whatever the last writer put there.
    """
    validate_document_shape(document)
    verify_document_digest(document)
    if document.get("document") != expected_kind:
        raise ConformanceError(
            "expected a " + expected_kind + " document, got " + repr(document.get("document")))
    return copy.deepcopy(document)


# --------------------------------------------------------------------------
# The register
# --------------------------------------------------------------------------

OBLIGATIONS = json.loads(OBLIGATIONS_PATH.read_text())
CASES = json.loads(CASES_PATH.read_text())
OBLIGATIONS_DIGEST = digest(OBLIGATIONS)

OBLIGATION_BY_ID = {o["id"]: o for o in OBLIGATIONS["obligations"]}
CASE_BY_ID = {c["case_id"]: c for c in CASES["cases"]}
PROFILE_BY_ID = {p["id"]: p for p in OBLIGATIONS["profiles"]}

ASSESSMENTS = frozenset({"passed", "failed", "unable"})
CANARY_SURFACES = frozenset(SCHEMA["$defs"]["canarySurface"]["enum"])
FAULT_CAPABILITIES = frozenset(SCHEMA["$defs"]["faultCapability"]["enum"])

# §8.3 — a case may be scoped to one profile ONLY when the fault it requires
# cannot exist on the other.  A local runtime's host IS the manager's host, so
# restarting it is `manager-restart`, which is in the common core; there is no
# separate host to restart.  Without this rule "applies_to" would be a way for
# a profile to narrow its own contract, which is exactly what §8.3 forbids.
PROFILE_ONLY_FAULTS = {"remote": frozenset({"host-restart"}),
                       "local-oci": frozenset()}


def core_for(profile: str) -> set:
    """The portable core a profile is certified against."""
    return {c["case_id"] for c in CASES["cases"]
            if c["scope"] == "portable-core" and profile in c["applies_to"]}


def _mandatory_faults(profile: str) -> frozenset:
    return frozenset(f for c in CASES["cases"]
                     if c["case_id"] in core_for(profile) for f in c["required_faults"])


# Derived from the core each profile actually runs, so an admitted fixture can
# always attempt every case it will be assessed on.  An earlier revision
# hard-coded an exemption here while leaving the case universal, which admitted
# a local fixture that then necessarily failed as 'unable'.
MANDATORY_FAULTS_BY_PROFILE = {profile: _mandatory_faults(profile)
                               for profile in ("local-oci", "remote")}


def obligations_covering(case_id: str) -> list:
    return sorted(o["id"] for o in OBLIGATIONS["obligations"] if case_id in o["cases"])


def covered(key: str) -> set:
    """Everything the register claims to cover under one vocabulary key."""
    found = set()
    for o in OBLIGATIONS["obligations"]:
        for value in o["covers"].get(key, []):
            found.add(tuple(value) if isinstance(value, list) else value)
    return found


# --------------------------------------------------------------------------
# Fixtures and cases
# --------------------------------------------------------------------------

def validate_fixture(fixture: dict) -> dict:
    accepted = accept_document(fixture, "fixture")
    profile = PROFILE_BY_ID.get(accepted["profile"])
    if profile is None:
        raise ConformanceError("unknown profile " + repr(accepted["profile"]))
    if accepted["locality"] != profile["locality"]:
        raise ConformanceError(
            "profile " + profile["id"] + " is " + profile["locality"]
            + "; the fixture claims " + accepted["locality"])

    if accepted["scripted_agent"]["model_provider_required"] is not False:
        raise ConformanceError(
            "the core gate runs against a scripted endpoint; a case whose outcome depends "
            "on what a model chose to say certifies nothing")

    hosts = accepted["host_identity"]
    if profile["locality"] == "remote":
        # SPEC §8.2 — remoteness is decided from facts, not from the label.
        if hosts["runtime_host_id"] == hosts["manager_host_id"]:
            raise ConformanceError(
                "a remote profile runs on a host that is not the manager's; these are the same")
        if hosts["workspace_path_resolves_on_manager"] is not False:
            raise ConformanceError(
                "the manager resolves the workspace path locally, so the runtime is not remote")
    elif hosts["runtime_host_id"] != hosts["manager_host_id"]:
        raise ConformanceError(
            "a local profile runs on the manager's host; these differ")

    surfaces = {c["surface"] for c in accepted["canaries"]}
    if surfaces != CANARY_SURFACES:
        raise ConformanceError(
            "a fixture plants a canary in every named surface; missing "
            + repr(sorted(CANARY_SURFACES - surfaces)))

    missing = MANDATORY_FAULTS_BY_PROFILE[profile["id"]] - set(accepted["fault_capabilities"])
    if missing:
        raise ConformanceError(
            "the portable core needs faults this fixture cannot inject: " + repr(sorted(missing)))
    return accepted


def validate_case(case: dict) -> dict:
    accepted = accept_document(case, "case")
    if accepted["family"] != accepted["case_id"][0]:
        raise ConformanceError("the case family must match its identifier")
    unknown = set(accepted["obligations"]) - set(OBLIGATION_BY_ID)
    if unknown:
        raise ConformanceError("case cites unknown obligations " + repr(sorted(unknown)))

    if accepted["scope"] == "portable-core":
        for oid in accepted["obligations"]:
            if accepted["case_id"] not in OBLIGATION_BY_ID[oid]["cases"]:
                raise ConformanceError(
                    "obligation " + oid + " does not list case " + accepted["case_id"]
                    + "; the register and the matrix must agree in both directions")
        # A supplemental case has no backlink because the register is fixed; a
        # portable core case without one would be a case nobody's obligation
        # decides.
        scoped_out = set(("local-oci", "remote")) - set(accepted["applies_to"])
        for profile in scoped_out:
            other = set(accepted["applies_to"])
            justified = any(set(accepted["required_faults"]) & PROFILE_ONLY_FAULTS[p]
                            for p in other)
            if not justified:
                raise ConformanceError(
                    "case " + accepted["case_id"] + " excludes profile " + profile
                    + " without requiring a fault that profile cannot have; a profile does "
                      "not get a smaller contract")
    else:
        if accepted["case_id"] in CASE_BY_ID:
            raise ConformanceError(
                "a supplemental case may not reuse a portable core case identifier")
        if accepted["obligations"]:
            # An additional property need not implement one of this contract's
            # obligations, and the register cannot backlink a case it has never
            # seen — so citing one could only ever be a false claim.  The
            # earlier revision required a citation, and its own example had to
            # name an unrelated obligation to pass validation.
            raise ConformanceError(
                "a supplemental case names no register obligation; it declares its own "
                "supplemental_source instead")
        if not accepted["supplemental_source"]:
            raise ConformanceError(
                "a supplemental case declares the namespaced source it comes from")

    expectation = accepted["expectation"]
    names = {p["fact"] for p in expectation["requires"]}
    if expectation["kind"] == "control-refusal":
        names.add("refusal")
    if set(accepted["required_facts"]) != names:
        raise ConformanceError(
            "required_facts must be exactly the facts the expectation reads; a fact nobody "
            "reads is not required, and a fact read but not required could be absent")
    return accepted


def faults_available(case: dict, fixture: dict) -> bool:
    return set(case["required_faults"]) <= set(fixture["fault_capabilities"])


# --------------------------------------------------------------------------
# Observations: facts in, nothing else
# --------------------------------------------------------------------------

def accept_observation(observation: dict, case: dict, fixture: dict) -> dict:
    """Whether the suite is ENTITLED to an opinion, not what the opinion is."""
    accepted = accept_document(observation, "observation")
    if accepted["case_id"] != case["case_id"]:
        raise ConformanceError("observation is for a different case")
    if accepted["case_digest"] != case["document_digest"]:
        raise ConformanceError(
            "the observation was made against a different revision of its case")
    if accepted["fixture_digest"] != fixture["document_digest"]:
        raise ConformanceError("the observation was made against a different fixture")

    purposes = {ref["purpose"] for ref in accepted["evidence"]}
    if purposes != set(case["deciding_evidence"]):
        # A sealed claim that some artifact exists is not an observation of the
        # property under test.  The case names the evidence that DECIDES it, so
        # anything else is unsupported and anything missing is undecided.
        raise ConformanceError(
            "the observation's evidence purposes " + repr(sorted(purposes))
            + " are not the deciding evidence " + repr(sorted(case["deciding_evidence"])))

    if accepted["status"] == "observed":
        missing = set(case["required_facts"]) - set(accepted["facts"])
        if missing:
            raise ConformanceError(
                "the observation is missing facts the case's expectation reads: "
                + repr(sorted(missing)))
    return accepted


# --------------------------------------------------------------------------
# The assessor
# --------------------------------------------------------------------------

def _is_empty(value: object) -> bool:
    return value in (None, "", 0, False) or (isinstance(value, (list, dict)) and not value)


def evaluate(predicate: dict, facts: dict) -> bool:
    op = predicate["op"]
    name = predicate["fact"]
    present = name in facts
    if op == "present":
        return present
    if op == "absent":
        return not present or _is_empty(facts[name])
    if not present:
        return False
    value = facts[name]
    if op == "equals":
        return value == predicate.get("value")
    if op == "not-equals":
        return value != predicate.get("value")
    if op == "is-true":
        return value is True
    if op == "is-false":
        return value is False
    if op == "empty":
        return _is_empty(value)
    if op == "non-empty":
        return not _is_empty(value)
    if op in ("subset-of", "disjoint-from"):
        if not isinstance(value, list):
            return False
        expected = set(predicate.get("value") or [])
        return (set(value) <= expected) if op == "subset-of" else not (set(value) & expected)
    raise ConformanceError("unknown predicate operator " + repr(op))


def assess(observation: dict, case: dict) -> tuple:
    """DERIVE the verdict from observed facts.  Returns (assessment, rationale).

    The observation has no say in this beyond the facts it reported.
    """
    if observation["status"] == "blocked":
        return "unable", "blocked: " + str(observation["blocked_by"])

    facts = observation["facts"]
    expectation = case["expectation"]
    unmet = []

    if expectation["kind"] == "control-refusal":
        observed = facts.get("refusal")
        if observed != expectation["expected_refusal"]:
            # Absence of success is not a refusal: a dropped, ignored or
            # crashed request would otherwise read as correct behaviour.
            unmet.append("refusal " + repr(observed) + " is not "
                         + repr(expectation["expected_refusal"]))
    elif "refusal" in facts and facts["refusal"] is not None:
        unmet.append("a non-refusal case observed a refusal: " + repr(facts["refusal"]))

    for predicate in expectation["requires"]:
        if not evaluate(predicate, facts):
            unmet.append(predicate["fact"] + " " + predicate["op"]
                         + ("" if "value" not in predicate else " " + repr(predicate["value"])))

    if unmet:
        return "failed", "; ".join(unmet)
    return "passed", "every clause of the expectation held"


# --------------------------------------------------------------------------
# The verdict and the profile signal
# --------------------------------------------------------------------------

@dataclass
class Report:
    verdict: str
    assessed: list = field(default_factory=list)
    supplemental: list = field(default_factory=list)
    passed: list = field(default_factory=list)
    failed: list = field(default_factory=list)
    unable: list = field(default_factory=list)
    missing: list = field(default_factory=list)
    rationale: str = ""
    signal: dict = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    residual_risk: dict = field(default_factory=dict)


def certify(run: dict, fixture: dict) -> Report:
    """§6 — a profile is certified only by a complete, clean portable core.

    Counts do not appear in this decision and neither does elapsed time; the
    run document carries no verdict at all, so there is nothing here to trust.
    """
    accepted_fixture = validate_fixture(fixture)
    accepted_run = accept_document(run, "run")

    if accepted_run["fixture_digest"] != accepted_fixture["document_digest"]:
        raise ConformanceError("the run names a different fixture")
    if accepted_run["profile"] != accepted_fixture["profile"]:
        raise ConformanceError(
            "the run's profile " + repr(accepted_run["profile"]) + " is not the fixture's "
            + repr(accepted_fixture["profile"]))
    if accepted_run["obligations_digest"] != OBLIGATIONS_DIGEST:
        raise ConformanceError("the run was produced against a different obligation register")

    # §9 — a run brings its own supplemental case definitions, because the
    # register fixes the portable core and a runtime-specific case has nowhere
    # else to come from.  An earlier revision let such a case be a valid
    # document that no run could assess.
    catalogue = dict(CASE_BY_ID)
    bound_supplemental: list = []
    for supplemental in accepted_run["supplemental_cases"]:
        case = validate_case(supplemental)
        if case["scope"] != "runtime-supplemental":
            raise ConformanceError(
                "a run may only carry runtime-supplemental case definitions; the portable "
                "core is fixed by the register")
        if case["case_id"] in catalogue:
            raise ConformanceError("supplemental case " + case["case_id"] + " is already defined")
        if accepted_fixture["profile"] not in case["applies_to"]:
            raise ConformanceError(
                "supplemental case " + case["case_id"] + " does not apply to profile "
                + accepted_fixture["profile"])
        catalogue[case["case_id"]] = case
        bound_supplemental.append(case["case_id"])

    core = core_for(accepted_fixture["profile"])
    seen: set = set()
    report = Report("not-certified")

    for observation in accepted_run["observations"]:
        raw_case = catalogue.get(observation["case_id"])
        if raw_case is None:
            raise ConformanceError("run observes unknown case " + repr(observation["case_id"]))
        case = validate_case(raw_case)
        if case["case_id"] in seen:
            raise ConformanceError(
                "case " + case["case_id"] + " observed twice; a rerun is a new run, not a "
                "second opinion inside one")
        accepted = accept_observation(observation, case, accepted_fixture)
        seen.add(case["case_id"])

        assessment, rationale = assess(accepted, case)
        if assessment == "passed" and not faults_available(case, accepted_fixture):
            # A case that could not be attempted did not pass, whatever facts
            # were reported for it.
            assessment, rationale = "unable", "required faults are not injectable by this fixture"
        entry = {"case_id": case["case_id"], "assessment": assessment,
                 "rationale": rationale}
        if case["scope"] != "portable-core":
            # §6.3 — reported, never counted.
            report.supplemental.append(entry)
            continue
        if case["case_id"] not in core:
            raise ConformanceError(
                "case " + case["case_id"] + " is not in the " + accepted_fixture["profile"]
                + " portable core; it requires a fault that profile cannot have")
        report.assessed.append(entry)
        report.facts[case["case_id"]] = accepted.get("facts", {})
        {"passed": report.passed, "failed": report.failed,
         "unable": report.unable}[assessment].append(case["case_id"])

    report.missing = sorted(core - seen)

    # §9 — once a run binds a supplemental definition it is accounted for, one
    # way or another.  Silently dropping an unobserved one would let a producer
    # advertise an extension and suppress its failed or blocked execution.
    for case_id in bound_supplemental:
        if case_id not in seen:
            report.supplemental.append({
                "case_id": case_id, "assessment": "unable",
                "rationale": "declared by this run but never observed"})

    if report.failed:
        report.rationale = str(len(report.failed)) + " portable core case(s) failed"
    elif report.unable:
        report.rationale = (str(len(report.unable)) + " portable core case(s) could not be "
                            "decided; 'unable' is not a pass")
    elif report.missing:
        report.rationale = str(len(report.missing)) + " portable core case(s) were not observed"
    else:
        report.verdict = "certified"
        report.rationale = "every portable core case was observed and passed"

    report.signal = profile_signal(report, accepted_fixture)
    report.residual_risk = derive_residual_risk(report)
    return report


# The one case whose facts say which surfaces were actually scanned.
CANARY_CASE_ID = "F-canary-each-surface"


def derive_residual_risk(report: Report) -> dict:
    """§10 — derived from accepted facts, never taken from a caller.

    A report that certified a run whose facts say all ten surfaces were scanned
    must not be free to state that none were.  The two sets partition the
    closed surface vocabulary and are disjoint by construction, because they
    are computed rather than supplied.
    """
    scanned: set = set()
    if CANARY_CASE_ID in dict((e["case_id"], e) for e in report.assessed):
        assessment = next(e["assessment"] for e in report.assessed
                          if e["case_id"] == CANARY_CASE_ID)
        if assessment == "passed":
            observed = report.facts.get(CANARY_CASE_ID, {}).get("surfaces_scanned") or []
            scanned = {s for s in observed if s in CANARY_SURFACES}

    unproven = ["redaction is not proof of absence: a canary scan proves the scan ran and "
                "found what was planted, not that nothing else is present"]
    if scanned != CANARY_SURFACES:
        unproven.append("surfaces not scanned in this run: "
                        + repr(sorted(CANARY_SURFACES - scanned)))
    if report.verdict != "certified":
        unproven.append("the portable core did not pass, so nothing above the failing or "
                        "undecided cases is established")
    return {"surfaces_scanned": sorted(scanned),
            "surfaces_not_scanned": sorted(CANARY_SURFACES - scanned),
            "unproven": unproven}


def profile_signal(report: Report, fixture: dict) -> dict:
    """§6.5 — the suite EMITS a signal; a route-policy consumer acts on it.

    Choosing what to do about a failing profile is policy, and policy is not
    a test result.  Emitting nothing would leave the consumer with no input;
    deciding here would put the suite in charge of routing.
    """
    undecided = sorted(report.unable + report.missing)
    if report.verdict == "certified":
        signal = "none"
    elif report.failed:
        signal = "disablement" if len(report.failed) > 1 else "probation"
    else:
        signal = "probation"
    return {"signal": signal,
            "runtime_profile_digest": fixture["runtime_profile_digest"],
            "adapter_build_digest": fixture["adapter_build_digest"],
            "failed_cases": sorted(report.failed),
            "undecided_cases": undecided,
            "consumer": "route-policy"}


def build_report(run: dict, fixture: dict, report_id: str, created_at: str) -> dict:
    """The assessor's own sealed document, derived from the run.

    Every member is computed here.  Nothing is taken from a caller, because a
    caller-supplied field on a derived document is a field the document is
    trusted for without having established it.
    """
    computed = certify(run, fixture)
    return seal_document({
        "suite_family": "baton.worker-conformance",
        "version": {"major": 1, "minor": 0},
        "document": "report",
        "report_id": report_id,
        "created_at": created_at,
        "run_digest": run["document_digest"],
        "fixture_digest": fixture["document_digest"],
        "obligations_digest": OBLIGATIONS_DIGEST,
        "assessed": computed.assessed,
        "supplemental": computed.supplemental,
        "verdict": computed.verdict,
        "verdict_rationale": computed.rationale,
        "profile_signal": computed.signal,
        "residual_risk": computed.residual_risk,
    })


def supplemental_cannot_compensate(run: dict, fixture: dict) -> bool:
    """§6.3 — a runtime-specific pass never offsets a portable core failure."""
    return certify(run, fixture).verdict == "not-certified"
