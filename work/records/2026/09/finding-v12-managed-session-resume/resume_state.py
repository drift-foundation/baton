"""What the retained prerequisites ACTUALLY leave for a restore. READ-ONLY.

Owner reroute 250274: "Prepare bounded separate resume proof using actual
retained context/provenance and actual executable deterministic path. W239533
verdict was accepted: do not fabricate changes-requested; establish real
continuation input and identify any additional selection needed."

So the first act is to read what is there rather than to assume it. This opens
W239528's retained control and Job stores READ-ONLY, through the same pinned
manager snapshot W239533's attribution used, and reports:

  * the line, its checkpoint and its current state;
  * the review attachment and the DISPOSITION of its verdict;
  * the producer attempt's provider CONTEXT -- whether one exists, whether it
    finalized, its generation and its conversation id -- because a managed
    resume is a second use of THAT context and nothing else;
  * whether any owner-committed correction operation exists for the frozen
    checkpoint;
  * and what the product's own `correction_feedback_of` says when asked for a
    restore prompt over this state. Its refusal, by name, is the finding.

IT OPENS NOTHING WRITABLE. Both stores are opened through the public
`open_readonly` constructors, no act is committed, no runtime is reached, and
nothing under `/home/sl/baton-runs` is written.
"""
import hashlib
import json
import os
import sys

# THE PINNED SNAPSHOT, AHEAD OF EVERYTHING. W247941's review made the reason
# explicit: cwd independence is not provenance. `baton_v12` and `tools` must be
# the bytes the prerequisites were accepted on, and the receipt below prints
# each module's `__file__` and digest so a reader can check rather than trust.
SNAPSHOT = "/home/sl/baton-runs/independent-review-247947/manager-source"
PRODUCER_SNAPSHOT = "/home/sl/baton-runs/single-implementation-242687/manager-source"
RUN_ROOT = "/home/sl/baton-runs/single-implementation-244216"
CONTROL = os.path.join(RUN_ROOT, "db", "control.sqlite3")
JOBS = os.path.join(RUN_ROOT, "db", "jobs.sqlite3")

# THE SUBJECT, as W239533's own ATTRIBUTION-248565.json records it.
AUTHORITY = "7ea319da93384b77bc3ddea38602d7a3"
WORK = "7ea319da-W1"
LINE = "line-0d5b62ba32f714e3dd0a8bb8a2c88ed1622ad5cf1dbf5db1d3bd40e0af044c8d"
CHECKPOINT = ("checkpoint-ab8207baa93b5abc12393a67c1e04046e14bebd7e9defdf09"
              "40e168203b711a9")
ATTACHMENT = ("review-3536ffc95a8771beec30d669b763fe2f0b450b2604fc16e1f38d3f"
              "28acaea156")
PRODUCER_ATTEMPT = ("attempt-4842e704ec3f10456e7a4e1e229401862cf8d8789779df0e"
                    "f6d93fe8a0734d4b")
REVIEWER_ATTEMPT = ("attempt-50b9aac1dd99231cc19043be78ae72f8fea77bfb7f124f6f"
                    "4b31142e6f981461")

if not os.path.isdir(os.path.join(SNAPSHOT, "baton_v12")):
    raise SystemExit(
        f"REFUSED: the pinned manager snapshot is not at {SNAPSHOT}; a reader "
        f"that silently falls back to the checkout reports a different "
        f"product than the one these prerequisites were accepted on")
for one in (SNAPSHOT,):
    while one in sys.path:                                    # pragma: no cover
        sys.path.remove(one)
    sys.path.insert(0, one)

NOW = "1970-01-01T00:00:00.000Z"


def digest_of(path):
    reading = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            reading.update(block)
    return reading.hexdigest()


def provenance():
    """Which bytes answered, for every product module this reader used."""
    held = {}
    for name in sorted(sys.modules):
        if name.split(".")[0] not in ("baton_v12", "tools"):
            continue
        place = getattr(sys.modules[name], "__file__", None)
        if not place:
            continue
        under = os.path.realpath(place).startswith(
            os.path.realpath(SNAPSHOT) + os.sep)
        held[name] = {"file": place, "from_snapshot": under,
                      "sha256": digest_of(place)}
    return {"modules": held,
            "not_from_snapshot": sorted(name for name, one in held.items()
                                        if not one["from_snapshot"])}


