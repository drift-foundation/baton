"""W197661 claim200930 — the acceptance predicate for THIS episode, on the
REAL contracts.

REPLACING instance-200254's verifier, which review200453 found to be a broken
instrument rather than a failing one. It called `status` without `--control` or
`--observe`, so the projection it judged answered `canonical=false` and said so
in its own document while the verifier never looked; and three of its final
predicates named members no contract has -- `episodes[].ended_state` on an
ordinarily completed stage, a `conclude` receipt where receipt acts are `admit`
and `claim`, and `job.status.outcome`, which does not exist. A check that can
never pass is not a finding.

TWO HALVES, AND THE SPLIT IS THE POINT.

  `judge` and everything it calls are PURE FUNCTIONS over documents. They open
  nothing, read no path and reach no deployment, so the predicates can be
  driven by POSITIVE AND NEGATIVE FIXTURES -- a successful shape this accepts
  and broken ones it must refuse -- without a live run. Review
  2026-09-18T06-19-15Z: "Contract-derived verifier and negative cases need not
  wait for successful live fixture."

  `main` is the thin shell that OBSERVES: it reads canonical status through
  the installed command with `--control`, opens the Authority READ-ONLY, seals
  or compares the immutable expected manifest, and writes a FRESH result named
  by this claim. It decides nothing the pure half does not.

FAIL-CLOSED, AND THIS TIME IT IS TRUE. Review 2026-09-18T06-19-15Z corrected a
claim of mine: `compose_lifecycle.policy_pin` only PREDICTS the approval pin,
and nothing executed the comparison. `check_policy_pin` is called here, its
answer is a required check, and a deployment whose configured pin is not the
Authority's current generation is refused before anything is called ready.

WHAT IT DOES NOT DO. It starts nothing, submits nothing, runs no container,
takes no provider turn, opens the Authority for writing and touches no version
control. It never overwrites a previous verification: each run writes its own
`verification-<claim>.json`.
"""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = Path("/home/sl/src/baton")

# THIS EPISODE'S IDENTITIES. Nothing here is inherited from an earlier one, and
# instance-200254's and instance-200000's image digests keep their own
# attribution.
DEST = Path("/home/sl/baton-v12-lifecycle-200564-clean")
AUTHORITY = "af29c003da434c3aa311b5de4a09f2ee"
WORK = "af29c003-W1"
JOB = "w197661-lifecycle"
SUBMISSION = "w197661-lifecycle-200564"
TARGET_BASE = "e486652c4ddebfb696e030b4b867e914248db542"
CANDIDATE_FILE = "w197661-fixture.txt"
CANDIDATE_BYTES = "w197661 deterministic fixture candidate\n"

CONTEXT = HERE / "context"
RECIPE = CONTEXT / "Dockerfile.fixture"
BUILT_DISTRO = HERE / "build/distro/out/distro"

# THE IMMUTABLE EXPECTED MANIFEST. Review 2026-09-18T05-14-53Z [R3]: the old
# verifier measured this episode's COPY inputs and compared them with -- this
# episode. Current-to-current is not provenance. This file is SEALED once, by
# an explicit act, and every later run compares against it; a build whose
# inputs moved afterwards is a failed check rather than a silently accepted
# one.
EXPECTED = HERE / "EXPECTED.json"


