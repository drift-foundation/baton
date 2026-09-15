"""The preparation image's entrypoint: W6633's worker, this image's agent.

W161230 slice2, CHECKPOINT A.2. One line of composition, in a file, as
`dogfood_entry.py` and `integration_entry.py` already are -- so the injection
is an artefact a reviewer can read and a case can import, and so `ENTRYPOINT`
stays exec-form with no shell in the process tree.

IT IS `baton_worker.main(agent=...)` AND NOTHING ELSE. There is no second serve
loop, no second launch reader and no second framing here: `main` is the
documented seam, the manager drives it, and a preparation image with its own
worker entry would be a second implementation nobody reviewed.

WHAT THE AGENT IS ALLOWED TO BE. `PreparationAgent` gets the VALIDATED launch
document the worker already read, the declarations the manager already wrote,
and the ordinary input namespace. It holds no Authority session, no store, no
lease and no writable target -- there is no `baton_v12` in this image for it to
have held one with -- and every bound it applies comes from the launch's own
sealed execution limits rather than from anything the request asked for.
"""

import os
import sys

import baton_worker

import reconciliation_task as task

__all__ = ["PreparationAgent", "REPORT_OUTPUT", "CANDIDATE_OUTPUT", "main"]

# THE TWO DECLARED OUTPUTS THIS WORKLOAD PRODUCES. They are matched against
# what the MANAGER declared rather than invented: an agent that wrote an output
# nobody declared would be naming a path the manager never bound.
REPORT_OUTPUT = "preparation-report"
CANDIDATE_OUTPUT = "prepared-candidate"

# These causal commands moved from the coordinator into preparation. Keep
# their original Job-owned boundary (default300s), rather than selecting the
# imported-candidate verification boundary (default1800s) by the new location.
BOUNDARY = "host_verification"


class PreparationAgent:
    """Consent and execution for one managed preparation.

    THE THREE ROOTS ARE THE CONTRACT'S, NOT OPERANDS. A path this program
    could be TOLD is a path a container can be pointed at wrongly, which is the
    whole reason the environment transport was retired. They are keyword
    arguments for one reason, the same one `integration_entry.main` gives: a
    case drives this over disposable directories, and the alternative -- a case
    that could only run against absolute container paths -- is a case that
    never runs.
    """

    def __init__(self, *, input_root=None, output_root=None, scratch=None):
        self._input = input_root or os.path.join(task.INPUT_ROOT, "source")
        self._output = output_root or task.OUTPUT_ROOT
        self._scratch = scratch or task.SCRATCH_ROOT

    def consider(self, seen, request):
        """Answer `accept` or `decline` -- and NOTHING ELSE.

        A consent answer carries no workspace path, no output and no plan: the
        container it comes from has none of those. What this one adds is that
        it declines a contract it could not honour, rather than accepting and
        discovering that later: without a sealed Job execution there is no
        verified bound for the commands, and a preparation run under a limit
        nobody agreed to is not one this workload will start.
        """
        contract = seen.get("contract", "")
        try:
            task.owned_limits(seen)
        except task.PreparationRefusal as refusal:
            return {"decision": "decline", "reason": str(refusal)}
        if "decline" in contract.lower():
            return {"decision": "decline",
                    "reason": "the contract asks for a decline"}
        return {"decision": "accept",
                "reason": "this container can honour the launched limits"}

    def work(self, seen, declared):
        """Read, verify, materialize, observe, and write what was declared.

        THE ORDER IS THE CONTRACT, and every step refuses before the next one
        can happen: the limits come from the sealed launch, the request must
        equal them, the published artifacts must be the ones the request was
        composed over, and only then is anything materialized or run. Nothing
        executes until all four hold.
        """
        owned = task.owned_limits(seen)
        request = task.read_request(self._input, owned=owned)
        measured = task.verify_input(self._input, request)
        seconds = _bound(owned)
        try:
            states, derived = task.materialize(self._input, request,
                                               self._scratch, seconds)
        except task.PreparationConflict as conflict:
            # A CONFLICT IS A REPORTED OUTCOME. The candidate and the target
            # changed the same content; nothing ran, and this workload does not
            # resolve that by preferring a side.
            return _conflicted(self._output, declared, request, conflict)
        completed, not_run, tag, phase, harness = task.observe(
            request, states, seconds)
        report = task.compose_report(request, states, completed, not_run, tag,
                                     phase, harness)
        report["input_content"] = measured
        # THE DERIVED IDENTITY, CARRIED SEPARATELY FROM THE ORIGINALS. The
        # combined state is content this container made; saying so is what
        # keeps a reader from mistaking it for the accepted candidate.
        report["derived_candidate"] = derived
        return _written(self._output, declared, report, states)


