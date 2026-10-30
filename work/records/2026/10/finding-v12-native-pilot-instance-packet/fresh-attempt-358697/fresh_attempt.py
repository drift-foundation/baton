"""Fresh attempt for the failed instance-3 implementation. OWNER SELECTION REQUIRED.

WHAT FAILED AND WHAT THIS DOES NOT DO. Owner358671 ran the accepted fresh3
packet; instance 3 installed and Job `quickstart-c` failed its implementation
stage on an EXPIRED OAUTH credential -- provider duration_api_ms 0, cost 0,
runtime destroyed, allocation released, review blocked. That is a credential
fault, not a product defect, and nothing here repairs, retries or revives it.
`quickstart-c`, its Work, its binding, its workers, its attempt logs and its
published status are PRESERVED UNTOUCHED and remain the record of that failure.

THERE IS NO SUPPORTED SAME-JOB RETRY, and this does not invent one.
`submission.submit` journals by submission identity, so an identical
resubmission is a REPLAY rather than a reset, and `submission._unclaimed`
refuses an existing Job claimed by another submission.
`episodes.restart_abandoned_correction` requires explicit abandonment, fence,
restored-line and excluded-writer receipts, which an expired credential does
not produce and which this will not manufacture. So the supported path is a
NEW Job on a NEW Work in the SAME instance, which is what this prepares.

THE STORE BOUNDARY, corrected at claim358825 after
review-2026-10-23T05-45-38Z.md. The previous revision read every file under
`db/` to digest them, copied `authority.sqlite3` with its WAL and SHM and
opened the copy, and copied `db/` into a rehearsal root. Its docstring then
said it "never opens the live stores", which was FALSE -- `read_bytes` and
`copy2` open them. AGENTS.md:267 is the governing rule and it also says what to
do instead: "Never read it directly either: if a question about the
coordination state can only be answered by opening the store, that inability is
the finding." So this revision touches no store at all. Production state is
read from ORDINARY ARTIFACT FILES and through the product's own
`view --status`, which says of itself "Read-only view of submitted Jobs.
Performs no act." The two questions that cannot be answered that way are named
in `MISSING_PROJECTIONS` and deferred to the operation that does guarantee
them, rather than worked around.

THE SHAPE, measured rather than assumed. Two additive shapes are both ACCEPTED
by the supported in-place call:

  A. add the new Job and RE-POINT the two existing workers' input_manifest
  B. add the new Job AND TWO NEW WORKERS carrying the new manifest

They differ at the one place that decides whether anything can run: the
product's own selector `stage_execution._job_workers`, whose `_disagreements`
compares "the Work" between a worker's manifest and the Job's binding. Under A
the old Job's stages become UNSERVABLE. Under B all four stage/Job
combinations select a worker. THIS USES B.

A JOB NAMES ITS OWN PRODUCER. `_job_workers` narrows the implementation lane to
`binding["source_worker_id"]`, so the new Job names the new implementation
worker. The first measurement left the old one and the new Job's implementation
stage was refused even though the new worker agreed on every operand.

NO NEW REPOSITORY IS NEEDED: the new workers reuse the existing
`source-implementation-pilot` and `source-review-pilot`, and the in-place
operation prepares no repositories. Nothing clones and no Git runs.

    python3 w325959-fresh-attempt.py                      # check, writes nothing
    python3 w325959-fresh-attempt.py --owner-selected      # apply, in place
    python3 w325959-fresh-attempt.py --emit-submission     # write the submission

WHAT IT NEVER DOES. No submit, no serve, no start, no stop, no engine,
provider, model or credential read. No store opened, copied, traversed or
hashed. No raw SQL and no read-only SQLite mode either. No bundle replacement,
no recovery or snapshot mechanism, no Git.
"""
import argparse
import copy
import hashlib
import io
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

# THE ACCEPTED HELPER THIS REUSES, consumed BY IMPORT and pinned, never copied.
DOSSIER = pathlib.Path("/home/sl/src/baton/work/records/2026/10/"
                       "finding-v12-native-pilot-instance-packet")
SIBLING = DOSSIER / "post-install-357462"
HELPER_PINS = {
    "configure.py":
        "sha256:b15280cc19aabca5bd519b88f57a34e7b7dabe7e67a40a28348befabf9d16333",
}
TEMPLATE_PINS = {
    "fresh3-358443/task.json":
        "sha256:2f87e9dc45b94eb4100d6127a5f6e9487cb7c6edb2bbac6f3653052f966a62d0",
    "fresh3-358443/submission.json":
        "sha256:76013289a5b0d587c148add78ac93ec16272481f2b00680a077c3602bd507c7c",
}

SELECTED = {
    "destination": "/home/sl/baton-instances/native-coordination-pilot-w321608-3",
    "authority": "5a8fa4b4275b4f7fa32efafc2c48f546",
    "old_job": "quickstart-c",
    "old_work": "5a8fa4b4-W1",
    "new_job": "quickstart-d",
    "new_work": "5a8fa4b4-W2",
    "new_submission": "sub-w321608-quickstart-4",
    "new_task": "w321608-native-operator-quickstart-4",
    "new_incarnation": "w325959-owner-submit-4",
    "suffix": "-d",
}

# THE ACCOUNTABLE BYTES: ordinary documents this operation could change.
# `db/` IS DELIBERATELY ABSENT -- digesting it meant reading every store file,
# which is the boundary violation this revision removes, and a before/after
# comparison of separate DB and WAL files is not a coherent snapshot protocol
# anyway. `repo/` and `distro/` are excluded because this operation prepares
# neither.
ACCOUNTABLE = ("authority-identity.json", "bootstrap.json", "deployment.json",
               "instance.json", "install-inputs.json", "justfile")
ACCOUNTABLE_TREES = ("generated", "state/task")

# WHAT THE SUPPORTED SURFACE CANNOT TELL US. Named as operational findings
# because AGENTS.md:267 says an inability is the finding, not a licence to open
# the store.
MISSING_PROJECTIONS = {
    "work_exists_on_authority": (
        "There is no supported read-only command that projects whether a given "
        "Work id already exists on an instance's Authority. The installed "
        "bundle exposes identity, status, view, logs, record, repository, "
        "disposition, monitor, publish, manager {submit,status,serve}, "
        "attempt-diagnostics, start and stop; none answers it. So THIS HELPER "
        "DOES NOT ANSWER IT. The Work-level collision is guaranteed by the "
        "supported apply operation itself: `bootstrap` creates the Work and "
        "the Authority refuses a duplicate. What is checked here, from "
        "ordinary configuration files, is the weaker binding-level question: "
        "no Job configured in this instance already binds the new Work."),
    "fresh_runtime_liveness": (
        "No supported read-only command freshly observes whether an execution "
        "runtime is alive. `manager status` says so of itself: it 'does not "
        "refresh the runtime axis -- that is the serving loop's'. So a "
        "snapshot's runtime axis is as of the last serving reconciliation, not "
        "as of now, and a stale supervisor PID is not cessation evidence "
        "either. The quiescence gate below therefore FAILS CLOSED: it requires "
        "a canonical projection, recent enough to be about now, in which no "
        "stage is executing -- and it refuses when that is unmet OR unknown "
        "rather than inferring cessation."),
}

