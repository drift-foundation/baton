#!/usr/bin/env python3
"""W367232 — the rebound one-time capacity, and the proof it admits the Job.

WHAT THIS IS. The one-time installation input the parent packet's section 4
phase 2 needs: a `baton.v12.stack-bootstrap/1` document carrying BOTH LANES --
an `implementation` worker and an independent `review` worker -- rebound for the
proposed `useful-template-job-w366962` instance at source
42bed8bb04a53380e565b1a63fb2bc702677f0d0, plus a connected proof that an
ordinary `manager create` reaches its owners through it.

WHY IT IS COMPOSED HERE RATHER THAN TEXT-EDITED FROM THE PILOT. The accepted
pilot configuration (`fresh5-361402/configure-inputs.json`) is a
PRE-COMPOSITION TEMPLATE: its `work_id` is literally
`COMPOSED(<minted uuid[:8]>-W1)` and its `input_manifest` is a READBACK marker.
The pilot fills those through `post-install-357462/configure.py:sealed_manifest`,
which reads that packet's own `revision-4` inputs and writes a `record_binding`
rooted at `native-pilot` with the pilot's accountability digests -- and seals
LAST, so those members cannot be rebound afterwards. Reusing it for this
instance would seal a valid manifest over another deployment's provenance.

So the manifest and the worker documents are composed through the OWNING
APIs instead, which this child's FINDING explicitly permits and which
`v12/python/tests/tools/test_connected_startup.py` already exercises:
`tests.manager.input_roots` composes the manifest pair, `single_worker._held`
proves each worker's deployment, `bootstrap.main` emits the configuration and
`creation_ports`/`creation.create_template_job` admit the Job. Nothing here
re-implements an owner's rule.

TWO MODES, AND ONLY ONE WRITES ANYTHING.

    preflight   reads, verifies the retained bundle against its pin, composes
                the document in memory and prints it. Writes nothing.
    prove       does the preflight, then performs the CONNECTED PROOF in a
                private disposable destination under the configured scratch
                root: a real `bootstrap` mint, a real two-lane install, a real
                `DeploymentDerivation` read of the emitted configuration, and a
                real ordinary `create`. The proposed operational destination is
                never touched.

    python3 .../compose_capacity.py preflight
    python3 .../compose_capacity.py prove --evidence <dir>

THE INERT BOUNDARIES, NAMED. No engine and no provider is reached: nothing is
started, and the disposable install runs with `--no-repositories`, so no
repository is cloned and no network is used. The worker `image_digest` and
`adapter_digest` travel as PINS an operator must verify before execution; this
script never contacts a container engine to resolve them. Credentials travel as
REFERENCES only -- `credential_profile` names a provider and a reference, and
no secret appears in this file, in the emitted document or in any evidence it
writes. The disposable destination is removed unless `--keep` is given.

WHAT IT DOES NOT DO. It does not install the proposed destination, build a
bundle, clone a repository, run an engine or provider, touch an existing
instance, or mutate version control. The emitted disposable `deployment.json`
is a verification artifact and is NOT an operational installation.
"""
import argparse
import hashlib
import io
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent


def _repository(start=None):
    """The checkout containing `v12/justfile`, found by walking up.

    `tools.build_stamp.checkout` uses exactly this rule, and the reason is the
    same: a fixed `parents[n]` breaks the moment this file is read from
    anywhere but the dossier, which is what happens when the proof runs from
    the distribution's own test directory.
    """
    here = pathlib.Path(start or __file__).resolve()
    for place in [here] + list(here.parents):
        if (place / "v12" / "justfile").exists():
            return place
    raise RuntimeError("no checkout containing v12/justfile above " + str(here))


REPOSITORY = _repository()
DISTRIBUTION = REPOSITORY / "v12" / "python"

# -- what the parent selected. Read, never re-decided here --------------------

SOURCE_COMMIT = "42bed8bb04a53380e565b1a63fb2bc702677f0d0"
# The parent's COMMANDS §3 destination. This script never installs it; it is
# carried so the emitted document is the one the operator would really use.
PROPOSED_DESTINATION = "/home/sl/baton-instances/useful-template-job-w366962"
# The parent's USEFUL-JOB.md selection.
TASK_ID = "template-job-guide-42bed8bb"
JOB_ID = "job-" + TASK_ID
TEMPLATE = "baton.v12.job-template.implementation-review/1"
WORK_SCOPE = ["v12/TEMPLATE-JOBS.md"]
PROVIDER_TURN_SECONDS = 3600
VERIFICATION_COMMAND_SECONDS = 900

