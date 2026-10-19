"""W325959 revision 3 — one coherent preparation path, exercised.

Review 2026-10-18T20-29-02Z proved four faults in revision 2 and this driver
answers all four by doing:

  R1. The submitted input identity is the PUBLIC `contracts.job_input_identity`
      projection -- revision 2 hashed the whole manifest and the reviewer
      proved the two unequal -- and the runtime consumer boundary
      (`stage_execution._disagreements`, which is `single_worker._matches`'s own
      operand comparison) is asked and answers empty. The duplicate-principals
      TypeError is fixed and the emitted configuration is validated rather than
      noted.
  R2. The documented sequence and the exercised one are the SAME: one
      installation, then the IN-PLACE configuration pass against the installed
      state root, with the install-derived storage selections preserved and the
      binding drift refused.
  R3. `tools.worker_image` BUILDS (build, save, normalize, load, clean). It is
      not a read-only validation and this driver no longer says it is.
  R4. The consumed documents are FROZEN into `inputs/` and digested; the seven
      deployment-accountability identities are named as the concrete missing
      documents, with the four that enter the Job input identity separated from
      the three the projection excludes.

What revision 2 established and this keeps:

  2. "Exercise the complete disposable composition and retain readbacks." The
     FINDING explicitly authorizes deterministic disposable preparation. This
     runs the SUPPORTED bootstrap entry point (`tools.bootstrap.main`, the same
     one `just -f v12/justfile bootstrap` execs) twice in a LABELLED DISPOSABLE
     ROOT -- never the selected destination -- and reads back what it made.
  3. "Actually compose owner and diagnosis ownership." `bootstrap._compose`
     registers worker stage routes only, so this driver performs the owner and
     diagnosis route registrations and proves them the only way that counts:
     the configured handler CLAIMS a Work on that route, and a wrong one is
     refused.
  4. The receipt grants are made per Work and read back, and the owner is
     proved to hold neither `verify` nor `review`.

It also composes the input manifest through `dogfood_operator.input_manifest`
and cross-binds it against the worker document, proves repetition preserves
what is there, proves a drifted selection is refused, and proves the submitted
Job carries no integration stage.

WHAT IT DOES NOT DO. No engine call, no provider call, no credential content
read (the credential SOURCE path is checked for existence only), no image
build, no install into the selected destination, no `start`, no submission to a
manager, and nothing that mutates this repository. The disposable root is
created under the operator's own scratch directory, labelled
`w325959-preflight`, and every identity it generates is labelled PREFLIGHT and
is not a production identity.

Harness: the strict classifier -- `0-harness-self-check` must fail with its own
named `CheckFailed`, a setup or cleanup error counts unexpected, and `main`
refuses the run if the self-check did not fail for its own reason.

Run from `v12/python`:

    PYTHONPATH=src:. python3 <this file> --packet <the dossier> \
        --evidence <directory> --root <a disposable root>
"""
import argparse
import hashlib
import io
import json
import os
import pathlib
import shutil
import time
import traceback
from contextlib import redirect_stdout

LABEL = "w325959-preflight"
BASE = "14e52d80679de5e844f72324df632da5e01cf393"
SELECTED = "/home/sl/baton-instances/native-coordination-pilot-w321608-1"
PREFLIGHT = "PREFLIGHT (W325959 disposable composition; not a production " \
            "identity and not the selected instance)"


class CheckFailed(AssertionError):
    def __init__(self, label, detail=None):
        super().__init__(f"{label} (detail: {detail!r})")
        self.label = label


class Checks:
    def __init__(self):
        self.held = []

    def expect(self, label, condition, detail=None):
        passed = bool(condition)
        self.held.append({"check": label, "passed": passed, "detail": detail})
        if not passed:
            raise CheckFailed(label, detail)
        return passed

    def note(self, label, value):
        self.held.append({"observation": label, "value": value})
        return value

    def document(self):
        return self.held

    def passed(self):
        return sum(1 for one in self.held if one.get("passed"))


def say(place, name, answer):
    (place / name).write_text(
        json.dumps(answer, indent=2, sort_keys=True, default=str) + "\n")


def configuration(packet, name):
    return json.loads((pathlib.Path(packet) / "revision-3" / "configuration"
                       / name).read_text())


def resolved(value, replacements):
    """One authored document with its READBACK members filled in."""
    if isinstance(value, dict):
        return {name: resolved(held, replacements)
                for name, held in value.items()}
    if isinstance(value, list):
        return [resolved(one, replacements) for one in value]
    if isinstance(value, str) and value.startswith("READBACK: "):
        for mark, held in replacements.items():
            if mark in value:
                return held
        raise CheckFailed("an unresolved READBACK had no replacement", value)
    return value


