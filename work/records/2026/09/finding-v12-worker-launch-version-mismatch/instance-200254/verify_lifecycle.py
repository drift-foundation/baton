"""W197661 claim200254 — the acceptance predicate for THIS episode's run.

REPLACING instance-200000's verifier, which review200179 [R3] found still
naming `lifecycle-198943` and `attempt-432eb7b7` -- identities from an episode
two runs earlier. A verifier that checks a deployment nobody ran is not
evidence, and `lifecycle.json` was an observation summary rather than a
predicate: it recorded what was seen and asserted nothing.

FAIL-CLOSED AND IDENTITY-BOUND. Every identity below is pinned to the exact
installed destination, Authority, Job, submission, attempts, image and runtime
this claim produced. A missing file, a mismatched digest or an unreached stage
is a FAILED check, never a skipped one, and `main` returns non-zero the moment
any required check does not hold -- so no later reader can take a zero here as
acceptance of something that did not happen.

WHAT IT DOES NOT DO. It starts nothing, submits nothing, runs no container and
touches no version control. It reads the deployment's own state and the
repository's own bytes.

JOB AND SUBMISSION ARE DIFFERENT THINGS and are never interchanged: the Job is
`w197661-lifecycle` and the submission that recorded it is
`w197661-lifecycle-200254`.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = Path("/home/sl/src/baton")

# THIS EPISODE'S OWN IDENTITIES, and nothing here is inherited from an earlier
# one. instance-199877's and instance-200000's image digests keep their own
# attribution and are not reassigned to this build.
DEST = Path("/home/sl/baton-v12-lifecycle-200254")
AUTHORITY = "b6157ee13ec54abbb458d2d2f0a7becb"
WORK = "b6157ee1-W1"
JOB = "w197661-lifecycle"
SUBMISSION = "w197661-lifecycle-200254"
TARGET_BASE = "e486652c4ddebfb696e030b4b867e914248db542"
CANDIDATE_FILE = "w197661-fixture.txt"
CANDIDATE_BYTES = "w197661 deterministic fixture candidate\n"

# EVERY COPY INPUT THE IMAGE WAS BUILT FROM, measured rather than named. The
# recipe is read for the list so a COPY added without a measurement here is a
# failed check rather than an unnoticed one.
CONTEXT = HERE / "context"
RECIPE = CONTEXT / "Dockerfile.fixture"

# THE COMPLETE REPLACEMENT RUNTIME this episode built and installed. The
# earlier 81-file manifest belongs to an earlier build and is not evidence for
# this one, so both the built distro and the installed copy are measured here.
BUILT_DISTRO = HERE / "build/distro/out/distro"


def sha_bytes(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def sha_file(place):
    return sha_bytes(Path(place).read_bytes())


def tree_digest(root):
    """Every regular file under one root, by relative path and content."""
    root = Path(root)
    held = {}
    for where, _, names in os.walk(root):
        if "__pycache__" in where:
            continue
        for name in sorted(names):
            place = Path(where) / name
            if place.is_symlink() or not place.is_file():
                continue
            held[str(place.relative_to(root))] = sha_file(place)
    return held


class Checks:
    """Every answer, recorded whether it held or not."""

    def __init__(self):
        self.held = []

    def check(self, what, answer, detail=None):
        self.held.append({"check": what, "held": bool(answer),
                          "detail": detail})
        return bool(answer)

    def same(self, what, found, wanted):
        return self.check(what, found == wanted,
                          {"found": found, "wanted": wanted})

    @property
    def failed(self):
        return [one["check"] for one in self.held if not one["held"]]


def status(run=None):
    """The Job projection, read through the INSTALLED command."""
    runner = run or (lambda argv: subprocess.run(
        argv, capture_output=True, text=True, timeout=180))
    found = runner([str(DEST / "distro/baton-v12-stack"), "manager",
                    "--store", str(DEST / "db/jobs.sqlite3"),
                    "--incarnation", "c200254-verify",
                    "--authority-uuid", AUTHORITY, "status"])
    if found.returncode != 0:
        return None
    try:
        return json.loads(found.stdout)
    except ValueError:
        return None


def review_line():
    """The one review line this run materialized, or None."""
    lines = DEST / "storage/.baton-review-lines"
    if not lines.is_dir():
        return None
    held = sorted(one for one in os.listdir(lines))
    return (lines / held[0]) if len(held) == 1 else None


def main(run=None):
    checks = Checks()

    # -- the installation, and it is THIS episode's ------------------------
    checks.check("the installed destination exists", DEST.is_dir(),
                 str(DEST))
    identity = DEST / "authority-identity.json"
    checks.check("the Authority identity is this episode's",
                 identity.is_file()
                 and json.loads(identity.read_text()).get(
                     "authority_uuid") == AUTHORITY, AUTHORITY)

    # -- the runtime: BOTH the built distro and the installed copy ---------
    built = tree_digest(BUILT_DISTRO) if BUILT_DISTRO.is_dir() else {}
    installed = tree_digest(DEST / "distro") if (DEST / "distro").is_dir() \
        else {}
    checks.check("this episode BUILT a complete runtime", bool(built),
                 {"files": len(built)})
    checks.same("the installed runtime is that exact build",
                sha_bytes(json.dumps(installed, sort_keys=True).encode()),
                sha_bytes(json.dumps(built, sort_keys=True).encode()))

    # -- the image, and every byte it was built from -----------------------
    iid = HERE / "build/fixture.iid"
    image = iid.read_text().strip() if iid.is_file() else None
    checks.check("this episode built its own fixture image", bool(image),
                 image)
    copied = [line.split()[1] for line in RECIPE.read_text().splitlines()
              if line.startswith("COPY")] if RECIPE.is_file() else []
    inputs = {}
    for one in copied:
        place = CONTEXT / one
        if place.is_file():
            inputs[one] = sha_file(place)
        elif place.is_dir():
            inputs[one] = tree_digest(place)
        else:
            checks.check("the recipe's COPY input " + one + " exists", False)
    checks.check("every COPY input is measured",
                 len(inputs) == len(copied) and bool(copied), sorted(inputs))
    checks.check("the recipe selects THIS episode's entrypoint",
                 RECIPE.is_file() and
                 'ENTRYPOINT ["python3", "/opt/baton/proposing_entry.py"]'
                 in RECIPE.read_text())
    checks.check("the image carries no second agent to fall back to",
                 not any("scripted_agent" in one for one in copied), copied)

    # -- the configuration this run was composed from ----------------------
    for name in ("bootstrap_inputs.json", "submission.json", "task.json",
                 "stage_execution.json", "policies.json", "runtime_profile.json",
                 "toolchain.json", "composition.json"):
        checks.check("the composed " + name + " is retained",
                     (HERE / name).is_file())
    composed = json.loads((HERE / "composition.json").read_text()) \
        if (HERE / "composition.json").is_file() else {}
    checks.check("the composition reported complete",
                 composed.get("complete") is True)
    checks.same("the composition pinned this episode's image",
                composed.get("image_in_engine", {}).get("reported_id"), image)

    # -- the Authority's canonical target ----------------------------------
    sys.path.insert(0, str(REPO / "v12/python"))
    sys.path.insert(0, str(REPO / "v12/python/src"))
    from baton_v12.authority import Authority

    authority = Authority.open(str(DEST / "db/authority.sqlite3"),
                               expected_authority_uuid=AUTHORITY)
    try:
        checks.same("the canonical target was ESTABLISHED from the declared "
                    "base", authority.canonical_target(), TARGET_BASE)
        checks.check("the Job's Work exists on this Authority",
                     authority.project_work(WORK) is not None, WORK)
    finally:
        authority.dispose()

    # -- the Job, its submission and its three stages ----------------------
    projection = status(run=run)
    checks.check("the installed command answers a status projection",
                 projection is not None)
    job = None
    for one in (projection or {}).get("jobs", []):
        if one.get("job_id") == JOB:
            job = one
    checks.check("the projection names this Job", job is not None, JOB)
    if job is not None:
        checks.same("it is the submission this episode recorded",
                    job.get("submission_id"), SUBMISSION)
        checks.same("its terminal policy is report-and-hold",
                    job.get("terminal_policy"), "report-and-hold")
        stages = {one["kind"]: one for one in job.get("stages", [])}
        checks.same("it has the three stages", sorted(stages),
                    ["implementation", "integration", "review"])

    # -- CANDIDATE PUBLICATION, proved from the line the manager made ------
    line = review_line()
    checks.check("exactly one review line was materialized",
                 line is not None, str(line) if line else None)
    if line is not None:
        candidate = line / "checkout" / CANDIDATE_FILE
        checks.check("the candidate file is on that line", candidate.is_file())
        checks.same("with exactly the declared bytes",
                    candidate.read_text() if candidate.is_file() else None,
                    CANDIDATE_BYTES)
        custody = line / "custody"
        attempts = sorted(os.listdir(custody)) if custody.is_dir() else []
        checks.same("one implementation attempt took custody",
                    len(attempts), 1)
        if attempts:
            held = custody / attempts[0]
            checks.same("the declared proposal tree is present",
                        sorted(os.listdir(held / "proposal"))
                        if (held / "proposal").is_dir() else None,
                        ["objects.bundle", "patch.diff", "result.json",
                         "verification.txt"])
            sealed = held / "sealed.json"
            checks.check("the output is SEALED", sealed.is_file())
            if sealed.is_file():
                found = json.loads(sealed.read_text())
                checks.same("the seal names this Work",
                            found.get("assignment_ref", {})
                            .get("work_ref", {}).get("work_id"), WORK)
                checks.same("its disposition is completed",
                            found.get("disposition"), "completed")

    # -- INDEPENDENT REVIEW AND REPORT-AND-HOLD ----------------------------
    #
    # ASSERTED, NOT SUMMARIZED. These are the two outcomes this Work's
    # lifecycle exercise exists to reach, so they are required checks: an
    # unreached stage FAILS here rather than being reported as an observation.
    reviewed = stages.get("review") if job is not None else None
    checks.check("the review stage reached an ending",
                 bool(reviewed) and any(
                     one.get("ended_state")
                     for one in reviewed.get("episodes", [])),
                 (reviewed or {}).get("state"))
    checks.check("a review verdict was accepted",
                 bool(reviewed) and any(
                     one["act"] == "conclude" and one["state"] == "performed"
                     for one in (reviewed or {}).get("receipts", [])),
                 [one["act"] for one in (reviewed or {}).get("receipts", [])])
    checks.check("the Job reached its report-and-hold terminal",
                 bool(job) and job.get("outcome") is not None,
                 (job or {}).get("outcome"))

    found = {"schema": "baton.w197661.verification/1", "claim": 200254,
             "destination": str(DEST), "authority_uuid": AUTHORITY,
             "work_id": WORK, "job_id": JOB, "submission_id": SUBMISSION,
             "image": image, "image_inputs": inputs,
             "built_runtime_files": len(built),
             "installed_runtime_files": len(installed),
             "checks": checks.held, "failed": checks.failed,
             "accepted": not checks.failed}
    (HERE / "verification.json").write_text(
        json.dumps(found, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"accepted": found["accepted"],
                      "failed": found["failed"],
                      "checks": len(checks.held)}, indent=1))
    if checks.failed:
        print("NOT ACCEPTED: a required check did not hold; this run is NOT "
              "a completed lifecycle", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