def _conflicted(output_root, declared, request, conflict):
    """What a preparation answers when the content cannot be combined."""
    report = {"schema": task.REPORT_SCHEMA,
              "orchestration_id": request.get("orchestration_id"),
              "kind": "not-collected", "status": None, "tag": "conflict",
              "phase": "combined", "completed": [],
              "not_run": list(request["commands"]),
              "harness_digest": request["harness_digest"],
              "harness_measured_digest": None,
              "source": dict(request["source"]), "states": {},
              "derived_candidate": None,
              "output": [{"name": "combined", "output": str(conflict)}]}
    answers = []
    for one in declared:
        if one["name"] == REPORT_OUTPUT:
            place = os.path.join(output_root, one["path"])
            os.makedirs(place, exist_ok=True)
            _emit(os.path.join(place, "report.json"),
                  task._canonical(report).encode("utf-8"))
            answers.append({"name": one["name"], "status": "present",
                            "result_metadata": {}})
        else:
            answers.append({"name": one["name"], "status": "absent",
                            "result_metadata": {}})
    return {"disposition": "completed", "outputs": answers,
            "recap": "preparation not-collected; the candidate and the target "
                     "snapshot cannot be combined"}


def _bound(owned):
    """The command bound, out of the LAUNCH'S OWN resolved boundaries.

    Not an operand and not a default written here. `observe` takes a seconds
    value from its caller, and this is the one caller that is entitled to
    decide it -- because this is where the sealed document is.
    """
    boundaries = owned.get("boundaries") or {}
    held = boundaries.get(BOUNDARY)
    if type(held) is not dict or type(held.get("seconds")) is not int \
            or type(held.get("seconds")) is bool:
        raise task.PreparationRefusal(
            "this launch resolves no " + BOUNDARY + " boundary, so there is "
            "no agreed bound for a preparation command and this workload will "
            "not invent one")
    return held["seconds"]


def _written(output_root, declared, report, states):
    """Every DECLARED output, written where the manager said and nowhere else.

    THE PATHS ARE THE DECLARATIONS'. An agent that chose its own would be
    naming material the manager never bound, and the worker -- which measures
    what was produced -- would be measuring a tree nobody asked for.
    """
    answers, produced = [], []
    for one in declared:
        place = os.path.join(output_root, one["path"])
        os.makedirs(place, exist_ok=True)
        if one["name"] == REPORT_OUTPUT:
            _emit(os.path.join(place, "report.json"),
                  task._canonical(report).encode("utf-8"))
        elif one["name"] == CANDIDATE_OUTPUT:
            # THE PREPARED CANDIDATE, WHICH IS THE COMBINED STATE'S CONTENT.
            # A preparation exists to produce one, and the state that carries
            # the fix and its test together is the combined one.
            _copy_out(states, "combined", place)
        else:
            # AN OUTPUT THIS WORKLOAD DOES NOT PRODUCE IS NOT INVENTED. It is
            # reported absent, because a manager that declared it is entitled
            # to know it did not arrive rather than to receive an empty
            # directory that looks produced.
            answers.append({"name": one["name"], "status": "absent",
                            "result_metadata": {}})
            continue
        produced.append(one["name"])
        answers.append({"name": one["name"], "status": "present",
                        # OPAQUE, and empty is the honest value: the worker
                        # measures the bytes, because a content manifest is a
                        # claim about a tree and this is the least trusted
                        # thing in the container.
                        "result_metadata": {}})
    return {"disposition": "completed", "outputs": answers,
            "recap": ("preparation " + report["kind"] + "; produced "
                      + (", ".join(produced) if produced else "nothing"))}


def _emit(place, body):
    handle = os.open(place, os.O_WRONLY | os.O_CREAT | os.O_EXCL
                     | os.O_NOFOLLOW, 0o600)
    try:
        written = 0
        while written < len(body):
            written += os.write(handle, body[written:])
    finally:
        os.close(handle)


def _copy_out(states, name, place):
    held = states.get(name)
    if held is None:
        raise task.PreparationRefusal(
            "this preparation ran no " + name + " state, so there is no "
            "prepared candidate to hand back")
    task._copy_tree(held["path"], place)


def main(argv=None, **taken):
    return baton_worker.main(agent=PreparationAgent(), **taken)


if __name__ == "__main__":
    sys.exit(main())