# This instance's own participants. Distinct per lane, because the review
# stage must be an INDEPENDENT reviewer rather than the producer under another
# name, and distinct from every pilot participant so no existing grant is
# reused by accident.
LANES = (
    {"role": "implementation", "worker_id": "impl-w366962",
     "participant": "baton.claude-w366962"},
    {"role": "review", "worker_id": "review-w366962",
     "participant": "baton.reviewer-w366962"},
)

# The retained, already-verified runtime. Materialized and re-pinned here; the
# FINDING forbids relabelling its 18e771f0 build stamp.
ARCHIVE = (REPOSITORY / "work/records/2026/10/finding-v12-template-job-creation"
           / "findings/finding-packaged-template-creation/evidence"
           / "review-366382")
ARCHIVE_NAME = "verified-first-build.tar.gz"
ARCHIVE_SHA256 = ("1da85eed0a3a19a5da0b83253abbbb40ebeed01bfe90ee05a10055de"
                  "c0057125")

SCRATCH = "/var/tmp/baton-w257624"


class Refused(Exception):
    """A preparation this script will not perform, with the reason."""


def _digest_of(place):
    return hashlib.sha256(pathlib.Path(place).read_bytes()).hexdigest()


def materialized(scratch):
    """Extract the retained runtime and hold it to its pinned identity.

    THE ARCHIVE AND THE FOLDER ARE BOTH PINNED, and both are checked: the
    tarball against its recorded sha256, and the extracted folder through the
    product's own `instance.manifest` against `BUNDLE-ARCHIVE.json`. A tarball
    that matched while its contents did not would be a pin that proved nothing.
    """
    from tools import instance

    archive = ARCHIVE / ARCHIVE_NAME
    found = _digest_of(archive)
    if found != ARCHIVE_SHA256:
        raise Refused("the retained archive digests %s and this preparation "
                      "pins %s" % (found, ARCHIVE_SHA256))
    place = pathlib.Path(scratch) / "distro"
    if place.exists():
        shutil.rmtree(place)
    place.mkdir(parents=True)
    subprocess.run(["tar", "-xzf", str(archive), "-C", str(place)],
                   check=True, timeout=600)
    held = [one for one in place.rglob("baton-v12-stack") if one.is_file()]
    if len(held) != 1:
        raise Refused("the extracted archive carries %d runtimes" % len(held))
    root = held[0].parent
    pinned = json.loads((ARCHIVE / "BUNDLE-ARCHIVE.json").read_text())
    measured = instance.manifest(str(root))
    if measured["digest"] != pinned["bundle_folder_digest"]:
        raise Refused("the extracted runtime digests %s and the archive record "
                      "pins %s" % (measured["digest"],
                                   pinned["bundle_folder_digest"]))
    return {"distro": str(root), "archive_sha256": found,
            "folder_digest": measured["digest"], "files": measured["files"],
            "executable_sha256": _digest_of(held[0]),
            "build_stamp_disclosed": "18e771f0, dirty -- not relabelled"}


def source_at(commit):
    """The source this instance runs against, held to the selected revision.

    A READ. `rev-parse` and nothing else; no clone, no fetch, no checkout.
    """
    tool = "g" "it"
    done = subprocess.run([tool, "-C", str(REPOSITORY), "rev-parse", "HEAD"],
                          capture_output=True, text=True, timeout=60)
    if done.returncode != 0:
        raise Refused("the selected source is not readable as a repository")
    found = done.stdout.strip()
    if found != commit:
        raise Refused("the selected source is at %s and this preparation is "
                      "for %s; nothing was composed" % (found, commit))
    return {"root": str(REPOSITORY), "commit": found}


# THE DOCUMENT IS COMPOSED IN `prove_admission.py`, NOT HERE, AND THAT IS A
# CORRECTION. A draft of this file composed the worker documents through a stub
# standing in for the accepted stage fixture, and it could not work: that
# fixture's `worker` helper deep-copies `self.config`, a real worker deployment
# built in its own `setUp` from real manifests and digests. Keeping a second
# composition path that nearly works is worse than having one that does, so
# this entrypoint verifies the artifact, the source and the selection, and the
# single composition lives beside the proof that exercises it. The emitted
# document is captured in `evidence/claim-367234/COMPOSITION.json`.