def sha_bytes(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def sha_file(place):
    return sha_bytes(Path(place).read_bytes())


def tree_manifest(root):
    """Every entry under one root: files by content, LINKS BY TARGET.

    Review [R3]: the old `tree_digest` skipped every symlink and every path
    containing `__pycache__`, so it did not bind the complete one-folder
    runtime -- a link repointed or a cached module replaced left the digest
    unchanged. A manifest that skips what it cannot hash is a manifest that
    says the skipped thing does not matter.
    """
    root = Path(root)
    held = {}
    for where, directories, names in os.walk(root, followlinks=False):
        directories.sort()
        for name in sorted(names) + sorted(
                one for one in directories
                if os.path.islink(os.path.join(where, one))):
            place = Path(where) / name
            relative = str(place.relative_to(root))
            if place.is_symlink():
                held[relative] = "link:" + os.readlink(place)
            elif place.is_file():
                held[relative] = sha_file(place)
            else:
                held[relative] = "other"
    return held


def manifest_digest(held):
    return sha_bytes(json.dumps(held, sort_keys=True).encode())


def copy_inputs(recipe=RECIPE, context=CONTEXT):
    """Every byte the image was built from, by the recipe's own COPY list."""
    if not Path(recipe).is_file():
        return None
    copied = [line.split()[1] for line in Path(recipe).read_text().splitlines()
              if line.startswith("COPY")]
    held = {}
    for one in copied:
        place = Path(context) / one
        if place.is_file():
            held[one] = sha_file(place)
        elif place.is_dir():
            held[one] = manifest_digest(tree_manifest(place))
        else:
            held[one] = "absent"
    return held


# -- the pure half -----------------------------------------------------------


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

    def bound(self, what, found, wanted, kind="text"):
        """Equal, both there, AND both the shape their kind promises.

        Review 2026-09-18T06-41-32Z [R1]: two absences compared equal, so
        emptying both sides passed every check. Review 2026-09-18T07-01-24Z
        [R1]: presence alone still accepted `False` on both sides -- a
        comparison of two well-typed-looking nothings is the same defect
        wearing a scalar.
        """
        held = _well_formed(found, kind) and _well_formed(wanted, kind)
        return self.check(what, held and found == wanted,
                          {"found": found, "wanted": wanted,
                           "well_formed": held, "kind": kind})

    def binding(self, what, found, wanted, kind="identity"):
        """A REQUIRED two-sided reference, with no optional-operand escape.

        Review 2026-09-18T07-01-24Z [R1]: `named` treated `wanted=None` as
        "no binding requested", so REMOVING the verdict's `checkpoint_id` --
        the very identity the check exists to bind -- turned the check off and
        reported a pass. A required reference has two sides by definition;
        a missing counterpart is the failure, not an exemption.
        """
        return self.bound(what, found, wanted, kind)

    def present(self, what, found, kind="identity"):
        """One required value whose contract is that it EXISTS and is shaped.

        Used only where there is genuinely no counterpart to bind against.
        """
        return self.check(what, _well_formed(found, kind),
                          {"found": found, "kind": kind})

    @property
    def failed(self):
        return [one["check"] for one in self.held if not one["held"]]


# WHAT EACH REQUIRED VALUE HAS TO LOOK LIKE. Review 2026-09-18T07-01-24Z [R1]:
# `_present` accepted every non-container scalar, so setting all five
# provenance members to `False` on BOTH sides passed every check -- presence is
# not validation, and the docstring claiming "well-formed" was describing an
# intention. Each kind is checked for the shape its own contract states.
_DIGEST = re.compile(r"\Asha256:[0-9a-f]{64}\Z")
_IDENTITY = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._:%/-]{1,255}\Z")


def _well_formed(value, kind="text"):
    """Whether a required value is there AND is the shape its kind promises.

    `identity` an unpadded printable name, `digest` this campaign's own
    prefixed sha256, `document` a non-empty mapping, `manifest` a non-empty
    mapping of names to digests or nested manifests, `text` any non-empty
    string. A boolean is never any of them, which is the probe that found this.
    """
    if isinstance(value, bool) or value is None:
        return False
    if kind == "identity":
        return type(value) is str and _IDENTITY.match(value) is not None
    if kind == "digest":
        return type(value) is str and _DIGEST.match(value) is not None
    if kind in ("document", "manifest"):
        if type(value) is not dict or not value:
            return False
        if kind == "manifest":
            return all(type(name) is str and name
                       and (_well_formed(held, "digest")
                            or _well_formed(held, "manifest"))
                       for name, held in value.items())
        return True
    if kind == "list":
        return type(value) is list and len(value) > 0
    return type(value) is str and value != ""


