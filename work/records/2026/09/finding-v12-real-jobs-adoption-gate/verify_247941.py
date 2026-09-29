"""This dossier's pins and its focused witness, measured rather than estimated.

`--pins` re-reads the artifacts ASSESSMENT-249338.md selected and prints what
it found beside what was pinned. It opens no deployed store, starts nothing and
writes nothing outside this dossier.
"""
import argparse
import hashlib
import io
import json
import os
import pathlib
import time
import unittest

HERE = pathlib.Path(__file__).resolve().parent
CHECKOUT = HERE.parents[4]
# THE SELECTED SNAPSHOT, and THE ONE PLACE IT IS NAMED. W247941 review
# 2026-09-29T11-27-34Z: I advanced `prepare_two_jobs` alone while THIS module still pinned
# the consumed `independent-review-247947` root, and `two_jobs.main` reads its value -- so
# the provenance chain disagreed with itself. Every consumer now derives from here.
SNAPSHOT_BEFORE_302142 = pathlib.Path(
    "/home/sl/baton-runs/independent-review-247947/manager-source")
SNAPSHOT = pathlib.Path(os.environ.get(
    "BATON_W247941_SNAPSHOT",
    "/home/sl/baton-instances/single-job-257627-291715/manager-source"))

# THE TWO IMPORT ROOTS, which are NOT the snapshot root. The same review reproduced the
# failure that makes this explicit: a PYTHONPATH of the tree root cannot import `baton_v12`
# or `tools` -- an import-only subprocess raises `ModuleNotFoundError` before any effect.
# The roots are the package root and the directory that holds `tools/`, exactly as the
# accepted single-Job sheet's own PYTHONPATH names them.
IMPORT_ROOTS = (SNAPSHOT / "v12" / "python" / "src", SNAPSHOT / "v12" / "python")


def import_path():
    """The PYTHONPATH a subprocess needs to import the SELECTED product."""
    return os.pathsep.join(str(one) for one in IMPORT_ROOTS)
RUNTIME = pathlib.Path(
    "/home/sl/baton-runs/managed-correction-236087/build/stack/out/distro")

# ---- O1: THE ACCEPTED RUN'S OWN RECORDS, which are the answer ------------
#
# W247941 review 2026-09-29T13-32-53Z: finish O1 by reusing already accepted values rather than
# re-researching them, and DISTINGUISH metadata already verified from genuinely missing selection.
# These two paths hold every remaining operand, and every value below is MEASURED from them:
#
#   ACCEPTED_RUN/PACKET.json    the operational packet the accepted single Job ran under. It carries
#                               `manager_runtime` (path, build commit, executable digest),
#                               `worker_image` (reference, config digest and each worker file's
#                               digest), `supervisor`, `code_boundary`, `manager_source.files` and
#                               the `fixture` files the Job actually read.
#   ACCEPTED_RUN/deployment.json  the configured deployment whose two workers carry the three
#                               DESCRIPTOR digests (adapter, policy, profile) and their names.
#
# THE TWO RUNTIME PATHS ARE NOT A DISAGREEMENT, and this is the distinction the review asked for.
# `RUNTIME` above is the DISTRO -- the historical bootstrap input, and the correct operand for
# `tools.bootstrap --distro`. `manager_runtime.path` is the INSTALLED copy the accepted run
# executed. `accepted()` hashes the executable at BOTH and holds them equal, so the pin identifies
# bytes rather than a location. It has to: the installed runtime's own build stamp records
# `dirty: true`, so the build commit alone does not identify what was built.
ACCEPTED_RUN = pathlib.Path("/home/sl/baton-runs/single-job-257627-291715")
ACCEPTED_INSTANCE = pathlib.Path(
    "/home/sl/baton-instances/single-job-257627-291715")
RUNTIME_EXECUTED = ACCEPTED_INSTANCE / "installation-runtime"
RUNTIME_EXECUTABLE = "baton-v12-stack"

# THE WORKER ADAPTER'S OWN SOURCE, inside the image. `adapter_sha256` has carried this value since
# W239528 claim 244216 with only a review reference for provenance; it is the accepted packet's
# `worker_image.worker_files["opt/baton/claude_agent.py"]`, which is the file the executed image
# actually ran. That is the named record the operand was missing.
ADAPTER_SOURCE = "opt/baton/claude_agent.py"