# THE PRODUCT'S OWN STAGE VOCABULARY, imported rather than restated, with
# anything outside it treated as unknown and therefore refused.
QUIESCENT_EXTRA = ("blocked",)
QUIESCENCE_MAX_AGE_SECONDS = 600


class Refused(SystemExit):
    def __init__(self, why):
        super().__init__("REFUSED: " + why)


def _digest(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _of(place):
    return _digest(pathlib.Path(place).read_bytes())


def pinned_helper():
    """The accepted helper, templates AND INHERITED INPUTS, by digest.

    RESTORED at claim358825. The previous revision pinned the helper module and
    the two fresh3 templates but NOT `configure.INHERITED_PINS` -- yet
    `configure.sealed_manifest` reads the prior deployment, the digest recipe
    and both native records from `SIBLING.parent` and seals them into every
    manifest this composes. So the protection that was required at claim357787
    and corrected at claim357900 was lost again here. These are enforced at
    their ACTUAL consumption path, which is `SIBLING.parent` and not wherever
    this file happens to sit.
    """
    answer = {}
    for root, pins, what in ((SIBLING, HELPER_PINS, "the accepted helper"),
                             (DOSSIER, TEMPLATE_PINS, "the template")):
        for one, want in list(pins.items()):
            held = pathlib.Path(root) / one
            if held.is_symlink() or not held.is_file():
                raise Refused(what + " " + one + " is missing at " + str(held))
            if not want:
                raise Refused(what + " " + one + " has no pinned digest; an "
                              "unpinned consumed document is not bound")
            if _of(held) != want:
                raise Refused(what + " " + one + " is " + _of(held) + " and "
                              "this procedure is bound to " + want)
            answer[one] = want
    sys.path.insert(0, str(SIBLING))
    import configure

    for one, want in list(configure.INHERITED_PINS.items()):
        held = SIBLING.parent / one
        if held.is_symlink() or not held.is_file():
            raise Refused("the inherited input " + one + " is missing at "
                          + str(held) + "; sealed_manifest consumes it")
        if not want:
            raise Refused("the inherited input " + one + " has no pinned "
                          "digest; an unpinned consumed document is not bound, "
                          "and the manifest seals it in")
        if _of(held) != want:
            raise Refused("the inherited input " + one + " is " + _of(held)
                          + " and this procedure is bound to " + want)
        answer[one] = want
    return configure, answer


def accountable_digest(destination):
    """One digest over the ordinary documents this operation could change.

    NO STORE IS READ. See ACCOUNTABLE's own comment for why `db/` is absent.
    """
    root = pathlib.Path(destination)
    held = hashlib.sha256()
    counted = 0
    for one in ACCOUNTABLE:
        place = root / one
        if place.is_file():
            counted += 1
            held.update(one.encode() + b"\0" + place.read_bytes())
    for tree in ACCOUNTABLE_TREES:
        base = root / tree
        if not base.is_dir():
            continue
        for place in sorted(base.rglob("*")):
            label = str(place.relative_to(root))
            counted += 1
            held.update(label.encode())
            if place.is_symlink():
                held.update(b"\0l\0" + os.readlink(place).encode())
            elif place.is_file():
                held.update(b"\0f\0" + place.read_bytes())
            else:
                held.update(b"\0d\0")
    return {"digest": held.hexdigest(), "counted": counted,
            "excludes": ["db/ -- no store is read", "repo/", "distro/"]}


def _publisher_alive(place, *, settle):
    """Does this projection advance while we watch it? Read-only, bounded.

    A projection that is still being written is being written BY SOMETHING, and
    that something is the serving stack. Refusing here is what makes the
    freshness requirement coherent instead of contradictory: a snapshot stays
    recent only while a publisher runs, so the supported way to hold both is to
    stop serving and then produce a ONE-SHOT projection with
    `manager ... status --control`, which needs no running loop.
    """
    first = (pathlib.Path(place).read_bytes(), pathlib.Path(place).stat().st_mtime_ns)
    time.sleep(settle)
    second = (pathlib.Path(place).read_bytes(),
              pathlib.Path(place).stat().st_mtime_ns)
    if first != second:
        try:
            was = json.loads(first[0]).get("observed_at")
            now_seen = json.loads(second[0]).get("observed_at")
        except Exception:                                      # noqa: BLE001
            was = now_seen = None
        raise Refused(
            "this projection is STILL BEING WRITTEN: watching " + str(place)
            + " for " + str(settle) + "s saw it advance"
            + (" from " + repr(was) + " to " + repr(now_seen) if was else "")
            + ". Something is publishing, which means the serving stack is "
            "alive -- and a terminal stage is not permission to reconfigure "
            "underneath it. This FAILS CLOSED.\n"
            "The supported sequence, each step separately selected by you:\n"
            "  1. stop serving:\n     " + _STOP_HINT + "\n"
            "  2. produce a ONE-SHOT projection, which needs no running loop, "
            "to a path of its own\n"
            "  3. re-check with --status <that path>")
    return {"watched_seconds": settle, "advanced": False,
            "basis": "two reads of an ordinary published file; no PID was "
                     "consulted and no process was signalled"}


_STOP_HINT = ('"<destination>/distro/baton-v12-stack" stop --instance '
              '"<destination>/instance.json"')


def projection(selected, *, now=None, max_age=QUIESCENCE_MAX_AGE_SECONDS,
               status=None, viewer=True, settle=7.0):
    """The published status, read as an ordinary artifact and PROVED READABLE.

    `state/status.json` is a document the product publishes; reading it opens
    no store. `view --status` is then run over it because the product says of
    that command "Read-only view of submitted Jobs. Performs no act." -- so the
    projection this gate judges is one the product itself accepts, not this
    helper's interpretation of a file.
    """
    from baton_v12.job_manager.documents import (STAGE_STATES,
                                                 TERMINAL_STAGE_STATES)

    destination = selected["destination"]
    place = pathlib.Path(status or pathlib.Path(destination, "state",
                                                "status.json"))
    answer = {"status_at": str(place), "read_as": "an ordinary published "
              "artifact; no store was opened"}
    if place.is_symlink() or not place.is_file():
        raise Refused("there is no published status projection at "
                      + str(place) + ". Quiescence cannot be established and "
                      "this FAILS CLOSED. Produce one with the supported "
                      "command and re-check:\n  " + _refresh_command(selected))
    held = json.loads(place.read_bytes())
    answer["schema"] = held.get("schema")
    answer["observed_at"] = held.get("observed_at")
    answer["canonical"] = held.get("canonical")
    if not str(answer["schema"] or "").startswith("baton.v12.job-status/"):
        raise Refused("the document at " + str(place) + " is not a "
                      "baton.v12.job-status projection (schema "
                      + repr(answer["schema"]) + ")")
    if held.get("canonical") is not True:
        raise Refused("the projection at " + str(place) + " reports "
                      "canonical " + repr(held.get("canonical")) + ". A "
                      "non-canonical projection is 'nobody could see the "
                      "pipeline', not 'the pipeline is empty', so this FAILS "
                      "CLOSED. `manager status` needs --control to be "
                      "canonical.")

    # THE PRODUCT'S OWN READER, over this same document.
    if viewer:
        answer["viewer"] = _viewed(destination, place)

    # FRESHNESS. A projection's runtime axis is only as recent as the last
    # serving reconciliation (see MISSING_PROJECTIONS), so an old snapshot is
    # UNKNOWN rather than reassuring.
    stamp = held.get("observed_at")
    age = _age_seconds(stamp, now=now)
    answer["age_seconds"] = age
    if age is None:
        raise Refused("the projection at " + str(place) + " carries no "
                      "readable observed_at, so its age is unknown and this "
                      "FAILS CLOSED")
    if age > max_age:
        raise Refused("the published projection is " + str(int(age))
                      + "s old and this gate accepts at most " + str(max_age)
                      + "s. An old snapshot cannot establish that nothing is "
                      "executing NOW -- its runtime axis is as of the last "
                      "serving reconciliation -- so this FAILS CLOSED rather "
                      "than inferring cessation. Refresh it with the supported "
                      "command and re-check:\n  " + _refresh_command(selected))

    # IS SOMETHING STILL PUBLISHING? ADDED at claim358825 after measuring the
    # real instance: its state/status.json was advancing every ~5 seconds, so a
    # publisher -- and therefore the serving stack -- was ALIVE, while every
    # stage was terminal or blocked and every allocation released. The earlier
    # gate would have called that quiescent, which is exactly the mistake
    # review-2026-10-23T05-45-38Z.md named: "a recorded exceptional stage is
    # not permission to replace configuration while supervisors or other work
    # are running."
    #
    # SAMPLED, NOT INFERRED FROM A PID. Two reads of an ordinary published
    # file; if its own observed_at advances, something is writing it now.
    if settle and settle > 0:
        answer["liveness"] = _publisher_alive(place, settle=settle)

    # QUIESCENCE, judged with the product's vocabulary and failing closed on
    # anything outside it.
    quiescent = set(TERMINAL_STAGE_STATES) | set(QUIESCENT_EXTRA)
    stages, busy, unknown = [], [], []
    for job in held.get("jobs") or []:
        for stage in job.get("stages") or []:
            state = stage.get("state")
            stages.append({"stage": stage.get("stage_id"), "state": state,
                           "allocation": (stage.get("allocation") or {})
                           .get("allocation_state"),
                           "runtime": (stage.get("runtime") or {})
                           .get("execution_runtime")})
            if state not in STAGE_STATES:
                unknown.append((stage.get("stage_id"), state))
            elif state not in quiescent:
                busy.append((stage.get("stage_id"), state))
            allocation = (stage.get("allocation") or {}).get("allocation_state")
            if allocation not in (None, "released"):
                busy.append((stage.get("stage_id"),
                             "allocation " + str(allocation)))
            runtime = (stage.get("runtime") or {}).get("execution_runtime")
            if runtime not in (None, "destroyed"):
                busy.append((stage.get("stage_id"), "runtime " + str(runtime)))
    answer["stages"] = stages
    if unknown:
        raise Refused("this projection reports stage states this helper does "
                      "not recognise: " + repr(unknown) + ". An unrecognised "
                      "state is UNKNOWN, not idle, so this FAILS CLOSED.")
    if busy:
        raise Refused("this instance is not quiescent: " + repr(busy)
                      + ". A recorded exceptional stage is not permission to "
                      "reconfigure while something is executing or holding an "
                      "allocation. Stop serving with the separately selected "
                      "owner command, refresh the projection and re-check:\n  "
                      + _stop_command(selected) + "\n  "
                      + _refresh_command(selected))
    answer["quiescent"] = True
    answer["quiescence_basis"] = (
        "every stage is in the product's TERMINAL_STAGE_STATES or `blocked`, "
        "every allocation is released or absent, every runtime is destroyed or "
        "absent, the projection is canonical and " + str(int(age)) + "s old. "
        "This is a statement about a published projection, NOT a fresh engine "
        "inspection -- see MISSING_PROJECTIONS.fresh_runtime_liveness.")
    answer["jobs"] = [one.get("job_id") for one in held.get("jobs") or []]
    return answer


def _age_seconds(stamp, *, now=None):
    if not isinstance(stamp, str):
        return None
    text = stamp.replace("Z", "+00:00")
    try:
        from datetime import datetime, timezone

        held = datetime.fromisoformat(text)
        if held.tzinfo is None:
            held = held.replace(tzinfo=timezone.utc)
        return max(0.0, (now if now is not None else time.time())
                   - held.timestamp())
    except Exception:                                          # noqa: BLE001
        return None


def _viewed(destination, place):
    """`view --status` over the published document. The product's own reader."""
    command = pathlib.Path(destination, "distro", "baton-v12-stack")
    if not command.is_file() or not os.access(command, os.X_OK):
        raise Refused("the installed bundle command is missing or not "
                      "executable at " + str(command) + "; the supported "
                      "read-only projection cannot be run")
    done = subprocess.run([str(command), "view", "--status", str(place)],
                          capture_output=True, text=True, timeout=120)
    if done.returncode != 0:
        raise Refused("the supported read-only view refused this projection "
                      "(exit " + str(done.returncode) + "): "
                      + (done.stderr or done.stdout or "")[-600:])
    return {"command": "view --status", "exit": 0,
            "performs": "no act, by the command's own description",
            "lines": len((done.stdout or "").strip().splitlines())}


def _refresh_command(selected):
    destination = selected["destination"]
    return ('"' + str(pathlib.Path(destination, "distro", "baton-v12-stack"))
            + '" manager --store "'
            + str(pathlib.Path(destination, "db", "jobs.sqlite3"))
            + '" --incarnation <an incarnation you choose> --authority-uuid "'
            + selected["authority"] + '" status --control "'
            + str(pathlib.Path(destination, "db", "control.sqlite3"))
            + '" > "' + str(pathlib.Path(destination, "state", "status.json"))
            + '"   # --control is what makes it canonical')


def _stop_command(selected):
    destination = selected["destination"]
    return ('"' + str(pathlib.Path(destination, "distro", "baton-v12-stack"))
            + '" stop --instance "'
            + str(pathlib.Path(destination, "instance.json"))
            + '"   # SEPARATELY SELECTED; this helper never stops anything')


def installed(selected):
    """What this instance already holds, from ordinary documents only."""
    from tools import instance

    destination = selected["destination"]
    places = instance.layout(destination)
    if not pathlib.Path(destination).is_dir():
        raise Refused("there is no instance at " + destination
                      + "; this continues an EXISTING installation")
    identity = pathlib.Path(places["identity"])
    if identity.is_symlink() or not identity.is_file():
        raise Refused("the instance has no authority identity at "
                      + str(identity))
    held = json.loads(identity.read_text())
    if held.get("schema") != "baton.v12.instance-identity/1":
        raise Refused("the identity at " + str(identity) + " is not a "
                      "baton.v12.instance-identity/1 document")
    if held["authority_uuid"] != selected["authority"]:
        raise Refused("this instance's authority is " + held["authority_uuid"]
                      + " and this procedure is bound to "
                      + selected["authority"]
                      + "; a fresh attempt belongs to the instance that failed")
    deployment = pathlib.Path(places["deployment"])
    if not deployment.is_file():
        raise Refused("there is no installed configuration at "
                      + str(deployment))
    configured = pathlib.Path(places["destination"], "generated",
                              "bootstrap-inputs.json")
    if not configured.is_file():
        raise Refused("the instance holds no generated/bootstrap-inputs.json "
                      "at " + str(configured) + "; that document is the input "
                      "this additive preparation EXTENDS, and composing a "
                      "replacement from scratch would silently unconfigure "
                      "whatever it failed to restate")
    install = pathlib.Path(places["destination"], "install-inputs.json")
    if not install.is_file():
        raise Refused("the instance holds no install-inputs.json at "
                      + str(install) + "; the synthetic rehearsal builds its "
                      "twin from this instance's own documents")
    return {"places": places, "deployment": json.loads(deployment.read_bytes()),
            "input": json.loads(configured.read_text()),
            "install": json.loads(install.read_text()),
            "input_at": str(configured)}


def collisions_refused(held, selected):
    """Every identity this creates must be free IN THE CONFIGURATION.

    WHAT THIS CAN AND CANNOT SEE, stated rather than implied. These are
    questions about ordinary configuration documents. The Authority-level
    question -- does this Work id already exist at all -- has no supported
    projection, so it is NOT asked here and is left to the operation that
    guarantees it. See MISSING_PROJECTIONS.work_exists_on_authority.
    """
    document = held["deployment"]
    bindings = {one.get("job_id"): one for one in
                document.get("job_bindings") or []}
    old_job, new_job = selected["old_job"], selected["new_job"]
    if old_job not in bindings:
        raise Refused("this instance does not bind the failed Job " + old_job
                      + "; it binds " + repr(sorted(bindings))
                      + ". This continues a specific failure and will not "
                      "guess which Job it was.")
    old = bindings[old_job]
    if old.get("job_work_id") != selected["old_work"]:
        raise Refused("Job " + old_job + " is bound to Work "
                      + repr(old.get("job_work_id")) + " and this procedure "
                      "recorded " + selected["old_work"])
    if new_job in bindings:
        raise Refused("Job " + new_job + " is ALREADY bound here, to Work "
                      + repr(bindings[new_job].get("job_work_id"))
                      + ". A fresh attempt is prepared once: inspect that Job "
                      "and continue from its projection rather than binding a "
                      "second one under the same name.")
    for one in document.get("job_bindings") or []:
        if selected["new_work"] in (one.get("job_work_id"),
                                    one.get("review_work_id")):
            raise Refused("Work " + selected["new_work"] + " is already bound "
                          "by Job " + repr(one.get("job_id")))
    configured = {one["worker_id"] for one in document.get("workers") or []}
    wanted = {one + selected["suffix"] for one in configured}
    clashing = sorted(configured & wanted)
    if clashing:
        raise Refused("these worker ids already exist: " + ", ".join(clashing)
                      + "; a fresh attempt adds its own workers rather than "
                      "reusing a name already serving something")
    return {"old_binding": old, "configured_workers": sorted(configured),
            "new_workers": sorted(wanted),
            "scope": "configuration documents only",
            "guaranteed_elsewhere": MISSING_PROJECTIONS[
                "work_exists_on_authority"]}


def base_unchanged(held, selected, projected):
    """The reviewed additive base is still the one this was prepared against."""
    answer = {}
    bindings = {one.get("job_id"): one for one in
                held["deployment"].get("job_bindings") or []}
    old = bindings[selected["old_job"]]
    for member in ("line_declared_base", "canonical_target_id"):
        answer[member] = old.get(member)
    jobs = set(projected.get("jobs") or [])
    configured = set(bindings)
    if not jobs <= configured:
        raise Refused("the published projection reports Jobs this instance's "
                      "configuration does not bind: "
                      + repr(sorted(jobs - configured))
                      + ". The configuration and the pipeline disagree, so the "
                      "reviewed additive base is not what is installed.")
    if selected["new_job"] in jobs:
        raise Refused("the published projection already reports Job "
                      + selected["new_job"] + "; it has been submitted "
                      "before. Inspect it rather than preparing it again.")
    answer["projected_jobs"] = sorted(jobs)
    answer["configured_jobs"] = sorted(configured)
    return answer


def composed(held, selected, configure):
    """The additive document, and the new manifest, task and submission."""
    document = copy.deepcopy(held["input"])
    places = held["places"]
    suffix = selected["suffix"]

    task = json.loads((DOSSIER / "fresh3-358443" / "task.json").read_text())
    task["task_id"] = selected["new_task"]
    body = json.dumps(task, indent=1, sort_keys=True).encode() + b"\n"
    task_place = pathlib.Path(places["state"], "task",
                              selected["new_task"] + ".json")
    manifest = configure.sealed_manifest(SIBLING, selected["authority"],
                                         selected["new_work"], task, body)

    old_job = None
    for one in document.get("jobs") or []:
        if one.get("job_id") == selected["old_job"]:
            old_job = one
    if old_job is None:
        raise Refused("the instance's own input document does not name Job "
                      + selected["old_job"])
    new_job = copy.deepcopy(old_job)
    new_job["job_id"] = selected["new_job"]
    new_job["work_id"] = selected["new_work"]
    new_job["source_worker_id"] = old_job["source_worker_id"] + suffix
    document["jobs"] = list(document["jobs"]) + [new_job]

    fresh_workers = []
    for one in copy.deepcopy(held["input"]["workers"]):
        one["worker_id"] = one["worker_id"] + suffix
        one["deployment"]["input_manifest"] = manifest
        one["deployment"]["task_document"] = str(task_place)
        fresh_workers.append(one)
    document["workers"] = list(held["input"]["workers"]) + fresh_workers

    submission = _submission_bound(selected, manifest)
    configure.cross_bound(document, manifest, submission)
    return {"document": document, "manifest": manifest, "task": task,
            "task_bytes": body, "task_place": str(task_place),
            "submission": submission, "new_job": new_job}


def _submission_bound(selected, manifest):
    """The new submission, through the manager's OWN validator."""
    from baton_v12.contracts import job_input_identity
    from baton_v12.job_manager import documents as job_documents

    submission = json.loads((DOSSIER / "fresh3-358443"
                             / "submission.json").read_text())
    submission["submission_id"] = selected["new_submission"]
    job = submission["jobs"][0]
    job["job_id"] = selected["new_job"]
    job["input_digest"] = job_input_identity(manifest)
    for stage in job["stages"]:
        stage["work_id"] = selected["new_work"]
        for one in stage.get("depends_on") or []:
            if one.get("job_id") == selected["old_job"]:
                one["job_id"] = selected["new_job"]
    if job["execution_limits"] != {"provider_turn_seconds": 3600,
                                   "verification_command_seconds": 900}:
        raise Refused("per-invocation limits were altered")
    text = json.dumps(submission)
    left = [one for one in text.split('"')
            if one.startswith(("READBACK", "COMPOSED(", "SELECTED("))]
    if left:
        raise Refused("unresolved markers remain in the submission: "
                      + repr(left[:2]))
    for one in (selected["old_job"], selected["old_work"]):
        if one in text:
            raise Refused("the new submission still names " + one
                          + "; a fresh attempt is not a replay of the failed "
                          "one")
    job_documents.owned_submission(submission)
    return submission


def agrees_with_installed(installed_document, submission, selected,
                          *, task_bytes):
    """The submission must match THE INSTALLED new workers, not just be valid.

    REQUIRED at claim358825: the previous revision only checked that the new
    Job name was configured, so a submission whose input identity disagreed
    with the workers that would serve it -- the exact `_disagreements` operand
    `the submitted input` -- would have been emitted and then refused at
    allocation.
    """
    from baton_v12.contracts import job_input_identity

    suffix = selected["suffix"]
    job = submission["jobs"][0]
    workers = [one for one in installed_document.get("workers") or []
               if one["worker_id"].endswith(suffix)]
    if len(workers) != 2:
        raise Refused("the installed configuration carries "
                      + str(len(workers)) + " workers ending " + repr(suffix)
                      + "; this submission is served by exactly two")
    answer = {"compared_workers": [one["worker_id"] for one in workers]}
    for one in workers:
        deployment = one["deployment"]
        manifest = deployment["input_manifest"]
        identity = job_input_identity(manifest)
        if identity != job["input_digest"]:
            raise Refused("installed worker " + one["worker_id"] + " projects "
                          "input identity " + identity + " and this submission "
                          "names " + job["input_digest"]
                          + "; the worker could not serve this Job")
        if manifest["work_ref"]["work_id"] != selected["new_work"]:
            raise Refused("installed worker " + one["worker_id"] + " names "
                          "Work " + manifest["work_ref"]["work_id"]
                          + " and this submission names "
                          + selected["new_work"])
        if deployment["policy_digest"] != job["policy_digest"]:
            raise Refused("installed worker " + one["worker_id"] + " names "
                          "policy " + deployment["policy_digest"]
                          + " and this submission names "
                          + job["policy_digest"])
        held = pathlib.Path(deployment["task_document"])
        if not held.is_file():
            raise Refused("installed worker " + one["worker_id"] + " names a "
                          "task document that is not there: " + str(held))
        if held.read_bytes() != task_bytes:
            raise Refused("the installed task document at " + str(held)
                          + " is not the bytes this submission was composed "
                          "against")
        if manifest["human_contract"]["content_digest"] != _digest(task_bytes):
            raise Refused("installed worker " + one["worker_id"] + "'s "
                          "manifest seals a human contract digest that is not "
                          "this task's bytes")
    answer["input_digest"] = job["input_digest"]
    answer["task_digest"] = _digest(task_bytes)
    answer["bound_to_installed_workers"] = True
    return answer


def _retargeted(value, was, now):
    if isinstance(value, str):
        return value.replace(was, now)
    if isinstance(value, dict):
        return {k: _retargeted(v, was, now) for k, v in value.items()}
    if isinstance(value, list):
        return [_retargeted(one, was, now) for one in value]
    return value


def _stub_bundle(where):
    """A bundle satisfying `admit`'s identity checks. SIMULATED, not a build."""
    where.mkdir(parents=True)
    command = where / "baton-v12-stack"
    command.write_text("#!/bin/sh\ncat <<I\n" + json.dumps(
        {"frozen": True,
         "schema_assets": {"agent-session-1.0": 1, "worker-control-1.0": 1},
         "native_rpds": str(where / "rpds.so")}) + "\nI\n")
    command.chmod(0o755)
    (where / "rpds.so").write_bytes(b"simulated native validator\n")
    return where


class _Done:
    def __init__(self, stdout="", returncode=0, stderr=""):
        self.stdout, self.returncode, self.stderr = stdout, returncode, stderr


def _simulated_runner(base):
    def ran(argv, **_named):
        argv = list(argv)
        if len(argv) > 1 and argv[1] == "clone":
            place = pathlib.Path(argv[-1])
            place.mkdir(parents=True, exist_ok=False)
            (place / ".simulated-git" / "objects" / "info").mkdir(parents=True)
            return _Done()
        if len(argv) > 3 and argv[3] == "rev-parse":
            if "--git-common-dir" in argv:
                return _Done(str(pathlib.Path(argv[2]) / ".simulated-git"))
            return _Done(base)
        return _Done()
    return ran


def rehearsed(held, selected, configure, *, stream=None):
    """A SYNTHETIC twin, built through the supported APIs. NO STORE IS COPIED.

    REWRITTEN at claim358825. The previous revision copied `db/` out of the
    live instance and ran the preparation over the copy, which opened the
    stores and -- because DB and WAL were copied as separate files -- would not
    have been a coherent snapshot even if that were permitted.

    This instead builds a twin from this instance's OWN ORDINARY DOCUMENTS:
    its `install-inputs.json` and its `generated/bootstrap-inputs.json`. The
    twin's stores are created from nothing by the supported bootstrap, so it
    mints its OWN Authority -- which is why every identity is retargeted onto
    that uuid below. The additive change is then applied there and the
    product's own selector is driven over the result.

    WHAT THIS IS AND IS NOT. It proves the additive SHAPE composes, applies and
    selects against a configuration structurally identical to this instance's.
    It is NOT a rehearsal of this instance's own stores, and it cannot be: no
    supported surface exposes them for that purpose, and copying them is the
    boundary violation this replaced.
    """
    from tools import bootstrap, instance, stage_execution

    source = pathlib.Path(held["places"]["destination"])
    answer = {"kind": "synthetic twin built through the supported bootstrap",
              "no_store_copied": True}
    with tempfile.TemporaryDirectory(prefix="w325959-synthetic-") as place:
        home = pathlib.Path(place)
        root = home / source.name
        distro = _stub_bundle(home / "distro")
        repository_source = home / "src"
        (repository_source / "v12").mkdir(parents=True)
        (repository_source / "v12" / "justfile").write_text("# simulated\n")

        old_binding = None
        for one in held["deployment"].get("job_bindings") or []:
            if one.get("job_id") == selected["old_job"]:
                old_binding = one
        base = old_binding["line_declared_base"]
        runner = _simulated_runner(base)

        # -- STEP 1: mint the twin's own authority, from THIS instance's own
        #    install document, carrying no workers and no jobs.
        install = _retargeted(held["install"], str(source), str(root))
        install["state_root"] = str(root)
        if install.get("workers") or install.get("jobs"):
            raise Refused("this instance's install-inputs.json carries "
                          "workers or jobs; the twin is minted from a document "
                          "that carries neither")
        root.mkdir(parents=True)
        staged = root / "install-inputs.json"
        staged.write_text(json.dumps(install, indent=1, sort_keys=True) + "\n")
        spoken = io.StringIO()
        if bootstrap.main(["--inputs", str(staged)], stream=spoken) != 0:
            raise Refused("the twin's authority could not be minted:\n"
                          + spoken.getvalue().strip()[-800:])
        places = instance.layout(str(root))
        twin = json.loads(pathlib.Path(places["identity"]).read_text())
        uuid = twin["authority_uuid"]
        answer["twin_authority"] = uuid
        if uuid == selected["authority"]:
            raise Refused("the twin minted the production authority " + uuid
                          + ", which cannot happen and would mean this is not "
                          "a twin")

        # -- STEP 2: the twin's configuration, retargeted onto its own identity
        #    and its own Works, with every manifest RE-SEALED for them.
        bound = dict(selected, destination=str(root), authority=uuid,
                     old_work=uuid[:8] + "-W1", new_work=uuid[:8] + "-W2")
        document = _retargeted(held["input"], str(source), str(root))
        document = _retargeted(document, selected["authority"], uuid)
        document = _retargeted(document, selected["old_work"],
                               bound["old_work"])
        old_task_place = pathlib.Path(
            document["workers"][0]["deployment"]["task_document"])
        old_task_source = pathlib.Path(_retargeted(str(old_task_place),
                                                   str(root), str(source)))
        if not old_task_source.is_file():
            raise Refused("this instance's task document is not readable at "
                          + str(old_task_source))
        old_task = json.loads(old_task_source.read_bytes())
        old_body = old_task_source.read_bytes()
        old_manifest = configure.sealed_manifest(SIBLING, uuid,
                                                 bound["old_work"], old_task,
                                                 old_body)
        for one in document["workers"]:
            one["deployment"]["authority_uuid"] = uuid
            one["deployment"]["input_manifest"] = old_manifest
            one["deployment"]["task_document"] = str(old_task_place)
        old_task_place.parent.mkdir(parents=True, exist_ok=True)
        old_task_place.write_bytes(old_body)
        emitted = root / "generated"
        emitted.mkdir(parents=True, exist_ok=True)
        twin_inputs = emitted / "bootstrap-inputs.json"
        twin_inputs.write_text(json.dumps(document, indent=1, sort_keys=True)
                               + "\n")
        spoken = io.StringIO()
        if bootstrap.main(["--inputs", str(twin_inputs), "--destination",
                           str(root), "--distro", str(distro),
                           "--repository-source", str(repository_source)],
                          stream=spoken, runner=runner) != 0:
            raise Refused("the twin could not be configured:\n"
                          + spoken.getvalue().strip()[-900:])
        twin_held = {"places": places,
                     "deployment": json.loads(
                         pathlib.Path(places["deployment"]).read_bytes()),
                     "input": json.loads(twin_inputs.read_text()),
                     "install": install}
        answer["twin_jobs_before"] = [one.get("job_id") for one in
                                      twin_held["deployment"]["job_bindings"]]

        # -- STEP 3: the additive change, applied to the twin.
        composition = composed(twin_held, bound, configure)
        task_place = pathlib.Path(composition["task_place"])
        task_place.parent.mkdir(parents=True, exist_ok=True)
        task_place.write_bytes(composition["task_bytes"])
        additive = emitted / "additive-inputs.json"
        additive.write_text(json.dumps(composition["document"], indent=1,
                                       sort_keys=True) + "\n")
        spoken = io.StringIO()
        code = bootstrap.main(["--inputs", str(additive)], stream=spoken)
        answer["exit"] = code
        answer["said"] = spoken.getvalue().strip().splitlines()[-6:]
        if code != 0:
            raise Refused("the supported operation REFUSED this additive "
                          "configuration on the synthetic twin (exit "
                          + str(code) + "):\n"
                          + spoken.getvalue().strip()[-1200:])
        after = json.loads(pathlib.Path(places["deployment"]).read_bytes())
        if stage_execution.held_configuration(after) is None:
            raise Refused("the rehearsed configuration failed "
                          "held_configuration")
        answer["bindings"] = after.get("job_bindings")
        answer["workers"] = [one["worker_id"] for one in
                             after.get("workers") or []]
        answer["preserved"] = preserved(twin_held["deployment"], after, bound)
        answer["selector"] = selects(after, bound)
        answer["submission_agrees_with_installed"] = agrees_with_installed(
            after, composition["submission"], bound,
            task_bytes=composition["task_bytes"])
    return answer


def preserved(before, after, selected):
    """The failed Job's binding AND its workers must survive byte-exact."""
    was = {one["job_id"]: one for one in before.get("job_bindings") or []}
    now = {one["job_id"]: one for one in after.get("job_bindings") or []}
    old_job = selected["old_job"]
    if old_job not in now:
        raise Refused("this dropped Job " + old_job + "'s binding")
    if now[old_job] != was[old_job]:
        raise Refused("this CHANGED Job " + old_job + "'s binding: "
                      + json.dumps(was[old_job]) + " -> "
                      + json.dumps(now[old_job]))
    old_workers = {one["worker_id"]: one for one in before.get("workers") or []}
    new_workers = {one["worker_id"]: one for one in after.get("workers") or []}
    for who, one in old_workers.items():
        if who not in new_workers:
            raise Refused("this dropped worker " + who)
        if new_workers[who] != one:
            raise Refused("this CHANGED existing worker " + who
                          + "; the failed Job's workers are preserved so its "
                          "stages remain accountable and servable")
    return {"binding_identical": True, "existing_workers_identical": True,
            "compared": sorted(old_workers)}


class _Shim:
    """Exactly the three attributes `_job_workers` reads, and nothing else.

    `StageDeployment` needs live stores, sessions and an open Authority, none
    of which this may construct -- and must not. The SELECTOR and its
    `_disagreements` are the product's own; this supplies their operands from
    an installed configuration document.
    """

    def __init__(self, given, jobs):
        self.given, self.jobs = given, jobs

    def binding_for(self, job_id):
        for one in self.given["job_bindings"]:
            if one.get("job_id") == job_id:
                return one
        raise Refused("this deployment binds no Job " + repr(job_id))


def selects(after, selected):
    """Drive the PRODUCT'S OWN selector for both Jobs and both roles."""
    from baton_v12.contracts import job_input_identity
    from tools import stage_execution

    given = stage_execution.held_configuration(after)
    suffix = selected["suffix"]
    manifests = {}
    for one in after["workers"]:
        key = "new" if one["worker_id"].endswith(suffix) else "old"
        manifests.setdefault(key, one["deployment"]["input_manifest"])
    if "old" not in manifests or "new" not in manifests:
        raise Refused("the installed configuration does not carry both an "
                      "existing and a new worker to compare")
    profile = after["workers"][0]["deployment"]
    jobs = [{"job_id": selected["old_job"],
             "input_digest": job_input_identity(manifests["old"]),
             "policy_digest": profile["policy_digest"]},
            {"job_id": selected["new_job"],
             "input_digest": job_input_identity(manifests["new"]),
             "policy_digest": profile["policy_digest"]}]
    deployment = _Shim(given, jobs)
    answer = {}
    for job_id, work in ((selected["old_job"], selected["old_work"]),
                         (selected["new_job"], selected["new_work"])):
        job = [one for one in jobs if one["job_id"] == job_id][0]
        for kind in ("implementation", "review"):
            stage = {"stage_id": job_id + "/" + kind, "job_id": job_id,
                     "kind": kind, "work_id": work,
                     "profile_name": profile["profile_name"],
                     "profile_digest": profile["profile_digest"]}
            try:
                _, compatible = stage_execution._job_workers(deployment, stage,
                                                             job)
            except BaseException as refusal:                   # noqa: BLE001
                raise Refused("the product's own selector would NOT serve "
                              + job_id + "/" + kind + " after this "
                              "configuration: " + str(refusal)[:500])
            chosen = [one["worker_id"] for one in compatible]
            if not chosen:
                raise Refused("no worker selects " + job_id + "/" + kind)
            answer[job_id + "/" + kind] = chosen
    return answer


def check(selected=None, *, configure=None, now=None,
          max_age=QUIESCENCE_MAX_AGE_SECONDS, status=None, viewer=True):
    """Read-only. Writes nothing here and opens no store."""
    selected = dict(SELECTED, **(selected or {}))
    pins = None
    if configure is None:
        configure, pins = pinned_helper()
    destination = selected["destination"]
    before = accountable_digest(destination)
    held = installed(selected)
    answer = {"mode": "check", "destination": destination,
              "authority": selected["authority"],
              "failed_job": selected["old_job"],
              "failed_work": selected["old_work"],
              "new_job": selected["new_job"], "new_work": selected["new_work"],
              "new_submission": selected["new_submission"],
              "new_task": selected["new_task"], "pins": pins,
              "accountable_before": before,
              "missing_projections": MISSING_PROJECTIONS}
    answer["collisions"] = collisions_refused(held, selected)
    answer["projection"] = projection(selected, now=now, max_age=max_age,
                                      status=status, viewer=viewer)
    answer["base"] = base_unchanged(held, selected, answer["projection"])
    composition = composed(held, selected, configure)
    answer["manifest_digest"] = composition["manifest"]["manifest_digest"]
    answer["input_digest"] = composition["submission"]["jobs"][0]["input_digest"]
    answer["task_digest"] = _digest(composition["task_bytes"])
    answer["rehearsal"] = rehearsed(held, selected, configure)
    after = accountable_digest(destination)
    answer["accountable_after"] = after
    if after != before:
        raise Refused("CHECK MODE CHANGED THIS INSTANCE: accountable bytes "
                      "went from " + before["digest"] + " to "
                      + after["digest"] + ". That is a defect in this helper; "
                      "report it rather than proceeding.")
    answer["destination_unchanged"] = True
    answer["next_commands"] = commands(selected)
    return answer


def apply(selected=None, *, configure=None, stream=None, now=None,
          max_age=QUIESCENCE_MAX_AGE_SECONDS, status=None, viewer=True):
    """OWNER-SELECTED. The one supported in-place call, after a full check."""
    from tools import bootstrap, stage_execution

    selected = dict(SELECTED, **(selected or {}))
    if configure is None:
        configure, _ = pinned_helper()
    destination = selected["destination"]
    answer = check(selected, configure=configure, now=now, max_age=max_age,
                   status=status, viewer=viewer)
    answer["mode"] = "apply"
    held = installed(selected)
    composition = composed(held, selected, configure)

    task_place = pathlib.Path(composition["task_place"])
    if task_place.is_symlink():
        raise Refused("the task document name " + str(task_place) + " is a "
                      "link; nothing here writes through one")
    if task_place.exists() and \
            task_place.read_bytes() != composition["task_bytes"]:
        raise Refused("a DIFFERENT task document is already at "
                      + str(task_place) + "; nothing here overwrites one")
    out = pathlib.Path(destination, "generated")
    staged = out / "additive-inputs.json"
    if out.is_symlink():
        raise Refused("the output directory " + str(out) + " is a link")
    for one in (staged, out / ("submission-" + selected["new_job"] + ".json")):
        if one.is_symlink():
            raise Refused("the output name " + str(one) + " is a link")
    if staged.exists():
        raise Refused("generated/additive-inputs.json already exists at "
                      + str(staged) + "; a previous attempt left it. Inspect "
                      "and move it rather than having this overwrite evidence.")
    task_place.parent.mkdir(parents=True, exist_ok=True)
    task_place.write_bytes(composition["task_bytes"])
    staged.write_text(json.dumps(composition["document"], indent=1,
                                 sort_keys=True) + "\n")
    spoken = stream or io.StringIO()
    code = bootstrap.main(["--inputs", str(staged)], stream=spoken)
    said = spoken.getvalue() if isinstance(spoken, io.StringIO) else ""
    answer["apply"] = {"exit": code, "inputs_at": str(staged),
                       "said": said.strip().splitlines()[-8:]}
    if code != 0:
        raise Refused("the supported operation refused in place (exit "
                      + str(code) + "):\n" + said.strip()[-1200:])
    after = json.loads(pathlib.Path(held["places"]["deployment"]).read_bytes())
    if stage_execution.held_configuration(after) is None:
        raise Refused("the installed configuration failed held_configuration")
    answer["apply"]["preserved"] = preserved(held["deployment"], after,
                                             selected)
    answer["apply"]["bindings"] = after.get("job_bindings")
    answer["apply"]["workers"] = [one["worker_id"] for one in after["workers"]]
    answer["apply"]["selector"] = selects(after, selected)
    answer["apply"]["task_digest"] = _of(task_place)
    answer["apply"]["submission_agrees_with_installed"] = agrees_with_installed(
        after, composition["submission"], selected,
        task_bytes=composition["task_bytes"])
    return answer


def emit_submission(selected=None, *, configure=None):
    """OWNER-SELECTED, separately. Writes the submission document only."""
    selected = dict(SELECTED, **(selected or {}))
    if configure is None:
        configure, _ = pinned_helper()
    destination = selected["destination"]
    held = installed(selected)
    bound = {one.get("job_id") for one in
             held["deployment"].get("job_bindings") or []}
    if selected["new_job"] not in bound:
        raise Refused("Job " + selected["new_job"] + " is not configured here "
                      "yet; apply the additive preparation first, or the "
                      "submit would name a Job this deployment cannot bind")
    composition = composed(held, selected, configure)
    # BOUND TO WHAT IS INSTALLED, not merely to a configured name.
    agreement = agrees_with_installed(held["deployment"],
                                      composition["submission"], selected,
                                      task_bytes=composition["task_bytes"])
    place = pathlib.Path(destination, "generated",
                         "submission-" + selected["new_job"] + ".json")
    if place.is_symlink():
        raise Refused("the output name " + str(place) + " is a link")
    if place.exists():
        raise Refused("the submission document already exists at " + str(place)
                      + "; inspect it rather than having this overwrite it")
    place.write_text(json.dumps(composition["submission"], indent=1,
                                sort_keys=True) + "\n")
    return {"mode": "emit-submission", "wrote": str(place),
            "digest": _of(place), "submission_id": selected["new_submission"],
            "job": selected["new_job"], "agreement": agreement,
            "input_digest": composition["submission"]["jobs"][0]["input_digest"],
            "next": commands(selected)["5_submit"]}


def commands(selected):
    destination = selected["destination"]
    command = str(pathlib.Path(destination, "distro", "baton-v12-stack"))
    me = str(pathlib.Path(__file__).resolve())
    return {
        "0_refresh_the_projection": _refresh_command(selected),
        "0_stop_if_not_quiescent": _stop_command(selected),
        "1_check": "python3 " + me,
        "2_apply": "python3 " + me + " --owner-selected",
        "3_emit_submission": "python3 " + me + " --emit-submission",
        "5_submit": [
            'C="' + command + '"',
            'A="' + selected["authority"] + '"',
            '"$C" manager \\',
            '    --store "' + str(pathlib.Path(destination, "db",
                                               "jobs.sqlite3")) + '" \\',
            '    --incarnation ' + selected["new_incarnation"] + ' \\',
            '    --authority-uuid "$A" \\',
            '    submit --document "' + str(pathlib.Path(
                destination, "generated",
                "submission-" + selected["new_job"] + ".json")) + '"',
        ],
        "6_serving": [
            'I="' + str(pathlib.Path(destination, "instance.json")) + '"',
            '"$C" status --instance "$I"',
            '"$C" start  --instance "$I"      # live serving',
        ],
        "expected_readbacks": {
            "job_bindings": "two entries: " + selected["old_job"] + " on "
                            + selected["old_work"] + " UNCHANGED, and "
                            + selected["new_job"] + " on "
                            + selected["new_work"],
            "workers": "four: the two existing ones unchanged, plus "
                       "implementation-pilot" + selected["suffix"]
                       + " and review-pilot" + selected["suffix"],
            "selector": "all four stage/Job pairs select a worker; the failed "
                        "Job stays servable rather than being orphaned",
            "submission_agrees_with_installed": "bound_to_installed_workers "
                                                "true",
            "status": "after submit, " + selected["new_job"] + " appears "
                      "alongside the retained " + selected["old_job"]
                      + ", whose implementation stays `exceptional` and whose "
                      "review stays `blocked`",
        },
        "stop_on_mismatch": "any readback that differs from the above is a "
                            "mismatch: stop and report it rather than "
                            "re-running, because the apply is prepared once "
                            "and a second one refuses by design",
    }


def main(argv=None, *, stream=sys.stdout):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", default=SELECTED["destination"])
    parser.add_argument("--status", default=None,
                        help="the published projection to judge quiescence "
                             "from; the instance's own state/status.json by "
                             "default")
    parser.add_argument("--max-projection-age", type=float,
                        default=QUIESCENCE_MAX_AGE_SECONDS,
                        help="refuse a projection older than this many "
                             "seconds; it cannot speak for now")
    parser.add_argument("--owner-selected", action="store_true",
                        help="apply the additive preparation in place")
    parser.add_argument("--emit-submission", action="store_true",
                        help="write the new submission document only")
    taken = parser.parse_args(argv)
    if taken.owner_selected and taken.emit_submission:
        raise Refused("apply and emit-submission are separate owner "
                      "selections; choose one")
    selected = {"destination": taken.destination}
    if taken.owner_selected:
        answer = apply(selected, max_age=taken.max_projection_age,
                       status=taken.status)
    elif taken.emit_submission:
        answer = emit_submission(selected)
    else:
        answer = check(selected, max_age=taken.max_projection_age,
                       status=taken.status)
    print(json.dumps(answer, indent=1, sort_keys=True), file=stream)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
