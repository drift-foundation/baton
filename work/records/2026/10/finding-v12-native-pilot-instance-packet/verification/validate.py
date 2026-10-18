"""W325959 — the packet's own structural verification, through product owners.

This is PREPARATION. Nothing here installs, submits, serves or executes: every
check loads one of `../configuration/*.json` and hands it to the validator that
actually owns that document in the product tree, then records what was accepted
and what was refused.

The point of the refusals is the packet's own contract: "an unresolved
production value stays explicit and non-executable". Each `SELECT:` sentinel
marks a value only the owner can choose and each `READBACK:` sentinel marks one
that does not exist until an earlier step has run. A sentinel is deliberately
not a valid digest, path or identity, so the product's own validators refuse
these documents TODAY — which is what makes the packet reviewable and
non-executable rather than a plausible default waiting to be run by accident.

Harness: the strict classifier from
`baton:work/records/2026/10/finding-v12-pilot-diagnostic-recovery-matrix/matrix-325259/matrix3.py`.
`0-harness-self-check` must fail with its own named `CheckFailed`; a setup or
cleanup error counts unexpected; `main` refuses the run if the self-check did
not fail for its own reason, and a zero exit alone is never acceptance.

Run from `v12/python`:

    PYTHONPATH=src:. python3 <this file> --packet <the dossier> \
        --evidence <directory>
"""
import argparse
import hashlib
import json
import pathlib
import time
import traceback

DESTINATION = "/home/sl/baton-instances/native-coordination-pilot-w321608-1"
BASE = "14e52d80679de5e844f72324df632da5e01cf393"
SENTINELS = ("SELECT: ", "READBACK: ")


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


def sentinels_in(value, path="$"):
    """Every explicitly unresolved value, by its own path in the document."""
    found = []
    if isinstance(value, dict):
        for name, held in sorted(value.items()):
            found += sentinels_in(held, f"{path}.{name}")
    elif isinstance(value, list):
        for index, held in enumerate(value):
            found += sentinels_in(held, f"{path}[{index}]")
    elif isinstance(value, str) and value.startswith(SENTINELS):
        found.append(path)
    return found


