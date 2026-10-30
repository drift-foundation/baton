"""Fresh instance-3 preparation: validate, mint, read back, compose, install.

THE ORDERING, resolved independently at review-2026-10-23T04-52-43Z.md and not
guessed here:

  1. bootstrap.main(["--inputs", install_doc])          # NO --destination
     generates and persists the authority and an empty configuration. No
     repositories, no runtime, no selector.
  2. READ BACK the minted authority_uuid from <destination>/authority-identity.json.
  3. COMPOSE the Work as <uuid[:8]>-W1 -- contracts/manifest.py refuses a Work
     reference that does not carry its authority's prefix -- and seal the
     manifest and task against it.
  4. bootstrap.main(["--inputs", full_doc, "--destination", root,
                     "--distro", bundle, "--repository-source", source])
     custody permits compatible source-only preparation, REUSES that uuid, and
     creates all four repositories, the Work, the configuration and the selector.

So no placeholder manifest is needed and NO MANUAL CLONE STEP is needed -- the
instance-2 workaround is not carried forward, which is what owner358374 asked.

EVERYTHING KNOWABLE IS REFUSED BEFORE STEP 1. CORRECTED at claim358517 after
review-2026-10-23T05-00-27Z.md, which proved a real defect rather than a
stylistic one: `prepare` used to return `planned` the moment `mint(apply=False)`
answered, which was BEFORE anything parsed the task, configure or submission
documents, BEFORE any contract was composed, and BEFORE `--distro` or
`--repository-source` were looked at. An independent reproduction therefore got
`planned: true` out of a malformed task plus a nonexistent bundle, and the
apply then CREATED THE DESTINATION and persisted authority-identity.json before
raising JSONDecodeError (evidence/review-358477/INVALID-INPUT.json). A partial
installation caused by an error knowable without writing anything is precisely
what a preflight exists to prevent, so `static_refusals` below now asks every
one of those questions first, and `prepare` re-asks the packet ones after the
mint so a packet edited mid-run cannot be installed either.

WHY A PROVISIONAL IDENTITY. The contracts cannot be composed for real until an
authority exists, and the authority does not exist until step 1 writes it. So
the pre-mint gate composes, seals and cross-binds the WHOLE document against an
explicitly provisional uuid, purely to make a sealing or cross-binding fault
refuse before the first write. It is thrown away: step 3 recomposes against the
uuid the product actually minted, and `prepare` asserts the installed document
carries that real one.

WHAT THIS NEVER DOES. No submission, no serving, no admission, no engine,
provider or model, no Git, and nothing against instance 1 or 2. Without
--owner-selected it PREFLIGHTS and writes nothing.

Reuses the accepted shared output contract and sealing from the instance-2
packet rather than restating them: `configure.SHARED_OUTPUTS`,
`configure.sealed_manifest`, `configure.cross_bound`, `configure.submission_of`.
"""
import argparse
import copy
import hashlib
import io
import json
import os
import pathlib
import sys

PACKET = pathlib.Path(__file__).resolve().parent
SIBLING = PACKET.parent / "post-install-357462"
sys.path.insert(0, str(SIBLING))
import configure                                            # noqa: E402

DESTINATION = "/home/sl/baton-instances/native-coordination-pilot-w321608-3"
JOB = "quickstart-c"
SUBMISSION = "sub-w321608-quickstart-3"
TASK = "w321608-native-operator-quickstart-3"
BUILD = pathlib.Path("/home/sl/baton-builds/w325959-30245386-356981")
# THE RESOLVED BUNDLE. Pending at handoff358474 and resolved at claim358517 by
# reading the build rather than assuming a subdirectory: this directory holds an
# executable `baton-v12-stack` whose own `identity` answers frozen: true, both
# frozen schema assets, `native_rpds` inside the bundle's own `_internal`,
# commit 30245386, dirty: false, and sha256 9cda6dab... -- the executable digest
# already pinned by the accepted instance-2 INDEX.
DISTRO = BUILD / "build" / "out" / "distro"
SOURCE = BUILD / "src"
RETAINED = ("/home/sl/baton-instances/native-coordination-pilot-w321608-1",
            "/home/sl/baton-instances/native-coordination-pilot-w321608-2")