def _present(value):
    """The older, weaker question, kept only where any non-empty value will do.

    Every REQUIRED identity, digest and manifest goes through `_well_formed`
    now; this remains for values whose contract is only "something is here".
    """
    if isinstance(value, bool) or value is None:
        return False
    if isinstance(value, (str, bytes, dict, list, tuple, set)):
        return len(value) > 0
    return True


def _stages(job):
    return {one.get("kind"): one for one in (job or {}).get("stages", [])}


def judge(observed):
    """Every predicate, over documents this function did not fetch.

    `observed` is a closed dictionary of what the shell read:

      status      the Job projection, as the installed command answered it
      expected    the sealed manifest, or None when nothing is sealed yet
      measured    this run's own measurement of the same things
      authority   {"policy_generation", "canonical_target", "work_present"}
      pin         {"configured_pin", "authority_generation", "equal"}
      line        {"candidate", "custody"} read from the materialized line
      records     the accepted verdict, checkpoint, result and terminal

    EVERY MEMBER IS REQUIRED, and a missing one is a FAILED check rather than
    a skipped one: the shell reports what it could not read, and this refuses
    to call an unread thing acceptable.
    """
    checks = Checks()
    status = observed.get("status") or {}

    # -- the projection is CANONICAL, which is the defect this replaces ------
    checks.check("the status projection is CANONICAL",
                 status.get("canonical") is True,
                 {"canonical": status.get("canonical"),
                  "why": "an unobserved projection answers canonical=false and "
                         "says nothing about where a run stopped"})

    job = None
    for one in status.get("jobs", []):
        if one.get("job_id") == JOB:
            job = one
    checks.check("the projection names this Job", job is not None, JOB)
    checks.bound("it is the submission this episode recorded",
                 (job or {}).get("submission_id"), SUBMISSION, "identity")
    checks.bound("its terminal policy is report-and-hold",
                 (job or {}).get("terminal_policy"), "report-and-hold")

    stages = _stages(job)
    checks.same("it has the three stages", sorted(stages),
                ["implementation", "integration", "review"])
    for kind in ("implementation", "review", "integration"):
        checks.bound(f"the {kind} stage COMPLETED",
                     (stages.get(kind) or {}).get("state"), "completed")
        checks.present(f"the {kind} stage names an attempt",
                       (stages.get(kind) or {}).get("attempt_id"))

    # -- the real records, and not three members no contract has -------------
    records = observed.get("records") or {}
    verdict = records.get("verdict") or {}
    checkpoint = records.get("checkpoint") or {}
    result = records.get("result") or {}
    terminal = records.get("terminal") or {}
    # AN UNREAD RECORD IS NOT A MISSING ONE, and neither is acceptable -- but
    # they are different failures and an operator looks in different places
    # for them. Review [R4]: "distinguish missing records from
    # unread/unimplemented ones" and "do not conflate the unimplemented reader
    # with a lifecycle refusal".
    for name, held in (("verdict", verdict), ("checkpoint", checkpoint),
                       ("result", result), ("terminal", terminal)):
        checks.check(f"the {name} record was READ",
                     _present(held) and "unread" not in held,
                     held.get("unread") if isinstance(held, dict) else held)
    checks.bound("a review verdict was ACCEPTED",
                 verdict.get("disposition"), "accepted")
    checks.binding("the accepted verdict names this episode's review "
                   "attempt", verdict.get("attempt_id"),
                   (stages.get("review") or {}).get("attempt_id"))
    checks.bound("the verdict names this Work",
                 verdict.get("work_id"), WORK, "identity")
    checks.present("an integration CHECKPOINT was accepted",
                   checkpoint.get("checkpoint_id"))
    checks.binding("the accepted checkpoint is the one the verdict names",
                   checkpoint.get("checkpoint_id"),
                   verdict.get("checkpoint_id"))
    checks.bound("the checkpoint records the declared base",
                 (checkpoint.get("evidence") or {}).get("base"), TARGET_BASE,
                 "identity")
    checks.bound("the checkpoint holds the candidate path",
                 (checkpoint.get("evidence") or {}).get("paths"),
                 [CANDIDATE_FILE], "list")
    checks.bound("the producer's frozen RESULT is completed",
                 result.get("disposition"), "completed")
    checks.bound("the frozen result names this Work",
                 ((result.get("assignment_ref") or {}).get("work_ref") or {})
                 .get("work_id"), WORK, "identity")
    checks.binding("the frozen result is THIS implementation attempt's",
                   result.get("attempt_id"),
                   (stages.get("implementation") or {}).get("attempt_id"))
    # THE TERMINAL, FROM THE CONTRACT AND NOT FROM A SPELLING. Review
    # 2026-09-18T07-01-24Z: I asserted `state == "held"` and called it proof of
    # a successful report-and-hold. `tools/stage_execution.managed_account`
    # says otherwise -- it writes `held` for a HELD QUEUE ENTRY or an ending
    # that was not `answered`, `answered` for an imported and settled
    # execution, and `completed` only once the integration receipt is there.
    # So `held` is a HOLD, which is the opposite of what I read it as, and the
    # name of the Job's terminal POLICY is not a state its integration reaches.
    checks.bound("the integration account reached its COMPLETED state",
                 terminal.get("state"), "completed", "text")
    checks.check("and `held` is not mistaken for that",
                 terminal.get("state") != "held",
                 {"state": terminal.get("state"),
                  "why": "managed_account writes held for a held queue entry "
                         "or an ending that was not answered; it is a hold "
                         "rather than a successful terminal"})

    # -- the candidate, proved from the line the manager materialized --------
    line = observed.get("line") or {}
    checks.bound("the candidate file carries exactly the declared bytes",
                 line.get("candidate"), CANDIDATE_BYTES)
    # THE ATTEMPT IS BOUND, NOT COUNTED. Review [R3]: the old verifier asserted
    # `len(attempts) == 1` and never compared the identity, so any one attempt
    # satisfied it.
    checks.binding("custody holds THIS implementation attempt",
                   line.get("custody"),
                   (stages.get("implementation") or {}).get("attempt_id"))

    # -- the Authority, read-only --------------------------------------------
    authority = observed.get("authority") or {}
    checks.bound("the canonical target was ESTABLISHED from the declared "
                 "base", authority.get("canonical_target"), TARGET_BASE,
                 "identity")
    checks.check("the Job's Work exists on this Authority",
                 authority.get("work_present") is True, WORK)

    # -- the approval pin, MEASURED against the Authority ---------------------
    pin = observed.get("pin") or {}
    checks.check("the configured approval pin EQUALS the Authority's "
                 "generation", pin.get("equal") is True,
                 {"configured_pin": pin.get("configured_pin"),
                  "authority_generation": pin.get("authority_generation"),
                  "why": "integration.driver._accepted_receipts refuses unless "
                         "these are equal, and a deployment that cannot "
                         "satisfy its own pin defers at its integration with "
                         "the reason only in a tick report"})

    # -- provenance, against an IMMUTABLE expectation -------------------------
    expected, measured = observed.get("expected"), observed.get("measured") or {}
    checks.check("an immutable expected manifest is SEALED",
                 bool(expected), EXPECTED.name)
    for name, kind in (("image", "identity"), ("image_inputs", "manifest"),
                       ("built_runtime", "digest"),
                       ("installed_runtime", "digest"),
                       ("configuration", "digest")):
        checks.bound(f"the {name} matches the sealed expectation",
                     measured.get(name), (expected or {}).get(name), kind)
    return checks


