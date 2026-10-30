"""Fresh instance-4 preparation, corrected. W325959, claim361402.

Answers `review-2026-10-24T02-35-41Z.md` R1-R3. Owner M361302 still stands: a
new revision destination and a fresh workload, no updater, no migration gate,
instances 1-3 preserved. `fresh4-361320` is preserved and superseded.

WHAT WAS WRONG WITH THE PREVIOUS ENTRYPOINT, and what each correction is.

  R2a. IT HASHED ITS OWN DOCUMENTS AT IMPORT AND CALLED THAT A PIN. A valid
  edit made before launch simply became the expectation, so the pin proved
  nothing an operator could rely on. The four digests below are now LITERAL
  CONSTANTS, reviewed with this file, and `prepare` refuses a document that
  does not hash to its literal -- which is what a pin is for.

  R2b. IT VERIFIED THE DEFAULT BUNDLE AND INSTALLED THE SELECTED ONE.
  `the_bundle` always hashed `DISTRO` while `prepare` passed `--bundle`
  through, so a different admissible bundle could be installed while the
  answer reported the reviewed one's digest. The bundle that is VERIFIED is
  now the bundle that is USED, and a caller selecting another must state the
  digest it expects -- there is no unchecked override.

  R3. THE SOURCE REVISION WAS A LABEL. `COMMIT` was reported and never
  checked, so a plain unversioned directory containing `v12` preflighted
  happily while the answer claimed `614668e0`. The source's actual `HEAD` is
  now READ -- `git -C <source> rev-parse HEAD`, a read, never a mutation --
  and a source that is not a repository, or is at another commit, refuses
  before the mint.

  R3 (the base). The previous packet's task and configuration declared
  `30245386` while claiming `614668e0` as the source. `30245386` is an
  ancestor, so it existed in the clone and nothing would have failed -- but
  naming an older base while cloning a newer HEAD is two statements about one
  selection. This revision's documents declare `614668e0`, so the declared
  base, the cloned target and the recorded source are one commit.

  R1 is a COMMANDS.md correction: `generated/preparation-readback.json` is
  the accepted module's OWN answer, whose `workspace_storage` is top-level
  and which has no `preparation` member. The selection-2b command indexed a
  wrapper that is not in the file. The proof now extracts it from the ACTUAL
  emitted document rather than asserting the shape.

THE ACCEPTED HELPER IS STILL IMPORTED AND PINNED, never copied; what is
rebound is its declared `JOB`, `SUBMISSION`, `TASK` and `RETAINED` constants,
and the rebinding is verified against the answer.

WHAT THIS NEVER DOES. No submission, no serving, no admission, no engine,
provider or model, no Git MUTATION, and nothing against instances 1, 2 or 3.
Without `--owner-selected` it PREFLIGHTS and writes nothing.
"""
import argparse
import hashlib
import json
import pathlib
import subprocess
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

# THE BUNDLE THIS REVISION INSTALLS. The digest is the reviewed one from
# `../bundle-361217/`; `the_bundle` recomputes whichever bundle is SELECTED
# and compares it with the expectation the caller is accountable for.
DISTRO = pathlib.Path("/home/sl/w325959-bundle/out/distro")
BUNDLE_DIGEST = ("1b014603aec40e9f6d9c03a8b21ae74a02d9f1fef1ff95fc0f3e8a851a2"
                 "29c07")
BUNDLE_FILES = 81
SOURCE = pathlib.Path("/home/sl/src/baton")
COMMIT = "614668e0831e8c87cdae11ca43620e0d544a84d5"

# LITERAL, REVIEWED WITH THIS FILE. Not computed at import: a pin a program
# derives from the bytes it is checking is not a pin.
PACKET_PINS = {
    "install-inputs.json":
        "sha256:6f544c461007ec85faa884b2d4843f431f96f1835d65e91a55ae4cd388"
        "07b937",
    "configure-inputs.json":
        "sha256:f60b129baad7fc098be76af530a6705b96cd510aa4d8b2ff552cf3b9d6e"
        "2a494",
    "task.json":
        "sha256:91a13de94a23941b6653b9da40ae56e28046c7b30456def7346382431852"
        "72f0",
    "submission.json":
        "sha256:863073a4db40e20490fcef782622d63f94d9267230ce0d86c3e0f769fb8"
        "6b26a",
}
ACCEPTED_PINS = {
    "fresh.py":
        "sha256:682c6b094f259fd1114781dbe54b79c5bd88c9590162f18a92551ceac58"
        "6521f",
}
RETAINED = ("/home/sl/baton-instances/native-coordination-pilot-w321608-1",
            "/home/sl/baton-instances/native-coordination-pilot-w321608-2",
            "/home/sl/baton-instances/native-coordination-pilot-w321608-3")


def _of(place):
    return "sha256:" + hashlib.sha256(
        pathlib.Path(place).read_bytes()).hexdigest()


