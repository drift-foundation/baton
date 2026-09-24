"""Re-derive the live run's verdict from the retained store, independently.

Review 2026-09-23T14:45:57Z R1: the supported `ControlStore.open_readonly`
refused with an `OperationalError` before the frozen attribution could be read,
so the accepted verdict in `live-review-248377/outcome.json` was a RETAINED
EXECUTION CLAIM rather than an independently derived fact. The reviewer asked
for "an operationally supported read-only snapshot/export from the exact pinned
deployment", bound to the source digest, authority, store and attempt, with the
verdict compared against the preserved outcome and the reviewer's three
identities shown to differ from the producer's.

This is that export, and it takes nothing on trust from the outcome: every
value below is READ from the store through a public reader, and the outcome is
opened only at the end, to be COMPARED against what was read.

WHAT IT DOES NOT DO. It opens no runtime, engine, network or credential; it
writes nothing to the deployment; it makes no raw SQLite connection, uses no
`immutable=` handle, copies no database and attempts no write-capable fallback.
`ControlStore.open_readonly` is the only opener, `mode=ro` is its own choice,
and one `snapshot()` covers every read so the facts are coherent with each
other.

THE COMPANION FILES ARE SQLITE'S, NOT THIS PROGRAM'S. A `wal` database opened
read-only gets its `-shm` and a zero-length `-wal` if they are absent; this
happened again here and is disclosed in PROGRESS.md, as it was at claim 244629.
"""
import argparse
import hashlib
import json
import pathlib

from baton_v12.job_manager.review_driver import review_verdict_from_result
from baton_v12.worker_manager import (ControlStore, checkpoint_of, cleanup_of,
                                      frozen_output_of, line_of, load_manifest,
                                      review_of, writer_of)

HERE = pathlib.Path(__file__).resolve().parent
EVIDENCE = HERE / "live-review-248377"
SCHEMA = "baton.independent-review-attribution/1"


def sha(path):
    reading = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            reading.update(block)
    return reading.hexdigest()


def read(store, thunk, what):
    """One public read, with the refusal named rather than swallowed."""
    try:
        return thunk()
    except Exception as failure:                             # noqa: BLE001
        raise SystemExit(
            f"the supported reader refused while reading {what}: "
            f"{type(failure).__name__}: {failure}") from None


def retention_of(packet):
    """The retention policy the run actually served, bound by its own digest.

    `cleanup_of` answers the committed cleanup FOR A POLICY, so reading it
    needs the policy this deployment ran under. That value lives in the run's
    `deployment.json`, and the packet records that file's SHA256 -- so the
    document is verified against the packet before a value is taken out of it
    rather than trusted for sitting at the right path.
    """
    deployment = packet["deployment"]
    place = pathlib.Path(deployment["config_path"])
    if not place.is_file():
        raise SystemExit(f"the run's deployment configuration is missing at "
                         f"{place}; it carries the retention policy this "
                         f"cleanup was committed under")
    digest = sha(place)
    if digest != deployment["config_sha256"]:
        raise SystemExit(f"the run's deployment configuration at {place} "
                         f"hashes {digest}, and the packet binds "
                         f"{deployment['config_sha256']}")
    held = json.loads(place.read_text("utf-8"))
    policy = held.get("retention_policy_digest")
    if not policy:
        raise SystemExit(f"{place} names no retention_policy_digest")
    return policy, digest


def derived(store, *, line_id, checkpoint_id, attachment_id, attempt_id,
            retention_policy_digest):
    """Everything the reviewer listed, inside ONE coherent snapshot."""
    with store.snapshot():
        line = read(store, lambda: line_of(store, line_id), "the line")
        checkpoint = read(store, lambda: checkpoint_of(store, checkpoint_id),
                          "the checkpoint")
        attachment = read(store, lambda: review_of(store, attachment_id),
                          "the review attachment")
        frozen = read(store, lambda: frozen_output_of(store, attempt_id),
                      "the frozen output")
        manifest = read(
            store,
            lambda: load_manifest(store, frozen["manifest_digest"],
                                  "resultManifest"),
            "the retained result manifest")
        verdict = read(
            store,
            lambda: review_verdict_from_result(store,
                                               attachment_id=attachment_id),
            "the derived verdict")
        cleanup = read(
            store,
            lambda: cleanup_of(
                store, attempt_id=attempt_id,
                retention_policy_digest=retention_policy_digest),
            "the cleanup record")
        # THE PRODUCER'S WRITER, through the checkpoint's own line rather than
        # through anything this program supplies.
        writer = read(store, lambda: writer_of(store, line["writer_id"]),
                      "the producer's writer") if line.get("writer_id") \
            else None
        if writer is None:
            current = read(
                store,
                lambda: checkpoint_of(store, line["current_checkpoint_id"]),
                "the line's current checkpoint")
            writer = read(store,
                          lambda: writer_of(store, current["writer_id"]),
                          "the producer's writer")
    return {"line": line, "checkpoint": checkpoint, "attachment": attachment,
            "frozen": frozen, "manifest": manifest, "verdict": verdict,
            "cleanup": cleanup, "writer": writer}