# -- the observing half ------------------------------------------------------


def read_status(run=None):
    """The Job projection, through the INSTALLED command, WITH the control
    store -- which is the whole of review200453's R1."""
    runner = run or (lambda argv: subprocess.run(
        argv, capture_output=True, text=True, timeout=180))
    found = runner([str(DEST / "distro/baton-v12-stack"), "manager",
                    "--store", str(DEST / "db/jobs.sqlite3"),
                    "--incarnation", "c200930-verify",
                    "--authority-uuid", AUTHORITY, "status",
                    "--control", str(DEST / "db/control.sqlite3")])
    if found.returncode != 0:
        return None
    try:
        return json.loads(found.stdout)
    except ValueError:
        return None


def read_authority():
    """Policy generation, canonical target and the Work, READ-ONLY.

    `Authority.open_readonly` exists for exactly this: `open` takes a write
    lock, applies the schema and sets a persistent journal mode, which is
    right for a serving deployment and wrong for a verifier. The old one used
    `open` while its docstring called itself read-only.
    """
    sys.path.insert(0, str(REPO / "v12/python"))
    sys.path.insert(0, str(REPO / "v12/python/src"))
    from baton_v12.authority import Authority

    authority = Authority.open_readonly(str(DEST / "db/authority.sqlite3"),
                                        expected_authority_uuid=AUTHORITY)
    try:
        return {"policy_generation": authority.policy_generation(),
                "canonical_target": authority.canonical_target(),
                "work_present": authority.project_work(WORK) is not None}
    finally:
        dispose = getattr(authority, "dispose", None)
        if dispose is not None:
            dispose()