# A VALID BUT OBVIOUSLY UNREAL AUTHORITY, used only by the pre-mint contract
# rehearsal and never installed.
PROVISIONAL = "0" * 32
Refused = configure.Refused


def _of(place):
    return "sha256:" + hashlib.sha256(pathlib.Path(place).read_bytes()).hexdigest()


# THE REVIEWED BYTES OF THIS PACKET'S OWN FOUR DOCUMENTS. Reported before
# claim358517 and merely reported; now enforced, because a hash printed next to
# a document nobody compared is decoration.
PACKET_PINS = {
    "install-inputs.json":
        "sha256:bfe7f223dcef1eb2d5ecbb5f05d5c925f5d7b04b22d96e5a516fd19e6bd3e77d",
    "configure-inputs.json":
        "sha256:b108d2189d15e77b0d7eb3cb1d9b9d61eb9ac3cb662ab91c2da1e34805b976ca",
    "task.json":
        "sha256:2f87e9dc45b94eb4100d6127a5f6e9487cb7c6edb2bbac6f3653052f966a62d0",
    "submission.json":
        "sha256:76013289a5b0d587c148add78ac93ec16272481f2b00680a077c3602bd507c7c",
}
# AND THE HELPER THIS IMPORTS. The accepted instance-2 module supplies the
# sealing, the cross-binding and the shared two-stage output contract, so its
# bytes are an input to this preparation exactly like a document is. Helper
# drift was called out by name in review-2026-10-23T05-00-27Z.md.
HELPER_PINS = {
    "configure.py":
        "sha256:b15280cc19aabca5bd519b88f57a34e7b7dabe7e67a40a28348befabf9d16333",
}


def _pinned(root, pins, *, what):
    """Each named file present, pinned, and hashing to its pin. READS ONLY."""
    answer = {}
    for name, want in (pins or {}).items():
        held = pathlib.Path(root) / name
        if held.is_symlink():
            raise Refused(what + " " + name + " at " + str(held) + " is a "
                          "link; this reads the reviewed file, not a name "
                          "somebody else controls")
        if not held.is_file():
            raise Refused(what + " " + name + " is missing at " + str(held)
                          + "; this preparation consumes it and will not "
                          "proceed without it")
        got = _of(held)
        if not want:
            raise Refused(what + " " + name + " has no pinned digest in this "
                          "procedure; an unpinned consumed document is not "
                          "bound, and this preparation seals it in")
        if got != want:
            raise Refused(what + " " + name + " is " + got + " and this "
                          "procedure is bound to " + want + "; these are not "
                          "the reviewed bytes")
        answer[name] = got
    return answer


def _parsed(packet, name):
    """A consumed document, parsed with its own name in the refusal."""
    held = pathlib.Path(packet) / name
    try:
        return json.loads(held.read_text())
    except json.JSONDecodeError as broken:
        raise Refused("the consumed document " + name + " at " + str(held)
                      + " is not valid JSON: " + str(broken)
                      + ". Nothing is minted for a packet that cannot be read.")
    except OSError as unreadable:
        raise Refused("the consumed document " + name + " at " + str(held)
                      + " cannot be read: " + str(unreadable))


def collisions_refused(destination, *, places):
    """Nothing this preparation would create may already exist."""
    root = pathlib.Path(destination)
    if root.is_symlink():
        raise Refused("the destination " + str(root) + " is a link; this "
                      "prepares a fresh instance and does not write through "
                      "a name somebody else controls")
    if root.exists():
        raise Refused("the destination " + str(root) + " already exists; a "
                      "fresh instance is prepared once. Inspect it rather "
                      "than having this write into somebody else's tree.")
    for name in ("instance", "deployment", "record", "identity", "distro"):
        held = pathlib.Path(places[name])
        if held.is_symlink() or held.exists():
            raise Refused("the destination already carries " + name + " at "
                          + str(held))
    return True