ACCEPTED_PINS = {
    "adapter_sha256":
        "18c34ff52faa150237df0c8d0206b805801ee71cb9e7a4ec6e84e4379d7f9d8d",
    "image_reference": "baton-v12-claude-worker:w239528-244216",
    "image_digest": "sha256:c862c055c6430addc918ca078a9e4d55f"
                    "6bd8173ed9c9878a8ad9d6cad334ca2",
    "runtime_build": "1e576ff2186db69e8b44da9d38874ff7e99ebbe3",
    "runtime_executable_sha256":
        "04aa459aed61704971e98b9260929b19953c41caad906e28551aae0ba457a58a",
    "supervisor_sha256":
        "248e570d8f9d459550b0aa5e92d1674c3226fe540ba987cae916a4a334606771",
    "stage_execution_sha256":
        "38c4cf74db023733603ea88f02b0246c0b16a62afecb743b77cf502ffc5e19e6",
    "adapter_name": "docker-single-worker",
    "adapter_digest": "sha256:5f2ef38f05ed7a9aecd11dd7e23e9cfb"
                      "e1f0243fe27bd2c9aa1b004580fcdef1",
    "policy_digest": "sha256:d398f8585dc7118d76836fdee00dcc0a"
                     "ae9882250e88e79cdd4ff7de19574795",
    "profile_digest": "sha256:93fdea4ac36c54656a7534b72ba0ea7d"
                      "796b5294cdb2fd7de4056d52709675be",
    "retention_policy_digest": "sha256:0f4cd2d13c46e81cb6e721119e48b342"
                               "efb3a7a0d831e241c429601aa2eae45a",
    # THE NAME COMES FROM THE SAME RECORD AS THE DIGEST, which it did not before. This packet
    # carried `claude-context-review` beside the accepted run's digest `93fdea4a…`; BOTH accepted
    # workers -- implementation and review -- are configured `claude-fresh-implementation`. A name
    # from one campaign beside a digest from another is exactly the pairing O1 exists to catch.
    "profile_name": "claude-fresh-implementation",
    "code_boundary": str(ACCEPTED_INSTANCE / "manager-source"),
    "runtime_executed_path": str(RUNTIME_EXECUTED),
}


def _accepted_document(name):
    place = ACCEPTED_RUN / name
    if not place.is_file():                                  # pragma: no cover
        return None
    with open(place, encoding="utf-8") as handle:
        return json.load(handle)


def accepted():
    """Every remaining ACCEPTED operand, MEASURED from the accepted run's own records.

    Reads two documents and one file. Opens no store, starts nothing, writes nothing. An absent
    record answers `None` for the values it would have carried rather than passing quietly, and
    `agree` is then False -- these are pins, so they fail closed.
    """
    held = {"pinned": dict(ACCEPTED_PINS), "found": {},
            "sources": {"packet": str(ACCEPTED_RUN / "PACKET.json"),
                        "deployment": str(ACCEPTED_RUN / "deployment.json"),
                        "distro_executable": str(RUNTIME / RUNTIME_EXECUTABLE),
                        "executed_executable":
                            str(RUNTIME_EXECUTED / RUNTIME_EXECUTABLE)}}
    found = held["found"]
    packet = _accepted_document("PACKET.json")
    if packet:
        image = packet.get("worker_image") or {}
        runtime = packet.get("manager_runtime") or {}
        supervisor = packet.get("supervisor") or {}
        found["adapter_sha256"] = (image.get("worker_files") or {}).get(
            ADAPTER_SOURCE)
        found["image_reference"] = image.get("reference")
        found["image_digest"] = image.get("config_digest")
        found["runtime_build"] = runtime.get("build_commit")
        found["runtime_executable_sha256"] = runtime.get("executable_sha256")
        found["runtime_executed_path"] = runtime.get("path")
        found["supervisor_sha256"] = supervisor.get("sha256")
        found["code_boundary"] = packet.get("code_boundary")
        found["stage_execution_sha256"] = (
            packet.get("manager_source") or {}).get("files", {}).get(
                "tools/stage_execution.py")
    deployment = _accepted_document("deployment.json")
    if deployment:
        # BOTH WORKERS, and they must AGREE: a descriptor that differs between the two is one
        # worker's configuration rather than the instance's, and reading `workers[0]` alone would
        # not notice. Review 2026-09-29T11-58-42Z made that distinction and this measures it.
        configured = [one.get("deployment") or {}
                      for one in deployment.get("workers") or ()]
        for name in ("adapter_name", "adapter_digest", "policy_digest",
                     "profile_digest", "profile_name",
                     "retention_policy_digest"):
            values = {one.get(name) for one in configured}
            found[name] = values.pop() if len(values) == 1 else sorted(
                str(one) for one in values)
    # THE SAME BYTES AT BOTH RUNTIME PATHS, which is what makes the executable digest the pin and
    # the path a locator.
    for label, root in (("distro", RUNTIME), ("executed", RUNTIME_EXECUTED)):
        place = root / RUNTIME_EXECUTABLE
        held.setdefault("runtime_executables", {})[label] = (
            sha(place) if place.is_file() else f"absent at {place}")
    held["runtime_executables_agree"] = (
        len(set(held["runtime_executables"].values())) == 1
        and held["runtime_executables"]["distro"]
        == ACCEPTED_PINS["runtime_executable_sha256"])
    held["agree"] = (all(found.get(name) == value
                         for name, value in held["pinned"].items())
                     and held["runtime_executables_agree"])
    return held
