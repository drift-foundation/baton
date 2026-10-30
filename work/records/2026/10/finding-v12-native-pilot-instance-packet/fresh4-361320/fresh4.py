"""Fresh instance-4 preparation, on the source-pinned bundle. W325959.

OWNER M361302 selects a NEW revision destination and a fresh workload rather
than an updated retained instance: no updater, no migration gate, and every
old instance preserved. So this is the accepted fresh3 preparation, driven
for revision 4 against the bundle built from `614668e0`.

THE ACCEPTED HELPER IS REUSED RATHER THAN COPIED. `fresh3-358443/fresh.py`
resolved the four-step ordering, the pre-mint gate and every refusal, and was
independently accepted at review-2026-10-23T05-17-50Z.md. Copying it here
would create a second copy to drift, so it is IMPORTED and PINNED by digest,
exactly as it imports and pins `post-install-357462/configure.py`.

WHAT IS REBOUND, AND WHY THAT IS NOT AN EDIT. `fresh` declares the revision's
three workload identities as module constants and `_compose` asserts the
submission carries them. This revision has different ones, so those three
names -- and only those three -- are rebound before use. The module's BYTES
are unchanged and pinned; what is rebound is the declaration they exist to
hold. `prepare` below then asserts the answer came back carrying the
revision-4 identities, so the rebinding is checked rather than trusted.

AND THE RETAINED SET GROWS. The accepted module names the two instances that
existed when it was written. Instance 3 exists now and holds the failed
`quickstart-c` the owner is preserving, so it is added -- a destination inside
it would otherwise not have been refused, which this packet's own proof found.

THE BUNDLE AND THE SOURCE ARE THIS REVISION'S OWN. The bundle is the one
pinned by `../bundle-361217/`: built from `614668e0`, 81 files, folder digest
`1b014603...`. The repository source is the checkout at that commit --
`bootstrap.prepare_repositories` CLONES, so what reaches the worker
repositories is committed history and not the dirty working tree.

WHAT THIS NEVER DOES. No submission, no serving, no admission, no engine,
provider or model, no Git mutation, and nothing against instances 1, 2 or 3.
Without `--owner-selected` it PREFLIGHTS and writes nothing.
"""
import argparse
import hashlib
import json
import pathlib
import sys

PACKET = pathlib.Path(__file__).resolve().parent
ACCEPTED = PACKET.parent / "fresh3-358443"
sys.path.insert(0, str(ACCEPTED))
import fresh                                                # noqa: E402

Refused = fresh.Refused

DESTINATION = "/home/sl/baton-instances/native-coordination-pilot-w321608-4"
JOB = "quickstart-d"
SUBMISSION = "sub-w321608-quickstart-4"
TASK = "w321608-native-operator-quickstart-4"

# THE BUNDLE THIS REVISION INSTALLS, pinned by `../bundle-361217/MANIFEST.json`
# and recomputed here through the product's own reader before anything runs.
DISTRO = pathlib.Path("/home/sl/w325959-bundle/out/distro")
BUNDLE_DIGEST = ("1b014603aec40e9f6d9c03a8b21ae74a02d9f1fef1ff95fc0f3e8a851a2"
                 "29c07")
BUNDLE_FILES = 81
SOURCE = pathlib.Path("/home/sl/src/baton")
COMMIT = "614668e0831e8c87cdae11ca43620e0d544a84d5"

# THIS REVISION'S OWN FOUR DOCUMENTS.
PACKET_PINS = {
    "install-inputs.json":
        "sha256:" + hashlib.sha256(
            (PACKET / "install-inputs.json").read_bytes()).hexdigest(),
    "configure-inputs.json":
        "sha256:" + hashlib.sha256(
            (PACKET / "configure-inputs.json").read_bytes()).hexdigest(),
    "task.json":
        "sha256:" + hashlib.sha256(
            (PACKET / "task.json").read_bytes()).hexdigest(),
    "submission.json":
        "sha256:" + hashlib.sha256(
            (PACKET / "submission.json").read_bytes()).hexdigest(),
}
# AND THE TWO HELPERS IT CONSUMES BY IMPORT. `configure.py`'s pin is the
# accepted one `fresh` already enforces; `fresh.py`'s is added here because
# this packet now depends on its bytes the same way.
ACCEPTED_PINS = {
    "fresh.py":
        "sha256:682c6b094f259fd1114781dbe54b79c5bd88c9590162f18a92551ceac586521f",
}


