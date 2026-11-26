"""Which durable review verdict, if any, belongs to one review stage. W385263.

Owner decision 2026-11-26: when every phase of an ordinary Job is complete,
the headline is ALL PHASES COMPLETE, and a durable review verdict is shown
beside it only when it matches THIS Job's review attempt and candidate
checkpoint. This module answers that one question for the shared status read,
so status, monitor and TUI agree, whether or not a manager is serving.

WHAT "MATCHES" MEANS, every step proved by the control store's own readers:

  * the attachment is the one this review attempt was given
    (`review_cycles.review_for_attempt`, which binds it to the act that
    attached it and to the reviewer's assignment generation);
  * the verdict is the one `record_verdict` would have named for that
    attachment and a disposition (`verdict-` + digest of both), read through
    `review_cycles.verdict_of`, which proves the row against its committed act;
  * the verdict names that attachment and the checkpoint the attachment
    examined, and that checkpoint is still its line's current checkpoint --
    the candidate. A verdict about an earlier round's checkpoint is history,
    not this candidate's verdict.

ANYTHING ELSE IS NO VERDICT. No attachment, no recorded verdict, more than one,
or a record the readers refuse all answer `None`, and the headline then shows
no verdict. Absence is never upgraded, and nothing here writes.
"""
from baton_v12.contracts import ContractRefusal, digest
from baton_v12.worker_manager import review_cycles

MEMBERS = ("disposition", "verdict_id", "attachment_id", "attempt_id",
           "checkpoint_id", "line_id", "base_object", "head_object",
           "tree_object", "importable")


def matching(control, *, attempt_id, generation):
    """The one verdict bound to this review attempt and its candidate, or None."""
    if type(attempt_id) is not str or not attempt_id \
            or type(generation) is not int or isinstance(generation, bool):
        return None
    try:
        attachment = review_cycles.review_for_attempt(
            control, attempt_id=attempt_id, generation=generation)
    except ContractRefusal:
        return None
    if attachment is None:
        return None
    try:
        line = review_cycles.line_of(control, attachment["line_id"])
    except ContractRefusal:
        return None
    candidate = line.get("current_checkpoint_id")
    found = []
    for disposition in review_cycles.DISPOSITIONS:
        identity = "verdict-" + digest(
            {"attachment_id": attachment["attachment_id"],
             "disposition": disposition}).split(":", 1)[1]
        try:
            verdict = review_cycles.verdict_of(control, identity)
        except ContractRefusal:
            continue
        if verdict["attachment_id"] == attachment["attachment_id"] \
                and verdict["disposition"] == disposition \
                and verdict["checkpoint_id"] == attachment["checkpoint_id"] \
                and verdict["line_id"] == attachment["line_id"] \
                and verdict["checkpoint_id"] == candidate:
            found.append(verdict)
    if len(found) != 1:
        return None
    verdict = found[0]
    # M386422: IMPORTABLE is the product's own integration eligibility -- the
    # line's accepted, frozen current checkpoint with this exact accepted
    # verdict (`review_cycles.integration_checkpoint`). Anything it refuses or
    # does not answer is "not established", never "importable".
    importable = False
    if verdict["disposition"] == "accepted":
        try:
            eligible = review_cycles.integration_checkpoint(control, attachment["line_id"])
        except ContractRefusal:
            eligible = None
        importable = (eligible is not None and eligible["checkpoint_id"] == verdict["checkpoint_id"])
    return {"disposition": verdict["disposition"],
            "verdict_id": verdict["verdict_id"],
            "attachment_id": verdict["attachment_id"],
            "attempt_id": attempt_id,
            "checkpoint_id": verdict["checkpoint_id"],
            "line_id": verdict["line_id"],
            "base_object": verdict.get("base_object"),
            "head_object": verdict.get("head_object"),
            "tree_object": verdict.get("tree_object"),
            "importable": importable}