# THE PINS OF THE SELECTED SNAPSHOT, each DERIVED from it with this module's own
# `source_files`/`manifest_digest` rather than copied from a report:
#
#   126 is `len(source_files(SNAPSHOT))` -- the whole snapshot, caches excluded.
#   109 is the count of `manager-source/` MEMBERS in `FINAL-PACKET-302142.json`.
#   The review resolved these as two different member sets rather than a conflict, and both
#   are recorded so neither number is mistaken for the other again.
PINNED = {
    "manager_source_files": 126,
    "manager_source_manifest_sha256": "a8264fd390c46fa1b090b2b6e318130c75cbfd93dfab3113fad1521616a0643e",
    "stage_execution_sha256":
        "38c4cf74db023733603ea88f02b0246c0b16a62afecb743b77cf502ffc5e19e6",
    "runtime_executable_sha256":
        "04aa459aed61704971e98b9260929b19953c41caad906e28551aae0ba457a58a",
}

# THE SUPERSEDED VALUES, kept so every earlier result in this dossier stays attributable to the
# generation it was measured against -- AND KEPT OUT OF `PINNED`. W247941 review
# 2026-09-29T11-35-05Z: I put them inside it, so `pins()` compared four history keys against a
# `found` map that has no measurement for them and reported mismatches that were my bookkeeping
# rather than any disagreement about source. History is metadata; a pin is something this module
# MEASURES.
HISTORY = {
    # THE OPERATIONAL PACKET'S OWN COUNT, identified at review 2026-09-29T11-42-13Z:
    # `/home/sl/baton-runs/single-job-257627-291715/PACKET.json` states
    # `manager_source.file_count` 109 and enumerates 109 members. It is a DIFFERENT member set
    # from this dossier's manifest, not a disagreement with it.
    "operational_packet_manager_source_files": 109,
    "manager_source_files_before_302142": 106,
    "manager_source_manifest_sha256_before_302142":
        "ab5e5b0befbb77f6e96a94e76d0d8b6e01935beb2e7f48090d0d3fc13fae1cd5",
    "stage_execution_sha256_before_302142":
        "6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801",
}

# THE PACKET'S OWN MEMBER COUNT, which is a DIFFERENT member set from `PINNED`'s whole-snapshot
# count and is therefore measured against the packet rather than the tree. Retained as an active
# pin because the review asked for it to be measured if retained; `_packet_members` below is the
# measurement, and an absent manifest answers `None` rather than passing quietly.
PACKET_MANIFEST = pathlib.Path(
    "/home/sl/src/baton/work/records/2026/09/finding-v12-startup-failure-fresh-packet"
    "/FINAL-PACKET-302142.json")
# 126, MEASURED from THIS manifest by `_packet_members` below, and the ambiguity is RESOLVED
# rather than left open. W247941 review 2026-09-29T11-42-13Z identified both member sets:
#
#   109 is the OPERATIONAL packet at `/home/sl/baton-runs/single-job-257627-291715/PACKET.json`,
#       whose `manager_source.file_count` and `len(manager_source.files)` both say 109;
#   126 is this dossier's `FINAL-PACKET-302142.json` filtered for `/manager-source/` members,
#       which is also what counting the tree with `source_files` gives.
#
# Two different sets, both valid, and neither is a wrong number. My previous prose called 109's
# provenance unidentified; it is identified, and that prose is withdrawn.
PACKET_MEMBERS = 126


def _packet_members():
    """How many `manager-source/` members the accepted packet manifest enumerates."""
    if not PACKET_MANIFEST.is_file():                        # pragma: no cover
        return None
    with open(PACKET_MANIFEST, encoding="utf-8") as handle:
        held = json.load(handle)
    return sum(1 for one in held.get("files", ())
               if "/manager-source/" in one.get("path", ""))