def read_line():
    """The candidate bytes and the ONE custody attempt, from the line."""
    lines = DEST / "storage/.baton-review-lines"
    if not lines.is_dir():
        return {}
    held = sorted(os.listdir(lines))
    if len(held) != 1:
        return {"candidate": None, "custody": None, "lines": held}
    line = lines / held[0]
    candidate = line / "checkout" / CANDIDATE_FILE
    custody = line / "custody"
    attempts = sorted(os.listdir(custody)) if custody.is_dir() else []
    return {"candidate": candidate.read_text() if candidate.is_file() else None,
            "custody": attempts[0] if len(attempts) == 1 else None}


def measure():
    """This run's own measurement of everything the seal pins."""
    iid = HERE / "build/fixture.iid"
    configured = DEST / "deployment.json"
    return {
        "image": iid.read_text().strip() if iid.is_file() else None,
        "image_inputs": copy_inputs(),
        "built_runtime": manifest_digest(tree_manifest(BUILT_DISTRO))
        if BUILT_DISTRO.is_dir() else None,
        "installed_runtime": manifest_digest(tree_manifest(DEST / "distro"))
        if (DEST / "distro").is_dir() else None,
        "configuration": sha_file(configured) if configured.is_file() else None,
    }


def main(argv=None, run=None):
    parser = argparse.ArgumentParser(prog="verify_lifecycle")
    parser.add_argument("--seal", action="store_true",
                        help="write EXPECTED.json from this measurement; "
                             "refused when one already exists, because an "
                             "expectation a failing run may rewrite is not one")
    # NO DEFAULT THAT CAN COLLIDE SILENTLY. A reusable name plus an
    # overwriting write is how the previous run's evidence disappeared.
    parser.add_argument("--claim", required=True,
                        help="this run's own identity; the result is created "
                             "exclusively under it and a collision is refused")
    # SYS.ARGV WHEN NOBODY PASSED ONE. The first form of this parsed an
    # EMPTY list on `argv is None`, so `--seal` typed at a terminal was
    # silently dropped and the seal step ran a verification instead.
    taken = parser.parse_args(sys.argv[1:] if argv is None else argv)

    measured = measure()
    if taken.seal:
        if EXPECTED.is_file():
            print("refused: an expectation is already sealed; a verifier that "
                  "reseals is a verifier that always passes", file=sys.stderr)
            return 2
        EXPECTED.write_text(json.dumps(measured, indent=2, sort_keys=True)
                            + "\n")
        print(json.dumps({"sealed": str(EXPECTED)}, indent=1))
        return 0

    sys.path.insert(0, str(HERE))
    import compose_lifecycle

    observed = {
        "status": read_status(run=run),
        "expected": json.loads(EXPECTED.read_text())
        if EXPECTED.is_file() else None,
        "measured": measured,
        "authority": read_authority(),
        "pin": compose_lifecycle.check_policy_pin(),
        "line": read_line(),
        "records": read_records(),
    }
    checks = judge(observed)
    found = {"schema": "baton.w197661.verification/2", "claim": taken.claim,
             "destination": str(DEST), "authority_uuid": AUTHORITY,
             "work_id": WORK, "job_id": JOB, "submission_id": SUBMISSION,
             "measured": measured, "pin": observed["pin"],
             "checks": checks.held, "failed": checks.failed,
             "accepted": not checks.failed}
    # A FRESH RESULT EVERY TIME, AND THE FILESYSTEM ENFORCES IT. Review
    # 2026-09-18T06-41-32Z [R3]: this used `write_text` with a reusable
    # default claim, so a second run REPLACED the evidence of the first and
    # returned zero -- "do not overwrite" written as a comment rather than as
    # a rule. `O_EXCL` is the rule; a collision is refused and the previous
    # bytes are untouched.
    place = HERE / f"verification-{taken.claim}.json"
    try:
        handle = os.open(place, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        print(f"refused: {place.name} already exists; a verification that "
              f"overwrites the previous one destroys the evidence somebody "
              f"would compare against. Name this run with --claim.",
              file=sys.stderr)
        return 2
    with os.fdopen(handle, "w") as writing:
        writing.write(json.dumps(found, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"accepted": found["accepted"],
                      "failed": found["failed"],
                      "checks": len(checks.held)}, indent=1))
    if checks.failed:
        print("NOT ACCEPTED: a required check did not hold; this run is NOT a "
              "completed lifecycle", file=sys.stderr)
        return 1
    return 0