def bootstrapped(inputs, root, *, extra=()):
    """The SUPPORTED entry point, with its own output captured."""
    from tools import bootstrap

    place = pathlib.Path(root) / "inputs.json"
    place.write_text(json.dumps(inputs, indent=2, sort_keys=True) + "\n")
    spoken = io.StringIO()
    code = bootstrap.main(["--inputs", str(place), *extra], stream=spoken)
    return {"exit": code, "said": spoken.getvalue().strip().splitlines()[-6:],
            "inputs_at": str(place)}


def authority(root, uuid=None):
    from tools import bootstrap
    from baton_v12.authority import Authority

    places = bootstrap.layout(root)
    if uuid is None:
        uuid = json.loads(
            pathlib.Path(places["identity"]).read_text())["authority_uuid"]
    return Authority.open(places["authority_store"],
                          expected_authority_uuid=uuid), uuid, places


# -- scenario 0 --------------------------------------------------------------

SELF_CHECK = ("the disposable root is the selected destination "
              "(INTENTIONALLY FALSE)")


def harness_self_check(packet, root, checks):
    checks.note("the disposable root", root)
    checks.expect(SELF_CHECK, os.path.realpath(root)
                  == os.path.realpath(SELECTED), root)
    return {}


# -- scenario 1 --------------------------------------------------------------

def pass_one_composes_and_reads_back(packet, root, checks):
    """The install inputs, composed by the supported command, then read back."""
    from tools import bootstrap

    inputs = dict(configuration(packet, "install-inputs.json"),
                  state_root=root)
    answer = bootstrapped(inputs, root)
    checks.expect("the supported bootstrap entry point composed pass one",
                  answer["exit"] == 0, answer)
    places = bootstrap.layout(root)
    for name in ("identity", "authority_store", "record", "configuration"):
        checks.expect(f"it made the {name}", os.path.exists(places[name]),
                      places[name])
    # AND WHAT IT DOES NOT MAKE, which the first cut of this scenario got
    # wrong: a compose-in-place pass creates the Authority, the record and the
    # configuration. The Job and control stores belong to the INSTALLED
    # instance and its manager, so their absence here is correct.
    for name in ("job_store", "control_store"):
        checks.expect(f"and did NOT make the {name}, which the installed "
                      f"instance's manager owns",
                      not os.path.exists(places[name]), places[name])
    identity = json.loads(pathlib.Path(places["identity"]).read_text())
    checks.expect("the Authority identity is 32 hex characters, generated "
                  "here and not named by the input",
                  len(identity["authority_uuid"]) == 32
                  and "authority_uuid" not in inputs,
                  identity["authority_uuid"])
    emitted = json.loads(pathlib.Path(places["configuration"]).read_text())
    checks.expect("the emitted configuration binds no Job and configures no "
                  "worker, which is what a fresh install is",
                  emitted["workers"] == [] and emitted["job_bindings"] == [],
                  {"workers": emitted["workers"],
                   "job_bindings": emitted["job_bindings"]})
    checks.expect("it carries this deployment's own generations and retention "
                  "selection",
                  emitted["pool_generation"] == 1
                  and emitted["policy_generation"] == 1
                  and emitted["retention_policy_digest"]
                  == inputs["retention_policy_digest"],
                  {k: emitted[k] for k in ("pool_generation",
                                           "policy_generation",
                                           "retention_policy_digest")})
    from baton_v12.authority import Authority

    stored = Authority.stored_identity(places["authority_store"])
    checks.expect("the store's own metadata names this build and this "
                  "identity", stored["store_kind"] == "baton.v12.python.authority"
                  and stored["authority_uuid"] == identity["authority_uuid"],
                  stored)
    held, uuid, _places = authority(root)
    try:
        checks.expect("the policy generation reads back as the input named",
                      held.policy_generation() == 1, held.policy_generation())
    finally:
        held.dispose()

    # REPETITION PRESERVES WHAT IS THERE.
    again = bootstrapped(inputs, root)
    checks.expect("repeating pass one is accepted", again["exit"] == 0, again)
    checks.expect("and the Authority identity is UNCHANGED, not regenerated",
                  json.loads(pathlib.Path(places["identity"]).read_text())
                  == identity)

    # AND WHAT A REPEATED JOB-LESS PASS DOES WITH A CHANGED GENERATION, which
    # my first cut asserted backwards: it is ACCEPTED. `bootstrap`'s
    # preservation rule is about BINDINGS -- a Job's Work, line and target --
    # and a Job-less install binds none, so there is nothing to conflict with.
    # The drift refusal is proved where bindings actually live, in pass two
    # (scenario 3).
    drifted = bootstrapped(dict(inputs, pool_generation=2), root)
    checks.expect("a repeated Job-less pass ACCEPTS a changed generation, "
                  "because preservation is about bindings and this binds none",
                  drifted["exit"] == 0, drifted)
    checks.expect("and even then the Authority identity does not move",
                  json.loads(pathlib.Path(places["identity"]).read_text())
                  == identity)
    moved = json.loads(pathlib.Path(places["configuration"]).read_text())
    checks.expect("the emitted configuration carries the changed generation, "
                  "so the change is visible rather than silent",
                  moved["pool_generation"] == 2, moved["pool_generation"])
    return {"identity": dict(identity, label=PREFLIGHT),
            "emitted_configuration": {k: emitted[k] for k in
                                      ("schema", "pool_generation",
                                       "policy_generation",
                                       "receipt_participants",
                                       "retention_disposition")},
            "stored_identity": stored,
            "pass_one": answer, "repeat": again, "drift": drifted}