OWNED = ("two_jobs.py", "test_two_jobs.py", "align_template.py",
         "add_roundtrip.py", "apply_249551.py", "apply_249551_tests.py",
         "apply_249551_root.py", "two_job_supervisor.py",
         "ADOPTION-247941.md",
         "CONTINUITY-247941.md", "SELECTIONS-247941.json", "verify_247941.py")
MODULES = ("test_two_jobs",)


# WHERE THE DISPOSABLE FIXTURE ROOT MAY LIVE, and why it is not folklore.
#
# Review 2026-09-23T17:25:40Z ran the roundtrip cases with a fixture root the
# product refused: `held_configuration` calls any mutable state inside "the
# checkout" a policy denial, and the checkout it detects is derived from the
# SOURCE THAT IMPORTED IT. Bound to the pinned snapshot under
# `/home/sl/baton-runs/...`, that makes `/home/sl/baton-runs` the checkout --
# so a fixture root under it is refused even though it is nowhere near the
# repository.
#
# The guard is right and is not weakened here. What this names is the setup
# that satisfies it: a DISK-BACKED directory outside both the repository and
# the pinned source's own root.
FIXTURE_ROOT_VARIABLE = "BATON_V12_DISK_ROOT"
FIXTURE_ROOT = "/var/tmp/baton-w247941"


def fixture_root_setup():
    """The exact command that prepares a usable disposable root."""
    return (f"mkdir -p {FIXTURE_ROOT} && "
            f"{FIXTURE_ROOT_VARIABLE}={FIXTURE_ROOT}")


def held_fixture_root(place=None):
    """Why a given fixture root will or will not serve. READ ONLY."""
    import os
    place = place or os.environ.get(FIXTURE_ROOT_VARIABLE)
    if not place:
        return [f"{FIXTURE_ROOT_VARIABLE} is unset; the suite would choose a "
                f"root for itself and may choose one the product refuses. "
                f"Use: {fixture_root_setup()}"]
    held = []
    whole = os.path.realpath(place)
    for what, root in (("this repository", str(CHECKOUT)),
                       ("the pinned source's own root",
                        os.path.dirname(str(SNAPSHOT)))):
        root = os.path.realpath(root)
        if os.path.commonpath([whole, root]) == root:
            held.append(f"{whole} is inside {what} at {root}; "
                        f"`held_configuration` denies mutable state there. "
                        f"Use: {fixture_root_setup()}")
    return held


def sha(path):
    reading = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            reading.update(block)
    return reading.hexdigest()


def source_files(root):
    """Every SOURCE file in the snapshot, compiled caches excluded.

    W247941, claim 255973. The snapshot held 193 files where this pins 106,
    and the extra 87 are `__pycache__` byte-code written into it at
    2026-09-24T04:27 by a run that imported from it -- importing from a
    directory writes caches into that directory. No source file was touched:
    none has an mtime later than the pin, the 106 remaining are byte-identical
    to the working tree except the three this Work owns and has edited, and
    with the caches excluded the manifest below reproduces the pinned
    `ab5e5b0b…` EXACTLY.

    So the count and the digest are taken over source, which is what they were
    always meant to describe. Nothing was deleted from the snapshot to make
    this true -- removing files from preserved material is not this Work's to
    do, and a digest made true by tidying the evidence would not be a digest.

    THE BOUNDARY CHANGED AND SAYING "NOTHING IS WEAKENED" WAS TOO BROAD.
    Review 2026-09-24T10:35:28Z [R3], and it is right. What this attests is
    SOURCE IDENTITY: the same 106 files, still moving on a changed byte, a
    rename or a swap. What it no longer attests is every byte Python may
    EXECUTE from this directory, because the former all-file boundary covered
    the caches and this does not. `PYTHONDONTWRITEBYTECODE` and `-B` prevent
    WRITING byte-code; they do not prevent LOADING an existing `.pyc`, so a
    cache-contaminated import root could still execute bytes no source digest
    here describes.

    THAT IS AN OPEN ITEM AND NOT A CLOSED ONE. The new reviewable snapshot
    owes a clean or separately verified import-cache boundary, so unreviewed
    cached code cannot stand in for reviewed source, with its own focused
    verifier cases. This function is the source half of that proof and is
    deliberately not the whole of it.
    """
    return [place for place in root.rglob("*")
            if place.is_file() and "__pycache__" not in place.parts]