def noninterference(destination, *, consumed=()):
    """No path this preparation writes OR READS belongs to a retained instance.

    CORRECTED at claim358517. This used to ask only about
    `instance.layout(destination)` -- the paths that would be WRITTEN -- so a
    packet, helper or bundle sitting inside instance 1 or 2 passed unexamined
    even though those bytes decide what gets installed. The review required the
    actual consumed document paths, so they are checked here by the same rule.
    """
    from tools import instance

    places = instance.layout(destination)
    held = []
    for one in RETAINED:
        held.append(str(pathlib.Path(one).resolve())
                    if pathlib.Path(one).exists() else one)

    def inside(value):
        for other in held:
            if value == other or value.startswith(other.rstrip("/") + "/"):
                return other
        return None

    checked = 0
    for key, value in places.items():
        if not isinstance(value, str):
            continue
        checked += 1
        trespass = inside(value)
        if trespass:
            raise Refused("instance 3's " + key + " at " + value
                          + " lies inside " + trespass
                          + "; a fresh instance isolates its own state")
    for label, value in consumed:
        if value is None:
            continue
        value = str(pathlib.Path(value).resolve()) if \
            pathlib.Path(value).exists() else str(value)
        checked += 1
        trespass = inside(value)
        if trespass:
            raise Refused("this preparation would READ its " + label + " from "
                          + value + ", which lies inside " + trespass
                          + "; a retained instance is not an input to a fresh "
                          "one")
    return {"isolated_from": list(RETAINED), "checked_paths": checked,
            "consumed_checked": [label for label, _ in consumed]}


def prerequisites(bundle, source):
    """The bundle and the repository source, before anything is minted.

    The supported call ADMITS the bundle and CLONES from the source. Both are
    knowable without writing, and the reproduction at review358477 passed a
    nonexistent bundle straight through a preflight that reported `planned`.
    """
    answer = {}
    if bundle in (None, ""):
        raise Refused("no --distro bundle was named; step 4 admits one and "
                      "cannot be planned without it")
    held = pathlib.Path(bundle)
    if held.is_symlink() or not held.is_dir():
        raise Refused("the bundle " + str(held) + " is not a directory this "
                      "preparation can admit (a link or a missing path is not "
                      "a one-folder bundle)")
    command = held / "baton-v12-stack"
    if command.is_symlink() or not command.is_file():
        raise Refused("the bundle " + str(held) + " carries no baton-v12-stack "
                      "executable at " + str(command) + "; `admit` runs this "
                      "file to read the bundle's own identity")
    if not os.access(command, os.X_OK):
        raise Refused("the bundle command " + str(command) + " is not "
                      "executable; `admit` runs it and would fail after the "
                      "destination had already been created")
    answer["bundle"] = str(held)
    answer["command"] = str(command)
    if source in (None, ""):
        raise Refused("no --repository-source was named; step 4 clones the "
                      "worker sources from it")
    src = pathlib.Path(source)
    if src.is_symlink() or not src.is_dir():
        raise Refused("the repository source " + str(src) + " is not a "
                      "directory; step 4 clones every non-mirror role from it")
    if not (src / "v12").is_dir():
        raise Refused("the repository source " + str(src) + " carries no v12 "
                      "directory; this is not the product source tree step 4 "
                      "expects")
    answer["source"] = str(src)
    return answer


