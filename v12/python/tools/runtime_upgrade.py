"""Upgrade a STOPPED installed instance's runtime in place. W386447.

`bootstrap` prepares a destination once and `instance.verify` refuses a runtime
that is not the one the selector recorded, so before this module the only way
to run a different build was a NEW destination -- new stores, so a Job held
for an owner's answer could not cross. This is the one supported, owner-run
act that replaces the one-folder runtime under a destination and keeps
everything else there: stores, Works, Jobs, lines, custody, configuration and
logs.

WHO RUNS IT. The NEW runtime, from where it was built:
`<built distro>/baton-v12-stack upgrade-runtime --instance <instance.json>
--distro <built distro>`. The code that checks the stores and composes the
deployment is therefore the code that will serve them; a frozen command must
BE the distro it installs.

WHAT IT REFUSES, before any effect: a selector whose installed runtime is not
the recorded one; a stack whose manager or publisher is live or unresolved
(`stack.admission` is held throughout, so no start can interleave); a durable
read, made by this code, that cannot be completed or shows any phase that is,
or may be, executing (`unresolved`); and a source runtime that is not a
frozen, self-contained bundle.

CRASH-SAFE BY A DURABLE INTENT. The new runtime is copied and verified under
a staging name first; then `runtime-upgrade.json` names both digests and both
names, and only then is the old runtime renamed aside and the new one renamed
in, and the selector republished. A rerun with the intent present rechecks
the stopped stack and the durable read, under the same lock, then rolls the
same steps forward and nothing else. Each finished upgrade is appended ONCE
to `runtime-upgrades.jsonl`, keyed by the intent's `upgrade_id`, so a rerun
after an interruption between that append and the intent's removal reuses the
committed record. The retired runtime is KEPT beside the destination, so the
previous build is still there to read.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path

from tools import instance, stack

SCHEMA = "baton.v12.runtime-upgrade/1"
INTENT = "runtime-upgrade.json"
HISTORY = "runtime-upgrades.jsonl"
# W386447 review 2026-11-27 [1]. A phase is SETTLED only in one of these
# states, which no worker executes in; every other state, and any state this
# code does not know, may be executing.
SETTLED_STATES = ("blocked", "queued", "awaiting-answer", "answered",
                  "changes-requested", "completed", "exceptional")
# And only when its recorded runtime, if one was ever attached, is gone. The
# execution axis is the durable one (`integration.runtime`); `quiescent` still
# names a container the serving runtime would have to manage, so it is not
# settled here.
SETTLED_RUNTIMES = ("not-started", "destroyed")


class UpgradeRefusal(Exception):
    pass


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(
        timespec="milliseconds").replace("+00:00", "Z")


def _names(destination, old, new):
    root = Path(destination)
    return {"staging": str(root / ("distro.upgrade-" + new[:16])),
            "retired": str(root / ("distro.retired-" + old[:16]))}


def _stopped(root):
    """Both supervisors absent or provably gone; anything else refuses."""
    for name in stack.PROCESSES:
        held = stack.ownership(stack.read_record(root, name))
        if held in (stack.LIVE, stack.UNKNOWN):
            raise UpgradeRefusal(
                "the " + name + " of this instance is " + held + "; a runtime "
                "is replaced only under a stopped stack. Stop it first; "
                "nothing was changed.")


def unresolved(status):
    """Every phase of a durable status document that is, or may be, executing.

    Read from what the document actually publishes for each stage: its
    `state` and its recorded runtime's `execution_runtime`. A held phase
    (`awaiting-answer`, `answered`) whose runtime was destroyed is settled; a
    `waiting` or `running` attempt, a runtime still attached, an unknown state
    or a document that does not describe every Job is not. Shared by the
    upgrade and by the field launcher's guard before it stops anything.
    """
    if type(status) is not dict or status.get("canonical") is not True \
            or type(status.get("jobs")) is not list:
        return ["the status read does not describe every Job"]
    found = []
    for job in status["jobs"]:
        stages = job.get("stages") if type(job) is dict else None
        if type(stages) is not list:
            found.append("a Job whose phases are not described")
            continue
        for stage in stages:
            stage = stage if type(stage) is dict else {}
            name = str(stage.get("stage_id") or "an unnamed phase")
            state = stage.get("state")
            if state not in SETTLED_STATES:
                found.append(name + " is " + str(state))
                continue
            runtime = stage.get("runtime")
            if runtime is None:
                continue
            axis = runtime.get("execution_runtime") if type(runtime) is dict \
                else None
            if axis not in SETTLED_RUNTIMES:
                found.append(name + " (" + str(state) + ") has a runtime "
                             + str(axis))
    return found


def _quiet(document, reader):
    """The durable read, by THIS code, completes and shows nothing executing.

    It opens the stores read-only and composes the deployment exactly as the
    status reader does, so a store or a configuration this build cannot read
    refuses here rather than at the first start.
    """
    try:
        status = reader(instance.settings(document))
    except Exception as failure:                             # noqa: BLE001
        raise UpgradeRefusal(
            "this runtime cannot read the instance's stores and configuration ("
            + type(failure).__name__ + ": " + str(failure)[:400]
            + "); nothing was changed.") from failure
    found = unresolved(status)
    if found:
        raise UpgradeRefusal(
            "not settled: " + "; ".join(found)
            + ". A runtime is replaced only when nothing is, or may be, "
            "executing. Nothing was changed.")
    return status


def _upgrade_id(intent):
    """The completion key: the intent's own operands, not when it finished."""
    operands = {key: intent[key] for key in
                ("schema", "recorded_at", "destination", "from", "to",
                 "staging", "retired")}
    return "runtime-upgrade:" + hashlib.sha256(json.dumps(
        operands, sort_keys=True).encode("utf-8")).hexdigest()


