"""Owner-run post-install configuration for destination 2. OWNER SELECTION REQUIRED.

THE SHAPE, and why it is this shape. Rewritten at claim357725 after
review-2026-10-23T03-04-01Z.md: preflight everything knowable BEFORE any write,
compose the whole document, make ONE supported call, then read the installed
configuration back and put it through the real consumer.

    bootstrap.main(["--inputs", <document>])      # NO --destination

is the supported in-place operation -- `v12/justfile` calls it "the older form
and still works" -- and `prepare` (bootstrap.py:1248) proves everything before
composing while REUSING this root's existing Authority: "a root that already has
a record keeps the Authority that record names."

NOTHING HERE REGISTERS. The supported operation already does:
add_route_handler (bootstrap.py:731), create_work (:746) and grant_capability
(:758, :760, :771). The previous revision duplicated that and, in duplicating
it, wrote routes and grants BEFORE a task or configuration conflict could
refuse. Deleting the duplicate removes the ordering defect at its source.

THE WORK IDENTITY, accurately. `jobs[0].work_id` is SELECTED by the packet,
created by the supported operation, and COLLISION-CHECKED by the authority --
that refusal is the safety property. It is not allocated by the authority and
this module does not describe it as a readback. What IS read back is the
installed configuration.

WHAT IT NEVER DOES. No repository command: the two worker sources are prepared
by PROPOSAL.md step 1 and this REFUSES until they exist and are proved. No
submission, no serving, no admission, no engine, provider or model. No Git.
"""
import argparse
import copy
import hashlib
import json
import io
import pathlib
import sys


class Refused(SystemExit):
    def __init__(self, why):
        super().__init__("REFUSED: " + why)