# -- scenario 2 --------------------------------------------------------------

def owner_and_diagnosis_ownership_are_composed(packet, root, checks):
    """The two routes bootstrap does NOT register, registered and proved."""
    from baton_v12.authority import Authority

    inputs = dict(configuration(packet, "install-inputs.json"),
                  state_root=root)
    checks.expect("pass one composed", bootstrapped(inputs, root)["exit"] == 0)
    held, uuid, places = authority(root)
    answer = {"authority_uuid": uuid, "label": PREFLIGHT}
    try:
        work = f"{uuid[:8]}-W1"
        diagnosis = f"{uuid[:8]}-W2"
        # THE GAP THE REVIEW NAMED, measured first: an owner route nobody
        # registered resolves to nobody.
        held.create_work(work, "impl", operation_id="w325959-create-pilot")
        refused = None
        try:
            held.session("baton.slaw").claim(
                {"work_id": work, "operation_id": "w325959-owner-early"})
        except Exception as caught:                          # noqa: BLE001
            refused = f"{type(caught).__name__}: {caught}"
        answer["owner_claim_before_registration"] = refused
        checks.expect("before registration the owner cannot take a Work on "
                      "its own route: the route resolves to nobody",
                      refused is not None and "route" in refused, refused)

        # THE REGISTRATIONS, and then the only readback that counts.
        for route, participant in (("owner", "baton.slaw"),
                                   ("diagnosis",
                                    "baton.diagnostician-pilot"),
                                   ("rview", "baton.reviewer-pilot"),
                                   ("impl", "baton.claude-pilot")):
            held.add_route_handler(route, participant)
        answer["registered"] = {"owner": "baton.slaw",
                                "diagnosis": "baton.diagnostician-pilot",
                                "rview": "baton.reviewer-pilot",
                                "impl": "baton.claude-pilot"}
        passed = held.session("baton.claude-pilot").claim(
            {"work_id": work, "operation_id": "w325959-impl-claim"})
        checks.expect("the implementation participant claims on `impl`",
                      passed["assignment"]["participant"]
                      == "baton.claude-pilot", passed["assignment"])
        live = held.assignment_of(work)
        held.session("baton.claude-pilot").pass_work(
            {"expect": live, "operation_id": "w325959-handoff-review",
             "to_route": "rview", "comment": "preflight handoff"})
        reviewed = held.session("baton.reviewer-pilot").claim(
            {"work_id": work, "operation_id": "w325959-review-claim"})
        checks.expect("the review participant claims after the handoff to "
                      "`rview`", reviewed["assignment"]["participant"]
                      == "baton.reviewer-pilot", reviewed["assignment"])
        live = held.assignment_of(work)
        held.session("baton.reviewer-pilot").pass_work(
            {"expect": live, "operation_id": "w325959-handoff-owner",
             "to_route": "owner", "comment": "preflight handoff to the owner"})
        owned = held.session("baton.slaw").claim(
            {"work_id": work, "operation_id": "w325959-owner-claim"})
        answer["owner_assignment"] = held.assignment_of(work)
        checks.expect("THE OWNER ROUTE IS REAL: baton.slaw claims the Work "
                      "its review ending handed on",
                      owned["assignment"]["participant"] == "baton.slaw",
                      owned["assignment"])
        checks.expect("and the decision names the owner's own principal",
                      owned["decision"]["principal"] == "principal:baton.slaw",
                      owned["decision"])
        wrong = None
        try:
            held.session("baton.diagnostician-pilot").claim(
                {"work_id": work, "operation_id": "w325959-wrong-route"})
        except Exception as caught:                          # noqa: BLE001
            wrong = f"{type(caught).__name__}: {caught}"
        answer["diagnostician_on_the_owner_route"] = wrong
        checks.expect("a participant that does not handle this route is "
                      "refused", wrong is not None, wrong)

        # THE DEDICATED DIAGNOSIS WORK, on its own route.
        held.create_work(diagnosis, "diagnosis",
                         operation_id="w325959-create-diagnosis")
        claimed = held.session("baton.diagnostician-pilot").claim(
            {"work_id": diagnosis, "operation_id": "w325959-diagnosis-claim"})
        answer["diagnosis_assignment"] = held.assignment_of(diagnosis)
        checks.expect("THE DIAGNOSIS ROUTE IS REAL: its handler claims a "
                      "dedicated diagnostic Work",
                      claimed["assignment"]["participant"]
                      == "baton.diagnostician-pilot",
                      claimed["assignment"])
        checks.expect("an identical claim replays rather than taking a second "
                      "one",
                      held.session("baton.diagnostician-pilot").claim(
                          {"work_id": diagnosis,
                           "operation_id": "w325959-diagnosis-claim"})
                      == claimed)

        # THE PER-WORK RECEIPT GRANTS, made and read back.
        scope = held.project_work(work)["scope"]
        grants = {"baton.verifier-pilot": "verify",
                  "baton.reviewer-receipt-pilot": "review",
                  "baton.slaw": "approve"}
        for who, capability in grants.items():
            held.grant_capability(who, capability, scope=scope)
        for who, capability in grants.items():
            checks.expect(f"{who} holds {capability} in this Work's own scope",
                          held.holds_capability(who, capability, scope=scope),
                          {"who": who, "capability": capability,
                           "scope": scope})
        for capability in ("verify", "review"):
            checks.expect(f"and the owner holds NO {capability} grant",
                          not held.holds_capability("baton.slaw", capability,
                                                    scope=scope))
        held.grant_capability("baton.slaw", "integrate", scope=scope)
        held.grant_capability("baton.slaw", "close", scope=scope)
        checks.expect("the owner holds approve, integrate and close",
                      all(held.holds_capability("baton.slaw", one,
                                                scope=scope)
                          for one in ("approve", "integrate", "close")))
        answer["grants"] = {"scope": scope,
                            "policy_generation": held.policy_generation(),
                            "receipts": grants,
                            "owner": ["approve", "integrate", "close"]}
        # AND THE CANONICAL DOSSIER, bound before any human citation.
        # ONE FLAT SEGMENT, which is the W39435 grammar -- the first cut
        # passed a path and the Authority refused it by name: "a canonical
        # dossier locator is ONE FLAT SEGMENT".
        # EIGHT hex characters, which is what the Authority's own refusal
        # spelled out: "lowercase letters, digits and single hyphens ending in
        # a 8-character hex suffix". My first two cuts used a path and then a
        # 12-character suffix, and both were refused by name.
        locator = "native-pilot-quickstart-" + uuid[:8]
        bound = held.bind_dossier(work, locator,
                                  operation_id="w325959-bind-dossier")
        answer["dossier_locator"] = locator
        answer["dossier"] = held.dossier_of(work)
        checks.expect("the canonical dossier binds, which the human "
                      "integration citation requires",
                      bool(answer["dossier"]), {"bound": bound,
                                                "read": answer["dossier"]})
    finally:
        held.dispose()
    return answer