def _of(place):
    return "sha256:" + hashlib.sha256(
        pathlib.Path(place).read_bytes()).hexdigest()


def accepted_helper():
    """The imported helper is the accepted bytes, re-checked every run."""
    answer = {}
    for name, want in ACCEPTED_PINS.items():
        place = ACCEPTED / name
        if not place.is_file():
            raise Refused("the accepted helper " + str(place) + " is absent")
        got = _of(place)
        if got != want:
            raise Refused("the accepted helper " + name + " is " + got
                          + " and this packet consumes " + want
                          + "; a drifted helper is not the reviewed one")
        answer[name] = got
    return answer


def the_bundle():
    """This revision's runtime, recomputed by the product's own reader."""
    from tools import instance

    held = instance.manifest(str(DISTRO))
    if held["digest"] != BUNDLE_DIGEST or held["files"] != BUNDLE_FILES:
        raise Refused(
            "the bundle at " + str(DISTRO) + " holds " + str(held["files"])
            + " files digesting " + held["digest"] + " and this packet pins "
            + str(BUNDLE_FILES) + " digesting " + BUNDLE_DIGEST)
    return held


# EVERY INSTANCE THIS REVISION MUST NOT TOUCH. The accepted module lists the
# two that existed when it was written; instance 3 exists now and holds the
# failed `quickstart-c` the owner is preserving, so it joins the set. Without
# this a destination INSIDE instance 3 would not have been refused -- which
# this packet's own proof caught.
RETAINED = ("/home/sl/baton-instances/native-coordination-pilot-w321608-1",
            "/home/sl/baton-instances/native-coordination-pilot-w321608-2",
            "/home/sl/baton-instances/native-coordination-pilot-w321608-3")


def identities():
    """Rebind the accepted module's declared constants, once.

    CHECKED RATHER THAN TRUSTED: `prepare` asserts the answer carries them.
    """
    fresh.JOB, fresh.SUBMISSION, fresh.TASK = JOB, SUBMISSION, TASK
    fresh.RETAINED = RETAINED
    return {"job": JOB, "submission": SUBMISSION, "task": TASK,
            "retained": list(RETAINED)}


def prepare(destination=DESTINATION, packet=PACKET, *, apply=False,
            bundle=DISTRO, source=SOURCE, runner=None, pins=None,
            check_bundle=True):
    """Revision 4, through the accepted preparation."""
    packet = pathlib.Path(packet)
    answer = {"revision": 4, "destination": destination,
              "source_commit": COMMIT,
              "accepted_helper": accepted_helper(),
              "identities": identities()}
    if check_bundle:
        answer["bundle"] = the_bundle()
    held = fresh.prepare(destination, packet, apply=apply, bundle=bundle,
                         source=source, runner=runner,
                         pins=PACKET_PINS if pins is None else pins)
    # THE REBINDING IS VERIFIED, not assumed: the accepted module's own
    # answer has to carry this revision's identities.
    for name, want in (("job", JOB), ("submission", SUBMISSION),
                       ("task", TASK)):
        if held.get(name) != want:
            raise Refused("the preparation answered " + name + " "
                          + repr(held.get(name)) + " and this revision is "
                          + repr(want))
    answer["preparation"] = held
    return answer


def main(argv=None, *, stream=sys.stdout):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", default=DESTINATION)
    parser.add_argument("--packet", default=str(PACKET))
    parser.add_argument("--bundle", default=str(DISTRO))
    parser.add_argument("--repository-source", default=str(SOURCE))
    parser.add_argument("--owner-selected", action="store_true",
                        help="perform the preparation; without it this "
                             "preflights and writes nothing")
    taken = parser.parse_args(argv)
    try:
        answer = prepare(taken.destination, taken.packet,
                         apply=taken.owner_selected,
                         bundle=pathlib.Path(taken.bundle),
                         source=pathlib.Path(taken.repository_source))
    except Refused as refusal:
        print("refused: " + str(refusal), file=sys.stderr)
        return 2
    json.dump(answer, stream, indent=1, sort_keys=True, default=str)
    stream.write("\n")
    return 0


if __name__ == "__main__":                                  # pragma: no cover
    raise SystemExit(main())