def independence(writer, attachment):
    """All three identities, compared rather than asserted.

    `attach_review` refused at attachment time if any of the three were shared;
    this repeats the comparison from the RETAINED rows, so the separation is a
    fact about what is in the store rather than a fact about what the manager
    once checked.

    IT REFUSES RATHER THAN PASSING VACUOUSLY. The first version of this read
    `worker_id`/`participant`/`principal` off the attachment row, which names
    them `reviewer_*`; every reviewer value came back `None`, nothing could
    equal anything, and the export said `independent: true` while having
    compared nothing at all. An absent identity is now a refusal, because a
    comparison over missing values is the most expensive kind of false
    negative -- it looks exactly like a pass.
    """
    producer = {"worker_id": writer.get("worker_id"),
                "participant": writer.get("participant"),
                "principal": writer.get("principal")}
    reviewer = {"worker_id": attachment.get("reviewer_worker_id"),
                "participant": attachment.get("reviewer_participant"),
                "principal": attachment.get("reviewer_principal")}
    missing = sorted([f"the producer's {one}" for one in producer
                      if not producer[one]] +
                     [f"the reviewer's {one}" for one in reviewer
                      if not reviewer[one]])
    if missing:
        raise SystemExit(
            "independence cannot be established from these rows: "
            + ", ".join(missing) + " is absent. A comparison over missing "
            "values would pass without comparing anything.")
    shared = sorted(one for one in producer
                    if producer[one] == reviewer[one])
    return {"producer": producer, "reviewer": reviewer, "shared": shared,
            "independent": not shared,
            "compared": sorted(producer)}


def assignment_binding(manifest, attachment, *, authority_uuid, work_id):
    """The result manifest's own assignment, against this attachment's.

    `review_verdict_from_result` already refuses a manifest whose assignment
    disagrees; this records WHAT it agreed about, so the export stands on
    stated values rather than on a refusal that did not happen.
    """
    reference = manifest.get("assignment_ref") or {}
    work = reference.get("work_ref") or {}
    return {
        "generation": reference.get("generation"),
        "participant": reference.get("participant"),
        "work_ref": work,
        "matches_attachment_generation":
            reference.get("generation") == attachment.get(
                "assignment_generation"),
        "matches_attachment_participant":
            reference.get("participant") == attachment.get(
                "reviewer_participant"),
        "matches_packet_work":
            work.get("authority_uuid") == authority_uuid
            and work.get("work_id") == work_id,
    }