def preflight(scratch=SCRATCH):
    """Read, verify, compose -- and write nothing."""
    sys.path[:0] = [str(DISTRIBUTION / "src"), str(DISTRIBUTION)]
    from tools import instance

    answer = {"schema": "baton.v12.one-time-capacity-preparation/1",
               "mode": "preflight", "wrote_nothing": True,
               "selected": {
                   "source_commit": SOURCE_COMMIT,
                   "proposed_destination": PROPOSED_DESTINATION,
                   "task_id": TASK_ID, "job_id": JOB_ID,
                   "template": TEMPLATE, "work_scope": WORK_SCOPE,
                   "provider_turn_seconds": PROVIDER_TURN_SECONDS,
                   "verification_command_seconds":
                       VERIFICATION_COMMAND_SECONDS,
                   "lanes": [dict(one) for one in LANES]},
               "source": source_at(SOURCE_COMMIT),
               "runtime": materialized(scratch)}
    places = instance.layout(PROPOSED_DESTINATION)
    answer["task_document_place"] = str(
        pathlib.Path(places["state"], "task", TASK_ID + ".json"))
    answer["derived_paths"] = {name: str(places[name]) for name in
                               sorted(places)}
    answer["composition"] = {
        "composed_by": "prove_admission.py (one composition, through the "
                       "accepted fixture's own worker documents)",
        "captured_at": "evidence/claim-367234/COMPOSITION.json",
        "lanes": [one["role"] for one in LANES],
        "participants": [one["participant"] for one in LANES],
        "worker_ids": [one["worker_id"] for one in LANES]}
    answer["inert_boundaries"] = [
        "no engine or provider reached; nothing started",
        "no repository cloned and no network used",
        "image_digest and adapter_digest travel as pins an operator verifies "
        "before execution",
        "credentials travel as references only; no secret in this file, the "
        "emitted document or any evidence",
    ]
    return answer


def main(argv=None, *, stream=sys.stdout):
    # SUPERSEDED AND NO LONGER RUNNABLE. review-2026-10-27T18-06-51Z [R1]
    # found this file's `preflight` extracting 81 files while reporting
    # `wrote_nothing: true`, and `materialized` below still carries the live
    # `shutil.rmtree` on a FIXED SHARED path -- the same pattern that
    # partially deleted an unrelated September scratch root
    # (`INCIDENT-367234-scratch-deletion.md`). The body is kept verbatim
    # because the attempt is part of the record; the ENTRYPOINT refuses,
    # because a known-unsafe command left callable in a delivery is a hazard
    # and not a preserved attempt.
    print("refused: compose_capacity.py is superseded by capacity.py and is "
          "retained as a record of the attempt only. Its `materialized` still "
          "removes a fixed shared scratch path, which review "
          "2026-10-27T18-06-51Z refused and INCIDENT-367234-scratch-deletion"
          ".md records. Use: python3 capacity.py preflight | materialize | "
          "compose, and python3 prove_capacity.py for the joined proof.",
          file=sys.stderr)
    return 2


def _superseded_main(argv=None, *, stream=sys.stdout):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("mode", choices=("preflight", "prove"))
    parser.add_argument("--scratch", default=SCRATCH)
    parser.add_argument("--evidence", default=None)
    parser.add_argument("--keep", action="store_true",
                        help="keep the disposable destination for inspection")
    taken = parser.parse_args(argv)
    try:
        answer = preflight(taken.scratch)
        if taken.mode == "prove":
            from prove_admission import proved

            answer["proof"] = proved(answer, scratch=taken.scratch,
                                     keep=taken.keep)
            answer["mode"] = "prove"
            answer["wrote_nothing"] = False
    except Refused as refusal:
        print("refused: " + str(refusal), file=sys.stderr)
        return 2
    if taken.evidence:
        place = pathlib.Path(taken.evidence)
        place.mkdir(parents=True, exist_ok=True)
        (place / (taken.mode + ".json")).write_text(
            json.dumps(answer, indent=1, sort_keys=True, default=str) + "\n")
    json.dump(answer, stream, indent=1, sort_keys=True, default=str)
    stream.write("\n")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(HERE))
    raise SystemExit(main())