# -- scenario 3 --------------------------------------------------------------

def pass_two_binds_the_two_stage_job(packet, root, checks):
    """Workers and the Job binding, composed by the supported command."""
    from tools import bootstrap, single_worker

    inputs = dict(configuration(packet, "install-inputs.json"),
                  state_root=root)
    checks.expect("pass one composed", bootstrapped(inputs, root)["exit"] == 0)
    held, uuid, places = authority(root)
    try:
        work = f"{uuid[:8]}-W1"
        held.create_work(work, "impl", operation_id="w325959-create-pilot")
        principals = {who: held.principal_of(who)
                      for who in ("baton.claude-pilot",
                                  "baton.reviewer-pilot")}
    finally:
        held.dispose()

    manifest_inputs = configuration(packet, "manifest-inputs.json")
    task = configuration(packet, "task.json")
    staged = pathlib.Path(root) / "staged"
    (staged / "inputs").mkdir(parents=True, exist_ok=True)
    task_place = staged / "inputs" / "task.json"
    task_place.write_text(json.dumps(task, sort_keys=True))

    # THE MANIFEST THIS STAGE DEPLOYMENT NEEDS, and the composer that does
    # NOT compose it. `dogfood_operator.input_manifest` hardcodes
    # `consumption: {"baton.directory/1": ...}` -- the STAGED delivery shape --
    # and the stage deployment refuses a source descriptor that does not
    # declare `baton.source-boundary/1`: "a descriptor with no boundary
    # declaration is a staged source whose content this manager measured, and
    # a nominated mount would deliver material its manifest does not
    # describe". My first cut used that composer and the manager said exactly
    # that. There is no composer in the tree for the nominated-mount shape, so
    # this ADAPTS the prior validated instance's own manifest -- its source
    # descriptor, outputs and policy identities -- replacing the Work
    # reference, the human contract and the manifest id, and re-seals it
    # through the same canonical digest the manager recomputes. The adaptation
    # is then held to the MANAGER's own structure check, not to this driver's
    # opinion.
    from baton_v12.contracts import digest as canonical
    from baton_v12.worker_manager.manifests import check_manifest_structure

    prior = json.loads(pathlib.Path(
        str(pathlib.Path(packet) / "revision-3" / "inputs" / "deployment.json")).read_text())
    source = prior["workers"][0]["deployment"]["input_manifest"]
    composed = json.loads(json.dumps(source))
    composed["work_ref"] = {"authority_uuid": uuid, "work_id": work}
    composed["manifest_id"] = "input-manifest-1"
    composed["human_contract"] = {
        "artifact_id": "w321608-native-operator-quickstart",
        "bytes": len(task_place.read_bytes()),
        "content_digest": "sha256:" + hashlib.sha256(
            task_place.read_bytes()).hexdigest(),
        "locator": "artifact://contracts/w321608-native-operator-quickstart",
        "media_type": source["human_contract"]["media_type"]}
    held_derived = manifest_inputs[
        "content_derived_and_recomputed_from_the_frozen_copies"]
    for member in ("retention_policy_digest", "policy_digest",
                   "runtime_profile_digest"):
        composed[member] = held_derived[member]
    # THE SEAL IS LAST, after every member is in place. An earlier cut sealed
    # and then kept assigning, and `verify_manifest_digest` said exactly what
    # that is: "an input manifest declares a manifest digest its own bytes do
    # not produce; a manifest that does not identify itself is not one".
    composed.pop("manifest_digest", None)
    composed["manifest_digest"] = canonical(composed)
    checks.expect("the adapted manifest passes the MANAGER's own structure "
                  "check", check_manifest_structure(
                      composed, "inputManifest",
                      what="the pilot input manifest") is not None)
    checks.expect("its source descriptor declares the boundary a nominated "
                  "mount requires",
                  "baton.source-boundary/1"
                  in composed["sources"][0]["consumption"],
                  composed["sources"][0]["consumption"])
    checks.expect("it names THIS Authority and THIS Work",
                  composed["work_ref"] == {"authority_uuid": uuid,
                                           "work_id": work},
                  composed["work_ref"])
    checks.expect("and this task document's own bytes",
                  composed["human_contract"]["content_digest"]
                  == "sha256:" + hashlib.sha256(
                      task_place.read_bytes()).hexdigest(),
                  composed["human_contract"]["content_digest"])
    checks.expect("the sealed digest is the canonical digest the manager "
                  "recomputes, and it moved because the Work did",
                  composed["manifest_digest"] != source["manifest_digest"],
                  {"adapted": composed["manifest_digest"],
                   "prior": source["manifest_digest"]})

    job_inputs = configuration(packet, "configure-inputs.json")
    replacements = {"generated by the one installation": uuid,
                    "the Work id created after the installation": work,
                    "adapted from inputs/deployment.json": composed}
    document = resolved(job_inputs, replacements)
    document["state_root"] = root
    for one in document["workers"]:
        deployment = one["deployment"]
        deployment["authority_store"] = places["authority_store"]
        deployment["principal"] = principals[deployment["participant"]]
        for member, place in (("workspace_storage", "workspaces"),
                              ("launch_home", "launch"),
                              ("credential_home", "credentials")):
            held_place = pathlib.Path(root) / place / one["role"]
            held_place.mkdir(parents=True, exist_ok=True)
            deployment[member] = str(held_place)
        deployment["nominated_source"] = str(
            pathlib.Path(root) / "repo" / "source")
        deployment["task_document"] = str(task_place)
        deployment["input_manifest"] = composed
    (pathlib.Path(root) / "repo" / "source").mkdir(parents=True,
                                                   exist_ok=True)
    checks.expect("every worker document now names all 29 members the worker "
                  "contract closes over",
                  all(sorted(one["deployment"])
                      == sorted(single_worker._MEMBERS)
                      for one in document["workers"]))
    checks.expect("the producer and the reviewer are distinct participants",
                  document["workers"][0]["participant"]
                  != document["workers"][1]["participant"])
    routes = {one["role"]: one["deployment"]["review_route"]
              for one in document["workers"]}
    checks.expect("the review worker's outgoing route is the OWNER route",
                  routes == {"implementation": "rview", "review": "owner"},
                  routes)
    checks.expect("no integration worker is configured",
                  [one["role"] for one in document["workers"]]
                  == ["implementation", "review"])

    presented = bootstrap.held(document)
    checks.expect("bootstrap's own input validator accepts the resolved "
                  "configuration pass", presented is not None)
    # R1: this call used to pass `principals` twice and the TypeError was
    # merely NOTED, which proved nothing. `bootstrap.configuration` takes the
    # document, the layout and the principals positionally in that order.
    # THE REAL SIGNATURE is `configuration(document, principals=None)`; the
    # layout is not an operand. Revision 2 passed three and the TypeError was
    # merely noted, which is why the review refused that as proof.
    emitted_now = bootstrap.configuration(
        dict(document, **{name: value for name, value
                          in bootstrap.layout(root).items()
                          if name in ("authority_store", "integration_store",
                                      "state_root")},
             authority_uuid=uuid), principals)
    checks.expect("and bootstrap.validated accepts the configuration this "
                  "input EMITS", bootstrap.validated(emitted_now) is not None)
    checks.expect("the emitted configuration carries both workers with their "
                  "resolved principals",
                  [one["deployment"]["principal"]
                   for one in emitted_now["workers"]]
                  == [principals["baton.claude-pilot"],
                      principals["baton.reviewer-pilot"]],
                  [one["deployment"]["principal"]
                   for one in emitted_now["workers"]])

    # R2: THE IN-PLACE CONFIGURATION PASS, which is what follows the ONE
    # installation. Revision 2's packet told the operator to run the install
    # recipe a second time, and `bootstrap.admit` (1877-1896) refuses an
    # installed destination that already carries a distro, a justfile and an
    # instance selector -- so the documented command could not have worked
    # while the driver proved something else. The supported transition is
    # `--inputs` alone against the installed state root, which is exactly what
    # this exercises, with the install-derived storage selections preserved.
    first = bootstrapped(document, root)
    checks.expect("the in-place configuration pass is accepted by the "
                  "supported entry point", first["exit"] == 0, first)
    repeated = bootstrapped(document, root)
    checks.expect("repeating it preserves what is there",
                  repeated["exit"] == 0, repeated)
    emitted_paths = json.loads(pathlib.Path(
        bootstrap.layout(root)["configuration"]).read_text())
    for one in emitted_paths["workers"]:
        deployment = one["deployment"]
        checks.expect(f"{one['worker_id']} keeps its install-derived storage "
                      f"selections",
                      all(str(root) in deployment[member] for member in
                          ("workspace_storage", "launch_home",
                           "credential_home", "nominated_source")),
                      {member: deployment[member] for member in
                       ("workspace_storage", "launch_home",
                        "credential_home", "nominated_source")})
    moved = json.loads(json.dumps(document))
    moved["jobs"][0]["line_declared_base"] = "0" * 40
    drifted = bootstrapped(moved, root)
    checks.expect("but a CHANGED Job binding is refused rather than moved",
                  drifted["exit"] != 0, drifted)
    checks.note("the refusal's own words", drifted["said"])
    emitted = json.loads(pathlib.Path(
        bootstrap.layout(root)["configuration"]).read_text())
    checks.expect("the emitted configuration carries both workers and the "
                  "one binding",
                  [one["role"] for one in emitted["workers"]]
                  == ["implementation", "review"]
                  and len(emitted["job_bindings"]) == 1,
                  {"workers": [one["worker_id"] for one in emitted["workers"]],
                   "bindings": emitted["job_bindings"]})
    checks.expect("and the binding still names the ORIGINAL base",
                  emitted["job_bindings"][0]["line_declared_base"] == BASE,
                  emitted["job_bindings"][0])

    # R1: THE PUBLIC PROJECTION, not a hash of the whole manifest. Review
    # 2026-10-18T20-29-02Z proved my revision-2 value unequal to it:
    # `contracts.job_input_identity` projects out the role-specific members
    # (worker image, toolchain, runtime profile, credential policy, role
    # instructions, manifest id, created_at, manifest digest) before the
    # canonical digest, and `stage_execution` compares against THAT.
    from baton_v12.contracts import job_input_identity

    identity = job_input_identity(composed)
    naive = "sha256:" + hashlib.sha256(
        json.dumps(composed, sort_keys=True).encode()).hexdigest()
    checks.expect("the Job input identity is the PUBLIC projection and is NOT "
                  "a hash of the whole manifest", identity != naive,
                  {"public": identity, "revision_2_was": naive})
    def moved(member, value):
        """One member changed, and the manifest RE-SEALED.

        `job_input_identity` validates the manifest first, so handing it a
        document whose declared digest no longer matches its bytes is refused
        with "a manifest that does not identify itself is not one" -- which is
        what an earlier cut of these two checks did.
        """
        other = dict(composed, **{member: value})
        other.pop("manifest_digest", None)
        other["manifest_digest"] = canonical(other)
        return job_input_identity(other)

    checks.expect("it is stable under the excluded members: changing the "
                  "worker image digest does not move it",
                  moved("worker_image_digest", "sha256:" + "f" * 64)
                  == identity)
    checks.expect("while changing an included policy identity DOES move it",
                  moved("resource_policy_digest", "sha256:" + "e" * 64)
                  != identity)

    submission = resolved(configuration(packet, "submission.json"),
                          {"the Work id created after the installation": work,
                           "contracts.job_input_identity": identity})
    from baton_v12.job_manager import documents

    owned = documents.owned_submission(submission)
    checks.expect("the submission names that identity",
                  owned["jobs"][0]["input_digest"] == identity,
                  owned["jobs"][0]["input_digest"])

    # AND THE RUNTIME CONSUMER BOUNDARY, asked without launching anything:
    # `stage_execution._disagreements` is `single_worker._matches`'s own
    # operand comparison, and an empty answer is what lets a configured worker
    # serve this stage.
    from tools import stage_execution

    binding = {"job_id": "quickstart-a", "job_work_id": work,
               "review_work_id": work, "line_declared_base": BASE,
               "canonical_target_id": BASE,
               "source_worker_id": "implementation-pilot"}
    job_document = {"input_digest": identity,
                    "policy_digest": owned["jobs"][0]["policy_digest"]}
    for one, stage in zip(document["workers"], owned["jobs"][0]["stages"]):
        found = stage_execution._disagreements(one["deployment"], stage,
                                               job_document, binding)
        checks.expect(f"the runtime consumer finds NO disagreement for "
                      f"{one['worker_id']}", found == {}, found)
    checks.expect("and it DOES disagree when the Job names another input",
                  stage_execution._disagreements(
                      document["workers"][0]["deployment"],
                      owned["jobs"][0]["stages"][0],
                      dict(job_document, input_digest="sha256:" + "0" * 64),
                      binding) != {})
    checks.expect("the submission validates with the readbacks in place",
                  [one["kind"] for one in owned["jobs"][0]["stages"]]
                  == ["implementation", "review"],
                  owned["jobs"][0]["job_id"])
    checks.expect("and carries the selected per-invocation ceilings",
                  owned["jobs"][0]["execution_limits"]
                  == {"provider_turn_seconds": 3600,
                      "verification_command_seconds": 900})
    return {"authority_uuid": uuid, "work_id": work, "label": PREFLIGHT,
            "pass_two": first, "repeat": repeated, "binding_drift": drifted,
            "emitted_bindings": emitted["job_bindings"],
            "input_manifest": {"manifest_id": composed["manifest_id"],
                               "manifest_digest": composed["manifest_digest"],
                               "work_ref": composed["work_ref"],
                               "worker_image_digest":
                               composed["worker_image_digest"],
                               "runtime_profile_digest":
                               composed["runtime_profile_digest"]},
            "routes": routes, "principals": principals,
            "emitted_validation": "accepted by bootstrap.validated",
            "job_input_identity": identity,
            "revision_2_naive_digest": naive,
            "submission_stages": [one["kind"] for one in
                                  owned["jobs"][0]["stages"]]}