def loaded(packet, name):
    place = pathlib.Path(packet) / "configuration" / name
    body = place.read_bytes()
    return json.loads(body), {
        "path": f"configuration/{name}", "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest()}


# -- scenario 0 --------------------------------------------------------------

SELF_CHECK = "the task document carries an unresolved sentinel (INTENTIONALLY FALSE)"


def harness_self_check(packet, checks):
    task, _held = loaded(packet, "task.json")
    found = sentinels_in(task)
    checks.note("the task document's unresolved values", found)
    checks.expect(SELF_CHECK, bool(found), found)
    return {}


# -- scenario 1 --------------------------------------------------------------

def the_task_document_is_immutable_and_owned(packet, checks):
    """The one fully pinned document, validated by the workload's own owner."""
    from tools import dogfood_operator

    task, held = loaded(packet, "task.json")
    checks.expect("the task document carries NO unresolved value",
                  sentinels_in(task) == [], sentinels_in(task))
    owned = dogfood_operator.held_task(task, what="the pilot quickstart task")
    checks.expect("it validates through dogfood_operator.held_task",
                  owned is not None)
    checks.expect("its declared base is the selected source",
                  owned["declared_base"] == BASE, owned["declared_base"])
    checks.expect("its source profile is the git line profile",
                  owned["source_profile"] == "git-line",
                  owned["source_profile"])
    checks.expect("the verification command is one closed argv",
                  isinstance(owned["verification"], list)
                  and owned["verification"][:2] == ["python3", "-c"]
                  and len(owned["verification"]) == 3,
                  owned["verification"][:2])

    # THE CHECK ITSELF IS RUN HERE, against a candidate this packet composes in
    # memory, because a verification argv nobody ever ran is a guess. It is run
    # in a temporary directory; nothing in the repository is touched.
    import os
    import subprocess
    import tempfile

    argv = owned["verification"]
    sections = ["## Supported commands", "## Execution is not acceptance",
                "## Reading a failed attempt",
                "## Cancelling or holding safely"]
    with tempfile.TemporaryDirectory() as root:
        os.makedirs(os.path.join(root, "v12"))
        place = os.path.join(root, "v12", "QUICKSTART.md")

        def ran(body):
            with open(place, "w", encoding="utf-8") as writing:
                writing.write(body)
            answer = subprocess.run(argv, cwd=root, capture_output=True,
                                    text=True, timeout=60)
            return {"status": answer.returncode,
                    "stdout": answer.stdout.strip(),
                    "stderr": answer.stderr.strip()[-200:]}

        # Long enough to clear the check's own 1200-byte floor, which the
        # first cut of this scenario did not manage -- the check caught it.
        filler = ("body text for this section, long enough to be real prose "
                  "rather than a heading with nothing under it, which is "
                  "exactly what the length floor exists to refuse. An "
                  "operator reading this section should learn what to run "
                  "and what the answer means, and a section that cannot "
                  "manage a few sentences has not done that. ")
        complete = "# Quickstart\n\n" + "\n\n".join(
            f"{one}\n\n{filler * 2}" for one in sections)
        accepted = ran(complete)
        checks.expect("the pinned check ACCEPTS a complete quickstart",
                      accepted["status"] == 0, accepted)
        missing = ran(complete.replace(sections[2], "## Something else"))
        checks.expect("it refuses a missing required section",
                      missing["status"] != 0
                      and "missing sections" in missing["stderr"], missing)
        short = ran("# Quickstart\n\n" + "\n\n".join(sections))
        checks.expect("it refuses a quickstart shorter than its own contract",
                      short["status"] != 0 and "shorter" in short["stderr"],
                      short)
        marked = ran(complete + "\n\nTODO: finish this\n")
        checks.expect("and it refuses an unresolved marker",
                      marked["status"] != 0
                      and "unresolved markers" in marked["stderr"], marked)
        empty = subprocess.run(argv, cwd=os.path.join(root, "v12"),
                               capture_output=True, text=True, timeout=60)
        checks.expect("with the file absent it refuses rather than passing",
                      empty.returncode != 0, empty.stderr.strip()[-120:])
        answers = {"accepted": accepted, "missing_section": missing,
                   "too_short": short, "marker": marked,
                   "absent": {"status": empty.returncode,
                              "stderr": empty.stderr.strip()[-120:]}}

    sealed = json.dumps(owned, sort_keys=True).encode("utf-8")
    return {"member": held, "task_id": owned["task_id"],
            "sealed_bytes": len(sealed),
            "sealed_sha256": hashlib.sha256(sealed).hexdigest(),
            "check_behaviour": answers,
            "note": "the sealed digest is over the canonical form "
                    "dogfood_operator._copied_task writes (sorted keys, no "
                    "indentation), which is what the input manifest's human "
                    "contract binds -- not over the pretty-printed file here."}


# -- scenario 2 --------------------------------------------------------------

def the_install_inputs_are_closed_and_refuse_their_sentinels(packet, checks):
    """Pass one, held to bootstrap's own input contract."""
    from tools import bootstrap

    document, held = loaded(packet, "install-inputs.json")
    checks.expect("the schema is this build's bootstrap input schema",
                  document["schema"] == bootstrap.SCHEMA, document["schema"])
    checks.expect("every REQUIRED member is named",
                  [name for name in bootstrap.REQUIRED
                   if document.get(name) in (None, "", [], {})] == [],
                  sorted(document))
    checks.expect("no member this build cannot carry is named",
                  bootstrap._unknown(document) == [],
                  bootstrap._unknown(document))
    checks.expect("the state root is the selected destination, absolute",
                  document["state_root"] == DESTINATION
                  and document["state_root"].startswith("/"),
                  document["state_root"])
    checks.expect("the three receipt actors are named and the review receipt "
                  "actor is NOT the owner",
                  sorted(document["receipt_participants"])
                  == sorted(bootstrap.RECEIPTS)
                  and document["receipt_participants"]["review"]
                  != document["owner_participant"],
                  document["receipt_participants"])
    checks.expect("the owner participant is the selected human",
                  document["owner_participant"] == "baton.slaw",
                  document["owner_participant"])
    checks.expect("the owner is configured for approve, integrate and close "
                  "and for neither verify nor review",
                  bootstrap.OWNER_GRANTS == ("approve", "integrate", "close")
                  and "verify" not in bootstrap.OWNER_GRANTS
                  and "review" not in bootstrap.OWNER_GRANTS,
                  bootstrap.OWNER_GRANTS)
    checks.expect("no worker and no Job is configured by the fresh install, "
                  "which is what bootstrap defers",
                  bootstrap.workers_of(document) == []
                  and bootstrap.jobs_of(document) == [])
    checks.expect("the integration role is OPTIONAL in this build, so a "
                  "two-stage pool is a configured deployment rather than a "
                  "workaround", "integration" in bootstrap.ROLES)

    unresolved = sentinels_in(document)
    checks.expect("the unresolved values are explicit and enumerable",
                  len(unresolved) >= 5, unresolved)

    # WHERE THE GATE ACTUALLY IS, and the first cut of this scenario guessed
    # wrong. `bootstrap.held` owns PRESENCE and RELATIONSHIPS -- every required
    # member named, an absolute state root, the role and Job rules, the
    # independence rule -- and it accepts an opaque string wherever a digest or
    # a generation belongs. So it accepts this document, and saying otherwise
    # would have been this packet claiming a protection it does not have.
    accepted = None
    try:
        bootstrap.held(document)
        accepted = True
    except Exception as caught:                              # noqa: BLE001
        accepted = f"{type(caught).__name__}: {caught}"
    checks.expect("bootstrap.held ACCEPTS it, because it validates presence "
                  "and relationships rather than value formats",
                  accepted is True, accepted)

    # THE GATE IS `bootstrap.validated`, which `prepare` calls before any
    # durable effect: it holds the configuration this input would EMIT to the
    # rules the manager holds it to.
    places = __import__("tools.instance", fromlist=["layout"]).layout(
        DESTINATION)
    would_emit = {
        "schema": bootstrap.MULTI_JOB_SCHEMA,
        "authority_store": places["authority_store"],
        "authority_uuid": "0" * 32,
        "integration_store": places["integration_store"],
        "state_root": places["deployment_state"],
        "pool_generation": 1, "policy_generation": 1,
        "checkpoint_profile": document["checkpoint_profile"],
        "integration_profile": document["integration_profile"],
        "retention_policy_digest": document["retention_policy_digest"],
        "retention_disposition": document["retention_disposition"],
        "receipt_participants": dict(document["receipt_participants"]),
        "workers": [], "job_bindings": []}
    refusal = None
    try:
        bootstrap.validated(would_emit)
    except Exception as caught:                              # noqa: BLE001
        refusal = f"{type(caught).__name__}: {caught}"
    checks.expect("and bootstrap.validated REFUSES the configuration this "
                  "input would emit while the sentinels stand, before any "
                  "durable effect -- which is what makes the packet "
                  "non-executable today",
                  refusal is not None and "sha256 digest" in refusal, refusal)
    return {"member": held, "unresolved": unresolved,
            "held_accepts": accepted,
            "validated_refusal": refusal,
            "finding": "bootstrap.held validates presence and relationships, "
                       "not value formats, so it accepts an opaque string "
                       "where a digest or a generation belongs. The gate "
                       "before any durable effect is bootstrap.validated, "
                       "which holds the EMITTED configuration to the manager's "
                       "own rules; its refusal here names the retention policy "
                       "digest. An earlier cut of this scenario asserted the "
                       "refusal came from `held` and the run said otherwise.",
            "receipt_participants": document["receipt_participants"],
            "owner_participant": document["owner_participant"]}


# -- scenario 3 --------------------------------------------------------------

def the_two_stage_submission_validates(packet, checks):
    """Pass three's submission, held to the Job manager's own validator.

    The stage set is the control W321690 established and the owner selected.
    The identities it cannot know yet are sentinels, so this scenario proves
    the SHAPE on a resolved copy and proves that the authored document itself
    is refused until the owner's and the readback values land.
    """
    import copy

    from baton_v12.job_manager import documents

    document, held = loaded(packet, "submission.json")
    checks.expect("the schema is job-submission/2, which is the only one that "
                  "carries execution_limits",
                  document["schema"] == documents.SUBMISSION_SCHEMA
                  and documents.SUBMISSION_LIMITS_SCHEMAS
                  == (documents.SUBMISSION_SCHEMA,), document["schema"])
    job = document["jobs"][0]
    kinds = [one["kind"] for one in job["stages"]]
    checks.expect("the Job declares implementation and review ONLY",
                  kinds == ["implementation", "review"], kinds)
    checks.expect("so no integration stage exists for a serving manager to "
                  "admit", "integration" not in kinds, kinds)
    checks.expect("the review stage depends on the implementation stage of "
                  "this Job",
                  job["stages"][1]["depends_on"]
                  == [{"job_id": job["job_id"], "kind": "implementation"}],
                  job["stages"][1]["depends_on"])
    checks.expect("the selected provider turn and verification ceilings are "
                  "carried by the Job",
                  job["execution_limits"]
                  == {"provider_turn_seconds": 3600,
                      "verification_command_seconds": 900},
                  job["execution_limits"])
    checks.expect("the terminal policy is this build's only one",
                  job["terminal_policy"] == "report-and-hold",
                  job["terminal_policy"])
    checks.expect("the test scope names the artifact this Work authors",
                  job["test_scope"] == ["v12/QUICKSTART.md"],
                  job["test_scope"])

    # AND WHAT THIS VALIDATOR DOES NOT OWN. `_job` takes `input_digest` and
    # `policy_digest` through `boundaries.text`: they are opaque to the Job
    # manager, which is correct -- the manifest's owner proves them. So the
    # authored document is ACCEPTED with its sentinels in place, and claiming
    # a refusal here would be claiming a protection this layer does not give.
    # The first cut of this scenario did exactly that and the run refused it.
    accepted = None
    try:
        documents.owned_submission(document)
        accepted = True
    except Exception as caught:                              # noqa: BLE001
        accepted = f"{type(caught).__name__}: {caught}"
    checks.expect("the submission validator ACCEPTS opaque digest text, "
                  "because digest syntax is the manifest owner's rule and not "
                  "this layer's", accepted is True, accepted)
    checks.note("where those two values are actually proved",
                "single_worker._held cross-binds the input manifest against "
                "the worker's own profile, policy and image digests and its "
                "32-character authority UUID; stage_execution's _DIGEST "
                "refuses anything but sha256:<64 hex> in the deployment "
                "document. A submission whose input_digest is not the "
                "manifest's job_input_identity is refused where the stage is "
                "matched, not here.")

    # THE SHAPE, PROVED ON A RESOLVED COPY. The sentinels are replaced with
    # syntactically valid stand-ins HERE AND ONLY HERE -- in this verification
    # run's memory, never in the packet -- so the reviewer can see that the
    # document the owner will complete is the one the validator accepts.
    resolved = copy.deepcopy(document)
    held_job = resolved["jobs"][0]
    held_job["input_digest"] = "sha256:" + "1" * 64
    held_job["policy_digest"] = "sha256:" + "2" * 64
    for stage in held_job["stages"]:
        stage["work_id"] = "0000000a-W1"
        stage["profile_name"] = "reference"
        stage["profile_digest"] = "sha256:" + "3" * 64
    owned = documents.owned_submission(resolved)
    checks.expect("with the owner's values and the readbacks in place, the "
                  "SAME document validates", owned["submission_id"]
                  == document["submission_id"], owned["submission_id"])
    checks.expect("and the validator preserves the two-stage set",
                  [one["kind"] for one in owned["jobs"][0]["stages"]]
                  == ["implementation", "review"])
    checks.expect("and the Job's own limits survive normalization",
                  owned["jobs"][0]["execution_limits"]
                  == {"provider_turn_seconds": 3600,
                      "verification_command_seconds": 900})
    return {"member": held, "unresolved": sentinels_in(document),
            "validator_accepts_opaque_digests": accepted,
            "stand_ins_used_only_here": {
                "input_digest": "sha256:1…", "policy_digest": "sha256:2…",
                "work_id": "0000000a-W1", "profile_digest": "sha256:3…"},
            "normalized_shape": {"schema": owned["schema"],
                                 "job_id": owned["jobs"][0]["job_id"],
                                 "stages": [one["kind"] for one in
                                            owned["jobs"][0]["stages"]]}}


# -- scenario 4 --------------------------------------------------------------

def the_worker_documents_name_every_member(packet, checks):
    """Pass two, held to the worker deployment contract's own member set."""
    from tools import bootstrap, single_worker, stage_execution

    document, held = loaded(packet, "job-inputs.json")
    checks.expect("the second pass names workers and jobs, which the fresh "
                  "install deferred",
                  bool(document.get("workers")) and bool(document.get("jobs")),
                  sorted(document))
    roles = [one["role"] for one in document["workers"]]
    checks.expect("the pool is implementation and review ONLY",
                  roles == ["implementation", "review"], roles)
    participants = {one["role"]: one["participant"]
                    for one in document["workers"]}
    checks.expect("the producer and the reviewer are different participants, "
                  "which bootstrap's independence rule requires",
                  participants["implementation"] != participants["review"],
                  participants)
    for worker in document["workers"]:
        checks.expect(f"worker {worker['worker_id']} names every member "
                      f"bootstrap requires of one",
                      sorted(worker) == sorted(bootstrap._WORKER),
                      sorted(worker))
        deployment = worker["deployment"]
        checks.expect(f"and its deployment names all "
                      f"{len(single_worker._MEMBERS)} members the worker "
                      f"contract closes over",
                      sorted(deployment) == sorted(single_worker._MEMBERS),
                      sorted(set(single_worker._MEMBERS) - set(deployment)))
        checks.expect(f"{worker['worker_id']} carries no secret member",
                      [name for name in stage_execution.SECRET_MEMBERS
                       if name in deployment] == [])
    job = document["jobs"][0]
    checks.expect("the Job binding names every member bootstrap requires",
                  sorted(job) == sorted(bootstrap._JOB), sorted(job))
    checks.expect("its producer is the configured implementation worker",
                  job["source_worker_id"] == "implementation-pilot",
                  job["source_worker_id"])
    checks.expect("the declared base and the canonical target are the "
                  "selected source",
                  job["line_declared_base"] == BASE
                  and job["canonical_target_id"] == BASE, job)
    unresolved = sentinels_in(document)
    checks.expect("every value that cannot exist before the instance does is "
                  "an explicit readback or selection", len(unresolved) >= 10,
                  len(unresolved))
    refusal = None
    try:
        bootstrap.held(document)
    except Exception as caught:                              # noqa: BLE001
        refusal = f"{type(caught).__name__}: {caught}"
    checks.expect("and the second pass is REFUSED while they stand",
                  refusal is not None, refusal)
    return {"member": held, "roles": roles, "participants": participants,
            "unresolved_count": len(unresolved), "unresolved": unresolved,
            "refusal_while_unresolved": refusal,
            "worker_member_count": len(single_worker._MEMBERS)}


# -- scenario 5 --------------------------------------------------------------

def the_destination_is_fresh_and_the_pins_hold(packet, checks):
    """The preflight, read-only, plus every pin this packet states."""
    import os

    from baton_v12.authority import schema as authority_schema
    from baton_v12.job_manager import execution_limits
    from tools import bootstrap, dossier_command, instance, stack_command

    places = instance.layout(DESTINATION)
    checks.expect("the selected destination does not exist yet",
                  not os.path.lexists(DESTINATION), DESTINATION)
    checks.expect("its parent exists and is a directory this user owns",
                  os.path.isdir(os.path.dirname(DESTINATION)),
                  os.path.dirname(DESTINATION))
    for name in ("distro", "justfile", "instance"):
        checks.expect(f"nothing occupies the {name} bootstrap refuses to "
                      f"replace", not os.path.lexists(places[name]),
                      places[name])
    checks.note("the layout this destination derives", places)

    checks.expect("thirteen installed subcommands",
                  len(stack_command.COMMANDS) == 13
                  and "disposition" in stack_command.COMMANDS
                  and "record" in stack_command.COMMANDS,
                  sorted(stack_command.COMMANDS))
    checks.expect("the bootstrap input schema is the one the packet names",
                  bootstrap.SCHEMA == "baton.v12.stack-bootstrap/1",
                  bootstrap.SCHEMA)
    checks.expect("nine required inputs and seven optional",
                  len(bootstrap.REQUIRED) == 9
                  and len(bootstrap.OPTIONAL) == 7,
                  {"required": bootstrap.REQUIRED,
                   "optional": bootstrap.OPTIONAL})
    checks.expect("the authority store schema is 6",
                  authority_schema.SCHEMA_VERSION == 6,
                  authority_schema.SCHEMA_VERSION)
    checks.expect("the instance selector schema is stack-instance/1",
                  instance.SCHEMA == "baton.v12.stack-instance/1",
                  instance.SCHEMA)
    checks.expect("the recovery set schema is instance-recovery-set/3",
                  dossier_command.RECOVERY_SCHEMA
                  == "baton.v12.instance-recovery-set/3",
                  dossier_command.RECOVERY_SCHEMA)
    checks.expect("limit generation 1 carries 3600/900/1800/300",
                  execution_limits.CURRENT_GENERATION == 1
                  and execution_limits.GENERATIONS[1]
                  == {"provider_turn": 3600, "ordinary_verification": 900,
                      "integration_verification": 1800,
                      "host_verification": 300},
                  execution_limits.GENERATIONS[1])
    checks.expect("with bounds 1 and 86400",
                  (execution_limits.MIN_SECONDS,
                   execution_limits.MAX_SECONDS) == (1, 86400))
    checks.expect("and a Job may express exactly two of them, which is why "
                  "the packet states the total and the cleanup allowance as "
                  "an operator envelope rather than a setting",
                  execution_limits.LIMIT_MEMBERS
                  == ("provider_turn_seconds", "verification_command_seconds"),
                  execution_limits.LIMIT_MEMBERS)
    checks.expect("the routes are the three this build serves",
                  bootstrap.ROUTES == {"implementation": "impl",
                                       "review": "rview",
                                       "integration": "integration"},
                  bootstrap.ROUTES)
    return {"destination": DESTINATION, "layout": places,
            "subcommands": sorted(stack_command.COMMANDS),
            "limits": execution_limits.GENERATIONS[
                execution_limits.CURRENT_GENERATION],
            "limit_members": list(execution_limits.LIMIT_MEMBERS),
            "stop_timeout_seconds_default": 30}


SCENARIOS = (
    ("0-harness-self-check", harness_self_check, SELF_CHECK,
     "a deliberately false expectation about the pinned task document"),
    ("1-task-document-immutable-and-owned",
     the_task_document_is_immutable_and_owned, None,
     "the one fully pinned document, validated by the workload's own owner "
     "and its verification argv actually run against five candidates"),
    ("2-install-inputs-closed-and-refusing",
     the_install_inputs_are_closed_and_refuse_their_sentinels, None,
     "pass one against bootstrap's own input contract"),
    ("3-two-stage-submission-validates", the_two_stage_submission_validates,
     None,
     "pass three against the Job manager's own validator, authored and "
     "resolved-copy"),
    ("4-worker-documents-name-every-member",
     the_worker_documents_name_every_member, None,
     "pass two against the worker deployment contract's closed member set"),
    ("5-destination-fresh-and-pins-hold",
     the_destination_is_fresh_and_the_pins_hold, None,
     "the read-only preflight and every pin the packet states"),
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", required=True)
    parser.add_argument("--evidence", required=True)
    taken = parser.parse_args()
    place = pathlib.Path(taken.evidence).resolve()
    place.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    answers, unexpected, passed = [], 0, 0

    print("W325959 packet verification (structural, no execution):")
    for name, body, intended, injected in SCENARIOS:
        at = time.monotonic()
        checks = Checks()
        record = {"scenario": name, "injected": injected,
                  "expected_failure": intended is not None,
                  "intended_failed_check": intended,
                  "performed": ["read the authored documents",
                                "called the product's own validators",
                                "ran the pinned verification argv in a "
                                "temporary directory"],
                  "not_performed": ["bootstrap", "install", "submit", "serve",
                                    "any store write", "any container",
                                    "any provider call", "any Git mutation"]}
        failure = None
        try:
            record.update(body(taken.packet, checks) or {})
            record["outcome"] = "observed"
        except CheckFailed as caught:
            record["outcome"] = "failed"
            record["failed_check"] = caught.label
            failure = caught
        except BaseException:                                # noqa: BLE001
            record["outcome"] = "failed"
            record["failure"] = traceback.format_exc()[-2000:]
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
    answer = {"schema": "baton.w325959.packet-verification/1",
              "packet": str(pathlib.Path(taken.packet).resolve()),
              "source_base": BASE,
              "destination": DESTINATION,
              "what_this_is": "contained structural verification of a "
                              "PREPARATION packet: the authored documents are "
                              "handed to the validators that own them, the "
                              "pinned verification argv is run against five "
                              "candidates in a temporary directory, and the "
                              "unresolved values are proved to make the "
                              "packet non-executable today",
              "scenarios": answers,
              "checks_passed": passed,
              "observed": sum(1 for one in answers
                              if one["outcome"] == "observed"),
              "failed_as_intended": sum(
                  1 for one in answers
                  if one.get("failed_for_intended_reason")),
              "unexpected": unexpected,
              "harness_self_check_failed_for_its_own_reason": sound,
              "seconds": round(time.monotonic() - started, 3)}
    say(place, "VALIDATION.json", answer)
    print(f"checks passed {passed}, observed {answer['observed']}, "
          f"failed-as-intended {answer['failed_as_intended']}, "
          f"unexpected {unexpected}, {answer['seconds']}s")
    if not sound:
        print("REFUSED: the self-check did not fail for its own intended "
              "reason, so these checks are not checking anything")
        return 2
    return 1 if unexpected else 0


if __name__ == "__main__":
    raise SystemExit(main())