def compared(verdict, outcome):
    """The derived verdict against the one the run published."""
    published = {one["attachment_id"]: one
                 for one in outcome["workload"]["verdicts"]}
    held = published.get(verdict["attachment_id"])
    if held is None:
        return {"agrees": False,
                "why": "the outcome published no verdict for this attachment"}
    differs = {name: {"derived": verdict.get(name), "published": held.get(name)}
               for name in ("verdict", "result_id", "result_digest", "base",
                            "head", "tree", "checkpoint_id", "attempt_id")
               if verdict.get(name) != held.get(name)}
    return {"agrees": not differs, "differs": differs,
            "compared_members": ["verdict", "result_id", "result_digest",
                                 "base", "head", "tree", "checkpoint_id",
                                 "attempt_id"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", required=True,
                        help="the EXECUTED packet, as retained in "
                             "live-review-248377/PACKET-executed.json")
    parser.add_argument("--outcome", required=True,
                        help="the retained outcome to compare against")
    parser.add_argument("--incarnation", required=True)
    parser.add_argument("--into", required=True,
                        help="where to write this export")
    chosen = parser.parse_args(argv)

    packet = json.loads(pathlib.Path(chosen.packet).read_text("utf-8"))
    outcome = json.loads(pathlib.Path(chosen.outcome).read_text("utf-8"))
    subject = packet["subject"]
    attachments = outcome["workload"]["attachments"]
    if len(attachments) != 1:
        raise SystemExit(f"this export reads ONE review attachment; the "
                         f"outcome names {len(attachments)}")
    attached = attachments[0]

    # THE PACKET'S OWN BINDING, not an operand of this program: the store the
    # run was composed against and the store the line lives in are the same
    # one, and the packet records it twice for exactly that reason.
    store_path = packet["producer_control_store"]
    if store_path != packet["deployment"]["control_store"]:
        raise SystemExit(
            f"this packet's producer store {store_path} is not the store its "
            f"deployment served: {packet['deployment']['control_store']}")
    policy, deployment_digest = retention_of(packet)
    store = ControlStore.open_readonly(
        store_path, incarnation=chosen.incarnation, clock=_moment)
    try:
        held = derived(store, line_id=subject["line_id"],
                       checkpoint_id=subject["checkpoint_id"],
                       attachment_id=attached["attachment_id"],
                       attempt_id=attached["runtime_attempt_id"],
                       retention_policy_digest=policy)
    finally:
        store.close()

    export = {
        "schema": SCHEMA,
        "work": "W239533",
        "claim": 248565,
        "participant": "baton.claude",
        "note": "derived from the pinned deployment through public readers "
                "inside one snapshot; the outcome was opened only to compare "
                "against it",
        "bound_to": {
            "control_store": store_path,
            "authority_uuid": subject["authority_uuid"],
            "work_id": subject["work_id"],
            "line_id": subject["line_id"],
            "checkpoint_id": subject["checkpoint_id"],
            "attachment_id": attached["attachment_id"],
            "attempt_id": attached["runtime_attempt_id"],
            "manager_source": packet["manager_source"]["path"]
            if isinstance(packet.get("manager_source"), dict)
            else packet.get("manager_source"),
            "executed_packet_sha256": sha(chosen.packet),
            "outcome_sha256": sha(chosen.outcome),
            "deployment_config_sha256": deployment_digest,
            "retention_policy_digest": policy,
        },
        "line": {"state": held["line"].get("state"),
                 "revision": held["line"].get("revision"),
                 "current_checkpoint_id":
                     held["line"].get("current_checkpoint_id")},
        "checkpoint": {"state": held["checkpoint"].get("state"),
                       "line_id": held["checkpoint"].get("line_id"),
                       "revision": held["checkpoint"].get("revision")},
        "attachment": {
            "attachment_id": held["attachment"].get("attachment_id"),
            "line_id": held["attachment"].get("line_id"),
            "checkpoint_id": held["attachment"].get("checkpoint_id"),
            "runtime_attempt_id":
                held["attachment"].get("runtime_attempt_id"),
            "assignment_generation":
                held["attachment"].get("assignment_generation"),
            "state": held["attachment"].get("state"),
            "attached_at": held["attachment"].get("attached_at"),
            "ended_at": held["attachment"].get("ended_at")},
        "frozen_result": {
            "result_id": held["frozen"].get("result_id"),
            "disposition": held["frozen"].get("disposition"),
            "manifest_digest": held["frozen"].get("manifest_digest")},
        "result_manifest": {
            "result_id": held["manifest"].get("result_id"),
            "manifest_digest": held["manifest"].get("manifest_digest"),
            "disposition": held["manifest"].get("disposition"),
            "assignment": assignment_binding(
                held["manifest"], held["attachment"],
                authority_uuid=subject["authority_uuid"],
                work_id=subject["work_id"])},
        "derived_verdict": held["verdict"],
        "cleanup": held["cleanup"],
        "independence": independence(held["writer"], held["attachment"]),
        "agreement_with_outcome": compared(held["verdict"], outcome),
    }
    pathlib.Path(chosen.into).write_text(
        json.dumps(export, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8")
    print(json.dumps({
        "wrote": chosen.into,
        "derived_verdict": held["verdict"].get("verdict"),
        "agrees_with_outcome": export["agreement_with_outcome"]["agrees"],
        "independent": export["independence"]["independent"],
        "cleanup": (held["cleanup"] or {}).get("cleanup"),
    }, indent=2))
    return 0


def _moment():
    """The instant formula the operator page documents, reused unchanged."""
    import attachment
    return attachment.now()


if __name__ == "__main__":
    raise SystemExit(main())