def _pinned(root, pins, *, what):
    answer = {}
    for name, want in sorted(pins.items()):
        place = pathlib.Path(root, name)
        if not place.is_file():
            raise Refused(what + ": " + str(place) + " is absent")
        got = _of(place)
        if got != want:
            raise Refused(what + ": " + name + " is " + got + " and this "
                          "packet pins " + want + "; an edited document is "
                          "not the reviewed one")
        answer[name] = got
    return answer


def the_packet(packet=PACKET, pins=None):
    """The four documents, against the LITERAL expectations. R2a."""
    return _pinned(packet, PACKET_PINS if pins is None else pins,
                   what="the packet document")


def accepted_helper():
    return _pinned(ACCEPTED, ACCEPTED_PINS, what="the accepted helper")


def the_bundle(bundle=DISTRO, *, digest=None, files=None):
    """The SELECTED bundle, recomputed and held to a stated expectation. R2b.

    `digest` is what the caller says this bundle must be. It defaults to the
    reviewed one, so the ordinary path verifies what it installs; a caller
    selecting a different bundle has to say which, and nothing is accepted
    unverified.
    """
    from tools import instance

    want = BUNDLE_DIGEST if digest is None else digest
    count = BUNDLE_FILES if files is None else files
    held = instance.manifest(str(bundle))
    if held["digest"] != want or (count is not None
                                  and held["files"] != count):
        raise Refused(
            "the SELECTED bundle at " + str(bundle) + " holds "
            + str(held["files"]) + " files digesting " + held["digest"]
            + " and this run expects " + str(count) + " digesting " + want)
    return dict(held, at=str(bundle))


def the_source(source=SOURCE, *, commit=None):
    """The selected source's ACTUAL revision, read from the repository. R3.

    A READ. `rev-parse` names the commit; nothing is written, staged,
    checked out or fetched. A directory that is not a repository, or one at
    another commit, refuses here -- before anything is minted.
    """
    want = COMMIT if commit is None else commit
    source = pathlib.Path(source)
    if not (source / "v12").is_dir():
        raise Refused("the selected source at " + str(source)
                      + " carries no v12 tree")
    try:
        ran = subprocess.run(["git", "-C", str(source), "rev-parse", "HEAD"],
                             capture_output=True, text=True, timeout=30)
    except OSError as failure:
        raise Refused("the selected source's revision could not be read: "
                      + str(failure)) from None
    if ran.returncode != 0:
        raise Refused(
            "the selected source at " + str(source) + " is not a repository "
            "this run can name a revision for: "
            + (ran.stderr or "").strip()[:160] + ". A source whose revision "
            "nobody can state is not a pinned input")
    held = ran.stdout.strip()
    if held != want:
        raise Refused("the selected source at " + str(source) + " is at "
                      + held + " and this packet pins " + want
                      + "; a later commit silently changes what is cloned")
    return {"at": str(source), "commit": held}


def identities():
    fresh.JOB, fresh.SUBMISSION, fresh.TASK = JOB, SUBMISSION, TASK
    fresh.RETAINED = RETAINED
    return {"job": JOB, "submission": SUBMISSION, "task": TASK,
            "retained": list(RETAINED)}


def prepare(destination=DESTINATION, packet=PACKET, *, apply=False,
            bundle=DISTRO, source=SOURCE, runner=None, pins=None,
            bundle_digest=None, bundle_files=None, commit=None):
    """Revision 4, corrected, through the accepted preparation."""
    packet = pathlib.Path(packet)
    answer = {"revision": 4, "corrected": "claim361402",
              "destination": destination,
              "packet_pins": the_packet(packet, pins),
              "accepted_helper": accepted_helper(),
              "identities": identities(),
              # THE BUNDLE THAT IS VERIFIED IS THE ONE THAT IS USED.
              "bundle": the_bundle(bundle, digest=bundle_digest,
                                   files=bundle_files),
              "source": the_source(source, commit=commit)}
    answer["source_commit"] = answer["source"]["commit"]
    held = fresh.prepare(destination, packet, apply=apply, bundle=bundle,
                         source=source, runner=runner,
                         pins=PACKET_PINS if pins is None else pins)
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
    parser.add_argument("--bundle-digest", default=None,
                        help="the digest the SELECTED bundle must have; "
                             "defaults to the reviewed one, and a different "
                             "bundle must state its own")
    parser.add_argument("--repository-source", default=str(SOURCE))
    parser.add_argument("--commit", default=None,
                        help="the revision the selected source must be at; "
                             "defaults to the pinned one")
    parser.add_argument("--owner-selected", action="store_true",
                        help="perform the preparation; without it this "
                             "preflights and writes nothing")
    taken = parser.parse_args(argv)
    try:
        answer = prepare(taken.destination, taken.packet,
                         apply=taken.owner_selected,
                         bundle=pathlib.Path(taken.bundle),
                         source=pathlib.Path(taken.repository_source),
                         bundle_digest=taken.bundle_digest,
                         commit=taken.commit)
    except Refused as refusal:
        print("refused: " + str(refusal), file=sys.stderr)
        return 2
    json.dump(answer, stream, indent=1, sort_keys=True, default=str)
    stream.write("\n")
    return 0


if __name__ == "__main__":                                  # pragma: no cover
    raise SystemExit(main())