def read_records(control=None, line_id=None, implementation_attempt=None):
    """The accepted verdict, checkpoint, frozen result and terminal, READ.

    Review 2026-09-18T06-41-32Z [R4], and the correction is mine: this was an
    unconditional stub that asserted "this episode has no accepted verdict or
    checkpoint yet". THAT WAS WRONG, and the reviewer said exactly why -- the
    retained episode's implementation and review both COMPLETED, so those
    records exist and I confused an unimplemented reader with a lifecycle
    refusal. Reading them proves it: the line is `accepted`, the verdict's
    disposition is `accepted`, and the checkpoint names the candidate path.

    READ-ONLY, THROUGH THE OWNING CONTRACTS. `ControlStore.open_readonly`
    opens the store `mode=ro`, and every record comes from its own module's
    public reader -- `review_cycles.integration_checkpoint`,
    `review_cycles.verdict_of`, `output.frozen_output_of` -- rather than from
    a shape this file invents.

    AND WHAT IT CANNOT READ, IT SAYS. The report-and-hold terminal is the
    integration stage OBSERVATION's own `state`, and that document is produced
    by the deployment's own reader in `tools.stage_execution`, which composes
    an Authority, sessions and worker preflights -- not a read-only path a
    verifier may take. So the terminal answers `unread` WITH ITS REASON, and
    `judge` fails that separately from a record that is merely missing. An
    honest gap named at its own boundary is not the same defect as a stub
    that asserted a fact about the lifecycle.
    """
    sys.path.insert(0, str(REPO / "v12/python"))
    sys.path.insert(0, str(REPO / "v12/python/src"))
    from baton_v12.worker_manager import ControlStore, review_cycles
    from baton_v12.worker_manager import output as output_records

    found = {"verdict": {"unread": "the control store was not opened"},
             "checkpoint": {"unread": "the control store was not opened"},
             "result": {"unread": "the control store was not opened"},
             "terminal": {
                 "unread": "the integration account's own state is produced by "
                           "tools.stage_execution.managed_account, which "
                           "composes an Authority, sessions and worker "
                           "preflights and is not a read-only path this "
                           "verifier may take; its vocabulary is held for a "
                           "held queue entry or an unanswered ending, "
                           "answered for an imported settled execution, and "
                           "completed once the integration receipt exists"}}
    if line_id is None:
        line_id = _one_line()
    if line_id is None:
        for name in ("verdict", "checkpoint", "result"):
            found[name] = {"unread": "this destination holds no single "
                                     "review line to read records from"}
        return found
    opened = control or ControlStore.open_readonly(
        str(DEST / "db/control.sqlite3"), incarnation="c201089-verify",
        clock=lambda: "2026-09-18T00:00:00.000Z")
    try:
        accepted = review_cycles.integration_checkpoint(opened, line_id)
        if accepted is None:
            found["checkpoint"] = {"missing": "this line has no accepted "
                                              "integration checkpoint"}
            found["verdict"] = {"missing": "no accepted checkpoint names a "
                                           "verdict on this line"}
        else:
            found["checkpoint"] = {
                "checkpoint_id": accepted.get("checkpoint_id"),
                "evidence": accepted.get("evidence") or {}}
            verdict_id = accepted.get("verdict_id")
            held = (review_cycles.verdict_of(opened, verdict_id)
                    if verdict_id else None)
            if held is None:
                found["verdict"] = {"missing": "the accepted checkpoint names "
                                               "no readable verdict"}
            else:
                # THE REVIEWING ATTEMPT IS THE ATTACHMENT'S, not a member the
                # verdict carries: the verdict names its attachment and the
                # attachment is what a reviewing attempt produced.
                found["verdict"] = {
                    "verdict_id": held.get("verdict_id"),
                    "disposition": held.get("disposition"),
                    "checkpoint_id": held.get("checkpoint_id"),
                    "work_id": held.get("work_id"),
                    "attempt_id": _reviewing_attempt(opened, held)}
        if implementation_attempt is None:
            implementation_attempt = _custody_attempt(line_id)
        if implementation_attempt is None:
            found["result"] = {"missing": "no single implementation attempt "
                                          "holds custody on this line"}
        else:
            frozen = output_records.frozen_output_of(opened,
                                                     implementation_attempt)
            found["result"] = ({"missing": "this implementation attempt has "
                                           "no frozen result"}
                               if frozen is None else
                               {"attempt_id": implementation_attempt,
                                "disposition": frozen.get("disposition"),
                                "result_id": frozen.get("result_id"),
                                "manifest_digest": frozen.get(
                                    "manifest_digest"),
                                # THE ASSIGNMENT LIVES IN THE RETAINED RESULT
                                # MANIFEST, not on the frozen row -- which
                                # answers `assignment_ref: null` and had this
                                # predicate failing over my reader rather than
                                # over the run. `load_manifest` is the owner.
                                "assignment_ref": _result_assignment(
                                    opened, frozen.get("manifest_digest"))})
    finally:
        if control is None:
            close = getattr(opened, "close", None)
            if close is not None:
                close()
    return found