# -- scenario 4 --------------------------------------------------------------

def the_reused_inputs_are_verified(packet, root, checks):
    """Every reused digest recomputed from the document it describes."""
    from baton_v12.contracts import digest as canonical

    prior = pathlib.Path(packet) / "revision-3" / "inputs"
    document = json.loads((prior / "deployment.json").read_text())
    held = {one["role"]: one["deployment"] for one in document["workers"]}
    answers = {}
    for name, member in (("policy.json", "policy_digest"),
                         ("runtime-profile.json", "profile_digest"),
                         ("adapter.json", "adapter_digest")):
        recomputed = canonical(json.loads((prior / name).read_text()))
        answers[name] = {"recomputed": recomputed,
                         "named_by_the_worker": held["implementation"][member]}
        checks.expect(f"{member} IS the canonical digest of {name}, "
                      f"recomputed here",
                      recomputed == held["implementation"][member],
                      answers[name])
    mine = configuration(packet, "configure-inputs.json")["workers"][0]["deployment"]
    for member in ("profile_digest", "policy_digest", "adapter_digest",
                   "image_digest", "adapter_name", "profile_name", "engine",
                   "network", "launch_contract", "credential_sources",
                   "credential_slots", "credential_profile",
                   "workspace_group", "workspace_capacity"):
        checks.expect(f"this packet reuses the prior instance's {member} "
                      f"verbatim", mine[member]
                      == held["implementation"][member],
                      {"mine": mine[member],
                       "prior": held["implementation"][member]})
    checks.expect("the retention policy digest is this tree's own retention "
                  "policy, recomputed",
                  mine["retention_policy_digest"] == "sha256:" +
                  hashlib.sha256(pathlib.Path(
                      "/home/sl/src/baton/v12/instance-retention.md"
                  ).read_bytes()).hexdigest(),
                  mine["retention_policy_digest"])
    checks.expect("the credential SOURCE is a reference this host has, and "
                  "its content is never read",
                  os.path.exists(mine["credential_sources"]),
                  mine["credential_sources"])
    checks.expect("the credential profile carries a provider and a reference "
                  "and no secret member",
                  all(sorted(one) == ["provider", "reference"]
                      for one in mine["credential_profile"].values()),
                  mine["credential_profile"])
    checks.expect("the worker deployment schema is this build's own",
                  mine["schema"] == __import__(
                      "tools.single_worker",
                      fromlist=["CONFIG_SCHEMA"]).CONFIG_SCHEMA, mine["schema"])
    checks.note("the image digest's provenance",
                {"digest": mine["image_digest"],
                 "from": str(prior / "deployment.json"),
                 "image_operation_classification": "python3 -m tools.worker_image --tag <tag> BUILDS an image (build, save, normalize, load, clean -- worker_image._main 384-440). It is NOT a read-only validation, and revision 2 wrongly called it one. A read-only presence check is an engine inspect of the recorded digest, which this preparation does not perform."})
    return {"recomputed": answers,
            "reused_from": str(prior / "deployment.json"),
            "image_digest": mine["image_digest"]}