def _completed(journal, upgrade_id):
    """The committed history record for this upgrade, if one was appended."""
    try:
        lines = journal.read_text().splitlines()
    except FileNotFoundError:
        return None
    for line in lines:
        try:
            record = json.loads(line)
        except ValueError:
            continue       # a torn final line is not a completion record
        if type(record) is dict and record.get("upgrade_id") == upgrade_id:
            return record
    return None


def _running_is(distro):
    from tools import stack_command

    if stack_command.frozen():
        running = os.path.realpath(stack_command.executable())
        named = os.path.realpath(os.path.join(distro, "baton-v12-stack"))
        if running != named:
            raise UpgradeRefusal(
                "this command is " + running + " and the runtime to install is "
                + named + "; the new runtime installs itself, so the code that "
                "checks the stores is the code that will serve them.")


def _held_digest(place):
    try:
        return instance.manifest(place)["digest"]
    except instance.InstanceRefusal:
        return None


def upgrade(place, distro, *, stream, reader=None, identity_of=None, now=_now):
    """Replace the runtime under `place`'s destination with `distro`."""
    from tools import bootstrap, job_status

    reader = reader or job_status.read
    identity_of = identity_of or bootstrap._identity_of
    document = instance.read(place)
    places = instance.layout(document["destination"])
    intent_place = Path(places["destination"]) / INTENT
    with stack.admission(Path(document["state"])):
        if intent_place.exists():
            intent = json.loads(intent_place.read_text())
            if intent.get("schema") != SCHEMA \
                    or document["runtime"]["digest"] not in (
                        intent["from"]["runtime"]["digest"],
                        intent["to"]["runtime"]["digest"]):
                raise UpgradeRefusal(
                    str(intent_place) + " does not describe an upgrade of this "
                    "selector's runtime; it was left as it is.")
            # REVALIDATED, NOT INHERITED (review 2026-11-27 [1]): an interrupted
            # upgrade is finished only by the runtime it installs, under a
            # stack that is stopped NOW and stores that are settled NOW.
            if _held_digest(distro) != intent["to"]["runtime"]["digest"]:
                raise UpgradeRefusal(
                    str(intent_place) + " records an upgrade to runtime "
                    + intent["to"]["runtime"]["digest"][:16] + ", and "
                    + str(distro) + " is not that runtime; it was left as it "
                    "is.")
            _running_is(distro)
            _stopped(Path(document["state"]))
            _quiet(document, reader)
            print("resuming   the recorded upgrade "
                  + intent["from"]["runtime"]["digest"][:16] + " -> "
                  + intent["to"]["runtime"]["digest"][:16], file=stream)
        else:
            _running_is(distro)
            installed = _held_digest(places["distro"])
            if installed != document["runtime"]["digest"]:
                raise UpgradeRefusal(
                    "the runtime at " + places["distro"] + " is not the one "
                    "this instance records; nothing here upgrades a runtime it "
                    "cannot identify. Nothing was changed.")
            source = instance.manifest(distro)
            if source["digest"] == installed:
                print("unchanged  the instance already runs runtime "
                      + installed[:16], file=stream)
                return 0
            try:
                said = identity_of(Path(distro) / "baton-v12-stack", source,
                                   str(distro))
            except bootstrap.BootstrapRefusal as refusal:
                raise UpgradeRefusal(str(refusal)) from refusal
            _stopped(Path(document["state"]))
            _quiet(document, reader)
            names = _names(places["destination"], installed, source["digest"])
            if os.path.lexists(names["retired"]):
                raise UpgradeRefusal(
                    "a retired runtime is already at " + names["retired"]
                    + "; it is left as it is and nothing was changed.")
            if os.path.lexists(names["staging"]):
                if _held_digest(names["staging"]) != source["digest"]:
                    raise UpgradeRefusal(
                        names["staging"] + " is there and is not this runtime; "
                        "it is left as it is and nothing was changed.")
            else:
                made = {}
                try:
                    bootstrap.copy_runtime(str(distro), names["staging"],
                                           made=made)
                except bootstrap.BootstrapRefusal as refusal:
                    raise UpgradeRefusal(
                        str(refusal) + "; the partial copy is retained at "
                        + names["staging"]) from refusal
                if _held_digest(names["staging"]) != source["digest"]:
                    raise UpgradeRefusal(
                        "the runtime copied to " + names["staging"] + " does not "
                        "digest as " + str(distro) + "; nothing was replaced.")
            intent = {"schema": SCHEMA, "recorded_at": now(),
                      "destination": places["destination"],
                      "from": {"identity": document["identity"],
                               "runtime": dict(document["runtime"])},
                      "to": {"identity": said,
                             "runtime": {"files": source["files"],
                                         "digest": source["digest"]}},
                      **names}
            intent["upgrade_id"] = _upgrade_id(intent)
            instance.publish(intent_place, intent)
            print("intent     " + str(intent_place), file=stream)
        old = intent["from"]["runtime"]["digest"]
        new = intent["to"]["runtime"]["digest"]
        # ROLL FORWARD, each step only when the names say it has not happened.
        if _held_digest(places["distro"]) == old \
                and not os.path.lexists(intent["retired"]):
            os.rename(places["distro"], intent["retired"])
        if not os.path.lexists(places["distro"]) \
                and _held_digest(intent["staging"]) == new:
            os.rename(intent["staging"], places["distro"])
        if _held_digest(places["distro"]) != new:
            raise UpgradeRefusal(
                "the runtime at " + places["distro"] + " is not the recorded "
                "upgrade target after rolling forward; " + str(intent_place)
                + " is kept for the next attempt.")
        current = instance.read(place)
        if current["runtime"]["digest"] != new:
            instance.publish(place, dict(current, identity=intent["to"]["identity"],
                                         runtime=dict(intent["to"]["runtime"])))
        # ONCE PER INTENT (review 2026-11-27 [2]): a record already committed
        # for this intent is the completion; only the intent's removal remains.
        journal = Path(places["destination"]) / HISTORY
        upgrade_id = intent.get("upgrade_id") or _upgrade_id(intent)
        if _completed(journal, upgrade_id) is None:
            torn = journal.exists() and journal.stat().st_size \
                and not journal.read_bytes().endswith(b"\n")
            with open(journal, "a") as appending:
                appending.write(("\n" if torn else "") + json.dumps(
                    dict(intent, upgrade_id=upgrade_id, completed_at=now()),
                    sort_keys=True) + "\n")
                appending.flush()
                os.fsync(appending.fileno())
        os.unlink(intent_place)
        print("upgraded   runtime " + old[:16] + " -> " + new[:16]
              + "; retired runtime kept at " + intent["retired"], file=stream)
        print("stores, Jobs, Works and configuration unchanged; start the stack "
              "to serve them with the new runtime", file=stream)
        return 0