def static_refusals(destination, packet, *, bundle, source, pins=PACKET_PINS,
                    helper=HELPER_PINS, inherited=None):
    """EVERY knowable constraint, before the first write. READS ONLY.

    Returns what it validated, including the PROVISIONAL composition, which is
    a rehearsal and is never installed.
    """
    packet = pathlib.Path(packet)
    answer = {"packet": str(packet), "helper": str(SIBLING)}

    # -- the reviewed bytes: this packet, its helper, and what the helper eats -
    answer["packet_digests"] = _pinned(packet, pins, what="the packet document")
    answer["helper_digests"] = _pinned(SIBLING, helper, what="the helper module")
    if inherited is None:
        inherited = configure.INHERITED_PINS
    # AGAINST THE ACTUAL CONSUMPTION SITE. `configure.sealed_manifest` reads
    # the prior deployment, the two native records and the digest recipe from
    # SIBLING.parent -- not from wherever this packet happens to sit -- so that
    # is where the pins have to be compared. Pinning `packet.parent` would bind
    # bytes nothing reads, which is the same class of defect as reporting a
    # hash without comparing it.
    answer["inherited_digests"] = _pinned(
        SIBLING.parent, inherited, what="the inherited input")

    # -- the documents parse, and are the documents this packet claims ---------
    install = _parsed(packet, "install-inputs.json")
    document = _parsed(packet, "configure-inputs.json")
    task = _parsed(packet, "task.json")
    submission = _parsed(packet, "submission.json")

    if install.get("workers") or install.get("jobs"):
        raise Refused("the install document must carry NO workers and NO jobs; "
                      "step 1 mints the authority before any Work can name it")
    for label, held in (("install-inputs.json", install),
                        ("configure-inputs.json", document)):
        if held.get("state_root") != destination:
            raise Refused(label + " names state_root "
                          + str(held.get("state_root")) + " and this run names "
                          + destination)
    if task.get("task_id") != TASK:
        raise Refused("task.json names task_id " + repr(task.get("task_id"))
                      + " and this packet is bound to " + TASK)
    if submission.get("submission_id") != SUBMISSION:
        raise Refused("submission.json names " + repr(
            submission.get("submission_id")) + " and this packet is bound to "
            + SUBMISSION)
    jobs = document.get("jobs") or []
    if len(jobs) != 1 or jobs[0].get("job_id") != JOB:
        raise Refused("configure-inputs.json must select exactly the one Job "
                      + JOB + "; it names "
                      + repr([one.get("job_id") for one in jobs]))

    # -- the destination's own paths, and the paths this READS -----------------
    from tools import instance

    places = instance.layout(destination)
    for name in ("integration_target", "integration_workspace"):
        value = str(document[name])
        inside = places["repository"].rstrip("/") + "/"
        if not value.startswith(inside):
            raise Refused(name + " is " + value + ", which is not under this "
                          "destination's repository " + inside)
    answer["noninterference"] = noninterference(destination, consumed=(
        ("packet", packet), ("helper", SIBLING), ("bundle", bundle),
        ("repository source", source),
        ("inherited inputs", SIBLING.parent)))
    collisions_refused(destination, places=places)

    # -- the bundle is admissible and the source is clonable ------------------
    answer["prerequisites"] = prerequisites(bundle, source)

    # -- THE CONTRACTS, REHEARSED AGAINST A PROVISIONAL IDENTITY --------------
    # The real authority does not exist yet. This proves the manifest seals, the
    # worker/manifest/submission cross-binding agrees and the manager's own
    # submission validator accepts -- so none of those faults can strand a
    # half-created destination. Thrown away; step 3 recomposes for real.
    rehearsed = _compose(packet, destination, PROVISIONAL, task=task,
                         document=copy.deepcopy(document))
    answer["provisional"] = {
        "authority_uuid": PROVISIONAL,
        "work": rehearsed["work"],
        "manifest_digest": rehearsed["manifest"]["manifest_digest"],
        "input_digest": rehearsed["submission"]["jobs"][0]["input_digest"],
        "note": "A REHEARSAL against a deliberately unreal authority, proving "
                "the contracts compose before anything is minted. It is not "
                "installed; step 3 recomposes against the minted uuid.",
    }
    answer["validated"] = True
    return answer


def mint(destination, packet, *, apply, stream=None):
    """STEP 1 -- authority and empty configuration only."""
    from tools import bootstrap

    document = json.loads((pathlib.Path(packet) / "install-inputs.json")
                          .read_text())
    # Re-asked here as well as in `static_refusals`: this is the function that
    # performs the first write, so it does not rely on a caller having checked.
    if document.get("workers") or document.get("jobs"):
        raise Refused("the install document must carry NO workers and NO jobs; "
                      "step 1 mints the authority before any Work can name it")
    if document["state_root"] != destination:
        raise Refused("the install document names state_root "
                      + document["state_root"] + " and this run names "
                      + destination)
    if not apply:
        return {"planned": True, "would_mint_under": destination}
    staged = pathlib.Path(destination)
    staged.mkdir(parents=True, exist_ok=False)
    place = staged / "install-inputs.json"
    place.write_text(json.dumps(document, indent=1, sort_keys=True) + "\n")
    spoken = stream or io.StringIO()
    code = bootstrap.main(["--inputs", str(place)], stream=spoken)
    said = spoken.getvalue() if isinstance(spoken, io.StringIO) else ""
    if code != 0:
        raise Refused("step 1 refused (exit " + str(code) + "):\n"
                      + said.strip()[-800:])
    return {"exit": code, "said": said.strip().splitlines()[-6:],
            "inputs_at": str(place)}