def asked(what, thunk):
    """One read, with its refusal kept rather than converted into a gap."""
    try:
        return {"asked": what, "answer": thunk()}
    except BaseException as failure:                          # noqa: BLE001
        return {"asked": what,
                "refused": f"{type(failure).__name__}: {failure}"}


def main():
    from baton_v12.job_manager import JobStore, episodes
    from baton_v12.worker_manager import ControlStore, provider_context
    from baton_v12.worker_manager import review_cycles, sessions

    for place in (CONTROL, JOBS):
        if not os.path.isfile(place):
            raise SystemExit(f"REFUSED: {place} is not a file to read")

    held = {"schema": "baton.v12-resume-state/1", "work": "W236087",
            "participant": "baton.claude",
            "read_only": True, "run_root": RUN_ROOT,
            "control_store": CONTROL, "job_store": JOBS,
            "control_sha256": digest_of(CONTROL),
            "job_store_sha256": digest_of(JOBS),
            "producer_snapshot_present": os.path.isdir(PRODUCER_SNAPSHOT)}

    control = ControlStore.open_readonly(CONTROL, incarnation="resume-state",
                                         clock=lambda: NOW)
    jobs = JobStore.open_readonly(JOBS, authority_uuid=AUTHORITY,
                                  incarnation="resume-state",
                                  clock=lambda: NOW)
    try:
        held["line"] = asked(
            "the development line this proposal lives on",
            lambda: review_cycles.line_of(control, LINE))
        held["checkpoint"] = asked(
            "the frozen checkpoint the review attached to",
            lambda: review_cycles.checkpoint_of(control, CHECKPOINT))
        held["review"] = asked(
            "the review attachment and its verdict",
            lambda: review_cycles.review_of(control, ATTACHMENT))

        # THE CONTEXT IS THE WHOLE QUESTION. A managed resume is a SECOND USE
        # of the producer's own provider context at generation 1; without a
        # finalized generation 0 there is nothing to resume, whatever the
        # verdict says.
        held["producer_context"] = asked(
            "the producer attempt's provider context use",
            lambda: provider_context.context_use_of(control,
                                                    PRODUCER_ATTEMPT))
        held["producer_execution"] = asked(
            "the producer attempt's proved context execution",
            lambda: provider_context.prove_context_execution(control,
                                                             PRODUCER_ATTEMPT))
        held["producer_sessions"] = asked(
            "the agent sessions recorded for the producer attempt",
            lambda: sessions.agent_sessions_of(control, PRODUCER_ATTEMPT))
        held["reviewer_context"] = asked(
            "the reviewer attempt's provider context use",
            lambda: provider_context.context_use_of(control,
                                                    REVIEWER_ATTEMPT))

        # AND WHETHER ANY CORRECTION WAS EVER OPENED for this checkpoint. The
        # operation id is derived, so this asks by identity rather than by
        # scanning for something that looks like one.
        def correction():
            found = {}
            from baton_v12.job_manager import submission
            for stage in submission.stage_rows(jobs):
                one = episodes.correction_operation_id(stage["job_id"],
                                                       CHECKPOINT)
                row = jobs.operation_record(one)
                found[stage["job_id"]] = {
                    "operation_id": one,
                    "record": None if row is None else {
                        "kind": row["kind"], "state": row["state"]}}
            return found

        held["correction_operations"] = asked(
            "an owner-committed correction for this frozen checkpoint",
            correction)

        # THE PRODUCT'S OWN ANSWER, asked directly. This is the reader a
        # restore invocation uses to build its prompt, and its refusal names
        # exactly what this dossier is missing.
        held["correction_feedback"] = asked(
            "the restore feedback the product would deliver",
            lambda: provider_context.correction_feedback_of(
                control, jobs, PRODUCER_ATTEMPT))
    finally:
        jobs.close()
        control.close()

    held["provenance"] = provenance()
    print(json.dumps(held, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