def _digest(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _of(place):
    return _digest(pathlib.Path(place).read_bytes())


# The packet bytes this procedure is bound to. A packet that does not hash to
# these is not the reviewed one, and configuring from it would be configuring
# from something nobody reviewed.
PACKET_PINS = {
    "task.json": "sha256:9d588235e058d043f2c2c2bcc50ecf560f0bddbe4358f5e0751bfe45a3437780",
    "submission.json": "sha256:948649b50ec1326954e6e9fe168eedab3bef5b1d7e21c84a8153eb13c1738cf2",
    "configure-inputs.json": "sha256:157ea4af10f5b82a6a2edb629922720fedd21dd3db7c763730d3496a3d4cfccd",
}
# AND THE INHERITED DOCUMENTS THIS CONSUMES, relative to the packet's parent.
# CORRECTED at claim357787: pinning only the packet's own three left the
# manifest's actual inputs -- the prior deployment, the two native records and
# the digest recipe -- unbound, so tampered inherited metadata would have been
# sealed in and called cross-bound.
# CORRECTED AGAIN at claim357900: these were None, and `preflight` only
# compared a pin when one was given -- so under the SHIPPED DEFAULTS the four
# inherited documents were checked for EXISTENCE and nothing else. An
# independent reproduction sealed an all-zero credential_policy_digest straight
# through. A pin that is absent by default is not a pin; these are now the
# reviewed bytes.
INHERITED_PINS = {
    "revision-4/inputs/deployment.json":
        "sha256:6a675445d361a5208f82dfc43593595cd2d5d9bcbb3e893842c03b5cb8587a3e",
    "revision-4/inputs/native-finding.md":
        "sha256:8e51f5ec4c0d8c1866412f1987e0b07f0a06c3c24969262c70ef4837f25b8947",
    "revision-4/inputs/native-plan.md":
        "sha256:39c50d05797f5ed0ea92ae27a44a6f18cbc95baf3210e361c3845a603c03d8ab",
    "revision-4/configuration/manifest-inputs.json":
        "sha256:4c924188e853cc457e57ae405bce4e7ab06ddbe9f3b461ba7eeafa00f7fb30ab",
}
# EVERY NAME THIS PROCEDURE WRITES under <destination>/generated. Derived from
# the writes rather than restated beside them, because the two drifting apart is
# exactly the defect an independent reproduction found at claim357763.
WRITES = ("bootstrap-inputs.json", "configure-inputs.json", "submission.json",
          "configuration-readback.json")
SELECTED = {
    "authority_uuid": "673355e1f28e4b5683cbef09eb8f2658",
    "runtime_digest": "3dbc610e0c2a0e1165367871097bd2a5bb590e271fee729b94b436a04045e7ac",
    "base": "302453869d07eb5579e79a6572586d3c3cf62a5c",
}


# THE SHARED TWO-STAGE OUTPUT CONTRACT. Added at claim358239 after the live
# review stage faulted: review-2026-10-23T04-08-43Z.md.
#
# WHY THE UNION, in the adapter's own words. claude_agent.py:460 says a shared
# Job's implementation and review manifests "cannot both satisfy" a single-role
# declaration, so "the declaration set is therefore THE UNION and each role
# produces its own half, answering the other half `missing-optional`. THE
# ASSEMBLY OWNS CONSTRUCTING THAT MANIFEST." This is the assembly.
#
# WHY EVERY ONE IS OPTIONAL. `_selected` (:4675) refuses in three ways: an
# unknown name; a name the role MUST produce that is absent; and -- at :4683 --
# a declared output marked `required` that the role does NOT produce. The
# implementation produces only `proposal`; the review produces only `findings`
# and `logs`. So any `required: true` among them refuses one of the two roles.
# The delivered packet declared `proposal` required and nothing else, which is
# exactly why the review turn refused before any provider call.
#
# `required` HERE IS THE ADAPTER'S PER-TURN CONTRACT, not the Job's acceptance.
# A stage answering `missing-optional` is making a statement in the manager's
# own vocabulary, not being excused. The downstream requirement that a proposal
# actually exists is the integration and receipt half and is unchanged by this.
_LIMITS = {"allowed_media_types": ["application/octet-stream", "text/plain"],
           "link_policy": "forbid", "max_bytes": 1048576, "max_entries": 100,
           "validator_digest": None}
SHARED_OUTPUTS = [
    {"name": "proposal", "path": "proposal", "required": False,
     "type": "git-change-proposal", "constraints": dict(_LIMITS)},
    {"name": "findings", "path": "findings", "required": False,
     "type": "review-report", "constraints": dict(_LIMITS)},
    {"name": "logs", "path": "logs", "required": False,
     "type": "turn-logs", "constraints": dict(_LIMITS)},
]


PRESERVED = ("integration_target", "integration_workspace",
             "owner_participant", "policy_generation", "pool_generation",
             "retention_disposition", "retention_policy_digest",
             "checkpoint_profile")


def installed_selections(places):
    """The selections the install already made, read from its own document."""
    place = pathlib.Path(places["deployment"])
    if not place.is_file():
        return None
    held = json.loads(place.read_bytes())
    return {name: held.get(name) for name in PRESERVED if name in held}


def drift_refused(before, proposed, *, what):
    """Refuse a changed selection by name. CALLED BEFORE ANY WRITE.

    CORRECTED at claim357834: the comparison used to happen AFTER the supported
    call, so a configuration that changed a preserved selection was caught only
    once the task document and the authority had already been written. The
    install's own choices are knowable from its deployment document, so this is
    a preflight question and is asked as one.
    """
    if not before:
        return {"compared": 0, "note": "the installation recorded no prior "
                                       "deployment document to compare"}
    drifted = {name: (before[name], proposed.get(name)) for name in before
               if proposed.get(name) != before[name]}
    if drifted:
        raise Refused(
            what + " changes selections the installation had already made: "
            + "; ".join(name + " " + repr(was) + " -> " + repr(now)
                        for name, (was, now) in drifted.items()))
    return {"compared": len(before), "preserved": sorted(before)}


def preflight(destination, packet, *, runner=None, pins=PACKET_PINS,
              selected=SELECTED, inherited=INHERITED_PINS):
    """EVERY knowable constraint, before the first write. Reads only.

    Ordered so the cheapest identity refusals come first and the repository
    proof -- which shells out through the injected runner -- comes last.
    """
    from tools import bootstrap, instance

    packet = pathlib.Path(packet)

    # -- the packet is the reviewed one ------------------------------------
    for name, want in (pins or {}).items():
        held = packet / name
        if not held.is_file():
            raise Refused("the packet has no " + name + " at " + str(held))
        if _of(held) != want:
            raise Refused(name + " is " + _of(held) + " and this procedure is "
                          "bound to " + want + "; this is not the reviewed packet")

    for name, want in (inherited or {}).items():
        held = packet.parent / name
        if not held.is_file():
            raise Refused("the inherited input " + name + " is missing at "
                          + str(held) + "; the manifest cross-binding consumes "
                          "it and will not proceed without it")
        if not want:
            raise Refused("the inherited input " + name + " has no pinned "
                          "digest in this procedure; an unpinned consumed "
                          "document is not bound, and the manifest seals it in")
        if _of(held) != want:
            raise Refused(name + " is " + _of(held) + " and this procedure is "
                          "bound to " + want)

    # -- the installation is the selected one -------------------------------
    places = instance.layout(destination)
    if not pathlib.Path(places["instance"]).is_file():
        raise Refused("there is no instance selector at " + places["instance"]
                      + "; this configures an EXISTING installation")
    selector = instance.read(places["instance"])
    instance.verify(selector)                   # the product's own bundle check
    identity = pathlib.Path(places["identity"])
    if not identity.is_file():
        raise Refused("the installation has no authority identity at "
                      + str(identity))
    # THE IDENTITY DOCUMENT'S OWN BYTES, not just its uuid member: the
    # supported call reads this file and refuses anything that is not a
    # baton.v12.instance-identity/1 document, so checking it here moves that
    # refusal before the first write instead of after it.
    if identity.is_symlink():
        raise Refused("the authority identity at " + str(identity)
                      + " is a link; this reads the instance's own record")
    held_identity = json.loads(identity.read_text())
    if held_identity.get("schema") != "baton.v12.instance-identity/1":
        raise Refused("the authority identity at " + str(identity)
                      + " is not a baton.v12.instance-identity/1 document "
                      "(schema " + repr(held_identity.get("schema")) + ")")
    uuid = held_identity["authority_uuid"]
    if uuid != selector["authority_uuid"]:
        raise Refused("the identity names authority " + uuid + " and the "
                      "selector names " + selector["authority_uuid"])
    if selected:
        if selected.get("authority_uuid") and uuid != selected["authority_uuid"]:
            raise Refused("this installation's authority is " + uuid
                          + " and the selected one is "
                          + selected["authority_uuid"])
        want = selected.get("runtime_digest")
        if want and selector["runtime"]["digest"] != want:
            raise Refused("the installed runtime digests "
                          + selector["runtime"]["digest"]
                          + " and the selected bundle is " + want)

    # -- the document's own paths are the layout's, exactly -----------------
    document = json.loads((packet / "configure-inputs.json").read_text())
    for name, derived in (("state_root", "destination"),
                          ("integration_target", None),
                          ("integration_workspace", None)):
        value = str(document[name])
        if derived is not None and value != places[derived]:
            raise Refused(name + " is " + value + " and this destination "
                          "derives " + places[derived])
        if derived is None:
            inside = places["repository"].rstrip("/") + "/"
            if not value.startswith(inside):
                raise Refused(name + " is " + value + ", which is not under "
                              "this destination's repository " + inside)
    if selected and selected.get("base"):
        for job in document.get("jobs") or []:
            for member in ("line_declared_base", "canonical_target_id"):
                if job.get(member) != selected["base"]:
                    raise Refused("job " + str(job.get("job_id")) + " names "
                                  + member + " " + str(job.get(member))
                                  + " and the selected base is "
                                  + selected["base"])

    # -- the task document would not conflict -------------------------------
    task = json.loads((packet / "task.json").read_text())
    body = json.dumps(task, indent=1, sort_keys=True).encode() + b"\n"
    task_place = pathlib.Path(places["state"], "task", task["task_id"] + ".json")
    if task_place.exists() and task_place.read_bytes() != body:
        raise Refused("a DIFFERENT task document is already at "
                      + str(task_place) + "; nothing here overwrites one")

    # -- NOTHING THIS PROCEDURE WRITES MAY ALREADY BE OCCUPIED --------------
    # CORRECTED at claim357787. The earlier list omitted bootstrap-inputs.json,
    # which `apply_supported` writes -- so an independent reproduction showed a
    # pre-existing one being OVERWRITTEN while the apply succeeded. The list is
    # now derived from WRITES rather than restated, and `lexists` is used
    # because `exists` follows a link and answers false for a broken one: an
    # occupied name would look free while the write still clobbered somebody
    # else's target.
    out = pathlib.Path(places["destination"], "generated")
    clashing = [name for name in WRITES if (out / name).is_symlink()
                or (out / name).exists()]
    if clashing:
        raise Refused("these outputs already exist under " + str(out) + ": "
                      + ", ".join(clashing)
                      + ". A previous attempt left them; inspect and move them "
                      "rather than having this overwrite evidence")
    if out.is_symlink():
        raise Refused("the output directory " + str(out) + " is a link to "
                      + str(out.resolve()) + "; this procedure does not write "
                      "through a name somebody else controls")
    if task_place.is_symlink():
        raise Refused("the task document name " + str(task_place) + " is a "
                      "link; nothing here writes through one")

    # -- the installation's own selections would survive --------------------
    # ASKED HERE, before the first write: the install's deployment document
    # already says what it chose, and the document this procedure would apply
    # already says what it would configure.
    prior = installed_selections(places)
    preservation = drift_refused(prior, document,
                                 what="this configuration input")

    # -- the Work this document selects is not already taken ----------------
    from baton_v12.authority import Authority

    held = Authority.open(places["authority_store"],
                          expected_authority_uuid=uuid)
    try:
        for job in document.get("jobs") or []:
            chosen = job.get("work_id")
            if not isinstance(chosen, str) or chosen.startswith(
                    ("READBACK", "SELECTED(")):
                raise Refused(
                    "job " + str(job.get("job_id")) + " still carries the "
                    "marker " + repr(chosen)[:80] + "; the Work id is SELECTED "
                    "in this document and must be a real identifier before the "
                    "supported operation can create it")
            try:
                existing = held.project_work(chosen)
            except Exception:                              # noqa: BLE001
                existing = None
            if existing is not None:
                raise Refused(
                    "the selected Work " + chosen + " already exists on this "
                    "authority. The supported operation would refuse it, and a "
                    "second registration is not a repeat of the first: inspect "
                    "it and continue from its projection.")
    finally:
        held.dispose()

    # -- the repositories exist and are independent -------------------------
    planned = bootstrap.repository_plan(document, places)
    absent = [name for name, place, _ in planned
              if not pathlib.Path(place).exists()]
    if absent:
        raise Refused(
            "these repositories are not prepared: " + ", ".join(absent)
            + ". NO supported operation adds a worker source repository to a "
            "prepared destination -- run PROPOSAL.md step 1 by hand first. "
            "This procedure does not clone.")
    bootstrap.repositories_proved(document, places, planned, runner=runner)

    return {"places": places, "selector": selector, "uuid": uuid,
            "document": document, "task": task, "task_bytes": body,
            "task_place": str(task_place), "out": out,
            "prior_selections": prior, "preservation": preservation}


def sealed_manifest(packet, uuid, work_id, task, task_bytes, *,
                    manifest_inputs=None):
    """The input manifest, CROSS-BOUND from the accepted documents, sealed last.

    The inherited manifest in revision-4/inputs/deployment.json carries values
    that disagree with the workers that would consume it -- policy_digest
    3a532add where they name 837d7a03, and a `cccc...` retention PLACEHOLDER --
    so copying it and resealing produces a valid seal over stale content, which
    is not evidence. manifest-inputs.json supplies the replacements and
    revision-4/prepare.py:314-320 is the loop that applies them.
    """
    from baton_v12.contracts import digest as seal
    from baton_v12.worker_manager.manifests import check_manifest_structure

    packet = pathlib.Path(packet)
    prior = json.loads((packet.parent / "revision-4" / "inputs"
                        / "deployment.json").read_text())
    held = manifest_inputs or json.loads(
        (packet.parent / "revision-4" / "configuration"
         / "manifest-inputs.json").read_text())

    composed = copy.deepcopy(prior["workers"][0]["deployment"]["input_manifest"])
    composed["work_ref"] = {"authority_uuid": uuid, "work_id": work_id}
    composed["manifest_id"] = "input-manifest-1"
    composed["human_contract"] = {
        "artifact_id": task["task_id"],
        "bytes": len(task_bytes),
        "content_digest": _digest(task_bytes),
        "locator": "artifact://contracts/" + task["task_id"],
        "media_type": composed["human_contract"]["media_type"]}
    records = {}
    for name in ("finding", "plan"):
        records[name + "_digest"] = _of(
            packet.parent / "revision-4" / "inputs" / ("native-" + name + ".md"))
    composed["record_binding"] = {
        "root": "native-pilot",
        "path": "native-pilot-quickstart-" + uuid[:8], **records}
    composed["outputs"] = SHARED_OUTPUTS

    # THE TEN THE MANIFEST ITSELF CARRIES: three recomputed from the frozen
    # copies plus seven accountability documents. `adapter_digest` is a WORKER
    # member, not a manifest one -- adding it here is refused by the frozen
    # schema's unevaluatedProperties, which is how this was caught. revision-4
    # prepare.py:314-320 replaces exactly these three and the seven.
    derived = held["content_derived_and_recomputed_from_the_frozen_copies"]
    for member in ("retention_policy_digest", "policy_digest",
                   "runtime_profile_digest"):
        composed[member] = derived[member]
    for member, item in held["proposed_accountability_documents"].items():
        composed[member] = item["digest"] if isinstance(item, dict) else item

    # THE SEAL IS LAST, after every member is in place: verify_manifest_digest
    # refuses a manifest whose declared digest its own bytes do not produce.
    composed.pop("manifest_digest", None)
    composed["manifest_digest"] = seal(composed)
    if check_manifest_structure(composed, "inputManifest",
                                what="the pilot input manifest") is None:
        raise Refused("the cross-bound manifest failed the structure check")
    return composed


def composed_document(held, manifest):
    """The bootstrap input, with the manifest and task bound into each worker."""
    document = copy.deepcopy(held["document"])
    for worker in document["workers"]:
        worker["deployment"]["authority_uuid"] = held["uuid"]
        worker["deployment"]["input_manifest"] = manifest
        worker["deployment"]["task_document"] = held["task_place"]
    left = [one for one in json.dumps(document).split('"')
            if one.startswith(("READBACK", "SELECTED("))]
    if left:
        raise Refused("unresolved markers remain: " + repr(left[:2]))
    return document


def cross_bound(document, manifest, submission):
    """Worker, manifest and submission must agree, not merely each be valid."""
    for worker in document["workers"]:
        deployment = worker["deployment"]
        for member in ("policy_digest", "retention_policy_digest"):
            if deployment[member] != manifest[member]:
                raise Refused(
                    "worker " + worker["worker_id"] + " names " + member + " "
                    + deployment[member] + " and the manifest names "
                    + manifest[member] + "; a seal over a value its consumer "
                    "disagrees with is not evidence")
    job = submission["jobs"][0]
    first = document["workers"][0]["deployment"]
    if job["policy_digest"] != first["policy_digest"]:
        raise Refused("the submission names policy " + job["policy_digest"]
                      + " and the workers name " + first["policy_digest"])
    for stage in job["stages"]:
        if stage["profile_digest"] != first["profile_digest"]:
            raise Refused("stage " + stage["kind"] + " names profile "
                          + stage["profile_digest"] + " and the workers name "
                          + first["profile_digest"])
    return True


def submission_of(packet, work_id, manifest):
    from baton_v12.contracts import job_input_identity
    from baton_v12.job_manager import documents as job_documents

    held = json.loads((pathlib.Path(packet) / "submission.json").read_text())
    job = held["jobs"][0]
    job["input_digest"] = job_input_identity(manifest)
    for stage in job["stages"]:
        stage["work_id"] = work_id
    if "READBACK" in json.dumps(held):
        raise Refused("the submission still carries a READBACK marker")
    if job["execution_limits"] != {"provider_turn_seconds": 3600,
                                   "verification_command_seconds": 900}:
        raise Refused("per-invocation limits were altered")
    job_documents.owned_submission(held)       # the manager's own validator
    return held


def apply_supported(document, out, *, stream=None):
    """THE ONE SUPPORTED CALL, and its output captured.

    `bootstrap.main(["--inputs", path])` with no --destination composes the
    deployment in place from `state_root`.
    """
    from tools import bootstrap

    out.mkdir(parents=True, exist_ok=True)
    staged = out / "bootstrap-inputs.json"
    staged.write_text(json.dumps(document, indent=1, sort_keys=True) + "\n")
    spoken = stream or io.StringIO()
    code = bootstrap.main(["--inputs", str(staged)], stream=spoken)
    said = spoken.getvalue() if isinstance(spoken, io.StringIO) else ""
    if code != 0:
        raise Refused("the supported configuration refused (exit " + str(code)
                      + "):\n" + said.strip()[-800:])
    return {"exit": code, "inputs_at": str(staged),
            "said": said.strip().splitlines()[-8:]}


def read_installed(places):
    """The installed configuration, through the REAL runtime consumer."""
    from tools import stage_execution

    place = pathlib.Path(places["deployment"])
    if not place.is_file():
        raise Refused("the supported operation wrote no deployment document at "
                      + str(place))
    installed = json.loads(place.read_bytes())
    owned = stage_execution.held_configuration(installed)
    if owned is None:
        raise Refused("the installed configuration failed held_configuration")
    roles = sorted(one["role"] for one in installed.get("workers") or [])
    if roles != ["implementation", "review"]:
        raise Refused("the installed configuration composes roles "
                      + repr(roles) + " rather than both stage workers")
    return installed, owned


def compose(destination, packet, *, apply=False, runner=None, pins=PACKET_PINS,
            selected=SELECTED, inherited=INHERITED_PINS):
    """Preflight, compose, ONE supported call, read back. In that order."""
    packet = pathlib.Path(packet)
    held = preflight(destination, packet, runner=runner, pins=pins,
                     selected=selected, inherited=inherited)
    work_id = held["document"]["jobs"][0]["work_id"]
    manifest = sealed_manifest(packet, held["uuid"], work_id, held["task"],
                               held["task_bytes"])
    document = composed_document(held, manifest)
    submission = submission_of(packet, work_id, manifest)
    cross_bound(document, manifest, submission)

    answer = {"authority_uuid": held["uuid"],
              "destination": held["places"]["destination"],
              "selected_work": work_id,
              "task_document": held["task_place"],
              "task_digest": _digest(held["task_bytes"]),
              "manifest_digest": manifest["manifest_digest"],
              "input_digest": submission["jobs"][0]["input_digest"],
              "submission_id": submission["submission_id"],
              "runtime_digest": held["selector"]["runtime"]["digest"],
              "applied": bool(apply)}
    answer["preflight_preservation"] = held["preservation"]
    if not apply:
        answer["planned"] = True
        return answer

    # THE FIRST WRITE HAPPENS HERE, and not before.
    task_place = pathlib.Path(held["task_place"])
    task_place.parent.mkdir(parents=True, exist_ok=True)
    task_place.write_bytes(held["task_bytes"])
    answer["supported_call"] = apply_supported(document, held["out"])
    installed, _owned = read_installed(held["places"])
    # THE SAME COMPARISON AGAIN, against what was actually installed. Preflight
    # refused a drifting INPUT before any effect; this confirms the supported
    # call did not introduce one of its own.
    answer["preservation"] = drift_refused(
        held["prior_selections"], installed,
        what="the installed configuration")
    answer["installed_workers"] = sorted(one["role"] for one in
                                         installed.get("workers") or [])
    answer["installed_job_bindings"] = len(installed.get("job_bindings") or [])
    answer["consumer"] = "tools.stage_execution.held_configuration accepted it"
    for name, value in (("configure-inputs.json", document),
                        ("submission.json", submission),
                        ("configuration-readback.json", answer)):
        pathlib.Path(held["out"], name).write_text(
            json.dumps(value, indent=1, sort_keys=True) + "\n")
    answer["emitted_under"] = str(held["out"])
    answer["configured"] = document
    answer["submission"] = submission
    return answer


def main(argv=None, *, stream=sys.stdout):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", required=True)
    parser.add_argument("--packet", default=str(pathlib.Path(__file__).parent))
    parser.add_argument("--owner-selected", action="store_true",
                        help="without this it PREFLIGHTS and writes nothing")
    taken = parser.parse_args(argv)
    answer = compose(taken.destination, taken.packet,
                     apply=taken.owner_selected)
    print(json.dumps(answer, indent=1, sort_keys=True), file=stream)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