def minted_authority(places):
    """STEP 2 -- the uuid this instance actually minted, read from its record."""
    held = pathlib.Path(places["identity"])
    if not held.is_file():
        raise Refused("step 1 wrote no authority identity at " + str(held))
    document = json.loads(held.read_text())
    if document.get("schema") != "baton.v12.instance-identity/1":
        raise Refused("the identity at " + str(held) + " is not a "
                      "baton.v12.instance-identity/1 document")
    uuid = document["authority_uuid"]
    if uuid == PROVISIONAL:
        raise Refused("the minted authority is the provisional rehearsal uuid "
                      + PROVISIONAL + "; the rehearsal is never installed")
    return uuid


def _compose(packet, destination, uuid, *, task=None, document=None):
    """The Work under that authority's prefix, and the sealed manifest.

    Shared by the pre-mint rehearsal and step 3 so the rehearsal exercises the
    REAL composition rather than a lookalike of it.
    """
    from tools import instance

    packet = pathlib.Path(packet)
    work = uuid[:8] + "-W1"
    if task is None:
        task = _parsed(packet, "task.json")
    body = json.dumps(task, indent=1, sort_keys=True).encode() + b"\n"
    if document is None:
        document = _parsed(packet, "configure-inputs.json")
    manifest = configure.sealed_manifest(SIBLING, uuid, work, task, body)
    document["jobs"][0]["work_id"] = work
    places = instance.layout(destination)
    task_place = pathlib.Path(places["state"], "task", task["task_id"] + ".json")
    for worker in document["workers"]:
        worker["deployment"]["authority_uuid"] = uuid
        worker["deployment"]["input_manifest"] = manifest
        worker["deployment"]["task_document"] = str(task_place)
    left = [one for one in json.dumps(document).split('"')
            if one.startswith("COMPOSED(")]
    if left:
        raise Refused("unresolved COMPOSED markers remain: " + repr(left[:2]))
    submission = configure.submission_of(packet, work, manifest)
    if submission["submission_id"] != SUBMISSION \
            or submission["jobs"][0]["job_id"] != JOB:
        raise Refused("the submission does not carry the selected identifiers")
    configure.cross_bound(document, manifest, submission)
    return {"work": work, "manifest": manifest, "document": document,
            "submission": submission, "task": task, "task_bytes": body,
            "task_place": str(task_place)}


def composed(packet, destination, uuid):
    """STEP 3 -- composition against the authority the product actually minted."""
    return _compose(packet, destination, uuid)


def install_and_configure(held, destination, *, bundle, source, apply,
                          runner=None, stream=None):
    """STEP 4 -- the one supported call that creates everything else."""
    from tools import bootstrap

    if not apply:
        return {"planned": True}
    task_place = pathlib.Path(held["task_place"])
    task_place.parent.mkdir(parents=True, exist_ok=True)
    task_place.write_bytes(held["task_bytes"])
    out = pathlib.Path(destination, "generated")
    out.mkdir(parents=True, exist_ok=True)
    staged = out / "bootstrap-inputs.json"
    staged.write_text(json.dumps(held["document"], indent=1, sort_keys=True)
                      + "\n")
    spoken = stream or io.StringIO()
    code = bootstrap.main(["--inputs", str(staged), "--destination", destination,
                           "--distro", str(bundle),
                           "--repository-source", str(source)],
                          stream=spoken, runner=runner)
    said = spoken.getvalue() if isinstance(spoken, io.StringIO) else ""
    if code != 0:
        raise Refused("step 4 refused (exit " + str(code) + "):\n"
                      + said.strip()[-900:])
    return {"exit": code, "said": said.strip().splitlines()[-10:],
            "inputs_at": str(staged), "emitted_under": str(out)}