def _one_line():
    """The one review line this destination materialized, or None."""
    lines = DEST / "storage/.baton-review-lines"
    if not lines.is_dir():
        return None
    held = sorted(os.listdir(lines))
    return held[0] if len(held) == 1 else None


def _custody_attempt(line_id):
    """The one attempt holding custody on that line, or None."""
    custody = DEST / "storage/.baton-review-lines" / line_id / "custody"
    held = sorted(os.listdir(custody)) if custody.is_dir() else []
    return held[0] if len(held) == 1 else None


def _result_assignment(control, manifest_digest):
    """The assignment a frozen result names, from its RETAINED MANIFEST."""
    from baton_v12.worker_manager.manifests import load_manifest

    if not manifest_digest:
        return None
    try:
        held = load_manifest(control, manifest_digest, "resultManifest")
    except Exception:                                      # noqa: BLE001
        return None
    return (held or {}).get("assignment_ref")


def _reviewing_attempt(control, verdict):
    """The attempt whose review produced this verdict, through its owner.

    The verdict names its ATTACHMENT; the attachment is the record a reviewing
    attempt made. Answered as `None` when this build's reader cannot resolve
    it, which `judge` treats as a missing identity rather than a match.
    """
    from baton_v12.worker_manager import review_cycles

    try:
        held = review_cycles.review_of(control, verdict.get("attachment_id"))
    except Exception:                                      # noqa: BLE001
        return None
    # `runtime_attempt_id` IS THE MEMBER ITS OWNER ANSWERS WITH, and reading
    # `attempt_id` -- which this file guessed at first -- answered None for a
    # record that carries the identity perfectly well.
    return (held or {}).get("runtime_attempt_id")


if __name__ == "__main__":
    sys.exit(main())