SCENARIOS = (
    ("0-harness-self-check", harness_self_check, SELF_CHECK,
     "a deliberately false expectation about which root this writes to"),
    ("1-pass-one-composes-and-reads-back", pass_one_composes_and_reads_back,
     None,
     "the supported bootstrap entry point, its readbacks, a repetition and a "
     "drifted selection"),
    ("2-owner-and-diagnosis-ownership", owner_and_diagnosis_ownership_are_composed,
     None,
     "the two routes bootstrap does not register, registered and proved by "
     "claim, plus the per-Work receipt grants"),
    ("3-pass-two-binds-the-two-stage-job", pass_two_binds_the_two_stage_job,
     None,
     "the composed input manifest, the resolved worker documents and the "
     "submission"),
    ("4-the-reused-inputs-are-verified", the_reused_inputs_are_verified, None,
     "every reused digest recomputed from the document it describes"),
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", required=True)
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--root", required=True,
                        help="a disposable root OUTSIDE the checkout and not "
                             "the selected destination")
    taken = parser.parse_args()
    place = pathlib.Path(taken.evidence).resolve()
    place.mkdir(parents=True, exist_ok=True)
    root = os.path.realpath(taken.root)
    if root == os.path.realpath(SELECTED) or LABEL not in root:
        print(f"REFUSED: the disposable root must carry the label {LABEL!r} "
              f"and must not be the selected destination")
        return 2
    started = time.monotonic()
    answers, unexpected, passed = [], 0, 0

    print("W325959 disposable preparation (labelled, not the selected "
          "instance):")
    for name, body, intended, injected in SCENARIOS:
        at = time.monotonic()
        checks = Checks()
        record = {"scenario": name, "injected": injected,
                  "expected_failure": intended is not None,
                  "intended_failed_check": intended,
                  "disposable_root": root, "label": PREFLIGHT,
                  "not_performed": ["any engine call", "any provider call",
                                    "any credential content read",
                                    "any image build",
                                    "any write to the selected destination",
                                    "any submission to a manager",
                                    "any mutation of this repository"]}
        failure, own = None, pathlib.Path(root) / name
        try:
            if own.exists():
                shutil.rmtree(own)
            own.mkdir(parents=True)
            with redirect_stdout(io.StringIO()):
                record.update(body(taken.packet, str(own), checks) or {})
            record["outcome"] = "observed"
        except CheckFailed as caught:
            record["outcome"] = "failed"
            record["failed_check"] = caught.label
            failure = caught
        except BaseException:                                # noqa: BLE001
            record["outcome"] = "failed"
            record["failure"] = traceback.format_exc()[-2500:]
        record["checks"] = checks.document()
        record["checks_passed"] = checks.passed()
        record["seconds"] = round(time.monotonic() - at, 3)
        passed += record["checks_passed"]
        if intended is None:
            wanted = record["outcome"] == "observed"
        else:
            wanted = (record["outcome"] == "failed"
                      and isinstance(failure, CheckFailed)
                      and failure.label == intended
                      and "failure" not in record)
            record["failed_for_intended_reason"] = wanted
        if not wanted:
            unexpected += 1
            record["unexpected"] = True
        answers.append(record)
        say(place, f"scenario-{name}.json", record)
        print(f"  {name}: {record['outcome']} "
              f"({record['checks_passed']} checks passed"
              f"{', as intended' if record.get('failed_for_intended_reason') else ''}"
              f"{', UNEXPECTED' if record.get('unexpected') else ''}) "
              f"{record['seconds']}s")

    self_check = [one for one in answers
                  if one["scenario"] == "0-harness-self-check"]
    sound = bool(self_check) and self_check[0].get(
        "failed_for_intended_reason") is True
    answer = {"schema": "baton.w325959.disposable-preparation/1",
              "label": PREFLIGHT, "disposable_root": root,
              "selected_destination_untouched": not os.path.lexists(SELECTED),
              "source_base": BASE,
              "scenarios": answers, "checks_passed": passed,
              "observed": sum(1 for one in answers
                              if one["outcome"] == "observed"),
              "failed_as_intended": sum(1 for one in answers
                                        if one.get(
                                            "failed_for_intended_reason")),
              "unexpected": unexpected,
              "harness_self_check_failed_for_its_own_reason": sound,
              "seconds": round(time.monotonic() - started, 3)}
    say(place, "PREPARATION.json", answer)
    print(f"checks passed {passed}, observed {answer['observed']}, "
          f"failed-as-intended {answer['failed_as_intended']}, "
          f"unexpected {unexpected}, {answer['seconds']}s")
    print(f"selected destination untouched: "
          f"{answer['selected_destination_untouched']}")
    if not sound:
        print("REFUSED: the self-check did not fail for its own intended "
              "reason")
        return 2
    return 1 if unexpected else 0


if __name__ == "__main__":
    raise SystemExit(main())