def prepare(destination=DESTINATION, packet=PACKET, *, apply=False,
            bundle=DISTRO, source=SOURCE, runner=None, pins=PACKET_PINS,
            helper=HELPER_PINS, inherited=None):
    """The whole fresh preparation, in the resolved order."""
    from tools import instance, stage_execution

    packet = pathlib.Path(packet)
    places = instance.layout(destination)
    answer = {"destination": destination, "job": JOB, "submission": SUBMISSION,
              "task": TASK, "applied": bool(apply),
              "bundle": str(bundle) if bundle else None,
              "repository_source": str(source) if source else None}

    # EVERYTHING KNOWABLE, BEFORE THE FIRST WRITE.
    answer["static"] = static_refusals(destination, packet, bundle=bundle,
                                       source=source, pins=pins, helper=helper,
                                       inherited=inherited)
    answer["packet_digests"] = answer["static"]["packet_digests"]
    answer["noninterference"] = answer["static"]["noninterference"]
    answer["step1"] = mint(destination, packet, apply=apply)
    if not apply:
        answer["planned"] = True
        return answer

    uuid = minted_authority(places)
    answer["authority_uuid"] = uuid
    # RE-ASKED AFTER THE MINT. The packet was read before step 1 and is read
    # again for step 3; a packet edited in between would otherwise be installed
    # under bytes nobody validated.
    _pinned(packet, pins, what="the packet document (re-checked after mint)")
    _pinned(SIBLING, helper, what="the helper module (re-checked after mint)")
    held = composed(packet, destination, uuid)
    answer["work"] = held["work"]
    answer["manifest_digest"] = held["manifest"]["manifest_digest"]
    answer["input_digest"] = held["submission"]["jobs"][0]["input_digest"]
    answer["step4"] = install_and_configure(
        held, destination, bundle=bundle, source=source, apply=apply,
        runner=runner)

    # THE TASK DIGEST DESCRIBES THE EMITTED BYTES. CORRECTED at claim358517:
    # this used to be computed before step 4 wrote the task document, so it was
    # always null -- a readback field that described nothing.
    task_place = pathlib.Path(held["task_place"])
    if not task_place.is_file():
        raise Refused("step 4 left no task document at " + str(task_place))
    answer["task_digest"] = _of(task_place)
    expected = "sha256:" + hashlib.sha256(held["task_bytes"]).hexdigest()
    if answer["task_digest"] != expected:
        raise Refused("the emitted task document digests "
                      + answer["task_digest"] + " and the composed bytes are "
                      + expected)

    installed = json.loads(pathlib.Path(places["deployment"]).read_bytes())
    if stage_execution.held_configuration(installed) is None:
        raise Refused("the installed configuration failed held_configuration")
    for worker in installed.get("workers") or []:
        named = worker.get("deployment", {}).get("authority_uuid")
        if named != uuid:
            raise Refused("installed worker " + str(worker.get("worker_id"))
                          + " names authority " + str(named) + " and this "
                          "instance minted " + uuid)
    answer["installed_workers"] = sorted(one["role"] for one in
                                         installed.get("workers") or [])
    answer["installed_job_bindings"] = len(installed.get("job_bindings") or [])
    answer["repositories"] = sorted(
        one.name for one in pathlib.Path(places["repository"]).iterdir())
    # MEASURED, NOT ASSUMED. `bootstrap.storage_bound` derives and bounds
    # workspace_storage but does not create it, and the consumer
    # `workspaces.check_workspace_storage` lstats the place and refuses "not a
    # directory this manager can see". So whether this is an owner prerequisite
    # is a question about what preparation actually left behind.
    answer["workspace_storage"] = sorted({
        one.get("deployment", {}).get("workspace_storage")
        for one in installed.get("workers") or []} - {None})
    answer["workspace_storage_present"] = {
        one: pathlib.Path(one).is_dir() for one in answer["workspace_storage"]}
    for name, value in (("configure-inputs.json", held["document"]),
                        ("submission.json", held["submission"]),
                        ("preparation-readback.json", answer)):
        pathlib.Path(destination, "generated", name).write_text(
            json.dumps(value, indent=1, sort_keys=True) + "\n")
    answer["configured"] = held["document"]
    answer["submission_document"] = held["submission"]
    return answer


def main(argv=None, *, stream=sys.stdout):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", default=DESTINATION)
    parser.add_argument("--packet", default=str(PACKET))
    parser.add_argument("--distro", default=str(DISTRO))
    parser.add_argument("--repository-source", default=str(SOURCE))
    parser.add_argument("--owner-selected", action="store_true",
                        help="without this it PREFLIGHTS and writes nothing")
    taken = parser.parse_args(argv)
    answer = prepare(taken.destination, taken.packet,
                     apply=taken.owner_selected, bundle=taken.distro,
                     source=taken.repository_source)
    print(json.dumps(answer, indent=1, sort_keys=True), file=stream)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