def manifest_digest(root):
    """ONE digest over every source file in the snapshot, paths included.

    Review 2026-09-23T17:12:02Z R5: counting 106 files says nothing about
    their CONTENT, and the count is the one property a drifted snapshot is
    most likely to keep. This hashes the sorted (relative path, file digest)
    pairs, so a changed byte, a renamed file or a swapped pair all move it.
    """
    reading = hashlib.sha256()
    for one in sorted(source_files(root)):
        reading.update(str(one.relative_to(root)).encode("utf-8"))
        reading.update(b"\0")
        reading.update(sha(one).encode("ascii"))
        reading.update(b"\n")
    return reading.hexdigest()


def pins():
    """What the selected artifacts hash to NOW, beside what was pinned."""
    held = {"pinned": dict(PINNED), "found": {}}
    if SNAPSHOT.is_dir():
        held["found"]["manager_source_files"] = len(source_files(SNAPSHOT))
        # THE LOCATOR IS THE SNAPSHOT'S REAL LAYOUT. Review 2026-09-29T11-35-05Z: this said
        # `SNAPSHOT/tools`, which is not where the file lives -- so `stage_execution_sha256`
        # answered `None` and looked like a disagreement when it was a wrong path.
        place = SNAPSHOT / "v12" / "python" / "tools" / "stage_execution.py"
        held["found"]["stage_execution_sha256"] = (
            sha(place) if place.is_file() else None)
        held["found"]["manager_source_manifest_sha256"] = manifest_digest(
            SNAPSHOT)
    else:                                                    # pragma: no cover
        held["found"]["manager_source"] = f"absent at {SNAPSHOT}"
    executable = RUNTIME / "baton-v12-stack"
    held["found"]["runtime_executable_sha256"] = (
        sha(executable) if executable.is_file() else f"absent at {executable}")
    held["checkout_stage_execution_sha256"] = sha(
        CHECKOUT / "v12/python/tools/stage_execution.py")
    held["fixture_root"] = held_fixture_root()
    # THE PACKET MEMBER COUNT IS MEASURED, not asserted. It is a second member set, so it is
    # compared against the packet manifest and reported beside the whole-snapshot count.
    held["pinned"]["packet_manager_source_members"] = PACKET_MEMBERS
    held["found"]["packet_manager_source_members"] = _packet_members()
    held["history"] = dict(HISTORY)
    # AND THE ACCEPTED RUN'S OWN OPERANDS, in the same answer and under the same `agree`. W247941
    # review 2026-09-29T13-32-53Z asked for O1 to be finished and PINNED rather than left as prose:
    # one command now reports the snapshot pins and the accepted-run pins together, and fails closed
    # on either.
    held["accepted_run"] = accepted()
    held["agree"] = (all(held["found"].get(name) == value
                         for name, value in held["pinned"].items())
                     and held["accepted_run"]["agree"])
    return held


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pins", action="store_true")
    parser.add_argument("--claim", type=int, default=249364)
    # THE RECEIPT IS NUMBERED BY THE CALLER. It was hardcoded to 17, so a
    # later run silently overwrote the receipt an earlier claim had cited
    # as its evidence.
    parser.add_argument("--receipt", type=int, default=17)
    chosen = parser.parse_args(argv)
    if chosen.pins:
        held = pins()
        print(json.dumps(held, indent=2, sort_keys=True))
        # IT FAILS CLOSED. The first version printed a disagreement and exited
        # 0, so an operator following step 1 of the packet would have seen a
        # drifted artifact and a success status in the same breath.
        return 0 if held["agree"] else 1
    loader = unittest.TestLoader()
    suite = unittest.TestSuite(
        [loader.loadTestsFromName(one) for one in MODULES])
    stream = io.StringIO()
    started = time.perf_counter()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    elapsed = time.perf_counter() - started
    log = f"verification-{chosen.receipt}.log"
    (HERE / log).write_text(stream.getvalue(), encoding="utf-8")
    receipt = {
        "schema": "baton.v12-adoption-gate-verification/1",
        "work": "W247941", "claim": chosen.claim,
        "participant": "baton.claude",
        "modules": list(MODULES),
        "checks": result.testsRun, "failures": len(result.failures),
        "errors": len(result.errors), "skipped": len(result.skipped),
        "measured_seconds": elapsed,
        "python": os.sys.version.split()[0],
        "owned": {name: sha(HERE / name) for name in OWNED},
        "pins": pins(),
        "log": log,
        "note": "the two-Job arrangement held by the product's own validator "
                "and driven through W130224's accepted two-Job fixture on "
                "disposable stores. No container, image, engine, live "
                "provider, network, credential, deployed store or deployment "
                "change.",
    }
    (HERE / f"verification-{chosen.receipt}.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({one: receipt[one] for one in
                      ("checks", "failures", "errors", "measured_seconds")},
                     indent=2))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
